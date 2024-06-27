import os
import pandas as pd
import src.data.mysql.locations as database_locations
import src.data.mysql.weather as database_weather

LOCATION_ID_COL = "NSRDB Closest Location ID"
NAME_COL = "Location"
REGION_COL = "State / Region / Province"
COUNTRY_COL = "Country"
LATITUDE_COL = "Lat"
LONGITUDE_COL = "Long"
API_COL = "API Endpoint"

YEAR_COL = "Year"
MONTH_COL = "Month"
DAY_COL = "Day"
HOUR_COL = "Hour"
MINUTE_COL = "Minute"

ALL_COLS = { YEAR_COL, MONTH_COL, DAY_COL, HOUR_COL, MINUTE_COL}.union(
    database_weather.METRIC_COLS_CSV
)

def csv_to_sql_col_map(colname):
    """Map column names from CSV files to columns names in SQL table schema"""
    col_map = {
        NAME_COL:"locationId",
        YEAR_COL:"yearOrStat",
    }
    if colname in col_map.keys():
        colname = col_map[colname]
    return database_weather.csv_to_sql_col_map(colname)

def process_single_file_contents(data, location_id):
    """Remap column names and add data to database"""
    data[NAME_COL] = location_id
    remapped_columns = [csv_to_sql_col_map(c) for c in data.columns]
    data.columns = remapped_columns
    database_weather.add(data, "weather")

def validate_single_file(filepath):
    """process a single weather data file"""
    df = pd.read_csv(filepath, skiprows=2, dtype={
        YEAR_COL:"int64",
        MONTH_COL:"int64",
        DAY_COL:"int64",
        HOUR_COL:"int64",
        MINUTE_COL:"int64",
    })
    if df.isnull().sum().sum() > 0:
        raise Exception(filepath+" has missing values")
    for col in ALL_COLS:
        if col not in df.columns:
            raise Exception(filepath+" has missing column: "+col)
    if df.shape[0] not in [17520, 17568]:
        raise Exception(filepath+" does not have twice hourly measurements for 365 or 366 days")
    return df

def read_listing(listing_path):
    dataframe = pd.read_csv(listing_path, dtype={
        LOCATION_ID_COL:"str",
        NAME_COL:"str",
        REGION_COL:"str",
        COUNTRY_COL:"str",
    })
    return dataframe

def read_metadata(filepath, attribute):
    """read weather file metadata and return value for input attribute"""
    return pd.read_csv(filepath, nrows=1).at[0,attribute]

def process_all_data_files(listing_path, data_path):
    """process all data files listed in listing path file"""
    listing_df = read_listing(listing_path)
    directory = os.fsencode(data_path)
    for file in os.listdir(directory):
        filename = os.fsdecode(file)
        print(filename, flush=True)
        if filename.startswith("."): continue
        location_id = filename.split("_")[0]
        if len(location_id) == 0:
            raise Exception(filename+" filename location id not in expected format")
        data = validate_single_file(os.path.join(data_path,filename))
        if not database_locations.exists(location_id):
            listing_info = listing_df.loc[listing_df[LOCATION_ID_COL]==location_id]
            if len(listing_info) == 0:
                raise Exception(filename+" location id "+location_id+" not found in "+listing_path)
            name = listing_info[NAME_COL].values[0]
            if pd.isna(name):
                raise Exception(NAME_COL+" not available for location id = "+location_id)
            region = listing_info[REGION_COL].values[0]
            if pd.isna(region):
                raise Exception(REGION_COL+" not available for location id = "+location_id)
            country = listing_info[COUNTRY_COL].values[0]
            if pd.isna(country):
                raise Exception(COUNTRY_COL+" not available for location id = "+location_id)
            latitude = filename.split("_")[1]
            try: float(latitude)
            except ValueError: raise Exception(latitude+" latitude not in expected format")
            longitude = filename.split("_")[2]
            try: float(longitude)
            except ValueError: raise Exception(longitude+" longitude not in expected format")
            elevation = read_metadata(os.path.join(data_path,filename),"Elevation")
            timezone = read_metadata(os.path.join(data_path,filename),"Time Zone")
            database_locations.add(
                id = location_id,
                name = name,
                region = region,
                country = country,
                latitude = latitude,
                longitude = longitude,
                elevation = float(elevation),
                timezone = float(timezone),
            )
        process_single_file_contents(data, location_id)
