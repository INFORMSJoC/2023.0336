from . import mysql_weather

_COUNTRY_REGION_NAME = None
_ID = None
_INFO_BY_ID = None

def exists(id):
    """Return boolean indicating whether location exists"""
    try:
        record = mysql_weather.DB.query(
            """SELECT *
                FROM location
                WHERE id = %s""",
            values=[id], output_format="item")
    except Exception as error:
        raise mysql_weather.WeatherDBException("exists failed for location id="+str(id)+"\n"+str(error))
    return record is not None


def add(id, name, region, country, latitude, longitude, elevation, timezone):
    """Add a location to the database"""
    try:
        data_dict={
            "id": id,
            "name": name,
            "region": region,
            "country": country,
            "latitude": latitude,
            "longitude": longitude,
            "elevation": elevation,
            "timezone": timezone,
        }
        id = mysql_weather.DB.insert(table_name="location", data_dict=data_dict)
    except Exception as error:
        raise mysql_weather.WeatherDBException("location add failed for location with id = "+str(id)+"\n"+str(error))
    return id


def _get():
    """Return dictionary of all locations"""
    global _COUNTRY_REGION_NAME
    if _COUNTRY_REGION_NAME: return _COUNTRY_REGION_NAME
    try:
        records = mysql_weather.DB.query(
            """SELECT *
                FROM location""",
            output_format="dict")
    except Exception as error:
        raise mysql_weather.WeatherDBException("exists failed for location id="+str(id)+"\n"+str(error))
    _COUNTRY_REGION_NAME = dict()
    for record in records:
        if record["country"] not in _COUNTRY_REGION_NAME:
            _COUNTRY_REGION_NAME[record["country"]] = dict()
        if record["region"] not in _COUNTRY_REGION_NAME[record["country"]]:
            _COUNTRY_REGION_NAME[record["country"]][record["region"]] = dict()
        _COUNTRY_REGION_NAME[record["country"]][record["region"]][record["name"]] = {
            "id":record["id"],
            "latitude":record["latitude"],
            "longitude":record["longitude"],
            "elevation":record["elevation"],
            "timezone":record["timezone"],
        }
    _COUNTRY_REGION_NAME = dict(sorted(_COUNTRY_REGION_NAME.items()))
    for country in _COUNTRY_REGION_NAME:
        _COUNTRY_REGION_NAME[country] = dict(sorted(_COUNTRY_REGION_NAME[country].items()))
        for region in _COUNTRY_REGION_NAME[country]:
            _COUNTRY_REGION_NAME[country][region] = dict(sorted(_COUNTRY_REGION_NAME[country][region].items()))
    return _COUNTRY_REGION_NAME

def get_countries():
    """Return list of countries"""
    country_region_name = _get()
    return list(country_region_name.keys())

def get_regions(country):
    """Return list of regions"""
    country_region_name = _get()
    if country not in country_region_name:
        raise mysql_weather.WeatherDBException("country "+country+" not in database")
    return list(country_region_name[country].keys())

def get_names(country, region):
    """Return list of regions"""
    country_region_name = _get()
    if country not in country_region_name:
        raise mysql_weather.WeatherDBException("country "+country+" not in database")
    if region not in country_region_name[country]:
        raise mysql_weather.WeatherDBException("region "+region+" not in database for country "+country)
    return country_region_name[country][region]

def get_ids():
    """Return list of all location IDs"""
    global _ID
    if _ID: return _ID
    _ID = []
    country_region_name = _get()
    for country in country_region_name.keys():
        for region in country_region_name[country].keys():
            for name in country_region_name[country][region]:
                _ID.append(country_region_name[country][region][name]["id"])
    return _ID

def get_info(id):
    """Return list of all location IDs"""
    global _INFO_BY_ID
    if not _INFO_BY_ID:
        _INFO_BY_ID = dict()
        country_region_name = _get()
        for country in country_region_name.keys():
            for region in country_region_name[country].keys():
                for name in country_region_name[country][region]:
                    _INFO_BY_ID[country_region_name[country][region][name]["id"]] = {
                        "country":country,
                        "region":region,
                        "name":name,
                        "latitude":country_region_name[country][region][name]["latitude"],
                        "longitude":country_region_name[country][region][name]["longitude"],
                        "elevation":country_region_name[country][region][name]["elevation"],
                        "timezone":country_region_name[country][region][name]["timezone"],
                    }
    if id not in _INFO_BY_ID:
        raise mysql_weather.WeatherDBException("id "+str(id)+" not in database")
    return _INFO_BY_ID[id]
