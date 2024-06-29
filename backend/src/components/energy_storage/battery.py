import src.utils as utils
from src.components import Generator, defaults

class Battery(Generator):

    def __init__(self, id, energy_rating, power_rating, charge_power_rating,
            charge_efficiency, discharge_efficiency, min_soc, max_soc,
            charge_level, economic_lifespan, investment_cost, om_cost):
        """Battery constructor __init__

        Arguments:
        id                      unique id for component
        energy_rating           max energy stored
        power_rating            max power for discharging
        charge_power_rating     max power for charging
        charge_efficiency       ratio of power in to power stored
        discharge_efficiency    ratio of energy stored to energy out
        min_soc                 min state of charge
        max_soc                 max state of charge
        charge_level            energy stored in battery
        economic_lifespan       number of years in economic life
        investment_cost         investment cost
        om_cost                 operating and maintenance cost/year (full usage)
        """

        self._id = id
        self._energy_rating = energy_rating
        self._power_rating = power_rating
        self._charge_power_rating = charge_power_rating
        self._charge_efficiency = charge_efficiency
        self._discharge_efficiency = discharge_efficiency
        self._min_soc = min_soc
        self._max_soc = max_soc
        self._charge_level = charge_level if charge_level else self._energy_rating
        self._starting_charge_percentage = self._charge_level / self._energy_rating
        self._economic_lifespan = economic_lifespan
        self._investment_cost = investment_cost
        self._om_cost = om_cost

    @classmethod
    def init_from_database(cls, cls_dict):
        """Battery class method reads dictionary from database info and calls constructor"""
        b = cls(
            id = cls_dict["id"],
            energy_rating = cls_dict["attributes"]["b_energy"],
            power_rating = cls_dict["attributes"]["b_discharge_power"],
            charge_power_rating = cls_dict["attributes"]["b_charge_power"],
            charge_efficiency = cls_dict["attributes"]["b_charge_eff"],
            discharge_efficiency = cls_dict["attributes"]["b_discharge_eff"],
            min_soc = cls_dict["attributes"]["b_min_soc"],
            max_soc = cls_dict["attributes"]["b_max_soc"],
            charge_level = None,
            economic_lifespan = cls_dict["attributes"]["b_economic_lifespan"],
            investment_cost = cls_dict["attributes"]["b_investment_cost"],
            om_cost = cls_dict["attributes"]["b_om_cost"],
        )
        b._validate_params()
        return b

    def _validate_params(self):
        """Verify parameter values are in acceptable ranges"""
        if self._energy_rating < defaults.EPSILON:
            raise ValueError("Battery size is too low, should be greater than 0")
        if self._power_rating < defaults.EPSILON:
            raise ValueError("Battery discharge power should be > 0")
        if self._charge_power_rating < defaults.EPSILON:
            raise ValueError("Battery charge power should be > 0")
        if self._charge_efficiency < defaults.EPSILON or self._charge_efficiency > 1.0:
            raise ValueError("Battery charge efficiency should be in (0,1]")
        if self._discharge_efficiency < defaults.EPSILON or self._discharge_efficiency > 1.0:
            raise ValueError("Battery discharge efficiency should be in (0,1]")
        if self._min_soc < 0.0 or self._min_soc > 1.0:
            raise ValueError("Battery min state of charge should be in [0,1]")
        if self._max_soc < defaults.EPSILON or self._max_soc > 1.0:
            raise ValueError("Battery max state of charge should be in [0,1]")
        if self._max_soc < self._min_soc:
            raise ValueError("Battery max soc should cannot be less than min soc")
        if self._charge_level < -1*defaults.EPSILON or self._charge_level > self._energy_rating:
            raise ValueError("Battery charge should be at least 0 and at most the battery size")

    def update(self, energy_rating):
        discharge_ratio = self._power_rating / self._energy_rating
        charge_ratio = self._charge_power_rating / self._energy_rating
        self._energy_rating = energy_rating
        self._power_rating = energy_rating * discharge_ratio
        self._charge_power_rating = energy_rating * charge_ratio
        self._charge_level = energy_rating

    def reset_charge(self):
        """Reset battery charge"""
        self._charge_level = self._starting_charge_percentage * self._energy_rating

    def _power(self):
        """Power generated when discharging"""
        return self._power_rating

    def _charge_power(self):
        """Power when charging"""
        return self._charge_power_rating

    def _energy_to_max_soc(self):
        """Energy required to charge battery to max state of charge"""
        energy = max(
            0,
            (self._energy_rating * self._max_soc - self._charge_level) \
                    / self._charge_efficiency,
        )
        return energy

    def energy_capacity(self, duration):
        """Energy charging capacity over an input duration"""
        energy = min(
            self._energy_to_max_soc(),
            utils.energy(
                power=self._charge_power(),
                duration=duration
            )
        )
        return energy

    def _charge_time(self, energy):
        """Duration required to receive an input amount of energy (including losses)"""
        duration = energy / self._charge_power()
        return duration

    def _charge_time_to_max_soc(self):
        """Duration required to charge battery to max soc (including losses)"""
        energy = self._energy_to_max_soc()
        return self._charge_time(energy)

    def _charge_breakdown(self, energy):
        """Split usable energy and efficiency losses"""
        usable = energy * self._charge_efficiency
        loss = energy - usable
        return usable, loss

    def _charge(self, duration):
        """Energy output for an input duration of time"""
        energy = utils.energy(
            power=self._charge_power(),
            duration=duration
        )
        usable, loss = self._charge_breakdown(energy)
        self._charge_level += usable
        return usable, loss

    def store_energy(self, power, duration):
        """Store energy for an input power supply and duration of time"""
        energy = utils.energy(power=power, duration=duration)
        duration = min(
            duration,
            self._charge_time(energy),
            self._charge_time_to_max_soc(),
        )
        usable, loss = self._charge(duration)
        return usable+loss

    def _discharge_time_to_min_soc(self):
        """Duration of time required to discharge battery to min soc (including losses)"""
        energy = max(
            0,
            self._charge_level - self._energy_rating * self._min_soc,
        )
        return self._generation_time(energy)

    def _discharge_breakdown(self, energy):
        """Split usable energy and efficiency losses"""
        return energy * self._discharge_efficiency

    def _energy_output(self, duration):
        """Energy generated over an input quantity of time"""
        output_duration = min(
            duration,
            self._discharge_time_to_min_soc(),
        )
        energy = utils.energy(
            power=self._power(),
            duration=output_duration
        )
        energy_output = self._discharge_breakdown(energy)
        return energy_output

    def _release(self, energy):
        """Output energy to grid by reducing charge level"""
        self._charge_level -= energy / self._discharge_efficiency
