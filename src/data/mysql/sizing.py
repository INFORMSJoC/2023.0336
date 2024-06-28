from . import mysql_helpers
from .components import add as component_add, remove as component_remove
from .grids import get_components as grid_get_components, add as grid_add, update_add_components as grid_update_add_components

def grid_get(id):
    """Returns a dictionary with sizing grid info"""
    try:
        sizing_grid = mysql_helpers.DB.query(
            """SELECT sizingId, name, deficitPercentage, excessPercentage, parent
                FROM sizing_grid 
                WHERE id = %s""",
        values=[id],output_format="dict")[0]
    except Exception as error:
        raise mysql_helpers.MicrogridDBException("sizing_grid_get select failed for id="+str(id)+"\n"+str(error))
    return sizing_grid


def grid_component_add(id, component_type_id, unused_percentage, time_steps_percentage):
    """Insert sizing grid data from run into database"""
    try:
        id = mysql_helpers.DB.insert(
            table_name="sizing_grid_component", 
            data_dict={
                "sizingGridId":id,
                "componentTypeId":component_type_id,
                "unusedPercentage":unused_percentage,
                "timeStepsPercentage":time_steps_percentage,
            }
        )
    except Exception as error:
        raise mysql_helpers.MicrogridDBException("sizing_grid_component insert failed for sizing_grid with id = " \
                                    +str(id)+"\n"+str(error))
    return id


def grid_component_spec_data_add(sizing_grid_component_id, component_spec_meta_parameter_name, value):
    """Insert sizing grid component spec data into database"""
    try:
        component_spec_meta_id = mysql_helpers.DB.query(
            """SELECT id
                FROM component_spec_meta
                WHERE parameterName = %s""",
            values=[component_spec_meta_parameter_name],output_format="item")[0]
    except Exception as error:
        raise mysql_helpers.MicrogridDBException("sizing_grid_component_spec_data_add read failed for parameterName = " \
                                    +component_spec_meta_parameter_name+"\n"+str(error))
    try:
        id = mysql_helpers.DB.insert(
            table_name="sizing_grid_component_spec_data", 
            data_dict={
                "sizingGridComponentId":sizing_grid_component_id,
                "componentSpecMetaId":component_spec_meta_id,
                "value":value,
            }
        )
    except Exception as error:
        raise mysql_helpers.MicrogridDBException("sizing_grid_component_spec_data_add failed for sizing_grid_component_id = " \
                                    +str(id)+" and component_spec_meta_id = "+component_spec_meta_id+"\n"+str(error))
    return id

def grid_component_spec_data_get(id, human_readable=False):
    """Read sizing grid component spec data for input sizing grid component id"""
    try:
        data = mysql_helpers.DB.query(
            """SELECT componentSpecMetaId AS id, name, sizing_grid_component_spec_data.value AS value
                FROM sizing_grid_component_spec_data
                JOIN component_spec_meta
                ON component_spec_meta.id = componentSpecMetaId
                WHERE sizingGridComponentId = %s""",
        values=[id],output_format="dict")
    except Exception as error:
        raise mysql_helpers.MicrogridDBException("sizing_grid_component_spec_data read failed for sizing_grid_component with id = " \
                                    +str(id)+"\n"+str(error))
    data = { d["name"]:d["value"] for d in data } if human_readable else { d["id"]:d["value"] for d in data }
    return data

def grid_components_get(id, human_readable=False):
    """Read sizing grid components for input sizing grid id"""
    try:
        components = mysql_helpers.DB.query(
            """SELECT sizing_grid_component.id AS id, componentTypeId, unusedPercentage AS "Unused Ratio", timeStepsPercentage as "Time Steps Ratio", name
                FROM sizing_grid_component
                JOIN component_type
                ON component_type.id = componentTypeId
                WHERE sizingGridId = %s""",
        values=[id],output_format="dict")
    except Exception as error:
        raise mysql_helpers.MicrogridDBException("sizing_grid_component read failed for sizing_grid with id = " \
                                    +str(id)+"\n"+str(error))
    reformatted_components = dict()
    for component in components:
        try:
            component_spec_data = grid_component_spec_data_get(component["id"], human_readable)
        except Exception as error:
            raise mysql_helpers.MicrogridDBException("sizing_grid_components_get sizing_grid_component_spec_data_get failed for id="+str(component["id"])+"\n"+str(error))
        reformatted_components = reformatted_components | component_spec_data
        if human_readable:
            for key, value in component.items():
                if key not in ["id","name","componentTypeId"]:
                    reformatted_components[component["name"]+" "+key] = value
    return reformatted_components

def grids_get(id, display_all, deficit_max, human_readable=True):
    """Returns a list of dictionaries with all sizing grids for the sizing run input id"""
    if deficit_max is None: deficit_max = 0.0
    try:
        sizing_grids = mysql_helpers.DB.query(
            """SELECT id as ID, name as Name, deficitPercentage AS "Sizing Grid Deficit Ratio" {0}
                FROM sizing_grid 
                WHERE {1} sizingId = %s AND deficitPercentage <= {2}""".format(
                    ", parent AS Parent, dominatedBy AS \"Dominated By\"" if display_all else "",
                    "" if display_all else "LENGTH(dominatedBy) = 0 and",
                    deficit_max,
            ),
        values=[id],output_format="dict")
    except Exception as error:
        raise mysql_helpers.MicrogridDBException("sizing_grids_get select failed for id="+str(id)+"\n"+str(error))
    sizing_grids_with_component_info = []
    for sizing_grid in sizing_grids:
        try:
            components = grid_components_get(sizing_grid["ID"], human_readable)
        except Exception as error:
            raise mysql_helpers.MicrogridDBException("sizing_grids_get sizing_grid_components_get failed for id="+str(sizing_grid["id"])+"\n"+str(error))
        sizing_grids_with_component_info.append((sizing_grid | components))
    return sizing_grids_with_component_info

def run_get(id):
    """Returns a dictionary with metadata for the sizing run input id"""
    try:
        sizing = mysql_helpers.DB.query(
            """SELECT gridId, powerloadId, startdatetime
                FROM sizing
                WHERE id = %s""",
        values=[id],output_format="dict")[0]
    except Exception as error:
        raise mysql_helpers.MicrogridDBException("sizing_run_get select failed for id="+str(id)+"\n"+str(error))
    return sizing

def runs_get(user_id):
    """Returns list of dictionaries with metadata for all sizing runs for input user"""
    try:
        sizings = mysql_helpers.DB.query(
            """SELECT sizing.id as "Result ID", gridId as "Microgrid Sizing Template ID",
                    grid.name as "Microgrid Sizing Template", powerload.name as "Powerload",
                    powerloadId as "Powerload ID", startdatetime as "Simulation Start"
                FROM sizing 
                JOIN sizing_user
                ON sizing_user.sizingId = sizing.id
                JOIN grid
                ON grid.id = sizing.gridId
                JOIN powerload
                ON powerload.id = sizing.powerloadId
                WHERE userId = %s
                ORDER BY sizing.id""",
        values=[user_id],output_format="dict")
    except Exception as error:
        raise mysql_helpers.MicrogridDBException("sizing_runs_get select failed for user_id="+str(user_id)+"\n"+str(error))
    return sizings

def run_add(user_id, grid_id, powerload_id, startdatetime, description=""):
    """Add a sizing run to the database"""
    mysql_helpers.user_quota_check(user_id, "sizing")
    try:
        data_dict={"powerloadId": powerload_id, "gridId": grid_id, "startdatetime":startdatetime}
        id = mysql_helpers.DB.insert(table_name="sizing", data_dict=data_dict)
    except Exception as error:
        raise mysql_helpers.MicrogridDBException("sizing_add insert failed\n"+str(error))
    if id == 0:
        return False, "Unable to create new sizing run entry"
    try:
        mysql_helpers.DB.insert(
            table_name="sizing_user", 
            data_dict={ "sizingId":id, "userId":user_id, "permissionId": mysql_helpers.PERMISSION_WRITE }
        )
    except Exception as error:
        raise mysql_helpers.MicrogridDBException("sizing_add insert failed for sizing_user with id = " \
                                    +str(id)+"\n"+str(error))
    return id, "Success"

def remove(id):
    """Delete sizing run from database"""
    try:
        mysql_helpers.DB.delete("sizing", {"id": id})
    except Exception as error:
        raise mysql_helpers.MicrogridDBException("sizing_remove failed for id="+str(id)+"\n"+str(error))
    return True, "Success"

def grid_designs_remove(id):
    """Delete sizing run results from database"""
    try:
        mysql_helpers.DB.delete("sizing_grid", {"sizingId": id})
    except Exception as error:
        raise mysql_helpers.MicrogridDBException("grid_designs_remove failed for id="+str(id)+"\n"+str(error))

def grid_design_add(id, name, deficit_percentage, excess_percentage, dominated_by, parent):
    """Insert sizing grid from run into database"""
    try:
        id = mysql_helpers.DB.insert(
            table_name="sizing_grid", 
            data_dict={ 
                "sizingId":id,
                "name":name,
                "deficitPercentage":deficit_percentage,
                "excessPercentage":excess_percentage,
                "dominatedBy":dominated_by,
                "parent":parent,
            }
        )
    except Exception as error:
        raise mysql_helpers.MicrogridDBException("sizing_grid insert failed for sizing with id = " \
                                    +str(id)+"\n"+str(error))
    return id

def result_save_to_grids(user_id, sizing_grid_id):
    """Save sizing grid from sizing run to user's components and grid"""
    try:
        sizing_grid = grid_get(sizing_grid_id)
    except Exception as error:
        raise mysql_helpers.MicrogridDBException("sizing_grid_save read failed\n"+str(error))    
    try:
        sizing_components = grid_components_get(sizing_grid_id)
    except Exception as error:
        raise mysql_helpers.MicrogridDBException("sizing_grid_save read failed\n"+str(error))    
    try:
        metadata = run_get(sizing_grid["sizingId"])
    except Exception as error:
        raise mysql_helpers.MicrogridDBException("sizing_grid_save read metadata failed\n"+str(error))        
    mysql_helpers.user_quota_check(user_id, "sizing")
    try:
        grid_components = grid_get_components(metadata["gridId"])
    except Exception as error:
        raise mysql_helpers.MicrogridDBException("sizing_grid_save read components failed\n"+str(error))
    new_components = dict()
    for component in grid_components:
        name = ""
        for key, value in sizing_components.items():
            if key in component["attributes"]:
                component["attributes"][key] = value
                name += "-"+(("%d" if value.is_integer() else "%s") % value)
        mysql_helpers.user_quota_check(user_id, "component")
        component_name = component["name"]+name
        try:
            component_id = mysql_helpers.unused_name_in_table(user_id, "component", component_name, return_id=True)
        except Exception as error:
            raise mysql_helpers.MicrogridDBException("sizing_grid_save _unused_name check failed\n"+str(error))        
        if type(component_id) is int:
            val1 = component_id
        else:
            try:
                val1, val2 = component_add(
                    user_id = user_id,
                    type_id = component["typeId"],
                    name = component_name,
                    description = component["description"]+" copy from sizing grid-"+str(metadata["gridId"]) \
                        + ", sizing result "+str(sizing_grid["sizingId"])+ ", sizing grid "+str(sizing_grid_id),
                    specifications = component["attributes"]
                )
                if val2 is not None:
                    if "is not in acceptable range of" in str(val2): val1 = None
                    else: return val1, val2
            except Exception as error:
                raise mysql_helpers.MicrogridDBException("sizing_grid_save component_add failed\n"+str(error))        
        if val1 is not None: new_components[val1] = 1
    try:
        val1, val2 = grid_add(
            user_id = user_id,
            grid_name = "sizing grid "+str(metadata["gridId"])+"-"+str(sizing_grid["name"])+"-"+str(sizing_grid_id),
            description = "copy from sizing grid-"+str(metadata["gridId"]) \
                        + ", sizing result "+str(sizing_grid["sizingId"])+ ", sizing grid "+str(sizing_grid_id)
        )
        if val2 is not None: return val1, val2
    except Exception as error:
        raise mysql_helpers.MicrogridDBException("sizing_grid_save grid_add failed\n"+str(error))        
    try:
        grid_update_add_components(val1, new_components)
    except Exception as error:
        raise mysql_helpers.MicrogridDBException("sizing_grid_save grid_update_add_components failed\n"+str(error))
    return True, "Success"
