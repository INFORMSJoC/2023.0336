import src.utils as utils
import math

class Generator(object):
    """Parent class for all components that generate energy provides universal methods"""

    def id_(self):
        """Return the component ID"""
        return self._id

    def __repr__(self):
        return (f'{self.__class__.__name__}('
           f'id={self._id!r})')

    def update_current_conditions(self, timestep, weather):
        """Update datetime"""
        self._timeperiod = timestep.time_period()
        self._current_weather = weather.current_sample

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

    def economic_lifespan(self):
        """Economic lifespan"""
        return self._economic_lifespan if "_economic_lifespan" in dir(self) else math.inf
    
    def investment_cost(self):
        """Investment cost"""
        return self._investment_cost if "_investment_cost" in dir(self) else 0.0
    
    def om_cost(self):
        """Annual operating and maintenance cost"""
        return self._om_cost if "_om_cost" in dir(self) else 0.0

    def residual_value(self, year):
        """Residual value of generator after input number of years in service"""
        if "_economic_lifespan" not in dir(self): return 0.0
        weight = max(
            0.0,
            (self._economic_lifespan - year) / self._economic_lifespan
        )
        return weight * self._investment_cost
