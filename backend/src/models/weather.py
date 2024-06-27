import src.data.mysql.weather as database_weather
import src.data.mysql.locations as database_locations
import pandas
from datetime import timedelta

_YEAR_PLACEHOLDER = 1904 # must be a leap year or February 29th records will trigger errors

class WeatherSample(object):

    def __init__(self, parent, dataframe_row):
        """Weather sample constructor __init__
        Do not store parent because it would cause memory issues"""
        self.latitude = parent.latitude
        self.longitude = parent.longitude
        self.elevation = parent.elevation
        self.timezone = parent.timezone
        if dataframe_row.shape[0] != 1:
            raise Exception("WeatherSample error: dataframe does not have exactly 1 row")
        self.temperature = dataframe_row["temperature"].values[0]
        self.global_horizontal_irradiance = dataframe_row["ghi"].values[0]
        self.diffuse_horizontal_irradiance = dataframe_row["dhi"].values[0]
        self.direct_normal_irradiance = dataframe_row["dni"].values[0]
        self.solar_zenith_angle = dataframe_row["solarZenithAngle"].values[0]
        self.surface_albedo = dataframe_row["surfaceAlbedo"].values[0]
        self.pressure = dataframe_row["pressure"].values[0]                    
        self.wind_speed = dataframe_row["windSpeed"].values[0]


class Weather(object):

    def __init__(self, location_id, sample_method="empirical"):
        """Weather constructor __init__

        Keyword arguments:
        location_id             ID of location to retrieve historical data
        sample_method           "mean", "empirical" or "normal"
        """
        self._location_id = location_id
        self._get_metadata()
        self._sample_method = sample_method
        self._dataframe = self._initialize()
        self._current_conditions = dict()
        self._cached_samples = dict()
        self.current_sample = None

    def __repr__(self):
        return (f'{self.__class__.__name__}('
           f'location_id={self._location_id!r},'
           f'deterministic_flag={self._deterministic_flag!r},')

    def _get_metadata(self):
        """Retrieve metadata or location"""
        metadata = database_locations.get_info(self._location_id)
        self.latitude = metadata["latitude"]
        self.longitude = metadata["longitude"]
        self.elevation = metadata["elevation"]
        self.timezone = metadata["timezone"]

    def _initialize(self):
        """Retrieve data for location and add datetime column for search efficiency"""
        dataframe = database_weather.read(self._location_id)
        if dataframe.shape[0] == 0:
            raise Exception("Weather error: no data found for location "+str(self._location_id))
        dataframe["year"] = _YEAR_PLACEHOLDER
        dataframe["datetime"] = pandas.to_datetime(dataframe[["year", "month", "day", "hour", "minute"]])
        return dataframe.drop("year", axis=1)

    def _get_current_conditions(self, timeperiod):
        """Return dataframe rows corresponding to input time period"""
        if timeperiod in self._current_conditions: return self._current_conditions[timeperiod]
        start = timeperiod.start().replace(year=_YEAR_PLACEHOLDER, second=0, microsecond=0)
        end = timeperiod.end().replace(year=_YEAR_PLACEHOLDER, second=0, microsecond=0)
        while (start.month == 2 and start.day == 29) or (end.month == 2 and end.month == 29):
            start = start + timedelta(days=1)
            end = end + timedelta(days=1)
        if start.minute < 15: start = start.replace(minute=0)
        if start.minute >= 45: start = (start.replace(minute=0) + timedelta(hours=1)).replace(year=_YEAR_PLACEHOLDER)
        if start.minute != 0: start = start.replace(minute=30)
        if end.minute < 15: end = end.replace(minute=0)
        if end.minute >= 45: end = (end.replace(minute=0) + timedelta(hours=1)).replace(year=_YEAR_PLACEHOLDER)
        if end.minute != 0: end = end.replace(minute=30)
        if start <= end: # check required because all years are the same _YEAR_PLACEHOLDER value
            dataframe = self._dataframe.loc[
                (self._dataframe["datetime"] >= start) &
                (self._dataframe["datetime"] <= end)
            ]
        else:
            dataframe = pandas.concat([
                self._dataframe.loc[
                    (self._dataframe["datetime"] >= start) &
                    (self._dataframe["datetime"] < str(_YEAR_PLACEHOLDER+1)+"-01-01")
                ],
                self._dataframe.loc[
                    (self._dataframe["datetime"] >= str(_YEAR_PLACEHOLDER)+"-01-01") &
                    (self._dataframe["datetime"] <= end)
                ]
            ], axis=0)
        current_conditions = dataframe.groupby(["yearOrStat"])[
            database_weather.METRIC_COLS_SQL
        ].agg("mean").reset_index() # if multiple datetimes exist (spacing > 30 mins), combine
        self._current_conditions[timeperiod] = current_conditions
        return current_conditions

    def _method_mean(self, timeperiod):
        """Apply 'mean' method for generating weather sample"""
        if timeperiod in self._cached_samples:
            return self._cached_samples[timeperiod]
        current_conditions = self._get_current_conditions(timeperiod)
        mean_row = current_conditions.loc[current_conditions["yearOrStat"] == "mean"]
        current_sample = WeatherSample(self, mean_row)
        self._cached_samples[timeperiod] = current_sample
        return current_sample
    
    def update(self, timeperiod):
        """Generate WeatherSample for input time period"""
        if self._sample_method == "mean":
            self.current_sample = self._method_mean(timeperiod)
        elif self._sample_method == "empirical":
            self.current_sample = None # need to write this method
        elif self._sample_method == "normal":
            self.current_sample = None # need to write this method
        else:
            raise ValueError("sample method for Weather undefined: "+self._sample_method)
