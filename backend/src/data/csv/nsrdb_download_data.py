import os
import configparser
import requests
import time
import math
import zipfile
import shutil
import weather
import src.data.mysql.weather as database_weather
from run.helpers import get_system_root_dir

_DOWNLOAD_DIR = os.path.join(get_system_root_dir(), "nsrdb_downloads")
os.makedirs(_DOWNLOAD_DIR, exist_ok=True)

_CONFIG_INI_API = configparser.ConfigParser()
_CONFIG_INI_API.read("src/data/csv/nsrdb_api.ini")
_API_KEY = _CONFIG_INI_API.get("SECURITY","API_KEY")
_EMAIL = _CONFIG_INI_API.get("EMAIL","API_KEY_REGISTERED_EMAIL")

_ENDPOINT_NAME_TO_LOC = {
    "US":"psm3-2-2-download",
    "Europe, Africa, & South Asia":"msg-iodc-download",
    "Asia, Australia, Pacific":"himawari-download",
}

_ENDPOINT_TO_NAMES = {
    "psm3-2-2-download":"2022,2021,2020,2019,2018,2017,2016,2015,2014,2013,2012,2011,2010,2009,2008,2007,2006,2005,2004,2003,2002,2001,2000,1999,1998",
    "msg-iodc-download":"2017,2018,2019",
    "himawari-download":"2016,2017,2018,2019,2020",
}

def attributes():
    s = ""
    for col in database_weather.METRIC_COLS.keys():
        s += col+","
    s = s[:-1]
    return s

def submit_query(endpoint, latitude, longitude):
    """
    Submit an API query to retrieve solar irradiance data.
    Returns the job ID.
    """
    url = f"https://developer.nrel.gov/api/nsrdb/v2/solar/{_ENDPOINT_NAME_TO_LOC[endpoint]}.json"
    params = {
        "api_key": _API_KEY,
        "email": _EMAIL,
        "wkt": "MULTIPOINT({0} {1})".format(longitude, latitude),
        "names": _ENDPOINT_TO_NAMES[_ENDPOINT_NAME_TO_LOC[endpoint]],
        "attributes": attributes(),
        "leap_day": "true",
        "utc": "false",
        "interval": "30",
    }
    response = requests.get(url, params=params)
    data = response.json()
    if "errors" in data and len(data["errors"]) > 0:
        raise Exception("NSRDB API exception: error in response\n"+str(data))
    if "outputs" not in data:
        raise Exception("NSRDB API exception: outputs missing from response\n"+str(data))
    return data["outputs"]["downloadUrl"]

def download(url, filename):
    """
    Download the result when it is ready.
    """
    while True:
        response = requests.get(url)
        if response.status_code != 200:
            time.sleep(10)
            continue
        result = requests.get(url)
        with open(os.path.join(_DOWNLOAD_DIR, filename+".zip"), "wb") as f:
            f.write(result.content)
        break

def extract(filename):
    """Extract the zip archive"""
    os.makedirs(os.path.join(_DOWNLOAD_DIR, filename), exist_ok=True)
    with zipfile.ZipFile(os.path.join(_DOWNLOAD_DIR, filename+".zip")) as zip_file:
        for member in zip_file.namelist():
            curfilename = os.path.basename(member)
            if not curfilename: continue # skip directories
            source = zip_file.open(member)
            target = open(os.path.join(os.path.join(_DOWNLOAD_DIR, filename, curfilename)), "wb")
            with source, target:
                shutil.copyfileobj(source, target)
    info = curfilename.split("_")
    return info[0], info[1], info[2]

def cleanup(filename):
    """Move files to web app folder"""
    os.remove(os.path.join(_DOWNLOAD_DIR, filename+".zip"))
    for currfilename in os.listdir(os.path.join(_DOWNLOAD_DIR, filename)):
        shutil.move(os.path.join(os.path.join(_DOWNLOAD_DIR, filename), currfilename), 
                    os.path.join("data/csv/weather/nsrdb-api-formatted-files/", currfilename))
    shutil.rmtree(os.path.join(_DOWNLOAD_DIR, filename))

def distance_between_coordinates(requested_lat, requested_long, received_lat, received_long):
    """Return the distance in miles between the two input lat/long coordinates"""
    radius_of_earth = 3958.8
    lat1 = math.radians(requested_lat)
    lon1 = math.radians(requested_long)
    lat2 = math.radians(received_lat)
    lon2 = math.radians(received_long)
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radius_of_earth * c


if __name__ == "__main__":
    listing_path = "data/csv/weather/locations.csv"
    listing_df = weather.read_listing(listing_path)
    download_urls  = dict()
    count = 0
    for index, row in listing_df.iterrows():
        time.sleep(3)
        download_urls[index] = submit_query(
            row[weather.API_COL], 
            row[weather.LATITUDE_COL], 
            row[weather.LONGITUDE_COL],
        )
        count += 1
        if count % 19 == 0:
            time.sleep(600)
            print("Waiting 10 minutes to run more jobs due to NSRDB limits.")

    for index, url in download_urls.items():
        download(url, str(index))
        location_id, latitude, longitude = extract(str(index))
        row = listing_df.loc[[index]]
        distance = distance_between_coordinates(float(latitude), float(longitude), 
            float(row.iloc[0][weather.LATITUDE_COL]), float(row.iloc[0][weather.LONGITUDE_COL])) 
        if distance > 10.0:
            print("Warning -- data retrieved for row has lat/long "+str(distance)+" miles from requested location\n"+str(row))
        else:
            listing_df.at[index, weather.LOCATION_ID_COL] = location_id
            cleanup(str(index))
        listing_df.to_csv(listing_path, index=False)
