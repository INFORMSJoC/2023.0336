from . import mysql_weather
import src.data.mysql.locations as database_locations

METRIC_COLS = {
    "air_temperature":"Temperature",
    "ghi":"GHI", 
    "dhi":"DHI",
    "dni":"DNI",
    # "relative_humidity":"Relative Humidity",
    "solar_zenith_angle":"Solar Zenith Angle",
    "surface_albedo":"Surface Albedo",
    "surface_pressure":"Pressure",
    # "total_precipitable_water":"Precipitable Water",
    # "wind_direction":"Wind Direction",
    "wind_speed":"Wind Speed"
}

METRIC_COLS_CSV = METRIC_COLS.values()

def csv_to_sql_col_map(colname):
    """Map column names from CSV format to columns names in SQL table schema"""
    if " " in colname:
        s = ""
        for part in colname.split(" "):
            s += part.capitalize()
        s = s[:1].lower() + s[1:]
    else:
        s = colname.lower()
    return s

METRIC_COLS_SQL = [csv_to_sql_col_map(c) for c in METRIC_COLS_CSV]

def add(dataframe, table_name):
    """Add a weather file records to the database"""
    try:
        mysql_weather.DB.add_dataframe(dataframe, table_name)
    except Exception as error:
        raise mysql_weather.WeatherDBException("weather add failed: "+str(error))

def read(location_id):
    """Read all weather records for input location id from the database"""
    try:
        dataframe = mysql_weather.DB.read_dataframe(
            """SELECT * FROM weather 
            WHERE locationId = {0}""".format(location_id)
        )
    except Exception as error:
        raise mysql_weather.WeatherDBException("weather read failed: "+str(error))
    return dataframe

def generate_summary_records():
    """Generate summary statistics over years of available data
    Store summary statistics in database"""
    location_ids = database_locations.get_ids()
    for location_id in location_ids:
        print(location_id, flush=True)
        data = read(location_id)
        groups = dict()
        for stat in ["mean", "std", "min", "median", "max"]:
            # fillna(0) for std with only one data point
            group = data.groupby(["month","day","hour","minute"])[
                METRIC_COLS_SQL
            ].agg(stat).fillna(0)
            group["locationId"] = location_id
            group["yearOrStat"] = stat
            groups[stat] = group.reset_index()
        for stat, group in groups.items():
            add(group, "weather")
