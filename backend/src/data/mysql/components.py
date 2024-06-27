import math
from . import mysql_microgrid
from src.components.electric_generators import WindTurbine, \
    SolarPhotovoltaicPanel, DieselGenerator
from src.components.energy_storage import Battery

_COMPONENT_TYPES = None
_COMPONENT_TYPE_NAMES = None
_COMPONENT_TYPE_IDS = None

def get_single(component_id, objectFlag=False):
    """Returns a dictionary or Python Class object, depending on the input flag value, 
    for the component specified by the input component_id"""
    try:
        component_info = mysql_microgrid.DB.query(
            """SELECT component.name AS name, component.id as id, component.description as description,
                    component_type.parameterName as typeName, component_type.id as typeId,
                    component_type.description as typeDescription
                FROM component
                JOIN component_type
                ON component.componentTypeId = component_type.id 
                WHERE component.id = %s""",
            [component_id], output_format="dict")[0]
    except Exception as error:
        raise mysql_microgrid.MicrogridDBException("component_get failed for component and type " \
                + "for component_id="+str(component_id)+"\n"+str(error))
    try:
        attributes_list = mysql_microgrid.DB.query(
            """SELECT id as parameterId, parameterName, component_spec_data.value
                FROM component_spec_data
                JOIN component_spec_meta
                ON component_spec_data.componentSpecMetaId = component_spec_meta.id 
                WHERE componentId = %s""",
            values=[component_id], output_format="dict")
    except Exception as error:
        raise mysql_microgrid.MicrogridDBException("component_get failed for spec meta and data for component_id=" \
            +str(component_id)+"\n"+str(error))
    if objectFlag:
        attributes = { x["parameterName"]:x["value"] for x in attributes_list }
        component_info.update({ "attributes":attributes })
        obj = globals()[component_info["typeName"]].init_from_database(component_info)
    else:
        attributes = { x["parameterId"]:x["value"] for x in attributes_list }
        component_info.update({ "attributes":attributes })
    return obj if objectFlag else component_info

def get_all(user_id):
    """Returns a list of dictionaries of all components accessible to the specified user_id"""
    try:
        component_ids = mysql_microgrid.DB.query(
            """SELECT component.id AS id
                FROM component
                JOIN component_type
                ON component.componentTypeId=component_type.id
                JOIN component_user 
                ON component.id=component_user.componentId
                WHERE userId = %s
                ORDER BY component_type.displayOrder, component.name""",
            [user_id], output_format="list")
    except Exception as error:
        raise mysql_microgrid.MicrogridDBException("components_get failed for user_id=" \
            +str(user_id)+"\n"+str(error))
    components = []
    for component_id in component_ids:
        components.append(get_single(component_id=component_id, objectFlag=False))
    return components

def update_attributes(component_id, component_specs):
    """Update spec data for a component in the database"""     
    for meta_id, value in component_specs.items():
        try:
            min_max = mysql_microgrid.DB.query(
                """SELECT minVal, maxVal
                    FROM component_spec_meta
                    WHERE id = %s""",
            [meta_id], output_format="dict")[0]
        except Exception as error:
            raise mysql_microgrid.MicrogridDBException("component_update_attributes failed to get min/max for meta id = {0}\n{1}".format(
                meta_id, error))
        min_value = min_max["minVal"] if min_max["minVal"] is not None else 0
        max_value = min_max["maxVal"] if min_max["maxVal"] is not None else math.inf
        try:
            mysql_microgrid.validate_input_value("float", value, min_value, max_value, "for meta id = {0} of ".format(meta_id))
        except Exception as error:
            remove(component_id)
            return False, str(error)
        try:
            component_spec_data = { 
                "componentId":component_id, 
                "componentSpecMetaId":meta_id,
                "value":value 
            }
            mysql_microgrid.DB.insert_update("component_spec_data", component_spec_data)
        except Exception as error:
            raise mysql_microgrid.MicrogridDBException("component_update_attributes failed update for spec_data = " \
                +component_spec_data+"\n"+str(error))
    return True, "Success"

def add(user_id, type_id:int, name, description, specifications):
    """Add a component to the database"""
    mysql_microgrid.user_quota_check(user_id, "component")
    if not mysql_microgrid.unused_name_in_table(user_id, "component", name):
        return False, "Component {0} already exists for this user".format(name)
    try:
        component_id = mysql_microgrid.DB.insert(
            table_name="component", 
            data_dict={ "name": name, "description":description, "componentTypeId": type_id, "id": None }
        )
    except Exception as error:
        raise mysql_microgrid.MicrogridDBException("component_add insert failed for component with name = " \
            +name+" and type id = "+str(type_id)+"\n"+str(error))
    try:
        mysql_microgrid.DB.insert(
            table_name="component_user", 
            data_dict={ "componentId":component_id, "userId":user_id, "permissionId": mysql_microgrid.PERMISSION_WRITE }
        )
    except Exception as error:
        raise mysql_microgrid.MicrogridDBException("component_add insert failed for component_user with component id = " \
            +str(component_id)+" and user id = "+str(user_id)+"\n"+str(error))
    try:
        component_defaults = mysql_microgrid.DB.query( ### CAN BE CACHED TO IMPROVE EFFICIENCY
            """SELECT id, value 
                FROM component_spec_meta
                WHERE componentTypeId = %s AND value IS NOT NULL""", 
            values=[type_id])
    except Exception as error:
        raise mysql_microgrid.MicrogridDBException("component_add select failed for spec_meta with component type id = " \
            +str(type_id)+"\n"+str(error))
    for key_val_tuple in component_defaults:
        key = str(key_val_tuple[0])
        if key not in specifications: specifications[key] = key_val_tuple[1]
    val1, val2 = update_attributes(component_id, specifications)
    if not val1: return val1, val2
    return component_id, None

def add_wrapper(user_id, type_id:int, name, description, specifications):
    """Wrapper for add a component to the database"""
    val1, val2  = add(user_id, type_id, name, description, specifications)
    if val2 is not None: return val1, val2
    return True, "Success"

def remove(component_id):
    """Remove a component from the database"""
    try:
        mysql_microgrid.DB.delete("component", {"id": component_id})
    except Exception as error:
        raise mysql_microgrid.MicrogridDBException("component_remove failed for component id = "+str(component_id)+"\n"+str(error))
    return True, "Success, component with ID {component_id} has been deleted."

def types_get():
    """Returns a dictionary keyed by component type id with a value dictionary
    containing both component type meta and spec meta info"""
    global _COMPONENT_TYPES
    if _COMPONENT_TYPES: return _COMPONENT_TYPES
    try:
        component_types_list = mysql_microgrid.DB.query("SELECT * FROM component_type ORDER BY displayOrder")
    except Exception as error:
        raise mysql_microgrid.MicrogridDBException("component_types_get select failed\n"+str(error))
    try:
        component_spec_meta = mysql_microgrid.DB.query(
            """SELECT *
            FROM component_spec_meta
            ORDER BY displayOrder""", output_format="dict")
    except Exception as error:
        raise mysql_microgrid.MicrogridDBException("component_types_get failed for select component_spec_meta\n"+str(error))
    component_types_with_specs = {}
    for ct in component_types_list:
        component_types_with_specs[ct[0]] = {
            "displayName": ct[1],
            "parameterName": ct[2],
            "description": ct[3],
            "graphLineColor": ct[5],
            "specs": []
        }
    for spec in component_spec_meta:
        component_types_with_specs[spec["componentTypeId"]]["specs"].append(spec)
    _COMPONENT_TYPES = component_types_with_specs
    return _COMPONENT_TYPES

def types_names_get():
    """Returns a dictionary keyed by the component type id with value of the parameter name"""
    global _COMPONENT_TYPE_NAMES
    if _COMPONENT_TYPE_NAMES: return _COMPONENT_TYPE_NAMES
    component_type_names_dict = {}
    for id, component_type in types_get().items():
        component_type_names_dict[id] = component_type["parameterName"]
    _COMPONENT_TYPE_NAMES = component_type_names_dict
    return _COMPONENT_TYPE_NAMES

def types_id_get(name):
    """Returns a the component type id for the input component type name"""
    global _COMPONENT_TYPE_IDS
    if _COMPONENT_TYPE_IDS: return _COMPONENT_TYPE_IDS[name]
    component_type_ids_dict = {}
    for id, component_type in types_get().items():
        component_type_ids_dict[component_type["parameterName"]] = id
    _COMPONENT_TYPE_IDS = component_type_ids_dict
    return _COMPONENT_TYPE_IDS[name]
