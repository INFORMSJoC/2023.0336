from flask import Blueprint
from extensions import get_wrapper, post_wrapper, update_name_description
import src.data.mysql.resilience as database_resilience

resilience_repairs_blueprint = Blueprint('repairs', __name__)

@resilience_repairs_blueprint.route('/get/')
@get_wrapper(pass_user_id=True)
def repair_get(user_id):
    return database_resilience.disturbances_repairs_get(user_id, "repair")

@resilience_repairs_blueprint.route('/update_name_description/', methods=['POST'])
@post_wrapper(table_name="repair", action="update", pass_user_id=True, pass_table_name=True)
def repair_update_name_description(request_dict, user_id, table_name):
    return update_name_description(request_dict, user_id, table_name)

@resilience_repairs_blueprint.route('/update_attributes/', methods=['POST'])
@post_wrapper(table_name="repair", action="update")
def repair_update_attributes(request_dict):
    return database_resilience.disturbance_repair_update_attributes(
        id=request_dict['id'],
        specs=request_dict['attributes'],
        table_name="repair",
    )

@resilience_repairs_blueprint.route('/add/', methods=['POST'])
@post_wrapper(table_name="repair", action="add", pass_user_id=True)
def repair_add(request_dict, user_id):
    return database_resilience.disturbance_repair_add(
        user_id=user_id,
        name=request_dict['name'], 
        description=request_dict['description'], 
        specifications=request_dict['attributes'], 
        table_name="repair",
    )

@resilience_repairs_blueprint.route('/remove/', methods=['POST'])
@post_wrapper(table_name="repair", action="remove")
def repair_remove(request_dict):
    return database_resilience.disturbance_repair_remove(request_dict['id'], "repair")
