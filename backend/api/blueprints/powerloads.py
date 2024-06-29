from flask import Blueprint
from extensions import get_wrapper, get_using_post_wrapper, post_wrapper, post_then_get_wrapper, update_name_description
import src.data.mysql.powerloads as database_powerloads

powerloads_blueprint = Blueprint('powerloads', __name__)

@powerloads_blueprint.route('/get/', methods=["GET"])
@get_wrapper(pass_user_id=True)
def get_all(user_id):
    return database_powerloads.get_all(user_id)

@powerloads_blueprint.route("/get/", methods=["POST"])
@get_using_post_wrapper(table_name="powerload", action="read")
def get_single(request_dict):
    return database_powerloads.get_single(request_dict['id'])

@powerloads_blueprint.route('/update/', methods=['POST'])
@post_wrapper(table_name="powerload", action="update", pass_user_id=True, pass_table_name=True)
def powerload_update(request_dict, user_id, table_name):
    if "image" in request_dict:
        return database_powerloads.update_image(
            id = request_dict['id'],
            image = request_dict['image'],
        )
    return update_name_description(request_dict, user_id, table_name)

@powerloads_blueprint.route('/add/', methods=['POST'])
@post_then_get_wrapper(table_name="powerload", action="add", pass_user_id=True)
def add(request_dict, user_id):
    return database_powerloads.add(
        user_id = user_id,
        name = request_dict['name'],
        data = request_dict['data'],
        description = request_dict['description'],
    )

@powerloads_blueprint.route('/remove/', methods=['POST'])
@post_wrapper(table_name="powerload", action="remove")
def remove(request_dict):
    return database_powerloads.remove(request_dict['id'])
