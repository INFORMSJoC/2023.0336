from dotenv import dotenv_values
import configparser
from flask import Flask
from flask_cors import CORS
from extensions import mysql, mail
from blueprints.authentication import authentication_blueprint
from blueprints.toplevel import toplevel_blueprint
from blueprints.tools import tools_blueprint
from blueprints.sizing import sizing_blueprint
from blueprints.resilience import resilience_blueprint

CONFIG_ENV = dotenv_values("config.env")
CONFIG_INI = configparser.ConfigParser()
CONFIG_INI.read("config.ini")
DEBUG = CONFIG_INI.getboolean("FRONTEND","DEBUG")

app = Flask(__name__) 
CORS(app)
if DEBUG: app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

app.secret_key = CONFIG_INI.get("SECURITY","SECRET_KEY")

app.config["MAIL_SERVER"]= CONFIG_INI.get("MAIL","MAIL_SERVER")
app.config["MAIL_PORT"] = CONFIG_INI.get("MAIL","MAIL_PORT")
app.config["MAIL_USERNAME"] = CONFIG_INI.get("MAIL","MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = CONFIG_INI.get("MAIL","MAIL_PASSWORD", fallback=None)
app.config["MAIL_USE_TLS"] = CONFIG_INI.getboolean("MAIL","MAIL_USE_TLS")
app.config["MAIL_USE_SSL"] = CONFIG_INI.getboolean("MAIL","MAIL_USE_SSL")
app.config["MAIL_REPLY_TO"] = CONFIG_INI.get("MAIL","MAIL_REPLY_TO")
mail.init_app(app)

CONFIG_ENV = dotenv_values("config.env")
app.config["MYSQL_HOST"] = CONFIG_ENV["MYSQL_HOST"]
app.config["MYSQL_USER"] = CONFIG_ENV["MYSQL_USER"]
app.config["MYSQL_PASSWORD"] = CONFIG_ENV["MYSQL_PASSWORD"]
app.config["MYSQL_DB"] = CONFIG_ENV["MYSQL_DATABASE"]
app.config["MYSQL_PORT"] = int(CONFIG_ENV["MYSQL_PORT"])
mysql.init_app(app)

app.register_blueprint(authentication_blueprint, url_prefix="/account")
app.register_blueprint(toplevel_blueprint, url_prefix="/")
app.register_blueprint(tools_blueprint, url_prefix="/tools/")
app.register_blueprint(sizing_blueprint, url_prefix="/tools/sizing/")
app.register_blueprint(resilience_blueprint, url_prefix="/tools/resilience/")

if __name__ == "__main__":
    app.run(
        host=CONFIG_INI.get("FRONTEND","HOST"),
        port=CONFIG_INI.get("FRONTEND","PORT"),
        debug=DEBUG
    )
