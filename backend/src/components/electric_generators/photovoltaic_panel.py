import PySAM.Pvwattsv8 as pvwatts
from src.components import Generator, defaults

class SolarPhotovoltaicPanel(Generator):

    def __init__(self, id, power_rating, is_sun_tracking, temperature_coefficient, 
                 economic_lifespan, investment_cost, om_cost):
        """SolarPhotovoltaicPanel constructor __init__

        Arguments:
        id                          unique id for component
        power_rating                power at standard test conditions (STC)
        is_sun_tracking             boolean true if auto-rotates to track sun; false if fixed angle
        temperature_coefficient     power correction factor for temperature (per degree C)
        economic_lifespan           number of years in economic life
        investment_cost             investment cost
        om_cost                     operating and maintenance cost/year (full usage)
        """
        self._id = id
        self._power_rating = power_rating
        self._is_sun_tracking = is_sun_tracking
        self._temperature_coefficient = temperature_coefficient
        self._temperature_stc = 25.0 # temperature (degrees C) at standard test conditions (STC)
        self._global_tilted_irradiance_stc = 1000.0 # global tilted irradiance (W/m^2) at standard test conditions (STC)
        self._economic_lifespan = economic_lifespan
        self._investment_cost = investment_cost
        self._om_cost = om_cost
        self._pvwatts_system_model = None

    @classmethod
    def init_from_database(cls, cls_dict):
        """SolarPhotovoltaicPanel class method reads dictionary from database info and calls constructor"""
        pv = cls(
            id = cls_dict["id"],
            power_rating = cls_dict["attributes"]["pv_power"],
            is_sun_tracking = cls_dict["attributes"]["is_sun_tracking"] == 1,
            temperature_coefficient = cls_dict["attributes"]["pv_temperature_coefficient"],
            economic_lifespan = cls_dict["attributes"]["pv_economic_lifespan"],
            investment_cost = cls_dict["attributes"]["pv_investment_cost"],
            om_cost = cls_dict["attributes"]["pv_om_cost"],
        )
        pv._validate_params()
        return pv

    def _validate_params(self):
        """Verify parameter values are in acceptable ranges"""
        if self._power_rating < defaults.EPSILON:
            raise ValueError("Solar photovoltaic size is too low, should be greater than 0")
        if self._temperature_coefficient < -0.01 or self._temperature_coefficient > 0.0:
            raise ValueError("Solar photovoltaic temperature coefficient should be between -0.01 and 0")

    def update(self, power_rating):
        self._power_rating = power_rating
    
    def _get_pvwatts_system_model(self):
        """Return PVwatts system model"""

        if self._pvwatts_system_model is not None:
            return self._pvwatts_system_model

        model_params = {
            "SystemDesign": {
                "array_type": 4 if self._is_sun_tracking else 0,
                "dc_ac_ratio": 1.2,
                "gcr": 0.4,
                "inv_eff": 96.0,
                "losses": 14.0,
                "module_type": 0.0,
                "system_capacity": self._power_rating,
            },
            "SolarResource": {
            }
        }
        if not self._is_sun_tracking:
            model_params["SystemDesign"]["azimuth"] = 180 if self._current_weather.latitude >= 0.0 else 0
            model_params["SystemDesign"]["tilt"] = abs(self._current_weather.latitude)
        self._pvwatts_system_model = pvwatts.new()
        self._pvwatts_system_model.assign(model_params)
        self._pvwatts_system_model.AdjustmentFactors.assign({'constant': 0})
        return self._pvwatts_system_model

    def _power_pvwatts(self):
        """Run PVwatts to get power"""
        weather = self._current_weather
        date_time = self._timeperiod.mid()
        solar_resource_data = {
                'tz': weather.timezone, # timezone
                'elev': weather.elevation, # elevation
                'lat': weather.latitude, # latitude
                'lon': weather.longitude, # longitude
                'year': (date_time.year,), # year
                'month': (date_time.month,), # month
                'day': (date_time.day,), # day
                'hour': (date_time.hour,), # hour
                'minute': (date_time.minute,), # minute
                'dn': (weather.direct_normal_irradiance,), # direct normal irradiance
                'df': (weather.diffuse_horizontal_irradiance,), # diffuse irradiance
                'gh': (weather.global_horizontal_irradiance,), # global horizontal irradiance
                'wspd': (weather.wind_speed,), # windspeed
                'tdry': (weather.temperature,) # dry bulb temperature
        }
        system_model = self._get_pvwatts_system_model()
        system_model.SolarResource.assign({'solar_resource_data': solar_resource_data})
        system_model.execute()
        power = system_model.Outputs.dc[0] / 1000.0
        return power
    
    def _power(self):
        return self._power_pvwatts()

    def _energy_output(self, duration):
        """Energy generated over an input duration of time"""
        energy_output = self._power() * duration
        return energy_output

    def _release(self, energy):
        """Output energy to grid (no action required for photovoltaic panel)"""
        pass
