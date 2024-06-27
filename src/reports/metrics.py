import os
from src.components import defaults

class Metrics(object):

    _EPSILON = 10**-10

    def __init__(self, timesteps):
        """Metrics constructor __init__

        Keyword arguments:
        timesteps          list of TimeStep objects
        """
        self.power, self.deficit = _power(timesteps)
        self.state_of_charge = _state_of_charge(timesteps)
        self.power_availability_ratio = _power_availability_ratio(timesteps)
        self.load_satisfaction_ratio = _load_satisfaction_ratio(timesteps)
        self._available_power_by_type(timesteps)

    def _available_power_by_type(self, timesteps):
        """Available power dictionary"""
        self.available_power = {}
        self.excess_power = {}
        types = _generator_types(timesteps[0])
        for s in timesteps:
            self.available_power[s] = {}
            self.excess_power[s] = {}
            for t in types:
                self.available_power[s][t] = s.grid_state().available_power_by_type(t)
                self.excess_power[s][t] = self.available_power[s][t] - self.power[s][t]

    def results_to_csv(self, filename=None, round_output=False):
        """Write csv file with data formatted to match Microgrid Excel tool"""
        timesteps = sorted(list(self.power.keys()), key=lambda s: s.time_period().start())
        types = list(self.power[timesteps[0]].keys())
        earliest_datetime = min([s.time_period().start() for s in timesteps])
        csv = "startDate,endDate,startTime,endTime"
        for type in types:
            csv += "," + type
        csv += ",excess,stateOfCharge"
        if timesteps[0].grid_state(): csv += ",case"
        csv += "\n"
        for timestep in timesteps:
            start_datetime = timestep.time_period().start()
            end_datetime = timestep.time_period().end()
            start_time = start_datetime - earliest_datetime
            end_time = end_datetime - earliest_datetime
            csv += start_datetime.strftime("%Y-%m-%d %H:%M:%S") + ","
            csv += end_datetime.strftime("%Y-%m-%d %H:%M:%S") + ","
            csv += str(start_time.total_seconds()/60.0) + ","
            csv += str(end_time.total_seconds()/60.0)
            excess = 0.0
            for type in types:
                csv += "," + str(
                    round(self.power[timestep][type],3) if round_output else self.power[timestep][type]
                )
                excess += self.power[timestep][type]
            csv += ","+str(
                round(excess,3) if round_output else excess
            )+"," + str(self.state_of_charge[timestep])
            if timestep.grid_state(): csv += ","+str(timestep.grid_state().case())
            csv += "\n"
        if not filename:
            return csv
        if not os.path.exists(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename))
        with open(filename, 'w') as f:
            f.write(csv)

    def deficit_percentage(self):
        count = 0
        for timestep in self.power:
            if self.deficit[timestep] < -self._EPSILON:
                count += 1
        return count / len(self.power)
    
    def excess_percentage(self):
        count = 0
        for timestep in self.power:
            excess = 0.0
            for der_type in self.available_power[timestep].keys():
                excess += self.available_power[timestep][der_type] - self.power[timestep][der_type]
            if excess > 100 * self._EPSILON:
                count += 1
        return count / len(self.power)
    
    def unused_percentage(self, type):
        count = 0
        ratio = 0
        for timestep in self.available_power:
            if self.available_power[timestep][type] > 100*self._EPSILON:
                if self.power[timestep][type] > 100*self._EPSILON: # differentiate battery charging vs. discharging
                    ratio += (self.available_power[timestep][type] - self.power[timestep][type])/self.available_power[timestep][type]
                    count += 1
        time_used_ratio = count / len(self.available_power.keys()) if len(self.available_power.keys()) > 0 else 0
        return ratio / count if count > 0 else -1, time_used_ratio


def _generator_types(timestep):
    """Return list of generator types included in input TimeStep object"""
    types = set()
    for generator in timestep.online_ratio():
        types.add(generator.__class__.__name__)
    return sorted(list(types))

def _power(timesteps):
    """Power dictionary"""
    power = {}
    deficit = {}
    types = _generator_types(timesteps[0])
    for timestep in timesteps:
        power[timestep] = {}
        power[timestep][defaults.LOAD] = -1 * timestep.power_load()
        deficit[timestep] = -1 * timestep.power_load()
        for type in types:
            power[timestep][type] = timestep.grid_state().power_supply_type(type)
            deficit[timestep] += power[timestep][type]
    return power, deficit

def _state_of_charge(timesteps):
    """State of charge dictionary"""
    state_of_charge = {}
    for timestep in timesteps:
        state_of_charge[timestep] = timestep.grid_state().state_of_charge()
    return state_of_charge

def _power_availability_ratio(timesteps):
    """% of power available relative to non-degraded power"""
    ratio = {}
    for timestep in timesteps:
        if timestep.grid_state().non_degraded_power() > defaults.EPSILON:
            ratio[timestep] = timestep.grid_state().available_power() \
                            / timestep.grid_state().non_degraded_power()
        else:
            ratio[timestep] = 1.0
    return ratio

def _load_satisfaction_ratio(timesteps):
    """% of load met at each time step"""
    load_satisfaction_ratio = {}
    for timestep in timesteps:
        load_satisfaction_ratio[timestep] = timestep.power_supply_ratio()
    return load_satisfaction_ratio
