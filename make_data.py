#!/usr/bin/env python3

import configparser
import configargparse
import secrets
import src.data.mysql.mysql_helpers as database_helpers

CONFIG_INI = configparser.ConfigParser()
try:
    CONFIG_INI.read("config.ini")
    SECRET_KEY = CONFIG_INI.get("SECURITY","SECRET_KEY")
except Exception as error:
    raise Exception("unable to read secret key from config.ini:\n"+str(error))

def microgrid_database(drop_create_db=False, build_db=True, load_data=True, load_data_guest=True, load_data_paper=False):
    """constructs main microgrid app database"""
    sql_files_to_execute = []
    if build_db: sql_files_to_execute.append("data/mysql/schema.sql")
    if load_data: sql_files_to_execute.append("data/mysql/data.sql")
    if load_data_guest: sql_files_to_execute.append("data/mysql/data_guest.sql")
    if load_data_paper: sql_files_to_execute.append("data/mysql/data_publication_experiments.sql")
    try:
        database_helpers.make_data(sql_files_to_execute, SECRET_KEY, drop_create_db)
    except Exception as error:
        raise Exception("make_data microgrid_database error:\n"+str(error))

def generate_secret_key():
    """Generates a secret key to be pasted in config.ini"""
    return secrets.token_urlsafe(50)

if __name__ == "__main__":
    """Use '-h' flag to view command-line options"""
    PARSER = configargparse.ArgParser()
    PARSER.add_argument("-c", "--config_file", is_config_file=True)
    PARSER.add_argument("--no_mysql", dest="mysql", action="store_false", help="do not modify MYSQL database")
    PARSER.add_argument("--drop_create", dest="drop_create", action="store_true", help="drop and create MYSQL database")
    PARSER.add_argument("--no_db", dest="db", action="store_false", help="do not rebuild MYSQL database")
    PARSER.add_argument("--no_data", dest="data", action="store_false", help="do not add data")
    PARSER.add_argument("--no_data_guest", dest="data_guest", action="store_false", help="do not add guest data")
    PARSER.add_argument("--data_paper", dest="data_paper", action="store_true", help="add paper data")
    PARSER.add_argument("--secret_key", dest="secret_key", action="store_true", help="return secret key for config.ini")
    if PARSER.parse_args().mysql:
        microgrid_database(
            drop_create_db = PARSER.parse_args().drop_create,
            build_db = PARSER.parse_args().db,
            load_data = PARSER.parse_args().data,
            load_data_guest = PARSER.parse_args().data_guest,
            load_data_paper = PARSER.parse_args().data_paper,
        )

    if PARSER.parse_args().secret_key:
        print(generate_secret_key())
