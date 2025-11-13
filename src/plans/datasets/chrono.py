# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
Handle chronological (time series) datasets.

Overview
--------

# todo [major docstring improvement] -- overview
Mauris gravida ex quam, in porttitor lacus lobortis vitae.
In a lacinia nisl. Pellentesque habitant morbi tristique senectus
et netus et malesuada fames ac turpis egestas.

Example
-------

# todo [major docstring improvement] -- examples
Lorem ipsum dolor sit amet, consectetur adipiscing elit.
Nulla mollis tincidunt erat eget iaculis. Mauris gravida ex quam,
in porttitor lacus lobortis vitae. In a lacinia nisl.

.. code-block:: python

    import numpy as np
    print("Hello World!")

Mauris gravida ex quam, in porttitor lacus lobortis vitae.
In a lacinia nisl. Mauris gravida ex quam, in porttitor lacus lobortis vitae.
In a lacinia nisl.

"""
from types import NoneType

# IMPORTS
# ***********************************************************************
# import modules from other libs

# Native imports
# =======================================================================
# import {module}
# ... {develop}

# External imports
# =======================================================================
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# ... {develop}

# Project-level imports
# =======================================================================
from plans.datasets.core import *

# ... {develop}


# CONSTANTS
# ***********************************************************************


# FUNCTIONS
# ***********************************************************************


# Classes
# ***********************************************************************


# TIME SERIES
# ======================================================================

# Water Balance Series
# ----------------------------------------------------------------------


class WaterBalanceSeries(TimeSeries):

    def __init__(self, name="MyWaterBalanceSeries", alias=None):
        # Use the superior initialization from the parent class (TimeSeries)
        super().__init__(name, alias=alias)
        self.varname = "Flow"
        self.varalias = "Wb"
        self.varfield = "wb"
        self.units = "mm"
        self.name_object = "Water Balance Time Series"
        self.agg = "sum"  # Aggregation method
        self.outlier_min = 0
        self.rawcolor = "blue"
        self.datarange_max = 10000  # absurd yearly precipitation
        self.datarange_min = 0

    @staticmethod
    def view_pq_plot(ts_rain, ts_flow, specs, show=True, return_fig=False):

        # setup hard coded of Streamflow specs
        ts_flow.view_specs["zorder_data"] = 2
        ts_flow.view_specs["zorder_histh"] = 2
        ts_flow.view_specs["zorder_cdf"] = 2

        # setup hard coded Rain specs
        ts_rain.view_specs["zorder_data"] = 1
        ts_rain.view_specs["zorder_histh"] = 1
        ts_rain.view_specs["zorder_cdf"] = 1
        ts_rain.view_specs["fill"] = True
        ts_rain.view_specs["color_fill"] = None
        ts_rain.view_specs["fill_only"] = True

        output = TimeSeries.view_compare_times_series(
            ts_first=ts_flow,
            ts_second=ts_rain,
            specs=specs,
            show=show,
            return_fig=return_fig,
        )

        return output


class RainSeries(WaterBalanceSeries):
    """
    A class for representing and working with rainfall time series data.

    **Notes**

    todo notes

    **Examples**

    todo examples


    """

    def __init__(self, name="MyRainSeries", alias=None):
        # Use the superior initialization from the parent class (TimeSeries)
        super().__init__(name, alias=alias)
        self.varname = "Rain"
        self.varalias = "P"
        self.varfield = "ppt"
        # Overwrite attributes specific to RainSeries
        self.name_object = "Rain Time Series"
        self.gapsize = (
            7 * 72
        )  # Maximum gap size of 1 week assuming measure device turns off when is not raining
        self.rawcolor = "slateblue"

    def interpolate_gaps(self, inplace=False, method=None):
        # overwrite interpolation method with constant=0
        super().interpolate_gaps(method="constant", constant=0, inplace=inplace)
        return None

    def _set_frequency(self):
        super()._set_frequency()
        # overwrite gapsize to 1 week
        dict_gaps = {
            "second": int(7 * 24 * 60 * 60),
            "minute": int(7 * 24 * 3),
            "hour": int(7 * 24),
            "day": int(7),
            "month": 1,
            "year": 1,
        }
        self.gapsize = dict_gaps[self.dtres]
        return None


class StreamflowSeries(WaterBalanceSeries):
    """
    A class for representing and working with streamflow data (specific flow).

    **Notes**

    todo notes

    **Examples**

    todo examples

    """

    def __init__(self, name="MyStreaFlowSeries", alias=None):
        # Use the superior initialization from the parent class (TimeSeries)
        super().__init__(name, alias=alias)
        self.varname = "Streamflow"
        self.varalias = "Q"
        self.varfield = "q"
        # Overwrite attributes specific
        self.name_object = "Streamflow Time Series"
        self.rawcolor = "blue"

    def get_baseflow(self):

        df = StreamflowSeries.separate_baseflow(
            df=self.data, dt_field=self.dtfield, var_field=self.varfield
        )

        return df

    @staticmethod
    def separate_baseflow(df, dt_field="datetime", var_field="q"):
        dt = 1

        # central derivative
        df["delta"] = (df[var_field].shift(-1) - df[var_field].shift(1)) / (2 * dt)
        df.loc[0, "delta"] = (df[var_field].iloc[1] - df[var_field].iloc[0]) / dt
        df.loc[len(df) - 1, "delta"] = (
            df[var_field].iloc[len(df) - 1] - df[var_field].iloc[len(df) - 2]
        ) / dt

        print(df.head(15))

        v_rises = np.zeros(len(df))

        for i in range(1, len(v_rises) - 1):
            lcl_v = df[var_field].values[i]
            lcl_v_last = df[var_field].values[i - 1]
            lcl_v_next = df[var_field].values[i + 1]

            if lcl_v_last > lcl_v and lcl_v_next > lcl_v:
                v_rises[i] = lcl_v

        df_qb = df.copy()
        df_qb["Qb"] = v_rises
        df_qb["Qb"] = df_qb["Qb"].replace(0, np.nan)
        df_qb.dropna(inplace=True)

        print(df_qb.head(15))

        plt.plot(df["datetime"], df["q"])
        plt.plot(df_qb["datetime"], df_qb["Qb"], marker="o")
        plt.show()

        return df_qb


class ETSeries(WaterBalanceSeries):
    """
    A class for representing and working with ET data.

    **Notes**

    todo notes

    **Examples**

    todo examples

    """

    def __init__(self, name="MyETSeries", alias=None):
        # Use the superior initialization from the parent class
        super().__init__(name, alias=alias)
        self.varname = "ET"
        self.varfield = "et"
        # Overwrite attributes specific
        self.name_object = "ET Time Series"
        self.rawcolor = "red"


class PETSeries(WaterBalanceSeries):
    """
    A class for representing and working with PET data.

    **Notes**

    todo notes

    **Examples**

    todo examples

    """

    def __init__(self, name="MyPETSeries", alias=None):
        # Use the superior initialization from the parent class (TimeSeries)
        super().__init__(name, alias=alias)
        self.varname = "PET"
        self.varalias = "PET"
        self.varfield = "pet"
        # Overwrite attributes specific
        self.name_object = "PET Time Series"
        self.rawcolor = "darkred"


# Other
# ----------------------------------------------------------------------


class TemperatureSeries(TimeSeries):
    """
    A class for representing and working with temperature time series data.

    **Notes**

    todo notes

    **Examples**

    todo examples

    """

    def __init__(self, name="MyTemperatureSeries", alias=None):
        # Use the superior initialization from the parent class (TimeSeries)
        super().__init__(name, alias=alias)
        self.varname = "Temperature"
        self.varalias = "TAS"
        self.varfield = "tas"
        self.units = "Celcius"
        # Overwrite attributes specific
        self.name_object = "Temperature Time Series"
        self.agg = "mean"  # Aggregation method,
        self.gapsize = 6  # Maximum gap size of 6 hours assuming hourly Temperature
        self.datarange_max = 50
        self.datarange_min = -20
        self.rawcolor = "orange"


class StageSeries(TimeSeries):
    """
    A class for representing and working with river stage time series data.


    **Notes**

    todo notes

    **Examples**

    todo examples


    """

    def __init__(self, name="MyStageSeries", alias=None):
        """
        Initialize a ``StageSeries`` object.
        """
        # Use the superior initialization from the parent class (TimeSeries)
        super().__init__(name, alias=alias)
        self.varname = "Stage"
        self.varalias = "H"
        self.varfield = "H"
        self.units = "cm"
        # Overwrite attributes specific to StageSeries
        self.name_object = "Stage Time Series"
        self.agg = "mean"  # Aggregation method, set to "mean" by default
        self.gapsize = 10  # Maximum gap size allowed for data interpolation
        # Extra attributes specific to StageSeries
        self.upstream_area = None

    def get_metadata(self):
        # Get metadata from the base class (TimeSeries)
        base_metadata = super().get_metadata()
        # Additional TimeSeries-specific metadata
        extra_metadata = {
            "UpstreamArea": self.upstream_area,
        }
        # Combine both base and specific metadata
        base_metadata.update(extra_metadata)
        return base_metadata


class DischargeSeries(TimeSeries):
    """
    A class for representing and working with discharge time series data (volumentric flow).

    **Notes**

    todo notes

    **Examples**

    todo examples

    """

    def __init__(self, name="MyFlowSeries", alias=None):
        # Use the superior initialization from the parent class (TimeSeries)
        super().__init__(name, alias=alias)
        self.varname = "Discharge"
        self.varfield = "Q"
        self.varalias = self.varfield
        self.units = "m3/s"
        # Overwrite attributes specific
        self.name_object = "Discharge Time Series"
        self.agg = "mean"  # Aggregation method, set to "mean" by default
        self.gapsize = 6  # Maximum gap size of 6 hours assuming hourly Flow
        self.datarange_max = 300000  # Amazon discharge
        self.datarange_min = 0
        self.rawcolor = "navy"
        # Specific attributes
        self.upstream_area = None  # in sq km

    @staticmethod
    def view_cfcs(freqs, specs=None, show=True, colors=None, labels=None):
        import matplotlib.pyplot as plt

        default_specs = {
            "folder": "C:/data",
            "filename": "cfcs",
            "fig_format": "jpg",
            "dpi": 300,
            "width": 4,
            "height": 6,
            "xmin": 0,
            "xmax": 100,
            "ymin": 0,
            "ymin_log": 1,
            "ymax": None,
            "log": True,
            "title": "CFCs",
            "ylabel": "m3/s",
            "xlabel": "Exeed. Prob. (%)",
        }
        # get specs
        if specs is not None:
            default_specs.update(specs)
        specs = default_specs.copy()

        # --------------------- figure setup --------------------- #
        fig = plt.figure(figsize=(specs["width"], specs["height"]))  # Width, Height

        # handle min max
        if specs["ymax"] is None:
            lst_max = [freq["Values"].max() for freq in freqs]
            specs["ymax"] = max(lst_max)

        if colors is None:
            colors = ["navy" for freq in freqs]
        if labels is None:
            labels = [None for freq in freqs]

        # --------------------- plotting --------------------- #
        for i in range(len(freqs)):
            plt.plot(
                freqs[i]["Exceedance"],
                freqs[i]["Values"],
                color=colors[i],
                label=labels[i],
            )
        if labels is not None:
            plt.legend()

        # --------------------- post-plotting --------------------- #
        # set basic plotting stuff
        plt.title(specs["title"])
        plt.ylabel(specs["ylabel"])
        plt.xlabel(specs["xlabel"])
        plt.xlim(specs["xmin"], specs["xmax"])
        if specs["log"]:
            plt.ylim(specs["ymin_log"], 1.2 * specs["ymax"])
            plt.yscale("log")
        else:
            plt.ylim(specs["ymin"], 1.2 * specs["ymax"])

        # Get current axes
        ax = plt.gca()
        # Set the y-ticks more densely
        ax.set_yticks([1, 2.5, 5, 10, 25, 50, 100, 250, 500])

        # Adjust layout to prevent cutoff
        plt.tight_layout()

        # --------------------- end --------------------- #
        # show or save
        if show:
            plt.show()
            return None
        else:
            file_path = "{}/{}.{}".format(
                specs["folder"], specs["filename"], specs["fig_format"]
            )
            plt.savefig(file_path, dpi=specs["dpi"])
            plt.close(fig)
            return file_path


# ------------- TIME SERIES COLLECTIONS -------------  #


class RainSeriesSamples(TimeSeriesSpatialSamples):
    # todo docstring

    def __init__(self, name="MyRSColection"):
        # todo docstring
        super().__init__(name=name, base_object=RainSeries)
        # overwrite parent attributes
        self.name_object = "Rainfall Series Samples"
        self._set_view_specs()


class TemperatureSeriesSamples(TimeSeriesSpatialSamples):
    # todo docstring

    def __init__(self, name="MyTempSColection"):
        # todo docstring
        super().__init__(name=name, base_object=TemperatureSeries)
        # overwrite parent attributes
        self.name_object = "Temperature Series Sample"
        self._set_view_specs()


class StageSeriesCollection(TimeSeriesCluster):
    # todo docstring
    def __init__(self, name="MySSColection"):
        # todo docstring
        super().__init__(name=name, base_object=StageSeries)
        # overwrite parent attributes
        self.name_object = "Stage Series Collection"
        self._set_view_specs()

    def set_data(self, df_info, src_dir=None, filter_dates=None):
        # generic part
        super().set_data(df_info=df_info, filter_dates=filter_dates)
        # custom part
        for i in range(len(df_info)):
            name = df_info["Name"].values[i]
            self.collection[name].upstream_area = df_info["UpstreamArea"].values[i]
        self.update(details=True)
        return None


if __name__ == "__main__":
    print("Hello World")
    # todo [move to testing]
