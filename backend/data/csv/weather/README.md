## Downloading Weather Data for Microgrid Planner

# Obtaining Coordinates for Locations of Interest

Coordinates can be obtained from Google Maps by clicking on a location and copying the latitude and longitude provided.

# Preparing Coordinates for the NSRDB API

The template `locations.xslx.template` can be copied to `locations.xls` and provides convenient functions for converting coordinates returned by Google Maps to the format required by the NSRDB API when running it manually in a web browser. This file can also be saved as a CSV to generate the required listing document `locations.csv`.

# NSRDB Weather Data API

To download NSRDB data using the API, you will need to sign up for an API key:
- https://developer.nrel.gov/signup/

Documentation for the NSRBD API can be found at https://developer.nrel.gov/docs/solar/nsrdb/.

The API endpoints are location specific. A summary of data sources is provided at https://nsrdb.nrel.gov/data-sets/international-data. Coverage can also be viewed interactively on the [NSRDB Viewer](https://nsrdb.nrel.gov/data-viewer).

Once the requested data is prepared, the API sends an email with a link to access the data. Store all downloaded data files in the `nsrdb-api-formatted-files` directory.

To download NSRDB data in the US, use the following API query:
- https://developer.nrel.gov/api/nsrdb/v2/solar/psm3-2-2-download.json?api_key={YOUR_API_KEY}&email={YOUR_EMAIL}&wkt=MULTIPOINT({LONGITUDE1}+{LATITUDE1},{LONGITUDE2}+{LATITUDE2})&names=2022,2021,2020,2019,2018,2017,2016,2015,2014,2013,2012,2011,2010,2009,2008,2007,2006,2005,2004,2003,2002,2001,2000,1999,1998&attributes={ATTIBUTE1,ATTRIBUTE2,ETC.}&leap_day=true&utc=false&interval=30
- Note: MULTIPOINT limit allows only two locations when downloading all available years.

To download NSRDB data in Europe, Africa, & South Asia use the following API query:
- https://developer.nrel.gov/api/nsrdb/v2/solar/msg-iodc-download.json?api_key={YOUR_API_KEY}&email={YOUR_EMAIL}&wkt=MULTIPOINT({LONGITUDE1}+{LATITUDE1},{LONGITUDE2}+{LATITUDE2})&names=2017,2018,2019&attributes={ATTIBUTE1,ATTRIBUTE2,ETC.}&leap_day=true&utc=false&interval=30

To download NSRDB data in Asia, Australia & Pacific, use the following API query:
- https://developer.nrel.gov/api/nsrdb/v2/solar/himawari-download.json?api_key={YOUR_API_KEY}&email={YOUR_EMAIL}&wkt=MULTIPOINT({LONGITUDE1}+{LATITUDE1},{LONGITUDE2}+{LATITUDE2})&names=2016,2017,2018,2019,2020&attributes={ATTIBUTE1,ATTRIBUTE2,ETC.}&leap_day=true&utc=false&interval=30


# Summary of Locations

The `locations.csv` file is required to provide a summary of all the locations present in the `nsrdb-api-formatted-files` directory. The `Location`, `State / Region / Province`, `Country` and `NSRDB Closest Location ID` columns are required to generate the dropdown menus in the frontend application for selecting a location. This information is also presented when results in the frontend application are displayed.

# Automated Data Retrieval

The script `src/data/csv/nsrdb_download_data` automates the process of downloading data from the NSRDB endpoints. You must prepare the listing file `locations.csv` and it will be processed to retrieve the data specified.
