from flask import Blueprint
from extensions import get_wrapper
from src.data.mysql import mysql_microgrid

metadata_blueprint = Blueprint('metadata', __name__)

@metadata_blueprint.route('/quotas/', methods=['GET'])
@get_wrapper()
def user_quota():
    return mysql_microgrid.user_quota()
