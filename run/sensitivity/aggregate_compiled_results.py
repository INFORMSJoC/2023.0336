#!/usr/bin/env python3

import os
import configargparse
import pandas as pd
from src.components import defaults
import run.sensitivity.helpers as sensitivity_helpers

"""
Script to aggregate all sensitivity results compiled by rightsize_sensitivity_all_designs.py

Command-line inputs:
-c --config_file            config file with command-line options
--results_dir               top level directory where results were stored
--sensitivity_timestamp     sensitivity subdirectory timestamp
"""

def process(filename):
    df = pd.read_csv(filename)
    headers = [defaults.PHOTOVOLTAIC_PANEL, defaults.DIESEL_GENERATOR, defaults.BATTERY]
    for col in headers:
        df[col+sensitivity_helpers.SENSITIVITY_COMPONENT_INCREASE_TAG] = df.apply(
            lambda x: 0 if x[col] == 0 else x[col]/x[col+sensitivity_helpers.SENSITIVITY_COMPONENT_ORIGINAL_TAG]-1,
            axis=1,
        )
    for i in range(len(headers)): headers[i] = headers[i]+sensitivity_helpers.SENSITIVITY_COMPONENT_INCREASE_TAG
    df[sensitivity_helpers.SENSITIVITY_INCREASE_PERCENTAGE_TAG] = df[headers].sum(axis=1)
    return df

PARSER = configargparse.ArgParser()
PARSER.add_argument("-c", "--config_file", is_config_file=True)
PARSER.add_argument("--results_dir", required=True)
PARSER.add_argument("--sensitivity_timestamp", required=True)
PARSER.add_argument("--local") # unused arg to allow same YAML as compile all
RESULTS_DIR = PARSER.parse_args().results_dir
df = pd.DataFrame
i = 0
for DESIGN_DIR in os.listdir(RESULTS_DIR):
    if not os.path.isdir(os.path.join(RESULTS_DIR,DESIGN_DIR)):
        continue
    rows = process(
        os.path.join(
            RESULTS_DIR,
            DESIGN_DIR,sensitivity_helpers.SENSITIVITY_FOLDER,
            PARSER.parse_args().sensitivity_timestamp+sensitivity_helpers.SENSITIVITY_FILENAME,
        ),
    )
    df = df.append(rows, ignore_index=True) if not df.empty else rows
df.to_csv(
    os.path.join(
        RESULTS_DIR,
        PARSER.parse_args().sensitivity_timestamp+sensitivity_helpers.SENSITIVITY_FILENAME,
    ),
    index=False,
)
