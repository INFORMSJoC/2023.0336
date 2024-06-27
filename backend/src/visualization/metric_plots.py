import os
from src.visualization import TwoDimensionalPlot

class MetricPlots(object):

    def __init__(self, metrics, dirpath=None):
        """Simulation constructor __init__

        Keyword arguments:
        metrics               a metrics object
        """
        self._metrics = metrics
        self._dirpath = dirpath
        if dirpath and not os.path.isdir(dirpath):
            os.makedirs(dirpath)

    def power(self, preview=False):
        """Plot power vs. time"""
        plot = TwoDimensionalPlot.init_by_dict_of_dicts(
            timestep_key_dict=self._metrics.power
        )
        plot.construct(
            xlabel="Time",
            ylabel="Power Supplied (kW)",
            preview=preview,
            filename=os.path.join(self._dirpath, "power-supplied.png"),
        )
    
    def available_power(self, preview=False):
        """Plot available power vs. time"""
        plot = TwoDimensionalPlot.init_by_dict_of_dicts(
            timestep_key_dict=self._metrics.available_power
        )
        plot.construct(
            xlabel="Time",
            ylabel="Power Available (kW)",
            preview=preview,
            filename=os.path.join(self._dirpath, "power-available.png"),
        )

    def excess_power(self, preview=False):
        """Plot excess power vs. time"""
        plot = TwoDimensionalPlot.init_by_dict_of_dicts(
            timestep_key_dict=self._metrics.excess_power
        )
        plot.construct(
            xlabel="Time",
            ylabel="Power Excess (kW)",
            preview=preview,
            filename=os.path.join(self._dirpath, "power-excess.png"),
        )

    def state_of_charge(self, preview=False):
        """Plot state of charge vs. time"""
        plot = TwoDimensionalPlot.init_by_dict(
            timestep_key_dict=self._metrics.state_of_charge
        )
        plot.construct(
            xlabel="Time",
            ylabel="State of Charge",
            preview=preview,
            filename=os.path.join(self._dirpath, "state_of_charge.png"),
        )

    def deficit(self, preview=False):
        """Plot deficit vs. time"""
        plot = TwoDimensionalPlot.init_by_dict(
            timestep_key_dict=self._metrics.deficit
        )
        plot.construct(
            xlabel="Time",
            ylabel="Power Deficit (kW)",
            preview=preview,
            filename=os.path.join(self._dirpath, "deficit.png"),
        )

    def microgrid_performance(self, preview=False):
        """Plot microgrid performance vs. time"""
        plot = TwoDimensionalPlot.init_by_dict(
            timestep_key_dict=self._metrics.power_availability_ratio
        )
        plot.construct(
            xlabel="Time",
            ylabel="Microgrid Performance",
            preview=preview,
            filename=os.path.join(self._dirpath, "microgrid_performance.png"),
        )

    def load_satisfied(self, preview=False):
        """Plot % of load satisfied vs. time"""
        plot = TwoDimensionalPlot.init_by_dict(
            timestep_key_dict=self._metrics.load_satisfaction_ratio
        )
        plot.construct(
            xlabel="Time",
            ylabel="% of Load Satisfied",
            preview=preview,
            filename=os.path.join(self._dirpath, "load_satisfied.png"),
        )  

    def all_plots(self, preview=False):
        """Run all plotting functions"""
        self.power(preview)
        self.available_power(preview)
        self.excess_power(preview)
        self.state_of_charge(preview)
        self.deficit(preview)
        self.microgrid_performance(preview)
        self.load_satisfied(preview)
