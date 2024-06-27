#!/usr/bin/env python3

import re
import pandas as pd
import configargparse
import subprocess

"""
Wrapper for stack_nolhs.rb that adds support for headers in the csv input

Command-line inputs:
-c --config_file        config file with command-line options
--doe_params_file       csv (with headers) filename for input into stack_nolhs.rb
-s --stack              pass through to stack_nolhs.rb
-l --levels             pass through to stack_nolhs.rb
--doe_output_file       csv output filename for input into run_yaml_design.rb
"""

PARSER = configargparse.ArgParser()
PARSER.add_argument("-c", "--config_file", is_config_file=True)
PARSER.add_argument("--doe_params_file", type=str, required=True)
PARSER.add_argument("-s","--stack", type=int, default=None)
PARSER.add_argument("-l","--levels", type=int, default=None)
PARSER.add_argument("--doe_output_file", type=str, default=None)
DF = pd.read_csv(PARSER.parse_args().doe_params_file)
DF_STRIPPED = DF.to_csv(header=False, index=False)
HEADERS = ','.join(DF.columns.tolist())
PASS_ARGS = "-s "+str(PARSER.parse_args().stack) if PARSER.parse_args().stack else ""
PASS_ARGS += " -l "+str(PARSER.parse_args().levels) if PARSER.parse_args().levels else ""
print(PASS_ARGS)
DOE = subprocess.run(
    args = "ruby run/design_of_experiments/stack_nolhs.rb "+PASS_ARGS+" -e",
    shell = True,
    input = DF_STRIPPED,
    stdout = subprocess.PIPE,
    encoding = "utf-8",
)
DOE_CSV = re.sub("[^\S\r\n]",",", DOE.stdout.strip())
DOE_OUTPUT = HEADERS +"\n"+ DOE_CSV +"\n"
OUTPUT_FILE = PARSER.parse_args().doe_output_file
if OUTPUT_FILE:
    with open(OUTPUT_FILE, 'w') as f:
        f.write(DOE_OUTPUT)
else:
    print(DOE_OUTPUT)
