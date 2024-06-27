from flask import Blueprint
from extensions import get_wrapper
import src.data.mysql.energy_management_systems as database_energy_management_systems

energy_management_systems_blueprint = Blueprint('energy_management_systems', __name__)

@energy_management_systems_blueprint.route('/get/', methods=['GET'])
@get_wrapper()
def get():
    return database_energy_management_systems.get()
