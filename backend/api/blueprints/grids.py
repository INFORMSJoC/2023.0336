from flask import Blueprint
from extensions import get_wrapper, get_using_post_wrapper, post_wrapper, update_name_description
import src.data.mysql.grids as database_grids

grids_blueprint = Blueprint('grids', __name__)

@grids_blueprint.route('/get/', methods=["POST"])
@get_using_post_wrapper(table_name="grid", action="read", pass_user_id=False, pass_table_name=False)
def get_single(request_dict):
    return database_grids.get_single(request_dict["id"])

@grids_blueprint.route('/get/', methods=["GET"])
@get_wrapper(pass_user_id=True)
def grids_get_0(user_id):
    return database_grids.get_all(user_id, 0)

@grids_blueprint.route('/get_sizing/', methods=["GET"])
@get_wrapper(pass_user_id=True)
def grids_get_1(user_id):
    return database_grids.get_all(user_id, 1)

@grids_blueprint.route('/update_name_description/', methods=['POST'])
@post_wrapper(table_name="grid", action="update", pass_user_id=True, pass_table_name=True)
def grid_update_name_description(request_dict, user_id, table_name):
    return update_name_description(request_dict, user_id, table_name)

@grids_blueprint.route('/update_add_components/', methods=['POST'])
@post_wrapper(table_name="grid", action="update")
def update_add_components(request_dict):
    return database_grids.update_add_components(
        grid_id=request_dict['id'], 
        components_dict={ c["id"]:c["quantity"] for c in request_dict['components'] },
    )

@grids_blueprint.route('/update_remove_components/', methods=['POST'])
@post_wrapper(table_name="grid", action="update")
def update_remove_components(request_dict):
    return database_grids.update_remove_components(
        grid_id=request_dict['id'], 
        components_list=[ c for c in request_dict['components'] ],
    )

@grids_blueprint.route('/add/', methods=['POST'])
@post_wrapper(table_name="grid", action="add", pass_user_id=True)
def add(request_dict, user_id):
    return database_grids.add_wrapper(
        user_id=user_id,
        grid_name=request_dict['name'], 
        description=request_dict['description'],
        is_sizing_template=request_dict['isSizingTemplate'],
    )

@grids_blueprint.route('/remove/', methods=['POST'])
@post_wrapper(table_name="grid", action="remove")
def remove(request_dict):
    return database_grids.remove(request_dict['id'])
