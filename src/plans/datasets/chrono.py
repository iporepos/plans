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

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from plans.datasets.core import *


# ------------- TIME SERIES OBJECTS -------------  #


class RainSeries(TimeSeries):
    """
    A class for representing and working with rainfall time series data.

    The ``RainSeries`` class extends the ``TimeSeries`` class and focuses on handling rainfall data.

    """

    def __init__(self, name="MyRainfallSeries", alias=None):
        """Initialize a RainSeries object.

        :param name: str, optional
            Name of the rainfall series. Default is "MyRainfallSeries".
        :type name: str

        :param alias: str, optional
            Alias for the rainfall series. Default is None.
        :type alias: str

        """
        # Use the superior initialization from the parent class (TimeSeries)
        super().__init__(name, alias=alias)
        self.varname = "Rain"
        self.varfield = "P"
        self.units = "mm"
        # Overwrite attributes specific to RainSeries
        self.name_object = "Rainfall Time Series"
        self.agg = "sum"  # Aggregation method, set to "sum" by default
        self.gapsize = (
            7 * 72
        )  # Maximum gap size of 1 week assuming measure device turns off when is not raining
        self.outlier_min = 0
        self.rawcolor = "darkgray"

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


class TempSeries(TimeSeries):
    """A class for representing and working with temperature time series data.

    The ``TemperatureSeries`` class extends the ``TimeSeries`` class and focuses on handling temperature data.

    **Examples**

    .. code-block:: python

        temperature_data = TempSeries(name="Temperature2022", alias="Temp2022")


    """

    def __init__(self, name="MyTemperatureSeries", alias=None):
        """
        Initialize a TempSeries object.

        :param name: Name of the temperature series. Default is "MyTemperatureSeries".
        :type name: str
        :param alias: Alias for the temperature series. Default is None.
        :type alias: str

        """
        # Use the superior initialization from the parent class (TimeSeries)
        super().__init__(name, alias=alias)
        self.varname = "Temperature"
        self.varalias = "Temp"
        self.varfield = "Temp"
        self.units = "Celcius"
        # Overwrite attributes specific
        self.name_object = "Temp Time Series"
        self.agg = "mean"  # Aggregation method, set to "sum" by default
        self.gapsize = 6  # Maximum gap size of 6 hours assuming hourly Temperature
        self.datarange_max = 50
        self.datarange_min = -20
        self.rawcolor = "orange"


class StageSeries(TimeSeries):
    """
    A class for representing and working with river stage time series data.

    The ``StageSeries`` class extends the ``TimeSeries`` class and focuses on handling river stage data.
    """

    def __init__(self, name="MyStageSeries", alias=None):
        """Initialize a StageSeries object.

        :param name: Name of the river stage series. Default is "MyStageSeries".
        :type name: str
        :param alias: Alias for the river stage series. Default is None.
        :type alias: str

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
        """Get all metadata from the base object.

        :return: metadata
        :rtype: dict

        **Notes:**

        - Metadata includes information from the base class (TimeSeries) and additional TempSeries-specific attributes.
        - The returned dictionary contains key-value pairs with metadata information.


        """
        # Get metadata from the base class (TimeSeries)
        base_metadata = super().get_metadata()
        # Additional TimeSeries-specific metadata
        extra_metadata = {
            "UpstreamArea": self.upstream_area,
        }
        # Combine both base and specific metadata
        base_metadata.update(extra_metadata)
        return base_metadata


class FlowSeries(TimeSeries):
    """A class for representing and working with streamflow time series data."""

    def __init__(self, name="MyFlowSeries", alias=None):
        """Initialize a FlowSeries object.

        :param name: str, optional
            Name of the streamflow series. Default is "MyFlowSeries".
        :type name: str

        :param alias: str, optional
            Alias for the flow

        """
        # Use the superior initialization from the parent class (TimeSeries)
        super().__init__(name, alias=alias)
        self.varname = "Flow"
        self.varfield = "Q"
        self.units = "m3/s"
        # Overwrite attributes specific
        self.name_object = "Flow Time Series"
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


class TempSeriesSamples(TimeSeriesSpatialSamples):
    # todo docstring

    def __init__(self, name="MyTempSColection"):
        # todo docstring
        super().__init__(name=name, base_object=TempSeries)
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
        # todo docstring
        """
        Set data for the time series collection from a info DataFrame.

        **Notes:**

        - The ``set_data`` method populates the time series collection with data based on the provided DataFrame.
        - It creates time series objects, loads data, and performs additional processing steps.
        - Adjust ``skip_process`` according to your data processing needs.

        :param df_info: class:`pandas.DataFrame`
            DataFrame containing metadata information for the time series collection.
            This DataFrame is expected to have matching fields to the metadata keys.

            Required fields:

            - ``Id``: int, required. Unique number id.
            - ``Name``: str, required. Simple name.
            - ``Alias``: str, required. Short nickname.
            - ``Units``: str, required. Units of data.
            - ``VarField``: str, required. Variable column in data file.
            - ``DtField``: str, required. Date-time column in data file
            - ``File``: str, required. Name or path to data time series ``csv`` file.
            - ``X``: float, required. Longitude in WGS 84 Datum (EPSG4326).
            - ``Y``: float, required. Latitude in WGS 84 Datum (EPSG4326).
            - ``Code``: str, required
            - ``Source``: str, required
            - ``Description``: str, required
            - ``Color``: str, required
            - ``UpstreamArea``: float, required


        :type df_info: class:`pandas.DataFrame`

        :param src_dir: str, optional
            Path for source directory in the case for only file names in ``File`` column.
        :type src_dir: str

        :param filter_dates: list, optional
            List of Start and End dates for filter data
        :type filter_dates: str




        """
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
