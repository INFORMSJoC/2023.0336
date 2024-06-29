import pytest
from make import make_data
from src.data.mysql import mysql_authentication, mysql_microgrid, mysql_weather

def pytest_sessionstart(session):
    if not mysql_authentication.DB.exists() or mysql_authentication.DB.num_tables() == 0:
        make_data.authentication_database(
            drop_create_db=True,
            load_data_dev=False,
        )

    if not mysql_microgrid.DB.exists() or mysql_microgrid.DB.num_tables() == 0:
        make_data.microgrid_database(
            drop_create_db=True,
            load_data_dev=False,
        )

    if not mysql_weather.DB.exists() or mysql_weather.DB.num_tables() == 0:
        make_data.weather_database(drop_create_db=True)
