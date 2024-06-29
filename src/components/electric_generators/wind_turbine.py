import src.utils as utils
from src.components import Generator, defaults

class WindTurbine(Generator):

    def __init__(self, id, power_rating, availability, capacity, date_time,
                    economic_lifespan, investment_cost, om_cost):
        """WindTurbine constructor __init__

        Arguments:
        id                      unique id for component
        power_rating            power at max wind
        availability            1 - % maintenance down time
        capacity                ratio of assumed wind level to max wind
        date_time               datetime object
        economic_lifespan       number of years in economic life
        investment_cost         investment cost
        om_cost                 operating and maintenance cost/year (full usage)
        """
        self._id = id
        self._power_rating = power_rating
        self._availability = availability
        self._capacity = capacity
        self._date_time = date_time
        self._economic_lifespan = economic_lifespan
        self._investment_cost = investment_cost
        self._om_cost = om_cost

    @classmethod
    def init_from_database(cls, cls_dict):
        """WindTurbine class method reads dictionary from database info and calls constructor"""
        return cls(
            id = cls_dict["id"],
            power_rating = cls_dict["attributes"]["wt_power"],
            availability = cls_dict["attributes"]["wt_availability"],
            capacity = cls_dict["attributes"]["wt_capacity"],
            date_time = None,
            economic_lifespan = cls_dict["attributes"]["wt_economic_lifespan"],
            investment_cost = cls_dict["attributes"]["wt_investment_cost"],
            om_cost = cls_dict["attributes"]["wt_om_cost"],
        )

    def update_current_conditions(self, date_time, weather):
        """Update datetime"""
        self._date_time = date_time

    def _validate_params(self):
        """Verify parameter values are in acceptable ranges"""
        if self._power_rating < defaults.EPSILON:
            raise ValueError("Wind turnbine size is too low, should be greater than 0")
        if self._availability < defaults.EPSILON or self._availability > 1.0:
            raise ValueError("Wind turbine availability should be in (0,1]")
        if self._capacity < defaults.EPSILON or self._capacity > 1.0:
            raise ValueError("Wind turbine capacity should be in (0,1]")

    def update(self, power_rating):
            self._power_rating = power_rating

    def _power(self):
        """Power generated"""
        self._validate_params()
        time = self._date_time.time()
        hours = time.hour + time.minute/60.0 + time.second/3600.0
        scale = 1.0 if hours >= 8 and hours <= 19 else 3.0
        return scale * self._power_rating * self._capacity * self._availability

    def _energy_output(self, duration):
        """Energy generated over an input duration of time"""
        energy_output = self._power() * duration
        return energy_output

    def _maintenance_time(self, duration_generation):
        """Maintenance time duration for input duration of generation time"""
        self._validate_params()
        return duration_generation * (1-self._availability) / self._availability

    def _release(self, energy):
        """Output energy to grid (no action required for wind turbine)"""
        pass

    def sizing_max_multiplier(self):
        """multiplier for design of experiments max when sizing DERs"""
        return 1.0/(self._capacity * self._availability)
