import configparser
from flask import Flask, jsonify
from flask_cors import CORS
import make_data
import src.data.mysql.mysql_helpers as database_helpers
from extensions import APIException, mail
from blueprints.components import components_blueprint
from blueprints.component_types import component_types_blueprint
from blueprints.grids import grids_blueprint
from blueprints.metadata import metadata_blueprint
from blueprints.powerloads import powerloads_blueprint
from blueprints.resilience.compute import resilience_compute_blueprint
from blueprints.resilience.disturbances import resilience_disturbances_blueprint
from blueprints.resilience.repairs import resilience_repairs_blueprint
from blueprints.simulate import simulate_blueprint
from blueprints.sizing.compute import sizing_compute_blueprint
from blueprints.sizing.results import sizing_results_blueprint

CONFIG_INI = configparser.ConfigParser()
CONFIG_INI.read("config.ini")
DEBUG = CONFIG_INI.getboolean("API","DEBUG")

if not database_helpers.exists() or database_helpers.num_tables() == 0:
    make_data.microgrid_database(
        drop_create_db=True,
        build_db=True,
        load_data=True,
        load_data_paper=False
    )

app = Flask(__name__)
CORS(app)

app.secret_key = CONFIG_INI.get("SECURITY","SECRET_KEY")

app.config["MAIL_SERVER"]= CONFIG_INI.get("MAIL","MAIL_SERVER")
app.config["MAIL_PORT"] = CONFIG_INI.get("MAIL","MAIL_PORT")
app.config["MAIL_USERNAME"] = CONFIG_INI.get("MAIL","MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = CONFIG_INI.get("MAIL","MAIL_PASSWORD", fallback=None)
app.config["MAIL_USE_TLS"] = CONFIG_INI.getboolean("MAIL","MAIL_USE_TLS")
app.config["MAIL_USE_SSL"] = CONFIG_INI.getboolean("MAIL","MAIL_USE_SSL")
app.config["MAIL_REPLY_TO"] = CONFIG_INI.get("MAIL","MAIL_REPLY_TO")
mail.init_app(app)

app.config['REDOC'] = {'spec_route': '/api/'}

@app.errorhandler(APIException)
def api_error(e):
    if DEBUG:
        print(e.message)
        print(e.traceback)
    return jsonify(e.to_dict()), e.status_code

app.register_blueprint(components_blueprint, url_prefix='/api/components')
app.register_blueprint(component_types_blueprint, url_prefix='/api/component_types')
app.register_blueprint(grids_blueprint, url_prefix='/api/grids')
app.register_blueprint(metadata_blueprint, url_prefix='/api/metadata')
app.register_blueprint(powerloads_blueprint, url_prefix='/api/powerloads')
app.register_blueprint(resilience_compute_blueprint, url_prefix='/api/resilience/compute')
app.register_blueprint(resilience_disturbances_blueprint, url_prefix='/api/resilience/disturbances')
app.register_blueprint(resilience_repairs_blueprint, url_prefix='/api/resilience/repairs')
app.register_blueprint(simulate_blueprint, url_prefix='/api/simulate')
app.register_blueprint(sizing_compute_blueprint, url_prefix='/api/sizing/compute')
app.register_blueprint(sizing_results_blueprint, url_prefix='/api/sizing/results')

if __name__ == "__main__":
    app.run(
        host=CONFIG_INI.get("API","HOST"),
        port=CONFIG_INI.get("API","PORT"),
        debug=CONFIG_INI.getboolean("API","DEBUG")
    )
