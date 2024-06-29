from . import mysql_microgrid

_ENERGY_MANAGEMENT_SYSTEMS = None
_ENERGY_MANAGEMENT_SYSTEM_PARAMETER_NAMES = None

def get():
    """Returns a list of energy management systems"""
    global _ENERGY_MANAGEMENT_SYSTEMS
    if _ENERGY_MANAGEMENT_SYSTEMS: return _ENERGY_MANAGEMENT_SYSTEMS
    try:
        _ENERGY_MANAGEMENT_SYSTEMS = mysql_microgrid.DB.query(
            """SELECT * FROM energy_management_system 
            ORDER BY displayOrder""",
            output_format="dict"
        )
    except Exception as error:
        raise mysql_microgrid.MicrogridDBException("get select failed\n"+str(error))
    return _ENERGY_MANAGEMENT_SYSTEMS


def get_parameter_name(id):
    """Returns the parameter name (Python method name) for the energy management system with input id"""
    global _ENERGY_MANAGEMENT_SYSTEM_PARAMETER_NAMES
    if not _ENERGY_MANAGEMENT_SYSTEM_PARAMETER_NAMES: 
        try:
            temp = mysql_microgrid.DB.query(
                """SELECT id, parameterName
                    FROM energy_management_system""")
        except Exception as error:
            raise mysql_microgrid.MicrogridDBException("get_parameter_name select failed\n"+str(error))
        _ENERGY_MANAGEMENT_SYSTEM_PARAMETER_NAMES = { str(record[0]):record[1] for record in temp }
    return _ENERGY_MANAGEMENT_SYSTEM_PARAMETER_NAMES[str(id)]
