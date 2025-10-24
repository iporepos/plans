# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
Primitive classes for handling datasets.

Overview
--------

# todo [docstring] -- overview
Mauris gravida ex quam, in porttitor lacus lobortis vitae.
In a lacinia nisl. Pellentesque habitant morbi tristique senectus
et netus et malesuada fames ac turpis egestas.

Example
-------

# todo [docstring] -- examples
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
# IMPORTS
# ***********************************************************************
# import modules from other libs

# Native imports
# =======================================================================
import os, glob, copy
import warnings

# ... {develop}

# External imports
# =======================================================================
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.dates as mdates
from matplotlib.ticker import MaxNLocator
import rasterio

# ... {develop}

# Project-level imports
# =======================================================================
from plans.root import Collection, DataSet
from plans.analyst import Univar, GeoUnivar
from plans import viewer
from plans import geo

# ... {develop}


# CONSTANTS
# ***********************************************************************
# define constants in uppercase

# CONSTANTS -- Project-level
# =======================================================================
DC_NODATA = {
    "byte": 255,  # categorical/boolean maps
    "uint8": 255,  # categorical/boolean maps
    "uint16": 0,  # zone maps
    "float16": -99999,  # fuzzy maps
    "float32": -99999,  # scientific maps
}
# ... {develop}


# CONSTANTS -- Module-level
# =======================================================================
# ... {develop}


# FUNCTIONS
# ***********************************************************************

# FUNCTIONS -- Project-level
# =======================================================================


def dataframe_prepro(dataframe):
    """
    Utility function for dataframe pre-processing.

    :param dataframe: incoming dataframe
    :type dataframe: :class:`pandas.DataFrame`
    :return: prepared dataframe
    :rtype: :class:`pandas.DataFrame`
    """
    # fix headings
    dataframe.columns = dataframe.columns.str.strip()
    # strip string fields
    for i in range(len(dataframe.columns)):
        # if data type is string
        if str(dataframe.dtypes.iloc[i]) == "base_object":
            # strip all data
            dataframe[dataframe.columns[i]] = dataframe[
                dataframe.columns[i]
            ].str.strip()
    return dataframe


def get_colors(size=10, cmap="tab20", randomize=True):
    """
    Utility function to get a list of random colors

    :param size: Size of list of colors
    :type size: int
    :param cmap: Name of matplotlib color map (cmap)
    :type cmap: str
    :return: list of random colors
    :rtype: list
    """
    import matplotlib.colors as mcolors

    # Choose a colormap from matplotlib
    _cmap = plt.get_cmap(cmap)
    # Generate a list of random numbers between 0 and 1
    if randomize:
        _lst_vals = np.random.rand(size)
    else:
        _lst_vals = np.linspace(0, 1, num=size)
    # Use the colormap to convert the random numbers to colors
    _lst_colors = [mcolors.to_hex(_cmap(x)) for x in _lst_vals]
    return _lst_colors


# FUNCTIONS -- Module-level
# =======================================================================
# ... {develop}


# CLASSES
# ***********************************************************************

# CLASSES -- Project-level
# =======================================================================

# Chronological classes
# -----------------------------------------------------------------------


class TimeSeries(Univar):
    # todo docstring

    # Dunder methods
    # -------------------------------------------------------------------
    def __init__(self, name="MyTimeSeries", alias="TS0"):
        # ------------ set defaults ----------- #

        # upstream setups
        self.dtfield = "datetime"
        self.agg = "mean"
        self.cmap = "Dark2"
        self.object_alias = "TS"
        self.rawcolor = "gray"  # alternativa color
        self.folder_src = None

        # ------------ call super ----------- #
        super().__init__(name=name, alias=alias)

        # overwriters
        self.color = "orange"  # overwrite from super

        # descriptors:
        self.code = None
        self.x = None
        self.y = None
        self.datarange_min = None
        self.datarange_max = None

        # --- auto update info
        # todo refactor names here later on --- why?
        self.dtfreq = None
        self.dtres = None
        self.start = None
        self.end = None
        self.var_min = None
        self.var_max = None
        self.is_standard = False
        self.gapsize = 6
        self.epochs_stats = None
        self.epochs_n = None
        self.smallgaps_n = None
        self.eva = None

        # incoming data
        self.file_input = None  # todo rename to file_data??
        self.file_data_dtfield = self.dtfield
        self.file_data_varfield = self.varfield

        self._set_view_specs()
        # ... continues in downstream objects ... #

    # Core internal methods
    # -------------------------------------------------------------------
    def _set_fields(self):
        """
        Set catalog fields names. Expected to increment superior methods.
        """
        # ------------ call super ----------- #
        super()._set_fields()

        # TimeSeries fields
        # todo evaluate to make this fields snakecase
        self.code_field = "code"
        self.x_field = "x"
        self.y_field = "y"

        self.varfield_field = "VarField"
        self.varname_field = "VarName"
        self.varalias_field = "VarAlias"
        self.datarange_min_field = "VarRange_min"
        self.datarange_max_field = "VarRange_max"
        self.var_min_field = "Var_min"
        self.var_max_field = "Var_max"

        self.dtfield_field = "DtField"
        self.dtfreq_field = "DtFreq"
        self.dtres_field = "DtRes"
        self.start_field = "Start"
        self.end_field = "End"

        self.isstandard_field = "IsStandard"

        # Epochs
        self.gapsize_field = "GapSize"
        self.epochs_n_field = "Epochs_n"
        self.smallgaps_n_field = "SmallGaps_n"
        self.epochs_id_field = "Epoch_Id"

        # file fields
        self.file_data_dtfield_field = "File_Data_DtField"
        self.file_data_varfield_field = "File_Data_VarField"

        # ... continues in downstream objects ... #

    def _set_frequency(self):
        """
        Guess the datetime resolution of a time series based on the consistency of
        timestamp components (e.g., seconds, minutes).

        .. caution::

            This method infers the datetime frequency of the time series data
            based on the consistency of timestamp components.

        """
        # Handle void data
        if self.data is None:
            pass
        else:
            # Copy the data
            df = self.data.copy()

            # Extract components of the datetime
            df["year"] = df[self.dtfield].dt.year
            df["month"] = df[self.dtfield].dt.month
            df["day"] = df[self.dtfield].dt.day
            df["hour"] = df[self.dtfield].dt.hour
            df["minute"] = df[self.dtfield].dt.minute
            df["second"] = df[self.dtfield].dt.second

            # Check consistency within each unit of time
            if df["second"].nunique() > 1:
                self.dtfreq = "1min"
                self.dtres = "second"
            elif df["minute"].nunique() > 1:
                self.dtfreq = "20min"  # force to 20min
                self.dtres = "minute"
            elif df["hour"].nunique() > 1:
                self.dtfreq = "h"
                self.dtres = "hour"
            elif df["day"].nunique() > 1:
                self.dtfreq = "D"
                self.dtres = "day"
            elif df["month"].nunique() > 1:
                self.dtfreq = "MS"
                self.dtres = "month"
                # force gapsize to 1 when daily+ time scale
                self.gapsize = 1
            else:
                self.dtfreq = "YS"
                self.dtres = "year"
                # force gapsize to 1 when daily+ time scale
                self.gapsize = 1

        return None

    # Get methods
    # -------------------------------------------------------------------
    def get_metadata(self):
        """
        Get a dictionary with object metadata.
        Expected to increment superior methods.

        .. note::

            Metadata does **not** necessarily inclue all object attributes.

        :return: dictionary with all metadata
        :rtype: dict
        """
        # ------------ call super ----------- #
        dict_meta = super().get_metadata()

        # customize local metadata:
        dict_meta_local = {
            # TS info
            self.code_field: self.code,
            self.x_field: self.x,
            self.y_field: self.y,
            # Variable info
            self.varfield_field: self.varfield,
            self.varname_field: self.varname,
            self.varalias_field: self.varalias,
            self.datarange_min_field: self.datarange_min,
            self.datarange_max_field: self.datarange_max,
            self.var_min_field: self.var_min,
            self.var_max_field: self.var_max,
            # DateTime info
            self.dtfield_field: self.dtfield,
            self.dtfreq_field: self.dtfreq,
            self.dtres_field: self.dtres,
            self.start_field: self.start,
            self.end_field: self.end,
            # Standardization
            self.isstandard_field: self.is_standard,
            # Epochs info
            self.gapsize_field: self.gapsize,
            self.epochs_n_field: self.epochs_n,
            self.smallgaps_n_field: self.smallgaps_n,
            # file data info
            self.file_data_dtfield_field: self.file_data_dtfield,
            self.file_data_varfield_field: self.file_data_varfield,
        }

        # update
        dict_meta.update(dict_meta_local)
        # mode file_data to the end
        dict_meta.pop(self.field_file_data)
        dict_meta[self.field_file_data] = self.file_data
        return dict_meta

    # Core methods
    # -------------------------------------------------------------------
    def update(self):
        """
        Update internal attributes based on the current data.

        **Notes**

        - Calls the ``set_frequency`` method to update the datetime frequency attribute.
        - Updates the ``start`` attribute with the minimum datetime value in the data.
        - Updates the ``end`` attribute with the maximum datetime value in the data.
        - Updates the ``var_min`` attribute with the minimum value of the variable field in the data.
        - Updates the ``var_max`` attribute with the maximum value of the variable field in the data.
        - Updates the ``data_size`` attribute with the length of the data.

        """
        super().update()

        if self.data is not None:
            self._set_frequency()
            self.start = self.data[self.dtfield].min()
            self.end = self.data[self.dtfield].max()
            self.var_min = self.data[self.varfield].min()
            self.var_max = self.data[self.varfield].max()
            self.size = len(self.data)
            self._set_view_specs()
            self.view_specs["xmax_aux"] = 1.2 * self.freq_df["Frequency"].max()
            self.view_specs["ymax"] = self.data[self.varfield].max()
            self.view_specs["xmax"] = self.data[self.dtfield].max()
            self.view_specs["xmin"] = self.data[self.dtfield].min()

        # ... continues in downstream objects ... #
        return None

    def setter(self, dict_setter, load_data=True):
        """
        Set selected attributes based on an incoming dictionary.
        Expected to increment superior methods.

        :param dict_setter: incoming dictionary with attribute values
        :type dict_setter: dict
        :param load_data: option for loading data from incoming file. Default is True.
        :type load_data: bool

        """
        # ---------- call super --------- #
        super().setter(dict_setter=dict_setter, load_data=False)

        # ---------- set basic attributes --------- #

        # -------------- set data logic here -------------- #
        if load_data:
            # handle missing keys
            if self.dtfield_field not in list(dict_setter.keys()):
                input_dtfield = None  # assume default
            else:
                input_dtfield = dict_setter[self.dtfield_field]
            if self.varfield_field not in list(dict_setter.keys()):
                input_varfield = None  # assume default
            else:
                input_varfield = dict_setter[self.varfield_field]
            if "Sep" not in list(dict_setter.keys()):
                in_sep = ";"  # assume default
            # call load
            self.load_data(
                file_data=self.file_data,
                input_dtfield=input_dtfield,
                input_varfield=input_varfield,
                in_sep=in_sep,
            )

        # ... continues in downstream objects ... #

    # Data methods
    # -------------------------------------------------------------------
    def set_data(
        self, input_df, input_dtfield, input_varfield, filter_dates=None, dropnan=True
    ):
        """
        Set time series data from an inputs DataFrame.

        :param input_df: Input DataFrame containing time series data.
        :type input_df: :class:`pandas.DataFrame`
        :param input_dtfield: Name of the datetime field in the inputs DataFrame.
        :type input_dtfield: str
        :param input_varfield: Name of the variable field in the inputs DataFrame.
        :type input_varfield: str
        :param filter_dates: List of [Start, End] used for filtering date range.
        :type dropnan: list
        :param dropnan: If True, drop NaN values from the DataFrame. Default is True.
        :type dropnan: bool

        **Notes**

        - Assumes the inputs DataFrame has a datetime column in the format "YYYY-mm-DD HH:MM:SS".
        - Renames columns to standard format (datetime: ``self.dtfield``, variable: ``self.varfield``).
        - Converts the datetime column to standard format.

        """
        # Get a copy of the inputs DataFrame
        df = input_df.copy()

        # Rename columns to standard format
        df = df.rename(
            columns={input_dtfield: self.dtfield, input_varfield: self.varfield}
        )

        # Filter data only to columns
        df = df[[self.dtfield, self.varfield]].copy()

        # Drop NaN values if specified
        if dropnan:
            df = df.dropna()

        # Convert datetime column to standard format
        df[self.dtfield] = pd.to_datetime(df[self.dtfield], format="%Y-%m0-%d %H:%M:%S")

        if filter_dates is None:
            pass
        else:
            if filter_dates[0] is not None:
                df = df.query("{} >= '{}'".format(self.dtfield, filter_dates[0]))
            if filter_dates[1] is not None:
                df = df.query("{} < '{}'".format(self.dtfield, filter_dates[1]))

        # Set the data attribute
        self.data = df.copy()

        # update all
        self.update()

        return None

    def load_data(
        self,
        file_data,
        input_dtfield=None,
        input_varfield=None,
        in_sep=";",
        filter_dates=None,
    ):
        """
        Load data from file. Expected to overwrite superior methods.

        :param file_data: Absolute Path to the ``csv`` inputs file.
        :type file_data: str
        :param input_varfield: Name of the incoming varfield.
        :type input_varfield: str
        :param input_dtfield: Name of the incoming datetime field. Default is "datetime".
        :type input_dtfield: str
        :param sep: String separator. Default is ``;``.
        :type sep: str
        :param filter_dates: List of start and end date to filter. Default is None
        :type sep: list

        **Notes**

        - Assumes the inputs file is in ``csv`` format.
        - Expects a datetime column in the format ``YYYY-mm-DD HH:MM:SS``.


        """

        # -------------- overwrite relative path inputs -------------- #
        file_data = os.path.abspath(file_data)

        # -------------- implement loading logic -------------- #

        # assume defaults
        if input_dtfield is None:
            input_dtfield = self.file_data_dtfield
        else:
            self.file_data_dtfield = input_dtfield

        if input_varfield is None:
            input_varfield = self.file_data_varfield
        else:
            self.file_data_varfield = input_varfield

        # -------------- call loading function -------------- #
        # print(self.file_data_dtfield)
        df = pd.read_csv(
            file_data,
            sep=in_sep,
            dtype={input_varfield: float},
            usecols=[input_dtfield, input_varfield],
            parse_dates=[self.file_data_dtfield],
        )
        # print(df[self.file_data_dtfield].dtype)

        # -------------- post-loading logic -------------- #
        df = df.rename(
            columns={input_dtfield: self.dtfield, input_varfield: self.varfield}
        )

        if filter_dates is None:
            pass
        else:
            if filter_dates[0] is not None:
                df = df.query("{} >= '{}'".format(self.dtfield, filter_dates[0]))
            if filter_dates[1] is not None:
                df = df.query("{} < '{}'".format(self.dtfield, filter_dates[1]))

        # Set the data attribute
        self.data = df.copy()

        # ------------ update related attributes ------------ #
        self.file_data = file_data[:]
        self.folder_src = os.path.dirname(self.file_data)

        self.update()

        return None

    def cut_edges(self, inplace=False):
        """
        Cut off initial and final NaN records in a given time series.

        :param inplace: If True, the operation will be performed in-place, and the original data will be modified.
            If False, a new DataFrame with cut edges will be returned, and the original data will remain unchanged.
            Default is False.
        :type inplace: bool
        :return: If inplace is False, a new DataFrame with cut edges.
            If inplace is True, returns None, and the original data is modified in-place.
        :rtype: :class:`pandas.DataFrame``` or None

        **Notes**

        - This function removes leading and trailing rows with NaN values in the specified variable field.
        - The operation is performed on a copy of the original data, and the original data remains unchanged.

        """

        # get dataframe
        in_df = self.data.copy()
        def_len = len(in_df)

        # drop first nan lines
        drop_ids = list()

        # loop to collect indexes in the start of series
        for def_i in range(def_len):  # go forward
            aux = in_df[self.varfield].isnull().iloc[def_i]
            if aux:
                drop_ids.append(def_i)
            else:
                break

        # loop to collect indexes in the end of series
        for def_i in range(def_len - 1, -1, -1):  # go backward
            aux = in_df[self.varfield].isnull().iloc[def_i]
            if aux:
                drop_ids.append(def_i)
            else:
                break

        # loop to drop rows:
        for def_i in range(len(drop_ids)):
            in_df.drop(drop_ids[def_i], inplace=True)

        # output
        if inplace:
            self.data = in_df.copy()
            return None
        else:
            return in_df

    def standardize(self):
        """
        Standardize the data based on regular datetime steps and the time resolution.

        **Notes**

        - Creates a full date range with the expected frequency for the standardization period.
        - Groups the data by epochs (based on the frequency and datetime field), applies the specified aggregation function, and fills in missing values with left merges.
        - Updates internal attributes, including ``self.isstandard`` to indicate that the data has been standardized.

        .. warning::

            The ``standardize`` method modifies the internal data representation.
            Ensure to review the data after standardization.

        """

        def _insert_epochs(df):
            # handle epochs
            epochs = {
                "1min": ["%Y-%m0-%d %H:%M", ""],
                "20min": ["%Y-%m0-%d %H", " :20"],
                "h": ["%Y-%m0-%d %H", ""],
                "D": ["%Y-%m0-%d", ""],
                "MS": ["%Y-%m0", ""],
                "YS": ["%Y", ""],
            }
            df[self.dtfield + "_epoch"] = (
                df[self.dtfield].dt.strftime(epochs[self.dtfreq][0])
                + epochs[self.dtfreq][1]
            )
            return df

        # the ideia is to implement regular time increments and insert null rows

        # make a copy of the data
        df_data = self.data.copy()
        # insert epochs based on data frequency
        df_data = _insert_epochs(df=df_data)
        # aggregate by epoch
        df_data = (
            df_data.groupby(self.dtfield + "_epoch")[self.varfield]
            .agg([self.agg])
            .reset_index()
        )
        df_data.rename(columns={self.agg: self.varfield}, inplace=True)

        # Standardize incoming start and end
        start_std = self.start.normalize()  # the start of day
        end_std = self.end.normalize() + pd.Timedelta(days=1)  # the start of next day
        end_std = end_std.date()

        # Get a standard date range for all periods
        dt_index = pd.date_range(start=start_std, end=end_std, freq=self.dtfreq)

        # Set standarnd dataframe
        df_data_std = pd.DataFrame({self.dtfield: dt_index})
        df_data_std = _insert_epochs(df=df_data_std)

        on_st = self.dtfield + "_epoch"
        df_data_std = pd.merge(left=df_data_std, right=df_data, on=on_st, how="left")

        # Clear extra column
        self.data = df_data_std.drop(columns=on_st).copy()

        # [removed] Cut off edges
        # self.cut_edges(inplace=True)

        # Set extra attributes
        self.is_standard = True

        # Update all attributes
        self.update()

        return None

    def clear_outliers(self, inplace=False):
        """
        Clears outlier values from the specified variable field in the DataFrame.

        :param inplace: If True, the operation is performed in-place, modifying the DataFrame directly. If False, a new DataFrame with outliers removed is returned. Default value = False
        :type inplace: if `inplace` is True, otherwise the DataFrame with outliers cleared.
        :rtype: :class:`pandas.DataFrame` or None
        """

        # copy local data
        vct = self.data[self.varfield].values

        # Clear lower values
        if self.datarange_min is not None:
            vct = np.where(vct < self.datarange_min, np.nan, vct)

        # Clear upper values
        if self.datarange_max is not None:
            vct = np.where(vct > self.datarange_max, np.nan, vct)

        # return case
        if inplace:
            # overwrite local data
            self.data[self.varfield] = vct
            return None
        else:
            return df

    def get_epochs(self, inplace=False):
        """
        Get Epochs (periods) for continuous time series (0 = gap epoch).

        :param inplace: Option to set Epochs inplace. Default is False.
        :type inplace: bool
        :return: A DataFrame if inplace is False or None.
        :rtype: :class:`pandas.DataFrame``, None

        **Notes**

        This function labels continuous chunks of data as Epochs, with Epoch 0
        representing gaps in the time series.

        """
        df = self.data.copy()
        # Create a helper column to label continuous chunks of data
        df["CumSum"] = (
            df[self.varfield]
            .isna()
            .astype(int)
            .groupby(df[self.varfield].notna().cumsum())
            .cumsum()
        )

        # get skip hint
        # print(f"debug: {self.gapsize}")
        skip_v = np.zeros(len(df))
        for i in range(len(df) - 1):
            n_curr = df["CumSum"].values[i]
            n_next = df["CumSum"].values[i + 1]
            if n_next < n_curr:
                if n_curr >= self.gapsize:
                    n_start = i - n_curr
                    if i <= n_curr:
                        n_start = 0
                    skip_v[n_start + 1 : i + 1] = 1
        df["Skip"] = skip_v

        # Set Epoch Field
        df[self.epochs_id_field] = 0
        # counter epochs
        counter = 1
        for i in range(len(df) - 1):
            if df["Skip"].values[i] == 0:
                df[self.epochs_id_field].values[i] = counter
            else:
                if df["Skip"].values[i + 1] == 0:
                    counter = counter + 1
        if df["Skip"].values[i + 1] == 0:
            df[self.epochs_id_field].values[i] = counter

        df = df.drop(columns=["CumSum", "Skip"])

        if inplace:
            self.data = df.copy()
            return None
        else:
            return df

    def update_epochs_stats(self):
        """
        Update all epochs statistics.

        **Notes**

        - This function updates statistics for all epochs in the time series.
        - Ensures that the data is standardized by calling the ``standardize`` method if it's not already standardized.
        - Removes epoch 0 from the statistics since it typically represents non-standardized or invalid data.
        - Groups the data by ``Epoch_Id`` and calculates statistics such as count, start, and end timestamps for each epoch.
        - Generates random colors for each epoch using the ``get_random_colors`` function with a specified colormap (`cmap`` attribute).
        - Includes the time series name in the statistics for identification.
        - Organizes the statistics DataFrame to include relevant columns: ``Name``, ``Epoch_Id``, ``Count``, ``Start``, ``End``, and ``Color``.
        - Updates the attribute ``epochs_n`` with the number of epochs in the statistics.

        **Examples**

        todo [examples]

        """

        # Ensure data is standardized
        if not self.is_standard:
            self.standardize()

        # Get epochs
        df = self.get_epochs(inplace=False)

        # Remove epoch = 0
        df.drop(df[df[self.epochs_id_field] == 0].index, inplace=True)
        df[self.smallgaps_n_field] = 1 * df[self.varfield].isna().values

        # group by
        aggregation_dict = {
            self.epochs_n_field: (self.epochs_id_field, "count"),
            self.start_field: (self.dtfield, "min"),
            self.end_field: (self.dtfield, "max"),
            self.smallgaps_n_field: (self.smallgaps_n_field, "sum"),
        }

        self.epochs_stats = (
            df.groupby(self.epochs_id_field).agg(**aggregation_dict).reset_index()
        )

        # Get colors
        self.epochs_stats[self.field_color] = get_colors(
            size=len(self.epochs_stats), cmap=self.cmap
        )

        # Include name
        self.epochs_stats[self.field_name] = self.name

        # Organize fields
        self.epochs_stats = self.epochs_stats[
            [
                self.field_name,
                self.epochs_id_field,
                self.epochs_n_field,
                self.smallgaps_n_field,
                self.start_field,
                self.end_field,
                self.field_color,
            ]
        ]

        # Update attributes
        self.epochs_n = len(self.epochs_stats)
        self.smallgaps_n = self.epochs_stats[self.smallgaps_n_field].sum()

        return None

    def interpolate_gaps(self, method="linear", constant=0, inplace=False):
        """
        Fills gaps in a time series using various interpolation methods.

        :param method: Specifies the interpolation method. The default value is ``linear``.
        :type method: str
        :param constant: The constant value used when the ``constant`` method is selected. Default value = 0.
        :type constant: float
        :param inplace: If True, modifies the original DataFrame in-place. Default value = False.
        :type inplace: bool
        :return: A new ``pandas.DataFrame`` with interpolated values if inplace is False, otherwise None.
        :rtype: :class:`pandas.DataFrame` or None

        **Notes**

        This function handles time series data, standardizing it if necessary before performing interpolation.
        The process is applied to each unique epoch within the series.

         - ``linear``: linear interpolation
         - ``nearest``: uses the value of the closest data point.
         - ``zero``: fills gaps with zeros.
         - ``constant``: fills gaps with a constant value provided in method parameter
         - ``slinear``: first order spline interpolation
         - ``quadratic``: second order spline interpolation
         - ``cubic``: third order spline interpolation

        """
        from scipy.interpolate import interp1d

        # Ensure data is standardized
        if not self.is_standard:
            self.standardize()

        # Get epochs for interpolation
        df = self.get_epochs(inplace=False)
        epochs = df["Epoch_Id"].unique()
        list_dfs = list()

        for epoch in epochs:
            df_aux1 = df.query("Epoch_Id == {}".format(epoch)).copy()
            if epoch == 0:
                df_aux1["{}_interp".format(self.varfield)] = np.nan
            else:
                if method == "constant":
                    df_aux1["{}_interp".format(self.varfield)] = np.where(
                        df_aux1[self.varfield].isna(),
                        constant,
                        df_aux1[self.varfield].values,
                    )
                else:  # use scipy methods
                    # clear from nan values
                    df_aux2 = df_aux1.dropna().copy()
                    # Create an interpolation function
                    interpolation_func = interp1d(
                        df_aux2[self.dtfield].astype(np.int64).values,
                        df_aux2[self.varfield].values,
                        kind=method,
                        fill_value="extrapolate",
                    )
                    # Interpolate full values
                    df_aux1["{}_interp".format(self.varfield)] = interpolation_func(
                        df_aux1[self.dtfield].astype(np.int64)
                    )
            # Append
            list_dfs.append(df_aux1)
        df_new = pd.concat(list_dfs, ignore_index=True)
        df_new = df_new.sort_values(by=self.dtfield).reset_index(drop=True)

        if inplace:
            self.data[self.varfield] = df_new["{}_interp".format(self.varfield)].values
            self.update()
            return None
        else:
            return df_new

    def aggregate(self, freq, bad_max, agg_funcs=None):
        """
        Aggregate the time series data based on a specified frequency using various aggregation functions.

        :param freq: Pandas-like alias frequency at which to aggregate the time series data.
        :type freq: str
        :param bad_max: The maximum number of ``Bad`` records allowed in a time window for aggregation. Records with more ``Bad`` entries will be excluded from the aggregated result. Default is 7.
        :type bad_max: int
        :param agg_funcs: A dictionary specifying customized aggregation functions for each variable. Default is None,
            which uses standard aggregation functions (sum, mean, median, min, max, std, var, percentiles).
        :type agg_funcs: dict
        :return: A new `pandas.DataFrame` with aggregated values based on the specified frequency.
        :rtype: :class:`pandas.DataFrame`

        **Notes**

        Resamples the time series data to the specified frequency using Pandas-like alias strings.
        Aggregates the values using the specified aggregation functions.
        Counts the number of ``Bad`` records in each time window and excludes time windows with more ``Bad`` entries
        than the specified threshold.

        Common options include:
         - ``h`` for hourly frequency
         - ``D`` for daily frequency
         - ``W`` for weekly frequency
         - ``MS`` for monthly/start frequency
         - ``QS`` for quarterly/start frequency
         - ``YS`` for yearly/start frequency

        More options and details can be found in the Pandas documentation:
        https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#timeseries-offset-aliases.


        """

        if agg_funcs is None:
            # Create a dictionary of standard and custom aggregation functions
            agg_funcs = {
                "sum": "sum",
                "mean": "mean",
                "median": "median",
                "min": "min",
                "max": "max",
                "std": "std",
                "var": "var",
            }
            """
            # Add custom percentiles to the dictionary
            percentiles_to_compute = [1, 5, 10, 25, 50, 75, 90, 95, 99]
            for p in percentiles_to_compute:
                agg_funcs[f"p{p}"] = lambda x, p=p: np.percentile(x, p)
            """

        # set list of tuples
        agg_funcs_list = [
            ("{}_{}".format(self.varfield, f), agg_funcs[f]) for f in agg_funcs
        ]

        # get data
        df = self.data.copy()
        df["Bad"] = df[self.varfield].isna().astype(int)
        # Set the 'datetime' column as the index
        df.set_index(self.dtfield, inplace=True)

        # Redata the time series to a frequency using aggregation functions
        agg_df1 = df.resample(freq)[self.varfield].agg(agg_funcs_list)
        agg_df2 = df.resample(freq)["Bad"].agg([("Bad_count", "sum")])

        # Reset the index to get 'datetime' as a regular column
        agg_df1.reset_index(inplace=True)
        agg_df2.reset_index(inplace=True)

        # merge with bad dates
        agg_df = pd.merge(left=agg_df1, right=agg_df2, how="left", on=self.dtfield)

        # set new df
        agg_df_new = pd.DataFrame(
            {
                self.dtfield: pd.date_range(
                    start=agg_df[self.dtfield].values[0],
                    end=agg_df[self.dtfield].values[-1],
                    freq=freq,
                )
            }
        )
        # remove bad records
        agg_df.drop(agg_df[agg_df["Bad_count"] > bad_max].index, inplace=True)
        # remove bad column
        agg_df.drop(columns=["Bad_count"], inplace=True)

        # left join
        agg_df_new = pd.merge(
            left=agg_df_new, right=agg_df, on=self.dtfield, how="left"
        )

        return agg_df_new

    def upscale(self, freq, bad_max, inplace=True):
        """
        Upscale time series for larger time steps. This method uses the `agg` attribute.
        See the `aggregate` method.

        :param freq: Pandas-like alias frequency at which to aggregate the time series data.
            Common options include:
            - ``h`` for hourly frequency
            - ``D`` for daily frequency
            - ``W`` for weekly frequency
            - ``MS`` for monthly/start frequency
            - ``QS`` for quarterly/start frequency
            - ``YS`` for yearly/start frequency
            More options and details can be found in the Pandas documentation:
            https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#timeseries-offset-aliases.
        :type freq: str
        :param bad_max: The maximum number of ``Bad`` records allowed in a time window for aggregation. Records with more ``Bad`` entries
            will be excluded from the aggregated result.
        :type bad_max: int
        :param inplace: option for overwrite data, default True
        :type inplace: bool

        """
        df_upscale = self.aggregate(
            freq=freq, bad_max=bad_max, agg_funcs={self.agg: self.agg}
        )
        df_upscale = df_upscale.rename(
            columns={"{}_{}".format(self.varfield, self.agg): self.varfield}
        )

        # return case
        if inplace:
            # overwrite local data
            self.data = df_upscale
            #
            self._set_frequency()

            return None
        else:
            return df_upscale

    # todo develop -- improve methods of downscaling
    def downscale(self, freq):
        """
        Donwscale time series for smaller time steps using linear inteporlation.

        :param freq: new time step frequency
        :type freq: str
        :return: Dataframe of downscaled data
        :rtype: :class:`pandas.DataFrame`
        """
        # update
        self.update()
        # get new index
        dt_index = pd.date_range(start=self.start, end=self.end, freq=freq)
        # set new dataframe
        df_downscale = pd.DataFrame({self.dtfield: dt_index})
        df_downscale = pd.merge(
            left=df_downscale, right=self.data, on=self.dtfield, how="left"
        )

        # handle flow variable
        if self.agg == "sum":

            # compute downscaling factor assuming at least 2 data points
            tdelta_source = (
                self.data[self.dtfield].values[1] - self.data[self.dtfield].values[0]
            )
            tdelta_new = (
                df_downscale[self.dtfield].values[1]
                - df_downscale[self.dtfield].values[0]
            )
            factor_downscale = tdelta_new / tdelta_source
            # apply factor
            df_downscale[self.varfield] = df_downscale[self.varfield] * factor_downscale

        # interpolate voids using linear method
        df_downscale[self.varfield] = df_downscale[self.varfield].interpolate(
            method="linear"
        )

        if self.agg == "sum":
            # apply factor for numerical loss/gain
            up_sum = self.data[self.varfield].sum()
            down_sum = df_downscale[self.varfield].sum()
            diff_factor = down_sum / up_sum
            df_downscale[self.varfield] = df_downscale[self.varfield] / diff_factor

        return df_downscale

    def assess_extreme_values(self, eva_freq="YS", eva_agg="max"):
        """
        Run Extreme Values Analysis (EVA) over the Time Series and set the ``eva`` attribute

        :param eva_freq: standard pandas frequency alias for upscaling data
        :type eva_freq: str
        :param eva_agg: standard pandas aggregation alias for upscaling (expected: ``max`` or ``min``)
        :type eva_agg: str

        """

        # set agg to max
        agg_old = self.agg[:]
        self.agg = eva_agg

        # upscale time series
        df_eva = self.upscale(freq=eva_freq, bad_max=self.gapsize, inplace=False)
        df_eva = df_eva.dropna()

        # reset agg
        self.agg = agg_old

        # fix dates to match actual maxima by making YEAR-Value tag
        df_eva["tag1"] = (
            df_eva[self.dtfield].dt.year.astype(str)
            + " - "
            + df_eva[self.varfield].astype(str)
        )
        df_d = self.data.copy()
        df_d["tag2"] = (
            df_d[self.dtfield].dt.year.astype(str)
            + " - "
            + df_d[self.varfield].astype(str)
        )
        # join by tag
        df_eva = pd.merge(left=df_eva, left_on="tag1", right=df_d, right_on="tag2")
        df_eva = df_eva.drop_duplicates(subset="tag1").reset_index(drop=True)

        # remake max df
        df_eva = pd.DataFrame(
            {
                self.dtfield: df_eva[f"{self.dtfield}_y"].values,
                self.varfield: df_eva[f"{self.varfield}_y"].values,
            }
        )

        # Setup Univar Object for Maxima Assessment
        uv_eva = Univar(name=f"EVA {self.varname}", alias=f"EVA_{self.varalias}")
        uv_eva.varfield = self.varfield
        uv_eva.varname = self.varname
        uv_eva.varalias = self.varalias
        uv_eva.data = df_eva.copy()
        uv_eva.update()

        # run Gumbel assessment
        self.eva = uv_eva.assess_gumbel_cdf()

        return None

    # View internal methods
    # -------------------------------------------------------------------

    def _build_axes(self, fig, gs, specs):
        # todo [docstring]
        # ------------ setup axes ------------
        if specs["mode"] == "full":
            fig.add_subplot(gs[2:10, 2:21])
            fig.add_subplot(gs[2:10, 23:28])
            fig.add_subplot(gs[2:10, 29:])
        elif specs["mode"] == "simple":
            print("hey")
            fig.add_subplot(gs[2:10, 2:31])
        else:
            fig.add_subplot(gs[2:10, 2:21])
            fig.add_subplot(gs[2:10, 23:28])
            fig.add_subplot(gs[2:10, 29:])

        return fig

    def _get_fig_specs(self):
        # todo [docstring]
        # handle specs
        specs = self.view_specs.copy()

        # handle mode
        mode = specs["mode"]
        if mode == "full":
            specs_aux = {
                "ncols": 34,
                "nrows": 16,
                "width": viewer.FIG_SIZES["L"]["w"],
                "height": viewer.FIG_SIZES["L"]["h"],
            }
        else:
            specs_aux = {
                "ncols": 34,
                "nrows": 12,
                "width": viewer.FIG_SIZES["L2"]["w"],
                "height": viewer.FIG_SIZES["L2"]["h"],
            }
        # update sizes
        specs.update(specs_aux)

        # update gridspecs
        specs.update(viewer.GRID_SPECS)

        return specs

    def _plot(self, fig, gs, specs):
        # handle mode
        if specs["mode"] == "simple":
            fig = super()._plot(fig=fig, gs=gs, specs=specs)
        else:
            fig = super()._plot(fig=fig, gs=gs, specs=specs)

        return fig

    def _set_view_specs(self):
        """
        Set view specifications.

        """

        # Call the parent method to initialize `view_specs`
        super()._set_view_specs()

        # Update or add new specifications specific to the child class
        self.view_specs.update(
            {
                "folder": self.folder_src,
                "title": "Time Series | {} | {} ({})".format(
                    self.name, self.varname, self.varalias
                ),
                "xvar": self.dtfield,
                "yvar": self.varfield,
                "xlabel": self.dtfield,
                "color": self.rawcolor,
                "color_aux": self.rawcolor,
                "color_fill": self.rawcolor,
                "color_eva": "blue",
                "legend_eva": "Annual Maxima",
                "alpha": 1,
                "alpha_aux": 1,
                "alpha_fill": 1,
                "fill": False,
                "xmin": None,
                "xmax": None,
                "xmax_aux": 20,
                "ymin": 0,
                "ymax": None,
                "linestyle": "solid",
                "marker": None,
                "marker_eva": ".",
                "n_bins": 100,
                "subtitle_a": None,
                "n_dates": 5,
                "include_eva": False,
                "x_stats": 0.73,
                "x_stats_sep": 0.12,
                "y_stats": 0.28,
            }
        )

        return None

    # View methods
    # -------------------------------------------------------------------

    def view(self, show=True, return_fig=False):
        """
        View the TimeSeries data.

        .. note::

            Use values in the ``view_specs()`` attribute for plotting

        :param show: option for showing instead of saving.
        :type show: bool
        :param return_fig: option for returning the figure object itself.
        :type return_fig: bool

        """
        specs = self.view_specs.copy()

        # handle eva specs
        if specs["include_eva"]:
            self.view_specs["hist_density"] = True
            self.view_specs["xlabel_b"] = "p(X)"

        # handle mode specs
        if specs["mode"] == "simple":
            self.view_specs["ax_histh"] = False
            self.view_specs["ax_cdf"] = False
        else:
            self.view_specs["ax_histh"] = 1
            self.view_specs["ax_cdf"] = 2

        # call base method and return the fig
        fig = super().view(show=False, return_fig=True)

        # -------------- PLOT EXTRA --------------

        # plotting series
        # ------------------------------------------------------------
        # todo develop DRY -- develop plotting static methods
        # --- call _plot()

        # series plot
        axes = fig.get_axes()
        print(axes)
        print(specs["ax_data"])

        ax = axes[specs["ax_data"]]
        ax.cla()
        # plot series
        ax.plot(
            self.data[specs["xvar"]],
            self.data[specs["yvar"]],
            linestyle=specs["linestyle"],
            marker=specs["marker"],
            color=specs["color"],
            alpha=specs["alpha"],
        )
        # fill option
        if specs["fill"]:
            lower = (self.data[specs["yvar"]].values * 0) + specs["ymin"]
            # Fill below the time series
            ax.fill_between(
                x=self.data[specs["xvar"]],
                y1=lower,
                y2=self.data[specs["yvar"]],
                color=specs["color_fill"],
                alpha=specs["alpha_fill"],
            )
        # handle dates
        if specs["n_dates"] is not None:
            n_dates = specs["n_dates"]
            dt_col = self.dtfield
            dates = self.data[dt_col]

            # Handle n_dates dynamically
            if n_dates <= 1:
                # Just the first one
                tick_indices = [0]
            elif n_dates == 2:
                # First and last
                tick_indices = [0, len(dates) - 1]
            else:
                # Evenly spaced positions across the dataset
                tick_indices = np.linspace(0, len(dates) - 1, n_dates, dtype=int)

            # Get the corresponding dates
            ticks = dates.iloc[tick_indices]

            # Apply to plot
            ax.set_xticks(ticks)
            ax.set_xticklabels([d.strftime("%Y-%m-%d") for d in ticks])
        # handle subtitle
        if specs["subtitle_a"] is not None:
            ax.set_title(specs["subtitle_a"])
        # handle range
        if specs["range"] is not None:
            ax.set_ylim(specs["range"])

        # handle range x
        if specs["range_x"] is not None:
            ax.set_ylim(specs["range_x"])

        # basic decorations
        ax.set_xlabel(specs["xlabel"])
        ax.set_ylabel(specs["ylabel"])

        # handle eva
        if specs["include_eva"]:
            if self.eva is not None:
                # ---- plot EVA series
                ax.plot(
                    self.eva["Data"][self.dtfield],
                    self.eva["Data"][self.varfield],
                    marker=".",
                    linestyle="none",
                    color=specs["color_eva"],
                    label=specs["legend_eva"],
                )
                ax.legend(frameon=True, fontsize=8, facecolor="white", loc="upper left")

                # ---- plot EVA histogram
                ax2 = axes[1]
                data = self.eva["Data"][self.varfield].values
                ax2.hist(
                    data,
                    bins=Univar.nbins_fd(data=data),
                    color=specs["color_eva"],
                    alpha=0.5,
                    orientation="horizontal",
                    density=True,
                    label=specs["legend_eva"],
                )
                # ax2.legend()

                # ---- plot EVA model
                ax3 = axes[2]
                ax3.cla()
                ax3.scatter(
                    x=self.eva["Data"]["T(X)_Weibull"],
                    y=self.eva["Data"][self.varfield],
                    marker=".",
                    color="black",  # specs["color_eva"],
                    zorder=3,
                    label="Empirical",
                )
                ax3.plot(
                    self.eva["Data_T(X)"]["T(X)_Gumbel"],
                    self.eva["Data_T(X)"][self.varfield],
                    color="blue",
                    linestyle="solid",
                    zorder=2,
                    label="Gumbel",
                )
                ax3.fill_between(
                    x=self.eva["Data_T(X)"]["T(X)_Gumbel"],
                    y1=self.eva["Data_T(X)"][f"{self.varfield}_P05"],
                    y2=self.eva["Data_T(X)"][f"{self.varfield}_P95"],
                    color="lightblue",
                    alpha=0.7,
                    zorder=1,
                    label="90%CR",
                )
                ax3.legend(
                    frameon=True, fontsize=8, facecolor="white", loc="lower right"
                )
                ax3.set_xlim(1, 1000)
                ax3.set_xscale("log")
                ax3.set_xlabel("T(X)")

        # -------------- SHIP --------------
        # create path
        file_path = "{}/{}.{}".format(
            specs["folder"], specs["filename"], specs["fig_format"]
        )
        if return_fig:
            return fig
        else:
            viewer.ship_fig(fig=fig, show=show, file_output=file_path, dpi=specs["dpi"])

    def view_epochs(self, show=True):
        """
        Get a basic visualization.
        Expected to overwrite superior methods.

        :param show: option for showing instead of saving.
        :type show: bool

        **Notes**

        - Uses values in the ``view_specs()`` attribute for plotting

        """
        # get specs
        specs = self.view_specs.copy()
        # --------------------- pre-processing --------------------- #
        # preprocessing
        if self.epochs_stats is None:
            self.update_epochs_stats()

        # --------------------- figure setup --------------------- #
        fig = plt.figure(figsize=(specs["width"], specs["height"]))  # Width, Height

        # handle min max
        if specs["xmin"] is None:
            specs["xmin"] = self.data[specs["xvar"]].min()
        if specs["ymin"] is None:
            specs["ymin"] = self.data[specs["yvar"]].min()
        if specs["xmax"] is None:
            specs["xmax"] = self.data[specs["xvar"]].max()
        if specs["ymax"] is None:
            specs["ymax"] = self.data[specs["yvar"]].max()

        # --------------------- plotting --------------------- #
        gaps_c = "tab:red"
        gaps_a = 0.6
        # plot loop
        for i in range(len(self.epochs_stats)):
            start = self.epochs_stats["Start"].values[i]
            end = self.epochs_stats["End"].values[i]
            df_aux = self.data.query(
                "{} >= '{}' and {} < '{}'".format(
                    self.dtfield, start, self.dtfield, end
                )
            )
            epoch_c = self.epochs_stats["Color"].values[i]
            epoch_id = self.epochs_stats["Epoch_Id"].values[i]
            plt.plot(
                df_aux[self.dtfield],
                df_aux[self.varfield],
                linestyle=specs["linestyle"],
                color=epoch_c,
                label=f"Epoch_{epoch_id}",
            )
            # Fill the space where there are missing values
            plt.fill_between(
                df_aux[self.dtfield],
                y1=0,
                y2=1.2 * specs["ymax"],
                where=df_aux[self.varfield].isna(),
                color=gaps_c,
                alpha=gaps_a,
            )
        # Create a dummy plot for missing data symbol
        plt.plot([], [], color=gaps_c, alpha=gaps_a, label="Gaps")
        if self.epochs_n <= 12:
            plt.legend(frameon=True, ncol=3)

        # --------------------- post-plotting --------------------- #
        # set basic plotting stuff
        plt.title(specs["title"])
        plt.ylabel(specs["ylabel"])
        plt.xlabel(specs["xlabel"])

        plt.xlim(specs["xmin"], specs["xmax"])
        plt.ylim(specs["ymin"], 1.2 * specs["ymax"])

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

    @staticmethod
    def add_hour(df, hour=12, dt_field="datetime"):
        # todo docstring
        df[dt_field] = df[dt_field].dt.normalize() + pd.to_timedelta(hour, unit="h")
        return df


# Chronological classes - collections
# -----------------------------------------------------------------------


class TimeSeriesCollection(Collection):
    """
    A collection of time series objects with associated metadata.

    The ``TimeSeriesCollection`` or simply ``TSC`` class extends the ``Collection`` class and
    is designed to handle time series data. It can be miscellaneous datasets.

    .. note::

        See ``TimeSeriesCluster`` for managing time series of the same variable


    """

    # Dunder methods
    # -------------------------------------------------------------------
    def __init__(self, name="myTSCollection", base_object=None):
        # If base_object is not provided, create a default TimeSeries object
        if base_object is None:
            base_object = TimeSeries

        # Call the constructor of the parent class (TimeSeries)
        super().__init__(base_object=base_object, name=name)

        # Set up date fields and special attributes in the catalog
        self.catalog["Start"] = pd.to_datetime(
            self.catalog["Start"], format="%Y-%m0-%d %H:%M:%S"
        )
        self.catalog["End"] = pd.to_datetime(
            self.catalog["End"], format="%Y-%m0-%d %H:%M:%S"
        )

        # Set auto attributes
        self.start = None
        self.end = None
        self.var_min = None
        self.var_max = None
        self.isstandard = False
        self.datarange_min = None
        self.datarange_max = None
        self.folder_src = None

        # Set specific attributes
        self.name_object = "Time Series Collection"
        self.dtfield = "datetime"
        self.overfield = "Overlapping"

        # load view specs
        self._set_view_specs()

    def __str__(self):
        return self.catalog.to_string(index=False)

    # Core internal methods
    # -------------------------------------------------------------------

    # Core methods
    # -------------------------------------------------------------------
    def update(self, details=False):
        """
        Update the time series collection.

        :param details: bool, optional
            If True, update additional details.
            Default is False.
        :type details: bool

        **Examples**


        """
        # Call the update method of the parent class (Collection)
        super().update(details=details)
        # Update start, end, min, and max attributes based on catalog information
        self.start = self.catalog["Start"].min()
        self.end = self.catalog["End"].max()
        self.var_min = self.catalog["Var_min"].min()
        self.var_max = self.catalog["Var_max"].max()

    # Data methods
    # -------------------------------------------------------------------
    def load_data(self, table_file, filter_dates=None):
        """
        Load data from table file (information table) into the time series collection.

        :param table_file: Path to file. Expected to be a ``csv`` table.
        :type table_file: str

        """
        input_df = pd.read_csv(table_file, sep=";")
        input_dir = os.path.dirname(table_file)
        self.set_data(df_info=input_df, src_dir=input_dir, filter_dates=filter_dates)
        return None

    def set_data(self, df_info, src_dir=None, filter_dates=None):
        """
        Set data for the time series collection from a info class:`pandas.DataFrame`.

        :param df_info: This DataFrame is expected to have matching fields to the metadata keys.
        :type df_info: class:`pandas.DataFrame`
        :param src_dir: Path for inputs directory in the case for only file names in ``File`` column.
        :type src_dir: str
        :param filter_dates: List of Start and End dates for filter data
        :type filter_dates: str

        **Notes**

        - The ``set_data`` method populates the time series collection with data based on the provided DataFrame.
        - It creates time series objects, loads data, and performs additional processing steps.
        - Adjust ``skip_process`` according to your data processing needs.

        """

        # handle mutable fields
        str_varname = self.baseobject().varname
        list_mutables = ["Units", "DtField", "VarField", "File"]
        dict_m_fields = {}
        for m in list_mutables:
            if m in df_info.columns:
                # assume <Varname>_ prefix:
                dict_m_fields[m] = m
            else:
                dict_m_fields[m] = "{}_{}".format(str_varname, m)

        for i in range(len(df_info)):
            # create object
            ts = self.baseobject(name=df_info["Name"].values[i])
            ts.alias = df_info["Alias"].values[i]
            ts.units = df_info[dict_m_fields["Units"]].values[i]
            # handle inputs file
            input_file = df_info[dict_m_fields["File"]].values[i]
            # if is a path:
            if os.path.exists(input_file):
                pass
            else:
                # assume file name only and concat
                if src_dir is not None:
                    input_file = "{}/{}".format(src_dir, input_file)
            # load data
            ts.load_data(
                file_data=input_file,
                input_varfield=df_info[dict_m_fields["VarField"]].values[i],
                input_dtfield=df_info[dict_m_fields["DtField"]].values[i],
                filter_dates=filter_dates,
            )
            # extra attrs
            ts.x = df_info["X"].values[i]
            ts.y = df_info["Y"].values[i]
            ts.code = df_info["Code"].values[i]
            ts.source = df_info["Source"].values[i]
            ts.description = df_info["Description"].values[i]
            ts.color = df_info["Color"].values[i]
            # append
            self.append(new_object=ts)
        self.update(details=True)
        return None

    def clear_outliers(self):
        """
        Clear outliers in the collection based on the ``datarange_min`` and ``datarange_max`` attributes.
        """
        for name in self.collection:
            self.collection[name].datarange_min = self.datarange_min
            self.collection[name].datarange_max = self.datarange_max
            self.collection[name].clear_outliers(inplace=True)
        return None

    def merge_data(self):
        """
        Merge data from multiple sources into a single DataFrame.

        :return: A merged DataFrame with datetime and variable fields from different sources.
        :rtype: pandas.DataFrame

        **Notes**

        - Updates the catalog details.
        - Merges data from different sources based on the specified datetime field and variable field.
        - The merged DataFrame includes a date range covering the entire period.

        """
        # Ensure catalog is updated with details
        self.update(details=True)

        # Get start, end, and frequency from the catalog
        start = self.start
        end = self.end

        # todo handle this issue on the first freq
        # consider the first freq
        freq = self.catalog["DtFreq"].values[0]

        # Create a date range for the entire period
        dt_index = pd.date_range(start=start, end=end, freq=freq)
        df = pd.DataFrame({self.dtfield: dt_index})

        # Merging loop for each catalog entry
        for i in range(len(self.catalog)):
            # Get attributes from the catalog
            name = self.catalog[self.field_name].values[i]
            alias = self.catalog[self.field_alias].values[i]
            varfield = self.catalog["VarField"].values[i]
            dtfield = self.catalog["DtField"].values[i]

            # Handle datetime field and set up right DataFrame
            b_drop = False
            if self.dtfield == dtfield:
                suffs = ("", "")
                dt_right_after = dtfield
            else:
                suffs = ("", "_right")
                b_drop = True

            df_right = self.collection[name].data[[dtfield, varfield]].copy()
            df_right = df_right.rename(
                columns={varfield: "{}_{}".format(varfield, alias)}
            )

            # Left join the DataFrames
            df = pd.merge(
                how="left",
                left=df,
                left_on=self.dtfield,
                right=df_right,
                right_on=dtfield,
                suffixes=suffs,
            )

            # Clear the right datetime column if needed
            if b_drop:
                df = df.drop(columns=[dt_right_after])
        return df

    def standardize(self):
        """
        This method standardizes all time series objects in the collection.

        **Notes**

        - The method iterates through each time series in the collection and standardizes it.
        - After standardizing individual time series, the data is merged.
        - The merged data is then reset for each individual time series in the collection.
        - Epoch statistics are updated for each time series after the reset.
        - Finally, the collection catalog is updated with details.

        """
        # Standardize and fill gaps across all series [overwrite]
        for name in self.collection:
            self.collection[name].standardize()
            self.collection[name].interpolate_gaps(inplace=True)

        # Merge data
        df = self.merge_data()

        # helper dict -- alias is the key
        dict_names = dict()
        for i in range(len(self.catalog)):
            a = self.catalog["Alias"].values[i]
            dict_names[a] = self.catalog["Name"].values[i]

        # Reset data for each time series
        for c in df.columns[1:]:
            # filter merged dataframe
            df_aux = df[[self.dtfield, c]].copy()

            alias = c.split("_")[1]
            name = dict_names[alias]
            # set data
            self.collection[name].set_data(
                input_df=df_aux,
                input_dtfield=self.dtfield,
                input_varfield=c,
                dropnan=False,
            )

        # Update epochs statistics for each time series
        for name in self.collection:
            self.collection[name].update_epochs_stats()

        # Update the collection catalog with details
        self.update(details=True)

        # Set standard flag
        self.isstandard = True

        return None

    def merge_local_epochs(self):
        """
        Merge local epochs statistics from individual time series within the collection.

        :return: Merged :class:`pandas.DataFrame``` containing epochs statistics.
        :rtype: :class:`pandas.DataFrame`

        **Notes**

        - This method creates an empty list to store individual epochs statistics dataframes.
        - It iterates through each time series in the collection.
        - For each time series, it updates the local epochs statistics using the :meth:``update_epochs_stats`` method.
        - The local epochs statistics dataframes are then appended to the list.
        - Finally, the list of dataframes is concatenated into a single dataframe.

        """
        # Create an empty list to store individual epochs statistics dataframes
        lst_df = list()

        # Iterate through each time series in the collection
        for name in self.collection:
            # Update epochs statistics for the current time series
            self.collection[name].update_epochs_stats()

            # Append the epochs statistics dataframe to the list
            lst_df.append(self.collection[name].epochs_stats.copy())

        # Concatenate the list of dataframes into a single dataframe
        df = pd.concat(lst_df).reset_index(drop=True)

        return df

    def get_epochs(self):
        """
        Calculate epochs for the time series data.

        :return: DataFrame with epochs information.
        :rtype: :class:`pandas.DataFrame`

        **Notes**

        - This method merges the time series data to create a working DataFrame.
        - It creates a copy of the DataFrame for NaN-value calculation.
        - Converts non-NaN values to 1 and NaN values to 0.
        - Calculates the sum of non-NaN values for each row and updates the DataFrame with the result.
        - Extracts relevant columns for epoch calculation.
        - Sets 0 values in the specified ``overfield`` column to NaN.
        - Creates a new :class:`TimeSeries`` instance for epoch calculation using the ``overfield`` values.
        - Calculates epochs using the :meth:``get_epochs`` method of the new :class:`TimeSeries`` instance.
        - Updates the original DataFrame with the calculated epochs.

        """
        # Merge data to create a working DataFrame
        df = self.merge_data()

        # Create a copy for nan-value calculation
        df_nan = df.copy()

        # Convert non-NaN values to 1, and NaN values to 0
        for v in df_nan.columns[1:]:
            df_nan[v] = df_nan[v].notna().astype(int)

        # Calculate the sum of non-NaN values for each row
        df_nan = df_nan.drop(columns=[self.dtfield])
        df[self.overfield] = df_nan.sum(axis=1)
        df[self.overfield] = df[self.overfield] / len(df_nan.columns)

        # Extract relevant columns for epoch calculation
        df_aux = df[[self.dtfield, self.overfield]].copy()

        # Set 0 values in the overfield column to NaN
        df_aux[self.overfield].replace(0, np.nan, inplace=True)

        # Create a new TimeSeries instance for epoch calculation
        ts_aux = TimeSeries()
        ts_aux.set_data(
            input_df=df_aux,
            input_varfield=self.overfield,
            input_dtfield=self.dtfield,
            dropnan=False,
        )

        # Calculate epochs and update the original DataFrame
        ts_aux.get_epochs(inplace=True)
        df["Epoch_Id"] = ts_aux.data["Epoch_Id"].values

        return df

    # View internal methods
    # -------------------------------------------------------------------
    def _set_view_specs(self):
        self.view_specs = {
            "title": "{} | {}".format(self.name_object, self.name),
            "width": 8,
            "width_spacing": 1.5,
            "left": 0.1,
            "height": 5,
            "xlabel": "Date",
            "ylabel": "%",
            "gantt": "Gantt chart (epochs)",
            "prev": "Series prevalence",
            "over": "Overlapping data",
            "vmin": 0,
            "vmax": None,
            "ymin": 0,
            "ymax": None,
            "xmin": None,
            "xmax": None,
        }
        return None

    # todo develop refactor to new view scheme (DRY)
    def view(
        self,
        show=True,
        folder="./output",
        filename=None,
        dpi=300,
        fig_format="jpg",
        suff="",
        usealias=False,
    ):
        """
        Visualize the time series collection.

        :param show: bool, optional
            If True, the plot will be displayed interactively.
            If False, the plot will be saved to a file.
            Default is True.
        :type show: bool

        :param folder: str, optional
            The folder where the plot file will be saved. Used only if show is False.
            Default is "./output".
        :type folder: str

        :param filename: str, optional
            The base name of the plot file. Used only if show is False. If None, a default filename is generated.
            Default is None.
        :type filename: str or None

        :param dpi: int, optional
            The dots per inch (resolution) of the plot file. Used only if show is False.
            Default is 300.
        :type dpi: int

        :param fig_format: str, optional
            The format of the plot file. Used only if show is False.
            Default is "jpg".
        :type fig_format: str

        :param usealias: bool, optional
            Option for using the Alias instead of Name in the plot.
            Default is False.
        :type usealias: bool


            If show is True, the plot is displayed interactively.
            If show is False, the plot is saved to a file.


        **Notes**

        This function generates a scatter plot with colored epochs based on the epochs' start and end times.
        The plot includes data points within each epoch, and each epoch is labeled with its corresponding ID.

        **Examples**

        """
        if usealias:
            _names = self.catalog["Name"].values
            _alias = self.catalog["Alias"].values
            dict_alias = dict()
            for i in range(len(self.catalog)):
                dict_alias[_names[i]] = _alias[i]

        # pre-processing
        local_epochs_df = self.merge_local_epochs()
        # Aggregate sum based on the 'Name' field
        agg_df = local_epochs_df.groupby("Name")["Epochs_n"].sum().reset_index()
        agg_df = agg_df.sort_values(by="Epochs_n", ascending=True).reset_index(
            drop=True
        )
        names = agg_df["Name"].values
        if usealias:
            alias = [dict_alias[name] for name in names]
        preval = 100 * agg_df["Epochs_n"].values / agg_df["Epochs_n"].sum()
        heights = np.linspace(0, 1, len(names) + 1)
        heights = heights[: len(names)] + ((heights[1] - heights[0]) / 2)

        # get epochs
        epochs_df = self.get_epochs()

        # Assuming date_values is a list of datetime objects
        date_values = epochs_df[self.dtfield].values
        # Calculate the number of ticks you want (e.g., 5)
        num_ticks = 5
        # Calculate the step size to evenly space the ticks
        step_size = len(date_values) // (num_ticks - 1)
        # Generate indices for the ticks
        tick_indices = np.arange(0, len(date_values), step_size)
        # Select the corresponding dates for the ticks
        ticks = [date_values[i] for i in tick_indices]

        # plot
        specs = self.view_specs.copy()

        # Deploy figure
        fig = plt.figure(figsize=(specs["width"], specs["height"]))  # Width, Height
        gs = mpl.gridspec.GridSpec(
            2,
            6,
            wspace=specs["width_spacing"],
            hspace=0.5,
            left=specs["left"],
            bottom=0.1,
            top=0.85,
            right=0.95,
        )
        fig.suptitle(specs["title"])

        # Gantt chart
        plt.subplot(gs[:1, :4])
        plt.title("a. {}".format(specs["gantt"]), loc="left")
        for i in range(len(names)):
            name = names[i]
            df_aux = local_epochs_df.query(f"Name == '{name}'")
            for j in range(len(df_aux)):
                x_time = [df_aux["Start"].values[j], df_aux["End"].values[j]]
                y_height = [heights[i], heights[i]]
                plt.plot(
                    x_time,
                    y_height,
                    color=df_aux["Color"].values[j],
                    linewidth=6,
                    solid_capstyle="butt",
                )
        plt.ylim(0, 1)
        plt.xlim((self.start, self.end))
        labels = names
        if usealias:
            labels = alias
        plt.yticks(heights, labels)
        plt.xlabel(specs["xlabel"])
        plt.xticks(ticks)
        plt.grid(axis="y")

        # overlapping chart
        plt.subplot(gs[1:, :4])
        plt.title("code. {}".format(specs["over"]), loc="left")
        plt.plot(
            epochs_df[self.dtfield], 100 * epochs_df[self.overfield], color="tab:blue"
        )
        plt.fill_between(
            epochs_df[self.dtfield],
            100 * epochs_df[self.overfield],
            color="tab:blue",
            alpha=0.4,
        )
        plt.ylim(-5, 105)
        plt.xlim((self.start, self.end))
        plt.xlabel(specs["xlabel"])
        plt.xticks(ticks)
        plt.ylabel("%")

        # Prevalence chart
        plt.subplot(gs[:1, 4:])
        plt.title("b. {}".format(specs["prev"]), loc="left")
        plt.barh(
            labels,
            preval,
            color="tab:gray",
        )
        # Add data values as text labels on the bars
        for index, value in enumerate(preval):
            plt.text(
                value,
                index,
                " {:.1f}%".format(value),
                ha="left",
                va="center",
                fontsize=10,
            )
        plt.xlim(0, 100)
        plt.grid(axis="x")
        plt.xlabel("%")

        # show or save
        if show:
            plt.show()
        else:
            if filename is None:
                filename = "{}{}".format(self.name, suff)
            plt.savefig("{}/{}.{}".format(folder, filename, fig_format), dpi=dpi)
            plt.close(fig)
        return None

    # todo develop refactor to new view scheme
    def export_views(
        self, folder, dpi=300, fig_format="jpg", suff="", skip_main=False, raw=False
    ):
        """
        Export views of time series data and individual time series within the collection.

        :param folder: The folder path where the views will be exported.
        :type folder: str
        :param dpi: Dots per inch (resolution) for the exported images, default is 300.
        :type dpi: int
        :param fig_format: Format for the exported figures, default is "jpg".
        :type fig_format: str
        :param suff: Suffix to be appended to the exported file names, default is an empty string.
        :type suff: str
        :param skip_main: Option for skipping the main plot (pannel)
        :type skip_main: bool
        :param raw: Option for considering a raw data series. No epochs analysis. Default is False.
        :type raw: str

        **Notes**

        - Updates the collection details and epoch statistics.
        - Calls the ``view`` method for the entire collection and individual time series with specified parameters.
        - Sets view specifications for individual time series, such as y-axis limits and time range.

        """
        self.update(details=True)

        for name in self.collection:
            self.collection[name].update_epochs_stats()

        if skip_main:
            pass
        else:
            self.view(
                show=False, folder=folder, dpi=dpi, fig_format=fig_format, suff=suff
            )

        for name in self.collection:
            # specs
            self.collection[name].view_specs["ymax"] = self.var_max
            self.collection[name].view_specs["ymin"] = 0
            self.collection[name].view_specs["xmax"] = self.end
            self.collection[name].view_specs["xmin"] = self.start
            # view
            self.collection[name].view_specs["folder"] = folder
            self.collection[name].view(show=False)
        return None

    # todo docstring
    def export_data(self, folder, filename=None, merged=True):
        if filename is None:
            filename = self.name
        if merged:
            df = self.get_epochs()
            df.to_csv("{}/{}.csv".format(folder, filename), sep=";", index=False)
            df = self.merge_local_epochs()
            df.to_csv("{}/{}_epochs.csv".format(folder, filename), sep=";", index=False)
        else:
            for name in self.collection:
                df = self.collection[name].export(folder=folder)


class TimeSeriesCluster(TimeSeriesCollection):
    """
    The ``TimeSeriesCluster`` instance is desgined for holding a collection
    of same variable time series. That is, no miscellaneus data is allowed.

    """

    def __init__(self, name="myTimeSeriesCluster", base_object=None):
        # initialize parent
        super().__init__(name=name, base_object=base_object)

        # Set extra specific attributes
        self.varname = base_object().varname
        self.varalias = base_object().varalias

        # Overwrite parent attributes
        self.name_object = "Time Series Cluster"


class TimeSeriesSamples(TimeSeriesCluster):
    # todo improve docstring
    """
    The ``TimeSeriesSamples`` instance is desgined for holding a collection
    of same variable time series arising from the same underlying process.
    This means that all elements in the collection are statistical data.

    .. note::

        This instance allows for the ``reducer()`` method.

    """

    def __init__(self, name="myTimeSeriesSamples", base_object=None):
        # todo [docstring]
        # initialize parent
        super().__init__(name=name, base_object=base_object)
        # Overwrite parent attributes
        self.name_object = "Time Series Samples"

    def reducer(self, reducer_funcs=None, stepwise=False):
        # todo [docstring]

        df_merged = self.merge_data()

        # set up output dict
        dict_out = {self.dtfield: df_merged[self.dtfield].values}

        # get grid
        grd_data = df_merged[df_merged.columns[1:]].values

        for funcname in reducer_funcs:
            # set array
            vct_red = np.zeros(len(df_merged))
            # row loop options
            args = reducer_funcs[funcname]["Args"]
            if args is None:
                if stepwise:
                    for i in range(len(vct_red)):
                        vct_red[i] = reducer_funcs[funcname]["Func"](grd_data[i])
                else:
                    vct_red = reducer_funcs[funcname]["Func"](grd_data, axis=1)
            else:
                if stepwise:
                    for i in range(len(vct_red)):
                        vct_red[i] = reducer_funcs[funcname]["Func"](grd_data[i], args)
                else:
                    vct_red = reducer_funcs[funcname]["Func"](grd_data, args, axis=1)
            # append to dict
            dict_out["{}_{}".format(self.varalias, funcname)] = vct_red[:]

        # set dataframe
        df = pd.DataFrame(dict_out)

        return df

    def mean(self):
        # todo [docstring]
        df = self.reducer(reducer_funcs={"mean": {"Func": np.mean, "Args": None}})
        return df

    def rng(self):
        # todo [docstring]
        df = self.reducer(reducer_funcs={"rng": {"Func": np.r, "Args": None}})
        return df

    def std(self):
        # todo [docstring]
        df = self.reducer(reducer_funcs={"std": {"Func": np.std, "Args": None}})
        return df

    def min(self):
        # todo [docstring]
        df = self.reducer(reducer_funcs={"min": {"Func": np.min, "Args": None}})
        return df

    def max(self):
        # todo [docstring]
        df = self.reducer(reducer_funcs={"max": {"Func": np.max, "Args": None}})
        return df

    def percentile(self, p=90):
        # todo [docstring]
        df = self.reducer(reducer_funcs={"max": {"Func": np.percentile, "Args": p}})
        return df

    def percentiles(self, values=None):
        # todo [docstring]
        if values is None:
            values = [1, 5, 10, 25, 50, 75, 90, 95, 99]
        dict_funcs = {}
        for v in values:
            if v < 10:
                dict_funcs["p0{}".format(v)] = {"Func": np.percentile, "Args": v}
            else:
                dict_funcs["p0{}".format(v)] = {"Func": np.percentile, "Args": v}

        df = self.reducer(reducer_funcs=dict_funcs)
        return df

    def stats(self, basic=False):
        # todo [docstring]
        df_stats = self.reducer(
            reducer_funcs={
                "sum": {"Func": np.sum, "Args": None},
                "mean": {"Func": np.mean, "Args": None},
                "std": {"Func": np.max, "Args": None},
                "min": {"Func": np.min, "Args": None},
                "max": {"Func": np.max, "Args": None},
            }
        )
        if basic:
            values = [25, 50, 75]
        # get percentiles
        df_per = self.percentiles(values=None)
        # join dataframes
        df = pd.merge(left=df_stats, right=df_per, on=self.dtfield)

        return df


class TimeSeriesSpatialSamples(TimeSeriesSamples):
    # todo improve docstring
    """
    The ``TimeSeriesSpatialSamples`` instance is desgined for holding a collection
    of same variable time series arising from the same underlying process in space.
    This means that all elements in the collection are statistical data in space.

    .. note::

        This instance allows for the ``regionalize()`` method.

    """

    def __init__(self, name="myTimeSeriesSpatialSample", base_object=None):
        # todo [docstring]
        # initialize parent
        super().__init__(name=name, base_object=base_object)
        # Overwrite parent attributes
        self.name_object = "Time Series Spatial"

    def get_weights_by_name(self, name, method="average"):
        # todo [docstring]
        # remaining names
        df_remain = self.catalog.query("Name != '{}'".format(name))
        list_names = list(df_remain["Name"].values)

        # w array
        w = np.ones(len(list_names))

        # handle methods
        if method.lower() == "average":
            return w
        elif method.lower() == "idw":
            # Get x,y
            x = self.collection[name].x
            y = self.collection[name].y
            # Get distances
            x_i = np.array([self.collection[_].x for _ in list_names])
            y_i = np.array([self.collection[_].y for _ in list_names])
            d_i = np.sqrt(np.square(x - x_i) + np.square(y - y_i))
            # Compute IDW
            idw_i = 1 / (d_i + (np.mean(d_i) / 10000))  # handle zero distance
            # Normaliza to [0-100] range
            w = 100 * idw_i / np.sum(idw_i)
            return w
        else:
            return w

    # docs ok
    def regionalize(self, method="average"):
        """
        Regionalize the time series data using a specified method.

        :param method: Method for regionalization, default is "average".
        :type method: str

        **Notes**

        - This method handles standardization. If the time series data is not standardized, it applies standardization.
        - Computes epochs for the time series data.
        - Iterates through each time series in the collection and performs regionalization.
        - For each time series, sets up source and destination vectors, computes weights, and calculates regionalized values.
        - Updates the destination column in-place with the regionalized values and updates epochs statistics.
        - Updates the collection catalog with details.


        """
        # Handle stardardization
        if self.isstandard:
            pass
        else:
            self.standardize()
        # Compute Epochs
        df = self.get_epochs()

        for i in range(len(self.catalog)):

            varfield = self.catalog["VarField"].values[
                i
            ]  # todo refactor fields (avoid hardcoded)
            name = self.catalog["Name"].values[i]
            df_src_catalog = self.catalog.query("Name != '{}'".format(name))

            # Get destination vector
            dst_vct = self.collection[name].data[varfield].values
            dst_mask = 1 * np.isnan(dst_vct)

            # Set up source
            src_vars = df_src_catalog["VarField"].values
            src_names = df_src_catalog["Name"].values
            src_alias = df_src_catalog["Alias"].values
            src_columns = [
                "{}_{}".format(src_vars[i], src_alias[i])
                for i in range(len(df_src_catalog))
            ]
            df_src = df[src_columns].copy()  # ensure name order

            # Set up weights
            vct_w = self.get_weights_by_name(name=name, method=method)

            # get product w * values
            w_v = vct_w * ~np.isnan(df_src.values)
            # horizontal weights sum
            w_sum = np.sum(w_v, axis=1)
            w_sum = np.where(w_sum == 0, np.nan, w_sum)
            # output sum
            o_sum = np.nansum(df_src.values * w_v, axis=1)
            # output average
            o = o_sum / w_sum

            # set destination column inplace
            self.collection[name].data[varfield] = np.where(dst_mask == 1, o, dst_vct)
            self.collection[name].update()
            self.collection[name].update_epochs_stats()

        # Update the collection catalog with details
        self.update(details=True)


# Core spatial classes
# -----------------------------------------------------------------------


class Raster(DataSet):
    # todo[docstring] -- examples
    """
    The basic Raster map dataset.

    """

    # Dunder methods
    # -------------------------------------------------------------------
    def __init__(self, name="myRasterMap", alias="Rst", dtype="float32"):
        self.raster_metadata = {
            "ncols": None,
            "nrows": None,
            "xllcorner": None,
            "yllcorner": None,
            "cellsize": None,
            "NODATA_value": None,
            "crs": None,
            "transform": None,
        }
        self.cmap = "jet"
        # extra
        self.varname = "Unknown variable"
        self.varalias = "UnVar"
        self.units = "unknown"
        self.datetime = None  # "2020-01-01"

        # ------------ call super ----------- #
        super().__init__(name=name, alias=alias)
        # -------------------------------------
        # set basic attributes
        self.dtype = dtype
        self.backup_data = None
        self.is_masked = False
        self.file_prj = None
        self.prj = None
        # accessible values
        self.nodatavalue = self.raster_metadata["NODATA_value"]
        self.cellsize = self.raster_metadata["cellsize"]
        # stats
        self.stats = None

    def __str__(self):
        dct_meta = self.get_metadata()
        lst_ = list()
        lst_.append("\n")
        lst_.append("Object: {}".format(type(self)))
        lst_.append("Metadata:")
        for k in dct_meta:
            lst_.append("\t{}: {}".format(k, dct_meta[k]))
        return "\n".join(lst_)

    # Core internal methods
    # -------------------------------------------------------------------
    def _set_fields(self):
        """
        Set fields names.
        Expected to increment superior methods.

        """
        # ------------ call super ----------- #
        super()._set_fields()
        # Attribute fields
        self.field_varname = "var_name"
        self.field_varalias = "var_alias"
        self.field_units = "units"
        self.field_datetime = "datetime"
        self.field_cellsize = "resolution"
        self.field_nrows = "rows"
        self.field_ncols = "columns"
        self.field_xll = "xll"
        self.field_yll = "yll"
        self.field_nodatavalue = "nodata_value"
        self.field_crs = "crs"
        self.field_epsg = "epsg"
        self.field_file_prj = "file_prj"
        # ... continues in downstream objects ... #

    # Get methods
    # -------------------------------------------------------------------

    def get_metadata(self):
        """
        Get a dictionary with object metadata.
        Expected to increment superior methods.

        .. note::

            Metadata does **not** necessarily inclue all object attributes.

        :return: dictionary with all metadata
        :rtype: dict
        """
        # ------------ call super ----------- #
        dict_meta = super().get_metadata()

        # customize local metadata:
        dict_meta_local = {
            self.field_varname: self.varname,
            self.field_varalias: self.varalias,
            self.field_units: self.units,
            self.field_datetime: self.datetime,
            self.field_cellsize: self.raster_metadata["cellsize"],
            self.field_nrows: self.raster_metadata["nrows"],
            self.field_ncols: self.raster_metadata["ncols"],
            self.field_xll: self.raster_metadata["xllcorner"],
            self.field_yll: self.raster_metadata["yllcorner"],
            self.field_nodatavalue: self.raster_metadata["NODATA_value"],
        }
        # update
        dict_meta.update(dict_meta_local)
        return dict_meta

    def get_bbox(self):
        """
        Get the Bounding Box of the map.

        :return: Dictionary of xmin, xmax, ymin, and ymax.
            - "xmin" (float): Minimum x-coordinate.
            - "xmax" (float): Maximum x-coordinate.
            - "ymin" (float): Minimum y-coordinate.
            - "ymax" (float): Maximum y-coordinate.
        :rtype: dict
        """
        return {
            "xmin": self.raster_metadata["xllcorner"],
            "xmax": self.raster_metadata["xllcorner"]
            + (self.raster_metadata["ncols"] * self.cellsize),
            "ymin": self.raster_metadata["yllcorner"],
            "ymax": self.raster_metadata["yllcorner"]
            + (self.raster_metadata["nrows"] * self.cellsize),
        }

    def get_extent(self):
        """
        Get the Extent of the map. See get_bbox.

        :return: list of [xmin, xmax, ymin, ymax]
        :rtype: list
        """
        d = self.get_bbox()
        extent = [d["xmin"], d["xmax"], d["ymin"], d["ymax"]]
        return extent

    def get_grid_datapoints(self, drop_nan=False):
        """
        Get flat and cleared grid data points (x, y, and z).

        **Notes**
        This function extracts coordinates (x, y, and z) from the raster grid.
        The x and y coordinates are determined based on the grid cell center positions.
        If drop_nan is True, nan values are ignored in the resulting DataFrame.
        The resulting DataFrame includes columns for x, y, z, i, and j coordinates.

        :param drop_nan: Option to ignore nan values.
        :type drop_nan: bool
        :return: DataFrame of x, y, and z fields.
        :rtype: :class:`pandas.DataFrame``` or None. If the grid is None, returns None.

        """
        if self.data is None:
            return None
        else:
            # get coordinates
            vct_i = np.zeros(self.data.shape[0] * self.data.shape[1])
            vct_j = vct_i.copy()
            vct_z = vct_i.copy()
            _c = 0
            for i in range(len(self.data)):
                for j in range(len(self.data[i])):
                    vct_i[_c] = i
                    vct_j[_c] = j
                    vct_z[_c] = self.data[i][j]
                    _c = _c + 1

            # transform
            n_height = self.data.shape[0] * self.cellsize
            vct_y = (
                self.raster_metadata["yllcorner"]
                + (n_height - (vct_i * self.cellsize))
                - (self.cellsize / 2)
            )
            vct_x = (
                self.raster_metadata["xllcorner"]
                + (vct_j * self.cellsize)
                + (self.cellsize / 2)
            )

            # drop nan or masked values:
            if drop_nan:
                vct_j = vct_j[~np.isnan(vct_z)]
                vct_i = vct_i[~np.isnan(vct_z)]
                vct_x = vct_x[~np.isnan(vct_z)]
                vct_y = vct_y[~np.isnan(vct_z)]
                vct_z = vct_z[~np.isnan(vct_z)]
            # built dataframe
            _df = pd.DataFrame(
                {
                    "x": vct_x,
                    "y": vct_y,
                    "z": vct_z,
                    "i": vct_i,
                    "j": vct_j,
                }
            )
            return _df

    def get_grid_data(self):
        """
        Get flat and cleared grid values.

        :return: 1D vector of cleared sample.
        :rtype: :class:`numpy.ndarray`` or None. If the grid is None, returns None.

        **Notes**

        - This function extracts and flattens the grid, removing any masked or NaN values.
        - For integer grids, the masked values are ignored.
        - For floating-point grids, both masked and NaN values are ignored.

        """
        if self.data is None:
            return None
        else:
            if self.data.dtype.kind in ["i", "u"]:
                # for integer grid
                _grid = self.data[~self.data.mask]
                return _grid
            else:
                # for floating point grid:
                _grid = self.data.ravel()[~np.isnan(self.data.ravel())]
                return _grid

    def get_univar(self):
        """
        Creates and returns a Univar object initialized with the current object's grid data.

        :return: A Univar object containing the grid data for univariate analysis.
        :rtype: :class:`plans.analyst.Univar`
        """
        from plans.analyst import Univar

        uni = Univar()
        uni.set_array(array=self.get_grid_data())
        return uni

    def get_stats(self, inplace=False):
        """
        Get basic statistics from flat and cleared grid.

        :return: Dict of basic statistics. If the grid is None, returns None.
        :rtype: dict or None

        """
        df = self.get_stats_df()
        dc = {}
        for row_dict in df.to_dict(orient="records"):
            dc[row_dict["statistic"]] = row_dict["value"]
        if inplace:
            self.stats = dc
        else:
            return dc

    def get_stats_df(self):
        """
        Get :class:`pandas.DataFrame` statistics from flat and cleared grid.

        :return: DataFrame of basic statistics. If the grid is None, returns None.
        :rtype: :class:`pandas.DataFrame` or None

        """
        uni = self.get_univar()
        return uni.assess_basic_stats()

    def get_aoi(self, by_value_lo, by_value_hi):
        """
        Get the AOI map from an interval of values (values are expected to exist in the raster).

        :param by_value_lo: Number for the lower bound (inclusive).
        :type by_value_lo: float
        :param by_value_hi: Number for the upper bound (inclusive).
        :type by_value_hi: float
        :return: AOI map.
        :rtype: :class:`AOI`` object

        **Notes**

        - This function creates an AOI (Area of Interest) map based on a specified value range.
        - The AOI map is constructed as a binary grid where values within the specified range are set to 1, and others to 0.

        """
        map_aoi = AOI(name="{} {}-{}".format(self.varname, by_value_lo, by_value_hi))
        map_aoi.set_raster_metadata(metadata=self.raster_metadata)
        map_aoi.prj = self.prj
        # set grid
        self.insert_nodata()
        map_aoi.set_data(
            grid=1 * (self.data >= by_value_lo) * (self.data <= by_value_hi)
        )
        self.mask_nodata()
        return map_aoi

    # Core methods
    # -------------------------------------------------------------------

    def update(self):
        """
        Refresh all mutable attributes based on data (includins paths).
        Expected to be incremented downstream.

        """
        super().update()
        # refresh all mutable attributes
        if self.data is not None:
            # data size
            self.size = self.raster_metadata["nrows"] * self.raster_metadata["ncols"]

        # raster metadata attributes
        self.nodatavalue = self.raster_metadata["NODATA_value"]
        self.cellsize = self.raster_metadata["cellsize"]

        # ... continues in downstream objects ... #
        return None

    def set_data(self, grid):
        """
        Set the data grid for the raster object.
        This function allows setting the data grid for the raster object.
        The incoming grid should be a NumPy array.

        :param grid: The data grid to be set for the raster.
        :type grid: :class:`numpy.ndarray`

        **Notes**

        - The function overwrites the existing data grid in the raster object with the incoming grid, ensuring that the data type matches the raster's dtype.
        - Nodata values are masked after setting the grid.

        """
        # overwrite incoming dtype
        self.data = grid.astype(self.dtype)
        # mask nodata values
        self.mask_nodata()
        return None

    def set_raster_metadata(self, metadata):
        """
        Set metadata for the raster object based on incoming metadata.
        This function allows setting metadata for the raster object from an incoming metadata dictionary.
        The metadata should include information such as the number of columns, number of rows, corner coordinates, cell size, and nodata value.

        :param metadata: A dictionary containing metadata for the raster.
        :type metadata: dict

        """
        for k in self.raster_metadata:
            if k in metadata:
                self.raster_metadata[k] = metadata[k]
        self.cellsize = self.raster_metadata[k]
        return None

    # Load data methods
    # -------------------------------------------------------------------

    def load_data(self, file_data, file_prj=None, id_band=1):
        """
        Load data and metadata from files to the Raster object.

        :param file_data: The path to the raster file.
        :type file_data: str
        :param file_prj: The path to the '.prj' projection file. If not provided, an attempt is made to use the same path and name as the ``.asc`` file with the '.prj' extension.
        :type file_prj: str
        :param id_band: Band id to read for GeoTIFF. Default value = 1
        :type id_band: int

        """
        # handle extension
        s_extension = os.path.basename(file_data).split(".")[-1]
        if s_extension == "asc":
            self.load_asc(file_input=file_data)
        else:
            self.load_tif(file_input=file_data, id_band=id_band)
        self.load_prj(file_input=file_prj)
        self.file_data = file_data
        self.update()
        return None

    def load_metadata(self, file_data):
        """
        Load only metadata from files to the raster object.

        :param file_data: The path to the raster file.
        :type file_data: str


        """
        # handle extension
        s_extension = os.path.basename(file_data).split(".")[-1]
        if s_extension == "asc":
            self.load_asc_metadata(file_input=file_data)
        else:
            self.load_tif_metadata(file_input=file_data, id_band=id_band)
        self.update()
        return None

    def load_image(self, file_input, xxl=False):
        """
        Load data from an image '.tif' raster files.

        :param file_input: The file path of the '.tif' raster file.
        :type file_input: str
        :param xxl: option flag for very large images
        :type xxl: bool



        **Notes**

        - The function uses the Pillow (PIL) library to open the '.tif' file and converts it to a NumPy array.
        - Metadata may need to be provided separately, as this function focuses on loading raster data.
        - The loaded data grid is set using the ``set_grid`` method of the raster object.

        """
        from PIL import Image

        if xxl:
            Image.MAX_IMAGE_PIXELS = None
        # Open the TIF file
        img_data = Image.open(file_input)
        # Convert the PIL image to a NumPy array
        grd_data = np.array(img_data)
        # set grid
        self.set_data(grid=grd_data)
        return None

    def load_tif(self, file_input, id_band=1):
        """
        Load data and metadata from `.tif` raster file.

        :param file_input: The file path to the ``.tif`` raster file.
        :type file_input: str


        """
        dc_raster = Raster.read_tif(
            file_input=file_input, dtype=self.dtype, id_band=id_band, metadata=True
        )
        # Set metadata and grid
        self.set_raster_metadata(metadata=dc_raster["metadata"].copy())
        self.set_data(grid=dc_raster["data"])
        return None

    def load_tif_metadata(self, file_input, id_band=1):
        """
        Load only metadata from `.tif` raster file.

        :param file_input: The file path to the ``.tif`` raster file.
        :type file_input: str


        """
        dc_metadata = Raster.read_tif_metadata(file_input=file_input, id_band=id_band)
        self.set_raster_metadata(metadata=dc_metadata)
        return None

    def load_asc(self, file_input):
        """
        Load data and metadata from `.asc` raster file.

        :param file_input: The file path to the ``.asc`` raster file.
        :type file_input: str


        """
        dc_raster = Raster.read_asc(
            file_input=file_input, dtype=self.dtype, metadata=True
        )
        # Set metadata and grid
        self.set_raster_metadata(metadata=dc_raster["metadata"].copy())
        self.set_data(grid=dc_raster["data"])
        return None

    def load_asc_metadata(self, file_input):
        """
        Load only metadata from ``.asc`` raster files.

        :param file_input: The file path to the ``.asc`` raster file.
        :type file_input: str



        """
        meta_dct = Raster.read_asc_metadata(file_input=file_input)
        # set attribute
        self.set_raster_metadata(metadata=meta_dct)
        return None

    def load_prj(self, file_input):
        """
        Load '.prj' auxiliary file to the 'prj' attribute.

        :param file_input: The file path to the '.prj' auxiliary file.
        :type file_input: str



        """
        if file_input is not None:
            # handle expected file
            if os.path.isfile(file_input):
                self.file_prj = file_input
                with open(file_input) as f:
                    self.prj = f.readline().strip("\n")
        return None

    def copy_structure(self, raster_ref, n_nodatavalue=None):
        """
        Copy structure (metadata and prj) from another raster object.

        :param raster_ref: The reference incoming raster object from which to copy.
        :type raster_ref: :class:`datasets.Raster`
        :param n_nodatavalue: The new nodata value for different raster objects. If None, the nodata value remains unchanged.
        :type n_nodatavalue: float

        """
        dict_meta = raster_ref.raster_metadata.copy()
        # handle new nodatavalue
        if n_nodatavalue is None:
            pass
        else:
            dict_meta["NODATA_value"] = n_nodatavalue
        self.set_raster_metadata(metadata=dict_meta)
        self.prj = raster_ref.prj[:]
        return None

    # Export methods
    # -------------------------------------------------------------------

    def export(self, folder, filename=None, mode="tif"):
        """
        Exports the raster to a specified file format and location.

        :param folder: The destination folder for the exported file.
        :type folder: str
        :param filename: [optional] The name of the output file. If None, the original raster name is used.
        :type filename: str
        :param mode: The export format, either "tif" (default) or "asc". Default value = "tif"
        :type mode: str


        """
        if filename is None:
            filename = self.name
        # handle mode
        if mode == "asc":
            self.export_asc(folder=folder, filename=filename)
        else:
            self.export_tif(folder=folder, filename=filename)
        # export prj
        self.export_prj(folder=folder, filename=filename)
        return None

    def export_tif(self, folder, filename=None):
        """
        Export an ``.tif`` raster file..

        :param folder: The directory path to export the raster file.
        :type folder: str
        :param filename: The name of the exported file without extension. If None, the name of the raster object is used.
        :type filename: str
        :return: The full file name (path and extension) of the exported raster file.
        :rtype: str
        """
        if self.data is None or self.raster_metadata is None:
            return None
        else:
            if filename is None:
                filename = self.name
            flenm = str(folder) + "/" + filename + ".tif"
            Raster.write_tif(
                grid_output=self.data,
                dc_metadata=self.raster_metadata,
                file_output=flenm,
                dtype=self.dtype,
                n_bands=1,
                id_band=1,
            )
            return flenm

    def export_asc(self, folder, filename=None):
        """
        Export an ``.asc`` raster file.

        :param folder: The directory path to export the raster file.
        :type folder: str
        :param filename: The name of the exported file without extension. If None, the name of the raster object is used.
        :type filename: str
        :return: The full file name (path and extension) of the exported raster file.
        :rtype: str
        """
        if self.data is None or self.raster_metadata is None:
            return None
        else:
            if filename is None:
                filename = self.name
            flenm = folder + "/" + filename + ".asc"
            Raster.write_asc(
                grid_output=self.data,
                dc_metadata=self.raster_metadata,
                file_output=flenm,
                dtype=self.dtype,
            )
            return flenm

    def export_prj(self, folder, filename=None):
        """
        Export a '.prj' file. This function exports the coordinate system information to a '.prj' file in the specified folder.

        :param folder: The directory path to export the '.prj' file.
        :type folder: str
        :param filename: The name of the exported file without extension. If None, the name of the raster object is used.
        :type filename: str
        :return: The full file name (path and extension) of the exported '.prj' file, or None if no coordinate system information is available.
        :rtype: str or None
        """
        if self.prj is None:
            return None
        else:
            if filename is None:
                filename = self.name
            flenm = folder + "/" + filename + ".prj"
            fle = open(flenm, "w+")
            fle.writelines([self.prj])
            fle.close()
            return flenm

    # Nodata methods
    # -------------------------------------------------------------------

    def reset_nodata(self, new_nodata, ensure=True):
        """
        Resets the no-data value in the raster metadata and updates the data mask accordingly.

        This method first ensures the current no-data values are masked, then updates the
        `NODATA_value` in the raster metadata, and finally re-applies the mask based on the new no-data value.

        :param new_nodata: The new no-data value to set.
        :type new_nodata: int or float
        :param ensure: If True, ensures the current no-data values are masked before resetting. Default value = True
        :type ensure: bool


        """
        # ensure current nodata is masked
        if ensure:
            self.mask_nodata()
        # reset in metadata
        self.raster_metadata["NODATA_value"] = new_nodata
        # de-mask
        self.insert_nodata()
        # mask again
        self.mask_nodata()
        return None

    def mask_nodata(self):
        """
        Mask grid cells as NaN where data is NODATA.




        **Notes**

        - The function masks grid cells as NaN where the data is equal to the specified NODATA value.
        - If NODATA value is not set, no masking is performed.

        """
        if self.nodatavalue is None:
            pass
        else:
            if self.data.dtype.kind in ["i", "u"]:
                # for integer grid
                self.data = np.ma.masked_where(self.data == self.nodatavalue, self.data)
            else:
                # for floating point grid:
                self.data[self.data == self.nodatavalue] = np.nan
        return None

    def insert_nodata(self):
        """
        Set grid cells as NODATA where data is NaN using the static method.
        """
        # Call the static method and update the instance's grid
        self.data = Raster.apply_nodata(self.data, self.nodatavalue)
        return None

    # AOI methods
    # -------------------------------------------------------------------

    def load_aoi_mask(self, file_raster, inplace=False):
        """
        Loads an Area of Interest (AOI) mask from a raster file and applies it to the current object's data.

        :param file_raster: The file path to the AOI raster.
        :type file_raster: str
        :param inplace: If True, the mask is applied in-place to the current object's data. Default value = False
        :type inplace: bool


        """
        from plans.datasets import AOI

        r = AOI()
        r.load_data(file_data=file_raster)
        self.apply_aoi_mask(grid_aoi=r.data, inplace=inplace)
        del r
        return None

    def apply_aoi_mask(self, grid_aoi, inplace=False):
        """
        Apply AOI (area of interest) mask to the raster map.
        This function applies an AOI (area of interest) mask to the raster map,
        replacing values outside the AOI with the NODATA value.

        **Notes**
        The function replaces values outside the AOI (where grid_aoi is 0) with the NODATA value.
        If NODATA value is not set, no replacement is performed.
        If inplace is True, the main grid is modified. If False, a backup of the grid is created before modification.
        This function is useful for focusing analysis or visualization on a specific area within the raster map.

        :param grid_aoi: Map of AOI (masked array or pseudo-boolean). Expected to have the same grid shape as the raster.
        :type grid_aoi: :class:`numpy.ndarray`
        :param inplace: If True, overwrite the main grid with the masked values.
            If False, create a backup and modify a copy of the grid. Default is False.
        :type inplace: bool



        """
        if self.nodatavalue is None or self.data is None:
            pass
        else:
            # ensure fill on masked values
            grid_aoi = np.ma.filled(grid_aoi, fill_value=0)
            # replace
            grd_mask = np.where(grid_aoi == 0, self.nodatavalue, self.data)

            if inplace:
                pass
            else:
                # pass a copy to backup grid
                self.backup_data = self.data.copy()
            # set main grid
            self.set_data(grid=grd_mask)
            self.is_masked = True
        return None

    def release_aoi_mask(self):
        """
        Release AOI mask from the main grid. Backup grid is restored.

        This function releases the AOI (area of interest) mask from the main grid,
        restoring the original values from the backup grid.

        **Notes**
        If an AOI mask has been applied, this function restores the original values to the main grid from the backup grid.
        If no AOI mask has been applied, the function has no effect.
        After releasing the AOI mask, the backup grid is set to None, and the raster object is no longer considered to have an AOI mask.




        """
        if self.is_masked:
            self.set_data(grid=self.backup_data)
            self.backup_data = None
            self.is_masked = False
        return None

    # Transformation methods
    # -------------------------------------------------------------------

    def rebase_grid(self, base_raster, inplace=False, method="linear_model"):
        """
        Rebase the grid of a raster.
        This function creates a new grid based on a provided reference raster.
        Both rasters are expected to be in the same coordinate system and have overlapping bounding boxes.

        :param base_raster: The reference raster used for rebase. It should be in the same coordinate system and have overlapping bounding boxes.
        :type base_raster: :class:`datasets.Raster`
        :param inplace: If True, the rebase operation will be performed in-place, and the original raster's grid will be modified. If False, a new rebased grid will be returned, and the original data will remain unchanged. Default is False.
        :type inplace: bool
        :param method: Interpolation method for rebasing the grid. Options include "linear_model," "nearest," and "cubic." Default is "linear_model."
        :type method: str
        :return: If inplace is False, a new rebased grid as a NumPy array. If inplace is True, returns None, and the original raster's grid is modified in-place.
        :rtype: :class:`numpy.ndarray`` or None

        Notes

        - The rebase operation involves interpolating the values of the original grid to align with the reference raster's grid.
        - The method parameter specifies the interpolation method and can be "linear_model," "nearest," or "cubic."
        - The rebase assumes that both rasters are in the same coordinate system and have overlapping bounding boxes.
        """
        from scipy.interpolate import griddata

        # get data points
        _df = self.get_grid_datapoints(drop_nan=True)
        # get base grid data points
        _dfi = base_raster.get_grid_datapoints(drop_nan=False)
        # set data points
        grd_points = np.array([_df["x"].values, _df["y"].values]).transpose()
        grd_new_points = np.array([_dfi["x"].values, _dfi["y"].values]).transpose()
        _dfi["zi"] = griddata(
            points=grd_points, values=_df["z"].values, xi=grd_new_points, method=method
        )
        grd_zi = np.reshape(_dfi["zi"].values, newshape=base_raster.data.shape)
        if inplace:
            # set
            self.set_data(grid=grd_zi)
            self.set_raster_metadata(metadata=base_raster.raster_metadata)
            self.prj = base_raster.prj
            return None
        else:
            return grd_zi

    def cut_edges(self, upper, lower, inplace=False):
        """
        Cutoff upper and lower values of the raster grid.

        :param upper: The upper value for the cutoff.
        :type upper: float or int
        :param lower: The lower value for the cutoff.
        :type lower: float or int
        :param inplace: If True, modify the main grid in-place. If False, create a processed copy of the grid. Default is False.
        :type inplace: bool
        :return: The processed grid if inplace is False. If inplace is True, returns None.
        :rtype: Union[None, np.ndarray]

        **Notes**
        Values in the raster grid below the lower value are set to the lower value.
        Values in the raster grid above the upper value are set to the upper value.
        If inplace is False, a processed copy of the grid is returned, leaving the original grid unchanged.
        This function is useful for clipping extreme values in the raster grid.

        """
        if self.data is None:
            return None
        else:
            new_grid = geo.prune(array=self.data, min_value=lower, max_value=upper)
            if inplace:
                self.set_data(grid=new_grid)
                return None
            else:
                return new_grid

    # View internal methods
    # -------------------------------------------------------------------

    def _plot(self, fig, gs, specs):
        """
        Generates a plot visualizing the Raster data.

        :param fig: The matplotlib figure object.
        :type fig: :class:`matplotlib.figure.Figure`
        :param gs: The matplotlib gridspec object for arranging subplots.
        :type gs: :class:`matplotlib.gridspec.GridSpec`
        :param specs: A dictionary containing plotting specifications and options.
        :type specs: dict
        :return: The modified matplotlib figure object with the plots.
        :rtype: :class:`matplotlib.figure.Figure`
        """
        # todo [DRY] most of this can be run on Univar -- make static method?
        import matplotlib.ticker as mticker

        # from matplotlib.ticker import PercentFormatter  # Import PercentFormatter
        formatter = mticker.ScalarFormatter(useOffset=False, useMathText=False)
        formatter.set_scientific(False)  # Ensure scientific notation is off

        def _get_max(std_values, data):
            data_max = np.max(data)
            closest_max_index = np.argmin(np.abs(np.array(std_values) - data_max))
            _id = closest_max_index + 1
            if _id >= len(std_values):
                _id = len(std_values) - 1
            return std_values[_id]

        def _plot_mean(axe, xmin, xmax):
            axe.hlines(
                y=y_mu,
                xmin=xmin,
                xmax=xmax,
                colors="red",
            )
            axe.annotate(
                r" $\mu$ = {}".format(round(y_mu, 2)),
                xy=(xmin, y_mu),
                xytext=(1, 3),
                textcoords="offset points",
                color="red",
            )

        # ------------- get aux data -------------
        uni = self.get_univar()
        y_mu = uni.stats_df.loc[uni.stats_df["statistic"] == "mean", "value"].values[0]

        ylim = specs["range"]
        # handle no range
        if specs["range"] is None:
            p_low = uni.stats_df.loc[
                uni.stats_df["statistic"] == "p01", "value"
            ].values[0]
            p_hi = uni.stats_df.loc[uni.stats_df["statistic"] == "p99", "value"].values[
                0
            ]
            rng = p_hi - p_low
            rng_margin = rng * 0.1
            ylim = (p_low - rng_margin, p_hi + rng_margin)

        # handle aux vars
        plot_mean = specs["plot_mean"]

        # ------------ setup axes ------------
        ax1 = fig.add_subplot(gs[2:14, 0:12])
        ax2 = fig.add_subplot(gs[2:8, 15:19])
        ax3 = fig.add_subplot(gs[2:8, 20:])
        ax_cbar = fig.add_subplot(gs[2:8, 12:13])

        if specs["title"] is not None:
            plt.suptitle(specs["title"], fontsize=9)

        # ------------ map plot ------------
        # handle zoom window
        i_min = 0
        i_max = len(self.data)
        j_min = 0
        j_max = len(self.data[0])
        if specs["zoom_window"] is not None:
            i_min = specs["zoom_window"]["i_min"]
            i_max = specs["zoom_window"]["i_max"]
            j_min = specs["zoom_window"]["j_min"]
            j_max = specs["zoom_window"]["j_max"]
        grid_show = self.data[i_min:i_max, j_min:j_max]
        grid_show_squared = Raster.make_square(grid_input=grid_show)
        # plot image
        im = ax1.imshow(
            grid_show_squared,
            cmap=specs["cmap"],
            vmin=ylim[0],
            vmax=ylim[1],
            interpolation="none",
            # extent=self.get_extent(),
            aspect="equal",
            origin="upper",
        )
        ax1.set_autoscale_on(False)  # Prevent auto-scaling which might add padding

        # plot helper geometry
        helper_geometry = specs["geometry"]
        if helper_geometry is not None:
            helper_geometry.plot(ax=ax1, color="none", edgecolor="k")
        if specs["subtitle_map"] is not None:
            ax1.set_title(specs["subtitle_map"], loc="left")
        # handle tick labels
        ax1.yaxis.set_major_formatter(formatter)
        ax1.xaxis.set_major_formatter(formatter)
        if specs["grid_map"]:
            ax1.grid(visible=specs["grid_map"])
        else:
            ax1.axis("off")
        ax1.grid(False)

        cbar = fig.colorbar(
            im, fraction=1, extend="neither", ax=ax_cbar, location="left"
        )
        # Set the tick locations to only min and max
        cbar.set_ticks(ylim)

        # Format the tick labels to display only these values
        # This custom formatter ensures only the set ticks are labeled
        # cbar.set_ticklabels(ylim)
        cbar.ax.yaxis.set_tick_params(which="both", labelleft=True, labelright=False)
        ax_cbar.axis("off")

        # todo [DRY] -- this can be optimized since is the same plots in Univar._plot()
        # ------------ hist plot ------------
        # Standard x-axis maximum values for hist
        sdmax1 = list(np.linspace(1, 9, 9) / 100)
        sdmax2 = list(np.linspace(10, 100, 10) / 100)
        standard_max_values = sdmax1 + sdmax2
        data = uni.data[uni.varfield].values
        h = ax2.hist(
            data,
            bins=specs["bins"],
            color=specs["color_hist"],
            alpha=1,
            orientation="horizontal",
            weights=np.ones(len(data)) / len(data),
        )
        ax2.xaxis.set_major_formatter(mticker.PercentFormatter(1))
        if specs["subtitle_hist"] is not None:
            ax2.set_title(specs["subtitle_hist"], loc="left")
        # Get the maximum value from the data
        xmax = _get_max(standard_max_values, h[0]) * 1.1
        ax2.set_xlim(0, xmax)
        ax2.set_ylim(ylim)
        ax2.set_xlabel("%")
        ax2.set_ylabel(specs["ylabel"])
        ax2.yaxis.set_major_formatter(formatter)
        # extra lines
        if plot_mean:
            _plot_mean(
                ax2,
                xmin=0,
                xmax=xmax,
            )

        # ------------ CDF plot ------------
        ax3.plot(
            uni.weibull_df["P(X)"], uni.weibull_df["Data"], color=specs["color_cdf"]
        )
        if specs["subtitle_cdf"] is not None:
            ax3.set_title(specs["subtitle_cdf"], loc="left")
        ax3.set_xlabel(specs["xlabel_cdf"])
        # ax3.set_xticklabels([0, 0.5, 1.0])
        ax3.set_xlim(-0.05, 1.05)
        ax3.xaxis.set_major_formatter(mticker.PercentFormatter(1))
        ax3.set_ylim(ylim)
        ax3.yaxis.set_major_formatter(formatter)
        ax3.set_yticklabels([])

        # extra lines
        if plot_mean:
            _plot_mean(
                ax3,
                xmin=-0.05,
                xmax=1.05,
            )

        fig = Univar.plot_stats(fig=fig, stats_df=uni.stats_df, x=0.5, y=0.4)
        fig = Raster.plot_metadata(
            fig=fig, metadata=self.raster_metadata, x=0.02, y=0.1
        )
        return fig

    def _set_view_specs(self):
        """
        Set default view specs.

        """
        super()._set_view_specs()
        # borrow from Univar
        uv = GeoUnivar()
        self.view_specs.update(uv.view_specs)
        self.view_specs.update(
            {
                "cmap": self.cmap,
                "title": "{} | {}".format(self.varname, self.name),
                "run_id": None,
                "zoom_window": None,
                "subtitle_map": "2D distribution",
            }
        )
        self.view_specs["ylabel"] = self.units
        self.view_specs["grid_map"] = False
        return None

    # View methods
    # -------------------------------------------------------------------

    def view(self, show=True, return_fig=False, helper_geometry=None):
        """
        Displays or returns a visualization of the spatial data.

        :param show: If True, the plot is displayed. Default value = True
        :type show: bool
        :param return_fig: If True, the matplotlib figure object is returned. Default value = False
        :type return_fig: bool
        :param helper_geometry: [optional] An optional geometry object to overlay on the map.
        :type helper_geometry: object
        :return: The matplotlib figure object if `return_fig` is True, otherwise None.
        :rtype: :class:`matplotlib.figure.Figure` or None
        """
        # handle specs
        specs = self.view_specs.copy()
        specs_aux = {
            "ncols": 24,
            "nrows": 16,
            "width": viewer.FIG_SIZES["M"]["w"],
            "height": viewer.FIG_SIZES["M"]["h"],
        }
        # update
        specs.update(specs_aux)
        # update gridspecs
        specs.update(viewer.GRID_SPECS)
        # update geometry
        specs["geometry"] = helper_geometry

        # -------------- BUILD --------------
        fig, gs = viewer.build_fig(specs=specs)

        # -------------- PLOT --------------
        fig = self._plot(fig=fig, gs=gs, specs=specs)

        # -------------- SHIP --------------
        # plt.tight_layout()
        # create path
        file_path = "{}/{}.{}".format(
            specs["folder"], specs["filename"], specs["fig_format"]
        )
        if return_fig:
            return fig
        else:
            viewer.ship_fig(fig=fig, show=show, file_output=file_path, dpi=specs["dpi"])

    # Static methods
    # -------------------------------------------------------------------

    @staticmethod
    def plot_metadata(fig, metadata, x=0.0, y=0.1):
        """
        Adds raster metadata as text annotations to a matplotlib figure.

        :param fig: The matplotlib figure object to which metadata will be added.
        :type fig: :class:`matplotlib.figure.Figure`
        :param metadata: A dictionary containing raster metadata (e.g., 'nrows', 'ncols', 'cellsize', 'xllcorner', 'yllcorner', 'NODATA_value').
        :type metadata: dict
        :param x: The x-coordinate (figure fraction) for the left-most column of metadata. Default value = 0.0
        :type x: float
        :param y: The y-coordinate (figure fraction) for the top row of metadata. Default value = 0.1
        :type y: float
        :return: The modified matplotlib figure object.
        :rtype: :class:`matplotlib.figure.Figure`
        """

        def _plot_column(x_position, ls_meta, start_y):
            current_y = start_y
            for m in ls_meta:
                plt.text(
                    x=x_position,
                    y=current_y,
                    s=m,
                    fontdict={"family": "monospace"},
                    transform=fig.transFigure,
                )
                current_y -= n_step

        n_step = 0.03

        s1 = "{:>10}: {:<10}".format("Rows", metadata["nrows"])
        s2 = "{:>10}: {:<10}".format("Cols", metadata["ncols"])
        s3 = "{:>10}: {:<10.2f}".format("Cell", metadata["cellsize"])
        ls_meta = [s1, s2, s3]
        _plot_column(x_position=x, ls_meta=ls_meta, start_y=y)

        s1 = "{:>10}: {:<10.2f}".format("XLL", metadata["xllcorner"])
        s2 = "{:>10}: {:<10.2f}".format("YLL", metadata["yllcorner"])
        s3 = "{:>10}: {:<10.2f}".format("NaN", metadata["NODATA_value"])
        ls_meta = [s1, s2, s3]
        _plot_column(x_position=x + 0.15, ls_meta=ls_meta, start_y=y)

        return fig

    @staticmethod
    def read_tif_metadata(file_input, n_band=1):
        """
        Read raster metadata from a file.

        :param file_input: Path to the input raster file.
        :type file_input: str
        :param n_band: [optional] Band number to read. Default value = 1
        :type n_band: int
        :return: Dictionary containing raster metadata.
        :rtype: dict
        """
        raster_input = rasterio.open(file_input)
        dc_metatada = {
            "ncols": raster_input.width,
            "nrows": raster_input.height,
            "xllcorner": raster_input.bounds.left,
            "yllcorner": raster_input.bounds.bottom,
            "cellsize": raster_input.res[0],
            "NODATA_value": raster_input.nodata,
            "crs": raster_input.crs,
            "transform": raster_input.transform,
        }
        raster_input.close()
        return dc_metatada

    @staticmethod
    def read_tif(file_input, dtype="float", id_band=1, metadata=True):
        """
        Read a raster band from a file.

        :param file_input: Path to the input raster file.
        :type file_input: str
        :param dtype: Data type for the output grid. Default value = "float"
        :type dtype: str
        :param id_band: Band id to read. Default value = 1
        :type id_band: int
        :param metadata: Whether to include metadata in the output dictionary. Default value = True
        :type metadata: bool
        :return: Dictionary containing the raster grid and optionally its metadata.
        :rtype: dict
        """
        raster_input = rasterio.open(file_input)
        grid_input = raster_input.read(id_band)
        dc_raster = {"data": grid_input.astype(dtype)}
        if metadata:
            dc_metadata = Raster.read_tif_metadata(file_input, id_band)
            dc_raster["metadata"] = dc_metadata
        raster_input.close()
        return dc_raster

    @staticmethod
    def write_tif(
        grid_output, dc_metadata, file_output, dtype="float32", n_bands=1, id_band=1
    ):
        """
        Write a raster band to a file.

        :param grid_output: The grid data to write.
        :type grid_output: :class:`numpy.ndarray`
        :param dc_metadata: Dictionary containing the raster metadata.
        :type dc_metadata: dict
        :param file_output: Path to the output raster file.
        :type file_output: str
        :param dtype: Data type alias for the output grid (numpy standard). Default value = "float32"
        :type dtype: str
        :param n_bands: Number of bands in the output raster. Default value = 1
        :type n_bands: int
        :param id_band: Band ID to write the data to. Default value = 1
        :type id_band: int
        :return: Path to the output raster file. (echo)
        :rtype: str
        """
        # Define the profile for the new GeoTIFF
        profile = {
            "driver": "GTiff",
            "height": dc_metadata["nrows"],
            "width": dc_metadata["ncols"],
            "count": n_bands,
            "dtype": dtype,
            "crs": dc_metadata["crs"],
            "transform": dc_metadata["transform"],
            "nodata": dc_metadata["NODATA_value"],
            "compress": "lzw",  # Using LZW compression
        }
        # write
        with rasterio.open(file_output, "w", **profile) as dst:
            dst.write(grid_output, id_band)
        return file_output

    @staticmethod
    def read_asc_metadata(file_input):
        """
        Reads metadata from an ASCII raster file.

        :param file_input: Path to the input ASCII file.
        :type file_input: str
        :return: A dictionary containing the metadata.
        :rtype: dict
        """
        with open(file_input) as f:
            def_lst = []
            for i, line in enumerate(f):
                if i >= 6:
                    break
                def_lst.append(line.strip())  # append each line to the list
        #
        # get metadata constructor loop
        meta_lbls = (
            "ncols",
            "nrows",
            "xllcorner",
            "yllcorner",
            "cellsize",
            "NODATA_value",
        )
        meta_format = ("int", "int", "float", "float", "float", "float")
        dc_metadata = dict()
        for i in range(6):
            lcl_lst = def_lst[i].split(" ")
            lcl_meta_str = lcl_lst[len(lcl_lst) - 1].split("\n")[0]
            if meta_format[i] == "int":
                dc_metadata[meta_lbls[i]] = int(lcl_meta_str)
            else:
                dc_metadata[meta_lbls[i]] = float(lcl_meta_str)
        # append missing params
        dc_metadata["crs"] = None
        dc_metadata["transform"] = None
        return dc_metadata

    @staticmethod
    def read_asc(file_input, dtype="float32", metadata=True):
        """
        Reads an ASCII raster file into a dictionary.

        :param file_input: Path to the input ASCII file.
        :type file_input: str
        :param dtype: Data type for the raster data. Default value = "float32"
        :type dtype: str
        :param metadata: Whether to read and include metadata from the ASCII file. Default value = True
        :type metadata: bool
        :return: A dictionary containing the raster data and optionally its metadata.
        :rtype: dict
        """
        # read
        with open(file_input) as f_file:
            lst_file = f_file.readlines()
        # Grid construction using numpy
        grd_data = np.genfromtxt(lst_file[6:], dtype=dtype)
        dc_raster = {"data": grd_data}
        if metadata:
            dc_raster["metadata"] = Raster.read_asc_metadata(file_input=file_input)
        return dc_raster

    @staticmethod
    def write_asc(grid_output, dc_metadata, file_output, dtype="float32"):
        """
        Writes a raster grid and its metadata to an ASCII file.

        :param grid_output: The raster data to write.
        :type grid_output: :class:`numpy.ndarray`
        :param dc_metadata: Dictionary containing the metadata for the ASCII file.
        :type dc_metadata: dict
        :param file_output: Path for the output ASCII file.
        :type file_output: str
        :param dtype: Data type for the raster data in the output file. Default value = "float32"
        :type dtype: str
        :return: The path of the generated output ASCII file.
        :rtype: str
        """
        # metadata construct heading
        meta_lbls = (
            "ncols",
            "nrows",
            "xllcorner",
            "yllcorner",
            "cellsize",
            "NODATA_value",
        )
        ndv = float(dc_metadata["NODATA_value"])
        exp_lst = list()
        for i in range(len(meta_lbls)):
            line = "{}    {}\n".format(meta_lbls[i], dc_metadata[meta_lbls[i]])
            exp_lst.append(line)

        # ----------------------------------
        # data constructor loop:
        grid_output_fix = Raster.apply_nodata(
            grid_input=grid_output, nodatavalue=ndv
        )  # insert nodatavalue
        # force dtype
        grid_output_fix2 = np.astype(grid_output_fix, dtype)
        for i in range(len(grid_output_fix2)):
            # replace np.nan to no data values
            lcl_row_sum = np.sum((np.isnan(grid_output_fix2[i])) * 1)
            if lcl_row_sum > 0:
                # print('Yeas')
                for j in range(len(grid_output_fix2[i])):
                    if np.isnan(grid_output_fix2[i][j]):
                        grid_output_fix2[i][j] = int(ndv)
            str_join = " " + " ".join(np.array(grid_output_fix2[i], dtype="str")) + "\n"
            exp_lst.append(str_join)

        fle = open(file_output, "w+")
        fle.writelines(exp_lst)
        fle.close()
        return file_output

    @staticmethod
    def apply_nodata(grid_input, nodatavalue=None):
        """
        Applies a nodata value to the input grid.

        :param grid_input: The input grid.
        :type grid_input: :class:`numpy.ndarray`
        :param nodatavalue: [optional] The nodata value to apply. Default value = None
        :type nodatavalue: int or float
        :return: The grid with the nodata value applied.
        :rtype: :class:`numpy.ndarray`
        """
        if nodatavalue is None:
            return grid_input  # Return original grid if no nodatavalue is provided
        else:
            if grid_input.dtype.kind in ["i", "u"]:
                # for integer grid
                return np.ma.filled(grid_input, fill_value=nodatavalue)
            else:
                # for floating point grid:
                return np.nan_to_num(grid_input, nan=nodatavalue)

    @staticmethod
    def make_square(grid_input):
        """
        Reshapes a 2D input grid into a square array, padding with NaNs or masked values if necessary.

        :param grid_input: The input 2D array (grid).
        :type grid_input: :class:`numpy.ndarray`
        :return: A square array containing the original grid, padded with NaNs or masked values.
        :rtype: :class:`numpy.ndarray`
        """
        # Determine the size for the squared array
        size = max(grid_input.shape)

        if grid_input.dtype.kind in ["i", "u"]:
            # for integer grid
            squared_arr = np.ma.masked_all((size, size))
        else:
            # for floating point grid:
            # Create a new array filled with NaN
            squared_arr = np.full((size, size), np.nan)
        # Place the original array (with masked values converted to NaN) in the upper left corner
        squared_arr[: grid_input.shape[0], : grid_input.shape[1]] = grid_input
        return squared_arr


class SciRaster(Raster):
    # todo [major docstring improvements]

    def __init__(self, name="MySciRaster", alias=None):
        # add new
        self.range_default = None
        super().__init__(name=name, alias=alias, dtype="float32")
        self.nodata_default = DC_NODATA[self.dtype]
        self._overwrite_nodata()

    def _set_view_specs(self):
        super()._set_view_specs()
        self.view_specs["range"] = self.range_default

    def _overwrite_nodata(self):
        self.raster_metadata["NODATA_value"] = self.nodata_default
        self.nodatavalue = self.nodata_default
        return None

    def set_raster_metadata(self, metadata):
        super().set_raster_metadata(metadata)
        self._overwrite_nodata()
        return None


class QualiRaster(Raster):
    """
    Basic qualitative raster map dataset.
    todo [docstring] -- examples
    """

    # Dunder methods
    # -------------------------------------------------------------------
    def __init__(self, name="QualiMap", dtype="uint8"):
        # prior setup
        self.path_csvfile = None
        self.table = None
        # call superior
        super().__init__(name=name, dtype=dtype)
        # overwrite
        self.cmap = "tab20"
        self.varname = "Unknown variable"
        self.varalias = "Var"
        self.description = "Unknown"
        self.units = "category ID"
        self.path_csvfile = None
        self.nodata_default = DC_NODATA[self.dtype]
        self._overwrite_nodata()
        # NOTE: view specs is set by setting table

    # Dunder methods
    # -------------------------------------------------------------------
    def _set_fields(self):
        # ------------ call super ----------- #
        super()._set_fields()
        # Attribute fields
        self.field_id = "id"
        self.field_area = "area"
        # ... continues in downstream objects ... #

    def _overwrite_nodata(self):
        self.raster_metadata["NODATA_value"] = self.nodata_default
        self.nodatavalue = self.nodata_default
        return None

    # Get methods
    # -------------------------------------------------------------------
    def get_metadata(self):
        """Get all metadata from base_object

        :return: metadata
        :rtype: dict
        """
        _dict = super().get_metadata()
        _dict["Path_CSV"] = self.path_csvfile
        return _dict

    def get_areas(self, inplace=False):
        """
        Get areas in map of each category in table.

        :param inplace: option to merge data with raster table
        :type inplace: bool, defaults to False
        :return: areas dataframe
        :rtype: :class:`pandas.DataFrame`
        """
        if self.table is None or self.data is None:
            return None
        else:
            # get unit area in meters
            _cell_size = self.cellsize
            if self.raster_metadata["crs"].linear_units == "degree":
                _cell_size = self.cellsize * 111111  # convert degrees to meters
            _n_unit_area = np.square(_cell_size)
            # get aux dataframe
            df_aux = self.table[
                [self.field_id, self.field_name, self.field_alias, self.field_color]
            ].copy()
            _lst_count = []
            # iterate categories
            for i in range(len(df_aux)):
                _n_id = df_aux[self.field_id].values[i]
                _n_count = np.sum(1 * (self.data == _n_id))
                _lst_count.append(_n_count)
            # set area fields
            lst_area_fields = []
            # Count
            s_count_field = "count"
            df_aux[s_count_field] = _lst_count
            lst_area_fields.append(s_count_field)

            # m2
            s_field = "{}_m2".format(self.field_area)
            lst_area_fields.append(s_field)
            df_aux[s_field] = df_aux[s_count_field].values * _n_unit_area

            # ha
            s_field = "{}_ha".format(self.field_area)
            lst_area_fields.append(s_field)
            df_aux[s_field] = df_aux[s_count_field].values * _n_unit_area / (100 * 100)

            # km2
            s_field = "{}_km2".format(self.field_area)
            lst_area_fields.append(s_field)
            df_aux[s_field] = (
                df_aux[s_count_field].values * _n_unit_area / (1000 * 1000)
            )

            # fraction
            s_field = "{}_f".format(self.field_area)
            lst_area_fields.append(s_field)
            df_aux[s_field] = df_aux[s_count_field] / df_aux[s_count_field].sum()

            # %
            s_field = "{}_%".format(self.field_area)
            lst_area_fields.append(s_field)
            df_aux[s_field] = 100 * df_aux[s_count_field] / df_aux[s_count_field].sum()

            # handle merge
            if inplace:
                for k in lst_area_fields:
                    self.table[k] = df_aux[k].values
                return None
            else:
                return df_aux

    def get_zonal_stats(self, raster_sample, merge=False, skip_count=False):
        """Get zonal stats from other raster map to sample.

        :param raster_sample: raster map to sample
        :type raster_sample: :class:`datasets.Raster`
        :param merge: option to merge data with raster table, defaults to False
        :type merge: bool
        :param skip_count: set True to skip count, defaults to False
        :type skip_count: bool
        :return: dataframe of zonal stats
        :rtype: :class:`pandas.DataFrame`
        """
        from plans.analyst import Univar

        # deploy dataframe
        df_aux1 = self.table.copy()
        self.clear_table()  # clean
        df_aux = self.table.copy()  # get copy
        df_aux = df_aux[
            [self.field_id, self.field_name, self.field_alias]
        ].copy()  # filter
        self.set_table(dataframe=df_aux1)  # restore uncleaned table

        # store copy of raster
        grid_raster = raster_sample.data
        varname = raster_sample.varname
        # collect statistics
        lst_stats = []
        for i in range(len(df_aux)):
            n_id = df_aux[self.field_id].values[i]
            # apply mask
            grid_aoi = 1 * (self.data == n_id)
            raster_sample.apply_aoi_mask(grid_aoi=grid_aoi, inplace=True)
            # get basic stats
            raster_uni = Univar(data=raster_sample.get_grid_data(), name=varname)
            df_stats = raster_uni.assess_basic_stats()
            lst_stats.append(df_stats.copy())
            # restore
            raster_sample.data = grid_raster

        # create empty fields
        lst_stats_field = []
        for k in df_stats["statistic"]:
            s_field = "{}_{}".format(varname, k)
            lst_stats_field.append(s_field)
            df_aux[s_field] = 0.0

        # fill values
        for i in range(len(df_aux)):
            df_aux.loc[i, lst_stats_field[0] : lst_stats_field[-1]] = lst_stats[i][
                "value"
            ].values

        # handle count
        if skip_count:
            df_aux = df_aux.drop(columns=["{}_count".format(varname)])
            lst_stats_field.remove("{}_count".format(varname))

        # handle merge
        if merge:
            for k in lst_stats_field:
                self.table[k] = df_aux[k].values

        return df_aux

    def get_aoi(self, by_value_id=None):
        """
        Get the AOI map from a specific value id (value is expected to exist in the raster)
        :param by_value_id: category id value
        :type by_value_id: int
        :return: AOI map
        :rtype: :class:`AOI`` object
        """
        from plans.datasets import AOI

        map_aoi = AOI(name="{} {}".format(self.varname, by_value_id))
        map_aoi.set_raster_metadata(metadata=self.raster_metadata)
        map_aoi.prj = self.prj
        # set grid
        self.insert_nodata()
        if by_value_id:
            map_aoi.set_data(grid=1 * (self.data == by_value_id))
        else:
            map_aoi.set_data(grid=1 * (self.data != self.nodatavalue))
        self.mask_nodata()
        return map_aoi

    # Set methods
    # -------------------------------------------------------------------
    def set_random_colors(self):
        """
        Set random colors to attribute table.
        """
        if self.table is None:
            pass
        else:
            self.table[self.field_color] = get_colors(
                size=len(self.table), cmap=self.cmap
            )
            # reaload table for reset viewspecs
            self.set_table(dataframe=self.table)
        return None

    def set_raster_metadata(self, metadata):
        super().set_raster_metadata(metadata)
        self._overwrite_nodata()
        return None

    def set_table(self, dataframe):
        """
        Set attributes dataframe from incoming :class:`pandas.DataFrame`.

        :param dataframe: incoming pandas dataframe
        :type dataframe: :class:`pandas.DataFrame`
        """
        self.table = dataframe_prepro(dataframe=dataframe.copy())
        self.table = self.table.sort_values(by=self.field_id).reset_index(drop=True)
        self.table = self.table.drop_duplicates(subset=self.field_id)
        # set view specs
        self._set_view_specs()
        return None

    # Data methods
    # -------------------------------------------------------------------
    def load_data(self, file_data, file_table=None, file_prj=None, id_band=1):
        """
        Load data from files to the raster object.

        :param file_data: The path to the raster file.
        :type file_data: str
        :param file_table: path to table file
        :type file_table: str
        :param file_prj: The path to the '.prj' projection file. If not provided, an attempt is made to use the same path and name as the ``.asc`` file with the '.prj' extension.
        :type file_prj: str
        :param id_band: Band id to read for GeoTIFF. Default value = 1
        :type id_band: int


        """
        super().load_data(file_data=file_data, file_prj=file_prj, id_band=id_band)
        self._overwrite_nodata()
        self.reset_nodata(new_nodata=self.nodata_default, ensure=False)
        if file_table is not None:
            self.load_table(file_table=file_table)
        self.update()
        return None

    def load_table(self, file_table):
        """
        Load attributes dataframe from table file.

        :param file_table: path to to file
        :type file_table: str
        """
        self.path_csvfile = file_table
        # read raw file
        df_aux = pd.read_csv(file_table, sep=";")
        # set to self
        self.set_table(dataframe=df_aux)
        return None

    def export(self, folder, filename=None):
        """
        Export raster sample

        :param folder: path to folder,
        :type folder: str
        :param filename: string of file without extension, defaults to None
        :type filename: str


        """
        super().export(folder=folder, filename=filename)
        self.export_table(folder=folder, filename=filename)
        return None

    def export_table(self, folder, filename=None):
        """
        Export table file.

        :param folder: path to folde
        :type folder: str
        :param filename: string of file without extension
        :type filename: str
        :return: full file name (path to and extension) string
        :rtype: str
        """
        if filename is None:
            filename = self.name
        flenm = folder + "/" + filename + self.file_csv_ext
        self.table.to_csv(flenm, sep=self.file_csv_sep, index=False)
        return flenm

    def clear_table(self):
        """
        Clear the unfound values in the map from the table.
        """
        if self.data is None:
            pass
        else:
            # found values:
            lst_ids = np.unique(self.data)
            # filter dataframe
            filtered_df = self.table[self.table[self.field_id].isin(lst_ids)]
            # reset table
            self.set_table(dataframe=filtered_df.reset_index(drop=True))
        return None

    def rebase_grid(self, base_raster, inplace=False):
        """
        This method calls the `rebase_grid` method of the superclass to perform
        the grid rebasement using the "nearest" interpolation method.

        :param base_raster: The raster object to rebase against.
        :type base_raster: :class:`Raster`
        :param inplace: If True, the operation is performed in-place. Default value = False
        :type inplace: bool
        :return: The rebased object.
        :rtype: :class:`Raster`
        """
        out = super().rebase_grid(base_raster, inplace, method="nearest")
        return out

    def reclassify(self, dict_ids, df_new_table, talk=False):
        """
        Reclassify QualiRaster Ids in grid and table

        :param dict_ids: dictionary to map from "Old_Id" to "New_id"
        :type dict_ids: dict
        :param df_new_table: new table for QualiRaster
        :type df_new_table: :class:`pandas.DataFrame`
        :param talk: option for printing messages
        :type talk: bool


        """
        grid_new = self.data.copy()
        for i in range(len(dict_ids["Old_Id"])):
            n_old_id = dict_ids["Old_Id"][i]
            n_new_id = dict_ids["New_Id"][i]
            if talk:
                print(">> reclassify Ids from {} to {}".format(n_old_id, n_new_id))
            grid_new = (grid_new * (grid_new != n_old_id)) + (
                n_new_id * (grid_new == n_old_id)
            )
        # set new grid
        self.set_data(grid=grid_new)
        # reset table
        self.set_table(dataframe=df_new_table)
        return None

    def apply_values(self, table_field):
        new_grid = geo.convert(
            array=self.data,
            old_values=self.table[self.field_id].values,
            new_values=self.table[table_field].values,
        )
        return new_grid

    # View methods
    # -------------------------------------------------------------------
    def _plot(self, fig, gs, specs):
        """
        Generates a plot visualizing the spatial data and its area distribution.

        This method creates a figure with a map of the spatial data and a horizontal bar chart
        showing the percentage area of each unique class. It can aggregate smaller classes
        into an "others" category and displays raster metadata.

        :param fig: The matplotlib figure object.
        :type fig: :class:`matplotlib.figure.Figure`
        :param gs: The matplotlib gridspec object for arranging subplots.
        :type gs: :class:`matplotlib.gridspec.GridSpec`
        :param specs: A dictionary containing plotting specifications and options.
        :type specs: dict
        :return: The modified matplotlib figure object with the plots.
        :rtype: :class:`matplotlib.figure.Figure`
        """

        # todo [DRY] most of this can be run on Univar -- make static method?
        import matplotlib.ticker as mticker

        # from matplotlib.ticker import PercentFormatter  # Import PercentFormatter
        formatter = mticker.ScalarFormatter(useOffset=False, useMathText=False)
        formatter.set_scientific(False)  # Ensure scientific notation is off

        def _get_max(std_values, data):
            data_max = np.max(data)
            closest_max_index = np.argmin(np.abs(np.array(std_values) - data_max))
            _id = closest_max_index + 1
            if _id >= len(std_values):
                _id = len(std_values) - 1
            return std_values[_id]

        def _plot_mean(axe, xmin, xmax):
            axe.hlines(
                y=y_mu,
                xmin=xmin,
                xmax=xmax,
                colors="red",
            )
            axe.annotate(
                r" $\mu$ = {}".format(round(y_mu, 2)),
                xy=(xmin, y_mu),
                xytext=(1, 3),
                textcoords="offset points",
                color="red",
            )

        def _categorize_and_limit(df, M):
            """
            Sorts a DataFrame by 'count' and aggregates rows beyond a limit M into an 'others' category.
            It now expects 'id' instead of 'class' and 'name' instead of 'category'.
            Includes 'color' and 'alias' fields, with specific values for the 'others' category.

            Args:
                df (pd.DataFrame): The input DataFrame with 'id', 'name', 'count', 'color', and 'alias' columns.
                M (int): The number of top rows to keep.

            Returns:
                pd.DataFrame: A new DataFrame with the top M rows and an aggregated 'others' row.
            """
            # Sort the DataFrame by 'count' in descending order
            df_sorted = df.sort_values(by="count", ascending=False)

            # Select the top M rows
            df_top_M = df_sorted.head(M)

            # Aggregate the remaining rows into an 'others' category
            df_others = df_sorted.iloc[
                M:
            ].copy()  # .copy() to avoid SettingWithCopyWarning

            # Create a dictionary for the 'others' aggregated row
            agg_field1 = f"{self.field_area}_f"
            agg_field2 = f"{self.field_area}_ha"
            agg_field3 = f"{self.field_area}_km2"
            agg_field4 = f"{self.field_area}_m2"
            agg_field5 = f"{self.field_area}_%"
            agg_field6 = "count"

            others_data = {
                self.field_id: np.nan,
                self.field_name: "others",  # 'name' instead of 'category'
                self.field_alias: "Etc",  # Specific alias for 'others'
                self.field_color: "black",  # Specific color for 'others'
                agg_field1: df_others[agg_field1].sum(),
                agg_field2: df_others[agg_field2].sum(),
                agg_field3: df_others[agg_field3].sum(),
                agg_field4: df_others[agg_field4].sum(),
                agg_field5: df_others[agg_field5].sum(),
                agg_field6: df_others[agg_field6].sum(),
            }

            # Convert the dictionary to a DataFrame row
            df_others_aggregated = pd.DataFrame([others_data])

            # Concatenate the top M rows with the 'others' category
            df_final = pd.concat([df_top_M, df_others_aggregated], ignore_index=True)

            return df_final

        ylim = specs["range"]

        # ---------- preable ---------
        df_areas = self.get_areas()

        # cut off zeros
        if specs["cutoff"]:
            df_areas = df_areas.query("count > 0")

        total_area = df_areas["{}_{}".format(self.field_area, specs["area_unit"])].sum()
        n_len = len(df_areas)
        n_max = 14

        # handle variations
        if n_len >= specs["max_classes"] + 1:
            df_areas = _categorize_and_limit(df=df_areas, M=specs["max_classes"])
        elif n_len < 10 and n_len >= 6:
            n_max = 10
        elif n_len < 6:
            n_max = 6

        # setup dataframe
        df_areas.sort_values(by="count", ascending=True, inplace=True)
        df_areas.reset_index(drop=True, inplace=True)

        # print(df_areas.to_string())

        # ------------ setup axes ------------
        ax1 = fig.add_subplot(gs[2:14, 0:12])

        ax2 = fig.add_subplot(gs[2:n_max, 18:23])

        if specs["title"] is not None:
            plt.suptitle(specs["title"], fontsize=9)

        # ------------ map plot ------------
        # handle zoom window
        i_min = 0
        i_max = len(self.data)
        j_min = 0
        j_max = len(self.data[0])
        if specs["zoom_window"] is not None:
            i_min = specs["zoom_window"]["i_min"]
            i_max = specs["zoom_window"]["i_max"]
            j_min = specs["zoom_window"]["j_min"]
            j_max = specs["zoom_window"]["j_max"]
        grid_show = self.data[i_min:i_max, j_min:j_max]
        grid_show_squared = Raster.make_square(grid_input=grid_show)
        im = ax1.imshow(
            grid_show_squared,
            cmap=specs["cmap"],
            vmin=ylim[0],
            vmax=ylim[1],
            interpolation="none",
            # extent=self.get_extent(),
            aspect="equal",
            origin="upper",
        )
        # todo the extent issue must be settled
        ax1.set_autoscale_on(False)  # Prevent auto-scaling which might add padding

        # plot helper geometry
        helper_geometry = specs["geometry"]
        if helper_geometry is not None:
            helper_geometry.plot(ax=ax1, color="none", edgecolor="k")
        if specs["subtitle_map"] is not None:
            ax1.set_title(specs["subtitle_map"], loc="left")
        # handle tick labels
        ax1.yaxis.set_major_formatter(formatter)
        ax1.xaxis.set_major_formatter(formatter)
        if specs["grid_map"]:
            ax1.grid(visible=specs["grid_map"])
        else:
            ax1.axis("off")

        # ------------ areas plot ------------
        n_w_legend = 0.1

        s_field = self.field_name
        if specs["use_alias"]:
            s_field = self.field_alias
        ax2.barh(
            df_areas[s_field],
            -n_w_legend,
            color=df_areas[self.field_color],
            edgecolor="k",
            linewidth=0.16 * viewer.MM_TO_PT,
            zorder=2,
        )
        ax2.barh(
            df_areas[s_field],
            df_areas[self.field_area + "_f"],
            color=specs["color"],
            zorder=1,
        )
        # Add value labels on each bar
        for index, value in enumerate(df_areas[self.field_area + "_f"].values):
            plt.text(
                value + 0.05,
                index,
                "{:.1f}%".format(value * 100),
                ha="left",
                va="center",
                fontfamily="Arial",
                fontsize=6,
            )  # Add text label: (x, y, text)
        if specs["subtitle_areas"] is not None:
            ax2.set_title(specs["subtitle_areas"], loc="left")
        dc_units = {
            "km2": "km$^2$",
            "m2": "m$^2$",
            "ha": "ha",
        }
        total_area = df_areas["{}_{}".format(self.field_area, specs["area_unit"])].sum()
        ax2.set_xlabel(
            "{}: {:.1f} {}".format(
                specs["total_area"], total_area, dc_units[specs["area_unit"]]
            )
        )
        ax2.set_xlim(-n_w_legend, 1)
        ax2.set_xticks([0, 0.25, 0.5, 0.75, 1])
        ax2.xaxis.set_major_formatter(mticker.PercentFormatter(1))

        fig = Raster.plot_metadata(
            fig=fig, metadata=self.raster_metadata, x=0.02, y=0.1
        )
        return fig

    def _set_view_specs(self):
        """
        Get default view specs


        """
        # handle if there is no table
        if self.table is None:
            pass
        else:
            from matplotlib.colors import ListedColormap

            # handle no color field in table:
            if self.field_color in self.table.columns:
                pass
            else:
                self.set_random_colors()

            # hack for non-continuous ids:
            _all_ids = np.arange(0, self.table[self.field_id].max() + 1)
            _lst_colors = []
            for i in range(0, len(_all_ids)):
                _df = self.table.query("{} >= {}".format(self.field_id, i)).copy()
                _color = _df[self.field_color].values[0]
                _lst_colors.append(_color)

            # setup
            super()._set_view_specs()
            self.view_specs.update(
                {
                    "cmap": ListedColormap(_lst_colors),
                    "color": "tab:gray",
                    "use_alias": False,
                    "cutoff": True,
                    "max_classes": 15,
                    "range": (0, self.table[self.field_id].max()),
                    "subtitle_areas": "Aereal ratios",
                    "area_unit": "km2",
                    "total_area": "Total area",
                }
            )

        return None

    def view(self, show=True, return_fig=False, helper_geometry=None):
        """
        Displays or returns a visualization of the spatial data and its area distribution.

        This method orchestrates the plotting process by setting up figure specifications,
        calling the internal plotting function (`_plot`), and then either displaying
        or saving the generated figure.

        :param show: If True, the plot is displayed. Default value = True
        :type show: bool
        :param return_fig: If True, the matplotlib figure object is returned. Default value = False
        :type return_fig: bool
        :param helper_geometry: [optional] An optional geometry object to overlay on the map.
        :type helper_geometry: object
        :return: The matplotlib figure object if `return_fig` is True, otherwise None.
        :rtype: :class:`matplotlib.figure.Figure` or None
        """
        # handle specs
        specs = self.view_specs.copy()
        specs_aux = {
            "ncols": 24,
            "nrows": 16,
            "width": viewer.FIG_SIZES["M"]["w"],
            "height": viewer.FIG_SIZES["M"]["h"],
        }
        # update
        specs.update(specs_aux)
        # update gridspecs
        specs.update(viewer.GRID_SPECS)
        # update geometry
        specs["geometry"] = helper_geometry

        # -------------- BUILD --------------
        fig, gs = viewer.build_fig(specs=specs)

        # -------------- PLOT --------------
        fig = self._plot(fig=fig, gs=gs, specs=specs)

        # -------------- SHIP --------------
        # create path
        file_path = "{}/{}.{}".format(
            specs["folder"], specs["filename"], specs["fig_format"]
        )
        if return_fig:
            return fig
        else:
            viewer.ship_fig(fig=fig, show=show, file_output=file_path, dpi=specs["dpi"])


class QualiHard(QualiRaster):
    """
    A Quali-Hard is a hard-coded qualitative map (that is, the table is pre-set)
    todo [docstring] -- examples
    """

    def __init__(self, name="qualihard"):
        super().__init__(name, dtype="uint8")
        self.varname = "QualiRasterHard"
        self.varalias = "QRH"
        self.description = "Preset Classes"
        self.units = "classes ID"
        self.set_table(dataframe=self.get_table())

    def get_table(self):
        """
        Retrieves a DataFrame representing a classification table.

        :return: A DataFrame with classification data.
        :rtype: :class:`pandas.DataFrame`
        """
        df_aux = pd.DataFrame(
            {
                self.field_id: [1, 2, 3],
                self.field_name: ["Class A", "Class B", "Class C"],
                self.field_alias: ["A", "B", "C"],
                self.field_color: ["red", "green", "blue"],
            }
        )
        return df_aux

    def load_data(self, file_data, file_prj=None, id_band=1, file_table=None):
        """
        Load data from file to the raster object.

        :param file_data: The path to the raster file.
        :type file_data: str
        :param file_prj: The path to the '.prj' projection file. If not provided, an attempt is made to use the same path and name as the ``.asc`` file with the '.prj' extension.
        :type file_prj: str
        :param id_band: Band id to read for GeoTIFF. Default value = 1
        :type id_band: int


        """
        # handle extension
        s_extension = os.path.basename(file_data).split(".")[-1]
        if s_extension == "asc":
            self.load_asc(file_input=file_data)
        else:
            self.load_tif(file_input=file_data, id_band=id_band)
        self.load_prj(file_input=file_prj)
        self.update()
        return None


class Zones(QualiRaster):
    """
    Zones map dataset is a QualiRaster designed to handle large volume of
    positive integer numbers (ids of zones)
    todo [docstring] -- examples
    """

    def __init__(self, name="ZonesMap"):
        super().__init__(name, dtype="uint32")
        self.varname = "Zone"
        self.varalias = "ZN"
        self.description = "Ids map of zones"
        self.units = "zones ID"
        self.table = None

    def compute_table(self):
        """
        Computes an internal table summarizing unique values in the spatial data,
        assigns aliases, names, and sets up viewing specifications.
        """
        if self.data is None:
            self.table = None
        else:
            self.insert_nodata()
            # get unique values
            vct_unique = np.unique(self.data)
            # reapply mask
            self.mask_nodata()
            # set table
            self.table = pd.DataFrame(
                {
                    self.field_id: vct_unique,
                    self.field_alias: [
                        "{}{}".format(self.varalias, vct_unique[i])
                        for i in range(len(vct_unique))
                    ],
                    self.field_name: [
                        "{} {}".format(self.varname, vct_unique[i])
                        for i in range(len(vct_unique))
                    ],
                }
            )
            self.table = self.table.drop(
                self.table[
                    self.table[self.field_id] == self.raster_metadata["NODATA_value"]
                ].index
            )
            self.table[self.field_id] = self.table[self.field_id].astype(int)
            self.table = self.table.sort_values(by=self.field_id)
            self.table = self.table.reset_index(drop=True)
            self.set_random_colors()
            # set view specs
            self._set_view_specs()
            # fix some view_specs:
            self.view_specs["b_xlabel"] = "zones ID"
            del vct_unique
            return None

    def set_data(self, grid):
        """
        Sets the spatial data for the object and recomputes the internal table.

        :param grid: The input grid data.
        :type grid: :class:`numpy.ndarray`


        """
        super().set_data(grid)
        self.compute_table()
        return None

    def load_data(self, asc_file, prj_file):
        # todo [refactor] -- this is deprecated -- use load tifs
        """
        Load data from files to raster

        :param asc_file: path to raster file
        :type asc_file: str
        :param prj_file: path to projection file
        :type prj_file: str


        """
        self.load_asc(file=asc_file)
        self.load_prj(file=prj_file)
        return None

    def get_aoi(self, zone_id):
        """
        Get the AOI map from a zone id

        :param zone_id: number of zone ID
        :type zone_id: int
        :return: AOI map
        :rtype: :class:`AOI`` object
        """
        from plans.datasets.spatial import AOI

        map_aoi = AOI(name="{} {}".format(self.varname, zone_id))
        map_aoi.set_raster_metadata(metadata=self.raster_metadata)
        map_aoi.prj = self.prj
        # set grid
        self.insert_nodata()
        map_aoi.set_data(grid=1 * (self.data == zone_id))
        self.mask_nodata()
        return map_aoi

    def view(
        self,
        show=True,
        folder="./output",
        filename=None,
        specs=None,
        dpi=150,
        fig_format="jpg",
    ):
        # todo [refactor] -- DRY
        """
        Plot a basic pannel of raster map.

        :param show: boolean to show plot instead of saving, defaults to False
        :type show: bool
        :param folder: path to output folder, defaults to ``./output``
        :type folder: str
        :param filename: name of file, defaults to None
        :type filename: str
        :param specs: specifications dictionary, defaults to None
        :type specs: dict
        :param dpi: image resolution, defaults to 96
        :type dpi: int
        :param fig_format: image fig_format (ex: png or jpg). Default jpg
        :type fig_format: str
        """
        # set Raster map for plotting
        map_zones_aux = Raster(name=self.name)
        # set up
        map_zones_aux.varname = self.varname
        map_zones_aux.varalias = self.varalias
        map_zones_aux.units = self.units
        map_zones_aux.set_raster_metadata(metadata=self.raster_metadata)
        map_zones_aux.prj = self.prj
        map_zones_aux.cmap = "tab20"
        map_zones_aux.update()

        # grid setup
        self.insert_nodata()
        map_zones_aux.set_data(grid=self.data)
        self.mask_nodata()
        map_zones_aux._set_view_specs()
        map_zones_aux.view_specs["vmin"] = self.table[self.field_id].min()
        map_zones_aux.view_specs["vmax"] = self.table[self.field_id].max()
        map_zones_aux.view_specs["folder"] = folder
        map_zones_aux.view_specs["filename"] = filename
        map_zones_aux.view_specs["dpi"] = dpi
        map_zones_aux.view_specs["fig_format"] = fig_format
        # update extra view specs:
        for k in self.view_specs:
            map_zones_aux.view_specs[k] = self.view_specs[k]
        # call view
        map_zones_aux.view(
            accum=False,
            show=show,
        )
        del map_zones_aux
        return None


# Core spatial classes -- collections
# -----------------------------------------------------------------------


class RasterCollection(Collection):
    """
    The raster collection base dataset.
    This data strucute is designed for holding and comparing :class:`Raster`` objects.
    """

    def __init__(self, name="myRasterCollection"):
        """
        Deploy the raster collection data structure.

        :param name: name of raster collection
        :type name: str
        """
        obj_aux = Raster
        super().__init__(base_object=obj_aux, name=name)
        # set up date fields and special attributes
        self.catalog[self.field_datetime] = pd.to_datetime(
            self.catalog[self.field_datetime]
        )
        self.short_catalog_ls = [
            "name",
            "alias",
            "datetime",
            "size",
            "resolution",
            "rows",
            "columns",
            "xll",
            "yll",
            "nodata_value",
        ]

    def _set_fields(self):
        """
        Set fields names.
        Expected to increment superior methods.
        """
        # ------------ call super ----------- #
        super()._set_fields()

        # Attribute fields
        self.field_datetime = Raster().field_datetime
        # ... continues in downstream objects ... #

    def load_data(
        self,
        name,
        file_data,
        file_prj=None,
        varname=None,
        varalias=None,
        units=None,
        datetime=None,
        dtype="float32",
        skip_grid=False,
    ):
        """
        Load a :class:`Raster`` base_object from a raster file.

        :param name: :class:`Raster.name`` name attribute
        :type name: str
        :param file_data: path to raster file
        :type file_data: str
        :param varname: :class:`Raster.varname`` variable name attribute, defaults to None
        :type varname: str
        :param varalias: :class:`Raster.varalias`` variable alias attribute, defaults to None
        :type varalias: str
        :param units: :class:`Raster.units`` units attribute, defaults to None
        :type units: str
        :param datetime: :class:`Raster.date`` date attribute, defaults to None
        :type datetime: str
        :param skip_grid: option for loading only the metadata
        :type skip_grid: bool
        """
        # create raster
        rst_aux = Raster(name=name, dtype=dtype)

        # set attributes
        rst_aux.varname = varname
        rst_aux.varalias = varalias
        rst_aux.units = units
        rst_aux.datetime = datetime

        # load projection file
        rst_aux.load_prj(file_input=file_prj)

        # read data file
        if skip_grid:
            rst_aux.load_metadata(file_data=file_data)
        else:
            rst_aux.load_data(file_data=file_data)

        # append to collection
        self.append(new_object=rst_aux)

        # delete aux
        del rst_aux

        return None

    # todo [develop] -- optimize
    # todo [develop] -- parallel loading
    def load_folder(
        self,
        folder,
        name_pattern,
        is_series=False,
        file_table=None,
        verbose=False,
        file_format="tif",
        logger=None,
    ):
        """
        Load all rasters from a folder by following a name pattern.

        :param folder: path to folder
        :type folder: str
        :param name_pattern: name pattern. example map_*
        :type name_pattern: str
        :param is_series: flag to handle datetime
        :type is_series: bool
        :param file_table: file path to qualiraster table
        :type file_table: str or Path
        :param verbose: option for printing messages
        :type verbose: bool
        :param file_format: file extension.
        :type file_format: str
        """

        def print_msg(msg, logger, verbose=True):
            if verbose:
                if logger is None:
                    print(msg)
                else:
                    logger.info(msg)

        # list files
        lst_maps = glob.glob("{}/{}.{}".format(folder, name_pattern, file_format))
        lst_prjs = glob.glob("{}/{}.prj".format(folder, name_pattern))

        msg = "loading folder: {} files".format(len(lst_maps))
        print_msg(msg, logger, verbose)

        # enter serial loop
        # -------------------------------------------------------
        n = 1
        for i in range(len(lst_maps)):

            map_file = lst_maps[i]

            # handle missing projection files
            if len(lst_prjs) > 0:
                prj_file = lst_prjs[i]
            else:
                prj_file = None

            # get name
            s_name = os.path.basename(map_file).split(".")[0]

            # load file

            # handle if is a series map
            if is_series:
                # get local datetime assuming is ar
                s_date_map = map_file.split("_")[-1].split(".")[0]

                if file_table is None:
                    # simple raster series
                    self.load_data(
                        name=s_name,
                        datetime=s_date_map,
                        file_data=map_file,
                        prj_file=prj_file,
                    )
                else:
                    # quali raster series
                    self.load_data(
                        name=s_name,
                        datetime=s_date_map,
                        file_data=map_file,
                        file_table=file_table,
                        file_prj=prj_file,
                    )
            else:
                if file_table is None:
                    # simple raster collection
                    self.load_data(
                        name=s_name,
                        file_data=map_file,
                        prj_file=prj_file,
                    )
                else:
                    # quali raster collection
                    self.load_data(
                        name=s_name,
                        file_data=map_file,
                        prj_file=prj_file,
                        file_table=file_table,
                    )

            # messages
            p = 100 * (n / len(lst_maps))
            msg = "[{:7.2f}%] loaded: {}.{}".format(p, s_name, file_format)
            print_msg(msg, logger, verbose)
            n = n + 1

        self.update(details=True)
        return None

    def is_same_grid(self):
        """
        Checks if all datasets in the catalog have the same grid dimensions (number of columns and rows).

        :return: True if all datasets have the same grid dimensions, False otherwise.
        :rtype: bool
        """
        u_cols = len(self.catalog["ncols"].unique())
        u_rows = len(self.catalog["nrows"].unique())
        if u_cols == 1 and u_rows == 1:
            return True
        else:
            return False

    def reduce(
        self,
        reducer_func,
        reduction_name,
        extra_arg=None,
        skip_nan=False,
        talk=False,
    ):
        """
        This method reduces the collection by applying a numpy broadcasting function (example: np.mean)

        :param reducer_func: reducer numpy function (example: np.mean)
        :type reducer_func: numpy function
        :param reduction_name: name for the output raster
        :type reduction_name: str
        :param extra_arg: extra argument for function (example: np.percentiles) - Default: None
        :type extra_arg: any
        :param skip_nan: Option for skipping NaN values in map
        :type skip_nan: bool
        :param talk: option for printing messages
        :type talk: bool
        :return: raster object based on the first object found in the collection
        :rtype: :class:`Raster`
        """
        import copy

        # return None if there is different grids
        if self.is_same_grid():
            # get shape parameters
            n = len(self.catalog)
            _first = self.catalog["Name"].values[0]
            n_flat = (
                self.collection[_first].data.shape[0]
                * self.collection[_first].data.shape[1]
            )

            # create the merged grid
            grd_merged = np.zeros(shape=(n, n_flat))
            # insert the flat arrays
            for i in range(n):
                _name = self.catalog[self.field_name].values[i]
                _vct_flat = self.collection[_name].data.flatten()
                grd_merged[i] = _vct_flat
            # transpose
            grd_merged_T = grd_merged.transpose()

            # setup stats vector
            vct_stats = np.zeros(n_flat)
            # fill vector
            for i in range(n_flat):
                _vct = grd_merged_T[i]
                # remove NaN
                if skip_nan:
                    _vct = _vct[~np.isnan(_vct)]
                    # handle void vector
                    if len(_vct) == 0:
                        _vct = np.nan
                if extra_arg is None:
                    vct_stats[i] = reducer_func(_vct)
                else:
                    vct_stats[i] = reducer_func(_vct, extra_arg)

            # reshape
            grd_stats = np.reshape(
                a=vct_stats, newshape=self.collection[_first].data.shape
            )
            # return set up
            output_raster = copy.deepcopy(self.collection[_first])
            output_raster.set_data(grd_stats)
            output_raster.name = reduction_name
            return output_raster
        else:
            if talk:
                print("Warning: different grids found")
            return None

    def to_mean(self, skip_nan=False, talk=False):
        """
        Reduce Collection to the Mean raster

        :param skip_nan: Option for skipping NaN values in map
        :type skip_nan: bool
        :param talk: option for printing messages
        :type talk: bool
        :return: raster object based on the first object found in the collection
        :rtype: :class:`Raster`
        """
        output_raster = self.reduce(
            reducer_func=np.mean,
            reduction_name="{} Mean".format(self.name),
            skip_nan=skip_nan,
            talk=talk,
        )
        return output_raster

    def to_sd(self, skip_nan=False, talk=False):
        """
        Reduce Collection to the Standard Deviation raster

        :param skip_nan: Option for skipping NaN values in map
        :type skip_nan: bool
        :param talk: option for printing messages
        :type talk: bool
        :return: raster object based on the first object found in the collection
        :rtype: :class:`Raster`
        """
        output_raster = self.reduce(
            reducer_func=np.std,
            reduction_name="{} SD".format(self.name),
            skip_nan=skip_nan,
            talk=talk,
        )
        return output_raster

    def to_min(self, skip_nan=False, talk=False):
        """
        Reduce Collection to the Min raster

        :param skip_nan: Option for skipping NaN values in map
        :type skip_nan: bool
        :param talk: option for printing messages
        :type talk: bool
        :return: raster object based on the first object found in the collection
        :rtype: :class:`Raster`
        """
        output_raster = self.reduce(
            reducer_func=np.min,
            reduction_name="{} Min".format(self.name),
            skip_nan=skip_nan,
            talk=talk,
        )
        return output_raster

    def to_max(self, skip_nan=False, talk=False):
        """
        Reduce Collection to the Max raster

        :param skip_nan: Option for skipping NaN values in map
        :type skip_nan: bool
        :param talk: option for printing messages
        :type talk: bool
        :return: raster object based on the first object found in the collection
        :rtype: :class:`Raster`
        """
        output_raster = self.reduce(
            reducer_func=np.max,
            reduction_name="{} Max".format(self.name),
            skip_nan=skip_nan,
            talk=talk,
        )
        return output_raster

    def to_sum(self, skip_nan=False, talk=False):
        """
        Reduce Collection to the Sum raster

        :param skip_nan: Option for skipping NaN values in map
        :type skip_nan: bool
        :param talk: option for printing messages
        :type talk: bool
        :return: raster object based on the first object found in the collection
        :rtype: :class:`Raster`
        """
        output_raster = self.reduce(
            reducer_func=np.sum,
            reduction_name="{} Sum".format(self.name),
            skip_nan=skip_nan,
            talk=talk,
        )
        return output_raster

    def to_percentile(self, percentile, skip_nan=False, talk=False):
        """
        Reduce Collection to the Nth Percentile raster

        :param percentile: Nth percentile (from 0 to 100)
        :type percentile: float
        :param skip_nan: Option for skipping NaN values in map
        :type skip_nan: bool
        :param talk: option for printing messages
        :type talk: bool
        :return: raster object based on the first object found in the collection
        :rtype: :class:`Raster`
        """
        output_raster = self.reduce(
            reducer_func=np.percentile,
            reduction_name="{} {}th percentile".format(self.name, str(percentile)),
            skip_nan=skip_nan,
            talk=talk,
            extra_arg=percentile,
        )
        return output_raster

    def to_median(self, skip_nan=False, talk=False):
        """
        Reduce Collection to the Median raster

        :param skip_nan: Option for skipping NaN values in map
        :type skip_nan: bool
        :param talk: option for printing messages
        :type talk: bool
        :return: raster object based on the first object found in the collection
        :rtype: :class:`Raster`
        """
        output_raster = self.reduce(
            reducer_func=np.median,
            reduction_name="{} Median".format(self.name),
            skip_nan=skip_nan,
            talk=talk,
        )
        return output_raster

    def get_collection_stats(self):
        """
        Get basic statistics from collection.

        :return: statistics sample
        :rtype: :class:`pandas.DataFrame`
        """
        # deploy dataframe
        df_aux = self.catalog[[self.field_name]].copy()
        lst_stats = []
        for i in range(len(self.catalog)):
            s_name = self.catalog[self.field_name].values[i]
            df_stats = self.collection[s_name].get_stats_df()
            lst_stats.append(df_stats.copy())

        # deploy fields
        for k in df_stats["statistic"]:
            df_aux[k] = 0.0

        # fill values
        for i in range(len(df_aux)):
            df_aux.loc[i, "count":"max"] = lst_stats[i]["value"].values

        # convert to integer
        df_aux["count"] = df_aux["count"].astype(dtype="uint32")

        return df_aux

    def get_views(
        self,
        show=False,
        folder="./output",
        dpi=300,
        fig_format="jpg",
        talk=False,
        specs=None,
        suffix=None,
    ):
        """
        Plot all basic pannel of raster maps in collection.

        :param show: boolean to show plot instead of saving,
        :type show: bool
        :param folder: path to output folder, defaults to ``./output``
        :type folder: str
        :param dpi: image resolution, defaults to 96
        :type dpi: int
        :param fig_format: image fig_format (ex: png or jpg). Default jpg
        :type fig_format: str
        :param talk: option for print messages
        :type talk: bool


        """

        # enter serial plot loop
        for k in self.collection:

            # get local raster
            rst_lcl = self.collection[k]

            # update incoming specs
            if specs is not None:
                rst_lcl.view_specs.update(specs)

            # setup hard viewspecs
            s_name = rst_lcl.name
            if suffix is not None:
                s_name = suffix + "_" + rst_lcl.name
            rst_lcl.view_specs["filename"] = s_name
            rst_lcl.view_specs["folder"] = folder
            rst_lcl.view_specs["dpi"] = dpi
            rst_lcl.view_specs["fig_format"] = fig_format

            # view
            if talk:
                print("plotting view of {}...".format(rst_lcl.name))
            rst_lcl.view(show=show)

        return None

    def view_bboxes(
        self,
        colors=None,
        datapoints=False,
        show=True,
        folder="./output",
        filename=None,
        dpi=150,
        fig_format="jpg",
    ):
        """
        View Bounding Boxes of Raster collection

        :param colors: list of colors for plotting. expected to be the same runsize of catalog
        :type colors: list
        :param datapoints: option to plot datapoints as well, defaults to False
        :type datapoints: bool
        :param show: option to show plot instead of saving, defaults to False
        :type show: bool
        :param folder: path to output folder, defaults to ``./output``
        :type folder: str
        :param filename: name of file, defaults to None
        :type filename: str
        :param dpi: image resolution, defaults to 96
        :type dpi: int
        :param fig_format: image fig_format (ex: png or jpg). Default jpg
        :type fig_format: str

        :rtype: none
        """
        fig = plt.figure(figsize=(5, 5))
        # get colors
        lst_colors = colors
        if colors is None:
            lst_colors = get_colors(size=len(self.catalog))
        # colect names and bboxes
        lst_x_values = list()
        lst_y_values = list()
        dct_bboxes = dict()
        dct_colors = dict()
        _c = 0
        for name in self.collection:
            dct_colors[name] = lst_colors[_c]
            lcl_bbox = self.collection[name].get_bbox()
            dct_bboxes[name] = lcl_bbox
            # append coordinates
            lst_x_values.append(lcl_bbox["xmin"])
            lst_x_values.append(lcl_bbox["xmax"])
            lst_y_values.append(lcl_bbox["ymin"])
            lst_y_values.append(lcl_bbox["ymax"])
            _c = _c + 1
        # get min and max
        n_xmin = np.min(lst_x_values)
        n_xmax = np.max(lst_x_values)
        n_ymin = np.min(lst_y_values)
        n_ymax = np.max(lst_y_values)
        # get ranges
        n_x_range = np.abs(n_xmax - n_xmin)
        n_y_range = np.abs(n_ymax - n_ymin)

        # plot loop
        for name in dct_bboxes:
            plt.scatter(
                dct_bboxes[name]["xmin"],
                dct_bboxes[name]["ymin"],
                marker="^",
                color=dct_colors[name],
            )
            if datapoints:
                df_dpoints = self.collection[name].get_grid_datapoints(drop_nan=False)
                plt.scatter(
                    df_dpoints["x"], df_dpoints["y"], color=dct_colors[name], marker="."
                )
            _w = dct_bboxes[name]["xmax"] - dct_bboxes[name]["xmin"]
            _h = dct_bboxes[name]["ymax"] - dct_bboxes[name]["ymin"]
            rect = plt.Rectangle(
                xy=(dct_bboxes[name]["xmin"], dct_bboxes[name]["ymin"]),
                width=_w,
                height=_h,
                alpha=0.5,
                label=name,
                color=dct_colors[name],
            )
            plt.gca().add_patch(rect)
        plt.ylim(n_ymin - (n_y_range / 3), n_ymax + (n_y_range / 3))
        plt.xlim(n_xmin - (n_x_range / 3), n_xmax + (n_x_range / 3))
        plt.gca().set_aspect("equal")
        plt.legend()

        # show or save
        if show:
            plt.show()
        else:
            if filename is None:
                filename = "bboxes"
            plt.savefig("{}/{}.{}".format(folder, filename, fig_format), dpi=dpi)
        plt.close(fig)
        return None

    def get_catalog(self, mode="full"):
        """
        Retrieves the data catalog in different modes.

        :param mode: The mode of the catalog to retrieve. Can be "full" for the complete catalog, "short" for a truncated version, or any other value to filter by a list `ls`. Default value = "full"
        :type mode: str
        :return: The requested data catalog.
        :rtype: :class:`pandas.DataFrame`
        """
        if mode == "full":
            return self.catalog
        elif mode == "short":
            return self.catalog[self.short_catalog_ls]
        else:
            return self.catalog[ls]


class QualiRasterCollection(RasterCollection):
    """
    The raster collection base dataset.

    This data strucute is designed for holding and comparing :class:`QualiRaster`` objects.
    """

    def __init__(self, name):
        """
        Deploy Qualitative Raster Series

        :param name: :class:`RasterSeries.name`` name attribute
        :type name: str
        :param varname: :class:`Raster.varname`` variable name attribute, defaults to None
        :type varname: str
        :param varalias: :class:`Raster.varalias`` variable alias attribute, defaults to None
        :type varalias: str
        """
        super().__init__(name=name)

    def load_data(self, name, file_data, file_table=None, prj_file=None):
        """
        Load a :class:`QualiRaster`` from file.

        :param name: :class:`Raster.name`` name attribute
        :type name: str
        :param file_data: path to raster file.
        :type file_data: str
        :param file_table: path to table file
        :type file_table: str
        :param prj_file: path to projection file
        :type prj_file: str

        """
        # create raster
        rst_aux = QualiRaster(name=name)

        # todo evaluate to include other attributes
        # read file
        rst_aux.load_data(file_data=file_data, file_table=file_table, prj_file=prj_file)

        # append to collection
        self.append(new_object=rst_aux)

        # delete aux
        del rst_aux
        return None


class RasterSeries(RasterCollection):
    """
    A :class:`RasterCollection`` where datetime matters and all maps in collections are
    expected to be the same variable, same projection and same grid.
    """

    def __init__(self, name, varname, varalias, units, dtype="float32"):
        """
        Deploy RasterSeries

        :param name: :class:`RasterSeries.name`` name attribute
        :type name: str
        :param varname: :class:`Raster.varname`` variable name attribute, defaults to None
        :type varname: str
        :param varalias: :class:`Raster.varalias`` variable alias attribute, defaults to None
        :type varalias: str
        :param units: :class:`Raster.units`` units attribute, defaults to None
        :type units: str
        """
        super().__init__(name=name)
        self.varname = varname
        self.varalias = varalias
        self.units = units
        self.dtype = dtype

    def load_data(
        self, name, datetime, file_data, prj_file=None, dtype="float32", skip_grid=False
    ):
        """
        Load a :class:`Raster`` object from raster file.

        :param name: :class:`Raster.name`` name attribute
        :type name: str
        :param datetime: :class:`Raster.date`` date attribute, defaults to None
        :type datetime: str
        :param file_data: path to raster file
        :type file_data: str
        :param prj_file: path to projection file
        :type prj_file: str
        :param skip_grid: option for loading only the metadata
        :type skip_grid: bool


        """
        super().load_data(
            name=name,
            file_data=file_data,
            file_prj=prj_file,
            varname=self.varname,
            varalias=self.varalias,
            units=self.units,
            datetime=datetime,
            dtype=dtype,
            skip_grid=skip_grid,
        )
        return None

    def load_folder(
        self,
        folder,
        name_pattern,
        file_table=None,
        verbose=False,
        file_format="tif",
        logger=None,
    ):
        super().load_folder(
            folder=folder,
            name_pattern=name_pattern,
            is_series=True,
            file_table=file_table,
            verbose=verbose,
            file_format=file_format,
            logger=logger,
        )
        return None

    def apply_aoi_masks(self, grid_aoi, inplace=False):
        """
        Batch method to apply AOI mask over all maps in collection

        :param grid_aoi: aoi grid
        :type grid_aoi: :class:`numpy.ndarray`
        :param inplace: overwrite the main grid if True, defaults to False
        :type inplace: bool


        """
        for name in self.collection:
            self.collection[name].apply_aoi_mask(grid_aoi=grid_aoi, inplace=inplace)
        return None

    def release_aoi_masks(self):
        """
        Batch method to release the AOI mask over all maps in collection



        """
        for name in self.collection:
            self.collection[name].release_aoi_mask()
        return None

    def rebase_grids(self, base_raster, talk=False):
        """
        Batch method for rebase all maps in collection

        :param base_raster: base raster for rebasing
        :type base_raster: :class:`datasets.Raster`
        :param talk: option for print messages
        :type talk: bool


        """
        if talk:
            print("rebase grids...")
        for name in self.collection:
            self.collection[name].rebase_grid(base_raster=base_raster, inplace=True)
        self.update(details=True)
        return None

    def get_series_stats(self):
        """
        Get the raster series statistics

        :return: dataframe of raster series statistics
        :rtype: :class:`pandas.DataFrame`
        """
        rst_aux = Raster()
        df_stats = self.get_collection_stats()
        df_series = pd.merge(
            self.catalog[[rst_aux.field_name, rst_aux.field_datetime]],
            df_stats,
            how="left",
            on=rst_aux.field_name,
        )
        return df_series

    def view_series_stats(
        self,
        statistic="mean",
        folder="./output",
        filename=None,
        specs=None,
        show=True,
        dpi=150,
        fig_format="jpg",
    ):
        """
        View raster series statistics

        :param statistic: statistc to view. Default mean
        :type statistic: str
        :param show: option to show plot instead of saving, defaults to False
        :type show: bool
        :param folder: path to output folder, defaults to ``./output``
        :type folder: str
        :param filename: name of file, defaults to None
        :type filename: str
        :param specs: specifications dictionary, defaults to None
        :type specs: dict
        :param dpi: image resolution, defaults to 96
        :type dpi: int
        :param fig_format: image fig_format (ex: png or jpg). Default jpg
        :type fig_format: str


        """
        df_series = self.get_series_stats()
        ts = DailySeries(
            name=self.name, varname="{}_{}".format(self.varname, statistic)
        )
        ts.set_data(
            dataframe=df_series, varfield=statistic, datefield=self.field_datetime
        )
        default_specs = {
            "title": "{} | {} {} series".format(self.name, self.varname, statistic),
            "ylabel": self.units,
        }
        if specs is None:
            specs = default_specs
        else:
            # overwrite incoming specs
            for k in default_specs:
                specs[k] = default_specs[k]
        ts.view(
            show=show,
            folder=folder,
            filename=filename,
            specs=specs,
            dpi=dpi,
            fig_format=fig_format,
        )
        return None


class QualiRasterSeries(RasterSeries):
    """
    A :class:`RasterSeries` where date matters and all maps in collections are
    expected to be :class:`QualiRaster`` with the same variable, same projection and same grid.
    """

    def __init__(self, name, varname, varalias, dtype="uint8"):
        """
        Deploy Qualitative Raster Series

        :param name: :class:`RasterSeries.name`` name attribute
        :type name: str
        :param varname: :class:`Raster.varname` variable name attribute, defaults to None
        :type varname: str
        :param varalias: :class:`Raster.varalias` variable alias attribute, defaults to None
        :type varalias: str
        """
        super().__init__(
            name=name, varname=varname, varalias=varalias, dtype=dtype, units="ID"
        )
        self.table = None

    def update_table(self, clear=True):
        """
        Update series table (attributes)

        :param clear: option for clear table from unfound values. default: True
        :type clear: bool

        """
        if len(self.catalog) == 0:
            pass
        else:
            for i in range(len(self.catalog)):
                _name = self.catalog[self.field_name].values[i]
                # clear table from unfound values
                if clear:
                    self.collection[_name].clear_table()
                # concat all tables
                if i == 0:
                    self.table = self.collection[_name].table.copy()
                else:
                    self.table = pd.concat(
                        [self.table, self.collection[_name].table.copy()]
                    )
        # clear from duplicates
        self.table = self.table.drop_duplicates(
            subset=QualiRaster().field_id, keep="last"
        )
        self.table = self.table.reset_index(drop=True)
        return None

    def append(self, raster):
        super().append(new_object=raster)
        self.update_table()
        return None

    def load_data(self, name, datetime, file_data, prj_file=None, table_file=None):
        """
        Load a :class:`QualiRaster` base_object from raster file.

        :param name: :class:`Raster.name` name attribute
        :type name: str
        :param datetime: :class:`Raster.date` date attribute
        :type datetime: str
        :param file_data: path to raster file
        :type file_data: str
        :param prj_file: path to projection file
        :type prj_file: str
        :param table_file: path to ``.txt`` table file
        :type table_file: str
        """
        # create raster
        rst_aux = QualiRaster(name=name)
        # set attributes
        rst_aux.datetime = datetime
        # read file
        rst_aux.load_asc(file=file_data)
        # load prj
        if prj_file is None:
            pass
        else:
            rst_aux.load_prj(file=prj_file)
        # set table
        if table_file is None:
            pass
        else:
            rst_aux.load_table(file_table=table_file)
        # append to collection
        self.append(new_object=rst_aux)
        # delete aux
        del rst_aux

    def w_load_file(self, file_info):
        """
        Worker function to load a single file.
        """
        s_name, s_date_map, asc_file, prj_file, table_file = file_info
        self.load_data(
            name=s_name,
            datetime=s_date_map,
            file_data=asc_file,
            prj_file=prj_file,
            table_file=table_file,
        )

    # todo [DRY] -- this seems duplicated except by the file_table parameters

    def load_folder(
        self,
        folder,
        name_pattern,
        file_table,
        verbose=False,
        file_format="tif",
        logger=None,
    ):
        super().load_folder(
            folder=folder,
            name_pattern=name_pattern,
            file_table=file_table,
            verbose=verbose,
            file_format=file_format,
            logger=logger,
        )
        return None

    def get_series_areas(self):
        """
        Get areas prevalance for all series

        :return: dataframe of series areas
        :rtype: :class:`pandas.DataFrame`
        """

        # compute areas for each raster
        for i in range(len(self.catalog)):
            s_raster_name = self.catalog[self.field_name].values[i]
            s_raster_date = self.catalog[self.field_datetime].values[i]
            # compute
            df_areas = self.collection[s_raster_name].get_areas()
            # insert name and date fields
            df_areas.insert(
                loc=0, column="{}_raster".format(self.field_name), value=s_raster_name
            )
            df_areas.insert(loc=1, column=self.field_datetime, value=s_raster_date)
            # concat dataframes
            if i == 0:
                df_areas_full = df_areas.copy()
            else:
                df_areas_full = pd.concat([df_areas_full, df_areas])
        df_areas_full[self.field_name] = df_areas_full[self.field_name].astype(
            "category"
        )
        df_areas_full[self.field_datetime] = pd.to_datetime(
            df_areas_full[self.field_datetime]
        )
        # handle id for raster
        field_name = "{}_raster".format(self.field_name)
        # slice from areas
        df_slice = df_areas_full[[field_name, self.field_datetime]].copy()
        df_slice = pd.DataFrame(df_slice).drop_duplicates(subset=field_name)

        # sort and reset
        df_slice = df_slice.sort_values(by=self.field_datetime)
        df_slice = df_slice.reset_index(drop=True)
        # create the id
        field_id = "id_raster"
        df_slice[field_id] = df_slice.index.values + 1
        df_slice = df_slice[[field_id, field_name]].copy()

        ls_old_columns = list(df_areas_full.columns)
        ls_new_columns = [field_id] + ls_old_columns

        # merge
        df_areas_full = pd.merge(
            left=df_areas_full, right=df_slice, on=field_name, how="left"
        )
        # organize
        df_areas_full = df_areas_full[ls_new_columns].copy()

        return df_areas_full

    # todo [refactor]
    @staticmethod
    def view_series_areas(
        df_table,
        df_areas,
        specs=None,
        show=True,
        export_areas=True,
        folder="./output",
        filename=None,
        dpi=300,
        fig_format="jpg",
    ):
        """
        View series areas

        :param specs: specifications dictionary, defaults to None
        :type specs: dict
        :param show: option to show plot instead of saving, defaults to False
        :type show: bool
        :param folder: path to output folder, defaults to ``./output``
        :type folder: str
        :param filename: name of file, defaults to None
        :type filename: str
        :param dpi: image resolution, defaults to 96
        :type dpi: int
        :param fig_format: image fig_format (ex: png or jpg). Default jpg
        :type fig_format: str


        """
        # get specs
        default_specs = {
            "title": "Area Series",
            "width": 5 * 1.618,
            "height": 5,
            "ylabel": "Area prevalence (%)",
            "range": (0, 100),
            "xlim": None,
            "legend_x": 0.85,
            "legend_y": 0.33,
            "legend_ncol": 3,
            "filter_by_id": None,  # list of ids
            "annotate": False,
            "annotate_by_id": None,
        }
        # handle inputs specs
        if specs is None:
            pass
        else:  # override default
            for k in specs:
                default_specs[k] = specs[k]
        specs = default_specs

        # Deploy figure
        fig = plt.figure(figsize=(specs["width"], specs["height"]))  # Width, Height
        gs = mpl.gridspec.GridSpec(
            3, 1, wspace=0.5, hspace=0.9, left=0.1, bottom=0.1, top=0.9, right=0.95
        )
        fig.suptitle(specs["title"])

        # start plotting
        plt.subplot(gs[0:2, 0])
        for i in range(len(df_table)):
            # get attributes
            _id = df_table["Id"].values[i]
            _name = df_table["Name"].values[i]
            _alias = df_table["Alias"].values[i]
            _color = df_table["Color"].values[i]
            # ploting
            if specs["filter_by_id"] == None:
                # filter series
                _df = df_areas.query("Id == {}".format(_id)).copy()
                plt.plot(_df["Date"], _df["Area_%"], color=_color, label=_name)
            else:
                if _id in specs["filter_by_id"]:
                    # filter series
                    _df = df_areas.query("Id == {}".format(_id)).copy()
                    plt.plot(_df["Date"], _df["Area_%"], color=_color, label=_name)
                    # annotate
                    if specs["annotate"]:
                        if _id in specs["annotate_by_id"]:
                            lst_dates = [_df["Date"].values[0], _df["Date"].values[-1]]
                            lst_areas = [
                                _df["Area_%"].values[0],
                                _df["Area_%"].values[-1],
                            ]
                            plt.plot(
                                lst_dates,
                                lst_areas,
                                color=_color,
                                marker="o",
                                linestyle="",
                            )
                            plt.text(
                                x=lst_dates[0],
                                y=lst_areas[0] + 5,
                                s="{:.1f}%".format(lst_areas[0]),
                                color=_color,
                            )
                            plt.text(
                                x=lst_dates[1],
                                y=lst_areas[1] + 5,
                                s="{:.1f}%".format(lst_areas[1]),
                                color=_color,
                            )
                else:
                    pass

        plt.legend(
            frameon=True,
            fontsize=9,
            markerscale=0.8,
            bbox_to_anchor=(specs["legend_x"], specs["legend_y"]),
            bbox_transform=fig.transFigure,
            ncol=specs["legend_ncol"],
        )
        plt.xlim(df_areas["Date"].min(), df_areas["Date"].max())
        plt.ylabel(specs["ylabel"])
        plt.ylim(specs["range"])
        if specs["xlim"]:
            plt.xlim(pd.to_datetime(specs["xlim"]))

        # show or save
        if show:
            plt.show()
        else:
            if filename is None:
                filename = "areas"
            # save fig1
            plt.savefig("{}/{}.{}".format(folder, filename, fig_format), dpi=dpi)
            # save areas
            if export_areas:
                df_areas.to_csv(
                    "{}/{}.csv".format(folder, filename), sep=";", index=False
                )
        plt.close(fig)
        return None


# CLASSES -- Module-level
# =======================================================================
# ... {develop}


# SCRIPT
# ***********************************************************************
# standalone behaviour as a script

if __name__ == "__main__":

    # Script section
    # ===================================================================
    print("Hello world!")
    # ... {develop}

    # Script subsection
    # -------------------------------------------------------------------
    # ... {develop}
