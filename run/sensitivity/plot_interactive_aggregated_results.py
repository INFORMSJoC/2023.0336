#!/usr/bin/env python3

import configargparse
import pandas as pd
from src.components import defaults
import run.sensitivity.helpers as sensitivity_helpers
from src.visualization import rightsize_plot

"""
Script to plot sensitivity results aggregated by aggregate_compiled_sensitivity_results.py

Command-line inputs:
-c --config_file    config file with command-line options
--file              file with aggregated results
--filter            metric of interest, by default set to "mean"
--filtermax         max value on slider for filter
--one-per-design    flag to return only best performing for each microgrid design
"""

def get_min(df):
    df = df.loc[df[COLNAME] == min(df[COLNAME])]
    df = df.loc[df[sensitivity_helpers.SENSITIVITY_INCREASE_PERCENTAGE_TAG] == min(df[sensitivity_helpers.SENSITIVITY_INCREASE_PERCENTAGE_TAG])]
    df = df.head(1)
    return df

def get_subset(df):
    df_subset = pd.DataFrame(columns=df.columns)
    groups = df.groupby(by=[
            defaults.DIESEL_GENERATOR + sensitivity_helpers.SENSITIVITY_COMPONENT_ORIGINAL_TAG,
            defaults.BATTERY + sensitivity_helpers.SENSITIVITY_COMPONENT_ORIGINAL_TAG,
            defaults.PHOTOVOLTAIC_PANEL + sensitivity_helpers.SENSITIVITY_COMPONENT_ORIGINAL_TAG,
        ],
    )
    for group_name, df_group in groups:
        df_subset = df_subset.append(get_min(df_group))
    return df_subset

PARSER = configargparse.ArgParser()
PARSER.add_argument("-c", "--config_file", is_config_file=True)
PARSER.add_argument("--file", required=True)
PARSER.add_argument("--filter", default="mean")
PARSER.add_argument("--filtermax", type=float, default=0.10)
PARSER.add_argument("--one_per_design", action="store_true")
COLNAME = PARSER.parse_args().filter
DF = pd.read_csv(PARSER.parse_args().file)
if PARSER.parse_args().one_per_design:
    DF = get_subset(DF)

rightsize_plot.rightsize_to_plot(
    df = DF,
    preview = True,
    filter = PARSER.parse_args().filter,
    filter_max = PARSER.parse_args().filtermax,
)
