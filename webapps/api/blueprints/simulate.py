from flask import Blueprint, request, Response
from dateutil import parser
import csv
import io
import random
from extensions import get_wrapper, authorization_required, APIException
import run.helpers as run_helpers
from src.utils import helpers
import src.grid.params as grid_params
import src.data.mysql.users as database_users

def compute(user_id):
    request_dict = request.get_json()
    inputs = {}
    inputs[run_helpers.STARTDATETIME] = request_dict[run_helpers.STARTDATETIME]
    try:
        date_time = parser.parse(inputs[run_helpers.STARTDATETIME])
    except Exception as error:
        raise ValueError("startdatetime not valid:\n"+str(error))
    inputs[run_helpers.LOAD_ID] = request_dict[run_helpers.LOAD_ID]
    inputs[run_helpers.GRID_ID] = request_dict[run_helpers.GRID_ID]
    try:
        if not database_users.has_permissions(user_id, inputs[run_helpers.GRID_ID], "grid", "read"):
            raise ValueError("User does not have permission to access grid")
        if not database_users.has_permissions(user_id, inputs[run_helpers.LOAD_ID], "powerload", "read"):
            raise ValueError("User does not have permission to access load")
    except Exception as error:
        raise RuntimeError("Error in simulation blueprint checking user permissions\n"+str(error))
    
    random.seed(0)
    weather = run_helpers.weather_random_number_generator(None, deterministic=True)
    run_params = {
        run_helpers.GRID_ID: inputs[run_helpers.GRID_ID],
        run_helpers.LOAD_ID: inputs[run_helpers.LOAD_ID],
        run_helpers.STARTDATETIME:date_time,
        run_helpers.ENERGY_MANAGEMENT_SYSTEM:grid_params.CONTROL_LOGIC_S
    }
    sim = run_helpers.initialize_simulation_object(run_params, weather)
    metrics = sim.run_simulation()
    return inputs, metrics.results_to_csv(round_output=True)


simulate_blueprint = Blueprint('simulate', __name__)

@simulate_blueprint.route('/csv/', methods=["POST"])
@authorization_required
def simulate_grid_to_csv(user_id):
    try:
        parameters, csv_data = compute(user_id)
        csv_params = ""
        for key, val in parameters.items():
            csv_params += key + "," + str(val) + "\n"
    except Exception as error:
        raise APIException("simulate_grid_to_csv\n"+str(error), status_code=500)
    return Response(
        csv_params+"\n"+csv_data,
        mimetype="text/csv",
        headers={"Content-disposition":"attachment; filename=simulate_grid.csv"}
    )

@simulate_blueprint.route('/compute/', methods=["POST"])
@get_wrapper(pass_user_id=True)
def simulate_grid_to_json(user_id):
    parameters, csv_data = compute(user_id)
    list_of_dicts = list(csv.DictReader(io.StringIO(csv_data)))
    list_of_dicts = [helpers.float_values(i) for i in list_of_dicts]
    return {'parameters':parameters, 'output':list_of_dicts}
