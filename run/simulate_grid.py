#!/usr/bin/env python3

import os
import json
import pickle
from datetime import datetime
import random
import helpers as run_helpers
import src.grid.params as grid_params
from src.visualization import MetricPlots

"""
Script to run simulation

Set parameters below
"""

RANDOM_SEED = 0
random.seed(RANDOM_SEED)
WEATHER_PARAMS = {
    run_helpers.WEATHER_CLOUD_LOWER:0.0,
    run_helpers.WEATHER_CLOUD_UPPER:1.0,
    run_helpers.WEATHER_SUN_MEAN:0.5,
    run_helpers.WEATHER_SUN_STDEV:0.15,
    run_helpers.WEATHER_AUTOREGRESSIVE_PROPORTION:0.90,
}
WEATHER = run_helpers.weather_random_number_generator(WEATHER_PARAMS)
RUN_PARAMS = {
    run_helpers.RNG_SEED:RANDOM_SEED,
    run_helpers.LOAD_ID:1,
    run_helpers.GRID_ID:100,
    run_helpers.STARTDATETIME:datetime(year=2020, month=9, day=1, hour=0, minute=0),
    run_helpers.EXTEND_TIMEFRAME:2.002,
    run_helpers.ENERGY_MANAGEMENT_SYSTEM:grid_params.CONTROL_LOGIC_S,
    run_helpers.WEATHER_PARAMS:WEATHER_PARAMS,
    run_helpers.DISTURBANCE_ID:None,
    run_helpers.DISTURBANCE_DATETIME:None,
    run_helpers.REPAIR_ID:None,
}
RESULTS_DIR = os.path.join(
    run_helpers.get_system_root_dir(),
    str(RUN_PARAMS[run_helpers.LOAD_ID]),
    "simulate_grid",
    run_helpers.timestamp_now(),
)

# create results directory
os.makedirs(RESULTS_DIR)

# write params in human-readable format
with open(os.path.join(RESULTS_DIR,run_helpers.PARAMS_JSON_FILENAME), "wt", encoding="utf-8") as f:
    json.dump(RUN_PARAMS, f, indent=4, default=str)

# write params in machine-readable format
with open(os.path.join(RESULTS_DIR,run_helpers.PARAMS_PICKLE_FILENAME), 'wb') as f:
    pickle.dump(RUN_PARAMS, f)

SIM = run_helpers.initialize_simulation_object(RUN_PARAMS, WEATHER)
METRICS = SIM.run_simulation()
METRICS.results_to_csv(os.path.join(RESULTS_DIR,"sim.csv"))
PLOTS = MetricPlots(metrics=METRICS, dirpath=os.path.join(RESULTS_DIR))
PLOTS.all_plots()
print(METRICS.deficit_percentage())
