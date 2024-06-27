import os
import sys
import configparser
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
import random
from functools import partial
from src.grid import Grid, Disturbance
from src.models import Simulation, Weather
from src.utils import helpers
import src.data.mysql.grids as database_grids
import src.data.mysql.resilience as database_resilience

"""
Helpers for all run scripts
"""

_CONFIG_INI = configparser.ConfigParser()
_CONFIG_INI.read("config.ini")
_PV_CHARS_FILE = os.path.join(os.getcwd(),_CONFIG_INI.get("DER", "PV_CHARS_FILE"))

RNG_SEED = "random_number_generator_seed"
LOAD_ID = "load_id"
GRID_ID = "grid_id"
DISTURBANCE_DATETIME = "disturbance_datetime"
DISTURBANCE_ID = "disturbance_id"
STARTDATETIME = "startdatetime"
EXTEND_TIMEFRAME = "extend_timeframe_proportion"
REPAIR_ID = "repair_id"
ENERGY_MANAGEMENT_SYSTEM = "energy_management_system"
WEATHER_PARAMS = "weather-generation-info"
WEATHER_CLOUD_LOWER = "cloud_lower"
WEATHER_CLOUD_UPPER = "cloud_upper"
WEATHER_SUN_MEAN = "sun_mean"
WEATHER_SUN_STDEV = "sun_stdev"
WEATHER_AUTOREGRESSIVE_PROPORTION = "autoregressive_proportion"
PARAMS_JSON_FILENAME = "params.json"
PARAMS_PICKLE_FILENAME = "params.pkl"

def initialize_simulation_object(run_param_dict, weather):
    """
    Initialize simulation object according to input run parameter dictionary
    """
    grid = Grid(diesel_level=sys.float_info.max)
    try:
        components = database_grids.get_components(run_param_dict[GRID_ID], objectFlag=True)
    except Exception as error:
        raise Exception("Error in initialize_simulation_object retrieving components:\n"+str(error))
    if len(components) == 0:
        raise ValueError("Cannot initialize_simulation_object on a microgrid with no components")
    # TEMPORARY CODE UNTIL PHOTOVOLTAIC MODEL IS UPDATED TO USE HISTORICAL DATA
    pv_chars = helpers.get_json_data(_PV_CHARS_FILE)
    for c in components:
        if c.__class__.__name__ == "SolarPhotovoltaicPanel":
            c.update_photovoltaic_characteristics(
                helpers.get_profile(pv_chars, "capacity"),
                helpers.get_profile(pv_chars, "sine_width"),
            )
    grid.initialize_components(components)
    if DISTURBANCE_ID in run_param_dict and run_param_dict[DISTURBANCE_ID] is not None:
        try:
            disturbance_probs = database_resilience.disturbance_repair_values_get(run_param_dict[DISTURBANCE_ID], "disturbance")
        except Exception as error:
            raise Exception("initialize_simulation_object failed to retrieve disturbance probabilities:\n"+str(error))
        try:
            repair_times = database_resilience.disturbance_repair_values_get(run_param_dict[REPAIR_ID], "repair")
        except Exception as error:
            raise Exception("initialize_simulation_object failed to retrieve repair times:\n"+str(error))
        disturbance = Disturbance(date_time=run_param_dict[DISTURBANCE_DATETIME])
        disturbance.load_disturbances(disturbance_probs)
        disturbance.load_repair_times(repair_times)
    else:
        disturbance = None
    sim = Simulation(
        grid=grid,
        control=run_param_dict[ENERGY_MANAGEMENT_SYSTEM],
        powerload_id=run_param_dict[LOAD_ID],
        start_datetime=run_param_dict[STARTDATETIME],
        weather=weather,
        extend_proportion= run_param_dict[EXTEND_TIMEFRAME] if EXTEND_TIMEFRAME in run_param_dict else 0,
        disturbance=disturbance,
    )
    return sim

def weather_random_number_generator(params, deterministic=False):
    weather_gen = random.Random(random.uniform(0,20000))
    if deterministic:
        return Weather(
            rand_num_generator = weather_gen,
            cloud_distribution = partial(weather_gen.uniform,1.0,1.0),
            sun_distribution = partial(weather_gen.uniform,1.0,1.0),
            autoregressive_proportion = 0.00,
        )
    return Weather(
        rand_num_generator = weather_gen,
        cloud_distribution = partial(weather_gen.uniform,params[WEATHER_CLOUD_LOWER],params[WEATHER_CLOUD_UPPER]),
        sun_distribution = partial(weather_gen.normalvariate,params[WEATHER_SUN_MEAN],params[WEATHER_SUN_STDEV]),
        autoregressive_proportion = params[WEATHER_AUTOREGRESSIVE_PROPORTION],
    )

def timestamp_now():
    return datetime.now().strftime("%y%m%d_%H%M%S")

def get_system_root_dir():
    config_file = "config.ini"
    config_dir_section = "DEFAULT"
    config_results_root = "RESULTS_ROOT_DIR"
    config = configparser.ConfigParser()
    config.read(config_file)
    try:
        root_dir = config.get(config_dir_section,config_results_root)
    except Exception as error:
        raise IOError("Copy config.ini.template to "+config_file+"\n")
    if not os.path.isdir(root_dir):
        yno = input(root_dir + " Does not exist. Create it? [Y/n]: ")
        if len(yno) == 0:
            yno = "y"
        if yno.lower() == "y":
            try:
                os.makedirs(root_dir)
            except Exception as error:
                raise IOError("Unable to create directory "+root_dir+"\n"+str(error))
        else:
            raise IOError("Valid root directory for results must be specified in "+config_file+"\n")
    return root_dir

def email(recipient_email, subject, message_body):
    smtp_server = _CONFIG_INI.get("MAIL","MAIL_SERVER")
    smtp_port = _CONFIG_INI.get("MAIL","MAIL_PORT")
    sender_email = _CONFIG_INI.get("MAIL","MAIL_USERNAME")
    sender_password = _CONFIG_INI.get("MAIL","MAIL_PASSWORD", fallback=None)

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = recipient_email
    message["Subject"] = subject
    message_body="<html><head></head><body>"+message_body+"</body></html>"
    message.attach(MIMEText(message_body, "html"))
    try:
        if _CONFIG_INI.getboolean("MAIL","MAIL_USE_SSL",fallback=False):
            server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        server = smtplib.SMTP(smtp_server, smtp_port)
        if sender_password is not None:
            if _CONFIG_INI.getboolean("MAIL","MAIL_USE_TLS",fallback=False):
                server.ehlo()
                server.starttls()
                server.ehlo()
            server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient_email, message.as_string())
        server.quit()
    except Exception as error:
        raise Exception(error)
