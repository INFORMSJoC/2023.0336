from flask import Blueprint
from extensions import get_wrapper, post_wrapper, update_name_description
import src.data.mysql.components as database_components

components_blueprint = Blueprint('components', __name__)

@components_blueprint.route('/get/', methods=["GET"])
@get_wrapper(pass_user_id=True)
def get_all(user_id):
    return database_components.get_all(user_id)

@components_blueprint.route('/update_name_description/', methods=['POST'])
@post_wrapper(table_name="component", action="update", pass_user_id=True, pass_table_name=True)
def component_update_name_description(request_dict, user_id, table_name):
    return update_name_description(request_dict, user_id, table_name)

@components_blueprint.route('/update_attributes/', methods=['POST'])
@post_wrapper(table_name="component", action="update")
def update_attributes(request_dict):
    return database_components.update_attributes(
        component_id=request_dict['id'],
        component_specs=request_dict['attributes']
    )

@components_blueprint.route('/add/', methods=['POST'])
@post_wrapper(table_name="component", action="add", pass_user_id=True)
def add(request_dict, user_id):
    return database_components.add_wrapper(
        user_id=user_id,
        type_id=request_dict['type'],
        name=request_dict['name'], 
        description=request_dict['description'], 
        specifications=request_dict['attributes'], 
    )

@components_blueprint.route('/remove/', methods=['POST'])
@post_wrapper(table_name="component", action="remove")
def remove(request_dict):
    return database_components.remove(request_dict['id'])
