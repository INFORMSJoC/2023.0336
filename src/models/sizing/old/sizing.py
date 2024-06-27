import os
import json
import src.utils as utils
from src.components import defaults as component_defaults
import logging

class Rightsize(object):

    """Method documented in Reich & Oriti 2021 (limited to diesel, photovoltaic, battery).
    Replaced with more general sizing method in sizing.py,
    but code maintained for comparison purposes only."""

    _EPSILON = 10 * component_defaults.EPSILON
    _DEFICIT_CUTOFF = 0.0
    _INFTY = 10**10
    _INFTY_CHECK = _INFTY / 2.0

    def __init__(self, sim, step_size_b, step_size_dg, step_size_pv, dirpath=None):
        self.sim = sim
        self.step_size_b = step_size_b
        self.step_size_dg = step_size_dg
        self.step_size_pv = step_size_pv
        self.solutions = None
        self._run(dirpath)

    def to_csv(self, filename):
        """Write csv file with data formatted to match Microgrid Excel tool"""
        components = [
            component_defaults.DIESEL_GENERATOR,
            component_defaults.PHOTOVOLTAIC_PANEL,
            component_defaults.BATTERY,
        ]
        csv = ""
        for c in components:
            csv += c + ","
        csv += "\n"
        for s in self.solutions:
            for c in components:
                csv += str(s[c]) + ","
            csv += "\n"
        if not os.path.exists(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename))
        with open(filename, 'w') as f:
            f.write(csv)

    def _find_min_capacity(self, dg_power, b_energy, pv_power, step_size, source):
        component_ratings = {
            component_defaults.DIESEL_GENERATOR:max(dg_power, self._EPSILON),
            component_defaults.BATTERY:max(b_energy, self._EPSILON),
            component_defaults.PHOTOVOLTAIC_PANEL:max(pv_power, self._EPSILON),
        }
        level = 0.0
        deficit_percentage = 1.0
        step_size_dynamic = step_size / 2.0
        increase_step = True
        while increase_step or step_size_dynamic > step_size or \
                                    deficit_percentage > self._DEFICIT_CUTOFF:
            if deficit_percentage <= self._DEFICIT_CUTOFF:
                increase_step = False
            if increase_step:
                step_size_dynamic *= 2.0
            elif step_size_dynamic > step_size:
                step_size_dynamic /= 2.0
            if deficit_percentage > self._DEFICIT_CUTOFF:
                level += step_size_dynamic
            elif level - step_size_dynamic >= 0.0:
                level -= step_size_dynamic
            else:
                level = 0.0
            component_ratings[source] = max(level, self._EPSILON)
            self.sim.grid.update_components(component_ratings)
            metrics = self.sim.run_simulation()
            deficit_percentage = metrics.deficit_percentage()
            logging.debug("--",(level, deficit_percentage))
        return level, metrics

    def _find_min_capacity_from_max(self, dg_power, b_energy, pv_power, step_size, source):
        component_ratings = {
            component_defaults.DIESEL_GENERATOR:max(dg_power, self._EPSILON),
            component_defaults.BATTERY:max(b_energy, self._EPSILON),
            component_defaults.PHOTOVOLTAIC_PANEL:max(pv_power, self._EPSILON),
        }
        level = component_ratings[source]
        deficit_percentage = 0.0
        increase_step = True if level > step_size else False
        step_size_dynamic = step_size / 2.0
        first_pass = True
        while first_pass or increase_step or step_size_dynamic > step_size or \
                                    deficit_percentage > self._DEFICIT_CUTOFF:
            first_pass = False
            if deficit_percentage > self._DEFICIT_CUTOFF or level < self._EPSILON:
                increase_step = False
            if increase_step or step_size_dynamic < step_size:
                step_size_dynamic *= 2.0
            elif step_size_dynamic > step_size:
                step_size_dynamic /= 2.0
            if deficit_percentage > self._DEFICIT_CUTOFF:
                level += step_size_dynamic
            elif level - step_size_dynamic >= 0.0:
                level -= step_size_dynamic
            else:
                level = 0.0
            component_ratings[source] = max(level, self._EPSILON)
            self.sim.grid.update_components(component_ratings)
            metrics = self.sim.run_simulation()
            deficit_percentage = metrics.deficit_percentage()
            logging.debug("++",(level, deficit_percentage))
        return level, metrics

    def _feasible_size_exists(self, diesel_power, battery_energy):
        self.sim.grid.update_components({
            component_defaults.DIESEL_GENERATOR:max(diesel_power, self._EPSILON),
            component_defaults.BATTERY:max(battery_energy, self._EPSILON),
            component_defaults.PHOTOVOLTAIC_PANEL:self._INFTY,
        })
        metrics = self.sim.run_simulation()
        deficit_percentage = metrics.deficit_percentage()
        return False if deficit_percentage > 0.0 else True

    def _dominated(self, sol, solutions):
        dg = component_defaults.DIESEL_GENERATOR
        pv = component_defaults.PHOTOVOLTAIC_PANEL
        b = component_defaults.BATTERY
        for s in solutions:
            if s[dg] <= sol[dg] + component_defaults.EPSILON and \
                s[pv] <= sol[pv] + component_defaults.EPSILON and \
                s[b] <= sol[b] + component_defaults.EPSILON:
                return True
        return False

    def _run(self, dirpath):
        peak_load=self.sim.peak_load()
        solutions = []
        dg_power = 0.0
        while dg_power < peak_load + self.step_size_dg:
            pv_power = self._INFTY
            b_step_size_dynamic = self.step_size_b
            b_energy, metrics = self._find_min_capacity(
                dg_power,
                0.0,
                pv_power,
                self.step_size_b,
                component_defaults.BATTERY
            )
            sol_found = False
            while pv_power >= self.step_size_pv:
                # print((dg_power, b_energy, pv_power))
                if self._feasible_size_exists(dg_power, b_energy):
                    if pv_power > self._INFTY_CHECK:
                        pv_power, metrics = self._find_min_capacity(
                            dg_power,
                            b_energy,
                            pv_power,
                            self.step_size_pv,
                            component_defaults.PHOTOVOLTAIC_PANEL,
                        )
                    else:
                        pv_power, metrics = self._find_min_capacity_from_max(
                            dg_power,
                            b_energy,
                            pv_power,
                            self.step_size_pv,
                            component_defaults.PHOTOVOLTAIC_PANEL,
                        )
                    b_prev = b_energy
                    if b_step_size_dynamic > self.step_size_b:
                        b_energy, metrics = self._find_min_capacity_from_max(
                            dg_power,
                            b_energy,
                            pv_power,
                            self.step_size_b,
                            component_defaults.BATTERY,
                        )
                    solution = {
                        component_defaults.DIESEL_GENERATOR:dg_power,
                        component_defaults.BATTERY:b_energy,
                        component_defaults.PHOTOVOLTAIC_PANEL:pv_power,
                    }
                    if not self._dominated(solution, solutions):
                        solutions.append(solution)
                        sol_found = True
                        if dirpath:
                            sol_name = utils.get_dirname(
                                diesel_val=dg_power,
                                photovoltaic_val=pv_power,
                                battery_val=b_energy,
                            )
                            metrics.results_to_csv(os.path.join(dirpath, sol_name, utils.SIM_RESULTS_FILENAME))
                            with open(os.path.join(dirpath, sol_name, utils.MICROGRID_DESIGN_FILENAME), "wt", encoding="utf-8") as f:
                                json.dump(solution, f, indent=4)
                        print(solution)
                    elif sol_found:
                        b_step_size_dynamic *= 2.0
                b_energy += b_step_size_dynamic
            dg_power += self.step_size_dg
        self.solutions = solutions
