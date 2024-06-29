import hashlib
from . import mysql_helpers

def make_data_passwords(secret_key):
    """Hash plain text passwords from .sql files"""
    try:
        users = mysql_helpers.DB.query("SELECT password, id FROM user", output_format="dict")
    except Exception as error:
        raise mysql_helpers.MicrogridDBException("make_data_passwords select failed "+"\n"+str(error))
    for user in users:
        hashed_password = hashlib.sha1((user["password"] + secret_key).encode()).hexdigest()
        try:
            mysql_helpers.DB.update(
                "user",
                data_dict = { "password":hashed_password },
                where_dict = { "id":user["id"] }
            )
        except Exception as error:
            raise mysql_helpers.MicrogridDBException("make_data_passwords failed update for user = " \
                +str(user)+"\n"+str(error))

def has_permissions(user_id, table_id, table_name, action):
    """Returns boolean value indicating whether user has privileges required
    to read, add, update or remove (specified by the action input)
    from the table (and child tables) specified by the input table_name"""
    try:
        role = mysql_helpers.DB.query(
                """SELECT role 
                    FROM user
                    WHERE id = %s""",
                values = [user_id], output_format="item")
    except Exception as error:
        raise mysql_helpers.MicrogridDBException("user_has_permissions failed for "+table_name+"_id = " \
                    +str(table_id)+" and user id = "+str(user_id)+"\n"+str(error))
    try:
        role = role[0]
    except Exception as error:
        raise mysql_helpers.MicrogridDBException("user_has_permissions role unavailable for user id = " \
                    +str(user_id)+"\n"+str(error))
    if role == "Guest" and action != "read": return False
    if table_id is None: return True
    try:
        permission_id = mysql_helpers.DB.query(
                """SELECT {0}_user.permissionId as permission 
                    FROM {0} 
                    JOIN {0}_user 
                    ON {0}.id = {0}_user.{0}Id
                    WHERE id = %s AND userId = %s""".format(table_name),
                values = [table_id, user_id], output_format="item")
    except Exception as error:
        raise mysql_helpers.MicrogridDBException("user_has_permissions failed for "+table_name+"_id = " \
                    +str(table_id)+" and user id = "+str(user_id)+"\n"+str(error))
    if permission_id is None: return False
    permission_id = permission_id[0]
    if permission_id not in [mysql_helpers.PERMISSION_READ, mysql_helpers.PERMISSION_WRITE]:
        raise mysql_helpers.MicrogridDBException("user_has_permissions unrecognized permission value {0} for " \
            "{1}_id = {2} and user id = {3}\n{4}".format(permission_id, table_name, table_id, user_id, error))
    return True if permission_id == mysql_helpers.PERMISSION_WRITE or action == "read" else False

def email_get(user_id):
    """Returns the email address of the current user"""
    try:
        email = mysql_helpers.DB.query(
            """SELECT email
                FROM user
                WHERE id = %s""",
            [user_id], output_format="item")[0]
    except Exception as error:
        raise mysql_helpers.MicrogridDBException("user_email_get failed for user_id="+str(user_id)+"\n"+str(error))
    return email

def get_run_email(table, id):
    """Return email address of user for run with input main table and associated id"""
    try:
        email = mysql_helpers.DB.query(
                """SELECT email
                    FROM user
                    JOIN {0}_user
                    ON {0}_user.userId = user.id
                    JOIN {0}
                    WHERE {0}.id = %s""".format(table),
                values = [id], output_format="item")[0]
    except Exception as error:
        raise mysql_helpers.MicrogridDBException("run_email failed for table="+table+", id="+str(id)+"\n"+str(error))
    return email
