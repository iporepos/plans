# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
{Short module description (1-3 sentences)}
todo docstring

Features
--------
todo docstring

* {feature 1}
* {feature 2}
* {feature 3}
* {etc}

Overview
--------
todo docstring
{Overview description}

Examples
--------
todo docstring
{Examples in rST}

Print a message

.. code-block:: python

    # print message
    print("Hello world!")
    # [Output] >> 'Hello world!'


"""
# IMPORTS
# ***********************************************************************
# import modules from other libs

# Native imports
# =======================================================================
import glob
import os.path
import shutil
from pathlib import Path

# ... {develop}

# External imports
# =======================================================================
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# ... {develop}

# Project-level imports
# =======================================================================
from plans.root import DataSet
from plans import geo
import plans.datasets as ds
from plans.analyst import Bivar

# ... {develop}


# CONSTANTS
# ***********************************************************************
# define constants in uppercase

# CONSTANTS -- Project-level
# =======================================================================
# ... {develop}

# Subsubsection example
# -----------------------------------------------------------------------
HELLO = "Hello World!"  # example
# ... {develop}

# CONSTANTS -- Module-level
# =======================================================================
# ... {develop}


# FUNCTIONS
# ***********************************************************************

# FUNCTIONS -- Project-level
# =======================================================================


def compute_decay(s, dt, k):
    # todo [docstring]
    #  Qt = dt * St / k
    return s * dt / k


def compute_flow(flow_pot, flow_cap):
    # todo [docstring]
    return np.where(flow_pot > flow_cap, flow_cap, flow_pot)


# ... {develop}

# FUNCTIONS -- Module-level
# =======================================================================
# ... {develop}


# CLASSES
# ***********************************************************************

# CLASSES -- Project-level
# =======================================================================


class Model(DataSet):
    # todo [optimize for DRY] move this class to root.py and make more abstract for all Models.
    #  Here can be a HydroModel(Model).
    """
    The core ``Model`` base object. Expected to hold one :class:`pandas.DataFrame` as simulation data and
    a dictionary as parameters. This is a dummy class to be developed downstream.

    """

    def __init__(self, name="MyModel", alias="HM01"):
        # ------------ call super ----------- #
        super().__init__(name=name, alias=alias)

        # defaults
        # self.field_datetime = "DateTime"

        # overwriters
        self.object_alias = "M"

        # variables
        self._set_model_vars()

        # parameters
        self.file_params = None  # global parameters
        self._set_model_params()

        # simulation data
        # dataframe for i/o and post-processing operations
        self.data = None
        # dict for fast numerical processing
        self.sdata = None
        self.slen = None

        # observed data
        self.filename_data_obs = "q_obs.csv"
        self.file_data_obs = None
        self.data_obs = None

        # evaluation parameters (model metrics)
        self.rmse = None
        self.rsq = None
        self.bias = None

        # run file
        self.file_model = None

        # flags
        self.update_dt_flag = True

        # testing helpers
        self.n_steps = None

        self._set_view_specs()

    def _set_fields(self):
        """
        Set fields names.
        Expected to increment superior methods.

        """
        # ------------ call super ----------- #
        super()._set_fields()
        # Attribute fields
        self.field_file_params = "file_parameters"
        self.field_folder_data = "folder_data"
        self.field_rmse = "rmse"
        self.field_rsq = "r2"
        self.field_bias = "bias"
        self.field_datetime = "datetime"
        self.field_units = "units"
        self.field_parameter = "parameter"
        self.field_id = "id"

        # ... continues in downstream objects ... #

    def _set_model_vars(self):
        # todo [docstrings]
        self.vars = {
            "t": {
                "units": "{k}",
                "description": "Accumulated time",
                "kind": "time",
            },
            "s": {
                "units": "mm",
                "description": "Storage level",
                "kind": "level",
            },
            "q": {
                "units": "mm/{dt_freq}",
                "description": "Outflow",
                "kind": "flow",
            },
            "san": {
                "units": "mm",
                "description": "Storage level (analytical solution)",
                "kind": "level",
            },
            "sobs": {
                "units": "mm",
                "description": "Storage level (observed evidence)",
                "kind": "level",
            },
        }
        self.var_eval = "s"

    def _set_model_params(self):
        """
        Internal method for setting up model parameters data

        :return: None
        :rtype: None
        """
        # model parameters
        self.params = {
            "k": {
                "value": None,
                "units": None,
                "dtype": np.float64,
                "description": "Residence time",
                "kind": "conceptual",
                "tex": None,
                "domain": None,
            },
            "S0": {
                "value": None,
                "units": "mm",  # default is mm
                "dtype": np.float64,
                "description": "Storage initial condition",
                "kind": "conceptual",
                "tex": None,
                "domain": None,
            },
            "dt": {
                "value": None,
                "units": None,
                "dtype": np.float64,
                "description": "Time Step in k units",
                "kind": "procedural",
                "tex": None,
                "domain": None,
            },
            "dt_freq": {
                "value": None,
                "units": "unitless",
                "dtype": str,
                "description": "Time Step frequency flag",
                "kind": "procedural",
            },
            "t0": {
                "value": None,
                "units": "timestamp",
                "dtype": str,
                "description": "Simulation start",
                "kind": "procedural",
                "tex": None,
                "domain": None,
            },
            "tN": {
                "value": None,
                "units": "timestamp",
                "dtype": str,
                "description": "Simulation end",
                "kind": "procedural",
                "tex": None,
                "domain": None,
            },
        }
        self.reference_dt_param = "k"
        return None

    def _set_view_specs(self):
        """
        Set view specifications.
        Expected to increment superior methods.

        :return: None
        :rtype: None
        """
        super()._set_view_specs()
        # cleanup useless entries
        dc_remove = {
            "xvar": "RM",
            "yvar": "TempDB",
            "xlabel": "RM",
            "ylabel": "TempDB",
            "color": self.color,
            "xmin": None,
            "xmax": None,
            "ymin": None,
            "ymax": None,
        }
        for k in dc_remove:
            del self.view_specs[k]
        # add new specs
        self.view_specs.update(
            {
                "width": 6,
                "height": 6,
            }
        )
        return None

    def get_vars(self):
        # todo [docstring]
        df = DataSet.dc2df(dc=self.vars, name="variable")
        df = df.sort_values(by="variable").reset_index(drop=True)
        return df

    def get_params(self):
        # todo [docstring]
        df = DataSet.dc2df(dc=self.params, name="parameter")
        df = df.sort_values(by="parameter").reset_index(drop=True)
        return df

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

        # remove useless fields
        del dict_meta[self.field_file_data]

        # customize local metadata:
        dict_meta_local = {
            self.field_rmse: self.rmse,
            self.field_rsq: self.rsq,
            self.field_bias: self.bias,
            self.field_file_params: self.file_params,
            self.field_folder_data: self.folder_data,
            # ... continue if necessary
        }

        # update
        dict_meta.update(dict_meta_local)
        return dict_meta

    def setter(self, dict_setter):
        """
        Set selected attributes based on an incoming dictionary.
        This is calling the superior method using load_data=False.

        :param dict_setter: incoming dictionary with attribute values
        :type dict_setter: dict
        :return: None
        :rtype: None
        """
        super().setter(dict_setter, load_data=False)

        # set new attributes
        self.file_params = Path(dict_setter[self.field_file_params])
        self.folder_data = Path(dict_setter[self.field_folder_data])

        # ... continues in downstream objects ... #
        return None

    def update(self):
        """
        Refresh all mutable attributes based on data (includins paths).
        Base method. This is overwrinting the superior method.

        :return: None
        :rtype: None
        """
        # refresh all mutable attributes

        # (re)set fields
        self._set_fields()

        # (re)set view specs
        ## self._set_view_specs()

        # update major attributes
        if self.data is not None:
            # data size (rows)
            self.size = len(self.data)

        # ... continues in downstream objects ... #
        return None

    def update_dt(self):
        """
        Update Time Step value, units and tag to match the model reference time parameter (like k)

        :return: None
        :rtype: None
        """
        # this flag prevents revisting the function unintentionally
        # todo actually this is more like a bad bugfix so it would be nice
        #  to remove the flag and optimize this process.
        if self.update_dt_flag:
            # handle inputs dt
            s_dt_unit_tag = str(self.params["dt"]["value"]) + self.params["dt"]["units"]

            # handle all good condition
            if s_dt_unit_tag == "1" + self.params[self.reference_dt_param]["units"]:
                pass
            else:
                #
                #
                # compute time step in reference units
                ft_aux = Model.get_timestep_factor(
                    from_unit=s_dt_unit_tag,
                    to_unit="1" + self.params[self.reference_dt_param]["units"],
                )
                #
                #
                # update
                self.params["dt"]["value"] = ft_aux
                self.params["dt"]["units"] = self.params[self.reference_dt_param][
                    "units"
                ][:]
                self.params["dt_freq"]["value"] = s_dt_unit_tag
            # shut down
            self.update_dt_flag = False
        return None

    def load_params(self):
        """
        Load parameter data

        :return: None
        :rtype: None
        """
        # -------------- load parameter data -------------- #

        #  develop logic in downstream objects

        return None

    def load_data(self):
        """
        Load simulation data. Expected to overwrite superior methods.

        :return: None
        :rtype: None
        """

        # -------------- load simulation data -------------- #

        # develop logic in downstream objects

        # -------------- update other mutables -------------- #
        self.update()

        # ... continues in downstream objects ... #

        return None

    def load(self):
        """
        Load parameters and data

        :return: None
        :rtype: None
        """
        # first params
        self.load_params()
        # then data
        self.load_data()
        return None

    def setup(self):
        """
        Set model simulation. Expected to be incremented downstream.

        .. warning::

            This method overwrites model data.


        :return: None
        :rtype: None
        """
        # ensure to update dt
        self.update_dt()
        # get timestep series
        vc_ts = Model.get_timestep_series(
            start_time=self.params["t0"]["value"],
            end_time=self.params["tN"]["value"],
            time_unit=self.params["dt_freq"]["value"],
        )
        vc_t = np.linspace(
            start=0,
            stop=len(vc_ts) * self.params["dt"]["value"],
            num=len(vc_ts),
            dtype=np.float64,
        )
        # built-up data
        self.slen = len(vc_t)
        # setup simulation data
        self.sdata = {
            self.field_datetime: vc_ts,
            "t": vc_t,
        }
        # setup
        # self.data = pd.DataFrame(self.sdata)
        # append variables to dataframe
        # develop logic in downstream objects

        # set initial conditions
        # develop logic in downstream objects

        return None

    def solve(self):
        """
        Solve the model for boundary and initial conditions by numerical methods.

        .. warning::

            This method overwrites model data.

        :return: None
        :rtype: None
        """
        # develop logic in downstream objects
        return None

    def evaluate(self):
        """
        Evaluate model.

        :return: None
        :rtype: None
        """
        # develop logic in downstream objects
        return None

    def run(self, setup_model=True):
        """
        Simulate model (full procedure).

        :param setup_model: flag for setting up data (default=True)
        :type setup_model: bool
        :return: None
        :rtype: None
        """
        if setup_model:  # by-passing setup may save computing time
            self.setup()
        self.solve()
        self.update()
        self.evaluate()
        return None

    def export(self, folder, filename):
        """
        Export object resources

        :param folder: path to folder
        :type folder: str
        :param filename: file name without extension
        :type filename: str
        :return: None
        :rtype: None
        """
        # export model simulation data
        super().export(folder, filename=filename, data_suffix="sim")

        # export model parameter file
        df_params = self.get_params()
        df_params.to_csv(f"{folder}/{filename}_params.csv", sep=";", index=False)

        # export model observation data
        # develop in downstream objects

        # ... continues in downstream objects ... #

    def save(self, folder):
        """
        Save to sourced files is not allowed for Model() family. Use .export() instead.
        This is overwriting superior methods.

        :return: None
        :rtype: None
        """
        return None

    def view(self, show=True):
        # develop logic in downstream object
        return None

    @staticmethod
    def get_timestep_factor(from_unit: str, to_unit: str) -> float:
        """
        Calculates the conversion factor between two time units.

        For instance, to find out how many days are in a given number of '10min' intervals,
        this function provides the multiplier.

        :param from_unit: The starting time unit (e.g., '10min', '15s').
        :type from_unit: str
        :param to_unit: The desired time unit (e.g., 'days', 'min').
        :type to_unit: str
        :return: The factor to convert from the starting to the desired time unit.
        :rtype: float
        """
        from_duration = pd.Timedelta(from_unit)
        to_duration = pd.Timedelta(to_unit)
        factor = to_duration.total_seconds() / from_duration.total_seconds()
        return 1 / factor

    @staticmethod
    def get_timestep_series(
        start_time: str, end_time: str, time_unit: str
    ) -> pd.DatetimeIndex:
        """
        Generates a time series of timestamps.

        Creates a sequence of timestamps between a start and end time,
        with a specified frequency.

        :param start_time: The starting timestamp for the series (e.g., '2024-01-01', '2024-01-01 00:00:00').
        :type start_time: str
        :param end_time: The ending timestamp for the series (e.g., '2024-01-10', '2024-01-10 23:59:59').
        :type end_time: str
        :param time_unit: The frequency or interval between timestamps (e.g., 'D' for day, 'H' for hour, '10min').
        :type time_unit: str
        :return: A pandas DatetimeIndex representing the generated time series.
        :rtype: pd.DatetimeIndex
        """
        raw_time_series = pd.date_range(start=start_time, end=end_time, freq=time_unit)
        time_series = pd.to_datetime(
            np.where(
                raw_time_series.microsecond > 0,
                raw_time_series.floor("s") + pd.Timedelta(seconds=1),
                raw_time_series,
            )
        )
        return time_series

    @staticmethod
    def get_gaussian_signal(
        value_max, size, sigma=50, position_factor=5, reverse=False
    ):
        """
        Generates a vector of normally (gaussian) distributed values. Useful for testing inputs inflows.

        :param value_max: actual maximum value in the vector
        :type value_max: float
        :param size: size of vector (time series size)
        :type size: int
        :param sigma: standard deviation for gaussian (normal) distribution.
        :type sigma: float
        :param position_factor: where to place the peak in the vector
        :type position_factor: float
        :param reverse: boolean to reverse position in order
        :type reverse: bool
        :return: vector of values
        :rtype: Numpy array
        """
        from scipy.ndimage import gaussian_filter

        # Create the initial signal
        v = np.zeros(size)
        # place peak
        v[int(len(v) / position_factor)] = value_max
        if reverse:
            v = v[::-1]
        # Apply Gaussian filter
        filtered_signal = gaussian_filter(v, sigma=len(v) / sigma)
        # Normalize the signal to have a maximum value of max_v
        normalized_signal = (filtered_signal / np.max(filtered_signal)) * value_max
        v_norm = normalized_signal * (normalized_signal > 0.01)
        return v_norm


# ... {develop}

# CLASSES -- Module-level
# =======================================================================
# ... {develop}


# SCRIPT
# ***********************************************************************
# standalone behaviour as a script
if __name__ == "__main__":
    # Test doctests
    # ===================================================================
    import doctest

    doctest.testmod()

    # Script section
    # ===================================================================
    print("Hello world!")
    # ... {develop}

    # Script subsection
    # -------------------------------------------------------------------
    # ... {develop}
