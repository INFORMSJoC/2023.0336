from flask import Blueprint, jsonify
from extensions import get_wrapper
import src.data.mysql.mysql_helpers as database_helpers

metadata_blueprint = Blueprint('metadata', __name__)

@metadata_blueprint.route('/quotas/', methods=['GET'])
@get_wrapper()
def user_quota():
    return database_helpers.user_quota()
