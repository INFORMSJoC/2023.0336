class TimeStep(object):

    def __init__(self, time_period, power_load, sun_weight):
        """TimeStep constructor __init__

        Keyword arguments:
        time_period        time period object
        power_load         constant / average power load during time period
        sun_weight         sun weight as a percent of max sun during time period
        """
        self._time_period = time_period
        self._power_load = power_load
        self._sun_weight = sun_weight
        self._online_ratio = None
        self._grid_state = None

    def time_period(self):
        return self._time_period

    def power_load(self):
        return self._power_load

    def update_power_load(self, power_load):
        self._power_load = power_load

    def sun_weight(self):
        return self._sun_weight

    def update_sun_weight(self, sun_weight):
        self._sun_weight = sun_weight

    def set_online_ratio(self, online_ratio):
        self._online_ratio = online_ratio

    def online_ratio(self):
        return self._online_ratio

    def set_grid_state(self, grid_state):
        self._grid_state = grid_state

    def grid_state(self):
        return self._grid_state

    def __repr__(self):
        return (f'{self.__class__.__name__}('
           f'time_period={self._time_period!r},'
           f'power_load={self._power_load!r},'
           f'sun_weight={self._sun_weight!r},'
           f'online_ratio={self._online_ratio!r},'
           f'grid_state={self._grid_state!r})')

    def power_supply_ratio(self):
        """Percent of load supplied by power generation (capped at 1.0)"""
        ratio = 1.0
        if self._power_load > 0.0:
            ratio = min(1.0, self._grid_state.power_supply() / self._power_load)
        return ratio
