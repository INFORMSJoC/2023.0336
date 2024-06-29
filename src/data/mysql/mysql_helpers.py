import numbers
import configparser
from dotenv import dotenv_values
from src.data.mysql.mysql import MySqlDatabase
from .users import make_data_passwords

class MicrogridDBException(Exception):
    pass

CONFIG_ENV = dotenv_values("config.env")
DB = MySqlDatabase(
  user = CONFIG_ENV["MYSQL_USER"],
  user_password = CONFIG_ENV["MYSQL_PASSWORD"],
  root_password =  CONFIG_ENV["MYSQL_ROOT_PASSWORD"],
  database_name = CONFIG_ENV["MYSQL_DATABASE"],
  host = CONFIG_ENV["MYSQL_HOST"],
  port = CONFIG_ENV["MYSQL_PORT"],
)

_CONFIG_INI = configparser.ConfigParser()
_CONFIG_INI.read("config.ini")
USER_ACCOUNT_QUOTA = dict(_CONFIG_INI.items("QUOTA"))

PERMISSION_READ = 1
PERMISSION_WRITE = 2

def exists():
    """Returns boolean indicating if database exists"""
    try:
        database_exists = True if DB.query(
            """SELECT SCHEMA_NAME
                FROM INFORMATION_SCHEMA.SCHEMATA
                WHERE SCHEMA_NAME = %s""",
            values = [DB.database_name], output_format="item", root=True,
        ) is not None else False
    except Exception as error:
        raise MicrogridDBException("exists() method failed\n"+str(error))
    return database_exists

def num_tables():
    """Returns integer number of tables in database"""
    try:
        num = DB.query(
            """SELECT COUNT(*)
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = %s""",
            values = [DB.database_name], output_format="item", root=True,
        )[0]
    except Exception as error:
        raise MicrogridDBException("num_tables() method failed\n"+str(error))
    return num

def make_data(filenames, secret_key=None, drop_create_db=False):
    """Drop / create user and database
    Execute all commands in list of .sql files as user or root, per input root flag"""
    if drop_create_db:
        try:
            DB.drop_create_user_database()
        except Exception as error:
            raise MicrogridDBException("Drop/create MYSQL user and database failed:\n"+str(error))
    for filename in filenames:
        try:
            DB.execute_sql_file(filename, root=False)
        except Exception as error:
            raise MicrogridDBException("Execute "+filename+" file failed:\n"+str(error))
    if secret_key: make_data_passwords(secret_key)

def validate_input_value(val_type, value, min_value, max_value, message=""):
    """Validates number or string inputs for float and int, and casts them to intended type"""
    if val_type not in ["float", "int"]:
        raise ValueError("_validate_input_value unexpected type of {0}".format(val_type))
    if val_type == "float":
        if not isinstance(value, numbers.Number) and (not value[0] == "-" or value[0].isdigit()) \
                and not (len(value) == 1 or value[1:].replace('.','',1).isdigit()):
            raise ValueError("_validate_input_value is not a float type for value = {0}".format(value))
        value = float(value)
    if val_type == "int":
        if not isinstance(value, int) and (not value[0] == "-" or value[0].isdigit()) \
                and not (len(value) == 1 or value[1:].isdigit()):
            raise ValueError("_validate_input_value is not an int type for value = {0}".format(value))
        value = int(value)
    if value < min_value or value > max_value:
        raise ValueError("value {0} {1} is not in acceptable range of [{2},{3}]".format(
            message, value, min_value, max_value)
        )

def unused_name_in_table(user_id, table_name, name, id=0, return_id=False):
    """Return boolean indicating if table_name with name does not already exist for user"""
    try:        
        record = DB.query(
            """SELECT {0}.id
                FROM {0} 
                JOIN {0}_user
                ON {0}.id = {0}_user.{0}Id
                WHERE name = %s AND userId = %s AND id <> %s""".format(table_name),
            values=[name, user_id, id], output_format="item"
        )
        if record is not None:
            return False if not return_id else record[0]
    except Exception as error:
        raise MicrogridDBException("_unused_name_in_table select failed for name="+name+"\n"+str(error))
    return True

def user_quota():
    """Return dictionary of quotas where keys are database table names
    and values are allowable number of entries per user"""
    return USER_ACCOUNT_QUOTA

def user_quota_check(user_id, table_name):
    """Raise exception if user has reached quota for allowable number of entries in specified table"""
    try:
        limit = int(USER_ACCOUNT_QUOTA[table_name])
        if DB.query(
                """SELECT COUNT({0}.id)
                    FROM {0}
                    JOIN {0}_user
                    ON {0}.id = {0}_user.{0}Id
                    WHERE userId = %s""".format(table_name),
                values=[user_id], output_format="item"
        )[0] >= limit:
            raise ValueError("reached user account quota of {0} entries in {1}".format(limit, table_name))
    except Exception as error:
        raise MicrogridDBException("_user_quota_exceeded failed for {0}\n{1}".format(table_name, error))

def update_name_description(user_id, table_name, id, name, description):
    """Update name and description for a specified table in the database"""
    flag = True
    message = "Success"
    try:
        if name and unused_name_in_table(user_id, table_name, name, id):
            DB.update(
                table_name = table_name, 
                data_dict = { "name":name },
                where_dict = { "id":id }
            )
        elif name:
            flag = False
            message = "Name "+name+" already exists"
        if description is not None:
            DB.update(
                table_name = table_name, 
                data_dict = { "description":description },
                where_dict = { "id":id }
            )
    except Exception as error:
        raise MicrogridDBException("""_update_name_description failed setting name 
                and / or description for {0} id = {1}\n {2}""".format(
            table_name, id, error))
    return flag, message
