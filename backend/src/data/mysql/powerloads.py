import math
import base64
from dateutil import parser
from datetime import timedelta
from . import mysql_microgrid

def get_all(user_id):
    """Returns a list of dictionaries with the id and name of every powerload
    for which the input user has access"""
    try:
        powerloads = mysql_microgrid.DB.query(
            """SELECT p.id AS id, p.name AS name, p.description AS description, 
                    p.startdatetime AS startdatetime, p.enddatetime AS enddatetime, p.image as image
                FROM powerload p
                JOIN powerload_user u
                ON p.id = u.powerloadId 
                WHERE u.userId = %s
                ORDER BY name""",
            [user_id],output_format="dict")
    except Exception as error:
        raise mysql_microgrid.MicrogridDBException("powerloads_get select failed for user id="+str(user_id)+"\n"+str(error))
    for powerload in powerloads:
        powerload["startdatetime"] = powerload["startdatetime"].strftime(mysql_microgrid.DATETIMEFORMAT)
        powerload["enddatetime"] = powerload["enddatetime"].strftime(mysql_microgrid.DATETIMEFORMAT)
        if powerload["image"] is not None:
            try: # process base64 not decoded from SQL data files
                powerload["image"] = "data:image/png;base64,"+powerload["image"].decode("utf-8")
            except: # process base64 decoded in add() method
                try:
                    powerload["image"] = "data:image/png;base64,"+base64.b64encode(powerload["image"]).decode("utf-8")
                except Exception as error:
                    raise mysql_microgrid.MicrogridDBException("powerload get_all image decoding failed \n"+str(error))
    return powerloads

def _data_get(powerload_id, startdatetime, objectFlag=False):
    """Returns a list of dictionaries with time and powerload value in chronological order
    for the input powerload id"""
    try:
        powerload_data = mysql_microgrid.DB.query(
            """SELECT time, value 
                FROM powerload_data 
                WHERE powerloadId = %s
                ORDER BY time ASC""",
            values=[powerload_id], output_format="dict")
    except Exception as error:
        raise mysql_microgrid.MicrogridDBException("powerload_data_get failed for powerload id = "+str(powerload_id)+"\n"+str(error))
    reformatted_powerload_data = [None] * (len(powerload_data)-1)
    for i in range(0,len(powerload_data)-1):
        start = startdatetime + timedelta(hours=powerload_data[i]["time"])
        end = startdatetime + timedelta(hours=powerload_data[i+1]["time"])
        mid = startdatetime + timedelta(hours=powerload_data[i]["time"]+((powerload_data[i+1]["time"]-powerload_data[i]["time"])/2.0))
        reformatted_powerload_data[i] = {
            "startdatetime": start if objectFlag else start.strftime(mysql_microgrid.DATETIMEFORMAT),
            "middatetime": mid if objectFlag else mid.strftime(mysql_microgrid.DATETIMEFORMAT),
            "enddatetime": end if objectFlag else end.strftime(mysql_microgrid.DATETIMEFORMAT),
            "powerload_original": powerload_data[i]["value"], # original data
            "powerload": (powerload_data[i]["value"]+powerload_data[i+1]["value"])/2.0 # interpolated data used in computations
        }
    if not objectFlag: # return last data point submitted by user
        start = startdatetime + timedelta(hours=powerload_data[len(powerload_data)-1]["time"])
        reformatted_powerload_data.append({
            "startdatetime": start.strftime(mysql_microgrid.DATETIMEFORMAT),
            "middatetime": None,
            "enddatetime": None,
            "powerload_original": powerload_data[i]["value"],
            "powerload": None
        })
    return reformatted_powerload_data

def get_single(powerload_id, objectFlag=False):
    """Returns a dictionaries metadata and powerload data for a given powerload id"""
    try:
        powerload = mysql_microgrid.DB.query(
            """SELECT name, description, startdatetime, enddatetime
                FROM powerload
                WHERE id = %s""",
            [powerload_id], output_format="dict")[0]
    except Exception as error:
        raise mysql_microgrid.MicrogridDBException("powerload_get select failed for id="+str(powerload_id)+"\n"+str(error))
    name = powerload["name"]
    description = powerload["description"]
    startdatetime = powerload["startdatetime"]
    enddatetime = powerload["enddatetime"]
    data = _data_get(powerload_id, startdatetime, objectFlag)
    return {
        "name":name,
        "id":powerload_id,
        "description": description,
        "startdatetime": startdatetime if objectFlag else startdatetime.strftime(mysql_microgrid.DATETIMEFORMAT),
        "enddatetime":  enddatetime if objectFlag else enddatetime.strftime(mysql_microgrid.DATETIMEFORMAT),
        "data":data,
    }

def update_image(id, image):
    """Add a powerload image to the database"""
    try:
        mysql_microgrid.DB.update(
            table_name = "powerload",
            data_dict = { "image": base64.b64decode(image.split("data:image/png;base64,")[1]) },
            where_dict = { "id":id }
        )
    except Exception as error:
        raise mysql_microgrid.MicrogridDBException("powerload update_image failed for id = "+str(id)+"\n"+str(error))
    return True, "Success"
    
def add(user_id, name, data, description=""):
    """Add a powerload to the database"""
    mysql_microgrid.user_quota_check(user_id, "powerload")
    for datetimestring in data["time"]:
        mysql_microgrid.validate_input_value("datetime", datetimestring, None, None, "for time of ")
    for num in data["value"]:
        mysql_microgrid.validate_input_value("float", num, 0, math.inf, "for powerload of ")
    data_len = len(data["time"])
    if data_len < 2:
        return False, "Powerload data must have at least two time, value entries", None
    if data_len != len(data["value"]):
        return False, "Powerload data provided did not have equal number of time, value entries", None
    max_len = int(mysql_microgrid.USER_ACCOUNT_QUOTA["powerload_file_lines"])
    if data_len > max_len:
        return False, "Powerload data has {0} lines, exceeds max allowable of {1}".format(data_len, max_len), None
    if not mysql_microgrid.unused_name_in_table(user_id, "powerload", name):
        return False, "Powerload {0} already exists for this user".format(name), None
    for i in range(0, data_len):
        data["time"][i] = parser.parse(data["time"][i], fuzzy=False)
    startdatetime = min(data["time"])
    enddatetime = max(data["time"])
    try:
        powerload_id = mysql_microgrid.DB.insert_update(
            "powerload",
            {
                "name": name,
                "description": description,
                "startdatetime": startdatetime,
                "enddatetime": enddatetime,
            }
        )
    except Exception as error:
        raise mysql_microgrid.MicrogridDBException("powerload_add update failed for name = "+name+"\n"+str(error))
    if powerload_id is None or powerload_id == 0:
        return False, "invalid powerload id", None
    try:
        mysql_microgrid.DB.insert_update("powerload_user", { "powerloadId":powerload_id, "userId":user_id, "permissionId": mysql_microgrid.PERMISSION_WRITE })
    except Exception as error:
        raise mysql_microgrid.MicrogridDBException("powerload_add update failed for user with powerloadId="+str(powerload_id)+"\n"+str(error))
    data["powerloadId"]=[powerload_id]*data_len
    for i in range(0, data_len):
        data["time"][i] = (data["time"][i] - startdatetime).total_seconds()/3600.0
    try:
        mysql_microgrid.DB.insert_update("powerload_data", data)
    except Exception as error:
        raise mysql_microgrid.MicrogridDBException("powerload_add update failed for data="+str(data)+"\n"+str(error))
    return True, "Success", powerload_id

def remove(powerload_id):
    """Delete powerload from database"""
    try:
        mysql_microgrid.DB.delete("powerload", {"id": powerload_id})
    except Exception as error:
        raise mysql_microgrid.MicrogridDBException("powerload_remove delete failed for id="+str(powerload_id)+"\n"+str(error))
    return True, "Success"
