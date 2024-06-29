#!/usr/bin/env python3

import os
import configargparse
import json
from src.components import defaults as component_defaults
import src.utils as utils
import run.helpers as run_helpers
import run.sensitivity.helpers as sensitivity_helpers

"""
Script to run sensitivity analysis on all rightsized designs
with optional capacity increases controlled by 'increase' and 'gridspaces' args

Command-line inputs:
-c --config_file        config file with command-line options
--results_dir           directory path for all rightsized mirogrid designs
--local                 flag for whether to run on HPC using SBATCH
--num_runs              number of runs to simulate sensitivity analysis
--rng_yaml              filepath to YAML file with random num gen parameters
--rng_seed              initial seed for random number generator
--extend_timeframe      proportion of scenarios to duplicate to extend timeframe
--output_all            flag for whether to output csv and figures
--doe_file              filepath to CSV file with design of experiments scenarios
--debug_limit           max number of microgrid designs to process (for debugging)
--incease               max percentage of capacity increase allowed, if needed to avoid power shortages
--gridspaces            number of gridspaces to use when increasing capacity along a dimension
"""

def run_job(results_dir):
    command = """time python3.9 run/sensitivity/run_single_design.py \\
        --results_dir {0} --num_runs {1} --rng_yaml {2} --rng_seed {3} \\
        --extend_timeframe {4} {5} {6} --timestamp {7}\n""".format(
            results_dir,
            PARSER.parse_args().num_runs,
            PARSER.parse_args().rng_yaml,
            PARSER.parse_args().rng_seed,
            PARSER.parse_args().extend_timeframe,
            "--output_all" if PARSER.parse_args().output else "",
            "--doe_file {0}".format(PARSER.parse_args().doe_file) \
                if PARSER.parse_args().doe_file else "",
            TIMESTAMP_ALL,
    )
    if RUN_ON_HPC:
        os.makedirs(os.path.join(results_dir,TIMESTAMP_ALL), exist_ok=True)
        jobfile = os.path.join(results_dir, TIMESTAMP_ALL, "hpc.job")
        with open(jobfile, "w") as fh:
            fh.writelines("#!/bin/bash\n\n")
            fh.writelines("#SBATCH --job-name={0}\n".format(results_dir.split("/")[-1]))
            fh.writelines("#SBATCH --mail-type=NONE\n")
            fh.writelines("#SBATCH --mail-user={0}@nps.edu\n".format(os.environ.get('USER')))
            fh.writelines("#SBATCH --cpus-per-task=1\n")
            fh.writelines("#SBATCH --mem=1gb\n")
            fh.writelines("#SBATCH --time=0-12:00\n")
            fh.writelines("#SBATCH --output={0}.out\n\n".format(
                    os.path.join(results_dir, TIMESTAMP_ALL, "hpc")
                )
            )
            fh.writelines(". /etc/profile\n\n")
            fh.writelines("module load lang/python\n\n")
            fh.writelines("module load lang/ruby\n\n")
            fh.writelines("export SETUPTOOLS_USE_DISTUTILS=stdlib\n\n")
            fh.writelines("# make requirements\n")
            fh.writelines(command)
        os.system("echo {0}".format(jobfile))
        os.system("sbatch {0}".format(jobfile))
    else:
        os.system(command)

def process_single_design(design_dir, max_percent_increase, grid_spaces):
    with open(os.path.join(design_dir, utils.MICROGRID_DESIGN_FILENAME), "rt") as f:
        design_dict = json.load(f)
    if grid_spaces == 0 and max_percent_increase > 0.0: grid_spaces = 1
    if max_percent_increase == 0.0: grid_spaces = 0
    grid_increase = max_percent_increase / grid_spaces if grid_spaces > 0 else 0
    jobs = set()
    for i in range(grid_spaces+1):
        for j in range(grid_spaces+1-i):
            jobs.add((design_dict[component_defaults.PHOTOVOLTAIC_PANEL] * (1 + i * grid_increase),
                      design_dict[component_defaults.BATTERY] * (1 + j * grid_increase)))
    for job in jobs:
        dg_power = design_dict[component_defaults.DIESEL_GENERATOR]
        jobname = "dg{0}_b{1}_pv{2}".format(str(int(dg_power)), str(int(job[1])), str(int(job[0])))
        results_dir = os.path.join(design_dir,sensitivity_helpers.SENSITIVITY_FOLDER,jobname)
        os.makedirs(results_dir, exist_ok=True)
        with open(os.path.join(results_dir, utils.MICROGRID_DESIGN_FILENAME), "wt", encoding="utf-8") as f:
            json.dump({
                component_defaults.DIESEL_GENERATOR:dg_power,
                component_defaults.BATTERY:job[1],
                component_defaults.PHOTOVOLTAIC_PANEL:job[0],
            }, f, indent=4)
        with open(os.path.join(results_dir, sensitivity_helpers.SENSITIVITY_MICROGRID_CAPACITY_INCREASE_FILENAME), "wt", encoding="utf-8") as f:
            json.dump({
                component_defaults.DIESEL_GENERATOR:0.0,
                component_defaults.BATTERY:job[1]-design_dict[component_defaults.BATTERY],
                component_defaults.PHOTOVOLTAIC_PANEL:job[0]-design_dict[component_defaults.PHOTOVOLTAIC_PANEL],
            }, f, indent=4)
        run_job(results_dir)

def process_designs(dirpath, max_percent_increase, grid_spaces):
    i = 0
    for filename in os.listdir(dirpath):
        filepath = os.path.join(dirpath, filename)
        if not os.path.isdir(filepath): continue
        i += 1
        if MAX_DESIGNS and i > MAX_DESIGNS:
            break
        process_single_design(
            design_dir=filepath,
            max_percent_increase=max_percent_increase,
            grid_spaces=grid_spaces,
        )

def restricted_float(x):
    try:
        x = float(x)
    except Exception as error:
        raise ValueError("%r not a floating-point literal" % (x,))
    if x < 0.0:
        raise ValueError("%r cannot be negative"%(x,))
    return x

def restricted_int(x):
    try:
        x = int(x)
    except Exception as error:
        raise ValueError("%r not an int literal" % (x,))
    if x < 0:
        raise ValueError("%r cannot be negative"%(x,))
    return x

PARSER = configargparse.ArgParser()
PARSER.add_argument("-c", "--config_file", is_config_file=True)
PARSER.add_argument("--local", dest="hpc", action="store_false")
PARSER.add_argument("--results_dir", required=True)
PARSER.add_argument("--num_runs", type=int, required=True)
PARSER.add_argument("--rng_yaml", required=True)
PARSER.add_argument("--rng_seed", type=int, default=100)
PARSER.add_argument("--extend_timeframe", type=float, default=0.0) # num grid spaces
PARSER.add_argument("--output_all", dest="output", action="store_true")
PARSER.add_argument("--doe_file", type=str, default=None)
# increase and gridspaces >0 allow sensitivity analysis to modify designs
PARSER.add_argument("--debug_limit", type=int)
PARSER.add_argument("--increase", type=restricted_float, default=0.0) # max percent [0,1] to increase capacity
PARSER.add_argument("--gridspaces", type=restricted_int, default=0) # num grid spaces
RIGHTSIZE_DIR = PARSER.parse_args().results_dir
RUN_ON_HPC=PARSER.parse_args().hpc
MAX_DESIGNS=PARSER.parse_args().debug_limit
MAX_CAPACITY_INCREASE=PARSER.parse_args().increase
GRIDSPACES=PARSER.parse_args().gridspaces
TIMESTAMP_ALL = run_helpers.timestamp_now()
print(TIMESTAMP_ALL)
if not RUN_ON_HPC and not MAX_DESIGNS:
    print("Warning: to run locally, explicitly set '--debug_limit' to the max number of designs to run")
process_designs(RIGHTSIZE_DIR, MAX_CAPACITY_INCREASE, GRIDSPACES)
