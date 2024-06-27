import math
from . import mysql_helpers
from .components import types_names_get as component_types_names_get

def disturbance_repair_values_get(id, table_name):
    """Returns a dictionary keyed by component_type parameterName with
    values for the input disturbance or repair id"""
    component_types = component_types_names_get()
    record = disturbance_repair_get(id, table_name)
    return { component_types[r["componentTypeId"]]:r["value"] for r in record }

def disturbance_repair_get(id, table_name):
    """Returns a dictionary containing disturbance or repair data
    for the specified id"""
    try:
        record = mysql_helpers.DB.query(
            """SELECT *
                FROM {0}_data
                WHERE {0}Id = %s""".format(table_name),
            values=[id], output_format="dict"
        )
    except Exception as error:
        raise mysql_helpers.MicrogridDBException("disturbance_repair_get select failed in {0}_data for id = {1}\n{2}".format(
            table_name, id, error))
    return record

def disturbances_repairs_get(user_id, table_name):
    """Returns a dictionary keyed by id with a value dictionary
    containing both {table_name} and {table_name}_data"""
    valid_table_names=["disturbance", "repair"]
    if table_name not in valid_table_names:
        raise ValueError("get_records: input must be one of %r." % valid_table_names)
    try:
        records = mysql_helpers.DB.query(
            """SELECT id, name, description
                FROM {0}
                JOIN {0}_user
                ON {0}_user.{0}Id = {0}.id
                WHERE {0}_user.userId = %s
                ORDER BY name""".format(table_name),
            values=[user_id], output_format="dict")
    except Exception as error:
        raise mysql_helpers.MicrogridDBException("disturbance_repair_get select failed in "+table_name+"\n"+str(error))
    records_list = []
    for r in records:
        records_list.append({
            "id": r["id"],
            "name": r["name"],
            "description": r["description"],
            "specs": disturbance_repair_get(r["id"], table_name),
        })
    return records_list

def disturbance_repair_update_attributes(id, specs, table_name):
    """Update data for a disturbance or repair in the database"""
    for spec_id, value in specs.items():
        min_value = 0.1 if table_name == "repair" else 0.0
        max_value = 1.0 if table_name == "disturbance" else math.inf
        mysql_helpers.validate_input_value("float", value, min_value, max_value, "for spec id = {0} of ".format(spec_id))
        try:
            data = { 
                table_name+"Id":id, 
                "componentTypeId":spec_id,
                "value":value 
            }
            mysql_helpers.DB.insert_update(table_name+"_data", data)
        except Exception as error:
            raise mysql_helpers.MicrogridDBException("disturbance_repair_update_attributes failed update for data = {0}\n{1}".format(
                data, error))
    return True, "Success"

def disturbance_repair_add(user_id, name, description, specifications, table_name):
    """Add a disturbance or repair to the database"""
    mysql_helpers.user_quota_check(user_id, table_name)
    if not mysql_helpers.unused_name_in_table(user_id, table_name, name):
        return False, "{0} named {1} already exists for this user".format(table_name, name)  
    try:
        id = mysql_helpers.DB.insert(
            table_name=table_name, 
            data_dict={ "name": name, "description":description, "id": None }
        )
    except Exception as error:
        raise mysql_helpers.MicrogridDBException("disturbance_repair_add insert failed for {0} with name = {1}\n{3}".format(
            table_name, name, error))
    try:
        mysql_helpers.DB.insert(
            table_name=table_name+"_user", 
            data_dict={ table_name+"Id":id, "userId":user_id, "permissionId": mysql_helpers.PERMISSION_WRITE }
        )
    except Exception as error:
        raise mysql_helpers.MicrogridDBException("disturbance_repair_add insert failed for {0}_user with {0} id = {1}\n{3}".format(
            table_name, id, error))
    disturbance_repair_update_attributes(id, specifications, table_name)
    return True, "Success"

def disturbance_repair_remove(id, table_name):
    """Remove a disturbance or repair from the database"""
    try:
        mysql_helpers.DB.delete(table_name, {"id": id})
    except Exception as error:
        raise mysql_helpers.MicrogridDBException("disturbance_repair_remove failed for {0} id = {1}\n{2}".format(
            table_name, id, error))
    return True, "Success"
