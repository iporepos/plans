# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
Primitive classes for handling datasets.
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
import matplotlib.ticker as mticker
import matplotlib.colors as mcolors
import rasterio

# ... {develop}

# Project-level imports
# =======================================================================
from plans.root import Collection, DataSet
from plans.datasets.analyst import Univar, GeoUnivar, LazyStat
from plans.stochastic import arma as _arma
from plans.stochastic import binning as _binning
from plans.stochastic import metrics as _metrics
from plans import viewer
from plans import geo

# ... {develop}


# CONSTANTS
# ***********************************************************************
# define constants in uppercase

# days in a year, averaged over a full cycle of the leap years
YEAR_DAYS = 365.2425

# CONSTANTS -- Project-level
# =======================================================================
DC_NODATA = {
    "byte": 255,  # categorical/boolean maps
    "uint8": 255,  # categorical/boolean maps
    "uint16": 0,  # zone maps
    "uint32": 0,  # zone maps
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
    """
    A time series dataset with a datetime-indexed variable.

    Extends :class:`~plans.datasets.analyst.Univar` with temporal structure:
    frequency detection, standardization, gap analysis, and scaling.
    """

    EPOCHS_ROWS = 14  # rows of the list of epochs, by column

    # Dunder methods
    # -------------------------------------------------------------------
    def __init__(self, name="MyTimeSeries", alias="TS0"):

        # upstream setups
        # ----------------------------------------------------------------
        self.dtfield = "datetime"
        self.agg = "mean"
        self.cmap = "Dark2"
        self.object_alias = "TS"
        self.rawcolor = "gray"  # alternativa color
        self.folder_src = None

        # call super
        # ----------------------------------------------------------------
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
        self.is_standard = False
        self.gapsize = 6
        self.epochs_stats = None
        self.epochs_n = None
        self.smallgaps_n = None
        self.eva = None

        # incoming data
        self.file_data = None
        self.file_data_dtfield = self.dtfield
        self.file_data_varfield = self.varfield

        # generator defaults. See generate()
        self.generator_floor = None
        self.generator_specs = {
            "baseline": 10.0,
            "topline": 20.0,
            "peak_day": 15,
            "power": 1.0,
            "memory_days": 5.0,
            "remainder_sd": 1.0,
            "change_per_year": 0.0,
        }

        self.layouts = {
            "full": {
                "ncols": 34,
                "nrows": 16,
                "width": viewer.FIG_SIZES["L"]["w"],
                "height": viewer.FIG_SIZES["L"]["h"],
            },
            "mini": {
                "ncols": 34,
                "nrows": 12,
                "width": viewer.FIG_SIZES["L"]["w"],
                "height": viewer.FIG_SIZES["L"]["h"],
            },
            "simple": {
                "ncols": 34,
                "nrows": 12,
                "width": viewer.FIG_SIZES["M"]["w"],
                "height": viewer.FIG_SIZES["M"]["h"],
            },
            "simple-shallow": {
                "ncols": 34,
                "nrows": 12,
                "width": viewer.FIG_SIZES["M3"]["w"],
                "height": viewer.FIG_SIZES["M3"]["h"],
            },
            "epochs": {
                "ncols": 34,
                "nrows": 12,
                "width": viewer.FIG_SIZES["L"]["w"],
                "height": viewer.FIG_SIZES["L"]["h"],
                "ax_hist": False,
                "ax_cdf": False,
            },
            "default": {
                "ncols": 34,
                "nrows": 16,
                "width": viewer.FIG_SIZES["L"]["w"],
                "height": viewer.FIG_SIZES["L"]["h"],
            },
        }

        # call internals
        # ----------------------------------------------------------------
        self._set_view_specs()
        # specs as last set by the object, to tell them from the user ones
        self.view_specs_base = dict(self.view_specs)

        # ... continues in downstream objects ... #
        # ----------------------------------------------------------------

    # Core internal methods
    # -------------------------------------------------------------------
    def _set_fields(self):
        """
        Set catalog fields names. Expected to increment superior methods.
        """
        # call super
        # ----------------------------------------------------------------
        super()._set_fields()

        # TimeSeries fields
        self.code_field = "code"
        self.x_field = "x"
        self.y_field = "y"

        self.varfield_field = "variable_field"
        self.varname_field = "variable_name"
        self.varalias_field = "variable_alias"
        self.datarange_min_field = "variable_range_min"
        self.datarange_max_field = "variable_range_max"
        self.var_min_field = "variable_min"
        self.var_max_field = "variable_max"

        self.dtfield_field = "datetime_field"
        self.dtfreq_field = "datetime_freq"
        self.dtres_field = "datetime_res"
        self.start_field = "start"
        self.end_field = "end"

        self.isstandard_field = "is_standard"

        # Epochs
        self.gapsize_field = "gap_size"
        self.epochs_n_field = "n_epoch"
        self.smallgaps_n_field = "n_gaps_small"
        self.epochs_id_field = "id_epoch"

        # file fields
        self.file_data_dtfield_field = "file_data_datetime_field"
        self.file_data_varfield_field = "file_data_variable_field"

        # ... continues in downstream objects ... #

    def _set_frequency(self):
        """
        Infer the datetime frequency of the time series from the spacing
        between consecutive timestamps.

        The *mode* (most common value) of consecutive timestamp deltas is
        used to determine the frequency, rather than checking which
        calendar components (seconds, minutes, hours, ...) vary across the
        series. This makes detection robust to a small minority of
        jittered or missing timestamps: as long as the majority of gaps
        between consecutive records share the same spacing, that spacing
        wins, even if a few records are irregular.

        Sets ``self.dtfreq`` to one of the supported Pandas-like frequency
        aliases (``"1min"``, ``"20min"``, ``"h"``, ``"D"``, ``"MS"``,
        ``"YS"``) based on which boundary the modal delta falls into, and
        ``self.dtres`` to the corresponding resolution label (``"second"``,
        ``"minute"``, ``"hour"``, ``"day"``, ``"month"``, ``"year"``).

        For ``"MS"`` and ``"YS"`` frequencies, ``self.gapsize`` is also
        forced to ``1``, since a single missing month or year is already a
        meaningful gap at that resolution.

        .. note::

            Detection is based on the *majority* delta, not a strict
            consistency check. If irregular spacing accounts for more than
            half of the deltas in the series, the detected frequency will
            reflect that majority rather than the "intended" sampling rate.
            Always sanity-check ``self.dtfreq`` after loading unfamiliar or
            untrusted data.

        :return: None. Updates ``self.dtfreq``, ``self.dtres``, and
            possibly ``self.gapsize`` in place.
        :rtype: None
        """
        # Handle void data
        if self.data is None:
            return None

        # Sort and compute consecutive timestamp deltas
        dt = self.data[self.dtfield].sort_values()
        deltas = dt.diff().dropna()

        if len(deltas) == 0:
            # single-row (or empty) series: fall back to a sensible default
            self.dtfreq = "h"
            self.dtres = "hour"
            return None

        # Use the *mode* of deltas: robust to a handful of jittered or
        # missing timestamps, unlike checking calendar-component variety.
        modal_delta = deltas.mode().iloc[0]

        # Map the modal delta onto the nearest supported frequency alias.
        # Boundaries are chosen so a delta comfortably fits its natural bucket.
        seconds = modal_delta.total_seconds()
        if seconds < 60:
            self.dtfreq = "1min"
            self.dtres = "second"
        elif seconds < 30 * 60:
            self.dtfreq = "20min"
            self.dtres = "minute"
        elif seconds < 20 * 3600:
            self.dtfreq = "h"
            self.dtres = "hour"
        elif seconds < 20 * 86400:
            self.dtfreq = "D"
            self.dtres = "day"
        elif seconds < 300 * 86400:
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
        # call super
        dc_meta = super().get_metadata()

        # customize local metadata:
        dc_meta_local = {
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
        dc_meta.update(dc_meta_local)
        # move file_data to the end
        dc_meta.pop(self.field_file_data)
        dc_meta[self.field_file_data] = self.file_data
        return dc_meta

    def get_range_datetime(self):
        """
        Return the [start, end] datetime extent of the loaded data.

        :return: Two-element list of [min, max] Timestamps.
        :rtype: list
        """
        ls = [self.data[self.dtfield].min(), self.data[self.dtfield].max()]
        return ls[:]

    def get_seasonal_ensemble(self, year_start=1):
        """
        Get an ensemble with one member per year of the series.

        :param year_start: first month of the year, from 1 to 12. Default is 1.
        :type year_start: int
        :return: ensemble with members of the same type as this series
        :rtype: :class:`SeasonalEnsemble`
        """
        se = SeasonalEnsemble(name=self.name, base_object=type(self))
        se.set_series(ts=self, year_start=year_start)
        return se

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
        - Refreshes the default ``view_specs``. Specs set by the user are kept.

        """
        dc_user = {}
        if self.data is not None:
            dc_user = {
                k: v
                for k, v in self.view_specs.items()
                if k not in self.view_specs_base or v != self.view_specs_base[k]
            }

        super().update()

        if self.data is not None:
            self._set_frequency()
            self.start = self.data[self.dtfield].min()
            self.end = self.data[self.dtfield].max()
            # keep the range from the parent, the reset below clears it
            range_y = self.view_specs["range"]
            self._set_view_specs()
            self.view_specs["range"] = range_y
            self.view_specs["xmax_aux"] = 1.2 * self.freq_df["Frequency"].max()
            self.view_specs["ymax"] = self.data[self.varfield].max()
            self.view_specs["xmax"] = self.data[self.dtfield].max()
            self.view_specs["xmin"] = self.data[self.dtfield].min()
            self.view_specs_base = dict(self.view_specs)
            self.view_specs.update(dc_user)

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
        self, input_df, input_dtfield, input_varfield, filter_dates=None, dropnan=False
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
        :param dropnan: If True, drop NaN values from the DataFrame. Default is False.
        :type dropnan: bool

        **Notes**

        - Assumes the inputs DataFrame has a datetime column in the format "YYYY-mm-DD HH:MM:SS".
        - Renames columns to standard format (datetime: ``self.dtfield``, variable: ``self.varfield``).
        - Converts the datetime column to standard format.

        """
        # Get a copy of the inputs DataFrame
        df = input_df.copy()

        # filter only for input fields
        df = df[[input_dtfield, input_varfield]].copy()

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
        df[self.dtfield] = pd.to_datetime(df[self.dtfield], format="%Y-%m-%d %H:%M:%S")

        if filter_dates is None:
            pass
        else:
            if filter_dates[0] is not None:
                df = df.query("{} >= '{}'".format(self.dtfield, filter_dates[0]))
            if filter_dates[1] is not None:
                df = df.query("{} < '{}'".format(self.dtfield, filter_dates[1]))

        # Set the data attribute
        self.data = df.copy()
        self.is_standard = False

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
        self.is_standard = False

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

        in_df = self._cut_edges(df=self.data)

        # output
        if inplace:
            self.data = in_df.copy()
            return None
        else:
            return in_df

    def _cut_edges(self, df):
        """
        Get a dataframe without its initial and final NaN records.

        :param df: dataframe with the variable field
        :type df: :class:`pandas.DataFrame`
        :return: copy of the dataframe, unchanged if all records are NaN
        :rtype: :class:`pandas.DataFrame`
        """
        vct_valid = df[self.varfield].notna().values
        if not vct_valid.any():
            return df.copy()
        n_start = np.argmax(vct_valid)
        n_end = len(vct_valid) - np.argmax(vct_valid[::-1])
        return df.iloc[n_start:n_end].copy()

    def standardize(self):
        """
        Force the time series onto a regular datetime grid at its detected frequency.

        This builds a full, evenly-spaced date range spanning the series'
        start to end (at day resolution) and left-merges the existing data
        onto it. Any regular-grid slot that has no matching timestamp in the
        original data becomes a row with a null value in ``varfield`` --
        i.e. standardizing an irregular series (one with missing timestamps)
        is what turns those missing timestamps into explicit gaps.

        If multiple original records fall within the same grid slot (e.g. two
        readings a few minutes apart, both bucketed into the same hour), they
        are aggregated using the ``agg`` attribute (e.g. ``"mean"``) before
        being placed in that slot.

        **Notes**

        - The target frequency is read from ``self.dtfreq``, which is set by
          ``_set_frequency()`` (called automatically on load, based on the
          mode of consecutive timestamp deltas -- robust to a handful of
          jittered or missing timestamps, but not to a majority of them).
        - Bucketing uses ``.dt.floor()`` for fixed-frequency grids
          (``1min``, ``20min``, ``h``, ``D``) and calendar-aware period
          flooring for calendar-variable grids (``MS``, ``YS``), so each
          timestamp is always bucketed independently based on its own value,
          never merged with unrelated timestamps in the same coarser unit.
        - Sets ``self.is_standard = True`` on completion. Methods that need
          the regular grid (e.g. ``get_epochs``, ``interpolate_gaps``) work on
          a regular copy while this flag is ``False``, leaving ``self.data`` as it is.
        - Calls ``self.update()`` at the end, refreshing derived statistics
          to reflect the new (possibly larger, possibly gap-containing) data.

        .. warning::

            This method modifies ``self.data`` in place (there is no
            ``inplace`` parameter). If you need the original, irregular data
            preserved, keep a separate reference or a ``copy.deepcopy`` of
            the object before calling this method.

        .. warning::

            Row count generally *increases* after standardizing an irregular
            series, since missing grid slots are inserted as null rows.
            Review ``len(self.data)`` and the null count after calling this
            method rather than assuming they're unchanged.

        :return: None. Updates ``self.data`` and ``self.is_standard`` in place.
        :rtype: None

        :Example:

        >>> ts.is_standard
        False
        >>> len(ts.data)
        311
        >>> ts.standardize()
        >>> ts.is_standard
        True
        >>> len(ts.data)          # now includes inserted null rows
        360
        >>> ts.data[ts.varfield].isna().sum()
        49
        """
        self.data = self._get_standard_data()
        self.is_standard = True

        # Update all attributes
        self.update()

        return None

    def _get_standard_data(self, cut=False):
        """
        Get a copy of the data on the regular grid. The series is not changed.

        :param cut: If True, also cut off the initial and final NaN records.
        :type cut: bool
        :return: data on the regular grid
        :rtype: :class:`pandas.DataFrame`
        """
        if self.is_standard:
            return (
                self._cut_edges(df=self.data).reset_index(drop=True)
                if cut
                else self.data.copy()
            )

        def _insert_epochs(df):
            """
            Assign each row in ``df`` to its containing time bucket at the
            series' detected frequency (``self.dtfreq``), used as a merge key
            for aligning data onto the standardized grid.

            For fixed-length frequencies (``"1min"``, ``"20min"``, ``"h"``,
            ``"D"``), each timestamp is floored independently to its own
            bucket boundary via ``.dt.floor()`` -- e.g. at ``"20min"``, a
            timestamp of ``08:07`` floors to ``08:00`` and ``08:23`` floors to
            ``08:20``, so timestamps in different buckets are never merged
            together regardless of which other timestamps happen to be present
            in the series.

            For calendar-variable frequencies (``"MS"``, ``"YS"``), where
            fixed-length flooring doesn't apply (months/years differ in
            length), bucketing instead uses calendar-aware period flooring via
            ``.dt.to_period(...).dt.to_timestamp()``.

            :param df: DataFrame containing at least the datetime column
                (``self.dtfield``) to bucket.
            :type df: :class:`pandas.DataFrame`
            :return: The same DataFrame with an added ``f"{self.dtfield}_epoch"``
                column holding each row's bucket timestamp.
            :rtype: :class:`pandas.DataFrame`
            """

            # Fixed-frequency aliases can be floored directly; calendar-variable
            # aliases (month/year lengths differ) need calendar-aware bucketing.
            if self.dtfreq in ("1min", "20min", "h", "D"):
                offset = pd.tseries.frequencies.to_offset(self.dtfreq)
                df[self.dtfield + "_epoch"] = df[self.dtfield].dt.floor(offset)
            elif self.dtfreq == "MS":
                df[self.dtfield + "_epoch"] = (
                    df[self.dtfield].dt.to_period("M").dt.to_timestamp()
                )
            else:  # "YS"
                df[self.dtfield + "_epoch"] = (
                    df[self.dtfield].dt.to_period("Y").dt.to_timestamp()
                )
            return df

        # the ideia is to implement regular time increments and insert null rows

        # make a copy of the data
        df_data = self.data.copy()
        # insert epochs based on data frequency
        df_data = _insert_epochs(df=df_data)
        # aggregate by epoch. A plain sum would turn empty slots into zeros
        dc_agg = {"min_count": 1} if self.agg == "sum" else {}
        df_data = (
            df_data.groupby(self.dtfield + "_epoch")[self.varfield]
            .agg(self.agg, **dc_agg)
            .reset_index()
        )

        # Standardize incoming start and end
        start_std = self.start.normalize()  # the start of day
        end_std = self.end.normalize() + pd.Timedelta(days=1)  # the start of next day
        end_std = end_std.date()

        # Get a standard date range for all periods
        # next day is excluded: grid ends at the last slot of the last day
        dt_index = pd.date_range(
            start=start_std, end=end_std, freq=self.dtfreq, inclusive="left"
        )

        # Set standarnd dataframe
        df_data_std = pd.DataFrame({self.dtfield: dt_index})
        df_data_std = _insert_epochs(df=df_data_std)

        on_st = self.dtfield + "_epoch"
        df_data_std = pd.merge(left=df_data_std, right=df_data, on=on_st, how="left")

        # Clear extra column
        df_data_std = df_data_std.drop(columns=on_st)
        if cut:
            df_data_std = self._cut_edges(df=df_data_std).reset_index(drop=True)
        return df_data_std

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
        representing gaps in the time series. Missing timestamps count as gaps,
        since the labels are made on the regular grid.

        With ``inplace=True``, the data becomes the labeled regular grid.

        """
        df = self._label_epochs(df=self._get_standard_data())

        if inplace:
            self.data = df.copy()
            self.is_standard = True
            return None
        else:
            return df

    def _label_epochs(self, df):
        """
        Label the records of a dataframe by epoch (0 = gap epoch).

        :param df: dataframe with the variable field, one record per time step
        :type df: :class:`pandas.DataFrame`
        :return: copy of the dataframe with the epoch field
        :rtype: :class:`pandas.DataFrame`
        """
        df = df.copy()
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
        # a run at the end has no record after it, so the loop can not see it
        if len(df) > 0 and df["CumSum"].values[-1] >= self.gapsize:
            skip_v[len(df) - df["CumSum"].values[-1] :] = 1
        df["Skip"] = skip_v

        # Set Epoch Field
        epoch_v = np.zeros(len(df), dtype=int)
        # counter epochs
        counter = 1
        skip_arr = df["Skip"].values
        for i in range(len(df) - 1):
            if skip_arr[i] == 0:
                epoch_v[i] = counter
            else:
                if skip_arr[i + 1] == 0:
                    counter = counter + 1
        # last row (not covered by the loop)
        if len(df) > 0 and skip_arr[-1] == 0:
            epoch_v[-1] = counter
        df[self.epochs_id_field] = epoch_v

        return df.drop(columns=["CumSum", "Skip"])

    def update_epochs_stats(self):
        """
        Update all epochs statistics.

        **Notes**

        - This function updates statistics for all epochs in the time series.
        - Works on a regular copy of the data without its NaN edges. The data itself is not changed.
        - Removes epoch 0 from the statistics since it typically represents non-standardized or invalid data.
        - Groups the data by and calculates statistics such as count, start, and end timestamps for each epoch.
        - Generates random colors for each epoch using the ``get_random_colors`` function with a specified colormap (`cmap`` attribute).
        - Includes the time series name in the statistics for identification.
        - Organizes the statistics DataFrame to include relevant columns
        - Updates the attribute with the number of epochs in the statistics.

        """

        # Get epochs
        df = self._label_epochs(df=self._get_standard_data(cut=True))

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
            size=len(self.epochs_stats), cmap=self.cmap, randomize=False
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
        :return: A new ``pandas.DataFrame`` with interpolated values and an ``is_interpolation``
            flag column (1 where the value was filled by interpolation, 0 where it was
            already present) if inplace is False, otherwise None.
        :rtype: :class:`pandas.DataFrame` or None

        **Notes**

        The interpolation runs on the regular grid. The series is only standardized if ``inplace`` is True.
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

        # Get epochs for interpolation
        df = self.get_epochs(inplace=False)
        epochs = df[self.epochs_id_field].unique()
        list_dfs = list()

        for epoch in epochs:
            df_aux1 = df.query("{} == {}".format(self.epochs_id_field, epoch)).copy()
            if epoch == 0:
                df_aux1["{}_interpolation".format(self.varfield)] = np.nan
            else:
                if method == "constant":
                    df_aux1["{}_interpolation".format(self.varfield)] = np.where(
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
                        bounds_error=False,  # edges of an epoch are not extrapolated
                        fill_value=np.nan,
                    )
                    # Interpolate full values
                    df_aux1["{}_interpolation".format(self.varfield)] = (
                        interpolation_func(df_aux1[self.dtfield].astype(np.int64))
                    )
            # flag rows that were missing and are now filled
            s_filled = df_aux1["{}_interpolation".format(self.varfield)]
            df_aux1["is_interpolation"] = (
                df_aux1[self.varfield].isna() & s_filled.notna()
            ).astype(int)
            # Append
            list_dfs.append(df_aux1)
        df_new = pd.concat(list_dfs, ignore_index=True)
        df_new = df_new.sort_values(by=self.dtfield).reset_index(drop=True)

        if inplace:
            if not self.is_standard:
                self.standardize()
            self.data[self.varfield] = df_new[
                "{}_interpolation".format(self.varfield)
            ].values
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

        # set list of tuples. A plain sum would turn empty periods into zeros
        agg_funcs_list = [
            (
                "{}_{}".format(self.varfield, f),
                (
                    (lambda x: x.sum(min_count=1))
                    if agg_funcs[f] == "sum"
                    else agg_funcs[f]
                ),
            )
            for f in agg_funcs
        ]

        # get data
        df = self.data.copy()
        df["Bad"] = df[self.varfield].isna().astype(int)

        # Set the 'datetime' column as the index
        df.set_index(self.dtfield, inplace=True)

        # Resample the time series to a frequency using aggregation functions
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

    def scale_up(self, freq, bad_max, inplace=True):
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

            **Anchoring behavior** -- this affects where each aggregation window starts/ends:

            - Plain multiples of a base unit (e.g. ``"5D"`` for a pentad, ``"10D"``) are
              *data-start-anchored*: bins are chunked every N units starting from wherever
              the series begins, not from a fixed calendar boundary.
            - Calendar units (``W``, ``MS``, ``QS``, ``YS``, etc.) are *calendar-anchored*:
              bins snap to fixed real-world boundaries regardless of where the data starts.
            - ``W`` defaults to ``W-SUN`` (weeks ending Sunday). Anchor to any weekday with
              a suffix, e.g. ``W-MON``, ``W-WED``, ``W-FRI``.
            - ``YS``/``YE`` default to the calendar year (start Jan 1 / end Dec 31). Anchor
              to any month with a suffix to define e.g. a hydrological/water year:
              ``"YS-OCT"`` (year starting Oct 1, e.g. US water year convention) or
              ``"YE-SEP"`` (year ending Sep 30). The suffix month plus ``YS-``/``YE-``
              together set whether that month is the start or the end of the bin.

        :type freq: str
        :param bad_max: The maximum number of ``Bad`` records allowed in a time window for aggregation. Records with more ``Bad`` entries
            will be excluded from the aggregated result.
        :type bad_max: int
        :param inplace: option for overwrite data, default True. When False, returns a new
            ``TimeSeries`` object (an exact copy of ``self``) holding the upscaled data,
            instead of a bare DataFrame.
        :type inplace: bool

        :return: ``None`` if ``inplace=True`` (data is overwritten in place), otherwise a new
            ``TimeSeries`` instance of the same subclass as ``self``, with identical metadata
            and the upscaled data/derived stats.
        :rtype: None or TimeSeries

        :Example:

        >>> # Pentad upscale (data-start-anchored)
        >>> ts_pentad = ts.scale_up(freq="5D", bad_max=0, inplace=False)
        >>> # Weekly upscale, anchored to Monday-ending weeks
        >>> ts_weekly = ts.scale_up(freq="W-MON", bad_max=0, inplace=False)
        >>> # Hydrological year, Oct-Sep
        >>> ts_hydro = ts.scale_up(freq="YS-OCT", bad_max=0, inplace=False)
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
            # update derived data
            self.stats_df = self.get_basic_stats()
            self.freq_df = self.get_frequency()
            self.weibull_df = self.get_cdf_weibull()

            return None
        else:
            import copy

            ts_new = copy.deepcopy(self)
            ts_new.data = df_upscale
            ts_new._set_frequency()
            ts_new.stats_df = ts_new.get_basic_stats()
            ts_new.freq_df = ts_new.get_frequency()
            ts_new.weibull_df = ts_new.get_cdf_weibull()

            return ts_new

    def scale_down(self, freq, covariate=None, align="center", inplace=False):
        """
        Downscale the time series to a finer time step.

        For non-flow variables (``self.agg != "sum"``), each coarse data
        point is first repositioned in time according to ``align`` (see
        below), then linearly interpolated onto the finer grid. Because
        this repositioning shifts the interpolation anchors away from a
        naive "value at period start" assumption, a single global
        multiplicative correction is applied afterward so that the
        downscaled series' overall mean exactly matches the original
        series' overall mean. Note this conserves the mean of the
        **whole series**, not each individual period -- an earlier,
        stricter per-period mean-preserving approach was found to
        produce unstable, oscillating results with volatile inputs and
        was intentionally not used here.

        The ``align`` parameter controls where each coarse point is
        assumed to sit within the period it represents:

        - ``"start"``: at the period's own timestamp (no shift). E.g. a
          daily value stays anchored at ``00:00``.
        - ``"center"`` (default): at the middle of the period. E.g. a
          daily value is anchored at ``12:00`` of that day.
        - ``"end"``: at the end of the period. E.g. a daily value is
          anchored at the following day's ``00:00``.

        Anchor placement leaves flat (constant) values outside the
        earliest/latest anchor -- e.g. with ``align="center"``, there is
        no data before the first period's midpoint, so the interpolated
        series holds that first value flat until the midpoint is reached.

        For flow/sum variables (``self.agg == "sum"``, e.g. precipitation
        totals), each source period's total is distributed across its fine
        sub-steps such that the sub-steps sum back to exactly that period's
        original total -- no mass leaks across period boundaries. ``align``
        is not used in this case (sum conservation is enforced directly at
        the level of each time step, not via anchor placement). Two modes:

        - **Uniform split** (default, ``covariate=None``): each period's
          total is split evenly across its fine sub-steps.
        - **Covariate-weighted** (``covariate`` given): each period's total
          is distributed proportionally to a covariate signal's own shape
          within that period, e.g. using a higher-resolution proxy (radar
          or satellite precipitation) to shape how a daily gauge total is
          spread across finer time steps. The covariate is linearly
          interpolated onto the target grid first if it isn't already
          sampled at ``freq``. Any period where the covariate is entirely
          zero or missing falls back to a uniform split for that period,
          so covariate gaps never produce ``NaN`` or divide-by-zero results.

        In both branches, the fine grid is extended one full period past
        the series' last timestamp so the final period is subdivided the
        same way as every other period, rather than being collapsed into
        a single fine step holding that whole period's value.

        :param freq: new time step frequency
        :type freq: str
        :param covariate: optional higher-resolution ``TimeSeries`` whose
            values are used to shape the within-period distribution for
            flow/sum variables. Ignored when ``self.agg != "sum"``.
        :type covariate: TimeSeries or None
        :param align: for non-sum variables, where each coarse point is
            anchored within its period: ``"start"``, ``"center"``
            (default), or ``"end"``. Ignored when ``self.agg == "sum"``.
        :type align: str
        :param inplace: option for overwrite data, default False. When
            ``True``, overwrites ``self.data`` with the downscaled result
            and returns ``None``. When ``False`` (default), returns a new
            ``TimeSeries`` instance (an exact copy of ``self``) holding
            the downscaled data, instead of a bare DataFrame.
        :type inplace: bool
        :return: ``None`` if ``inplace=True`` (data is overwritten in
            place), otherwise a new ``TimeSeries`` instance of the same
            subclass as ``self``, with identical metadata and the
            downscaled data/derived stats.
        :rtype: None or TimeSeries

        :Example:

        >>> # non-sum variable, e.g. daily-average water level -> hourly,
        >>> # anchored at midday, overall mean preserved
        >>> ts_level_hourly = ts_level.scale_down(freq="1h")
        >>> # uniform split: each day's total spread evenly across hours
        >>> ts_flat = ts_daily.scale_down(freq="1h")
        >>> # covariate-weighted: shaped by an hourly satellite proxy
        >>> ts_shaped = ts_daily.scale_down(freq="1h", covariate=ts_satellite)
        """
        # update
        self.update()

        if len(self.data) < 2:
            raise ValueError(
                "scale_down requires at least 2 data points to infer period length"
            )
        period_delta = self.data[self.dtfield].iloc[1] - self.data[self.dtfield].iloc[0]

        if self.agg != "sum":
            # non-flow variable: linear interpolation on anchored, offset
            # timestamps, then a global multiplicative correction to
            # preserve the overall (whole-series) mean.
            # the fine grid must cover the *entire* last period, not just
            # its start timestamp -- otherwise the final period is
            # truncated to a single fine step instead of being subdivided
            # like every other period (same issue fixed below for sum
            # variables, applies here too since this is still per-period
            # subdivision of a continuous span).
            dt_index = pd.date_range(
                start=self.start,
                end=self.end + period_delta,
                freq=freq,
                inclusive="left",
            )

            if align == "start":
                anchor_offset = pd.Timedelta(0)
            elif align == "center":
                anchor_offset = period_delta / 2
            elif align == "end":
                anchor_offset = period_delta
            else:
                raise ValueError(
                    f"Unknown align option: {align!r}. Expected 'start', 'center', or 'end'."
                )

            df_anchor = self.data[[self.dtfield, self.varfield]].copy()
            df_anchor[self.dtfield] = df_anchor[self.dtfield] + anchor_offset

            s_anchor = df_anchor.set_index(self.dtfield)[self.varfield]
            combined_index = s_anchor.index.union(dt_index)
            s_interp = s_anchor.reindex(combined_index).interpolate(method="time")
            # flat extrapolation outside the anchors' own range
            s_interp = s_interp.reindex(dt_index).ffill().bfill()

            df_downscale = pd.DataFrame(
                {self.dtfield: dt_index, self.varfield: s_interp.values}
            )

            # global correction: rescale so the downscaled series' overall
            # mean matches the original coarse series' overall mean
            mean_original = self.data[self.varfield].mean()
            mean_downscaled = df_downscale[self.varfield].mean()
            if mean_downscaled != 0:
                factor = mean_original / mean_downscaled
                df_downscale[self.varfield] = df_downscale[self.varfield] * factor

        else:
            # sum/flow variable: the fine grid must cover the *entire* last
            # period, not just its start timestamp -- otherwise the final
            # period gets a single fine step holding its whole total instead
            # of being subdivided like every other period. Extend the range
            # by one period_delta and exclude the resulting boundary point
            # (which would mark the start of a period with no data).
            dt_index = pd.date_range(
                start=self.start,
                end=self.end + period_delta,
                freq=freq,
                inclusive="left",
            )

            # set new dataframe
            df_downscale = pd.DataFrame({self.dtfield: dt_index})
            df_downscale = pd.merge(
                left=df_downscale, right=self.data, on=self.dtfield, how="left"
            )

            # -- flow/sum variable: distribute each source period's total across
            # its fine sub-steps, exactly preserving each period's sum --

            # tag each fine timestamp with the source period it belongs to
            df_source = (
                self.data[[self.dtfield, self.varfield]]
                .rename(
                    columns={
                        self.dtfield: "_period_start",
                        self.varfield: "_period_total",
                    }
                )
                .sort_values("_period_start")
            )
            df_downscale = pd.merge_asof(
                df_downscale.sort_values(self.dtfield),
                df_source,
                left_on=self.dtfield,
                right_on="_period_start",
                direction="backward",
            )

            n_per_period = df_downscale.groupby("_period_start")[
                self.dtfield
            ].transform("count")
            uniform_weights = 1.0 / n_per_period

            if covariate is None:
                weights = uniform_weights
            else:
                # covariate-weighted: use the covariate's own shape within each period
                cov_data = covariate.data[
                    [covariate.dtfield, covariate.varfield]
                ].rename(
                    columns={
                        covariate.dtfield: self.dtfield,
                        covariate.varfield: "_cov",
                    }
                )
                df_downscale = pd.merge(
                    df_downscale, cov_data, on=self.dtfield, how="left"
                )
                # resample the covariate onto the target grid if it doesn't
                # already align exactly (e.g. covariate is coarser than `freq`)
                df_downscale["_cov"] = (
                    df_downscale["_cov"].interpolate(method="linear").bfill().ffill()
                )

                cov_clipped = df_downscale["_cov"].clip(lower=0)
                period_cov_sum = cov_clipped.groupby(
                    df_downscale["_period_start"]
                ).transform("sum")
                # fall back to uniform weights in periods with no usable covariate signal
                weights = np.where(
                    period_cov_sum > 0, cov_clipped / period_cov_sum, uniform_weights
                )

            df_downscale[self.varfield] = df_downscale["_period_total"] * weights
            df_downscale = df_downscale[[self.dtfield, self.varfield]]

        # return case
        if inplace:
            # overwrite local data
            self.data = df_downscale
            #
            self._set_frequency()
            # update derived data
            self.stats_df = self.get_basic_stats()
            self.freq_df = self.get_frequency()
            self.weibull_df = self.get_cdf_weibull()

            return None
        else:
            import copy

            ts_new = copy.deepcopy(self)
            ts_new.data = df_downscale
            ts_new._set_frequency()
            ts_new.stats_df = ts_new.get_basic_stats()
            ts_new.freq_df = ts_new.get_frequency()
            ts_new.weibull_df = ts_new.get_cdf_weibull()

            return ts_new

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
        df_eva = self.scale_up(freq=eva_freq, bad_max=self.gapsize, inplace=False)
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
        """
        Add subplots to the figure grid according to the active layout.
        """
        # ------------ setup axes ------------
        if specs["layout"] == "full":
            fig.add_subplot(gs[2:10, 2:20])
            fig.add_subplot(gs[2:10, 22:27])
            fig.add_subplot(gs[2:10, 29:])

        elif specs["layout"] == "mini":
            fig.add_subplot(gs[2:10, 2:20])
            fig.add_subplot(gs[2:10, 22:27])
            fig.add_subplot(gs[2:10, 29:])

        elif specs["layout"] == "simple":
            fig.add_subplot(gs[2:10, 2:34])

        elif specs["layout"] == "simple-shallow":
            # lower top, so the panel title sits below the figure title
            fig.add_subplot(gs[4:10, 2:34])

        elif specs["layout"] == "epochs":
            fig.add_subplot(gs[2:10, 2:20])
            fig.add_subplot(gs[2:10, 22:])  # legend

        else:
            fig.add_subplot(gs[2:10, 2:20])
            fig.add_subplot(gs[2:10, 22:27])
            fig.add_subplot(gs[2:10, 29:])

        return fig

        """    def _get_fig_specs(self):
        # todo [docstring]
        # handle specs
        specs = self.view_specs.copy()

        # handle layout
        layout = specs["layout"]
        if layout not in list(self.layouts.keys()):
            layout = "default"

        specs_aux = self.layouts[layout].copy()

        # update sizes
        specs.update(specs_aux)

        # update gridspecs
        specs.update(viewer.GRID_SPECS)

        return specs"""

    def _plot(self, fig, gs, specs):
        fig = super()._plot(fig=fig, gs=gs, specs=specs)

        # todo continue plots

        return fig

    def _set_view_specs(self):
        """
        Set view specifications.

        """

        # Call the parent method to initialize `view_specs`
        super()._set_view_specs()

        # Update or add new specifications specific to the child class

        s_title = "Time Series | {} | {} ({})".format(
            self.name, self.varname, self.varalias
        )

        self.view_specs.update(
            {
                # export
                "folder": self.folder_src,
                # titles
                "title": s_title,
                "subtitle_data": "Time Series",
                "subtitle_epochs": "Epochs",
                # fields
                "xvar": self.dtfield,
                "yvar": self.varfield,
                "xlabel": self.dtfield,
                # colors
                "color": self.rawcolor,
                "color_aux": self.rawcolor,
                "color_fill": None,
                "color_eva": "blue",
                # legend
                "legend_eva": "Annual Maxima",
                # alphas
                "alpha": 1,
                "alpha_aux": 1,
                "alpha_fill": 1,
                # options
                "fill": False,
                "fill_only": False,
                "color_gaps": "tab:red",
                "alpha_gaps": 0.6,
                "linewidth_gaps": 0.5,  # keeps gaps narrower than a pixel visible
                # ranges todo review
                "xmin": None,
                "xmax": None,
                "xmax_aux": 20,
                "ymin": 0,
                "ymax": None,
                "pad_x": 0.05,  # share of the time span added on each side
                # styles
                "linestyle": "solid",
                "marker": None,
                "marker_eva": ".",
                "drawstyle": None,
                "n_bins": 100,
                "n_dates": 5,
                "format_dates": "%Y-%m-%d",
                "include_eva": False,
                # stats locators
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

        **Layouts**, set by ``view_specs["layout"]``:

        ==================  ================================================================================
        Layout              Panels
        ==================  ================================================================================
        ``full``            Series, histogram and CDF, with the statistics table.
        ``mini``            Series, histogram and CDF.
        ``simple``          Series only.
        ``simple-shallow``  Series only, in a shallow figure.
        ``epochs``          Series with epochs in colors and gaps in the background, and the list of epochs.
        ``default``         Same panels of ``mini``, in the figure of ``full``.
        ==================  ================================================================================

        **View specs**, set by ``view_specs[key] = value`` before the call:

        ====================  ===================  =====================================================================================================================
        Key                   Default              Description
        ====================  ===================  =====================================================================================================================
        ``style``             ``"wien"``           Name of the plot style. See :func:`plans.viewer.set_style`.
        ``folder``            auto                 Folder of the saved figure.
        ``filename``          auto                 Name of the saved figure, without extension.
        ``fig_format``        ``"jpg"``            Format of the saved figure.
        ``dpi``               ``300``              Resolution of the saved figure.
        ``title``             auto                 Title of the figure.
        ``xvar``              auto                 Internal. Column of dates.
        ``yvar``              auto                 Internal. Column of values.
        ``xlabel``            auto                 Label of the x axis.
        ``ylabel``            auto                 Label of the y axis.
        ``color``             ``"gray"``           Color of the line.
        ``xmin``              None                 Not in use.
        ``xmax``              None                 Not in use.
        ``ymin``              ``0``                Bottom of the fill.
        ``ymax``              None                 Not in use.
        ``layout``            ``"full"``           Name of the layout. See the table of layouts.
        ``data_plot``         ``"scatter"``        Plot of the data panel: ``"scatter"`` or ``"boxplot"``.
        ``subtitle_data``     ``"Time Series"``    Title of the series panel. None hides it.
        ``subtitle_box``      ``"Boxplot"``        Title of the data panel, if a boxplot.
        ``subtitle_hist``     ``"Histogram"``      Title of the histogram. None hides it.
        ``subtitle_cdf``      ``"CDF"``            Title of the CDF. None hides it.
        ``subtitle_qq``       ``"Q-Q"``            Title of the Q-Q panel. None hides it.
        ``yvar_field``        auto                 Column of values. Set with the data.
        ``xlabel_cdf``        ``"P(X)"``           Label of the x axis of the CDF.
        ``xlabel_qq``         auto                 Label of the x axis of the Q-Q panel.
        ``data_label``        auto                 Label of the data in the legend.
        ``data_legend``       ``False``            Show the legend of the data panel.
        ``color_hist``        ``"tab:grey"``       Color of the histogram.
        ``color_cdf``         ``"black"``          Color of the CDF.
        ``color_mean``        ``"red"``            Color of the mean line.
        ``color_mean_text``   None                 Color of the mean label. None is gray.
        ``scheme_cmap``       ``"equal"``          Classes of the color map: ``"equal"``, ``"quantiles"`` or other schemes of :func:`plans.stochastic.binning.get_bins`.
        ``n_classes_cmap``    ``5``                Number of classes of the color map.
        ``cmap``              ``"viridis"``        Name of the color map.
        ``alpha``             ``1``                Opacity of the line.
        ``alpha_hist``        ``1``                Opacity of the histogram.
        ``alpha_cdf``         ``1``                Opacity of the CDF.
        ``range``             None                 Range of the y axis, as ``[low, high]``. None is set from the data.
        ``range_x``           None                 Range of the x axis, as ``[low, high]``. None is the time span with ``pad_x``.
        ``plot_mean``         ``True``             Show the mean line.
        ``plot_mean_data``    ``False``            Show the mean line also on the data panel.
        ``linestyle_mean``    ``"solid"``          Line style of the mean.
        ``pad_mean``          ``1``                Spaces between the mean label and its line.
        ``plot_mean_label``   ``True``             Show the mean label.
        ``hist_density``      ``True``             Not in use.
        ``bins``              ``20``               Number of histogram bins, or the width of the bins if ``bins_density``.
        ``bins_density``      ``False``            Take ``bins`` as the width of the bins.
        ``ax_data``           ``0``                Internal. Index of the data axis.
        ``ax_hist``           ``1``                Internal. Index of the histogram axis. False has no histogram.
        ``ax_cdf``            ``2``                Internal. Index of the CDF axis. False has no CDF.
        ``x_stats``           ``0.73``             Horizontal position of the statistics table, as a share of the figure.
        ``x_stats_sep``       ``0.12``             Space between columns of the statistics table.
        ``y_stats``           ``0.28``             Vertical position of the statistics table, as a share of the figure.
        ``zorder_data``       ``1``                Drawing order of the data.
        ``zorder_histh``      ``1``                Drawing order of the histogram.
        ``zorder_cdf``        ``1``                Drawing order of the CDF.
        ``scatter_factor``    ``4``                Size of the scatter markers.
        ``colorize_scatter``  ``False``            Color the scatter markers by the color map.
        ``box_width``         ``0.4``              Width of the boxplot.
        ``box_showfliers``    ``True``             Show the outliers of the boxplot.
        ``subtitle_epochs``   ``"Epochs"``         Title of the list of epochs, in the ``epochs`` layout.
        ``color_aux``         ``"gray"``           Not in use.
        ``color_fill``        None                 Color of the fill. None is the color of the line.
        ``color_eva``         ``"blue"``           Color of the annual maxima.
        ``legend_eva``        ``"Annual Maxima"``  Label of the annual maxima.
        ``alpha_aux``         ``1``                Not in use.
        ``alpha_fill``        ``1``                Opacity of the fill.
        ``fill``              ``False``            Fill below the line, down to ``ymin``.
        ``fill_only``         ``False``            With ``fill``, hide the line.
        ``color_gaps``        ``"tab:red"``        Color of the gaps, in the ``epochs`` layout.
        ``alpha_gaps``        ``0.6``              Opacity of the gaps, in the ``epochs`` layout.
        ``linewidth_gaps``    ``0.5``              Width of the edge of the gaps, which keeps short ones visible.
        ``xmax_aux``          ``20``               Not in use.
        ``pad_x``             ``0.05``             Share of the time span added on each side of the x axis, if ``range_x`` is None.
        ``linestyle``         ``"solid"``          Line style.
        ``marker``            None                 Marker of the line.
        ``marker_eva``        ``"."``              Not in use.
        ``drawstyle``         None                 Draw style of the line, such as ``"steps-mid"``.
        ``n_bins``            ``100``              Not in use.
        ``n_dates``           ``5``                Number of date ticks, evenly spaced in time. None chooses them automatically.
        ``format_dates``      ``"%Y-%m-%d"``       Format of the date labels.
        ``include_eva``       ``False``            Show the annual maxima and their model. Needs the extreme values analysis.
        ``gs_*``              auto                 Internal. Replaced by the shared grid of :mod:`plans.viewer`.
        ====================  ===================  =====================================================================================================================

        :param show: option for showing instead of saving.
        :type show: bool
        :param return_fig: option for returning the figure object itself.
        :type return_fig: bool

        """
        # HANDLE SPECS
        # ------------------------------------------------------------
        specs = self.view_specs.copy()

        # handle eva specs
        if specs["include_eva"]:
            self.view_specs["hist_density"] = True
            self.view_specs["xlabel_b"] = "p(X)"

        # handle mode specs
        if "simple" in specs["layout"] or specs["layout"] == "epochs":
            self.view_specs["ax_hist"] = False
            self.view_specs["ax_cdf"] = False
        else:
            self.view_specs["ax_hist"] = 1
            self.view_specs["ax_cdf"] = 2

        # BUILD FIG
        # ------------------------------------------------------------
        self.view_specs["ax_data"] = False
        fig = super().view(show=False, return_fig=True)
        self.view_specs["ax_data"] = 0

        # PLOT EXTRA
        # ------------------------------------------------------------
        # todo develop DRY -- develop plotting static methods
        # --- call _plot()

        # SERIES
        # ------------------------------------------------------------

        # series plot
        axes = fig.get_axes()

        ax = axes[specs["ax_data"]]
        ax.cla()

        if specs["layout"] == "epochs":
            self._plot_epochs(ax=ax, ax_legend=axes[1], specs=specs)
        else:
            TimeSeries.plot_series(data=self.data, ax=ax, specs=specs)

        # handle eva
        # ----------------------------------------------
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
                    bins=_binning.get_nbins_fd(data=data),
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

        # keep y grid lines off the x ticks
        # ----------------------------------------------
        if specs["include_eva"] and self.eva is not None:
            # the EVA model panel has its own y axis
            viewer.clear_xticks(axes=axes[:2])
            viewer.clear_xticks(axes=axes[2:])
        elif specs["layout"] == "epochs":
            viewer.clear_xticks(axes=[ax])
        else:
            viewer.clear_xticks(axes=axes)

        # SHIP
        # ----------------------------------------------------------------
        # create path
        file_path = "{}/{}.{}".format(
            specs["folder"], specs["filename"], specs["fig_format"]
        )
        viewer.set_layers(fig=fig)
        if return_fig:
            return fig
        else:
            viewer.ship_fig(fig=fig, show=show, file_output=file_path, dpi=specs["dpi"])

    def _plot_epochs(self, ax, ax_legend, specs):
        """
        Plot each epoch in its own color and the gaps in the background, with the
        list of epochs on the side. The series is not changed.

        :param ax: axis of the series
        :type ax: :class:`matplotlib.axes.Axes`
        :param ax_legend: axis of the legend
        :type ax_legend: :class:`matplotlib.axes.Axes`
        :param specs: plot specification dictionary
        :type specs: dict
        :return: None
        :rtype: None
        """
        self.update_epochs_stats()
        df = self._get_standard_data(cut=True)
        dates = df[self.dtfield]

        # all epochs under the same range and without their own ticks
        sp = dict(specs, data_legend=False, n_dates=None)
        if sp["range_x"] is None:
            sp["range_x"] = TimeSeries.get_range_x(
                xmin=dates.min(), xmax=dates.max(), pad=specs["pad_x"]
            )
        for i in range(self.epochs_n):
            is_epoch = dates.between(
                self.epochs_stats[self.start_field].values[i],
                self.epochs_stats[self.end_field].values[i],
            )
            sp["color"] = self.epochs_stats[self.field_color].values[i]
            sp["data_label"] = "Epoch {}".format(
                self.epochs_stats[self.epochs_id_field].values[i]
            )
            TimeSeries.plot_series(data=df[is_epoch], ax=ax, specs=sp)

        # the step gives width to gaps of a single record, and the edge keeps it
        # visible when it is narrower than a pixel
        vct_gaps = df[self.varfield].isna().values
        if vct_gaps.any():
            ax.fill_between(
                dates,
                0,
                1,
                where=vct_gaps,
                step="mid",
                transform=ax.get_xaxis_transform(),
                color=specs["color_gaps"],
                alpha=specs["alpha_gaps"],
                linewidth=specs["linewidth_gaps"],
                zorder=0.5,  # below the lines
                label="Gaps",
            )
        TimeSeries.set_date_ticks(
            ax=ax,
            xmin=dates.min(),
            xmax=dates.max(),
            n_dates=specs["n_dates"],
            format_dates=specs["format_dates"],
        )

        # list up to what fits in the space, gaps first
        ls_handles, ls_labels = ax.get_legend_handles_labels()
        n_rows = TimeSeries.EPOCHS_ROWS
        if vct_gaps.any():
            ls_handles = ls_handles[-1:] + ls_handles[:-1]
            ls_labels = ls_labels[-1:] + ls_labels[:-1]
        ls_handles = ls_handles[: 3 * n_rows]
        ls_labels = ls_labels[: 3 * n_rows]
        ax_legend.axis("off")
        ax_legend.set_title(
            "{} ({})".format(specs["subtitle_epochs"], self.epochs_n), loc="left"
        )
        ax_legend.legend(
            ls_handles,
            ls_labels,
            loc="upper left",
            bbox_to_anchor=(0, 1),
            ncol=int(np.ceil(len(ls_labels) / n_rows)),
            fontsize=7,
            frameon=False,
            borderaxespad=0,
        )
        return None

    @staticmethod
    def get_range_x(xmin, xmax, pad):
        """
        Get the range of a time axis with a padding on each side.

        :param xmin: first date
        :type xmin: :class:`pandas.Timestamp`
        :param xmax: last date
        :type xmax: :class:`pandas.Timestamp`
        :param pad: share of the time span added on each side
        :type pad: float
        :return: first and last date of the range
        :rtype: list
        """
        delta = pad * (xmax - xmin)
        return [xmin - delta, xmax + delta]

    @staticmethod
    def set_date_ticks(ax, xmin, xmax, n_dates, format_dates):
        """
        Set ticks evenly spaced in calendar time on a time axis, within its limits.

        :param ax: target axis
        :type ax: :class:`matplotlib.axes.Axes`
        :param xmin: date of the first tick
        :type xmin: :class:`pandas.Timestamp`
        :param xmax: date of the last tick
        :type xmax: :class:`pandas.Timestamp`
        :param n_dates: number of ticks. If None, they are chosen automatically
        :type n_dates: int
        :param format_dates: format of the dates. If None, it is the current one
        :type format_dates: str
        :return: None
        :rtype: None
        """
        if n_dates is None:
            ax.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=3, maxticks=7))
            return None
        # ticks out of the limits would widen the axis
        num_low, num_high = ax.get_xlim()
        num_start = max(mdates.date2num(xmin), num_low)
        num_end = min(mdates.date2num(xmax), num_high)
        if n_dates <= 1:
            ax.set_xticks([num_start])
        else:
            ax.set_xticks(np.linspace(num_start, num_end, n_dates))
        if format_dates is not None:
            ax.xaxis.set_major_formatter(mdates.DateFormatter(format_dates))
        return None

    @staticmethod
    def plot_series(data, ax, specs):
        """
        Draw a time series line (and optional fill) onto an existing axes.

        :param data: DataFrame containing the series to plot.
        :type data: :class:`pandas.DataFrame`
        :param ax: Target Matplotlib axes.
        :type ax: :class:`matplotlib.axes.Axes`
        :param specs: Plot specification dictionary (from ``view_specs``).
        :type specs: dict
        """
        if specs["fill"]:
            if specs["color_fill"] is None:
                specs["color_fill"] = specs["color"]
            lower = (data[specs["yvar"]].values * 0) + specs["ymin"]
            # Fill below the time series
            ax.fill_between(
                x=data[specs["xvar"]],
                y1=lower,
                y2=data[specs["yvar"]],
                color=specs["color_fill"],
                alpha=specs["alpha_fill"],
                step=(
                    specs["drawstyle"].split("-")[1]
                    if specs.get("drawstyle", False)
                    else None
                ),
                zorder=specs["zorder_data"],
                label=specs["data_label"],
                edgecolor="none",
            )

        if not specs["fill_only"]:

            if specs["fill"]:
                label = None
            else:
                label = specs["data_label"]

            ax.plot(
                data[specs["xvar"]],
                data[specs["yvar"]],
                linestyle=specs["linestyle"],
                marker=specs["marker"],
                color=specs["color"],
                alpha=specs["alpha"],
                linewidth=specs.get("linewidth", None),
                drawstyle=specs["drawstyle"],
                label=label,
                zorder=specs["zorder_data"],
            )

        # handle subtitle
        if specs["subtitle_data"] is not None:
            ax.set_title(specs["subtitle_data"], loc="left")

        # handle range
        if specs["range"] is not None:
            ax.set_ylim(specs["range"])

        # handle range x
        dates = data[specs["xvar"]]
        if specs["range_x"] is not None:
            ax.set_xlim(specs["range_x"])
        elif len(dates) > 0:
            ax.set_xlim(
                TimeSeries.get_range_x(
                    xmin=dates.min(), xmax=dates.max(), pad=specs["pad_x"]
                )
            )

        # handle dates
        if specs["n_dates"] is not None and len(dates) > 0:
            TimeSeries.set_date_ticks(
                ax=ax,
                xmin=dates.min(),
                xmax=dates.max(),
                n_dates=specs["n_dates"],
                format_dates=specs.get("format_dates", None),
            )

        if specs["data_legend"]:
            ax.legend(
                loc="upper right"
                # todo dev more options
            )

        # basic decorations
        ax.set_xlabel(specs["xlabel"])
        ax.set_ylabel(specs["ylabel"])

        return None

    @staticmethod
    def add_hour(df, hour=12, dt_field="datetime"):
        """
        Set the time component of a date-only datetime column to a fixed hour.

        :param df: DataFrame with a datetime column to modify.
        :type df: :class:`pandas.DataFrame`
        :param hour: Hour to set. Default is 12 (noon).
        :type hour: int
        :param dt_field: Name of the datetime column. Default is ``"datetime"``.
        :type dt_field: str
        :return: DataFrame with the datetime column updated.
        :rtype: :class:`pandas.DataFrame`
        """
        df[dt_field] = df[dt_field].dt.normalize() + pd.to_timedelta(hour, unit="h")
        return df

    @staticmethod
    def view_compare_times_series(
        ts_first, ts_second, specs, show=False, return_fig=False
    ):
        """
        Plot two ``TimeSeries`` objects together for visual comparison.

        Renders a three-panel figure -- the two series overlaid on a
        shared time axis, a horizontal histogram, and a CDF -- using
        ``ts_first``'s panel layout as the base and drawing ``ts_second``
        on top of it. Both series are shown with their own colors (taken
        from each object's ``view_specs["color"]``) and labeled with
        their respective ``name`` attributes; each series' mean is
        annotated on the CDF panel.

        :param ts_first: The first time series to plot. Its own
            ``view_specs`` supplies the base panel layout (axes,
            figure size, etc.); set ``ts_first.view_specs["color"]``
            before calling to control its plotted color.
        :type ts_first: TimeSeries
        :param ts_second: The second time series to plot on top of the
            first. Likewise, set ``ts_second.view_specs["color"]`` to
            control its color.
        :type ts_second: TimeSeries
        :param specs: Plot overrides applied to both series before
            plotting (merged into each series' ``view_specs``). Must
            include ``"title"``. If ``return_fig`` is ``False``, must
            also include ``"folder"`` and ``"filename"`` (used to build
            the output file path); ``"dpi"`` and ``"fig_format"`` are
            taken from ``ts_first.view_specs`` regardless of what is
            passed in ``specs``. Without ``"range"``, the y axis of
            all panels covers both series.
        :type specs: dict
        :param show: If ``return_fig`` is ``False``, whether to display
            the figure interactively in addition to saving it. Ignored
            if ``return_fig`` is ``True``.
        :type show: bool
        :param return_fig: If ``True``, return the Matplotlib
            :class:`~matplotlib.figure.Figure` instead of saving it to
            disk. Useful for inline display (e.g. in a notebook) or for
            further customization before saving.
        :type return_fig: bool

        :return: The :class:`~matplotlib.figure.Figure` if
            ``return_fig=True``, otherwise ``None`` (the figure is
            saved to ``"{folder}/{filename}.{fig_format}"``).
        :rtype: :class:`matplotlib.figure.Figure` or None

        .. note::

            Both input objects' ``view_specs`` are mutated in place by
            this method (colors, labels, layout, and the contents of
            ``specs`` are all written into
            ``ts_first.view_specs``/``ts_second.view_specs``). If you
            need the originals preserved, pass copies.

        :Example:

        >>> ts1.view_specs["color"] = "tab:blue"
        >>> ts2.view_specs["color"] = "tab:orange"
        >>> fig = TimeSeries.view_compare_times_series(
        ...     ts1, ts2, specs={"title": "Site A vs Site B"}, return_fig=True
        ... )
        """
        ts1 = ts_first
        ts2 = ts_second

        specs["layout"] = "mini"
        specs["data_legend"] = True
        specs["linestyle_mean"] = "dashed"
        specs["alpha_hist"] = 0.75
        specs["alpha_cdf"] = 1.0

        specs["dpi"] = ts_first.view_specs["dpi"]
        specs["fig_format"] = ts_first.view_specs["fig_format"]

        ts1.view_specs.update(specs)
        ts2.view_specs.update(specs)

        # shared range, so neither series is cut off
        range_y = specs.get("range")
        if range_y is None:
            vmin = min(ts1.var_min, ts2.var_min)
            vmax = max(ts1.var_max, ts2.var_max)
            margin = 0.05 * (vmax - vmin)
            range_y = [vmin - margin, vmax + margin]
        ts1.view_specs["range"] = range_y
        ts2.view_specs["range"] = range_y

        # shared time axis, from the first date to the last one of both
        xmin = min(ts1.data[ts1.dtfield].min(), ts2.data[ts2.dtfield].min())
        xmax = max(ts1.data[ts1.dtfield].max(), ts2.data[ts2.dtfield].max())
        range_x = specs.get("range_x")
        if range_x is None:
            range_x = TimeSeries.get_range_x(
                xmin=xmin, xmax=xmax, pad=ts1.view_specs["pad_x"]
            )
        ts1.view_specs["range_x"] = range_x
        ts2.view_specs["range_x"] = range_x

        # setup first series
        # ----------------------------------------------------------------
        ts1.view_specs["title"] = specs["title"]

        # colors are the same from data
        ts1.view_specs["color_hist"] = ts1.view_specs["color"]
        ts1.view_specs["color_cdf"] = ts1.view_specs["color"]
        ts1.view_specs["color_mean"] = ts1.view_specs["color"]

        ts2.view_specs["color"] = ts2.view_specs["color"]
        ts2.view_specs["color_hist"] = ts2.view_specs["color"]
        ts2.view_specs["color_cdf"] = ts2.view_specs["color"]
        ts2.view_specs["color_mean"] = ts2.view_specs["color"]

        # label is the name
        ts1.view_specs["data_label"] = ts1.name
        ts2.view_specs["data_label"] = ts2.name

        # hard coded specs
        ## ts1.view_specs['pad_mean'] = 2
        ## ts2.view_specs['pad_mean'] = 20

        # plot
        # ----------------------------------------------------------------
        fig = ts1.view(return_fig=True)

        axes = fig.get_axes()

        # plot series
        TimeSeries.plot_series(
            data=ts2.data, ax=axes[ts2.view_specs["ax_data"]], specs=ts2.view_specs
        )
        TimeSeries.set_date_ticks(
            ax=axes[ts2.view_specs["ax_data"]],
            xmin=xmin,
            xmax=xmax,
            n_dates=ts2.view_specs["n_dates"],
            format_dates=ts2.view_specs["format_dates"],
        )

        # plot hist
        df_clean = ts2.data.dropna()
        data = df_clean[ts2.varfield].values

        Univar.plot_histh(
            data=data, ax=axes[ts2.view_specs["ax_hist"]], specs=ts2.view_specs
        )

        # plot cdf
        Univar.plot_cdf(
            cdf_df=ts2.get_cdf_weibull(),
            ax=axes[ts2.view_specs["ax_cdf"]],
            specs=ts2.view_specs,
        )

        # the second series resets the y limits
        viewer.clear_xticks(axes=axes)

        # SHIP
        # ----------------------------------------------------------------

        viewer.set_layers(fig=fig)
        if return_fig:
            return fig
        else:
            # create path
            file_path = "{}/{}.{}".format(
                specs["folder"], specs["filename"], specs["fig_format"]
            )
            viewer.ship_fig(fig=fig, show=show, file_output=file_path, dpi=specs["dpi"])

    # Generator methods
    # -------------------------------------------------------------------
    @staticmethod
    def _get_steps_per_year(freq):
        """
        Get the number of time steps in a year for a frequency.

        :param freq: frequency alias
        :type freq: str
        :return: steps per year, a whole number when the steps follow the calendar
        :rtype: float
        """
        dates = pd.date_range(start="2000-01-01", periods=13, freq=freq)
        deltas = dates[1:] - dates[:-1]
        # fixed steps
        if deltas.nunique() == 1:
            return YEAR_DAYS / (deltas[0].total_seconds() / 86400)
        # calendar steps, counted over a full cycle of the leap years
        dates = pd.date_range(start="1700-01-01", end="2099-12-31", freq=freq)
        return len(dates) / 400

    def _get_generator_params(self, start, freq, n):
        r"""
        Convert ``generator_specs`` to the parameters of a given time step.

        .. math::

            \varphi = e^{-\Delta t / \tau},
            \qquad \sigma = s \sqrt{1 - \varphi^2}

        :param start: first date of the series
        :type start: :class:`pandas.Timestamp`
        :param freq: frequency alias
        :type freq: str
        :param n: number of steps
        :type n: int
        :return: parameters. See :func:`plans.stochastic.arma.fit_params`.
        :rtype: dict
        """
        specs = self.generator_specs
        period = TimeSeries._get_steps_per_year(freq=freq)
        step_days = YEAR_DAYS / period

        # memory in days to memory per step
        phi = 0.0
        if specs["memory_days"] > 0:
            phi = np.exp(-step_days / specs["memory_days"])

        # variables that accumulate over the step are given per day
        factor = step_days if self.agg == "sum" else 1.0
        baseline = factor * specs["baseline"]
        topline = factor * specs["topline"]
        m = _arma.shape_mean(power=specs["power"])

        return _arma.make_params(
            period=period,
            average=baseline + (topline - baseline) * m,
            n=n,
            cycle_change=factor * specs["change_per_year"],
            baseline=baseline,
            topline=topline,
            phase=((specs["peak_day"] - start.dayofyear) / step_days) % period,
            power=specs["power"],
            phi=phi,
            sigma=factor * specs["remainder_sd"] * np.sqrt(1 - phi**2),
        )

    def generate(self, start, end, freq=None, params=None, seed=None, inplace=False):
        """
        Generate a synthetic series with trend, a yearly cycle and AR(1) memory.

        Without ``params``, it uses the ``generator_specs`` attribute, which each child
        class sets for its own variable and which can be edited. These specs are in
        physical terms, so they apply to any time step:

        - ``baseline`` and ``topline``: lowest and highest points of the yearly cycle,
          at the middle of the record. Per day if the object aggregates by sum.
        - ``peak_day``: day of the year of the peak.
        - ``power``: shape of the cycle. See :func:`plans.stochastic.arma.cycle_shape`.
        - ``memory_days``: time for the memory of the remainder to decay by a factor of e.
        - ``remainder_sd``: standard deviation of the remainder. Per day if aggregated by sum.
        - ``change_per_year``: change of the trend per year. Per day if aggregated by sum.

        Values below ``generator_floor`` are pruned to it, if it is set.

        .. warning::

            Default specs are plausible values for examples, not climatology. There is
            no daily cycle at any time step, since sub-daily series are meant to come
            from downscaling a daily series.

        :param start: first date
        :type start: str or :class:`pandas.Timestamp`
        :param end: last date
        :type end: str or :class:`pandas.Timestamp`
        :param freq: frequency alias. By default, it is the one in ``params`` or ``D``.
        :type freq: str
        :param params: parameters, usually from :meth:`fit`. Those from :meth:`fit` follow
            the calendar, so the cycle and trend carry over to any ``start``.
        :type params: dict
        :param seed: random seed
        :type seed: int
        :param inplace: If True, sets the data of this object. Default value = False
        :type inplace: bool
        :return: generated data if inplace is False, otherwise None.
        :rtype: :class:`pandas.DataFrame` or None
        """
        # handle frequency
        params_freq = None if params is None else params.get("freq")
        if freq is None:
            freq = "D" if params_freq is None else params_freq
        elif params_freq is not None:
            # memory and noise in parameters are per step
            if pd.tseries.frequencies.to_offset(freq) != (
                pd.tseries.frequencies.to_offset(params_freq)
            ):
                raise ValueError(f"params were fitted for freq '{params_freq}'")

        period = TimeSeries._get_steps_per_year(freq=freq)
        if period < 2:
            raise ValueError("freq must have at least 2 steps per year")

        dates = pd.date_range(start=start, end=end, freq=freq)
        if len(dates) == 0:
            raise ValueError(f"No dates between {start} and {end} for freq '{freq}'")

        # handle parameters
        if params is None:
            params = self._get_generator_params(start=dates[0], freq=freq, n=len(dates))
        else:
            params = TimeSeries._move_params(params=params, start=dates[0])

        values = _arma.build(params=params, n=len(dates), seed=seed)
        if self.generator_floor is not None:
            values = np.clip(values, a_min=self.generator_floor, a_max=None)

        df = pd.DataFrame({self.dtfield: dates, self.varfield: values})

        if inplace:
            self.set_data(
                input_df=df, input_dtfield=self.dtfield, input_varfield=self.varfield
            )
            return None
        return df

    @staticmethod
    def _move_params(params, start):
        """
        Move step 0 of the parameters from their origin, if any, to a new start.

        :param params: parameters
        :type params: dict
        :param start: new first date
        :type start: :class:`pandas.Timestamp`
        :return: parameters that apply from the new start
        :rtype: dict
        """
        if "origin" not in params:
            return params
        delta = start - pd.Timestamp(params["origin"])
        shift = (delta.total_seconds() / 86400) / (YEAR_DAYS / params["period"])
        return dict(
            params,
            start=params["start"] + params["slope"] * shift,
            phase=(params["phase"] - shift) % params["period"],
        )

    def decompose(self, params=None):
        """
        Split the data into trend, cycle, remainder and shocks. The data is not
        changed. The remainder holds the memory and the shocks, so that
        ``trend + cycle + remainder`` rebuilds the data.

        :param params: parameters. By default, they come from :meth:`fit`.
        :type params: dict
        :return: dates and components, in columns ``trend``, ``cycle``, ``remainder``
            and ``shocks``
        :rtype: :class:`pandas.DataFrame`
        """
        if params is None:
            params = self.fit()
        df = self.data.sort_values(by=self.dtfield)
        if df[self.varfield].isna().any():
            raise ValueError("There are gaps in the data. Fill them to decompose")
        params = TimeSeries._move_params(params=params, start=df[self.dtfield].iloc[0])
        dc_parts = _arma.decompose(x=df[self.varfield].values, params=params)
        return pd.DataFrame({self.dtfield: df[self.dtfield].values, **dc_parts})

    def fit(self):
        """
        Fit the generator parameters to the data. The data is not changed.

        The time step comes from the timestamps, so the data must be regular and
        without gaps. Use :meth:`standardize` and :meth:`interpolate_gaps` first if needed.

        :return: parameters from :func:`plans.stochastic.arma.fit_params`, and also
            ``origin`` and ``freq``, so :meth:`generate` can use them from any date.
        :rtype: dict
        """
        if self.data is None:
            raise ValueError("There is no data to fit")

        df = self.data.dropna(subset=[self.varfield]).sort_values(by=self.dtfield)
        deltas = df[self.dtfield].diff().dropna()
        if len(deltas) == 0:
            raise ValueError("There is not enough data to fit")
        step = deltas.mode().iloc[0]

        # months vary in length, while all other steps must be constant
        s_error = "Timestamps are not regular. Check for gaps or use standardize()"
        if 27 < step.total_seconds() / 86400 < 32:
            freq = "MS"
            if deltas.max() > pd.Timedelta(days=31):
                raise ValueError(s_error)
        else:
            freq = pd.tseries.frequencies.to_offset(step).freqstr
            # whole days use the same alias as generate()
            n_days = step.total_seconds() / 86400
            if n_days == int(n_days):
                freq = "D" if n_days == 1 else f"{int(n_days)}D"
            if (deltas != step).any():
                raise ValueError(s_error)

        period = TimeSeries._get_steps_per_year(freq=freq)
        if period < 2:
            raise ValueError("Data must have at least 2 steps per year")

        params = _arma.fit_params(x=df[self.varfield].values, period=period)
        params["origin"] = str(df[self.dtfield].iloc[0])
        params["freq"] = freq
        return params


# Chronological classes - collections
# -----------------------------------------------------------------------


class TimeSeriesCollection(Collection):
    """
    A collection of time series objects with associated metadata.

    The ``TimeSeriesCollection`` class extends the ``Collection`` class and
    is designed to handle time series data. It can be miscellaneous datasets.

    .. note::

        See ``TimeSeriesCluster`` for managing time series of the same variable


    """

    # stacked layouts: grid rows of an average panel, rows between panels (a
    # title stays closer to its own panel), and height of a row in mm
    PANEL_ROWS = 5
    PANEL_GAP_ROWS = 2
    ROW_HEIGHT = 5

    # Dunder methods
    # -------------------------------------------------------------------
    def __init__(self, name="myTSCollection", base_object=None):
        # If base_object is not provided, create a default TimeSeries object
        if base_object is None:
            base_object = TimeSeries

        # Call the constructor of the parent class (TimeSeries)
        super().__init__(base_object=base_object, name=name)

        # Set up date fields and special attributes in the catalog
        self.catalog["start"] = pd.to_datetime(
            self.catalog["start"], format="%Y-%m0-%d %H:%M:%S"
        )
        self.catalog["end"] = pd.to_datetime(
            self.catalog["end"], format="%Y-%m0-%d %H:%M:%S"
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

        # Named figure layouts (mirrors the TimeSeries/Univar pattern: a
        # fine grid with deliberate margin bands left/right/top/bottom for
        # labels, ticks, and the figure suptitle -- unlike a coarse grid
        # where every row/column is claimed by a panel, leaving no room for
        # long y-tick labels (series names) or title text).
        self.layouts = {
            "full": {  # gantt + overlap + prevalence
                "ncols": 34,
                "nrows": 16,
                "width": viewer.FIG_SIZES["L"]["w"],
                "height": viewer.FIG_SIZES["L"]["h"],
            },
            "simple": {  # gantt + overlap only
                "ncols": 34,
                "nrows": 16,
                "width": viewer.FIG_SIZES["M"]["w"],
                "height": viewer.FIG_SIZES["M"]["h"],
            },
            "default": {
                "ncols": 34,
                "nrows": 16,
                "width": viewer.FIG_SIZES["L"]["w"],
                "height": viewer.FIG_SIZES["L"]["h"],
            },
            # one panel per row. Rows and height come from the panels
            "stacked": {  # series + histograms + CDFs
                "ncols": 34,
                "width": viewer.FIG_SIZES["L"]["w"],
            },
            "stacked-simple": {  # series only
                "ncols": 34,
                "width": viewer.FIG_SIZES["L"]["w"],
            },
        }

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
        self.start = self.catalog["start"].min()
        self.end = self.catalog["end"].max()
        self.var_min = self.catalog["variable_min"].min()
        self.var_max = self.catalog["variable_max"].max()

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

    def merge_data(self, standard=False):
        """
        Merge data from every series in the collection into one DataFrame,
        aligned by an outer join on the datetime field.

        :param standard: If True, merge the data of each series on its regular
            grid, so missing timestamps show up. The series are not changed.
        :type standard: bool
        :return: A merged DataFrame with one datetime column and one value
            column per series (named ``"{variable_field}_{alias}"``).
        :rtype: pandas.DataFrame

        **Notes**

        This is a passive alignment: the datetime axis is the union of every
        series' own timestamps, nothing more. It does **not** assume, pick,
        or resample onto any single frequency -- a collection is explicitly
        allowed to mix a daily and an hourly series, and each keeps its own
        native timestamps here. A daily series simply has no row (NaN) at
        the hourly series' intermediate timestamps, and vice versa; nothing
        is invented and nothing is thrown away. This also means the result
        is read-only with respect to the members: it is a view for
        reporting/analysis, and is never written back into any series' own
        ``.data`` (see :meth:`standardize`).

        """
        # Ensure catalog is updated with details
        self.update(details=True)

        df = None
        for i in range(len(self.catalog)):
            # Get attributes from the catalog
            name = self.catalog[self.field_name].values[i]
            alias = self.catalog[self.field_alias].values[i]
            varfield = self.catalog["variable_field"].values[i]
            dtfield = self.catalog["datetime_field"].values[i]

            ts = self.collection[name]
            df_right = ts._get_standard_data(cut=True) if standard else ts.data
            df_right = df_right[[dtfield, varfield]].copy()
            df_right = df_right.rename(
                columns={
                    varfield: "{}_{}".format(varfield, alias),
                    dtfield: self.dtfield,
                }
            )

            if df is None:
                df = df_right
            else:
                # Outer join: keep every timestamp from every series, and
                # let each series be NaN wherever it has no record of its
                # own -- no shared grid is assumed or manufactured.
                df = pd.merge(how="outer", left=df, right=df_right, on=self.dtfield)

        df = df.sort_values(by=self.dtfield).reset_index(drop=True)
        return df

    def standardize(self):
        """
        Standardize every series in the collection, independently.

        :Notes:

        This is deliberately just a batched per-series operation: each
        member calls its own :meth:`TimeSeries.standardize` (regularize onto
        *its own* native time step), and its own epoch stats are refreshed.
        Gaps stay as they are. Filling them is a separate decision, see
        :meth:`TimeSeries.interpolate_gaps`.

        No cross-series merge happens here, and no series' ``.data`` is
        touched by any other series. A collection is explicitly allowed to
        mix frequencies (e.g. hourly temperature alongside daily rainfall),
        so there is no single shared grid to standardize *onto* -- that
        would mean picking one series' frequency as authoritative and
        silently resampling everyone else onto it, corrupting their native
        resolution. Cross-series alignment for reporting/analysis is a
        separate, non-destructive concern: see :meth:`merge_data` and
        :meth:`get_epochs`.

        """
        for name in self.collection:
            self.collection[name].standardize()
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
        df = self.merge_data(standard=True)

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
        df_aux[self.overfield] = df_aux[self.overfield].replace(0, np.nan)

        # Create a new TimeSeries instance for epoch calculation
        ts_aux = TimeSeries()
        ts_aux.set_data(
            input_df=df_aux,
            input_varfield=self.overfield,
            input_dtfield=self.dtfield,
            dropnan=False,
        )

        # Calculate epochs on the merged grid and update the original DataFrame
        df_labels = ts_aux._label_epochs(df=ts_aux.data)
        df[ts_aux.epochs_id_field] = df_labels[ts_aux.epochs_id_field].values

        return df

    # View internal methods
    # -------------------------------------------------------------------
    def _set_view_specs(self):
        """
        Set view specifications for the collection dashboard plot
        (Gantt chart of per-series epochs + cross-series overlap +
        series prevalence). Mirrors the ``TimeSeries``/``Univar`` pattern:
        everything the plot needs lives in ``self.view_specs`` and is
        consumed by :meth:`_get_fig_specs` / :meth:`_plot`.
        """
        self.view_specs = {
            # layout: "full" (gantt + overlap + prevalence),
            # "simple" (gantt + overlap only), "stacked" (panels of series,
            # histograms and CDFs) or "stacked-simple" (panels of series)
            "layout": "full",
            "style": "wien",
            # titles
            "title": "{} | {}".format(self.name_object, self.name),
            "gantt": "Gantt chart (epochs)",
            "over": "Overlapping data",
            "prev": "Series prevalence",
            # axis labels
            "xlabel": "Date",
            "ylabel_over": "%",
            "xlabel_prev": "%",
            # data controls
            "usealias": False,
            "n_dates": 5,
            "format_dates": "%Y-%m-%d",
            "xtick_rotation": 0,
            # styling
            "color_over": "tab:blue",
            "alpha_over": 0.4,
            "color_prev": "tab:gray",
            "gantt_linewidth": 6,  # max width, shrinks to fit many series
            # above this many series, per-series labels are hidden
            "n_series_max": 10,
            # ranges (None = auto from self.start/self.end and data)
            "xmin": None,
            "xmax": None,
            "ymin": None,
            "ymax": None,
            "pad_x": 0.05,  # share of the time span added on each side, if auto
            # export
            "folder": "./output",
            "filename": None,
            "suff": "",
            "dpi": 300,
            "fig_format": "jpg",
            # series layouts (registered by same-variable subclasses)
            "series": "Series",
            "subtitle_hist": "Histogram",
            "subtitle_cdf": "CDF",
            "ylabel": None,
            "range": None,  # common y range, None is auto
            "cmap_series": "tab10",  # None uses each series color
            "linewidth": 0.8,
            "alpha_hist": 0.4,
            "histtype": "bar",  # "step" draws outlines only
            "bins": 30,  # common bins for all histograms
            "plot_mean": True,
            "legend": True,
            # background series (large collections or highlight mode)
            "highlight": None,  # list of names drawn in color
            "plot_background": True,  # False hides background lines
            "color_background": "silver",
            "linewidth_background": 0.5,
            "alpha_background": 0.6,
            "alpha_hist_background": 0.1,
            # stacked layouts
            "panels": None,  # list of lists of names. None is one series per panel
            "panel_heights": None,  # relative heights, like [3, 1]. None is equal
        }
        return None

    def _set_series_layouts(self):
        """
        Register the ``series`` layouts. Meant for same-variable subclasses only,
        since series of different variables can not share axes.
        """
        self.layouts.update(
            {
                "series": {  # series + histograms + CDFs
                    "ncols": 34,
                    "nrows": 12,
                    "width": viewer.FIG_SIZES["L"]["w"],
                    "height": viewer.FIG_SIZES["L"]["h"],
                },
                "series-simple": {  # series only
                    "ncols": 34,
                    "nrows": 16,
                    "width": viewer.FIG_SIZES["L2"]["w"],
                    "height": viewer.FIG_SIZES["L2"]["h"],
                },
            }
        )
        return None

    def _get_fig_specs(self):
        """
        Merge ``view_specs`` with the chosen named ``layout``'s sizing and
        with the shared grid defaults (:data:`viewer.GRID_SPECS`).
        """
        specs = self.view_specs.copy()

        layout = specs["layout"]
        if layout not in self.layouts:
            raise ValueError(
                f"Unknown layout '{layout}'. Options: {list(self.layouts.keys())}"
            )
        specs_aux = self.layouts[layout].copy()

        specs.update(specs_aux)
        specs.update(viewer.GRID_SPECS)

        if layout in ["stacked", "stacked-simple"]:
            specs["panels"] = self._get_panels(specs=specs)
            specs["panel_rows"] = self._get_panel_rows(specs=specs)
            # title and header rows + panel rows + rows between panels + date row
            n_gaps = (len(specs["panels"]) - 1) * TimeSeriesCollection.PANEL_GAP_ROWS
            n_rows = 2 + sum(specs["panel_rows"]) + n_gaps + 1
            specs["nrows"] = n_rows
            specs["height"] = n_rows * TimeSeriesCollection.ROW_HEIGHT

        return specs

    def _get_panels(self, specs):
        """
        Get the names of series in each panel, checking them. Series in a panel
        share an axis, so they must have the same units.

        :param specs: plot specification dictionary
        :type specs: dict
        :return: names of series, for each panel
        :rtype: list
        """
        ls_panels = specs["panels"]
        if ls_panels is None:
            ls_panels = [[n] for n in self.catalog[self.field_name].values]
        if len(ls_panels) == 0:
            raise ValueError("No panels to view. Set the series first")

        for ls_names in ls_panels:
            if len(ls_names) == 0:
                raise ValueError("Empty panel in view_specs['panels']")
            for name in ls_names:
                if name not in self.collection:
                    raise ValueError(
                        f"Unknown series '{name}'. "
                        f"Options: {list(self.collection.keys())}"
                    )
            ls_units = [self.collection[n].units for n in ls_names]
            if len(set(ls_units)) > 1:
                raise ValueError(
                    f"Series of a panel must have the same units. "
                    f"Got {dict(zip(ls_names, ls_units))}"
                )

        ls_heights = specs["panel_heights"]
        if ls_heights is not None:
            if len(ls_heights) != len(ls_panels):
                raise ValueError(
                    f"Got {len(ls_heights)} panel heights "
                    f"for {len(ls_panels)} panels"
                )
            if min(ls_heights) <= 0:
                raise ValueError("Panel heights must be positive")
        return ls_panels

    def _get_panel_rows(self, specs):
        """
        Get the grid rows of each panel, by share of the total height.

        :param specs: plot specification dictionary
        :type specs: dict
        :return: number of rows, for each panel
        :rtype: list
        """
        n_panels = len(specs["panels"])
        ls_heights = specs["panel_heights"] or [1] * n_panels
        n_rows = TimeSeriesCollection.PANEL_ROWS * n_panels
        # at least two rows, so a small panel still shows its y axis
        return [max(2, round(n_rows * h / sum(ls_heights))) for h in ls_heights]

    def _build_axes(self, fig, gs, specs):
        """Add the dashboard's Axes to ``fig`` according to ``layout``."""
        if specs["layout"] in ["stacked", "stacked-simple"]:
            is_simple = specs["layout"] == "stacked-simple"
            ax_series = None
            ax_cdf = None
            i_row = 2
            for n_rows in specs["panel_rows"]:
                rows = slice(i_row, i_row + n_rows)
                # series and CDFs share their x axis across panels
                ax = fig.add_subplot(
                    gs[rows, 3:] if is_simple else gs[rows, 3:20], sharex=ax_series
                )
                ax_series = ax if ax_series is None else ax_series
                if not is_simple:
                    fig.add_subplot(gs[rows, 22:27])
                    ax = fig.add_subplot(gs[rows, 29:], sharex=ax_cdf)
                    ax_cdf = ax if ax_cdf is None else ax_cdf
                i_row = i_row + n_rows + TimeSeriesCollection.PANEL_GAP_ROWS
        elif specs["layout"] == "series":
            fig.add_subplot(gs[2:10, 3:20])  # 0: series
            fig.add_subplot(gs[2:10, 22:27])  # 1: histograms
            fig.add_subplot(gs[2:10, 29:])  # 2: CDFs
        elif specs["layout"] == "series-simple":
            # one row below the title, for the legend
            fig.add_subplot(gs[3:14, 4:])
        elif specs["layout"] == "simple":
            fig.add_subplot(gs[2:7, 4:32])  # gantt
            fig.add_subplot(gs[10:15, 4:32])  # overlap
        else:  # "full" / default
            fig.add_subplot(gs[2:7, 4:24])  # gantt
            fig.add_subplot(gs[10:15, 4:24])  # overlap
            fig.add_subplot(gs[2:7, 27:33])  # prevalence
        return fig

    def _plot(self, fig, gs, specs):
        """
        Draw the Gantt / overlap / prevalence panels onto ``fig`` using
        proper Axes objects (``ax.set_xlim(...)`` etc.) rather than
        stateful ``plt.*`` calls, so this composes safely with other plots
        and is safe to call more than once per session.
        """
        # series layouts
        if specs["layout"] in ["series", "series-simple"]:
            fig = self._build_axes(fig=fig, gs=gs, specs=specs)
            self._plot_series(axes=fig.get_axes(), specs=specs)
            self._clear_title(fig=fig, title=fig.suptitle(specs["title"]))
            return fig

        if specs["layout"] in ["stacked", "stacked-simple"]:
            fig = self._build_axes(fig=fig, gs=gs, specs=specs)
            self._plot_stacked(axes=fig.get_axes(), specs=specs)
            fig.suptitle(specs["title"])
            return fig

        fig = self._build_axes(fig=fig, gs=gs, specs=specs)
        axes = fig.get_axes()

        usealias = specs["usealias"]
        dict_alias = dict()
        if usealias:
            _names = self.catalog[self.field_name].values
            _alias = self.catalog[self.field_alias].values
            for i in range(len(self.catalog)):
                dict_alias[_names[i]] = _alias[i]

        # pre-processing: each series' TEMPORAL COVERAGE -- its valid
        # (non-gap) record count, divided by how many of *its own*
        # resolution's steps fit across the *collection's* full time
        # range (self.start to self.end), not the series' own span. A
        # series with zero gaps still reads under 100% if it only covers
        # part of the collection's overall range (e.g. an hourly sensor
        # running for just the first half of a year-long collection reads
        # ~50%, not ~100%), and every series is comparable on the same
        # 0-100% scale regardless of its own frequency.
        local_epochs_df = self.merge_local_epochs()
        coverage_rows = []
        for name in self.collection:
            ts = self.collection[name]
            valid_n = local_epochs_df.loc[
                local_epochs_df[self.field_name] == name, "n_epoch"
            ].sum()
            expected_n = len(
                pd.date_range(start=self.start, end=self.end, freq=ts.dtfreq)
            )
            pct = 100 * valid_n / expected_n if expected_n > 0 else 0.0
            coverage_rows.append({self.field_name: name, "coverage_pct": pct})
        agg_df = (
            pd.DataFrame(coverage_rows)
            .sort_values(by="coverage_pct", ascending=True)
            .reset_index(drop=True)
        )
        names = agg_df[self.field_name].values
        labels = [dict_alias[name] for name in names] if usealias else names
        preval = agg_df["coverage_pct"].values
        heights = np.linspace(0, 1, len(names) + 1)
        heights = heights[: len(names)] + ((heights[1] - heights[0]) / 2)

        # cross-series overlap
        epochs_df = self.get_epochs()

        xmin, xmax, range_x = self._get_range_x(specs=specs)

        # large collections drop per-series labels
        n_series = len(names)
        is_large = n_series > specs["n_series_max"]

        # --- Gantt chart ---
        ax_gantt = axes[0]
        ax_gantt.set_title(specs["gantt"], loc="left")
        # fit line width to row height (points), so rows never overlap
        row_pt = ax_gantt.get_window_extent().height * 72 / fig.dpi / n_series
        gantt_linewidth = min(specs["gantt_linewidth"], 0.7 * row_pt)
        for i in range(len(names)):
            name = names[i]
            df_aux = local_epochs_df.query("{} == '{}'".format(self.field_name, name))
            for j in range(len(df_aux)):
                x_time = [df_aux["start"].values[j], df_aux["end"].values[j]]
                y_height = [heights[i], heights[i]]
                ax_gantt.plot(
                    x_time,
                    y_height,
                    color=df_aux["color"].values[j],
                    linewidth=gantt_linewidth,
                    solid_capstyle="butt",
                )
        ax_gantt.set_ylim(0, 1)
        ax_gantt.set_xlim(range_x)
        if is_large:
            ax_gantt.set_yticks([])
            ax_gantt.set_ylabel("{} series".format(n_series))
        else:
            ax_gantt.set_yticks(heights, labels)
        ax_gantt.set_xlabel(specs["xlabel"])
        TimeSeries.set_date_ticks(
            ax=ax_gantt,
            xmin=xmin,
            xmax=xmax,
            n_dates=specs["n_dates"],
            format_dates=specs["format_dates"],
        )
        ax_gantt.tick_params(axis="x", labelrotation=specs["xtick_rotation"])
        ax_gantt.grid(axis="y")

        # --- Overlapping chart ---
        ax_over = axes[1]
        ax_over.set_title(specs["over"], loc="left")
        ax_over.plot(
            epochs_df[self.dtfield],
            100 * epochs_df[self.overfield],
            color=specs["color_over"],
        )
        ax_over.fill_between(
            epochs_df[self.dtfield],
            100 * epochs_df[self.overfield],
            color=specs["color_over"],
            alpha=specs["alpha_over"],
        )
        ymin = specs["ymin"] if specs["ymin"] is not None else -5
        ymax = specs["ymax"] if specs["ymax"] is not None else 105
        ax_over.set_ylim(ymin, ymax)
        ax_over.set_xlim(range_x)
        ax_over.set_xlabel(specs["xlabel"])
        TimeSeries.set_date_ticks(
            ax=ax_over,
            xmin=xmin,
            xmax=xmax,
            n_dates=specs["n_dates"],
            format_dates=specs["format_dates"],
        )
        ax_over.tick_params(axis="x", labelrotation=specs["xtick_rotation"])
        ax_over.set_ylabel(specs["ylabel_over"])

        # --- Prevalence chart (only in the "full" layout) ---
        if len(axes) > 2:
            ax_prev = axes[2]
            ax_prev.set_title(specs["prev"], loc="left")
            # rows aligned with the gantt chart
            ax_prev.barh(
                heights,
                preval,
                height=0.8 / n_series,
                color=specs["color_prev"],
            )
            ax_prev.set_ylim(0, 1)
            if is_large:
                ax_prev.set_yticks([])
            else:
                # percentages as tick labels (names read across from the gantt)
                ax_prev.set_yticks(heights, ["{:.1f}%".format(p) for p in preval])
            ax_prev.set_xlim(0, 100)
            ax_prev.grid(axis="x")
            ax_prev.set_xlabel(specs["xlabel_prev"])

        fig.suptitle(specs["title"])
        return fig

    def _get_range_x(self, specs):
        """
        Get the time axis: from the first date to the last one of all series,
        with a padding on the sides not set by ``xmin`` and ``xmax``.

        :param specs: plot specification dictionary
        :type specs: dict
        :return: first and last tick, and the range of the axis
        :rtype: tuple
        """
        xmin = specs["xmin"] if specs["xmin"] is not None else self.start
        xmax = specs["xmax"] if specs["xmax"] is not None else self.end
        range_x = TimeSeries.get_range_x(xmin=xmin, xmax=xmax, pad=specs["pad_x"])
        if specs["xmin"] is not None:
            range_x[0] = xmin
        if specs["xmax"] is not None:
            range_x[1] = xmax
        return xmin, xmax, range_x

    def _get_labels(self, specs):
        """
        Get series labels (names or aliases), in catalog order.
        """
        field = self.field_alias if specs["usealias"] else self.field_name
        return list(self.catalog[field].values)

    def _plot_series(self, axes, specs, extra=None, force_background=False):
        """
        Plot all series overlaid: series, and (if axes are given) horizontal
        histograms and CDFs. Reuses the single ``TimeSeries`` plotters.

        Series in ``highlight`` are drawn in color on top of the others, drawn
        in background style. Above ``n_series_max`` series without highlights,
        all series are background. With ``plot_background`` off, background
        series leave the series panel, but stay in the histograms and CDFs.

        Layers, from the bottom: background, bands (from the ensemble), extras
        and members in color.

        :param axes: axes to plot on (1 or 3)
        :type axes: list
        :param specs: plot specification dictionary
        :type specs: dict
        :param extra: [optional] foreground series that are not members
            (e.g., ensemble reducers)
        :type extra: list
        :param force_background: option to draw all non-highlighted members
            in background style
        :type force_background: bool
        :return: None
        :rtype: None
        """
        ls_names = list(self.catalog[self.field_name].values)
        dc_labels = dict(zip(ls_names, self._get_labels(specs=specs)))
        ls_extra = extra if extra is not None else []

        # FOREGROUND AND BACKGROUND
        # -------------------------------------------------------------------
        ls_highlight = [n for n in (specs["highlight"] or []) if n in ls_names]
        if len(ls_highlight) > 0:
            ls_fore = ls_highlight
        elif force_background or len(ls_names) > specs["n_series_max"]:
            ls_fore = []
        else:
            ls_fore = ls_names
        # (series, label, zorder): background first, extras last
        ls_items = [
            (self.collection[n], dc_labels[n], 1) for n in ls_names if n not in ls_fore
        ]
        ls_items += [(self.collection[n], dc_labels[n], 4) for n in ls_fore]
        ls_items += [(ts, ts.name, 3) for ts in ls_extra]
        n_fore = len(ls_fore) + len(ls_extra)
        if specs["cmap_series"] is not None and n_fore > 0:
            cmap = viewer.get_discrete_cmap(
                n_classes=n_fore, base_cmap_name=specs["cmap_series"]
            )

        # COMMON RANGES
        # -------------------------------------------------------------------
        xmin, xmax, range_x = self._get_range_x(specs=specs)
        range_y = specs["range"]
        if range_y is None:
            vmin = np.nanmin(
                [
                    self.collection[n].data[self.collection[n].varfield].min()
                    for n in ls_names
                ]
            )
            vmax = np.nanmax(
                [
                    self.collection[n].data[self.collection[n].varfield].max()
                    for n in ls_names
                ]
            )
            margin = 0.05 * (vmax - vmin)
            range_y = [vmin - margin, vmax + margin]
        # common bin edges, so histograms are comparable
        vct_bins = np.linspace(range_y[0], range_y[1], specs["bins"] + 1)

        ylabel = specs["ylabel"]
        if ylabel is None:
            ylabel = "{} ({})".format(self.varname, self.catalog["units"].values[0])

        # PLOT EACH SERIES
        # -------------------------------------------------------------------
        hist_max = 0
        i_fore = 0
        for i, (ts, label, zorder) in enumerate(ls_items):
            is_fore = zorder > 1
            if not is_fore:
                color = specs["color_background"]
            elif specs["cmap_series"] is None:
                color = ts.color
            else:
                color = cmap(i_fore)
            i_fore = i_fore + 1 if is_fore else i_fore

            # series specs from the single series, with cluster overrides
            sp = ts.view_specs.copy()
            sp.update(
                {
                    "color": color,
                    "color_hist": color,
                    "color_cdf": color,
                    "color_mean": color,
                    "data_label": label if is_fore else None,
                    "data_legend": False,
                    "linewidth": specs["linewidth"],
                    "range": range_y,
                    "range_x": range_x,
                    "n_dates": None,
                    "xlabel": specs["xlabel"],
                    "ylabel": ylabel,
                    # subtitles only once
                    "subtitle_data": specs["series"] if i == 0 else None,
                    "subtitle_hist": specs["subtitle_hist"] if i == 0 else None,
                    "subtitle_cdf": specs["subtitle_cdf"] if i == 0 else None,
                    # histograms
                    "bins": vct_bins,
                    "bins_density": False,
                    "alpha_hist": specs["alpha_hist"],
                    "histtype": specs["histtype"],
                    "alpha_cdf": 1,
                    # mean lines without labels
                    "plot_mean": specs["plot_mean"],
                    "plot_mean_label": False,
                    "linestyle_mean": "dashed",
                    "zorder_data": zorder,
                    "zorder_histh": zorder,
                    "zorder_cdf": zorder,
                }
            )
            if not is_fore:
                sp.update(
                    {
                        "linewidth": specs["linewidth_background"],
                        "alpha": specs["alpha_background"],
                        "alpha_hist": specs["alpha_hist_background"],
                        "alpha_cdf": specs["alpha_background"],
                        "plot_mean": False,
                    }
                )
            # no rows: the panel is still set up, but without the line
            is_hidden = not is_fore and not specs["plot_background"]
            df_series = ts.data.iloc[:0] if is_hidden else ts.data
            TimeSeries.plot_series(data=df_series, ax=axes[0], specs=sp)

            if len(axes) > 1:
                vct_data = ts.data[ts.varfield].dropna().values
                h = Univar.plot_histh(data=vct_data, ax=axes[1], specs=sp)
                hist_max = max(hist_max, np.max(h[0]))
                Univar.plot_cdf(cdf_df=ts.get_cdf_weibull(), ax=axes[2], specs=sp)

        # DECORATIONS
        # -------------------------------------------------------------------
        TimeSeries.set_date_ticks(
            ax=axes[0],
            xmin=xmin,
            xmax=xmax,
            n_dates=specs["n_dates"],
            format_dates=specs["format_dates"],
        )
        if len(axes) > 1:
            # histograms share the series axis
            Univar.set_hist_xaxis(ax=axes[1], hist_max=hist_max)

        viewer.clear_xticks(axes=axes)
        self._set_series_legend(axes=axes, specs=specs)
        return None

    def _set_series_legend(self, axes, specs):
        """
        Set the legend of labeled (foreground) artists of the series panel.
        """
        _, ls_labels = axes[0].get_legend_handles_labels()
        if not specs["legend"] or len(ls_labels) == 0:
            return None
        # above the series panel, beside its title. Fewer columns if too wide
        x_title = axes[0]._left_title.get_window_extent().x1
        for ncol in range(len(ls_labels), 0, -1):
            legend = axes[0].legend(
                loc="lower right",
                bbox_to_anchor=(1, 1),
                ncol=ncol,
                fontsize=7,
                frameon=False,
                handlelength=1.5,
                columnspacing=1,
            )
            if legend.get_window_extent().x0 > x_title:
                break
        return None

    def _clear_title(self, fig, title):
        """
        Lower the top of all panels if legend rows reach the figure title.

        :param fig: figure with the panels, the first one having the legend
        :type fig: :class:`matplotlib.figure.Figure`
        :param title: figure title
        :type title: :class:`matplotlib.text.Text`
        :return: None
        :rtype: None
        """
        axes = fig.get_axes()
        legend = axes[0].get_legend()
        if legend is None:
            return None
        overlap = legend.get_window_extent().y1 - title.get_window_extent().y0
        if overlap > 0:
            for ax in axes:
                box = ax.get_position()
                height = box.height - overlap / fig.bbox.height
                ax.set_position([box.x0, box.y0, box.width, height])
        return None

    def _plot_stacked(self, axes, specs):
        """
        Plot series on stacked panels with a shared time axis, and (if axes are
        given) their histograms and CDFs. A lone series looks as in its own
        view, from its ``view_specs``. Series sharing a panel have overlaid
        histograms and CDFs in the color of the series. Colors repeated in a
        panel are replaced, and the y range covers all series of the panel.

        :param axes: axes to plot on, by panel: series, or series, histogram and CDF
        :type axes: list
        :param specs: plot specification dictionary
        :type specs: dict
        :return: None
        :rtype: None
        """
        dc_labels = dict(
            zip(self.catalog[self.field_name].values, self._get_labels(specs=specs))
        )
        xmin, xmax, range_x = self._get_range_x(specs=specs)
        n_panels = len(specs["panels"])
        n_axes = len(axes) // n_panels

        for i, ls_names in enumerate(specs["panels"]):
            ax_series, *ls_lateral = axes[i * n_axes : (i + 1) * n_axes]
            is_single = len(ls_names) == 1
            is_last = i == n_panels - 1
            ls_series = [self.collection[n] for n in ls_names]
            ls_colors = self._get_panel_colors(ls_series=ls_series, specs=specs)

            # y range and label common to the panel
            ls_ranges = [ts.view_specs["range"] for ts in ls_series]
            range_y = [min(r[0] for r in ls_ranges), max(r[1] for r in ls_ranges)]
            vct_bins = np.linspace(range_y[0], range_y[1], specs["bins"] + 1)
            s_units = ls_series[0].units
            ylabel = s_units
            if len(set(ts.varname for ts in ls_series)) == 1:
                ylabel = "{} ({})".format(ls_series[0].varname, s_units)

            hist_max = 0
            for name, ts, color in zip(ls_names, ls_series, ls_colors):
                sp = ts.view_specs.copy()
                sp.update(
                    {
                        "color": color,
                        "data_label": dc_labels[name],
                        "data_legend": False,
                        "range": range_y,
                        "range_x": range_x,
                        "n_dates": None,
                        "xlabel": None,
                        "ylabel": ylabel,
                        # names of lone series are in the title
                        "subtitle_data": dc_labels[name] if is_single else None,
                        # lateral titles only once
                        "subtitle_hist": specs["subtitle_hist"] if i == 0 else None,
                        "subtitle_cdf": specs["subtitle_cdf"] if i == 0 else None,
                    }
                )
                if not is_single:
                    sp.update(
                        {
                            "color_hist": color,
                            "color_cdf": color,
                            "color_mean": color,
                            "bins": vct_bins,
                            "bins_density": False,
                            "alpha_hist": specs["alpha_hist"],
                            "histtype": specs["histtype"],
                            "plot_mean": specs["plot_mean"],
                            "plot_mean_label": False,
                            "linestyle_mean": "dashed",
                        }
                    )
                TimeSeries.plot_series(data=ts.data, ax=ax_series, specs=sp)

                if len(ls_lateral) > 0:
                    vct_data = ts.data[ts.varfield].dropna().values
                    h = Univar.plot_histh(data=vct_data, ax=ls_lateral[0], specs=sp)
                    hist_max = max(hist_max, np.max(h[0]))
                    Univar.plot_cdf(
                        cdf_df=ts.get_cdf_weibull(), ax=ls_lateral[1], specs=sp
                    )

            if len(ls_lateral) > 0:
                ax_hist, ax_cdf = ls_lateral
                Univar.set_hist_xaxis(ax=ax_hist, hist_max=hist_max)
                # axis labels only below the last panel
                if not is_last:
                    ax_hist.set_xlabel(None)
                    ax_cdf.set_xlabel(None)

            viewer.clear_xticks(axes=[ax_series] + ls_lateral)
            if not is_single:
                self._set_series_legend(axes=[ax_series], specs=specs)

        TimeSeries.set_date_ticks(
            ax=axes[0],
            xmin=xmin,
            xmax=xmax,
            n_dates=specs["n_dates"],
            format_dates=specs["format_dates"],
        )
        axes[(n_panels - 1) * n_axes].set_xlabel(specs["xlabel"])
        return None

    @staticmethod
    def _get_panel_colors(ls_series, specs):
        """
        Get the color of each series in a panel. A series with a color already
        in use takes the color of ``cmap_series`` farthest from those in use.

        :param ls_series: series of the panel
        :type ls_series: list
        :param specs: plot specification dictionary
        :type specs: dict
        :return: colors, for each series
        :rtype: list
        """
        cmap = viewer.get_discrete_cmap(
            n_classes=10, base_cmap_name=specs["cmap_series"] or "tab10"
        )
        ls_free = [mcolors.to_rgba(cmap(i)) for i in range(10)]
        ls_rgba = []
        ls_colors = []
        for ts in ls_series:
            color = ts.view_specs["color"]
            if mcolors.to_rgba(color) in ls_rgba:
                color = max(
                    ls_free,
                    key=lambda c: min(
                        np.linalg.norm(np.subtract(c, u)) for u in ls_rgba
                    ),
                )
            ls_rgba.append(mcolors.to_rgba(color))
            ls_colors.append(color)
        return ls_colors

    def view(self, show=True, return_fig=False):
        """
        Visualize the time series collection: a Gantt chart of each
        series' own epochs, the cross-series overlap over time, and (in
        the ``"full"`` layout) each series' data prevalence. The ``"stacked"``
        and ``"stacked-simple"`` layouts draw series on panels instead, set by
        ``view_specs["panels"]`` and ``view_specs["panel_heights"]``.

        Every knob previously passed as a loose keyword (``folder``,
        ``filename``, ``dpi``, ``fig_format``, ``usealias``, colors,
        titles, axis ranges, layout choice...) now lives in
        ``self.view_specs`` -- set it before calling, exactly like
        :meth:`TimeSeries.view`.

        **Layouts**, set by ``view_specs["layout"]``:

        ==================  ======================================================================================
        Layout              Panels
        ==================  ======================================================================================
        ``full``            Gantt chart, overlap and prevalence.
        ``simple``          Gantt chart and overlap.
        ``default``         Same as ``full``.
        ``stacked``         A panel for each entry of ``panels``, with histograms and CDFs, on a shared time axis.
        ``stacked-simple``  A panel for each entry of ``panels``, on a shared time axis.
        ==================  ======================================================================================

        **View specs**, set by ``view_specs[key] = value`` before the call:

        =========================  ===============  ===========================================================================================
        Key                        Default          Description
        =========================  ===============  ===========================================================================================
        ``layout``                 ``"full"``       Name of the layout. See the table of layouts.
        ``style``                  ``"wien"``       Name of the plot style. See :func:`plans.viewer.set_style`.
        ``title``                  auto             Title of the figure.
        ``gantt``                  auto             Title of the Gantt chart.
        ``over``                   auto             Title of the overlap panel.
        ``prev``                   auto             Title of the prevalence panel.
        ``xlabel``                 auto             Label of the time axis.
        ``ylabel_over``            ``"%"``          Label of the y axis of the overlap panel.
        ``xlabel_prev``            ``"%"``          Label of the x axis of the prevalence panel.
        ``usealias``               ``False``        Use aliases instead of names in labels.
        ``n_dates``                ``5``            Number of date ticks, evenly spaced in time. None chooses them automatically.
        ``format_dates``           ``"%Y-%m-%d"``   Format of the date labels.
        ``xtick_rotation``         ``0``            Rotation of the date labels in the ``full`` and ``simple`` layouts.
        ``color_over``             ``"tab:blue"``   Color of the overlap panel.
        ``alpha_over``             ``0.4``          Opacity of the fill of the overlap panel.
        ``color_prev``             ``"tab:gray"``   Color of the prevalence bars.
        ``gantt_linewidth``        ``6``            Largest width of the Gantt lines. It shrinks to fit many series.
        ``n_series_max``           ``10``           Above this many series, labels are hidden and series lines go to the background.
        ``xmin``                   None             Start of the time axis. None is the first date of all series, with ``pad_x``.
        ``xmax``                   None             End of the time axis. None is the last date of all series, with ``pad_x``.
        ``ymin``                   None             Bottom of the overlap panel. None is automatic.
        ``ymax``                   None             Top of the overlap panel. None is automatic.
        ``pad_x``                  ``0.05``         Share of the time span added on each side of the time axis not set by ``xmin`` or ``xmax``.
        ``folder``                 auto             Folder of the saved figure.
        ``filename``               auto             Name of the saved figure, without extension. None is the name of the collection.
        ``suff``                   ``""``           Suffix of the saved figure, if ``filename`` is None.
        ``dpi``                    ``300``          Resolution of the saved figure.
        ``fig_format``             ``"jpg"``        Format of the saved figure.
        ``series``                 ``"Series"``     Title of the series panel, in the ``series`` layouts.
        ``subtitle_hist``          ``"Histogram"``  Title of the histograms.
        ``subtitle_cdf``           ``"CDF"``        Title of the CDFs.
        ``ylabel``                 auto             Label of the y axis, in the ``series`` layouts. None comes from the variable.
        ``range``                  None             Common y range, in the ``series`` layouts. None is set from the data.
        ``cmap_series``            ``"tab10"``      Color map of the series. In ``series`` layouts, None uses the color of each series.
        ``linewidth``              ``0.8``          Width of the series lines, in the ``series`` layouts.
        ``alpha_hist``             ``0.4``          Opacity of overlaid histograms.
        ``histtype``               ``"bar"``        Type of overlaid histograms. ``"step"`` draws outlines only.
        ``bins``                   ``30``           Number of common bins of overlaid histograms.
        ``plot_mean``              ``True``         Show mean lines on overlaid histograms and CDFs.
        ``legend``                 ``True``         Show the legend of overlaid series.
        ``highlight``              None             Names of the series drawn in color, in the ``series`` layouts.
        ``plot_background``        ``True``         Show the background lines on the series panel.
        ``color_background``       ``"silver"``     Color of the background series.
        ``linewidth_background``   ``0.5``          Width of the background lines.
        ``alpha_background``       ``0.6``          Opacity of the background lines.
        ``alpha_hist_background``  ``0.1``          Opacity of the background histograms.
        ``panels``                 None             Names of the series in each panel, as a list of lists. None is one series per panel.
        ``panel_heights``          None             Relative heights of the panels, like ``[3, 1]``. None is equal.
        =========================  ===============  ===========================================================================================

        :param show: option for showing instead of saving.
        :type show: bool
        :param return_fig: option for returning the figure object itself.
        :type return_fig: bool
        :return: the :class:`matplotlib.figure.Figure` if ``return_fig``
            is True, otherwise None (the figure is shown or saved to
            ``"{folder}/{filename or name+suff}.{fig_format}"``).
        :rtype: :class:`matplotlib.figure.Figure` or None
        """
        # SPECS
        specs = self._get_fig_specs()

        # BUILD
        fig, gs = viewer.build_fig(specs=specs)

        # PLOT
        fig = self._plot(fig=fig, gs=gs, specs=specs)

        # SHIP
        filename = specs["filename"]
        if filename is None:
            filename = "{}{}".format(self.name, specs["suff"])
        file_path = "{}/{}.{}".format(specs["folder"], filename, specs["fig_format"])
        viewer.set_layers(fig=fig)
        if return_fig:
            return fig
        else:
            viewer.ship_fig(fig=fig, show=show, file_output=file_path, dpi=specs["dpi"])

    # todo develop refactor to new view scheme (DRY)
    def view_old(
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


        """
        if usealias:
            _names = self.catalog["name"].values
            _alias = self.catalog["alias"].values
            dict_alias = dict()
            for i in range(len(self.catalog)):
                dict_alias[_names[i]] = _alias[i]

        # pre-processing
        local_epochs_df = self.merge_local_epochs()
        # Aggregate sum based on the 'Name' field
        agg_df = local_epochs_df.groupby("name")["n_epoch"].sum().reset_index()
        agg_df = agg_df.sort_values(by="n_epoch", ascending=True).reset_index(drop=True)
        names = agg_df["name"].values
        if usealias:
            alias = [dict_alias[name] for name in names]
        preval = 100 * agg_df["n_epoch"].values / agg_df["n_epoch"].sum()
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
            df_aux = local_epochs_df.query(f"name == '{name}'")
            for j in range(len(df_aux)):
                x_time = [df_aux["start"].values[j], df_aux["end"].values[j]]
                y_height = [heights[i], heights[i]]
                plt.plot(
                    x_time,
                    y_height,
                    color=df_aux["color"].values[j],
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

    def export_data(self, folder, filename=None, merged=True):
        """
        Export collection data as CSV files in the given folder.

        :param folder: Output folder path.
        :type folder: str
        :param filename: Base filename; defaults to ``self.name`` when ``None``.
        :type filename: str or None
        :param merged: If ``True``, exports a merged data CSV and an epochs
            summary CSV. If ``False``, exports each series individually.
        :type merged: bool
        """
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
    Collection of same-variable time series from different sites
    (e.g., a network of rain gauges). No miscellaneous data is allowed.

    Supports cross-site analysis: correlation between sites via
    :meth:`get_correlation` and gap filling from neighboring sites via
    :meth:`regionalize`. Site coordinates are read from the ``x`` and ``y``
    attributes of each series.

    .. note::

        See ``TimeSeriesEnsemble`` for many realizations of the same series
        (same site and time).

    """

    def __init__(self, name="myTimeSeriesCluster", base_object=None):
        # initialize parent
        super().__init__(name=name, base_object=base_object)

        # Set extra specific attributes
        self.varname = self.baseobject().varname
        self.varalias = self.baseobject().varalias

        # Overwrite parent attributes
        self.name_object = "Time Series Cluster"

        # Cluster layouts
        self._set_series_layouts()
        self.layouts.update(
            {
                "correlation": {
                    "ncols": 24,
                    "nrows": 24,
                    "width": viewer.FIG_SIZES["S"]["w"],
                    "height": viewer.FIG_SIZES["S"]["h"],
                },
            }
        )

        # reload view specs
        self._set_view_specs()

    # Data methods
    # -------------------------------------------------------------------
    def _get_names_others(self, name):
        """
        Get names of all series except ``name``, in catalog order.
        """
        return [n for n in self.catalog[self.field_name].values if n != name]

    def get_correlation(self, method="pearson", min_overlap=30):
        """
        Get the correlation matrix between all series, on their overlapping time steps.

        :param method: correlation method. Options: ``pearson`` or ``spearman``
        :type method: str
        :param min_overlap: minimum number of overlapping time steps.
            Pairs with less overlap are set to NaN.
        :type min_overlap: int
        :return: square correlation matrix, indexed by series names
        :rtype: :class:`pandas.DataFrame`
        """
        dc_funcs = {"pearson": _metrics.pearson, "spearman": _metrics.spearman}
        func = dc_funcs[method.lower()]

        # merged columns follow catalog order
        df = self.merge_data()
        ls_names = list(self.catalog[self.field_name].values)
        grd = df[df.columns[1:]].values

        n = len(ls_names)
        grd_corr = np.full(shape=(n, n), fill_value=np.nan)
        for i in range(n):
            for j in range(i, n):
                # overlapping steps only
                mask = ~np.isnan(grd[:, i]) & ~np.isnan(grd[:, j])
                if np.sum(mask) < min_overlap:
                    continue
                r = func(x=grd[mask, i], y=grd[mask, j])
                grd_corr[i, j] = r
                grd_corr[j, i] = r

        return pd.DataFrame(grd_corr, index=ls_names, columns=ls_names)

    def get_weights_by_name(self, name, method="average"):
        """
        Compute interpolation weights of all other series relative to a named series.

        :param name: name of the target series (excluded from the weight set)
        :type name: str
        :param method: weighting scheme: ``average`` (uniform) or ``idw``
            (inverse-distance). Default is ``average``.
        :type method: str
        :return: weights for the other series, in catalog order
        :rtype: :class:`numpy.ndarray`
        """
        ls_names = self._get_names_others(name=name)
        w = np.ones(len(ls_names))

        if method.lower() == "idw":
            x = self.collection[name].x
            y = self.collection[name].y
            x_i = np.array([self.collection[n].x for n in ls_names])
            y_i = np.array([self.collection[n].y for n in ls_names])
            d_i = np.sqrt(np.square(x - x_i) + np.square(y - y_i))
            # small offset handles zero distance
            idw_i = 1 / (d_i + (np.mean(d_i) / 10000))
            # normalize to [0-100] range
            w = 100 * idw_i / np.sum(idw_i)

        return w

    def regionalize(self, method="average"):
        """
        Fill gaps of every series with a weighted average of the other series.

        :param method: weighting scheme: ``average`` (uniform) or ``idw``
            (inverse-distance). Default is ``average``.
        :type method: str
        :return: None
        :rtype: None

        **Notes**

        - Series are standardized first, if not yet.
        - Only gaps are filled; observed values are never changed.
        - Values are taken as they are, so sites with different levels
          (e.g., temperature at different elevations) will bias the filling.
        - All fillings use the original data, so filled values do not cascade.

        """
        # Handle standardization
        if not self.isstandard:
            self.standardize()

        # merged columns follow catalog order
        df = self.merge_data()
        ls_names = list(self.catalog[self.field_name].values)
        ls_columns = list(df.columns[1:])

        for name in ls_names:
            ts = self.collection[name]

            # sources
            ls_src = self._get_names_others(name=name)
            ls_src_columns = [ls_columns[ls_names.index(n)] for n in ls_src]
            grd_src = df[ls_src_columns].values

            # weighted average over available sources
            vct_w = self.get_weights_by_name(name=name, method=method)
            grd_w = vct_w * ~np.isnan(grd_src)
            vct_w_sum = np.sum(grd_w, axis=1)
            vct_w_sum = np.where(vct_w_sum == 0, np.nan, vct_w_sum)
            vct_o = np.nansum(grd_src * grd_w, axis=1) / vct_w_sum

            # align merged grid to the series own grid
            vct_o = (
                pd.Series(vct_o, index=df[self.dtfield])
                .reindex(ts.data[ts.dtfield].values)
                .values
            )

            # fill gaps only
            vct_dst = ts.data[ts.varfield].values
            ts.data[ts.varfield] = np.where(np.isnan(vct_dst), vct_o, vct_dst)
            ts.update()
            ts.update_epochs_stats()

        # Update the collection catalog with details
        self.update(details=True)
        return None

    # View internal methods
    # -------------------------------------------------------------------
    def _set_view_specs(self):
        """
        Set view specifications. Expected to increment superior methods.
        """
        super()._set_view_specs()
        self.view_specs.update(
            {
                # correlation layout
                "correlation": "Correlation",
                "corr_method": "pearson",
                "corr_min_overlap": 30,
                "cmap_corr": "RdBu_r",
                "range_corr": [-1, 1],  # narrow it to reveal structure
                "annotate": True,
            }
        )
        return None

    def _build_axes(self, fig, gs, specs):
        """
        Add axes to figure based on layout.
        """
        if specs["layout"] == "correlation":
            fig.add_subplot(gs[3:20, 5:20])
        else:
            fig = super()._build_axes(fig=fig, gs=gs, specs=specs)
        return fig

    def _plot(self, fig, gs, specs):
        """
        Plot on figure based on layout.
        """
        if specs["layout"] == "correlation":
            fig = self._build_axes(fig=fig, gs=gs, specs=specs)
            self._plot_correlation(ax=fig.get_axes()[0], specs=specs)
            fig.suptitle(specs["title"])
        else:
            fig = super()._plot(fig=fig, gs=gs, specs=specs)
        return fig

    def view(self, show=True, return_fig=False):
        """
        Get the visualization, which also has the correlation between series.

        **Layouts**, set by ``view_specs["layout"]``:

        ==================  ======================================================================================
        Layout              Panels
        ==================  ======================================================================================
        ``full``            Gantt chart, overlap and prevalence.
        ``simple``          Gantt chart and overlap.
        ``default``         Same as ``full``.
        ``stacked``         A panel for each entry of ``panels``, with histograms and CDFs, on a shared time axis.
        ``stacked-simple``  A panel for each entry of ``panels``, on a shared time axis.
        ``series``          All series overlaid, with histograms and CDFs.
        ``series-simple``   All series overlaid.
        ``correlation``     Correlation matrix.
        ==================  ======================================================================================

        **View specs**, set by ``view_specs[key] = value`` before the call:

        =========================  =================  ===========================================================================================
        Key                        Default            Description
        =========================  =================  ===========================================================================================
        ``layout``                 ``"full"``         Name of the layout. See the table of layouts.
        ``style``                  ``"wien"``         Name of the plot style. See :func:`plans.viewer.set_style`.
        ``title``                  auto               Title of the figure.
        ``gantt``                  auto               Title of the Gantt chart.
        ``over``                   auto               Title of the overlap panel.
        ``prev``                   auto               Title of the prevalence panel.
        ``xlabel``                 auto               Label of the time axis.
        ``ylabel_over``            ``"%"``            Label of the y axis of the overlap panel.
        ``xlabel_prev``            ``"%"``            Label of the x axis of the prevalence panel.
        ``usealias``               ``False``          Use aliases instead of names in labels.
        ``n_dates``                ``5``              Number of date ticks, evenly spaced in time. None chooses them automatically.
        ``format_dates``           ``"%Y-%m-%d"``     Format of the date labels.
        ``xtick_rotation``         ``0``              Rotation of the date labels in the ``full`` and ``simple`` layouts.
        ``color_over``             ``"tab:blue"``     Color of the overlap panel.
        ``alpha_over``             ``0.4``            Opacity of the fill of the overlap panel.
        ``color_prev``             ``"tab:gray"``     Color of the prevalence bars.
        ``gantt_linewidth``        ``6``              Largest width of the Gantt lines. It shrinks to fit many series.
        ``n_series_max``           ``10``             Above this many series, labels are hidden and series lines go to the background.
        ``xmin``                   None               Start of the time axis. None is the first date of all series, with ``pad_x``.
        ``xmax``                   None               End of the time axis. None is the last date of all series, with ``pad_x``.
        ``ymin``                   None               Bottom of the overlap panel. None is automatic.
        ``ymax``                   None               Top of the overlap panel. None is automatic.
        ``pad_x``                  ``0.05``           Share of the time span added on each side of the time axis not set by ``xmin`` or ``xmax``.
        ``folder``                 auto               Folder of the saved figure.
        ``filename``               auto               Name of the saved figure, without extension. None is the name of the collection.
        ``suff``                   ``""``             Suffix of the saved figure, if ``filename`` is None.
        ``dpi``                    ``300``            Resolution of the saved figure.
        ``fig_format``             ``"jpg"``          Format of the saved figure.
        ``series``                 ``"Series"``       Title of the series panel, in the ``series`` layouts.
        ``subtitle_hist``          ``"Histogram"``    Title of the histograms.
        ``subtitle_cdf``           ``"CDF"``          Title of the CDFs.
        ``ylabel``                 auto               Label of the y axis, in the ``series`` layouts. None comes from the variable.
        ``range``                  None               Common y range, in the ``series`` layouts. None is set from the data.
        ``cmap_series``            ``"tab10"``        Color map of the series. In ``series`` layouts, None uses the color of each series.
        ``linewidth``              ``0.8``            Width of the series lines, in the ``series`` layouts.
        ``alpha_hist``             ``0.4``            Opacity of overlaid histograms.
        ``histtype``               ``"bar"``          Type of overlaid histograms. ``"step"`` draws outlines only.
        ``bins``                   ``30``             Number of common bins of overlaid histograms.
        ``plot_mean``              ``True``           Show mean lines on overlaid histograms and CDFs.
        ``legend``                 ``True``           Show the legend of overlaid series.
        ``highlight``              None               Names of the series drawn in color, in the ``series`` layouts.
        ``plot_background``        ``True``           Show the background lines on the series panel.
        ``color_background``       ``"silver"``       Color of the background series.
        ``linewidth_background``   ``0.5``            Width of the background lines.
        ``alpha_background``       ``0.6``            Opacity of the background lines.
        ``alpha_hist_background``  ``0.1``            Opacity of the background histograms.
        ``panels``                 None               Names of the series in each panel, as a list of lists. None is one series per panel.
        ``panel_heights``          None               Relative heights of the panels, like ``[3, 1]``. None is equal.
        ``correlation``            ``"Correlation"``  Title of the correlation panel.
        ``corr_method``            ``"pearson"``      Correlation method: ``"pearson"``, ``"kendall"`` or ``"spearman"``.
        ``corr_min_overlap``       ``30``             Fewest common records for a correlation.
        ``cmap_corr``              ``"RdBu_r"``       Color map of the correlation.
        ``range_corr``             ``[-1, 1]``        Range of the color map. Narrow it to reveal structure.
        ``annotate``               ``True``           Show values on the correlation cells.
        =========================  =================  ===========================================================================================

        :param show: option for showing instead of saving
        :type show: bool
        :param return_fig: option for returning the figure object
        :type return_fig: bool
        :return: figure object if ``return_fig`` is True, else None
        :rtype: :class:`matplotlib.figure.Figure` or None
        """
        return super().view(show=show, return_fig=return_fig)

    def _plot_correlation(self, ax, specs):
        """
        Plot the correlation matrix as an annotated heatmap.
        """
        df_corr = self.get_correlation(
            method=specs["corr_method"], min_overlap=specs["corr_min_overlap"]
        )
        ls_labels = self._get_labels(specs=specs)
        grd = df_corr.values
        n = len(ls_labels)

        im = ax.imshow(
            grd,
            cmap=specs["cmap_corr"],
            vmin=specs["range_corr"][0],
            vmax=specs["range_corr"][1],
        )
        # annotations are unreadable on large clusters
        if specs["annotate"] and n <= specs["n_series_max"]:
            for i in range(n):
                for j in range(n):
                    s = "-" if np.isnan(grd[i, j]) else "{:.2f}".format(grd[i, j])
                    # white text on strong colors
                    color = "white" if abs(np.nan_to_num(grd[i, j])) > 0.6 else "black"
                    ax.text(j, i, s, ha="center", va="center", color=color, fontsize=6)
        if n <= specs["n_series_max"]:
            ax.set_xticks(range(n), ls_labels, rotation=90)
            ax.set_yticks(range(n), ls_labels)
        else:
            ax.set_xticks([])
            ax.set_yticks([])
            ax.set_xlabel("{} series".format(n))
            ax.set_ylabel("{} series".format(n))
        ax.grid(visible=False)
        ax.set_title(
            "{} ({})".format(specs["correlation"], specs["corr_method"]), loc="left"
        )
        plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        return None


class TimeSeriesEnsemble(TimeSeriesCollection):
    """
    Collection of same-variable time series as realizations of the same
    series (same site and time), e.g., stochastic draws or model runs.

    Supports ensemble reduction across members at each time step via
    :meth:`reducer` and its shortcuts (:meth:`mean`, :meth:`percentiles`,
    :meth:`stats`, etc.). Reducers ignore missing values. The ``series``
    view draws members in background style, with reducers and percentile
    bands on top.

    .. note::

        See ``TimeSeriesCluster`` for same-variable series from different sites.

    """

    def __init__(self, name="myTimeSeriesEnsemble", base_object=None):
        # initialize parent
        super().__init__(name=name, base_object=base_object)

        # Set extra specific attributes
        self.varname = self.baseobject().varname
        self.varalias = self.baseobject().varalias

        # Overwrite parent attributes
        self.name_object = "Time Series Ensemble"

        # Ensemble layouts
        self._set_series_layouts()

        # reload view specs
        self._set_view_specs()

    # Reducer methods
    # -------------------------------------------------------------------
    def reducer(self, reducer_funcs=None, stepwise=False):
        """
        Apply reducer functions across all members at each time step.

        :param reducer_funcs: mapping of output name to a dict with
            ``"Func"`` (callable) and ``"Args"`` (extra scalar argument or None).
        :type reducer_funcs: dict
        :param stepwise: if True, apply each function row-by-row rather than
            vectorized along axis 1. Default is False.
        :type stepwise: bool
        :return: DataFrame with datetime and one column per reducer function,
            named ``"{varalias}_{name}"``
        :rtype: :class:`pandas.DataFrame`
        """
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
        """Return the time-step-wise mean across all members."""
        return self.reducer(reducer_funcs={"mean": {"Func": np.nanmean, "Args": None}})

    def median(self):
        """Return the time-step-wise median across all members."""
        return self.reducer(
            reducer_funcs={"median": {"Func": np.nanmedian, "Args": None}}
        )

    def rng(self):
        """Return the time-step-wise range (max - min) across all members."""
        return self.reducer(
            reducer_funcs={"rng": {"Func": TimeSeriesEnsemble._nanrange, "Args": None}}
        )

    def std(self):
        """Return the time-step-wise standard deviation across all members."""
        return self.reducer(reducer_funcs={"std": {"Func": np.nanstd, "Args": None}})

    def min(self):
        """Return the time-step-wise minimum across all members."""
        return self.reducer(reducer_funcs={"min": {"Func": np.nanmin, "Args": None}})

    def max(self):
        """Return the time-step-wise maximum across all members."""
        return self.reducer(reducer_funcs={"max": {"Func": np.nanmax, "Args": None}})

    def percentile(self, p=90):
        """
        Return the time-step-wise p-th percentile across all members.

        :param p: percentile value (0-100). Default is 90.
        :type p: float
        :return: DataFrame with datetime and the ``"{varalias}_p{p}"`` column
        :rtype: :class:`pandas.DataFrame`
        """
        return self.percentiles(values=[p])

    def percentiles(self, values=None):
        """
        Return time-step-wise percentiles across all members.

        :param values: percentile values to compute. Default is
            ``[1, 5, 10, 25, 50, 75, 90, 95, 99]``.
        :type values: list
        :return: DataFrame with datetime and one ``"{varalias}_p{p}"`` column
            per value (e.g., ``p05``, ``p50``)
        :rtype: :class:`pandas.DataFrame`
        """
        if values is None:
            values = [1, 5, 10, 25, 50, 75, 90, 95, 99]
        dict_funcs = {
            TimeSeriesEnsemble._get_percentile_name(p=v): {
                "Func": np.nanpercentile,
                "Args": v,
            }
            for v in values
        }
        return self.reducer(reducer_funcs=dict_funcs)

    def stats(self, basic=False):
        """
        Return a combined DataFrame of common statistics and percentiles across all members.

        :param basic: if True, compute only quartile percentiles (25, 50, 75).
        :type basic: bool
        :return: DataFrame with datetime, sum, mean, std, min, max and percentiles
        :rtype: :class:`pandas.DataFrame`
        """
        df_stats = self.reducer(
            reducer_funcs={
                "sum": {"Func": np.nansum, "Args": None},
                "mean": {"Func": np.nanmean, "Args": None},
                "std": {"Func": np.nanstd, "Args": None},
                "min": {"Func": np.nanmin, "Args": None},
                "max": {"Func": np.nanmax, "Args": None},
            }
        )
        values = [25, 50, 75] if basic else None
        df_per = self.percentiles(values=values)
        df = pd.merge(left=df_stats, right=df_per, on=self.dtfield)
        return df

    def get_reducer_series(self, name):
        """
        Get a reducer as a series object of the ensemble base type.

        :param name: reducer name: ``mean``, ``median``, ``min``, ``max`` or a
            percentile such as ``p90``
        :type name: str
        :return: series holding the reducer values
        :rtype: :class:`TimeSeries`
        """
        dc_funcs = {
            "mean": self.mean,
            "median": self.median,
            "min": self.min,
            "max": self.max,
        }
        if name in dc_funcs:
            df = dc_funcs[name]()
        elif name.startswith("p"):
            df = self.percentile(p=float(name[1:]))
        else:
            raise ValueError(f"Unknown reducer: {name}")

        ts = self.baseobject(name=name, alias=name)
        ts.set_data(
            input_df=df, input_dtfield=self.dtfield, input_varfield=df.columns[1]
        )
        return ts

    # View internal methods
    # -------------------------------------------------------------------
    def _set_view_specs(self):
        """
        Set view specifications. Expected to increment superior methods.
        """
        super()._set_view_specs()
        self.view_specs.update(
            {
                "layout": "series",
                # reducers drawn in color, members in background
                "reducers": ["mean"],
                # percentile bands, as [low, high] pairs
                "bands": [[5, 95]],
                "color_band": "#8db4dc",  # light, so lines stay readable on top
                "alpha_band": 0.6,
            }
        )
        return None

    def _plot_series(self, axes, specs, extra=None, force_background=False):
        """
        Plot members in background style, with reducers and bands on top.
        """
        ls_reducers = specs["reducers"] or []
        ls_bands = specs["bands"] or []
        ls_extra = [self.get_reducer_series(name=r) for r in ls_reducers]
        super()._plot_series(
            axes=axes,
            specs=specs,
            extra=ls_extra,
            force_background=len(ls_reducers) + len(ls_bands) > 0,
        )

        # BANDS
        # -------------------------------------------------------------------
        # between background members and foreground lines
        for p_lo, p_hi in ls_bands:
            df = self.percentiles(values=[p_lo, p_hi])
            s_lo = TimeSeriesEnsemble._get_percentile_name(p=p_lo)
            s_hi = TimeSeriesEnsemble._get_percentile_name(p=p_hi)
            axes[0].fill_between(
                df[self.dtfield],
                df["{}_{}".format(self.varalias, s_lo)],
                df["{}_{}".format(self.varalias, s_hi)],
                color=specs["color_band"],
                alpha=specs["alpha_band"],
                edgecolor="none",
                zorder=2,
                label="{}-{}".format(s_lo, s_hi),
            )

        # legend again, now including bands
        self._set_series_legend(axes=axes, specs=specs)
        return None

    def view(self, show=True, return_fig=False):
        """
        Get the visualization, with members in the background and reducers and bands on top.

        **Layouts**, set by ``view_specs["layout"]``:

        ==================  ======================================================================================
        Layout              Panels
        ==================  ======================================================================================
        ``full``            Gantt chart, overlap and prevalence.
        ``simple``          Gantt chart and overlap.
        ``default``         Same as ``full``.
        ``stacked``         A panel for each entry of ``panels``, with histograms and CDFs, on a shared time axis.
        ``stacked-simple``  A panel for each entry of ``panels``, on a shared time axis.
        ``series``          All series overlaid, with histograms and CDFs.
        ``series-simple``   All series overlaid.
        ==================  ======================================================================================

        **View specs**, set by ``view_specs[key] = value`` before the call:

        =========================  ===============  ===========================================================================================
        Key                        Default          Description
        =========================  ===============  ===========================================================================================
        ``layout``                 ``"series"``     Name of the layout. See the table of layouts.
        ``style``                  ``"wien"``       Name of the plot style. See :func:`plans.viewer.set_style`.
        ``title``                  auto             Title of the figure.
        ``gantt``                  auto             Title of the Gantt chart.
        ``over``                   auto             Title of the overlap panel.
        ``prev``                   auto             Title of the prevalence panel.
        ``xlabel``                 auto             Label of the time axis.
        ``ylabel_over``            ``"%"``          Label of the y axis of the overlap panel.
        ``xlabel_prev``            ``"%"``          Label of the x axis of the prevalence panel.
        ``usealias``               ``False``        Use aliases instead of names in labels.
        ``n_dates``                ``5``            Number of date ticks, evenly spaced in time. None chooses them automatically.
        ``format_dates``           ``"%Y-%m-%d"``   Format of the date labels.
        ``xtick_rotation``         ``0``            Rotation of the date labels in the ``full`` and ``simple`` layouts.
        ``color_over``             ``"tab:blue"``   Color of the overlap panel.
        ``alpha_over``             ``0.4``          Opacity of the fill of the overlap panel.
        ``color_prev``             ``"tab:gray"``   Color of the prevalence bars.
        ``gantt_linewidth``        ``6``            Largest width of the Gantt lines. It shrinks to fit many series.
        ``n_series_max``           ``10``           Above this many series, labels are hidden and series lines go to the background.
        ``xmin``                   None             Start of the time axis. None is the first date of all series, with ``pad_x``.
        ``xmax``                   None             End of the time axis. None is the last date of all series, with ``pad_x``.
        ``ymin``                   None             Bottom of the overlap panel. None is automatic.
        ``ymax``                   None             Top of the overlap panel. None is automatic.
        ``pad_x``                  ``0.05``         Share of the time span added on each side of the time axis not set by ``xmin`` or ``xmax``.
        ``folder``                 auto             Folder of the saved figure.
        ``filename``               auto             Name of the saved figure, without extension. None is the name of the collection.
        ``suff``                   ``""``           Suffix of the saved figure, if ``filename`` is None.
        ``dpi``                    ``300``          Resolution of the saved figure.
        ``fig_format``             ``"jpg"``        Format of the saved figure.
        ``series``                 ``"Series"``     Title of the series panel, in the ``series`` layouts.
        ``subtitle_hist``          ``"Histogram"``  Title of the histograms.
        ``subtitle_cdf``           ``"CDF"``        Title of the CDFs.
        ``ylabel``                 auto             Label of the y axis, in the ``series`` layouts. None comes from the variable.
        ``range``                  None             Common y range, in the ``series`` layouts. None is set from the data.
        ``cmap_series``            ``"tab10"``      Color map of the series. In ``series`` layouts, None uses the color of each series.
        ``linewidth``              ``0.8``          Width of the series lines, in the ``series`` layouts.
        ``alpha_hist``             ``0.4``          Opacity of overlaid histograms.
        ``histtype``               ``"bar"``        Type of overlaid histograms. ``"step"`` draws outlines only.
        ``bins``                   ``30``           Number of common bins of overlaid histograms.
        ``plot_mean``              ``True``         Show mean lines on overlaid histograms and CDFs.
        ``legend``                 ``True``         Show the legend of overlaid series.
        ``highlight``              None             Names of the series drawn in color, in the ``series`` layouts.
        ``plot_background``        ``True``         Show the background lines on the series panel.
        ``color_background``       ``"silver"``     Color of the background series.
        ``linewidth_background``   ``0.5``          Width of the background lines.
        ``alpha_background``       ``0.6``          Opacity of the background lines.
        ``alpha_hist_background``  ``0.1``          Opacity of the background histograms.
        ``panels``                 None             Names of the series in each panel, as a list of lists. None is one series per panel.
        ``panel_heights``          None             Relative heights of the panels, like ``[3, 1]``. None is equal.
        ``reducers``               ``["mean"]``     Names of the reducers drawn in color, such as ``mean``. None hides them.
        ``bands``                  ``[[5, 95]]``    Percentile bands, as ``[low, high]`` pairs. None hides them.
        ``color_band``             ``"#8db4dc"``    Color of the bands.
        ``alpha_band``             ``0.6``          Opacity of the bands.
        =========================  ===============  ===========================================================================================

        :param show: option for showing instead of saving
        :type show: bool
        :param return_fig: option for returning the figure object
        :type return_fig: bool
        :return: figure object if ``return_fig`` is True, else None
        :rtype: :class:`matplotlib.figure.Figure` or None
        """
        return super().view(show=show, return_fig=return_fig)

    # Static methods
    # -------------------------------------------------------------------
    @staticmethod
    def _nanrange(x, axis=None):
        """
        Range (max - min) ignoring missing values.
        """
        return np.nanmax(x, axis=axis) - np.nanmin(x, axis=axis)

    @staticmethod
    def _get_percentile_name(p):
        """
        Get the percentile name, zero padded (e.g., ``p05``, ``p50``, ``p2.5``).
        """
        if float(p).is_integer():
            return "p{:02d}".format(int(p))
        return "p{}".format(p)


class SeasonalEnsemble(TimeSeriesEnsemble):
    """
    Ensemble of the years of a single series, for seasonal plots.

    Each year becomes a member, with dates moved onto one reference year, so
    reducers, bands and ``highlight`` work across years. Works with any time
    step that repeats each year: sub-daily, daily or monthly.

    .. note::

        Dates in members and reducers are placeholders. The reference year
        is a leap year, so 29 Feb has its own step, filled only by leap years.
        To join reducers by calendar date, use the month and day, as in
        ``df["datetime"].dt.strftime("%m-%d")``.

    """

    # short month names, independent of the machine language
    MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()

    def __init__(self, name="mySeasonalEnsemble", base_object=None):
        # initialize parent
        super().__init__(name=name, base_object=base_object)

        # Set extra specific attributes
        self.year_start = 1

        # Overwrite parent attributes
        self.name_object = "Seasonal Ensemble"

        # reload view specs
        self._set_view_specs()

    # Data methods
    # -------------------------------------------------------------------
    def set_series(self, ts, year_start=1):
        """
        Split a series into one member per year, replacing current members.

        Members are named by year, like ``2021``. When the year does not start
        in January (e.g., a water year), names hold both years, like ``2020-21``.
        Incomplete years are kept, and count in the reducers.

        :param ts: series to split
        :type ts: :class:`TimeSeries`
        :param year_start: first month of the year, from 1 to 12. Default is 1.
        :type year_start: int
        :return: None
        :rtype: None
        """
        if year_start not in range(1, 13):
            raise ValueError(f"year_start must be from 1 to 12, not {year_start}")
        if ts.data is None:
            raise ValueError("No data in the series. Set the data first")

        self.year_start = year_start
        self.varname = ts.varname
        self.varalias = ts.varalias
        for name in list(self.collection.keys()):
            self.remove(name=name)

        # ------------ align steps ------------
        df = ts.data[[ts.dtfield, ts.varfield]].copy()
        dates = SeasonalEnsemble._align_steps(dates=df[ts.dtfield])
        before_start = dates.dt.month < year_start
        vct_years = dates.dt.year - before_start.astype(int)
        df[ts.dtfield] = pd.to_datetime(
            {
                "year": self._get_reference_start().year + before_start.astype(int),
                "month": dates.dt.month,
                "day": dates.dt.day,
                "hour": dates.dt.hour,
                "minute": dates.dt.minute,
                "second": dates.dt.second,
            }
        )

        # ------------ set members ------------
        for year, df_year in df.groupby(vct_years):
            name = str(year)
            if year_start > 1:
                name = "{}-{:02d}".format(year, (year + 1) % 100)
            member = self.baseobject(name=name, alias=name)
            member.units = ts.units
            member.varname = ts.varname
            member.varalias = ts.varalias
            member.set_data(
                input_df=df_year,
                input_dtfield=ts.dtfield,
                input_varfield=ts.varfield,
            )
            self.append(new_object=member)
        self.update(details=True)
        return None

    # View internal methods
    # -------------------------------------------------------------------
    def _set_view_specs(self):
        """
        Set view specifications. Expected to increment superior methods.
        """
        super()._set_view_specs()
        self.view_specs.update(
            {
                # x axis labels: "days", "month", "month-letter" or "month-alias"
                "xaxis": "month-alias",
                "xlabel": None,  # None is set by the x axis mode
                "pad_x": 0,  # a padding would repeat months at the edges
            }
        )
        return None

    def _get_reference_start(self):
        """
        Get the first date of the reference year, chosen so it holds 29 Feb.
        """
        year = 2000 if self.year_start <= 2 else 1999
        return pd.Timestamp(year=year, month=self.year_start, day=1)

    def _plot_series(self, axes, specs, extra=None, force_background=False):
        """
        Plot as in the ensemble, with the x axis of the reference year.
        """
        dc_labels = {
            "days": "Day",
            "month": "Month",
            "month-letter": "Month",
            "month-alias": "Month",
        }
        if specs["xaxis"] not in dc_labels:
            raise ValueError(
                f"Unknown xaxis '{specs['xaxis']}'. Options: {list(dc_labels.keys())}"
            )

        # the x axis opens at the start of the year, even without complete members
        if specs["xmin"] is None:
            specs["xmin"] = self._get_reference_start()
        if specs["xlabel"] is None:
            specs["xlabel"] = dc_labels[specs["xaxis"]]

        super()._plot_series(
            axes=axes, specs=specs, extra=extra, force_background=force_background
        )
        self._set_xaxis(ax=axes[0], mode=specs["xaxis"])
        return None

    def _set_xaxis(self, ax, mode):
        """
        Set the ticks and labels of the x axis.
        """
        if mode == "days":
            # counted from the start of the reference year
            num_start = mdates.date2num(self._get_reference_start())
            ax.xaxis.set_major_locator(
                mticker.FixedLocator(
                    [num_start] + [num_start + d - 1 for d in range(50, 367, 50)]
                )
            )
            ax.xaxis.set_major_formatter(
                mticker.FuncFormatter(lambda x, pos: str(round(x - num_start) + 1))
            )
            return None

        dc_formats = {
            "month": lambda i: str(i + 1),
            "month-letter": lambda i: SeasonalEnsemble.MONTHS[i][0],
            "month-alias": lambda i: SeasonalEnsemble.MONTHS[i],
        }
        func = dc_formats[mode]
        ax.xaxis.set_major_locator(mdates.MonthLocator())
        ax.xaxis.set_major_formatter(
            mticker.FuncFormatter(lambda x, pos: func(mdates.num2date(x).month - 1))
        )
        return None

    def view(self, show=True, return_fig=False):
        """
        Get the visualization, with the years of the series on the same calendar.

        **Layouts**, set by ``view_specs["layout"]``:

        ==================  ======================================================================================
        Layout              Panels
        ==================  ======================================================================================
        ``full``            Gantt chart, overlap and prevalence.
        ``simple``          Gantt chart and overlap.
        ``default``         Same as ``full``.
        ``stacked``         A panel for each entry of ``panels``, with histograms and CDFs, on a shared time axis.
        ``stacked-simple``  A panel for each entry of ``panels``, on a shared time axis.
        ``series``          All series overlaid, with histograms and CDFs.
        ``series-simple``   All series overlaid.
        ==================  ======================================================================================

        **View specs**, set by ``view_specs[key] = value`` before the call:

        =========================  =================  ===========================================================================================
        Key                        Default            Description
        =========================  =================  ===========================================================================================
        ``layout``                 ``"series"``       Name of the layout. See the table of layouts.
        ``style``                  ``"wien"``         Name of the plot style. See :func:`plans.viewer.set_style`.
        ``title``                  auto               Title of the figure.
        ``gantt``                  auto               Title of the Gantt chart.
        ``over``                   auto               Title of the overlap panel.
        ``prev``                   auto               Title of the prevalence panel.
        ``xlabel``                 auto               Label of the time axis.
        ``ylabel_over``            ``"%"``            Label of the y axis of the overlap panel.
        ``xlabel_prev``            ``"%"``            Label of the x axis of the prevalence panel.
        ``usealias``               ``False``          Use aliases instead of names in labels.
        ``n_dates``                ``5``              Number of date ticks, evenly spaced in time. None chooses them automatically.
        ``format_dates``           ``"%Y-%m-%d"``     Format of the date labels.
        ``xtick_rotation``         ``0``              Rotation of the date labels in the ``full`` and ``simple`` layouts.
        ``color_over``             ``"tab:blue"``     Color of the overlap panel.
        ``alpha_over``             ``0.4``            Opacity of the fill of the overlap panel.
        ``color_prev``             ``"tab:gray"``     Color of the prevalence bars.
        ``gantt_linewidth``        ``6``              Largest width of the Gantt lines. It shrinks to fit many series.
        ``n_series_max``           ``10``             Above this many series, labels are hidden and series lines go to the background.
        ``xmin``                   None               Start of the time axis. None is the first date of all series, with ``pad_x``.
        ``xmax``                   None               End of the time axis. None is the last date of all series, with ``pad_x``.
        ``ymin``                   None               Bottom of the overlap panel. None is automatic.
        ``ymax``                   None               Top of the overlap panel. None is automatic.
        ``pad_x``                  ``0``              Share of the time span added on each side of the time axis not set by ``xmin`` or ``xmax``.
        ``folder``                 auto               Folder of the saved figure.
        ``filename``               auto               Name of the saved figure, without extension. None is the name of the collection.
        ``suff``                   ``""``             Suffix of the saved figure, if ``filename`` is None.
        ``dpi``                    ``300``            Resolution of the saved figure.
        ``fig_format``             ``"jpg"``          Format of the saved figure.
        ``series``                 ``"Series"``       Title of the series panel, in the ``series`` layouts.
        ``subtitle_hist``          ``"Histogram"``    Title of the histograms.
        ``subtitle_cdf``           ``"CDF"``          Title of the CDFs.
        ``ylabel``                 auto               Label of the y axis, in the ``series`` layouts. None comes from the variable.
        ``range``                  None               Common y range, in the ``series`` layouts. None is set from the data.
        ``cmap_series``            ``"tab10"``        Color map of the series. In ``series`` layouts, None uses the color of each series.
        ``linewidth``              ``0.8``            Width of the series lines, in the ``series`` layouts.
        ``alpha_hist``             ``0.4``            Opacity of overlaid histograms.
        ``histtype``               ``"bar"``          Type of overlaid histograms. ``"step"`` draws outlines only.
        ``bins``                   ``30``             Number of common bins of overlaid histograms.
        ``plot_mean``              ``True``           Show mean lines on overlaid histograms and CDFs.
        ``legend``                 ``True``           Show the legend of overlaid series.
        ``highlight``              None               Names of the series drawn in color, in the ``series`` layouts.
        ``plot_background``        ``True``           Show the background lines on the series panel.
        ``color_background``       ``"silver"``       Color of the background series.
        ``linewidth_background``   ``0.5``            Width of the background lines.
        ``alpha_background``       ``0.6``            Opacity of the background lines.
        ``alpha_hist_background``  ``0.1``            Opacity of the background histograms.
        ``panels``                 None               Names of the series in each panel, as a list of lists. None is one series per panel.
        ``panel_heights``          None               Relative heights of the panels, like ``[3, 1]``. None is equal.
        ``reducers``               ``["mean"]``       Names of the reducers drawn in color, such as ``mean``. None hides them.
        ``bands``                  ``[[5, 95]]``      Percentile bands, as ``[low, high]`` pairs. None hides them.
        ``color_band``             ``"#8db4dc"``      Color of the bands.
        ``alpha_band``             ``0.6``            Opacity of the bands.
        ``xaxis``                  ``"month-alias"``  Labels of the x axis: ``"days"``, ``"month"``, ``"month-letter"`` or ``"month-alias"``.
        =========================  =================  ===========================================================================================

        :param show: option for showing instead of saving
        :type show: bool
        :param return_fig: option for returning the figure object
        :type return_fig: bool
        :return: figure object if ``return_fig`` is True, else None
        :rtype: :class:`matplotlib.figure.Figure` or None
        """
        return super().view(show=show, return_fig=return_fig)

    # Static methods
    # -------------------------------------------------------------------
    @staticmethod
    def _align_steps(dates):
        """
        Check that time steps repeat each year, moving monthly steps to the
        first day of the month.

        :param dates: dates of the series
        :type dates: :class:`pandas.Series`
        :return: dates with repeating steps
        :rtype: :class:`pandas.Series`
        """
        step = dates.sort_values().diff().dropna().mode()[0]
        day = pd.Timedelta(days=1)
        if 28 * day <= step <= 31 * day:
            return dates.dt.to_period("M").dt.to_timestamp()
        if step > day or day % step != pd.Timedelta(0):
            raise ValueError(
                f"Time step of {step} does not repeat each year. "
                "Use a monthly, daily or shorter step"
            )
        return dates


# Core spatial classes
# -----------------------------------------------------------------------


class Raster(GeoUnivar):
    """
    The basic Raster map dataset. A :class:`GeoUnivar` with a grid as data, in
    place of a table with geometries.

    """

    N_DRAW = 5000  # records to draw on the data and CDF panels
    var_min = LazyStat(getter="_get_var_min")
    var_max = LazyStat(getter="_get_var_max")

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
        self.datetime = None  # "2020-01-01"

        # call super
        super().__init__(name=name, alias=alias)
        # -------------------------------------
        # overwrite the defaults of the family
        self.varname = "Unknown variable"
        self.varalias = "UnVar"
        self.units = "unknown"
        self._set_view_specs()
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
    @property
    def data(self):
        """
        The grid. A new grid drops the statistics of the previous one.
        """
        return self._data

    @data.setter
    def data(self, grid):
        self._data = grid
        self._reset_stats()

    def _reset_stats(self):
        """
        Drop the statistics, to be computed again on next use.

        :return: None
        :rtype: None
        """
        super()._reset_stats()
        self.var_min = None
        self.var_max = None
        return None

    def _get_values(self):
        """
        Get the values of the grid, flat and cleared.

        :return: vector of values
        :rtype: :class:`numpy.ndarray`
        """
        return self.get_grid_data()

    def _get_var_min(self):
        values = self._get_values()
        return values.min() if values.size > 0 else None

    def _get_var_max(self):
        values = self._get_values()
        return values.max() if values.size > 0 else None

    def _thin(self, data):
        """
        Get evenly spaced records of a sequence, since a screen shows no more than a
        few thousand. Panels of statistics and the histogram still use all data.

        :param data: vector or dataframe, with one record for each value
        :type data: :class:`numpy.ndarray` or :class:`pandas.DataFrame`
        :return: thinned sequence
        :rtype: :class:`numpy.ndarray` or :class:`pandas.DataFrame`
        """
        return data[:: max(1, len(data) // self.N_DRAW)]

    def _set_fields(self):
        """
        Set fields names.
        Expected to increment superior methods.

        """
        # call super
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
        # call super
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

    def get_crs_info(self):
        """
        Get the EPSG code and the units of the cells, from the CRS or the projection
        file. Without the database of PROJ, a CRS may lose its EPSG code.

        :return: dictionary of ``epsg`` and ``units``, ``"m"`` or ``"deg."``. None if unknown.
        :rtype: dict
        """
        dc_info = {"epsg": None, "units": None}
        crs = self.raster_metadata["crs"]
        if crs is None and self.prj is not None:
            try:
                crs = rasterio.crs.CRS.from_wkt(self.prj)
            except rasterio.errors.CRSError:
                pass
        if crs is None:
            return dc_info

        # without PROJ, a CRS is neither of these, and asking only prints errors
        if crs.is_projected or crs.is_geographic:
            dc_info["epsg"] = crs.to_epsg()
        s_wkt = crs.to_wkt()
        if crs.is_geographic:
            dc_info["units"] = "deg."
        elif crs.linear_units in ["metre", "meter"] or 'UNIT["metre"' in s_wkt:
            dc_info["units"] = "m"
        elif 'UNIT["degree"' in s_wkt:
            dc_info["units"] = "deg."
        return dc_info

    def get_metadata_lines(self):
        """
        Get the lines of text of the metadata, for the annotations of the view.

        :return: lines of text
        :rtype: list
        """
        dc_meta = self.raster_metadata
        dc_crs = self.get_crs_info()
        s_cell = "{:.6g}".format(dc_meta["cellsize"])
        if dc_crs["units"] is not None:
            s_cell = "{} {}".format(s_cell, dc_crs["units"])
        n_nodata = dc_meta["NODATA_value"]
        return [
            "{:>5}: {}".format("Rows", dc_meta["nrows"]),
            "{:>5}: {}".format("Cols", dc_meta["ncols"]),
            "{:>5}: {}".format("Cell", s_cell),
            "{:>5}: {:.2f}".format("XLL", dc_meta["xllcorner"]),
            "{:>5}: {:.2f}".format("YLL", dc_meta["yllcorner"]),
            "{:>5}: {}".format("NaN", "n/a" if n_nodata is None else n_nodata),
            "{:>5}: {}".format("EPSG", dc_crs["epsg"] or "n/a"),
        ]

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
            _grid = np.ma.compressed(self.data)
            if _grid.dtype.kind in ["i", "u"]:
                # for integer grid
                return _grid
            else:
                # for floating point grid:
                return _grid[~np.isnan(_grid)]

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
        # always from the current grid, which may have been edited in place
        self.stats_df = self.get_basic_stats()
        return self.stats_df.copy()

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
        from plans.datasets.spatial import AOI

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
        # the grid is not a table, and specs hold the range of the map
        DataSet.update(self)
        # refresh all mutable attributes
        if self.data is not None:
            # data size
            self.size = self.raster_metadata["nrows"] * self.raster_metadata["ncols"]
            self._reset_stats()

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

    def set_array(self, array):
        """
        Set the data grid for the raster object. See :meth:`set_data`.

        :param array: The data grid to be set for the raster.
        :type array: :class:`numpy.ndarray`
        :return: None
        :rtype: None
        """
        self.set_data(grid=array)
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
        self.cellsize = self.raster_metadata["cellsize"]
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

    def load_metadata(self, file_data, id_band=1):
        """
        Load only metadata from files to the raster object.

        :param file_data: The path to the raster file.
        :type file_data: str
        :param id_band: Band id to read for GeoTIFF. Default value = 1
        :type id_band: int


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
        dc_metadata = Raster.read_tif_metadata(file_input=file_input, n_band=id_band)
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

        # handle prj
        if raster_ref.prj is not None:
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
        :return: file path to output file
        :rtype: str

        """
        if filename is None:
            filename = self.name
        # handle mode
        if mode == "asc":
            fo = self.export_asc(folder=folder, filename=filename)
        else:
            fo = self.export_tif(folder=folder, filename=filename)

        # export prj
        self.export_prj(folder=folder, filename=filename)

        return fo

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

    def _set_view_specs(self):
        """
        Set default view specs.

        """
        super()._set_view_specs()
        self.view_specs.update(
            {
                "cmap": self.cmap,
                "scheme_cmap": "continuous",
                "zorder_map": 0,  # below the grid
                "alpha": None,  # by the number of points
                "title": "{} | {}".format(self.varname, self.name),
                "run_id": None,
                "zoom_window": None,
            }
        )
        self.view_specs["ylabel"] = self.units
        return None

    def _plot(self, fig, gs, specs):
        """
        Plot the panels of the family, with the raster on the map panel.

        :param fig: The matplotlib figure object.
        :type fig: :class:`matplotlib.figure.Figure`
        :param gs: The matplotlib gridspec object for arranging subplots.
        :type gs: :class:`matplotlib.gridspec.GridSpec`
        :param specs: A dictionary containing plotting specifications and options.
        :type specs: dict
        :return: The modified matplotlib figure object with the plots.
        :rtype: :class:`matplotlib.figure.Figure`
        """
        # the figure follows the current grid, which may have been edited in place
        self._reset_stats()
        return super()._plot(fig=fig, gs=gs, specs=specs)

    def _get_annotation_columns(self):
        """
        Get the columns of annotations, with the metadata next to the statistics.

        :return: list of columns, each one a list of lines of text
        :rtype: list
        """
        ls_columns = super()._get_annotation_columns()
        if self.cellsize is not None:
            ls_columns.append(self.get_metadata_lines())
        return ls_columns

    def _draw_map(self, ax, cmap, norm, specs):
        """
        Draw the grid on the map panel, in map coordinates.

        :param ax: axis to plot on
        :type ax: :class:`matplotlib.axes.Axes`
        :param cmap: color map
        :type cmap: :class:`matplotlib.colors.Colormap`
        :param norm: norm of the color scheme
        :type norm: :class:`matplotlib.colors.Normalize`
        :param specs: plot specification dictionary
        :type specs: dict
        :return: None
        :rtype: None
        """
        # handle zoom window
        n_rows, n_cols = self.data.shape
        dc_zoom = {"i_min": 0, "i_max": n_rows, "j_min": 0, "j_max": n_cols}
        if specs["zoom_window"] is not None:
            dc_zoom = specs["zoom_window"]
        i_min, i_max = dc_zoom["i_min"], dc_zoom["i_max"]
        j_min, j_max = dc_zoom["j_min"], dc_zoom["j_max"]

        # handle extent. A grid without metadata stays in pixels
        extent = None
        if self.cellsize is not None:
            d = self.get_bbox()
            extent = [
                d["xmin"] + j_min * self.cellsize,
                d["xmin"] + j_max * self.cellsize,
                d["ymax"] - i_max * self.cellsize,
                d["ymax"] - i_min * self.cellsize,
            ]
        ax.imshow(
            self.data[i_min:i_max, j_min:j_max],
            cmap=cmap,
            norm=norm,
            extent=extent,
            interpolation="none",
            aspect="equal",
            origin="upper",
            zorder=specs["zorder_map"],
        )
        return None

    def view(self, show=True, return_fig=False):
        """
        Get the visualization, with the raster on the map panel. All layouts and view
        specs of :meth:`plans.datasets.analyst.GeoUnivar.view` are available, except
        for those of points. These are the differences:

        ====================  ================  =========================================================================
        Key                   Default           Description
        ====================  ================  =========================================================================
        ``scheme_cmap``       ``"continuous"``  Color scheme. Classes are also available, such as ``"equal"``.
        ``cmap``              auto              Name of the color map, from the ``cmap`` attribute.
        ``range``             auto              Range of the y axis and of continuous colors. None is set from the data.
        ``zoom_window``       None              Part of the grid on the map, as a dictionary of ``i_min``, ``i_max``, ``j_min`` and ``j_max``.
        ``zorder_map``        ``0``             Drawing order of the raster, which stays below the grid of the map.
        ``alpha``             None              Opacity of the data panel. None sets it by the number of points.
        ``run_id``            None              Not in use.
        ====================  ================  =========================================================================

        The data and CDF panels draw evenly spaced records, up to about ``N_DRAW``
        of them. The histogram and the statistics use all data.

        :param show: option for showing instead of saving
        :type show: bool
        :param return_fig: option for returning the figure object
        :type return_fig: bool
        :return: figure object if ``return_fig`` is True, else None
        :rtype: :class:`matplotlib.figure.Figure` or None
        """
        return super().view(show=show, return_fig=return_fig)

    # Static methods
    # -------------------------------------------------------------------

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


class SciRaster(Raster):
    """
    Scientific (float32) raster dataset with a configurable nodata value and display range.
    """

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
        # call super
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

    def get_normality(self, clevel=0.95):
        """
        Not available, since category IDs have no distribution.

        :param clevel: confidence level
        :type clevel: float
        :raises ValueError: always
        """
        raise ValueError("Normality is meaningless for category IDs")

    def get_cdf_gumbel(self):
        """
        Not available, since category IDs have no maxima.

        :raises ValueError: always
        """
        raise ValueError("The Gumbel CDF is meaningless for category IDs")

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
            df_stats = raster_sample.get_stats_df()
            lst_stats.append(df_stats)
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
        Plot the map panel of the family, with the areas of each class in place of
        the panels of statistics.

        :param fig: The matplotlib figure object.
        :type fig: :class:`matplotlib.figure.Figure`
        :param gs: The matplotlib gridspec object for arranging subplots.
        :type gs: :class:`matplotlib.gridspec.GridSpec`
        :param specs: A dictionary containing plotting specifications and options.
        :type specs: dict
        :return: The modified matplotlib figure object with the plots.
        :rtype: :class:`matplotlib.figure.Figure`
        """

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
        fig = GeoUnivar._build_axes(fig=fig, gs=gs, specs=specs)
        ax1 = fig.get_axes()[specs["ax_map"]]
        # one panel takes the place of the others
        for ax in fig.get_axes()[1:]:
            ax.remove()
        # the rows below are for the annotations
        n_max = min(n_max, 10)
        n_left = 21 if specs["layout"] == "full" else 18
        ax2 = fig.add_subplot(gs[2:n_max, n_left:32])

        if specs["title"] is not None:
            plt.suptitle(specs["title"], fontsize=9)

        # ------------ map plot ------------
        self._plot_map(ax=ax1, specs=specs)

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
            ax2.text(
                value + 0.05,
                index,
                "{:.1f}%".format(value * 100),
                ha="left",
                va="center",
                **viewer.get_annotation_specs(),
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

        if specs["layout"] == "full":
            self._plot_annotations(fig=fig, specs=specs)
        return fig

    def _get_annotation_columns(self):
        """
        Get the columns of annotations. Here, only the metadata.

        :return: list of columns, each one a list of lines of text
        :rtype: list
        """
        return [self.get_metadata_lines()] if self.cellsize is not None else []

    def _get_cmap_norm(self, specs):
        """
        Get the color map and the norm of the map panel, one color for each ID.

        :param specs: plot specification dictionary
        :type specs: dict
        :return: color map and norm
        :rtype: tuple
        """
        v_range = specs["range"]
        return specs["cmap"], mcolors.Normalize(vmin=v_range[0], vmax=v_range[1])

    def _set_view_specs(self):
        """
        Get default view specs


        """
        super()._set_view_specs()
        # the areas of each class play the role of the color bar
        self.view_specs["cbar_map"] = False
        # the panel of areas is the one above the annotations
        self.view_specs["ax_hist"] = 1
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

    def view(self, show=True, return_fig=False):
        """
        Get the visualization, with the map and the areas of each class. All layouts
        of :meth:`plans.datasets.analyst.GeoUnivar.view` and the keys of the map panel
        are available. These are the differences:

        ==================  =====================  =========================================================
        Key                 Default                Description
        ==================  =====================  =========================================================
        ``cmap``            auto                   Colors of the classes, from the table.
        ``range``           auto                   Range of the IDs, from the table.
        ``cbar_map``        ``False``              Show the color bar of the map. The areas take its role.
        ``color``           ``"tab:gray"``         Color of the bars of areas.
        ``use_alias``       ``False``              Label the bars with the alias of the classes.
        ``cutoff``          ``True``               Hide classes without area.
        ``max_classes``     ``15``                 Number of classes shown. Others are aggregated.
        ``subtitle_areas``  ``"Aereal ratios"``    Title of the panel of areas. None hides it.
        ``area_unit``       ``"km2"``              Unit of the total area: ``"m2"``, ``"ha"`` or ``"km2"``.
        ``total_area``      ``"Total area"``       Label of the total area.
        ==================  =====================  =========================================================

        :param show: option for showing instead of saving
        :type show: bool
        :param return_fig: option for returning the figure object
        :type return_fig: bool
        :return: figure object if ``return_fig`` is True, else None
        :rtype: :class:`matplotlib.figure.Figure` or None
        """
        return super().view(show=show, return_fig=return_fig)


class QualiHard(QualiRaster):
    """
    A Quali-Hard is a hard-coded qualitative map (that is, the table is pre-set)
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
        self.load_asc(file_input=asc_file)
        self.load_prj(file_input=prj_file)
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
        map_zones_aux.view(show=show)
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
        # call super
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
        u_cols = len(self.catalog["columns"].unique())
        u_rows = len(self.catalog["rows"].unique())
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
            _first = self.catalog[self.field_name].values[0]
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
            grd_stats = vct_stats.reshape(self.collection[_first].data.shape)
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

    # todo [develop] -- RasterSeries performance overhaul (see brainstorm 2026-08-21)
    #
    # 1. Fast/tiered loading for RasterSeries.load_folder
    #    - Tier 1: read files straight into a raw (time, rows, cols) numpy stack
    #      via rasterio.open() + np.stack(), no per-file Raster construction.
    #      Use file 1 as canonical template (projection, units, cmap, range).
    #    - Tier 2: cheap shape/CRS check per file against template; only build
    #      full Raster objects for outputs, not for every loaded input.
    #    - Fall back to full per-object RasterCollection path if check fails
    #      (folder violates RasterSeries same-grid/same-variable contract).
    #    - Parallelize Tier 1 reads (rasterio releases GIL) -- see existing
    #      "parallel loading" todo.
    #
    # 2. reduce() is NOT vectorized -- currently loops per-pixel in Python
    #    (flatten -> transpose -> for i in range(n_flat): reducer_func(...)).
    #    For RasterSeries (grids guaranteed aligned), replace with a single
    #    vectorized call on the stack: np.nanmean(stack, axis=0), etc.
    #    Keep to_mean/to_min/to_max/... public API, swap implementation only
    #    when is_same_grid() / RasterSeries context guarantees alignment.
    #
    # 3. Per-timestep stats (min/max/mean/nodata count) as byproduct of Tier 1
    #    stack load -- vectorized across the whole stack, cached as a small
    #    DataFrame on RasterSeries, instead of get_collection_stats() looping
    #    get_stats_df() per object. Keep full per-raster get_stats() as
    #    opt-in for single-raster inspection (percentiles, histograms).
    #
    # 4. MonthlyRasterSeries (RasterSeries subclass): month-only filename
    #    suffix (e.g. _YYYY-MM) instead of full date; needs its own datetime
    #    parser override, current logic hardcodes filename.split("_")[-1].
    #
    # 5. SPI/SPEI as SciRaster (single map) + SPISeries/SPEISeries
    #    (RasterSeries subclass) -- computed on top of items 1-3: rolling
    #    sum on raw stack -> group by end-month -> fit Gamma/log-logistic
    #    per pixel -> equiprobability transform to standard normal.

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
