from flask import Blueprint, jsonify
from extensions import get_wrapper
import src.data.mysql.components as database_components

component_types_blueprint = Blueprint('component_types', __name__)

@component_types_blueprint.route('/get/', methods=['GET'])
@get_wrapper()
def get():
    return database_components.types_get()
