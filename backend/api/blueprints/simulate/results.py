from flask import Blueprint, request
from extensions import get_wrapper, post_wrapper, get_using_post_wrapper
import src.data.mysql.simulate as database_simulate

simulate_results_blueprint = Blueprint('simulate_results', __name__)

@simulate_results_blueprint.route('/get/', methods=["GET"])
@get_wrapper(pass_user_id=True)
def results_get(user_id):
    return database_simulate.MODEL_HELPERS.results_get(user_id)

@simulate_results_blueprint.route('/get/', methods=["POST"])
@get_using_post_wrapper(table_name="simulate", action="read")
def result_get(request_dict):
    return database_simulate.MODEL_HELPERS.result_get(request_dict['id'])

@simulate_results_blueprint.route('/remove/', methods=['POST'])
@post_wrapper(table_name="simulate", action="remove")
def remove(request_dict):
    return database_simulate.MODEL_HELPERS.remove(id=request_dict['id'])

@simulate_results_blueprint.route('/metrics/', methods=["POST"])
@get_using_post_wrapper(table_name="simulate", action="read")
def simulate_result(request_dict):
    return database_simulate.metrics_get(request_dict['id'])
