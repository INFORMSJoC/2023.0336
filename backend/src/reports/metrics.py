import os
import csv
import io
from src.utils import helpers
from src.components import defaults
import src.data.mysql.mysql_microgrid as mysql_microgrid

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
        self._diesel_consumption = _diesel_consumption(timesteps)
        self._diesel_is_wet_stacking = _diesel_is_wet_stacking(timesteps)

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

    def summary_stats(self):
        """Percent of powerload by type, including unmet powerload demand; total fuel consumption;
        Total time wet stacking"""
        timesteps = sorted(list(self.power.keys()), key=lambda s: s.time_period().start())
        types = list(self.power[timesteps[0]].keys())
        percent_powerload_energy = "Contribution as a % of Total Energy"
        total_diesel_gallons = "Diesel (gallons)"
        total_diesel_wet_stacking_hours = "Diesel Generator Wet Stacking (hours)"
        total_unmet_power_hours = "Unmet Power (hours)"
        total_co2_pounds = "CO2 (pounds)"
        unmet_energy = "Unmet Energy"
        summary_stats = { 
            percent_powerload_energy: { t:0.0 for t in types },
            total_diesel_gallons: 0.0,
            total_diesel_wet_stacking_hours: 0.0,
            total_unmet_power_hours: self.deficit_time()
        }
        for timestep in timesteps:
            for t in types:
                summary_stats[percent_powerload_energy][t] += self.power[timestep][t] * timestep.time_period().duration()
            summary_stats[total_diesel_gallons] += self._diesel_consumption[timestep]
            summary_stats[total_diesel_wet_stacking_hours] += self._diesel_is_wet_stacking[timestep] * timestep.time_period().duration()
        for t in types:
            if t == defaults.LOAD: continue
            summary_stats[percent_powerload_energy][t] /= -1 * summary_stats[percent_powerload_energy][defaults.LOAD]
        summary_stats[percent_powerload_energy][defaults.LOAD] = 0
        summary_stats[percent_powerload_energy][unmet_energy] = 1 - sum(summary_stats[percent_powerload_energy][t] for t in types)
        del summary_stats[percent_powerload_energy][defaults.LOAD]
        summary_stats[total_co2_pounds] = 22.45 * summary_stats[total_diesel_gallons]
        return summary_stats

    def results_to_csv(self, filename=None, round_output=False):
        """Write csv file with data formatted to match Microgrid Excel tool"""
        timesteps = sorted(list(self.power.keys()), key=lambda s: s.time_period().start())
        types = list(self.power[timesteps[0]].keys())
        csv = "startDate,midDate,endDate"
        for type in types:
            csv += "," + type
        csv += ",excess,stateOfCharge"
        if timesteps[0].grid_state(): csv += ",case"
        csv += "\n"
        for timestep in timesteps:
            csv += timestep.time_period().start().strftime(mysql_microgrid.DATETIMEFORMAT) + ","
            csv += timestep.time_period().mid().strftime(mysql_microgrid.DATETIMEFORMAT) + ","
            csv += timestep.time_period().end().strftime(mysql_microgrid.DATETIMEFORMAT)
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

    def deficit_time(self):
        time = 0.0
        for timestep in self.power:
            if self.deficit[timestep] < -self._EPSILON:
                time += timestep.time_period().duration()
        return time

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

    def output_to_dict(self):
        """write output to dictionary for frontend display"""
        csv_data = self.results_to_csv(round_output=True)
        list_of_dicts = [helpers.float_values(i) for i in list(csv.DictReader(io.StringIO(csv_data)))]
        return {"output":list_of_dicts, "summary_stats":self.summary_stats()}


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

def _diesel_consumption(timesteps):
    """Diesel consumption dictionary"""
    diesel_consumption = {}
    for timestep in timesteps:
        diesel_consumption[timestep] = timestep.grid_state().diesel_consumption()
    return diesel_consumption

def _diesel_is_wet_stacking(timesteps):
    """Diesel wet stacking status dictionary"""
    diesel_is_wet_stacking = {}
    for timestep in timesteps:
        diesel_is_wet_stacking[timestep] = timestep.grid_state().diesel_is_wet_stacking()
    return diesel_is_wet_stacking
