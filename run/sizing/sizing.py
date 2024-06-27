#!/usr/bin/env python3

import random
import os
import configparser
import configargparse
import json
import pickle
import run.helpers as run_helpers
from datetime import datetime
import src.grid.params as grid_params
from src.models.sizing.sizing import Sizing
import src.data.mysql.sizing as database_sizing
import src.data.mysql.users as database_users

"""
Script to run DOE sizing method

Command-line inputs:
-c --config_file        config file with command-line options
-n --num_levels         number of levels for each DER type, to which DOE levels are mapped
-r --run_id             database id of run info
-g --grid_id            database id of microgrid template
-p --powerload_id       database id of powerload profile
-a --algorithm          algorithm to run
--debug                 run debug mode
"""

CONFIG_INI = configparser.ConfigParser()
CONFIG_INI.read("config.ini")
FRONTEND_URL = CONFIG_INI.get("FRONTEND","URL",fallback="")
ADMIN_EMAIL = CONFIG_INI.get("MAIL","MAIL_USERNAME",fallback="")

PARSER = configargparse.ArgParser()
PARSER.add_argument("-c", "--config_file", is_config_file=True)
PARSER.add_argument("-n","--num_levels", type=int, default=11)
PARSER.add_argument("-r","--run_id", type=int)
PARSER.add_argument("-g","--grid_id", type=int)
PARSER.add_argument("-p","--powerload_id", type=int)
PARSER.add_argument("-s","--startdatetime", type=str, default=None, help='Start date and time (format: YYYY-MM-DD_HH:MM:SS)')
PARSER.add_argument("-a","--algorithm", type=str, default="heuristic")
PARSER.add_argument("--debug", dest="debug", action="store_true")
NUM_LEVELS = PARSER.parse_args().num_levels
RUN_ID = PARSER.parse_args().run_id
if RUN_ID is not None:
    RUN_INFO = database_sizing.run_get(RUN_ID)
    GRID_ID = RUN_INFO["gridId"]
    POWERLOAD_ID = RUN_INFO["powerloadId"]
    STARTDATETIME = RUN_INFO["startdatetime"]
else:
    GRID_ID = PARSER.parse_args().grid_id
    POWERLOAD_ID = PARSER.parse_args().powerload_id
    try:
        STARTDATETIME = datetime.strptime(PARSER.parse_args().startdatetime, '%Y-%m-%d_%H:%M:%S')
    except ValueError:
        raise ValueError("Invalid startdatetime format. Please use YYYY-MM-DD_HH:MM:SS.")
ALGORITHM = PARSER.parse_args().algorithm
DEBUG = PARSER.parse_args().debug

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
RUN_PARAMS = {
    run_helpers.RNG_SEED:RANDOM_SEED,
    run_helpers.LOAD_ID:POWERLOAD_ID,
    run_helpers.GRID_ID:GRID_ID,
    run_helpers.STARTDATETIME:STARTDATETIME,
    run_helpers.EXTEND_TIMEFRAME:0.0,
    run_helpers.ENERGY_MANAGEMENT_SYSTEM:grid_params.CONTROL_LOGIC_S,
    run_helpers.WEATHER_PARAMS:WEATHER_PARAMS,
    run_helpers.DISTURBANCE_ID:None,
    run_helpers.DISTURBANCE_DATETIME:None,
    run_helpers.REPAIR_ID:None,
    "debug":DEBUG,
    "num_levels":NUM_LEVELS,
    "algorithm":ALGORITHM,
}

RESULTS_DIR = None if RUN_ID is not None else os.path.join(
    run_helpers.get_system_root_dir(),
    str(RUN_PARAMS[run_helpers.LOAD_ID]),
    "sizing",
    run_helpers.timestamp_now(),
)
if RESULTS_DIR is not None: 
    os.makedirs(RESULTS_DIR)
    with open(os.path.join(RESULTS_DIR,run_helpers.PARAMS_JSON_FILENAME), "wt", encoding="utf-8") as f:
        json.dump(RUN_PARAMS, f, indent=4, default=str)
    with open(os.path.join(RESULTS_DIR,run_helpers.PARAMS_PICKLE_FILENAME), 'wb') as f:
        pickle.dump(RUN_PARAMS, f)

SIM = run_helpers.initialize_simulation_object(RUN_PARAMS, WEATHER)
SIZING = Sizing(SIM, NUM_LEVELS)
recipient_email = None if RUN_ID is None else database_users.get_run_email("sizing", RUN_ID)
try:
    SIZING.run(algorithm=ALGORITHM, results_dir=RESULTS_DIR, database_id=RUN_ID, debug=DEBUG)
    if recipient_email is not None:
        run_helpers.email(
            recipient_email=recipient_email,
            subject="Sizing run complete: id = "+str(RUN_ID),
            message_body="<a href=\""+FRONTEND_URL+"/tools/sizing/results/"+str(RUN_ID)+"\">View results</a>"
        )
except Exception as error:
    if recipient_email is not None:
        run_helpers.email(
            recipient_email=recipient_email,
            subject="Sizing run failed: id = "+str(RUN_ID),
            message_body="Contact <a href=\"mailto:"+ADMIN_EMAIL+"\">"+ADMIN_EMAIL+"</a> for more info."
        )
    raise RuntimeError("Error in sizing run\n"+str(error))
