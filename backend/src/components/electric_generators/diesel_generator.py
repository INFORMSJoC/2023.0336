import src.utils as utils
from src.components import Generator, defaults

class DieselGenerator(Generator):

    def __init__(self, id, power_rating, load_factor, epg_efficiency, soft_min,
                    fuel_level, startup_delay, economic_lifespan, investment_cost,
                    om_cost):
        """DieselGenerator constructor __init__

        Arguments:
        id                      unique id for component
        power_rating            max power at peak load
        load_factor             ratio of operating load to peak load
        epg_efficiency          efficiency ratio of the electrically powered governor
        soft_min                lowest ratio that avoids wet stacking
        fuel_level              volume of fuel available
        startup_delay           time delay to start up when grid power is lost
        economic_lifespan       number of years in economic life
        investment_cost         investment cost
        om_cost                 operating and maintenance cost/year (full usage)
        """
        self._id = id
        self._power_rating = power_rating
        self._load_factor = load_factor
        self._epg_efficiency = epg_efficiency
        self._soft_min = soft_min
        self._fuel_level = fuel_level if fuel_level else 0.0
        self._startup_delay = startup_delay
        self._economic_lifespan = economic_lifespan
        self._investment_cost = investment_cost
        self._om_cost = om_cost
        self._fuel_consumed = 0.0

    @classmethod
    def init_from_database(cls, cls_dict):
        """DieselGenerator class method reads dictionary from database info and calls constructor"""
        dg = cls(
            id = cls_dict["id"],
            power_rating = cls_dict["attributes"]["dg_power"],
            load_factor = cls_dict["attributes"]["dg_load"],
            epg_efficiency = cls_dict["attributes"]["dg_epg_efficiency"],
            soft_min = cls_dict["attributes"]["dg_min_load"],
            fuel_level = None,
            startup_delay = cls_dict["attributes"]["dg_startup_delay"],
            economic_lifespan = cls_dict["attributes"]["dg_economic_lifespan"],
            investment_cost = cls_dict["attributes"]["dg_investment_cost"],
            om_cost = cls_dict["attributes"]["dg_om_cost"],
        )
        dg._validate_params()
        return dg

    def _validate_params(self):
        """Verify parameter values are in acceptable ranges"""
        if self._power_rating < defaults.EPSILON:
            raise ValueError("Diesel generator size is too low, should be > 0")
        if self._load_factor < defaults.EPSILON or self._load_factor > 1:
            raise ValueError("Diesel generator load factor is too low, should be in (0,1]")
        if self._epg_efficiency < defaults.EPSILON or self._epg_efficiency > 1:
            raise ValueError("Diesel generator electrically powered governor efficiency should be in (0,1]")
        if self._fuel_level < 0 - defaults.EPSILON:
            raise ValueError("Diesel generator fuel level is too low, should be >= 0")

    def update(self, power_rating):
        self._power_rating = power_rating
        self._fuel_level = 0.0
        self._fuel_consumed = 0.0

    def startup_delay(self):
        """Time delay to become available when grid power is lost"""
        return self._startup_delay

    def _power(self):
        """Power generated (linear relationship with load factor assumed)"""
        return self._power_rating * self._load_factor

    def wet_stacking(self, power):
        """True if generating input power causes wet stacking, otherwise False"""
        return power < self._power_rating * self._soft_min

    def _fuel_cons_rate(self):
        """Fuel consumption rate (linear relationship with load factor assumed)"""
        # kWh per gallon of diesel (https://afdc.energy.gov/fuels/properties converted from BTU)
        return self._power() * self._load_factor / (37.658 * self._epg_efficiency)

    def _energy_output(self, duration):
        """Energy generated over an input duration of time"""
        fuel = min(
            self._fuel_level,
            self.fuel_for_time(duration)
        )
        energy = self._power() * fuel / self._fuel_cons_rate()
        return energy

    def fuel_for_time(self, duration):
        """Volume of fuel required to run generator for an input amount of time"""
        fuel_consumption = self._fuel_cons_rate() * duration
        return fuel_consumption

    def _fuel_for_energy(self, energy):
        """Volume of fuel required to generate an input amount of energy"""
        duration = self._generation_time(energy)
        fuel = self.fuel_for_time(duration)
        return fuel

    def refill_required(self, power, duration):
        """Refill volume of fuel required to generate an input power for a duration"""
        energy = utils.energy(power=power, duration=duration)
        fuel = min(
            self._fuel_for_energy(energy),
            self.fuel_for_time(duration)
        )
        refill = max(
            0.0,
            fuel - self._fuel_level + defaults.EPSILON
        )
        return refill

    def refill_fuel(self, fuel):
        """Refill generator with an input volume of fuel (assumes infinite fuel capacity)"""
        self._fuel_level += fuel

    def remove_fuel(self, fuel):
        """Remove fuel that was refilled solely for the purpose of computing min and max energy available"""
        self._fuel_level -= fuel

    def _release(self, energy):
        """Output energy to grid by reducing generator fuel level"""
        fuel = self._fuel_for_energy(energy)
        self._fuel_level -= fuel
        self._fuel_consumed += fuel

    def reset_fuel_consumed(self):
        """Reset fuel consumption tracker to 0.0"""
        self._fuel_consumed = 0.0

    def _fuel_cost(self, unit_cost, annual_use_factor):
        """Cost of total fuel consumed based on input unit cost and usage factor"""
        # return 1138800
        return annual_use_factor * unit_cost * self._fuel_consumed

    def _max_load_factor(self, function, *args, **kwargs):
        """Modify load factor to 1.0 for the purpose of computing max energy and fuel.
        Reset load factor to original value after computation."""
        load_factor = self._load_factor
        self._load_factor = 1.0
        value = function(*args, **kwargs)
        self._load_factor = load_factor
        return value

    def max_fuel_for_time(self, duration):
        """Maximum fuel required to run generator for an input amount of time"""
        return self._max_load_factor(self.fuel_for_time, duration)

    def max_available_energy(self, duration):
        """Maximum energy generated over an input duration of time"""
        return self._max_load_factor(self.available_energy, duration)

    def _min_load_factor(self, function, *args, **kwargs):
        """Modify load factor to soft min for the purpose of computing min energy and fuel.
        Reset load factor to original value after computation."""
        load_factor = self._load_factor
        self._load_factor = self._soft_min
        value = function(*args, **kwargs)
        self._load_factor = load_factor
        return value

    def min_fuel_for_time(self, duration):
        """Minimum fuel required to run generator for an input amount of time"""
        return self._min_load_factor(self.fuel_for_time, duration)

    def min_available_energy(self, duration):
        """Minimum energy generated over an input duration of time"""
        return self._min_load_factor(self.available_energy, duration)
