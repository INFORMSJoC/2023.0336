from src.components import defaults

class GridState(object):

    def __init__(self, case, non_degraded_power, available_power,
                    power_generation, state_of_charge):
        """GridState constructor __init__

        Keyword arguments:
        case                 code indicating use of components
        non_degraded_power   non-degraded average power in isolation mode
        available_power      available average power
        power_generation     dictionary mapping components to average power
        state_of_charge      state of charge of aggregate BESS capacity
        """
        self._case = case
        self._non_degraded_power = non_degraded_power
        self._available_power = available_power
        self._power_generation = power_generation
        self._state_of_charge = state_of_charge

    def case(self):
        return self._case

    def power_generation(self):
        return self._power_generation

    def state_of_charge(self):
        return self._state_of_charge

    def __repr__(self):
        return (f'{self.__class__.__name__}('
           f'case={self._case!r},'
           f'power_generation={self._power_generation!r},'
           f'state_of_charge={self._state_of_charge!r})')

    def non_degraded_power(self):
        """Non-degraded power to meet load (and charge BESS)"""
        non_degraded_power = 0.0
        for generator, power in self._non_degraded_power.items():
            if generator.__class__.__name__ not in [
                defaults.BATTERY,
            ]:
                non_degraded_power += power
        return non_degraded_power

    def available_power(self):
        """Total power available to meet load (and charge BESS)"""
        available_power = 0.0
        for generator, power in self._available_power.items():
            if generator.__class__.__name__ not in [
                defaults.BATTERY,
            ]:
                available_power += power
        return available_power
    
    def available_power_by_type(self, type):
        """Power available by DER type"""
        power_available = 0.0
        for generator, power in self._available_power.items():
            if generator.__class__.__name__ == type:
                power_available += power
        return power_available

    def power_supply(self):
        """Total power supplied to meet load (and charge BESS)"""
        power_supply = 0.0
        for generator, power in self._power_generation.items():
            power_supply += power
        return power_supply

    def power_supply_type(self, type):
        """Power supplied of input type to meet load (and charge BESS)"""
        power_supply = 0.0
        for generator, power in self._power_generation.items():
            if generator.__class__.__name__ == type:
                power_supply += power
        return power_supply
