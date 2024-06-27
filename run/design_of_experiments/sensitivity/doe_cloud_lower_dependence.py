#!/usr/bin/env python3

import pandas as pd
import configargparse

"""
Wrapper for stack_nolhs.rb that adds support for headers in the csv input

Command-line inputs:
--doe_experiment_file   csv output by stack_nolhs_wrapper.py
"""

PARSER = configargparse.ArgParser()
PARSER.add_argument("--doe_experiment_file", type=str, required=True)
FILEPATH = PARSER.parse_args().doe_experiment_file
DF = pd.read_csv(FILEPATH)
DF['cloud_lower'] = DF['cloud_lower'] * DF['cloud_upper']
DF.to_csv(FILEPATH.split(".csv")[0]+"_cloud_lower_modified.csv", index=False)
