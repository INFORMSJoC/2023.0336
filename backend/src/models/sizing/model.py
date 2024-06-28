import math
import os
import random
import json
import src.components.defaults as component_defaults
import src.data.mysql.sizing as database_sizing
import src.data.mysql.components as database_components
import datetime
from itertools import product

""" dictionary keyed by database component_type parameterName = python class name
with values from component_spec_meta parameterName"""
_COMPONENT_SPEC_BY_TYPE_INCLUDED_IN_SIZING = { 
    component_defaults.PHOTOVOLTAIC_PANEL:["pv_power"], 
    component_defaults.WIND_TURBINE:["wt_power", "wt_peak_power"], 
    component_defaults.DIESEL_GENERATOR:["dg_power"],
    component_defaults.BATTERY:["b_energy", "b_charge_power", "b_discharge_power"]
}
_MULTIPLIER = {"b_charge_power":None, "b_discharge_power":None, "wt_peak_power":None}
_MAX_MULTIPLIER = {
    component_defaults.PHOTOVOLTAIC_PANEL:5.0,
    component_defaults.WIND_TURBINE:5.0,
    component_defaults.DIESEL_GENERATOR:1.0,
    component_defaults.BATTERY:10.0
}

class Design(dict):

    def get_name(self):
        """Returns a string representation of the design"""
        return "-".join([str(self[der_type]) for der_type in self])
    
    def may_be_dominated_by(self, design):
        """Checks if the input design may dominate the current design"""
        flag = False
        for der_type in self.keys():
            if design[der_type] > self[der_type]:
                return False
            if design[der_type] < self[der_type]:
                flag = True
        return flag
    
    def is_dominated(self, results):
        """Checks if the design is dominated by any of the input results"""
        for r in results.values():
            if r.dominates_design(self):
                return True
        return False


class Result(object):

    def __init__(self, sizing, design, deficit_percentage, excess_percentage, unused_percentage, time_used_ratio, metrics_summary_stats, parent):
        self.sizing = sizing
        self.design = design
        self.deficit_percentage = deficit_percentage
        self.excess_percentage = excess_percentage
        self.unused_percentage = unused_percentage
        self.time_used_ratio = time_used_ratio
        self.metrics_summary_stats = metrics_summary_stats
        self.parent = parent
        self.dominated_by = None

    def get_name(self):
        """Returns a string representation of the design"""
        return self.design.get_name()

    def is_dominated(self):
        """Checks if the result is dominated"""
        return self.dominated_by is not None
    
    def is_dominated_by(self, result):
        """Checks if the result is dominated by the input result"""
        if not self.design.may_be_dominated_by(result.design):
            return False
        return result.deficit_percentage <= self.deficit_percentage
    
    def dominates_design(self, design):
        """Checks if the result dominates the input design"""
        return design.may_be_dominated_by(self.design) and self.deficit_percentage == 0.0

    def set_dominated_by(self, results):
        """Sets the result that dominates the current result from the input results"""
        results_not_self = { k:v for k,v in results.items() }
        if self.get_name() in results_not_self: results_not_self.pop(self.get_name())
        for v in results_not_self.values():
            if self.is_dominated_by(v):
                self.dominated_by = v
                return

    def generate_alternative_design(self, down_flag, der_type, step_size):
        """Generates an alternative design 
        by moving up or down the levels of the input der_type 
        by the input step_size"""
        if (down_flag and self.deficit_percentage > 0.0) or (not down_flag and self.deficit_percentage == 0.0):
            return None
        index = self.sizing.levels[der_type].index(self.design[der_type])
        new_index = index-step_size if down_flag else index+step_size
        while new_index >= 0 and new_index < len(self.sizing.levels[der_type]) and \
            self.sizing.levels[der_type][new_index] == self.sizing.levels[der_type][index]:
                new_index = new_index-1 if down_flag else new_index+1
        if new_index < 0 or new_index >= len(self.sizing.levels[der_type]): return None
        new_design = Design({ k:v for k,v in self.design.items() })
        new_design[der_type] = self.sizing.levels[der_type][new_index]
        return new_design
    
    def to_csv(self):
        """Writes the result to a csv string"""
        csv = self.get_name()+","
        for der_type in self.sizing.der_types: csv += "{}".format(self.design[der_type])+","
        csv += "{:.6f}".format(self.deficit_percentage)+","+"{:.2f}".format(self.excess_percentage)
        for der_type in self.sizing.der_types: 
            csv += ","+"{:.2f}".format(self.unused_percentage[der_type]) + ","+"{:.2f}".format(self.time_used_ratio[der_type])
        csv += ","+(self.dominated_by.get_name() if self.dominated_by is not None else "")
        csv += ","+(self.parent.get_name() if self.parent is not None else "none")+"\n"
        return csv
    
    def to_database(self, id):
        """Writes the result to the database"""
        record_id = database_sizing.grid_design_add(
            id=id,
            name=self.get_name(),
            deficit_percentage=self.deficit_percentage,
            excess_percentage=self.excess_percentage,
            dominated_by=self.dominated_by.get_name() if self.dominated_by is not None else "",
            parent=self.parent.get_name() if self.parent is not None else "none",
            metrics_summary_stats = json.dumps(self.metrics_summary_stats)
        )
        for der_type in self.sizing.der_types:
            component_type_id = database_components.types_id_get(der_type)
            component_id = database_sizing.grid_component_add(
                id = record_id,
                component_type_id=component_type_id,
                unused_percentage = self.unused_percentage[der_type],
                time_steps_percentage = self.time_used_ratio[der_type],
            )
            for i in range(0, len(_COMPONENT_SPEC_BY_TYPE_INCLUDED_IN_SIZING[der_type])):
                component_spec_meta_parameter_name = _COMPONENT_SPEC_BY_TYPE_INCLUDED_IN_SIZING[der_type][i]
                multiplier = _MULTIPLIER[component_spec_meta_parameter_name] if component_spec_meta_parameter_name in _MULTIPLIER else 1.0
                database_sizing.grid_component_spec_data_add(
                    sizing_grid_component_id=component_id,
                    component_spec_meta_parameter_name=component_spec_meta_parameter_name,
                    value = self.design[der_type] * multiplier,
                )

class Sizing(object):

    def __init__(self, core_sim, num_levels):
        self.core_sim = core_sim
        self.num_levels = num_levels
        self.levels = None
        self.info = { "min":{}, "max":{}, "decimals":{}}
        self.der_types = []
        self.peak_load = None
        self.energy_resources = None
        self.results = dict() # use as ordered set with None values
        self._initialize()

    def closest_level(self, value, resource_type):
        """Returns the closest level to the input value for the input resource_type"""
        return min(self.levels[resource_type], key=lambda x:abs(x-value))

    def _initialize(self):
        """Initializes the sizing object"""                
        random.seed(0)
        self.peak_load, self.energy_resources = self.core_sim.der_sizing_initialize()
        self.energy_resources = { k:v for k,v in self.energy_resources.items() }
        for der_type, resource in self.energy_resources.items():
            if der_type == "Battery":
                _MULTIPLIER["b_charge_power"] = resource[0]._charge_power_rating / resource[0]._energy_rating
                _MULTIPLIER["b_discharge_power"] = resource[0]._power_rating / resource[0]._energy_rating
            if der_type == "WindTurbine":
                _MULTIPLIER["wt_peak_power"] = resource[0]._power_peak / resource[0]._power_rating
            self.der_types.append(der_type)
            self.info["min"][der_type] = 0
            self.info["max"][der_type] = self.peak_load * _MAX_MULTIPLIER[der_type]
            self.info["decimals"][der_type] = 0

    def _generate_levels(self, num_levels):
        """Generates levels for each DER type"""
        self.levels = {}
        for der_type in self.der_types:
            self.levels[der_type] = [ round_to_nearest_5(
                round(self.info["min"][der_type] 
                          + ((self.info["max"][der_type]-self.info["min"][der_type])*i/(num_levels-1))),
                round_up=i==num_levels-1
            ) for i in range(0,num_levels) ]

    def _simulate(self, design, parent):
        """Simulates the input design and returns the result"""
        random.seed(0)
        self.core_sim.der_sizing_load_design(self.energy_resources, design)
        metrics = self.core_sim.run()
        result = Result(
            sizing = self,
            design = design,
            deficit_percentage = metrics.deficit_percentage(),
            excess_percentage = metrics.excess_percentage(),
            unused_percentage = {t:metrics.unused_percentage(t)[0] for t in self.der_types},
            time_used_ratio = {t:metrics.unused_percentage(t)[1] for t in self.der_types},
            metrics_summary_stats = metrics.summary_stats(),
            parent = parent,
        )
        return result

    def _analyze_design(self, design, parent, results):
        """Analyzes the input design and returns the result if it is not dominated by any existing results"""
        if design is None: return None
        if results is not None and design.is_dominated(results): return None
        if design.get_name() in self.results:
            result = self.results[design.get_name()]
        else:
            result = self._simulate(design, parent)
            self.results[result.get_name()] = result
            if results is not None: result.set_dominated_by(results)
        if results is not None and result.is_dominated(): return None
        return result

    def _run_designs(self, designs, debug=False):
        """Runs the input designs""" 
        if debug: designs = [Design({'SolarPhotovoltaicPanel': 0, 'DieselGenerator': 70, 'Battery': 385})]
        for design in designs:            
            self._analyze_design(design, None, self.results)
        for result in list(self.results.values()):
            result.set_dominated_by(self.results)

    def _filter_non_dominated(self, deficit_percentage=1.0):
        """Filters non-dominated results by deficit percentage"""
        non_dominated = dict()
        for k,v in self.results.items():
            if not v.is_dominated() and v.deficit_percentage <= deficit_percentage: non_dominated[k] = v
        return non_dominated

    def _run_exact(self, num_levels=None):
        """exact algorithm performs an exhaustive search (grows exponentially), 
        but prunes branches when designs are dominated or when deficits are encountered"""
        if num_levels is None: num_levels = self.num_levels
        self._generate_levels(num_levels)
        cutoff_set = set()
        combinations = sorted(product(range(num_levels), repeat=len(self.der_types)), reverse=True)
        for combination in combinations:
            design = Design({self.der_types[i]:self.levels[self.der_types[i]][combination[i]] \
                             for i in range(len(self.der_types))})
            flag = True
            for i in range(len(self.der_types)):
                parent = list(combination)
                parent[i] = parent[i] + 1
                if tuple(parent) in cutoff_set:
                    flag = False
                    break
            if not flag:
                cutoff_set.add(combination)
                continue
            result = self._simulate(design, None)
            self.results[result.get_name()] = result
            if result.deficit_percentage > 0.0: cutoff_set.add(combination)
        for result in list(self.results.values()):
            if not result.is_dominated(): result.set_dominated_by(self.results)

    def _map_to_finer_grid(self):
        """map results to closest values in levels"""
        designs = [ Design({der_type:self.closest_level(value=val, resource_type=der_type)
                    for der_type, val in result.design.items()}) 
                    for result in self.results.values() ]
        self._run_designs(designs)

    def _run_heuristic(self):
        """heuristic algorithm first performs an exact search on a small instance size,
        then maps the solutions identified to a finer grid specified by the input number of levels,
        performs a binary search for designs followed by a linear search to refine those designs"""
        if self.num_levels <= 6: raise ValueError("num_levels must be at least 6 to run heuristic")
        print("starting exact search",datetime.datetime.now().time().strftime("%H:%M:%S"), flush=True)
        self._run_exact(num_levels=6)
        self._generate_levels(self.num_levels)
        self._map_to_finer_grid()
        print("starting binary search",datetime.datetime.now().time().strftime("%H:%M:%S"), flush=True)
        for result in list(self.results.values()):
            for i in range(0,len(self.der_types)):
                down_flag = result.deficit_percentage == 0.0
                current_result = result
                for der_type in randomize_order(self.der_types, i):
                    step_size = int(2 ** math.floor(math.log2(len(self.levels[der_type]))))
                    while (step_size >= 1):
                        new_result = current_result
                        while (new_result is not None):
                            current_result = new_result
                            design = current_result.generate_alternative_design(down_flag, der_type, int(step_size))
                            new_result = self._analyze_design(design, current_result, None)
                            if new_result is not None: 
                                self.results[new_result.get_name()] = new_result
                                if new_result.deficit_percentage > current_result.deficit_percentage: break
                            else:
                                if (not down_flag) and (current_result.deficit_percentage == 0.0) : down_flag = True
                        step_size = step_size / 2
        for result in list(self.results.values()):
            if not result.is_dominated(): result.set_dominated_by(self.results)
        print("finished binary search",datetime.datetime.now().time().strftime("%H:%M:%S"), flush=True)
        non_dominated = self._filter_non_dominated(deficit_percentage=0.0)
        for result in list(non_dominated.values()):
            current_result = result
            for i in range(len(self.der_types)):
                for der_type in self.der_types:
                    while(True):
                        design = current_result.generate_alternative_design(True, der_type, 1)
                        new_result = self._analyze_design(design, current_result, non_dominated)
                        if new_result is None: break
                        self.results[new_result.get_name()] = new_result
                        if new_result.deficit_percentage > 0.0: break
                        current_result = new_result
        for result in list(self.results.values()):
            if not result.is_dominated(): result.set_dominated_by(self.results)
        print("finished linear search",datetime.datetime.now().time().strftime("%H:%M:%S"), flush=True)

    def results_to_csv(self, results_dir=None, debug=False):
        """Returns a csv string of the results.
        Writes results to a file if results_dir is not None"""
        results_csv = "name,"+",".join(self.der_types)+","+"deficit_percentage,excess_percentage,"
        for der_type in self.der_types:
            results_csv += "unused-"+der_type+",time-steps-in-use-%-"+der_type+","
        results_csv += "dominated_by,parent\n"
        for result in self.results.values(): results_csv += result.to_csv()
        if debug: print(results_csv, flush=True)
        if results_dir is not None: 
            with open(os.path.join(results_dir,"results.csv"), "w") as f:
                print(results_csv, file=f)
        return results_csv
    
    def results_to_database(self, id):
        """Writes the results to the database"""
        database_sizing.grid_designs_remove(id)
        for result in self.results.values():
            result.to_database(id)

    def run(self, algorithm, results_dir=None, database_id=None, debug=False):
        """Runs the input algorithm and writes the results to a file or database"""
        print("running "+algorithm, flush=True)
        algorithm = str("_run_"+str(algorithm))
        if hasattr(self, algorithm) and callable(getattr(self, algorithm)):
            function_to_call = getattr(self, algorithm)  
            function_to_call()
        else:
            print(algorithm+" not found or not callable", flush=True)
            exit()
        if results_dir is not None: self.results_to_csv(results_dir, debug)
        if database_id is not None:
            self.results_to_database(database_id)

def update_results(results, result):
    """Updates the results with the input result"""
    for k in list(results.keys()):
        if results[k].is_dominated_by(result):
            results[k].dominated_by = result
            del results[k]
    results[result.get_name()] = result

def randomize_order(list_to_randomize, index_to_place_first):
    """Randomizes the order of the input list"""
    randomized = [i for i in list_to_randomize]
    randomized.pop(index_to_place_first)
    random.shuffle(randomized)
    randomized.insert(0, list_to_randomize[index_to_place_first])
    return randomized

def round_to_nearest_5(num:int, round_up=False):
    """Rounds the input number to the nearest 5"""
    last_num = int(str(num)[-1])
    num = int(str(num)[:-1]+"0")
    if last_num > 7 or round_up: return num+10
    if last_num < 3: return num
    return num+5
