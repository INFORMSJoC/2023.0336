import datetime
import math
import src.utils as utils
from src.components import Generator, defaults

class SolarPhotovoltaicPanel(Generator):

    def __init__(self, id, power_rating, capacity, sine_width,
                    economic_lifespan, investment_cost, om_cost):
        """SolarPhotovoltaicPanel constructor __init__

        Arguments:
        id                      unique id for component
        power_rating            power at max sun
        capacity                dictionary of capacity (sun strength) by month
        sine_width              dictionary of sine width (sun strength) by month
        economic_lifespan       number of years in economic life
        investment_cost         investment cost
        om_cost                 operating and maintenance cost/year (full usage)
        """
        self._id = id
        self._power_rating = power_rating
        self._capacity = capacity
        self._sine_width = sine_width
        self._economic_lifespan = economic_lifespan
        self._investment_cost = investment_cost
        self._om_cost = om_cost
        self._date_time = None
        self._day_of_week = None
        self._sun_weight = None
        self._cloud_weight = None

    @classmethod
    def init_from_database(cls, cls_dict):
        """SolarPhotovoltaicPanel class method reads dictionary from database info and calls constructor"""
        return cls(
            id = cls_dict["id"],
            power_rating = cls_dict["attributes"]["pv_power"],
            capacity = None,
            sine_width = None,
            economic_lifespan = cls_dict["attributes"]["pv_economic_lifespan"],
            investment_cost = cls_dict["attributes"]["pv_investment_cost"],
            om_cost = cls_dict["attributes"]["pv_om_cost"],
        )
       
    def update_photovoltaic_characteristics(self, capacity, sine_width):
        """TEMPORARY CODE FOR WEB APP UNTIL PHOTOVOLTAIC MODEL IS UPDATED TO USE HISTORICAL DATA"""
        self._capacity = capacity
        self._sine_width = sine_width

    def update_current_conditions(self, date_time, weather):
        """Update datetime and sun weight"""
        self._date_time = date_time
        day_of_week = self._date_time.weekday()
        if self._cloud_weight == None or self._day_of_week != day_of_week:
            self._day_of_week = day_of_week
            self._cloud_weight = weather.cloud_weight(self._date_time)
        if self._sun_weight == None: self._sun_weight = self._cloud_weight
        self._sun_weight = weather.sun_weight(self._date_time, self._sun_weight)

    def _validate_params(self):
        """Verify parameter values are in acceptable ranges"""
        if self._power_rating < defaults.EPSILON:
            raise ValueError("Solar photovoltaic size is too low, should be greater than 0")
        if self._date_time is None:
            raise ValueError("Solar photovoltaic "+self._id+" datetime has not been set")
        month = self._date_time.strftime("%B")
        if month not in self._capacity or month not in self._sine_width:
            raise ValueError("Solar photovoltaic info missing "+month)
        # if self._capacity[month] < defaults.EPSILON or self._capacity[month] > 1.0:
        #     raise ValueError("Solar photovoltaic capacity should be in (0,1]")
        if self._sine_width[month] < defaults.EPSILON or self._sine_width[month] > 1.0:
            raise ValueError("Solar photovoltaic sine width should be in (0,1]")

    def update(self, power_rating):
        self._power_rating = power_rating

    def _power(self):
        """Power generated"""
        self._validate_params()
        capacity = self._capacity[self._date_time.strftime("%B")]
        sine_width = self._sine_width[self._date_time.strftime("%B")]
        time = self._date_time.time()
        hours = time.hour + time.minute/60.0 + time.second/3600.0
        power = max(
            0,
            -1*self._power_rating*capacity * min(self._sun_weight * self._cloud_weight,1) / (2*sine_width) * \
                (math.sin(2*math.pi*hours/24.0 + math.pi/2) - (2*sine_width-1))
        )
        return  power

    def _energy_output(self, duration):
        """Energy generated over an input duration of time"""
        energy_output = self._power() * duration
        return energy_output

    def _release(self, energy):
        """Output energy to grid (no action required for photovoltaic panel)"""
        pass

    def sizing_max_multiplier(self):
        """multiplier for design of experiments max when sizing DERs"""
        return 3.0
