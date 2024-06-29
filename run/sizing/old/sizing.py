#!/usr/bin/env python3

import os
import json
import pickle
from datetime import datetime
import random
import run.helpers as run_helpers
import src.grid.params as grid_params
from src.models import Rightsize
from src.visualization import rightsize_plot

"""
Script to run microgrid rightsizing method from Reich & Oriti (2021)
(limited to diesel, photovoltaic, battery).
Replaced with more general sizing method in sizing.py,
but code maintained for comparison purposes only.
"""

STEP_SIZE_BATTERY = 5
STEP_SIZE_DIESEL = 5
STEP_SIZE_PHOTOVOLTAIC = 5

RANDOM_SEED = 0
random.seed(RANDOM_SEED)
WEATHER_PARAMS = {
    run_helpers.WEATHER_CLOUD_LOWER:0.5,
    run_helpers.WEATHER_CLOUD_UPPER:0.5,
    run_helpers.WEATHER_SUN_MEAN:0.5,
    run_helpers.WEATHER_SUN_STDEV:0.0,
    run_helpers.WEATHER_AUTOREGRESSIVE_PROPORTION:0.90,
}
WEATHER = run_helpers.weather_random_number_generator(WEATHER_PARAMS)

# edit run parameters
RUN_SIM = True # set to False when replotting rightsized points with zoom window
RUN_PARAMS = {
    run_helpers.RNG_SEED:RANDOM_SEED,
    run_helpers.LOAD_ID:1,
    run_helpers.GRID_ID:250,
    run_helpers.STARTDATETIME:datetime(year=2020, month=9, day=1, hour=0, minute=0),
    run_helpers.EXTEND_TIMEFRAME:0.0,
    run_helpers.ENERGY_MANAGEMENT_SYSTEM:grid_params.CONTROL_LOGIC_S,
    "step_size_battery":STEP_SIZE_BATTERY,
    "step_size_diesel":STEP_SIZE_DIESEL,
    "step_size_photovoltaic":STEP_SIZE_PHOTOVOLTAIC,
    run_helpers.WEATHER_PARAMS:WEATHER_PARAMS,
    run_helpers.DISTURBANCE_ID:None,
    run_helpers.DISTURBANCE_DATETIME:None,
    run_helpers.REPAIR_ID:None,
}
RESULTS_DIR = os.path.join(
    run_helpers.get_system_root_dir(),
    str(RUN_PARAMS[run_helpers.LOAD_ID]),
    "rightsize",
    "b"+str(int(STEP_SIZE_BATTERY)) \
        +"_dg"+str(STEP_SIZE_DIESEL)
        +"_pv"+str(STEP_SIZE_PHOTOVOLTAIC),
    run_helpers.timestamp_now(),
)

# create results directory
os.makedirs(RESULTS_DIR, exist_ok=True)

# write params in human-readable format
with open(os.path.join(RESULTS_DIR,run_helpers.PARAMS_JSON_FILENAME), "wt", encoding="utf-8") as f:
    json.dump(RUN_PARAMS, f, indent=4, default=str)

# write params in machine-readable format
with open(os.path.join(RESULTS_DIR,run_helpers.PARAMS_PICKLE_FILENAME), 'wb') as f:
    pickle.dump(RUN_PARAMS, f)

CSV = os.path.join(RESULTS_DIR, "rightsize.csv")
if RUN_SIM:
    SIM = run_helpers.initialize_simulation_object(RUN_PARAMS, WEATHER)
    RIGHTSIZE = Rightsize(
        sim = SIM, 
        step_size_b = STEP_SIZE_BATTERY,
        step_size_dg = STEP_SIZE_DIESEL,
        step_size_pv = STEP_SIZE_PHOTOVOLTAIC,
        dirpath = RESULTS_DIR,
    )
    RIGHTSIZE.to_csv(CSV)
    PNG = os.path.join(RESULTS_DIR, "rightsize.png")
    rightsize_plot.rightsize_to_plot(
        inputfilename=CSV,
        battery_max=None,
        photovoltaic_max=None,
        preview=False,
        filename=PNG,
    )
else:
    # edit zoom window parameters below
    PNG_ZOOM = os.path.join(RESULTS_DIR, "rightsize_zoom.png")
    rightsize_plot.rightsize_to_plot(
        inputfilename=CSV,
        battery_max=100000,
        photovoltaic_min=4900,
        photovoltaic_max=5100,
        preview=False,
        filename=PNG_ZOOM,
    )
