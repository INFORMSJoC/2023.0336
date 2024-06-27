import os
import src.utils.helpers as util_helpers
import src.data.mysql.simulate as database_simulate

class Simulate(object):

    def __init__(self, core_sim):
        self._core_sim = core_sim

    def to_database(self, id, metrics):
        """write the metrics to database"""
        database_simulate.metrics_add(id, metrics.output_to_dict())

    def results_to_disk(self, results_dir, metrics):
        """write the metrics to database"""
        metrics.results_to_csv(os.path.join(results_dir,util_helpers.CORE_SIM_RESULTS_FILENAME))

    def run(self, results_dir=None, database_id=None):
        """Run the simulation"""
        metrics = self._core_sim.run()
        if results_dir is not None: self.results_to_disk(results_dir, metrics)
        if database_id is not None: self.to_database(database_id, metrics)
