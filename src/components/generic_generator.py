import src.utils as utils

class Generator(object):
    """Parent class for all components that generate energy provides universal methods"""

    def id_(self):
        """Return the component ID"""
        return self._id

    def __repr__(self):
        return (f'{self.__class__.__name__}('
           f'id={self._id!r})')

    def update_current_conditions(self, date_time, weather):
        """Update current conditions (pass by default)"""
        pass

    def startup_delay(self):
        """Time delay to become available when grid power is lost defaults to 0.0"""
        return 0.0

    def _generation_time(self, energy):
        """Duration required to generate an input amount of energy (including losses)"""
        duration = energy / self._power()
        return duration

    def max_available_energy(self, duration):
        return self.available_energy(duration)

    def available_energy(self, duration):
        """Available energy (not including losses) for an input duration"""
        energy = self._energy_output(duration)
        return energy

    def generate_energy(self, power, duration):
        """Generate energy for an input power demand and duration"""
        energy = min(
            self.max_available_energy(duration),
            utils.energy(power=power, duration=duration)
        )
        self._release(energy)
        return energy

    def investment_cost(self):
        """Investment cost"""
        return self._investment_cost if "_investment_cost" in dir(self) else 0.0

    def om_cost(self, fuel_unit_cost, annual_use_factor):
        """Annual operating and maintenance cost"""
        om_cost = 0.0
        if "_fuel_cost" in dir(self):
            om_cost += self._fuel_cost(fuel_unit_cost, annual_use_factor)
        if "_om_cost" in dir(self): om_cost += self._om_cost
        return om_cost

    def residual_value(self, year):
        """Residual value of generator after input number of years in service"""
        if "_economic_lifespan" not in dir(self): return 0.0
        weight = max(
            0.0,
            (self._economic_lifespan - year) / self._economic_lifespan
        )
        return weight * self._investment_cost

    def sizing_max_multiplier(self):
        """multiplier for design of experiments max when sizing DERs"""
        return 1.0
