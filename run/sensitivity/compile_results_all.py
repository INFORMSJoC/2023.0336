#!/usr/bin/env python3

import os
import configargparse

"""
Script to complile all results from rightsize_sensitivity_all_designs.py

Command-line inputs:
-c --config_file            config file with command-line options
--local                     flag for whether to run on HPC using SBATCH
--results_dir               top level directory where results were stored
--sensitivity_timestamp     sensitivity subdirectory timestamp
"""

def run_job(hpc, results_dir):
    command = """python3.9 run/sensitivity/compile_results_single.py \\
              --results_dir={0} --sensitivity_timestamp={1}\n""".format(
        results_dir,
        PARSER.parse_args().sensitivity_timestamp,
    )
    if hpc:
        jobfile = os.path.join(results_dir, "compile_results.job")
        with open(jobfile, "w") as fh:
            fh.writelines("#!/bin/bash\n\n")
            fh.writelines("#SBATCH --job-name={0}\n".format(results_dir.split("/")[-1]))
            fh.writelines("#SBATCH --mail-type=NONE\n")
            fh.writelines("#SBATCH --mail-user={0}@nps.edu\n".format(os.environ.get('USER')))
            fh.writelines("#SBATCH --cpus-per-task=1\n")
            fh.writelines("#SBATCH --mem=1gb\n")
            fh.writelines("#SBATCH --time=0-01:00\n")
            fh.writelines("#SBATCH --output={0}.out\n\n".format(
                    os.path.join(results_dir, "compile_results")
                )
            )
            fh.writelines(". /etc/profile\n\n")
            fh.writelines("module load lang/python\n\n")
            fh.writelines("export SETUPTOOLS_USE_DISTUTILS=stdlib\n\n")
            fh.writelines(command)
        os.system("sbatch {0}".format(jobfile))
    else:
        os.system(command)

PARSER = configargparse.ArgParser()
PARSER.add_argument("-c", "--config_file", is_config_file=True)
PARSER.add_argument("--local", dest="hpc", action="store_false")
PARSER.add_argument("--results_dir", required=True)
PARSER.add_argument("--sensitivity_timestamp", required=True)
RUN_ON_HPC=PARSER.parse_args().hpc
RESULTS_DIR = PARSER.parse_args().results_dir
for MICROGRID_DESIGN_DIR in os.listdir(RESULTS_DIR):
    if not os.path.isdir(os.path.join(RESULTS_DIR,MICROGRID_DESIGN_DIR)):
        continue
    run_job(RUN_ON_HPC,os.path.join(RESULTS_DIR,MICROGRID_DESIGN_DIR))
