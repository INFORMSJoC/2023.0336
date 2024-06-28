import zlib
import json
from . import mysql_microgrid
from . import model_helpers

MODEL_HELPERS = model_helpers.ModelDatabaseHelpers("simulate")

def metrics_get(id):
    """Return a metrics dictionary from the database"""
    try:
        record = mysql_microgrid.DB.query(
            """SELECT metrics
                FROM simulate
                WHERE id = %s""",
        values=[id],output_format="dict")[0]
    except Exception as error:
        raise mysql_microgrid.MicrogridDBException("metrics_get select failed for id="+str(id)+"\n"+str(error))
    if record["metrics"] is not None:
        return json.loads(zlib.decompress(record["metrics"]).decode())
    return None

def metrics_add(id, metrics):
    """Add a metrics object to the database"""
    try:
        data_dict = {"metrics": zlib.compress(json.dumps(metrics).encode())}
        where_dict = {"id": id}
        mysql_microgrid.DB.update(table_name="simulate", data_dict=data_dict, where_dict=where_dict)
    except Exception as error:
        raise mysql_microgrid.MicrogridDBException("metrics_add insert failed\n"+str(error))
