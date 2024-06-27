from flask import Blueprint, request
from extensions import get_wrapper, post_wrapper
import src.data.mysql.sizing as database_sizing
import src.data.mysql.users as database_users

sizing_results_blueprint = Blueprint('sizing_results', __name__)

@sizing_results_blueprint.route('/get/', methods=["GET"])
@get_wrapper(pass_user_id=True)
def runs_get(user_id):
    return database_sizing.runs_get(user_id)

@sizing_results_blueprint.route('/get/', methods=["POST"])
@get_wrapper(pass_user_id=True)
def grids_get(user_id):
    sizing_id = request.get_json()['id']
    if not database_users.has_permissions(user_id, sizing_id, "sizing", "read"):
        raise ValueError("User does not have permission to access sizing run")
    return database_sizing.grids_get(sizing_id, request.get_json()['display_all'], request.get_json()['deficit_max'])


@sizing_results_blueprint.route('/remove/', methods=['POST'])
@post_wrapper(table_name="sizing", action="remove")
def remove(request_dict):
    return database_sizing.remove(request_dict['id'])

@sizing_results_blueprint.route('/save_to_grids/', methods=["POST"])
@post_wrapper(table_name="sizing", action="read", pass_user_id=True, pass_table_name=False)
def result_save_to_grids(request_dict, user_id):
    return database_sizing.result_save_to_grids(user_id, request_dict['sizing_grid_id'])
