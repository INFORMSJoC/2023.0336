from datetime import timedelta
from src.utils import TimePeriod, TimeStep
from src.reports import Metrics
import src.data.mysql.powerloads as database_powerloads

class Simulation(object):

    def __init__(self, grid, control, powerload_id, start_datetime, 
                 weather, extend_proportion=0.0, disturbance=None):
        """Simulation constructor __init__

        Keyword arguments:
        grid                    a grid
        control                 string name of grid control logic function to use
        powerload_id            database id of power load profile
        start_datetime          datetime object set to start of simulation
        weather                 weather object with distributions
        extend_proportion       extend the timeframe by the specified proportion
        disturbance             object with disturbance event information
        """
        self.grid = grid
        self._control = control
        self._powerload_id = powerload_id
        self._start_datetime = start_datetime
        self._weather = weather
        self._extend_proportion = extend_proportion
        self._disturbance = disturbance
        self.timesteps = None
        self._load()

    def _load(self):
        """Construct list of timesteps in chronological order
        Extend the timeframe by a specified input proportion of timesteps"""
        self.timesteps = []
        start = 0
        for load in database_powerloads.data_get(self._powerload_id):
            t = load["time"]
            tp = TimePeriod(
                start = self._start_datetime + timedelta(hours=start),
                end = self._start_datetime + timedelta(hours=t),
            )
            self.timesteps.append(TimeStep(
                time_period=tp,
                power_load=load["powerload"],
                sun_weight=1.0, 
            ))
            start = t
        if self._extend_proportion > 0.0:
            last_timestep = self.timesteps[-1]
            num_extra_timesteps = int(self._extend_proportion * len(self.timesteps))
            i = 0
            while i < num_extra_timesteps:
                timestep_to_duplicate = self.timesteps[i % len(self.timesteps)]
                tp = TimePeriod(
                    start = last_timestep.time_period().end(),
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

    def _simulate_disturbance(self):
        """Disturbance sets grid status at each time period"""
        if self._disturbance is None: return
        self._disturbance.simulate(self.grid)
        online_ratio = self._disturbance.propogate(
            grid=self.grid,
            time_periods=self._get_time_periods(),
        )
        for timestep in self.timesteps:
            timestep.set_online_ratio(online_ratio[timestep.time_period()])

    def _clear_disturbance(self):
        """Reset online ratio at each time period to 'None'"""
        if self._disturbance is None: return
        for timestep in self.timesteps:
            timestep.set_online_ratio(None)

    def _operate_grid(self, timestep, previous_case=None):
        """Update grid parameters for input timestep, then generate power"""
        self.grid.update_current_conditions(timestep, self._weather)
        power_generation = self.grid.operate(
            control = self._control,
            previous_case = previous_case,
            load = timestep.power_load(),
            duration = timestep.time_period().duration(),
        )
        return power_generation

    def _run(self):
        """Iterate through timesteps, operate grid and store info"""
        self._weather.perturb()
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

    def run_simulation(self):
        """Run simulation"""    
        diesel_level = self.grid.get_diesel_level()
        self._simulate_disturbance()
        self._run()
        metrics = Metrics(self.timesteps)
        self._clear_disturbance()
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
        self._simulate_disturbance()
        return self.peak_load(), self.grid.get_generator_dict()
    
    def der_sizing_load_design(self, initial_energy_resources, design_specs):
        """a more generalized version may be needed
        design specs can currently only accomodate component ratings"""
        component_ratings = design_specs
        self.grid.update_components_doe(initial_energy_resources, component_ratings)
