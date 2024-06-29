#!/usr/bin/env python3

import os
import configargparse
import pandas as pd
import numpy as np
import re
from src.components import defaults
import run.helpers as run_helpers
import run.sensitivity.helpers as sensitivity_helpers
from src.visualization import rightsize_plot

"""
Script to group and visualize sensitivity results by microgrid design

Command-line inputs:
-c --config_file    config file with command-line options
--file              file with aggregated results
--outdir            directory path for generated plots
--increase_level    proportion by which rightsized design was allowed to increase
--min_cloud_upper   lower bound by which to filter out runs with low cloud_upper values
--hide_increases    boolean flag to indicate whether original or increased values are shown
"""

def visualize_threshold(results, rightsized_designs,
                        deficit_threshold=0.0, epsilon_threshold=0.0):
    """identify which microgrid designs satisfy the deficit and epsilon thresholds"""
    meets_threshold = []
    for microgrid in results:
        data = np.array(results[microgrid])
        meets_deficit_threshold = (data <= deficit_threshold).sum() / len(data)
        if HIDE_INCREASES: # index by original microgrid designs
            microgrid = rightsized_designs[microgrid]
        meets_threshold.append(
            [i for i in microgrid]+[meets_deficit_threshold >= 1-epsilon_threshold]
        )
    df_to_plot = pd.DataFrame(meets_threshold, columns=[
        defaults.DIESEL_GENERATOR,
        defaults.BATTERY,
        defaults.PHOTOVOLTAIC_PANEL,
        sensitivity_helpers.SENSITIVITY_MEETS_THRESHOLD,
    ])
    df_to_plot = df_to_plot.drop_duplicates()
    label = "epsilon="+str(epsilon_threshold)+",z="+str(deficit_threshold)
    label_latex = r"$\epsilon = "+str(epsilon_threshold)+\
                        ", \overline{z} = "+str(deficit_threshold)+"$"
    if len(df_to_plot.loc[df_to_plot[sensitivity_helpers.SENSITIVITY_MEETS_THRESHOLD] == True]):
        rightsize_plot.rightsize_to_plot(
            df = df_to_plot,
            threshold_label = label_latex,
            original_designs = HIDE_INCREASES,
            capacity_increase = INCREASE_LEVEL,
            filename = os.path.join(OUTDIR,label+".png"),
        )
    else:
        print("no points meet threshold: ", label)

def group_results_by_microgrid_design(df):
    """reformat results into one list per microgrid design
    return a dictionary of lists keyed by microgrid desigs"""
    results_cols = []
    for col in df.columns:
        if re.search("^\d+$",col):
            results_cols.append(col)
    groups = df.groupby(by=[
            defaults.DIESEL_GENERATOR,
            defaults.BATTERY,
            defaults.PHOTOVOLTAIC_PANEL,
        ],
    )
    results = dict()
    rightsized_designs = dict()
    for group_name, df_group in groups:
        rightsized_designs[group_name] = ( # map increases to original microgrid designs
            df_group[defaults.DIESEL_GENERATOR+sensitivity_helpers.SENSITIVITY_COMPONENT_ORIGINAL_TAG].unique()[0],
            df_group[defaults.BATTERY+sensitivity_helpers.SENSITIVITY_COMPONENT_ORIGINAL_TAG].unique()[0],
            df_group[defaults.PHOTOVOLTAIC_PANEL+sensitivity_helpers.SENSITIVITY_COMPONENT_ORIGINAL_TAG].unique()[0],
        )
        for index, row in df_group.iterrows():
            if group_name not in results:
                results[group_name] = row[results_cols].tolist()
            else:
                results[group_name].extend(row[results_cols].tolist())
    return results, rightsized_designs

PARSER = configargparse.ArgParser()
PARSER.add_argument("-c", "--config_file", is_config_file=True)
PARSER.add_argument("--file", required=True)
PARSER.add_argument("--outdir", required=True)
PARSER.add_argument("--increase_level", type=float, default=0.0)
PARSER.add_argument("--hide_increases", default=False, action="store_true")
PARSER.add_argument("--min_cloud_upper", type=float, default=0.0)
INCREASE_LEVEL = PARSER.parse_args().increase_level
HIDE_INCREASES = PARSER.parse_args().hide_increases
CLOUD_UPPER_MIN = PARSER.parse_args().min_cloud_upper
OUTDIR = os.path.join(
    PARSER.parse_args().outdir,
    "cloud_upper_min-"+str(CLOUD_UPPER_MIN),
    "increase-"+str(INCREASE_LEVEL),
    "" if INCREASE_LEVEL == 0.0 else ("hide-increases" if HIDE_INCREASES else "show-increases"),
)
DF = pd.read_csv(PARSER.parse_args().file)
TOL = 0.0001
DF = DF.loc[DF[sensitivity_helpers.SENSITIVITY_INCREASE_PERCENTAGE_TAG]>INCREASE_LEVEL-TOL]
DF = DF.loc[DF[sensitivity_helpers.SENSITIVITY_INCREASE_PERCENTAGE_TAG]<INCREASE_LEVEL+TOL]
DF = DF.loc[DF[run_helpers.WEATHER_CLOUD_UPPER]>CLOUD_UPPER_MIN]
DF = DF[DF[defaults.DIESEL_GENERATOR].notna()]
SIM_RESULTS, RIGHTSIZED_DESIGNS = group_results_by_microgrid_design(DF)
for DEFICIT_THRESHOLD in [0, .01, .05]:
    for EPSILON_THRESHOLD in [0, .01, .05, .10]:
        visualize_threshold(
            SIM_RESULTS,
            RIGHTSIZED_DESIGNS,
            deficit_threshold=DEFICIT_THRESHOLD,
            epsilon_threshold=EPSILON_THRESHOLD,
        )
