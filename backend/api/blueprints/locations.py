from flask import Blueprint
from extensions import get_wrapper, get_using_post_wrapper
import src.data.mysql.locations as database_locations

locations_blueprint = Blueprint('locations', __name__)

@locations_blueprint.route('/get/', methods=["GET"])
@get_wrapper()
def get_countries():
    return database_locations.get_countries()

@locations_blueprint.route('/get/', methods=["POST"])
@get_using_post_wrapper(table_name=None, action=None)
def get_regions_or_names(request_dict):
    if "id" in request_dict:
        return database_locations.get_info(request_dict["id"])
    if "region" in request_dict:
        return database_locations.get_names(request_dict["country"], request_dict["region"])
    return database_locations.get_regions(request_dict["country"])
