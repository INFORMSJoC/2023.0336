import random
from datetime import timedelta
import src.utils as utils
from src.components import defaults as comp_defaults

class Disturbance(object):

    def __init__(self, date_time, probabilities=None, repair_times=None):
        """Grid constructor __init__

        Keyword arguments:
        date_time           datetime when disturbance event occurs
        probabilities       dictionary mapping generator types to probabilities
        repair_times        dictionary mapping generator types to repair times
        """
        self._date_time = date_time
        self._probabilities = probabilities if probabilities else dict()
        self._repair_times = repair_times if repair_times else dict()
        self._affected = {}
        self._mean_times_to_repair = {}
        self._rand_num_generator = random.Random(random.uniform(0,20000))
        self._rand_state = self._rand_num_generator.getstate()

    def __repr__(self):
        return (f'{self.__class__.__name__}('
           f'date_time={self._date_time!r},'
           f'probabilities={self._probabilities!r},'
           f'repair_times={self._repair_times!r},'
           f'affected={self._affected!r},'
           f'mean_times_to_repair={self._mean_times_to_repair!r})')

    def load_disturbances(self, disturbances:dict=None):
        for generator, probability in disturbances.items():
            self._probabilities[generator] = probability

    def load_repair_times(self, repair_times:dict=None):
        for generator, repair_time in repair_times.items():
            self._repair_times[generator] = repair_time

    def simulate(self, grid):
        """Construct dictionary generator ID --> boolean operational status"""
        self._affected = {}
        for generator in grid.get_generators():
            probability = self._probabilities[generator.__class__.__name__]
            affected = self._rand_num_generator.uniform(0, 1) <= probability
            self._affected[generator] = affected
            if affected:
                self._mean_times_to_repair[generator] = self._rand_num_generator.expovariate(
                    1.0/self._repair_times[generator.__class__.__name__]
                )

    def propogate(self, grid, time_periods):
        """Construct dictionary generator ID --> boolean operational status"""
        status = {}
        for generator in grid.get_generators():
            delay = generator.startup_delay()
            unavailable_start = None
            if delay > comp_defaults.EPSILON: # off by default (need to improve)
                unavailable_start = time_periods[0].start()
                unavailable_end = self._date_time + timedelta(hours=delay)
            if self._affected[generator]:
                if unavailable_start is None: unavailable_start = self._date_time
                unavailable_end = self._date_time + timedelta(
                    hours=self._mean_times_to_repair[generator]
                ) + timedelta(hours=delay)
            for time_period in time_periods:
                if unavailable_start is None:
                    online_ratio = 1.0
                elif time_period.end() <= unavailable_start:
                    online_ratio = 1.0
                elif time_period.start() >= unavailable_end:
                    online_ratio = 1.0
                elif time_period.start() >= unavailable_start and \
                        time_period.end() <= unavailable_end:
                    online_ratio = 0.0
                elif time_period.start() >= unavailable_start:
                    time_on = (time_period.end() - unavailable_end).total_seconds()/3600.0
                    online_ratio = time_on / time_period.duration()
                elif time_period.end() <= unavailable_end:
                    time_on = (unavailable_start - time_period.start()).total_seconds()/3600.0
                    online_ratio = time_on / time_period.duration()
                if time_period not in status: status[time_period] = {}
                status[time_period][generator] = online_ratio
        return status
