import os
import random
import src.utils as utils
from src.components import defaults as component_defaults

class Sensitivity(object):

    """Method documented in Reich & Sanchez 2023"""

    _EPSILON = 10 * component_defaults.EPSILON

    def __init__(self, sim, b_energy, dg_power, pv_power, num_runs, dirpath=None):
        self.sim = sim
        self._load_num_generator = random.Random(random.uniform(0,20000))
        self._load_rand_state = self._load_num_generator.getstate()
        self._reset_original_loads()
        self.b_energy = b_energy
        self.dg_power = dg_power
        self.pv_power = pv_power
        self.num_runs = num_runs
        self.deficits = None
        self._run(dirpath)

    def _reset_original_loads(self):
        if self.sim.timesteps == None: return
        self._original_loads = dict()
        for timestep in self.sim.timesteps:
            self._original_loads[timestep] = timestep.power_load()

    def _generate_random_loads(self):
        utils.perturb_random_number_generator(
            stored_state=self._load_rand_state,
            random_number_generator=self._load_num_generator,
        )
        for timestep in self.sim.timesteps:
            timestep.update_power_load(
                max(0, self._load_num_generator.normalvariate(
                    self._original_loads[timestep],
                    0.1 * self._original_loads[timestep]
                ))
            )

    def _run(self, dirpath=None):
        component_ratings = {
            component_defaults.DIESEL_GENERATOR:max(self.dg_power, self._EPSILON),
            component_defaults.BATTERY:max(self.b_energy, self._EPSILON),
            component_defaults.PHOTOVOLTAIC_PANEL:max(self.pv_power, self._EPSILON),
        }
        self.sim.grid.update_components(component_ratings)
        self.deficits = []
        for i in range(0,self.num_runs):
            self._generate_random_loads()
            metrics = self.sim.run_simulation()
            self.deficits.append(metrics.deficit_percentage())
            if dirpath:
                sol_name = utils.RUN_PREFIX+str(int(i+1))
                metrics.results_to_csv(os.path.join(dirpath, sol_name, utils.SIM_RESULTS_FILENAME))
