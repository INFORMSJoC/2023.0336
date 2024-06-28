from datetime import timedelta
from src.utils import TimePeriod, TimeStep
from src.reports import Metrics
import src.data.mysql.energy_management_systems as database_energy_management_systems
import src.data.mysql.powerloads as database_powerloads

class CoreSimulation(object):

    def __init__(self, grid, energy_management_system_id, powerload_id, weather, 
                 start_datetime=None, end_datetime=None, 
                 extend_proportion=0.0):
        """Simulation constructor __init__

        Keyword arguments:
        grid                            a grid
        energy_management_system_id     database id for energy management system
        powerload_id                    database id of power load profile
        start_datetime                  datetime object set to start of simulation
        end_datetime                    datetime object set to end of simulation
        weather                         weather object with distributions
        extend_proportion               extend the timeframe by the specified proportion
        """
        self.grid = grid
        self._energy_management_system = database_energy_management_systems.get_parameter_name(energy_management_system_id)
        self._powerload_id = powerload_id
        self._weather = weather
        self._start_datetime = start_datetime
        self._end_datetime = end_datetime
        self._extend_proportion = extend_proportion
        self.timesteps = None
        self._load()

    def _load(self):
        """Construct list of timesteps in chronological order
        Extend the timeframe by a specified input proportion of timesteps"""
        self.timesteps = []
        powerload_info = database_powerloads.get_single(self._powerload_id, objectFlag=True)
        start = powerload_info["startdatetime"]
        end = powerload_info["enddatetime"]
        if self._start_datetime is not None:
            if self._start_datetime < start - timedelta(seconds=1):
                raise Exception("Simulation _load failed because start datetime specified is before beginning of powerload timeline.")
            if self._start_datetime > end + timedelta(seconds=1):
                raise Exception("Simulation _load failed because start datetime specified is after end of powerload timeline.")
            start = self._start_datetime
        if self._end_datetime is not None:
            if self._end_datetime < start - timedelta(seconds=1):
                raise Exception("Simulation _load failed because end datetime specified is before the start datetime specified.")
            if self._end_datetime > end  + timedelta(seconds=1):
                raise Exception("Simulation _load failed because end datetime specified is after end of powerload timeline.")
            end = self._end_datetime
        if end <= start:
            raise Exception("Simulation _load failed because end datetime specified does not occur after start datetime specified.")
        for i in range(0,len(powerload_info["data"])):
            if powerload_info["data"][i]["startdatetime"] < start: continue
            if powerload_info["data"][i]["enddatetime"] > end: continue
            tp = TimePeriod(
                start = powerload_info["data"][i]["startdatetime"],
                mid = powerload_info["data"][i]["middatetime"],
                end = powerload_info["data"][i]["enddatetime"],
            )
            self.timesteps.append(TimeStep(
                time_period=tp,
                power_load=powerload_info["data"][i]["powerload"],
                sun_weight=1.0, 
            ))
            start = tp.end()
        if len(self.timesteps) == 0:
            raise Exception("Simulation _load failed start time {0} and end time {1} are too close together;".format(start, end) \
                            + " no timesteps to simulate\n")
        if self._extend_proportion > 0.0:
            last_timestep = self.timesteps[-1]
            num_extra_timesteps = int(self._extend_proportion * len(self.timesteps))
            i = 0
            while i < num_extra_timesteps:
                timestep_to_duplicate = self.timesteps[i % len(self.timesteps)]
                tp = TimePeriod(
                    start = last_timestep.time_period().end(),
                    mid = last_timestep.time_period().end() + timedelta(
                        hours=timestep_to_duplicate.time_period().duration()/2.0
                    ),
                    end = last_timestep.time_period().end() + timedelta(
                        hours=timestep_to_duplicate.time_period().duration()
                    ),
                )
                last_timestep = TimeStep(
                    time_period = tp,
                    power_load = timestep_to_duplicate.power_load(),
                    sun_weight = timestep_to_duplicate.sun_weight(),
                )
                self.timesteps.append(last_timestep)
                i += 1
        online_ratio = {}
        for generator in self.grid.get_generators():
            online_ratio[generator] = 1.0
        for timestep in self.timesteps:
            timestep.set_online_ratio(online_ratio)

    def _get_time_periods(self):
        """Return list of time periods"""
        time_periods = []
        for timestep in self.timesteps:
            time_periods.append(timestep.time_period())
        return time_periods

    def _operate_grid(self, timestep, previous_case=None):
        """Update grid parameters for input timestep, then generate power"""
        self._weather.update(timestep.time_period())
        self.grid.update_current_conditions(timestep, self._weather)
        power_generation = self.grid.operate(
            energy_management_system = self._energy_management_system,
            previous_case = previous_case,
            load = timestep.power_load(),
            duration = timestep.time_period().duration(),
        )
        return power_generation

    def _run(self):
        """Iterate through timesteps, operate grid and store info"""
        case = None
        for timestep in self.timesteps:
            timestep.set_grid_state(
                self._operate_grid(
                    timestep=timestep,
                    previous_case=case,
                )
            )
            case = timestep.grid_state().case()

    def _clear_run(self, diesel_level):
        """Reset grid state at each time period to 'None'
        Reset batteries to starting charge levels"""
        self.grid.reset_batteries()
        for timestep in self.timesteps:
            timestep.set_grid_state(None)
        self.grid.reset_fuel(diesel_level)

    def run(self):
        """Run simulation"""    
        diesel_level = self.grid.get_diesel_level()
        self._run()
        metrics = Metrics(self.timesteps)
        self._clear_run(diesel_level)
        return metrics

    def peak_load(self):
        """Return peak load"""
        peak_load = 0.0
        for timestep in self.timesteps:
            if timestep.power_load() > peak_load:
                peak_load = timestep.power_load()
        return peak_load

    def der_sizing_initialize(self):
        """Return peak load and generator dict for sizing method"""
        return self.peak_load(), self.grid.get_generator_dict()
    
    def der_sizing_load_design(self, initial_energy_resources, design_specs):
        """a more generalized version may be needed
        design specs can currently only accomodate component ratings"""
        component_ratings = design_specs
        self.grid.update_components_doe(initial_energy_resources, component_ratings)
