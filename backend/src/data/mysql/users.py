from . import mysql_microgrid, mysql_authentication

def has_permissions(user_id, table_id, table_name, action, admin=False):
    """Returns boolean value indicating whether user has privileges required
    to read, add, update or remove (specified by the action input)
    from the table (and child tables) specified by the input table_name"""
    if admin: return True
    if table_name == None: return True
    try:
        role = mysql_authentication.DB.query(
                """SELECT role 
                    FROM user
                    WHERE id = %s""",
                values = [user_id], output_format="item")
    except Exception as error:
        raise mysql_authentication.AuthenticationDBException("user_has_permissions failed for user id = "+str(user_id)+"\n"+str(error))
    try:
        role = role[0]
    except Exception as error:
        raise mysql_microgrid.MicrogridDBException("user_has_permissions role unavailable for user id = " \
                    +str(user_id)+"\n"+str(error))
    if role == "Guest" and action != "read" and table_name not in ["simulate", "sizing"]: return False
    if table_id is None: return True
    try:
        permission_id = mysql_microgrid.DB.query(
                """SELECT {0}_user.permissionId as permission 
                    FROM {0} 
                    JOIN {0}_user 
                    ON {0}.id = {0}_user.{0}Id
                    WHERE id = %s AND userId = %s""".format(table_name),
                values = [table_id, user_id], output_format="item")
    except Exception as error:
        raise mysql_microgrid.MicrogridDBException("user_has_permissions failed for "+table_name+"_id = " \
                    +str(table_id)+" and user id = "+str(user_id)+"\n"+str(error))
    if permission_id is None: return False
    permission_id = permission_id[0]
    if permission_id not in [mysql_microgrid.PERMISSION_READ, mysql_microgrid.PERMISSION_WRITE]:
        raise mysql_microgrid.MicrogridDBException("user_has_permissions unrecognized permission value {0} for " \
            "{1}_id = {2} and user id = {3}\n{4}".format(permission_id, table_name, table_id, user_id, error))
    return permission_id == mysql_microgrid.PERMISSION_WRITE or action == "read"

def email_get(user_id):
    """Returns the email address of the current user"""
    try:
        email = mysql_authentication.DB.query(
            """SELECT email
                FROM user
                WHERE id = %s""",
            [user_id], output_format="item")[0]
    except Exception as error:
        raise mysql_authentication.AuthenticationDBException("user_email_get failed for user_id="+str(user_id)+"\n"+str(error))
    return email

def get_result_email(table, id):
    """Return email address of user for result with input main table and associated id"""
    try:
        user_id = mysql_microgrid.DB.query(
                """SELECT userId
                    FROM {0}_user
                    JOIN {0}
                    ON {0}_user.{0}Id = {0}.id
                    WHERE {0}.id = %s""".format(table),
                values = [id], output_format="item")[0]
    except Exception as error:
        raise mysql_microgrid.MicrogridDBException("run_email failed for table="+table+", id="+str(id)+"\n"+str(error))
    return email_get(user_id)
