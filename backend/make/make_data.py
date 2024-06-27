#!/usr/bin/env python3

import os
import configparser
import configargparse
from src.data.mysql import mysql_authentication, mysql_microgrid, mysql_weather
from src.data.csv.weather import process_all_data_files
import src.data.mysql.weather as database_weather

CONFIG_INI_GLOBAL = configparser.ConfigParser()
CONFIG_INI_GLOBAL.read(os.path.join(os.path.dirname(os.getcwd()),"config.ini"))
SECRET_KEY = CONFIG_INI_GLOBAL.get("SECURITY","SECRET_KEY")

CONFIG_INI = configparser.ConfigParser()
CONFIG_INI.read("config.ini")
ADMIN_PASSWORD = CONFIG_INI.get("SECURITY","ADMIN_PASSWORD")


def authentication_database(drop_create_db=False, load_data_dev=False):
    """constructs authentication database"""
    sql_files_to_execute = []
    sql_files_to_execute.append("data/mysql/schema-authentication.sql")
    sql_files_to_execute.append("data/mysql/data-authentication.sql")
    if load_data_dev: sql_files_to_execute.append("data/mysql/data-authentication-dev-test.sql")
    try:
        mysql_authentication.DB.make_data(sql_files_to_execute, drop_create_db)
        mysql_authentication.make_data_passwords(SECRET_KEY, ADMIN_PASSWORD)
    except Exception as error:
        raise Exception("make_data authentication_database error:\n"+str(error))

def microgrid_database(drop_create_db=False, load_data_dev=False):
    """constructs main microgrid app database"""
    sql_files_to_execute = []
    sql_files_to_execute.append("data/mysql/schema-microgrid.sql")
    sql_files_to_execute.append("data/mysql/data-microgrid.sql")
    sql_files_to_execute.append("data/mysql/data-microgrid-guest.sql")
    if load_data_dev: sql_files_to_execute.append("data/mysql/data-microgrid-dev-test.sql")
    try:
        mysql_microgrid.DB.make_data(sql_files_to_execute, drop_create_db)
    except Exception as error:
        raise Exception("make_data microgrid_database error:\n"+str(error))

def weather_database(drop_create_db=False):
    """constructs main microgrid app database"""
    sql_files_to_execute = []
    sql_files_to_execute.append("data/mysql/schema-weather.sql")
    try:
        mysql_weather.DB.make_data(sql_files_to_execute, drop_create_db)
    except Exception as error:
        raise Exception("make_data weather_database error:\n"+str(error))
    process_all_data_files(
        listing_path="data/csv/weather/locations.csv",
        data_path="data/csv/weather/nsrdb-api-formatted-files/",
    )
    database_weather.generate_summary_records()

if __name__ == "__main__":
    """Use '-h' flag to view command-line options"""
    PARSER = configargparse.ArgParser()
    PARSER.add_argument("-c", "--config_file", is_config_file=True)
    PARSER.add_argument("--drop_create", dest="drop_create", action="store_true", help="drop and create MYSQL database")
    PARSER.add_argument("--authentication", dest="authentication", action="store_true", help="build authentication MYSQL database")
    PARSER.add_argument("--microgrid", dest="microgrid", action="store_true", help="build microgrid MYSQL database")
    PARSER.add_argument("--weather", dest="weather", action="store_true", help="build weather MYSQL database")
    PARSER.add_argument("--data_dev", dest="data_dev", action="store_true", help="add dev test data")
    if PARSER.parse_args().authentication:
        authentication_database(
                drop_create_db = PARSER.parse_args().drop_create,
                load_data_dev = PARSER.parse_args().data_dev,
            )
    if PARSER.parse_args().microgrid:
        microgrid_database(
            drop_create_db = PARSER.parse_args().drop_create,
            load_data_dev = PARSER.parse_args().data_dev,
        )
    if PARSER.parse_args().weather:
        weather_database(PARSER.parse_args().drop_create)
