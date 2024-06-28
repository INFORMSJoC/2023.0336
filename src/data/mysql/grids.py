import math
from . import mysql_helpers
from .components import get_single as component_get

def get_components(grid_id, objectFlag=False):
    """Returns list of dictionaries or Python Class objects
    for each component in the specified grid"""
    try:
        sql_query = """SELECT componentId, quantity FROM grid_component 
            JOIN component ON component.id=grid_component.componentId 
            WHERE grid_component.gridId = %s"""
    except Exception as error:
        raise mysql_helpers.MicrogridDBException("_grid_get_components select failed for grid_id="+str(grid_id)+"\n"+str(error))
    component_info = mysql_helpers.DB.query(sql_query, values=[grid_id], output_format="dict")
    components = []         
    for c in component_info:
        if not objectFlag:
            component = component_get(component_id=c["componentId"], objectFlag=objectFlag)
            component["quantity"] = c["quantity"]
            components.append(component)
        else:
            for i in range(0, c["quantity"]):
                component = component_get(component_id=c["componentId"], objectFlag=objectFlag)
                components.append(component)
    return components

def get_single(id):
    """Returns a dictionary with grid and component info"""
    try:
        grid = mysql_helpers.DB.query(
            """SELECT name, description
                FROM grid
                WHERE id = %s""",
        values=[id],output_format="dict")[0]
    except Exception as error:
        raise mysql_helpers.MicrogridDBException("grid_get select failed for id="+str(id)+"\n"+str(error))
    name = grid["name"]
    description = grid["description"]
    components = get_components(id)
    return {
        "name":name,
        "id":id,
        "description": description,
        "components":components,
    }

def get_all(user_id, isSizingTemplate):
    """Returns list of dictionaries with grid and component info"""
    try:
        grids = mysql_helpers.DB.query(
            """SELECT gridId AS id
                FROM grid 
                JOIN grid_user
                ON grid_user.gridId = grid.id
                WHERE userId = %s AND isSizingTemplate = %s
                ORDER BY name""",
        values=[user_id, isSizingTemplate],output_format="list")
    except Exception as error:
        raise mysql_helpers.MicrogridDBException("grids_get select failed for user_id="+str(user_id)+"\n"+str(error))
    grid_list = []
    for grid_id in grids:
        grid_list.append(get_single(grid_id))
    return grid_list

def update_remove_components(grid_id, components_list):
    """Remove components from grid in the database"""
    for id in components_list:
        try:
            mysql_helpers.DB.delete(
                table_name = "grid_component",
                where_dict = { "componentId":id, "gridId":grid_id })
        except Exception as error:
            raise mysql_helpers.MicrogridDBException("grid_update_remove_components failed for component id = " \
                                       +str(id)+"\n"+str(error))
    return True, "Success"
    
def update_add_components(grid_id, components_dict):
    """Add components to grid in the database"""
    for id, quantity in components_dict.items():
        mysql_helpers.validate_input_value("int", quantity, 1, math.inf, "for id = {0} of ".format(id))
        try:
            mysql_helpers.DB.insert_update(
                table_name = "grid_component", 
                data_dict= { "componentId":id, "gridId":grid_id, "quantity":quantity }
            )
        except Exception as error:
            raise mysql_helpers.MicrogridDBException("grid_update_add_components failed for component id = " \
                                        +str(id)+"\n"+str(error))
    return True, "Success"

def add(user_id, grid_name, description="", is_sizing_template=None):
    """Add a grid to the database"""
    mysql_helpers.user_quota_check(user_id, "grid")
    if not mysql_helpers.unused_name_in_table(user_id, "grid", grid_name):
        return False, "grid {0} already exists for this user".format(grid_name)
    try:
        data_dict={"name": grid_name, "description": description, "id": None}
        if is_sizing_template is not None: data_dict["isSizingTemplate"]=is_sizing_template
        grid_id = mysql_helpers.DB.insert(table_name="grid", data_dict=data_dict)
    except Exception as error:
        raise mysql_helpers.MicrogridDBException("grid_add insert failed for grid with name = "+grid_name+"\n"+str(error))
    if grid_id == 0:
        return False, "Unable to create new grid with name {0}".format(grid_name)
    try:
        mysql_helpers.DB.insert(
            table_name="grid_user", 
            data_dict={ "gridId":grid_id, "userId":user_id, "permissionId": mysql_helpers.PERMISSION_WRITE }
        )
    except Exception as error:
        raise mysql_helpers.MicrogridDBException("grid_add insert failed for grid_user with id = " \
                                    +str(grid_id)+"\n"+str(error))
    return grid_id, None

def add_wrapper(user_id, grid_name, description="", is_sizing_template=None):
    """Wrapper for add a grid to the database"""
    val1, val2  = add(user_id, grid_name, description, is_sizing_template)
    if val2 is not None: return val1, val2
    return True, "Success"

def remove(grid_id):
    """Remove a grid from the database"""
    try:
        mysql_helpers.DB.delete("grid", { "id":grid_id })
    except Exception as error:
        raise mysql_helpers.MicrogridDBException("grid_remove delete failed for grid id = "+str(grid_id)+"\n"+str(error))
    return True, "Success"
