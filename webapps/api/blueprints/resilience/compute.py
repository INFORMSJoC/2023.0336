from flask import Blueprint, request, jsonify
from datetime import datetime
from dateutil import parser
import configparser
import csv
import io
import random
from extensions import get_wrapper, APIException
import run.helpers as run_helpers
from src.utils import helpers
import src.grid.params as grid_params
import src.data.mysql.users as database_users

_CONFIG_INI = configparser.ConfigParser()
_CONFIG_INI.read("config.ini")
_MAX_NUM_RUNS = _CONFIG_INI.getint("QUOTA","RESILIENCE_RUNS")
_NUM_RUNS_KEY = "num_runs"

def compute(user_id):
    request_dict = request.get_json()
    inputs = {}
    inputs[_NUM_RUNS_KEY] = int(request_dict[_NUM_RUNS_KEY]) \
        if _NUM_RUNS_KEY in request_dict else 1
    num_runs = inputs[_NUM_RUNS_KEY]
    if num_runs > _MAX_NUM_RUNS:
        raise ValueError("num runs = {0} exceeds allowed limit of {1}".format(num_runs, _MAX_NUM_RUNS))
    inputs[run_helpers.STARTDATETIME] = request_dict[run_helpers.STARTDATETIME]
    try:
        date_time = parser.parse(inputs[run_helpers.STARTDATETIME])
    except Exception as error:
        raise ValueError("startdatetime not defined\n"+str(error))
    inputs[run_helpers.LOAD_ID] = request_dict[run_helpers.LOAD_ID]
    inputs[run_helpers.GRID_ID] = request_dict[run_helpers.GRID_ID]
    inputs[run_helpers.DISTURBANCE_ID] = request_dict[run_helpers.DISTURBANCE_ID]
    inputs[run_helpers.DISTURBANCE_DATETIME] = request_dict[run_helpers.DISTURBANCE_DATETIME]
    try:
        disturbance_date_time = parser.parse(inputs[run_helpers.DISTURBANCE_DATETIME])
    except Exception as error:
        raise ValueError("disturbance datetime not defined\n"+str(error))
    inputs[run_helpers.REPAIR_ID] = request_dict[run_helpers.REPAIR_ID]
    inputs[run_helpers.EXTEND_TIMEFRAME] = float(request_dict[run_helpers.EXTEND_TIMEFRAME]) \
        if run_helpers.EXTEND_TIMEFRAME in request_dict else 1.0
    try:
        for table in [
            (run_helpers.GRID_ID, "grid"),
            (run_helpers.LOAD_ID, "powerload"),
            (run_helpers.DISTURBANCE_ID, "disturbance"),
            (run_helpers.REPAIR_ID, "repair"),
        ]:
            if not database_users.has_permissions(user_id, inputs[table[0]], table[1], "read"):
                raise ValueError("User does not have permission to access {0}".format(table[1]))
    except Exception as error:
        raise RuntimeError("Error in simulation blueprint checking user permissions\n"+str(error))

    random.seed(0)
    weather_params = {
        run_helpers.WEATHER_CLOUD_LOWER:0.0,
        run_helpers.WEATHER_CLOUD_UPPER:1.0,
        run_helpers.WEATHER_SUN_MEAN:0.5,
        run_helpers.WEATHER_SUN_STDEV:0.15,
        run_helpers.WEATHER_AUTOREGRESSIVE_PROPORTION:0.90,
    }
    weather = run_helpers.weather_random_number_generator(weather_params)
    run_params = {
        run_helpers.GRID_ID:inputs[run_helpers.GRID_ID],
        run_helpers.LOAD_ID:inputs[run_helpers.LOAD_ID],
        run_helpers.STARTDATETIME:date_time,
        run_helpers.ENERGY_MANAGEMENT_SYSTEM:grid_params.CONTROL_LOGIC_S,
        run_helpers.DISTURBANCE_ID:inputs[run_helpers.DISTURBANCE_ID],
        run_helpers.DISTURBANCE_DATETIME:disturbance_date_time,
        run_helpers.REPAIR_ID:inputs[run_helpers.REPAIR_ID],
        run_helpers.EXTEND_TIMEFRAME:inputs[run_helpers.EXTEND_TIMEFRAME],
        run_helpers.WEATHER_PARAMS:weather_params,
        _NUM_RUNS_KEY:num_runs,
    }
    sim = run_helpers.initialize_simulation_object(run_params, weather)
    metrics = sim.run_simulation()
    return inputs, metrics.results_to_csv(round_output=True)


resilience_compute_blueprint = Blueprint("resilience", __name__)

@resilience_compute_blueprint.route("/run/", methods=["POST"])
@get_wrapper(pass_user_id=True)
def resilience(user_id):
    parameters, csv_data = compute(user_id)
    list_of_dicts = list(csv.DictReader(io.StringIO(csv_data)))
    list_of_dicts = [helpers.float_values(i) for i in list_of_dicts]
    return { "parameters":parameters, "output":list_of_dicts }
