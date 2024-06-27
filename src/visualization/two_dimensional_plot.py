import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd

FIGURE = plt.figure(figsize=(10,5))

class TwoDimensionalPlot(object):

    def __init__(self, x, y,):
        self._x = x
        self._y = y

    @classmethod
    def init_by_dict_of_dicts(cls, timestep_key_dict):
        """TwoDimensionalPlot class method reads dict with timestep key and calls constructor"""
        df = pd.DataFrame.from_dict(
            { i.time_period().start():
                {j:timestep_key_dict[i][j] for j in timestep_key_dict[i].keys()}
                for i in timestep_key_dict.keys()
            },
            orient='index')
        return cls(
            x=df.index,
            y=df,
        )

    @classmethod
    def init_by_dict(cls, timestep_key_dict):
        """TwoDimensionalPlot class method reads dict with timestep key and calls constructor"""
        df = pd.DataFrame.from_dict(
            { i.time_period().start():timestep_key_dict[i]
                for i in timestep_key_dict.keys()
            },
            orient='index')
        return cls(
            x=df.index.values,
            y=df.iloc[:,0].values,
        )

    @classmethod
    def init_by_dict_for_time(cls, timestep_key_dict, t_start, t_end): #need to add:  t_start, t_end so it will filter on start and stop time within the dataframe
        """TwoDimensionalPlot class method reads dict with timestep key and calls constructor for a specifc time period"""
        df = pd.DataFrame.from_dict(
            { i.time_period().start():timestep_key_dict[i]
                for i in timestep_key_dict.keys()
            }, 
            orient='index')
        #t_start = self._dist_start_time(2)#see below
        #print(t_start, "and ", t_end)
        #t_end = self.dist_end_time(2) #need to talk to Dave about how to call these before simulate_grid.py
        #df = df.loc[t_start:t_end] #filter down to the disturbance time
        if t_start!=-1 and t_end!=-1:
            df=df.loc[t_start:t_end]
        return cls(
            x=df.index.values,
            y=df.iloc[:,0].values,
        )    

    def construct(self, xlabel, ylabel, tick_hour_spacing=24, preview=False, filename=None):
        ax = FIGURE.gca()
        ax.plot(self._x, self._y)
        ax.set(
            xlabel=xlabel,
            ylabel=ylabel,
            title=_strip_unit(ylabel)+" vs. "+_strip_unit(xlabel),
        )
        ax.grid()
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%b %H:%M'))
        ax.xaxis.set_major_locator(
            mdates.HourLocator(interval=tick_hour_spacing)
        )
        ax.tick_params(axis='x', labelrotation=70)
        lines = ax.get_lines()
        if isinstance(self._y, pd.DataFrame) and self._y.columns.size > 1:
            ax.legend(
                self._y.columns.values,
                bbox_to_anchor=(1.05, 1),
                loc='upper left',
            )
        plt.tight_layout()
        if preview: plt.show()
        if filename:
            if not os.path.exists(os.path.dirname(filename)):
                os.makedirs(os.path.dirname(filename))
            FIGURE.savefig(filename)
        FIGURE.clf()
        plt.close(FIGURE)

def _strip_unit(s):
    return s.split("(")[0].strip()
