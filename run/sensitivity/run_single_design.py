#!/usr/bin/env python3

import random
import os
import sys
import select
import configargparse
import json
import pickle
import yaml
import subprocess
from src.models import Sensitivity
from src.components import defaults as component_defaults
import run.helpers as run_helpers
import src.utils as utils

"""
Script to run sensitivity analysis on a single specified microgrid design

Command-line inputs:
-c --config_file        config file with command-line options
--results_dir           directory path of single microgrid design
--num_runs              number of runs to simulate sensitivity analysis
--rng_yaml              filepath to YAML file with random num gen parameters
--rng_seed              initial seed for random number generator
--extend_timeframe      proportion of scenarios to duplicate to extend timeframe
--output_all            flag for whether to output csv and figures
--doe_file              filepath to CSV file with design of experiments scenarios
--timestamp             inherited when run via 'rightsize_sensitivity_all_designs.py'
"""

PARSER = configargparse.ArgParser()
PARSER.add_argument("-c", "--config_file", is_config_file=True)
PARSER.add_argument("--results_dir", required=True)
PARSER.add_argument("--num_runs", type=int, required=True)
PARSER.add_argument("--rng_yaml", required=True)
PARSER.add_argument("--rng_seed", type=int, default=100)
PARSER.add_argument("--extend_timeframe", type=float, default=0.0)
PARSER.add_argument("--output_all", dest="output", action="store_true")
PARSER.add_argument("--doe_file", type=str, default=None)
PARSER.add_argument("--timestamp")

def run_simulation(rng_parameter_dict, run_params, results_dir):
    random_seed = PARSER.parse_args().rng_seed
    random.seed(random_seed)
    run_params[run_helpers.RNG_SEED] = random_seed

    weather = run_helpers.weather_random_number_generator(rng_parameter_dict)
    run_params[run_helpers.WEATHER_PARAMS] = rng_parameter_dict

    sim = run_helpers.initialize_simulation_object(run_params, weather)
    sensitivity_analysis = Sensitivity(
        sim = sim,
        b_energy = GRID_DESIGN[component_defaults.BATTERY],
        dg_power = GRID_DESIGN[component_defaults.DIESEL_GENERATOR],
        pv_power = GRID_DESIGN[component_defaults.PHOTOVOLTAIC_PANEL],
        num_runs = PARSER.parse_args().num_runs,
        dirpath = results_dir if PARSER.parse_args().output else None,
    )

    os.makedirs(results_dir, exist_ok=True)

    with open(os.path.join(results_dir,run_helpers.PARAMS_PICKLE_FILENAME), 'wb') as fp:
        pickle.dump(run_params, fp)

    with open(os.path.join(results_dir,run_helpers.PARAMS_JSON_FILENAME), 'wt', encoding="utf-8") as fp:
        json.dump(run_params, fp, indent=4, default=str)

    with open(os.path.join(results_dir,"deficits.pkl"), 'wb') as fp:
        pickle.dump(sensitivity_analysis.deficits, fp)

    with open(os.path.join(results_dir,"deficits.json"), 'wt', encoding="utf-8") as fp:
        json.dump(sensitivity_analysis.deficits, fp, indent=4, default=str)

    return sensitivity_analysis.deficits

RESULTS_DIR = PARSER.parse_args().results_dir
if RESULTS_DIR.endswith("/"):
    RESULTS_DIR = RESULTS_DIR[:-1]

PARAMS_FILE = os.path.join(
    os.path.dirname(RESULTS_DIR), # parent directory of rightsized design
    run_helpers.PARAMS_PICKLE_FILENAME,
)

FLAG_PARENT_IS_ANCESTOR = True
if not os.path.exists(PARAMS_FILE):
    PARAMS_FILE = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(RESULTS_DIR))), # ancestor directory of modified design
        run_helpers.PARAMS_PICKLE_FILENAME,
    )
    FLAG_PARENT_IS_ANCESTOR = False

with open(PARAMS_FILE, "rb") as f:
    RUN_PARAMS = pickle.load(f)
    f.close()

with open(os.path.join(RESULTS_DIR, utils.MICROGRID_DESIGN_FILENAME), "rt") as f:
    GRID_DESIGN = json.load(f)
    f.close()

TIMESTAMP = PARSER.parse_args().timestamp if PARSER.parse_args().timestamp else run_helpers.timestamp_now()
RESULTS_DIR = os.path.join(RESULTS_DIR,TIMESTAMP)
os.makedirs(RESULTS_DIR, exist_ok=True)

RUN_PARAMS[run_helpers.EXTEND_TIMEFRAME] = PARSER.parse_args().extend_timeframe # extend timeframe for sensitivity analysis

# supports two methods for DOE YAML input
DOE_FLAG = True if PARSER.parse_args().doe_file else False
DESIGNS_YAML = sys.stdin.read() if select.select([sys.stdin],[],[],0.0)[0] else "" # (unix/mac, will break on Windows)
if len(DESIGNS_YAML)>0: # YAML piped from stardard input 
    DOE_FLAG = True
elif DOE_FLAG: # YAML file reference input
    REFORMATTING_SCRIPT_OUTPUT = subprocess.Popen(
        args = "ruby run/design_of_experiments/run_yaml_design.rb "+PARSER.parse_args().doe_file+" "+ PARSER.parse_args().rng_yaml,
        shell = True,
        stdout = subprocess.PIPE,
    )
    DESIGNS_YAML = REFORMATTING_SCRIPT_OUTPUT.communicate()[0].decode("utf-8")
if DOE_FLAG: # run design of experiments
    FIRST_ITERATION = True
    CSV_OUTPUT = ""
    COUNTER = 0
    for DOE_DESIGN_PARAMS in yaml.safe_load_all(DESIGNS_YAML):
        COUNTER+=1
        DEFICIT_PERCENTAGES = run_simulation(
            DOE_DESIGN_PARAMS,
            RUN_PARAMS,
            os.path.join(RESULTS_DIR,"doe-design-"+str(COUNTER)),
        )
        OUTPUT = ""
        if FIRST_ITERATION:
            OUTPUT += ','.join([i for i in sorted(DOE_DESIGN_PARAMS.keys())])
            OUTPUT += ','+','.join([utils.RUN_PREFIX + str(i) for i in range(PARSER.parse_args().num_runs)])+"\n"
            FIRST_ITERATION = False
        for KEY in sorted(DOE_DESIGN_PARAMS):
            VAL = DOE_DESIGN_PARAMS[KEY]
            if type(VAL) != dict:
                OUTPUT += str(VAL) + ","
        OUTPUT += ",".join([str(i) for i in DEFICIT_PERCENTAGES])
        CSV_OUTPUT += OUTPUT+"\n"
        print(OUTPUT)
    with open(os.path.join(RESULTS_DIR,"rng_doe.csv"), 'w') as f:
        f.write(CSV_OUTPUT)
else: # run single set of random number generation parameters
    DEFICIT_PERCENTAGES = run_simulation(
        RUN_PARAMS[run_helpers.WEATHER_PARAMS],
        RUN_PARAMS,
        os.path.join(RESULTS_DIR,"non-doe-single-param-set"),
    )
