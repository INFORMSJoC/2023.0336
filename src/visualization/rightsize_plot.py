import os
from mpl_toolkits.mplot3d import Axes3D
import matplotlib
from cycler import cycler
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
from matplotlib.offsetbox import AnchoredText
import numpy as np
import pandas as pd
from src.components import defaults
import run.sensitivity.helpers as sensitivity_helpers

def rightsize_to_plot(df=None, inputfilename=None, battery_min=None, battery_max=None,
                        photovoltaic_min=None, photovoltaic_max=None,
                        diesel_min=None, diesel_max=None, filter=None,
                        filter_min=0.0, filter_max=1.0,
                        threshold_label=None, original_designs=True, capacity_increase=0.0,
                        preview=False, filename=None):
    if inputfilename:
        df = pd.read_csv(inputfilename)
    if battery_min:
        df = df.loc[df[defaults.BATTERY] >= battery_min]
    if battery_max:
        df = df.loc[df[defaults.BATTERY] <= battery_max]
    if photovoltaic_min:
        df = df.loc[df[defaults.PHOTOVOLTAIC_PANEL] >= photovoltaic_min]
    if photovoltaic_max:
        df = df.loc[df[defaults.PHOTOVOLTAIC_PANEL] <= photovoltaic_max]
    if diesel_min:
        df = df.loc[df[defaults.DIESEL_GENERATOR] >= diesel_min]
    if diesel_max:
        df = df.loc[df[defaults.DIESEL_GENERATOR] <= diesel_max]

    def draw(ax, df, battery_max, photovoltaic_max, dg_legend_reference):
        colors = matplotlib.rcParams["axes.prop_cycle"].by_key()['color']
        for dg in sorted(df[defaults.DIESEL_GENERATOR].unique()):
            rows = df.loc[df[defaults.DIESEL_GENERATOR] == dg]
            ax.plot(
                rows[defaults.PHOTOVOLTAIC_PANEL],
                rows[defaults.BATTERY],
                marker = "o",
                linestyle = "None",
                color = colors[dg_legend_reference.index(dg)],
                label ='${i}$'.format(i=dg),
            )

    plt.close(1) # close the unused blank figure
    figure = plt.figure(figsize=(10,5))

    def my_fmt(x,pos):
        if x >= 10000: return "{:,.0f}".format(x)
        return "{:.0f}".format(x)

    ax = figure.gca()
    y_axis_formatter = matplotlib.ticker.FuncFormatter(my_fmt)
    ax.yaxis.set_major_formatter(y_axis_formatter)
    plt.xlabel("Photovoltaic Power (kW)")
    plt.ylabel("BESS Energy (kW h)")
    zoom_subtitle = " -- Region of Interest" if battery_max and photovoltaic_max else ""
    plt.title("Rightsized Microgrid Designs"+zoom_subtitle)
    dg_legend_reference = sorted(df[defaults.DIESEL_GENERATOR].unique())
    if sensitivity_helpers.SENSITIVITY_MEETS_THRESHOLD in df.columns:
        x_max = df[defaults.PHOTOVOLTAIC_PANEL].max()
        y_max = df[defaults.BATTERY].max()
        ax.set_xlim(-.05*x_max, 1.05*x_max)
        ax.set_ylim(-.05*y_max, 1.05*y_max)
        df = df.loc[df[sensitivity_helpers.SENSITIVITY_MEETS_THRESHOLD] == True]
        if threshold_label:
            if capacity_increase == 0.0:
                title = " Rightsized Microgrid Designs\nSatifying Sensitivity Threshold "
            elif original_designs:
                title = " Rightsized Microgrid Designs Can Be Increased\nBy "\
                        +str(capacity_increase)+" Times Capacity To Satisfy Sensitivity Threshold "
            else:
                title = " Microgrid Designs With Increased Capacity By "+str(capacity_increase)+" Times "\
                    +"Rightsized Level\nSatisfying Sensitivity Threshold "
            plt.title(str(df.shape[0])+title+threshold_label)

    draw(ax, df, battery_max, photovoltaic_max, dg_legend_reference)
    plt.legend(
        title= "Diesel Generator\nPower (kW)",
        bbox_to_anchor=(1.05, 1),
        loc='upper left',
    )
    plt.tight_layout()

    if filter:
        # adjust the main plot to make room for the sliders
        plt.subplots_adjust(left=0.25, bottom=0.25)

        # Make a horizontal slider to control the frequency.
        slider = Slider(
            ax = plt.axes([0.25, 0.1, 0.65, 0.03]),
            label = filter+" coverage failure measure",
            valmin = filter_min,
            valmax = filter_max,
            valinit = filter_max,
        )

        # callback function executed when slider value changes
        # accepts a single float as its arg, so use of global vars is unavoidable
        def update(val):
            for line in ax.get_lines():
                line.remove()
            for text in ax.artists:
                text.remove()
            num_points = df.loc[df[filter] <= val].shape[0]
            percent_points = num_points / df.shape[0]
            ax.add_artist(AnchoredText(filter+" <= {:.4f}".format(val)+", "+str(num_points)+" points, {:.0%}".format(percent_points)+" of points", loc=1))
            draw(ax, df.loc[df[filter] <= val], battery_max, photovoltaic_max, dg_legend_reference)

        # register the update function with each slider
        slider.on_changed(update)

    if preview: plt.show()
    if filename:
        if not os.path.exists(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename))
        figure.savefig(filename)
    figure.clf()
    plt.close(figure)
