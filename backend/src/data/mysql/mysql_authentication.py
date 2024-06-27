import os
import hashlib
from dotenv import dotenv_values
from src.data.mysql.mysql_core import MySqlDatabase

class AuthenticationDBException(Exception):
    pass

CONFIG_ENV = dotenv_values(os.path.join(os.path.dirname(os.getcwd()),"database-authentication.env"))
DB = MySqlDatabase(
  user = CONFIG_ENV["MYSQL_USER"],
  user_password = CONFIG_ENV["MYSQL_PASSWORD"],
  root_password =  CONFIG_ENV["MYSQL_ROOT_PASSWORD"],
  database_name = CONFIG_ENV["MYSQL_DATABASE"],
  host = CONFIG_ENV["MYSQL_HOST"],
  port = CONFIG_ENV["MYSQL_PORT"],
)

def make_data_passwords(secret_key, admin_password):
    """Hash plain text passwords from .sql files"""
    try:
        users = DB.query("SELECT username, password, id FROM user", output_format="dict")
    except Exception as error:
        raise AuthenticationDBException("make_data_passwords select failed "+"\n"+str(error))
    for user in users:
        if user["username"] == "admin": user["password"] = admin_password
        hashed_password = hashlib.sha1((user["password"] + secret_key).encode()).hexdigest()
        try:
            DB.update(
                "user",
                data_dict = { "password":hashed_password },
                where_dict = { "id":user["id"] }
            )
        except Exception as error:
            raise AuthenticationDBException("make_data_passwords failed update for user = " \
                +str(user)+"\n"+str(error))
