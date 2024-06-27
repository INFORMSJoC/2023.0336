from flask import Blueprint, request
from extensions import get_wrapper, post_wrapper, get_using_post_wrapper
import src.data.mysql.sizing as database_sizing

sizing_results_blueprint = Blueprint('sizing_results', __name__)

@sizing_results_blueprint.route('/get/', methods=["GET"])
@get_wrapper(pass_user_id=True)
def results_get(user_id):
    return database_sizing.MODEL_HELPERS.results_get(user_id)

@sizing_results_blueprint.route('/get/', methods=["POST"])
@get_using_post_wrapper(table_name="sizing", action="read")
def grids_get(request_dict):
    return database_sizing.grids_get(request_dict['id'], request_dict['display_all'], request_dict['deficit_max'])

@sizing_results_blueprint.route('/remove/', methods=['POST'])
@post_wrapper(table_name="sizing", action="remove")
def remove(request_dict):
    return database_sizing.MODEL_HELPERS.remove(request_dict['id'])

@sizing_results_blueprint.route('/save_to_grids/', methods=["POST"])
@post_wrapper(table_name="sizing", action="read", pass_user_id=True, pass_table_name=False)
def result_save_to_grids(request_dict, user_id):
    return database_sizing.result_save_to_grids(user_id, request_dict['sizing_grid_id'])
