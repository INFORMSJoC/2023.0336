import src.utils as utils

class Weather(object):

    def __init__(self, rand_num_generator, cloud_distribution, sun_distribution, autoregressive_proportion):
        """Weather constructor __init__

        Keyword arguments:
        rand_num_generator              random number generator for weather conditions
        cloud_distribution              cloud distribution attached to random number generator
        sun_distribution                sun distribution attached to random number generator
        autoregressive_proportion       sun weight is a function of previous sun and random num
        """
        self._rand_num_generator = rand_num_generator
        self._cloud_distribution = cloud_distribution
        self._sun_distribution = sun_distribution
        self._autoregressive_proportion = autoregressive_proportion
        self._rand_state = None
        self._sun_weight = dict()
        self._cloud_weight = dict()

    def __repr__(self):
        return (f'{self.__class__.__name__}('
           f'cloud_distribution={self._cloud_distribution!r},'
           f'sun_distribution={self._sun_distribution!r},'
           f'autoregressive_proportion={self._autoregressive_proportion!r})')

    def perturb(self):
        utils.perturb_random_number_generator(
            stored_state=self._rand_state,
            random_number_generator=self._rand_num_generator,
        )
        self._sun_weight = dict()
        self._cloud_weight = dict()

    def cloud_weight(self, date_time):
        """Values in [0,1] with 1 for no clouds and 0 for complete cloud cover"""
        if date_time not in self._cloud_weight:
            self._cloud_weight[date_time] = self._cloud_distribution()
        return self._cloud_weight[date_time]

    def sun_weight(self, date_time, prev_weight):
        """Value >= 0 of sun weight with max sun * cloud in photovoltaic panel = 1"""
        if date_time not in self._sun_weight:
            self._sun_weight[date_time] = self._autoregressive_proportion * prev_weight \
                                    + (1-self._autoregressive_proportion) * max(
                self._sun_distribution(),
                0.0,
            )
        return self._sun_weight[date_time]
