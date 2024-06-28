from dotenv import dotenv_values
from src.data.mysql.mysql_core import MySqlDatabase

class WeatherDBException(Exception):
    pass

CONFIG_ENV = dotenv_values("database-weather.env")
DB = MySqlDatabase(
  user = CONFIG_ENV["MYSQL_USER"],
  user_password = CONFIG_ENV["MYSQL_PASSWORD"],
  root_password =  CONFIG_ENV["MYSQL_ROOT_PASSWORD"],
  database_name = CONFIG_ENV["MYSQL_DATABASE"],
  host = CONFIG_ENV["MYSQL_HOST"],
  port = CONFIG_ENV["MYSQL_PORT"],
)
