import os
import configparser
from flask import Flask, jsonify
from flask_cors import CORS
from make import make_data
from src.data.mysql import mysql_authentication, mysql_microgrid, mysql_weather
from extensions import APIException, mail
from blueprints.energy_management_systems import energy_management_systems_blueprint
from blueprints.components import components_blueprint
from blueprints.component_types import component_types_blueprint
from blueprints.grids import grids_blueprint
from blueprints.locations import locations_blueprint
from blueprints.metadata import metadata_blueprint
from blueprints.powerloads import powerloads_blueprint
from blueprints.simulate.compute import simulate_compute_blueprint
from blueprints.simulate.results import simulate_results_blueprint
from blueprints.sizing.compute import sizing_compute_blueprint
from blueprints.sizing.results import sizing_results_blueprint

CONFIG_INI = configparser.ConfigParser()
CONFIG_INI.read("config.ini")
DEBUG = CONFIG_INI.getboolean("API","DEBUG")

CONFIG_INI_GLOBAL = configparser.ConfigParser()
CONFIG_INI_GLOBAL.read(os.path.join(os.path.dirname(os.getcwd()),"config.ini"))

if not mysql_authentication.DB.exists() or mysql_authentication.DB.num_tables() == 0:
    make_data.authentication_database(
        drop_create_db=True,
        load_data_dev=True,
    )

if not mysql_microgrid.DB.exists() or mysql_microgrid.DB.num_tables() == 0:
    make_data.microgrid_database(
        drop_create_db=True,
        load_data_dev=False,
    )

if not mysql_weather.DB.exists() or mysql_weather.DB.num_tables() == 0:
    make_data.weather_database(drop_create_db=True)

app = Flask(__name__)
CORS(app)

app.secret_key = CONFIG_INI_GLOBAL.get("SECURITY","SECRET_KEY")

app.config["MAIL_SERVER"]= CONFIG_INI_GLOBAL.get("MAIL","MAIL_SERVER")
app.config["MAIL_PORT"] = CONFIG_INI_GLOBAL.get("MAIL","MAIL_PORT")
app.config["MAIL_USERNAME"] = CONFIG_INI_GLOBAL.get("MAIL","MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = CONFIG_INI_GLOBAL.get("MAIL","MAIL_PASSWORD", fallback=None)
app.config["MAIL_USE_TLS"] = CONFIG_INI_GLOBAL.getboolean("MAIL","MAIL_USE_TLS")
app.config["MAIL_USE_SSL"] = CONFIG_INI_GLOBAL.getboolean("MAIL","MAIL_USE_SSL")
app.config["MAIL_REPLY_TO"] = CONFIG_INI_GLOBAL.get("MAIL","MAIL_REPLY_TO")
mail.init_app(app)

app.config['REDOC'] = {'spec_route': '/api/'}

@app.errorhandler(APIException)
def api_error(e):
    if DEBUG:
        print(e.message, flush=True)
        print(e.traceback, flush=True)
    return jsonify(e.to_dict()), e.status_code

app.register_blueprint(energy_management_systems_blueprint, url_prefix='/api/energy_management_systems')
app.register_blueprint(components_blueprint, url_prefix='/api/components')
app.register_blueprint(component_types_blueprint, url_prefix='/api/component_types')
app.register_blueprint(grids_blueprint, url_prefix='/api/grids')
app.register_blueprint(locations_blueprint, url_prefix='/api/locations')
app.register_blueprint(metadata_blueprint, url_prefix='/api/metadata')
app.register_blueprint(powerloads_blueprint, url_prefix='/api/powerloads')
app.register_blueprint(simulate_compute_blueprint, url_prefix='/api/simulate/compute')
app.register_blueprint(simulate_results_blueprint, url_prefix='/api/simulate/results')
app.register_blueprint(sizing_compute_blueprint, url_prefix='/api/sizing/compute')
app.register_blueprint(sizing_results_blueprint, url_prefix='/api/sizing/results')

if __name__ == "__main__":
    app.run(
        host=CONFIG_INI.get("API","HOST"),
        port=CONFIG_INI.get("API","PORT"),
        debug=CONFIG_INI.getboolean("API","DEBUG")
    )
