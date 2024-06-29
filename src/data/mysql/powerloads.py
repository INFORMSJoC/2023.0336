import math
from . import mysql_helpers

def get_all(user_id):
    """Returns a list of dictionaries with the id and name of every powerload
    for which the input user has access"""
    try:
        powerloads = mysql_helpers.DB.query(
            """SELECT p.id AS id, p.name AS name, p.description AS description 
                FROM powerload p
                JOIN powerload_user u
                ON p.id = u.powerloadId 
                WHERE u.userId = %s
                ORDER BY name""",
            [user_id],output_format="dict")
    except Exception as error:
        raise mysql_helpers.MicrogridDBException("powerloads_get select failed for user id="+str(user_id)+"\n"+str(error))
    return powerloads

def data_get(powerload_id):
    """Returns a list of dictionaries with time and powerload value in chronological order
    for the input powerload id"""
    try:
        powerload_data = mysql_helpers.DB.query(
            """SELECT time, value 
                FROM powerload_data 
                WHERE powerloadId = %s
                ORDER BY time ASC""",
            values=[powerload_id], output_format="dict")
    except Exception as error:
        raise mysql_helpers.MicrogridDBException("powerload_data_get failed for powerload id = "+str(powerload_id)+"\n"+str(error))
    reformatted_powerload_data = [{"time": d["time"], "powerload": d["value"]} for d in powerload_data]
    return reformatted_powerload_data

def get_single(powerload_id):
    """Returns a dictionaries metadata and powerload data for a given powerload id"""
    try:
        powerload = mysql_helpers.DB.query(
            """SELECT name, description
                FROM powerload
                WHERE id = %s""",
            [powerload_id], output_format="dict")[0]
    except Exception as error:
        raise mysql_helpers.MicrogridDBException("powerload_get select failed for id="+str(powerload_id)+"\n"+str(error))
    name = powerload["name"]
    description = powerload["description"]
    data = data_get(powerload_id)
    return {
        "name":name,
        "id":powerload_id,
        "description": description,
        "data":data,
    }

def add(user_id, name, data, description=""):
    """Adds a powerload to the database"""
    mysql_helpers.user_quota_check(user_id, "powerload")
    for k, v in data.items():
        for num in v:
            mysql_helpers.validate_input_value("float", num, 0, math.inf, "for {0} of ".format(k))
    data_len = len(data["time"])
    if data_len != len(data["value"]):
        return False, "Powerload data provided did not have equal number of time, value entries"
    max_len = int(mysql_helpers.USER_ACCOUNT_QUOTA["powerload_file_lines"])
    if data_len > max_len:
        return False, "Powerload data has {0} lines, exceeds max allowable of {1}".format(data_len, max_len)
    if not mysql_helpers.unused_name_in_table(user_id, "powerload", name):
        return False, "Powerload {0} already exists for this user".format(name)
    try:
        powerload_id = mysql_helpers.DB.insert_update(
            "powerload",
            {"name": name, "description": description}
        )
    except Exception as error:
        raise mysql_helpers.MicrogridDBException("powerload_add update failed for name = "+name+"\n"+str(error))
    if powerload_id is None or powerload_id == 0:
        return False, "invalid powerload id"
    try:
        mysql_helpers.DB.insert_update("powerload_user", { "powerloadId":powerload_id, "userId":user_id, "permissionId": mysql_helpers.PERMISSION_WRITE })
    except Exception as error:
        raise mysql_helpers.MicrogridDBException("powerload_add update failed for user with powerloadId="+str(powerload_id)+"\n"+str(error))
    data["powerloadId"]=[powerload_id]*data_len
    try:
        mysql_helpers.DB.insert_update("powerload_data", data)
    except Exception as error:
        raise mysql_helpers.MicrogridDBException("powerload_add update failed for data="+str(data)+"\n"+str(error))
    return True, "Success"

def remove(powerload_id):
    """Delete powerload from database"""
    try:
        mysql_helpers.DB.delete("powerload", {"id": powerload_id})
    except Exception as error:
        raise mysql_helpers.MicrogridDBException("powerload_remove delete failed for id="+str(powerload_id)+"\n"+str(error))
    return True, "Success"
