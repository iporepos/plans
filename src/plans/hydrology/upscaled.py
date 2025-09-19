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
# import {module}
# ... {develop}

# External imports
# =======================================================================
import numpy as np
import pandas as pd

# ... {develop}

# Project-level imports
# =======================================================================
from plans.hydrology.core import Model

# ... {develop}


# CONSTANTS
# ***********************************************************************
# define constants in uppercase

# CONSTANTS -- Project-level
# =======================================================================
# ... {develop}

# CONSTANTS -- Module-level
# =======================================================================
# ... {develop}


# FUNCTIONS
# ***********************************************************************

# FUNCTIONS -- Project-level
# =======================================================================
# ... {develop}

# FUNCTIONS -- Module-level
# =======================================================================
# ... {develop}


# CLASSES
# ***********************************************************************

# CLASSES -- Project-level
# =======================================================================


class LinearStorage(Model):
    """
    Linear Storage Model. This is a Toy Model. No inflow, only outflows. Simulates storage decay only.

    """

    def __init__(self, name="MyLinearStorage", alias="LS01"):
        # todo [docstring]
        # ------------ call super ----------- #
        super().__init__(name=name, alias=alias)
        # overwriters
        self.object_alias = "LS"
        # expected filenames
        self.file_data_obs = None
        self.filename_data_obs = "S_obs.csv"
        self.folder_data_obs = None

    def _set_model_vars(self):
        # todo [docstring]
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
        """Intenal method for setting up model parameters data

        :return: None
        :rtype: None
        """
        # model parameters
        self.params = {
            "k": {
                "value": None,
                "units": "d",
                "dtype": np.float64,
                "description": "Residence time",
                "kind": "conceptual",
                "tex": None,
                "domain": "soils",
            },
            "s0": {
                "value": None,
                "units": "mm",  # default is mm
                "dtype": np.float64,
                "description": "Storage initial condition",
                "kind": "conceptual",
                "domain": "soils",
                "tex": None,
            },
            "dt": {
                "value": None,
                "units": None,
                "dtype": np.float64,
                "description": "Time Step in k units",
                "kind": "procedural",
                "domain": "time",
                "tex": None,
            },
            "dt_freq": {
                "value": None,
                "units": "unitless",
                "dtype": str,
                "description": "Time Step frequency flag",
                "kind": "procedural",
                "domain": "time",
                "tex": None,
            },
            "t0": {
                "value": None,
                "units": "timestamp",
                "dtype": str,
                "description": "Simulation start",
                "kind": "procedural",
                "domain": "time",
                "tex": None,
            },
            "tN": {
                "value": None,
                "units": "timestamp",
                "dtype": str,
                "description": "Simulation end",
                "kind": "procedural",
                "domain": "time",
                "tex": None,
            },
        }
        self.reference_dt_param = "k"
        return None

    def setter(self, dict_setter):
        """
        Set selected attributes based on an incoming dictionary.
        This is calling the superior method using load_data=False.

        :param dict_setter: incoming dictionary with attribute values
        :type dict_setter: dict
        :return: None
        :rtype: None
        """
        super().setter(dict_setter)

        # specific files
        self.folder_data_obs = self.folder_data  # same here

        # ... continues in downstream objects ... #
        return None

    def load_params(self):
        """
        Load parameter data from parameter file (stored in `self.file_params`)

        .. warning::

            This method overwrites model data.

        :return: None
        :rtype: None
        """
        # load dataframe
        df_ = pd.read_csv(
            self.file_params, sep=self.file_csv_sep, encoding="utf-8", dtype=str
        )
        ls_input_params = [p.lower() for p in df_["parameter"]]
        df_["parameter"] = ls_input_params

        # parse to dict
        for p in self.params:
            if p in set(ls_input_params):
                # set value
                self.params[p][self.field_bootfile_value] = self.params[p]["dtype"](
                    df_.loc[df_["parameter"] == p, self.field_bootfile_value].values[0]
                )
                # units
                self.params[p]["units"] = df_.loc[
                    df_["parameter"] == p, "units"
                ].values[0]
                # min
                self.params[p]["min"] = self.params[p]["dtype"](
                    df_.loc[df_["parameter"] == p, "min"].values[0]
                )
                # max
                self.params[p]["max"] = self.params[p]["dtype"](
                    df_.loc[df_["parameter"] == p, "max"].values[0]
                )

        # handle inputs dt
        self.update_dt()

        return None

    def load_data(self):
        """
        Load simulation data from folder data (stored in `self.folder_data`). Overwrites superior methods.

        .. warning::

            This method overwrites model data.

        :return: None
        :rtype: None
        """
        # -------------- load observation data -------------- #
        self.file_data_obs = Path(f"{self.folder_data_obs}/{self.filename_data_obs}")
        self.data_obs = pd.read_csv(
            self.file_data_obs,
            sep=self.file_csv_sep,
            encoding=self.file_encoding,
            parse_dates=[self.field_datetime],
        )

        # -------------- update other mutables -------------- #
        self.update()

        # ... continues in downstream objects ... #

        return None

    def setup(self):
        """
        Set model simulation.

        .. warning::

            This method overwrites model data.


        :return: None
        :rtype: None
        """
        # setup superior object
        super().setup()

        # append extra variables to dict
        self.sdata["s"] = np.full(self.slen, np.nan)
        self.sdata["q"] = np.full(self.slen, np.nan)
        self.sdata["S_a"] = np.full(self.slen, np.nan)

        # set initial conditions
        self.sdata["s"][0] = self.params["s0"]["value"]

        return None

    def solve(self):
        """
        Solve the model for inputs and initial conditions by numerical methods.

        .. warning::

            This method overwrites model data.

        :return: None
        :rtype: None
        """
        # get data pointer
        sdata = self.sdata

        # make simpler variables for clarity
        k = self.params["k"]["value"]
        dt = self.params["dt"]["value"]

        # simulation steps (this is useful for testing and debug)
        if self.n_steps is None:
            n_steps = self.slen
        else:
            n_steps = self.n_steps

        # --- analytical solution
        sdata["S_a"][:] = self.params["s0"]["value"] * np.exp(-sdata["t"] / k)

        # --- numerical solution
        # loop over (Euler Method)
        for t in range(n_steps - 1):
            sdata["q"][t] = compute_decay(s=sdata["s"][t], dt=dt, k=k)
            sdata["s"][t + 1] = sdata["s"][t] - sdata["q"][t]

        # reset data
        self.data = pd.DataFrame(sdata)

        return None

    def get_evaldata(self):
        # todo [docstring]
        # merge simulation and observation data based
        df = pd.merge(
            left=self.data, right=self.data_obs, on=self.field_datetime, how="left"
        )

        # remove other columns
        df = df[[self.field_datetime, self.var_eval, "{}_obs".format(self.var_eval)]]

        # remove voids
        df.dropna(subset=["{}_obs".format(self.var_eval)], inplace=True)

        # handle scaling factor for flows (expected to be in k-units)
        factor = 1.0
        if self.vars[self.var_eval]["kind"] == "flow":
            factor = self.params["dt"]["value"]
        # scale the factor
        df["{}".format(self.var_eval)] = df["{}".format(self.var_eval)] / factor
        return df

    def evaluate(self):
        """
        Evaluate model metrics.

        :return: None
        :rtype: None
        """
        df = self.get_evaldata()

        # evaluate paired data
        vc_pred = df[self.var_eval].values
        vc_obs = df["{}_obs".format(self.var_eval)].values

        # compute evaluation metrics
        self.rmse = Bivar.rmse(pred=vc_pred, obs=vc_obs)
        self.rsq = Bivar.rsq(pred=vc_pred, obs=vc_obs)
        self.bias = Bivar.bias(pred=vc_pred, obs=vc_obs)

        return None

    def export(self, folder, filename, views=False):
        """
        Export object resources.

        :param folder: path to folder
        :type folder: str
        :param filename: file name without extension
        :type filename: str
        :return: None
        :rtype: None
        """
        # export model simulation data
        super().export(folder, filename=filename)

        # export model observation data
        df_obs = self.get_evaldata()
        fpath = Path(folder + "/" + filename + "_obs" + self.file_csv_ext)
        df_obs.to_csv(
            fpath, sep=self.file_csv_sep, encoding=self.file_encoding, index=False
        )

        # export views
        if views:
            self.view_specs["folder"] = folder
            self.view_specs["filename"] = filename
            self.view(show=False)

        # ... continues in downstream objects ... #

    def view(self, show=True):
        # todo [docstring]
        plt.rcParams["font.family"] = "Arial"
        specs = self.view_specs.copy()
        ts = ds.TimeSeries(name=self.name, alias=self.alias)
        ts.set_data(
            input_df=self.data, input_dtfield=self.field_datetime, input_varfield="s"
        )
        ts.view_specs["title"] = "Linear Model - R2: {}".format(round(self.rsq, 2))
        fig = ts.view(show=False, return_fig=True)
        # obs series plot
        # access axes from fig
        axes = fig.get_axes()
        ax = axes[0]
        ax.plot(
            self.data_obs[self.field_datetime], self.data_obs["sobs"], ".", color="k"
        )
        # handle return
        if show:
            plt.show()
        else:
            file_path = "{}/{}.{}".format(
                specs["folder"], specs["filename"], specs["fig_format"]
            )
            plt.savefig(file_path, dpi=specs["dpi"])
            plt.close(fig)
            return None


class LSRR(LinearStorage):
    # todo [major docstring improvement]
    """
    Rainfall-Runoff model based on a Linear Storage. This is a Toy Model. Inflow rain (P) in a necessary data inputs.

    """

    def __init__(self, name="MyLSRR", alias="LSRR001"):
        # todo [docstring]
        super().__init__(name=name, alias=alias)
        # overwriters
        self.object_alias = "LSRR"

        # observation data
        self.filename_data_obs = "q_obs.csv"

        # inputs data
        self.data_clim = None
        self.file_data_clim = None
        self.folder_data_clim = None
        self.filename_data_clim = "clim.csv"

    def _set_model_params(self):
        """
        Intenal method for setting up model parameters data

        :return: None
        :rtype: None
        """
        super()._set_model_params()
        # model parameters
        self.params.update(
            {
                "q_max": {
                    "value": None,
                    "units": "mm/{dt_freq}",
                    "dtype": np.float64,
                    "description": "Downstream limiting control for Q",
                    "kind": "conceptual",
                    "tex": "$Q_{max}$",
                    "domain": "soils",
                },
            }
        )

        return None

    def _set_model_vars(self):
        # todo [docstring]
        self.vars = {
            "t": {
                "units": "{k}",
                "description": "Accumulated time",
                "kind": "time",
                "tex": "$t$",
            },
            "p": {
                "units": "mm/{dt_freq}",
                "description": "Inflow",
                "kind": "flow",
                "tex": "$P$",
            },
            "s": {
                "units": "mm",
                "description": "Storage level",
                "kind": "level",
                "tex": "$S$",
            },
            "q": {
                "units": "mm/{dt_freq}",
                "description": "Outflow",
                "kind": "flow",
                "tex": "$Q$",
            },
            "q_obs": {
                "units": "mm/d",
                "description": "Outflow (observed evidence)",
                "kind": "flow",
                "tex": "$Q_{obs}$",
            },
        }
        self.var_eval = "q"
        self.var_inputs = ["p"]
        return None

    def _set_view_specs(self):
        """
        Set view specifications. Expected to increment superior methods.

        :return: None
        :rtype: None
        """
        super()._set_view_specs()
        # cleanup useless entries

        # add new specs
        self.view_specs.update(
            {
                # update vales
                "gs_wspace": 0.4,
                "gs_hspace": 0.7,
                "gs_left": 0.15,
                "gs_right": 0.85,
                "gs_bottom": 0.1,
                "gs_top": 0.9,
                # new params
                "color_P": "tab:gray",
                "color_Q": "blue",
                "color_Q_obs": "indigo",
                "color_S": "black",
                "ymax_P": None,
                "ymax_Q": None,
                "ymax_S": None,
            }
        )
        return None

    def setter(self, dict_setter):
        """
        Set selected attributes based on an incoming dictionary.
        This is calling the superior method using load_data=False.

        :param dict_setter: incoming dictionary with attribute values
        :type dict_setter: dict
        :return: None
        :rtype: None
        """
        super().setter(dict_setter)

        # specific files
        self.folder_data_clim = self.folder_data  # same here

        # ... continues in downstream objects ... #
        return None

    def load_data(self):
        """
        Load input simulation data. Expected to overwrite superior methods.

        .. warning::

            This method overwrites model data.

        :return: None
        :rtype: None
        """

        # -------------- load climate inputs data -------------- #
        self.file_data_clim = Path(f"{self.folder_data_clim}/{self.filename_data_clim}")
        df_data_input = pd.read_csv(
            self.file_data_clim,
            sep=self.file_csv_sep,
            encoding=self.file_encoding,
            parse_dates=[self.field_datetime],
        )

        # Format the datetime column to string (e.g., 'YYYY-MM-DD HH:MM:SS')
        df_data_input["DT_str"] = df_data_input[self.field_datetime].dt.strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        # set t0 and tN
        self.params["t0"]["value"] = df_data_input["DT_str"].values[0]
        self.params["tN"]["value"] = df_data_input["DT_str"].values[-1]

        # set the data inputs for climate
        self.data_clim = df_data_input[[self.field_datetime] + self.var_inputs].copy()
        self.data_clim_src = self.data_clim.copy()

        # -------------- load observation data -------------- #
        self.file_data_obs = Path(f"{self.folder_data_obs}/{self.filename_data_obs}")
        self.data_obs = pd.read_csv(
            self.file_data_obs,
            sep=self.file_csv_sep,
            encoding=self.file_encoding,
            parse_dates=[self.field_datetime],
        )

        # -------------- update other mutables -------------- #
        self.update()

        # ... continues in downstream objects ... #

        return None

    def setup(self):
        """
        Set model simulation data.

        .. warning::

            This method overwrites model data.

        :return: None
        :rtype: None
        """
        # setup superior object
        super().setup()

        # drop superior meaningless columns
        del self.sdata["S_a"]
        ## self.data.drop(columns=["S_a"], inplace=True)

        # handle inputs P values
        rs = ds.RainSeries()
        rs.set_data(
            input_df=self.data_clim.copy(),
            input_varfield="p",
            input_dtfield=self.field_datetime,
        )
        df_downscaled = rs.downscale(freq=self.params["dt_freq"]["value"])

        # set interpolated inputs variables
        self.sdata["p"] = df_downscaled["P"].values[:]

        return None

    def solve(self):
        """
        Solve the model for inputs and initial conditions by numerical methods.

        .. warning::

            This method overwrites model data.

        :return: None
        :rtype: None
        """
        # make simpler variables for clarity
        k = self.params["k"]["value"]
        qmax = self.params["q_max"]["value"]
        dt = self.params["dt"]["value"]

        # get data reference
        sdata = self.sdata

        # simulation steps (this is useful for testing and debug)
        if self.n_steps is None:
            n_steps = self.slen
        else:
            n_steps = self.n_steps

        # --- numerical solution
        # loop over (Euler Method)
        for t in range(n_steps - 1):
            # Qt = dt * St / k
            sdata["q"][t] = np.min([compute_decay(s=sdata["s"][t], dt=dt, k=k), qmax])
            # S(t + 1) = S(t) + P(t) - Q(t)
            sdata["s"][t + 1] = sdata["s"][t] + sdata["p"][t] - sdata["q"][t]

        # set io data
        self.data = pd.DataFrame(sdata)
        self.data = self.data[[self.field_datetime, "t", "p", "q", "s"]].copy()

        return None

    def view(self, show=True, return_fig=False):
        # todo [docstring]
        specs = self.view_specs.copy()
        n_dt = self.params["dt"]["value"]
        # start plot
        fig = plt.figure(figsize=(specs["width"], specs["height"]))  # Width, Height
        plt.suptitle("{} | Model LSRR - R2: {}".format(self.name, round(self.rsq, 3)))
        # grid
        gs = mpl.gridspec.GridSpec(
            3,
            1,
            wspace=specs["gs_wspace"],
            hspace=specs["gs_hspace"],
            left=specs["gs_left"],
            right=specs["gs_right"],
            bottom=specs["gs_bottom"],
            top=specs["gs_top"],
        )  # nrows, ncols

        first_date = self.data[self.field_datetime].iloc[0]
        last_date = self.data[self.field_datetime].iloc[-1]
        ls_dates = [first_date, last_date]
        n_flow_max = np.max([self.data["p"].max(), self.data["q"].max()])

        # ------------ P plot ------------
        n_pmax = self.data["p"].max() / n_dt
        ax = fig.add_subplot(gs[0, 0])
        plt.plot(
            self.data[self.field_datetime],
            self.data["p"] / n_dt,
            color=specs["color_P"],
            zorder=2,
        )
        plt.title("$P$ ({} mm)".format(round(self.data["p"].sum(), 1)), loc="left")
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
        ax.set_xticks(ls_dates)
        # normalize X axis
        plt.xlim(ls_dates)
        # normalize Y axis
        ymax_p = specs["ymax_P"]
        if ymax_p is None:
            ymax_p = 1.2 * n_pmax
        plt.ylim(0, ymax_p)
        plt.ylabel("mm/{}".format(self.params["dt"]["units"].lower()))

        # ------------ Q plot ------------
        n_qmax = np.max([self.data["q"].max() / n_dt, self.data_obs["q_obs"].max()])
        # n_qmax = self.data["q"].max() / n_dt
        q_sum = round(self.data["q"].sum(), 1)
        ax = fig.add_subplot(gs[1, 0])
        # titles
        plt.title("$Q$ ({} mm) ".format(q_sum), loc="left")
        plt.title(
            "$Q_{obs}$" + " ({} mm)".format(round(self.data_obs["q_obs"].sum(), 1)),
            loc="right",
        )
        # plots
        plt.plot(
            self.data[self.field_datetime],
            self.data["q"] / n_dt,
            color=specs["color_Q"],
        )
        plt.plot(
            self.data_obs[self.field_datetime],
            self.data_obs["q_obs"],
            ".",
            color=specs["color_Q_obs"],
        )
        # tic labels
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
        ax.set_xticks(ls_dates)
        # normalize X axis
        plt.xlim(ls_dates)
        # normalize Y axis
        ymax_q = specs["ymax_Q"]
        if ymax_q is None:
            ymax_q = 1.2 * n_qmax
        plt.ylim(0, 1.2 * ymax_q)
        plt.ylabel("mm/{}".format(self.params["dt"]["units"].lower()))

        # ------------ S plot ------------
        n_smax = self.data["s"].max()
        ax = fig.add_subplot(gs[2, 0])
        plt.title(
            r"$S$ ($\mu$ = {} mm)".format(round(self.data["s"].mean(), 1)), loc="left"
        )
        plt.plot(self.data[self.field_datetime], self.data["s"], color=specs["color_S"])
        # ticks
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
        ax.set_xticks(ls_dates)
        # normalize X axis
        plt.xlim(ls_dates)
        plt.ylabel("mm")
        # normalize Y axis
        ymax_s = specs["ymax_S"]
        if ymax_s is None:
            ymax_s = 1.2 * n_smax
        plt.ylim(0, ymax_s)

        # handle return
        if return_fig:
            return fig
        else:
            if show:
                plt.show()
            else:
                file_path = "{}/{}.{}".format(
                    specs["folder"], specs["filename"], specs["fig_format"]
                )
                plt.savefig(file_path, dpi=specs["dpi"])
                plt.close(fig)


class LSRRE(LSRR):
    # todo [major docstring improvement]
    """
    Rainfall-Runoff-Evaporation model based on a Linear Storage. This is a Toy Model.
    Inflow rain (P) and outflow potential evaporation (E_pot) are necessary data inputs.

    """

    def __init__(self, name="MyLSRRE", alias="LSRRE001"):
        super().__init__(name=name, alias=alias)
        # overwriters
        self.object_alias = "LSRRE"
        # controllers
        self.shutdown_epot = False

    def _set_model_vars(self):
        # todo [docstring]
        super()._set_model_vars()
        self.vars.update(
            {
                "e": {
                    "units": "mm/{dt_freq}",
                    "description": "External Outflow",
                    "kind": "flow",
                    "tex": "$E$",
                },
                "e_pot": {
                    "units": "mm/{dt_freq}",
                    "description": "Maximal External Outflow",
                    "kind": "flow",
                    "tex": "$E_{pot}$",
                },
            }
        )
        self.var_inputs = ["p", "e_pot"]

    def setup(self):
        """
        Set model simulation.

        .. warning::

            This method overwrites model data.


        :return: None
        :rtype: None
        """
        # setup superior object
        super().setup()

        # set E (actual)
        self.sdata["e"] = np.full(self.slen, np.nan)

        # handle inputs E_pot values
        rs = ds.RainSeries()  # todo best practice is to have a EvapoSeries() object
        rs.varfield = "e_pot"
        rs.varname = "e_pot"
        rs.set_data(
            input_df=self.data_clim,
            input_varfield="e_pot",
            input_dtfield=self.field_datetime,
        )
        df_downscaled = rs.downscale(freq=self.params["dt_freq"]["value"])

        # set interpolated inputs variables
        self.sdata["e_pot"] = df_downscaled["e_pot"].values[:]

        return None

    def solve(self):
        """
        Solve the model for inputs and initial conditions by numerical methods.

        .. warning::

            This method overwrites model data.

        :return: None
        :rtype: None
        """
        # make simpler variables for clarity
        k = self.params["k"]["value"]
        qmax = self.params["q_max"]["value"]
        dt = self.params["dt"]["value"]

        # get data reference
        sdata = self.sdata

        # simulation steps (this is useful for testing and debug)
        if self.n_steps is None:
            n_steps = self.slen
        else:
            n_steps = self.n_steps

        if self.shutdown_epot:
            sdata["e_pot"] = np.full(self.slen, 0.0)

        # --- numerical solution
        # loop over (Euler Method)
        for t in range(n_steps - 1):
            # potential flow
            q_pot = np.min([compute_decay(s=sdata["s"][t], dt=dt, k=k), qmax])

            # Et = Et_pot
            e_pot = sdata["e_pot"][t]

            # Potential outflow O_pot
            o_pot = q_pot + e_pot

            # Maximum outflow Omax = St
            o_max = sdata["s"][t]

            # actual outflow
            o_act = np.min([o_max, o_pot])

            # allocate Q and E
            with np.errstate(divide="ignore", invalid="ignore"):
                sdata["q"][t] = o_act * np.where(o_pot == 0, 0, q_pot / o_pot)
                sdata["e"][t] = o_act * np.where(o_pot == 0, 0, e_pot / o_pot)

            # S(t + 1) = S(t) + P(t) - Q(t) - E(t)
            sdata["s"][t + 1] = (
                sdata["s"][t] + sdata["p"][t] - sdata["q"][t] - sdata["e"][t]
            )

        # set data
        self.data = pd.DataFrame(sdata)
        # organize cols
        ls_vars = [self.field_datetime, "t", "p", "e_pot", "e", "q", "s"]
        self.data = self.data[ls_vars].copy()

        return None

    def view(self, show=True, return_fig=False):
        # todo [docstring]
        specs = self.view_specs.copy()
        n_dt = self.params["dt"]["value"]
        fig = super().view(show=False, return_fig=True)
        plt.suptitle("{} | Model LSRRE - R2: {}".format(self.name, round(self.rsq, 3)))
        axes = fig.get_axes()
        # ---- E plot
        ax = axes[0]
        e_sum = round(self.data["e"].sum(), 1)
        ax2 = ax.twinx()  # Create a second y-axis that shares the same x-axis
        ax2.plot(
            self.data[self.field_datetime], self.data["e"] / n_dt, c="tab:red", zorder=1
        )
        e_max = self.data["e"].max()
        if e_max == 0:
            ax2.set_ylim(-1, 1)
        else:
            ax2.set_ylim(0, 1.2 * e_max / n_dt)
        ax2.set_title("$E$ ({} mm)".format(e_sum), loc="right")
        ax2.set_ylabel("mm/d")
        # handle return
        if return_fig:
            return fig
        else:
            if show:
                plt.show()
            else:
                file_path = "{}/{}.{}".format(
                    specs["folder"], specs["filename"], specs["fig_format"]
                )
                plt.savefig(file_path, dpi=specs["dpi"])
                plt.close(fig)


class LSFAS(LSRRE):
    # todo [major docstring improvement]
    """
    Rainfall-Runoff-Evaporation model based on Linear Storage and Fill-And-Spill (FAS) mechanism.
    Inflow rain (P) and potential evapotranspiration (E_pot) are necessary data inputs.

    """

    def __init__(self, name="MyLSFAS", alias="LSFAS001"):
        # todo [docstring]
        super().__init__(name=name, alias=alias)
        # overwriters
        self.object_alias = "LSFAS"
        # controllers:
        self.shutdown_qb = False

    def _set_model_vars(self):
        super()._set_model_vars()
        # todo [refactor] update TeX symbols
        self.vars.update(
            {
                "ss": {
                    "units": "mm",
                    "description": "Spill storage",
                    "kind": "flow",
                    "tex": "tex",
                },
                "qs": {
                    "units": "mm/{dt_freq}",
                    "description": "Spill flow (outflow)",
                    "kind": "flow",
                    "tex": "tex",
                },
                "qsf": {
                    "units": "mm/mm",
                    "description": "Spill flow fraction",
                    "kind": "constant",
                    "tex": "tex",
                },
                "qb": {
                    "units": "mm/{dt_freq}",
                    "description": "Base flow (outflow)",
                    "kind": "flow",
                    "tex": "tex",
                },
            }
        )
        return None

    def _set_model_params(self):
        """
        Intenal method for setting up model parameters data

        :return: None
        :rtype: None
        """
        super()._set_model_params()
        # clean useless model parameters from upstream
        del self.params["q_max"]
        # add new params
        self.params.update(
            {
                "s_a": {
                    "value": None,
                    "units": "mm",
                    "dtype": np.float64,
                    "description": "Activation level for storage spill",
                    "kind": "conceptual",
                    "tex": "$s_{a}$",
                    "domain": "lulc",
                },
                "s_c": {
                    "value": None,
                    "units": "mm",
                    "dtype": np.float64,
                    "description": "Effective fragmentantion level of storage",
                    "kind": "conceptual",
                    "tex": "$s_{c}$",
                    "domain": "lulc",
                },
            }
        )
        self.reference_dt_param = "k"
        return None

    def setup(self):
        """
        Set model simulation.

        .. warning::

            This method overwrites model data.


        :return: None
        :rtype: None
        """
        # setup superior object
        super().setup()

        # add new columns
        self.sdata["qs"] = np.full(self.slen, np.nan)
        self.sdata["qb"] = np.full(self.slen, np.nan)
        self.sdata["qsf"] = np.full(self.slen, np.nan)
        self.sdata["ss"] = np.full(self.slen, np.nan)

        return None

    def solve(self):
        """
        Solve the model for inputs and initial conditions by numerical methods.

        .. warning::

            This method overwrites model data.

        :return: None
        :rtype: None
        """
        # make simpler variables for clarity
        k = self.params["k"]["value"]
        s_a = self.params["s_a"]["value"]
        s_c = self.params["s_c"]["value"]
        # dt is the fraction of 1 Day/(1 simulation time step)
        dt = self.params["dt"]["value"]
        # get reference data
        sdata = self.sdata

        # simulation steps (this is useful for testing and debug)
        if self.n_steps is None:
            n_steps = self.slen
        else:
            n_steps = self.n_steps

        # remove E_pot (useful for testing)
        if self.shutdown_epot:
            sdata["e_pot"] = np.full(self.slen, 0.0)

        # --- numerical solution
        # loop over (Euler Method)
        for t in range(n_steps - 1):
            # Compute dynamic spill storage capacity in mm/D
            ss_cap = np.max([0, sdata["s"][t] - s_a])  # spill storage = s - s_a
            sdata["ss"][t] = ss_cap

            # Compute runoff fraction
            with np.errstate(divide="ignore", invalid="ignore"):
                qs_f = np.where((ss_cap + s_c) == 0, 0, (ss_cap / (ss_cap + s_c)))
            sdata["qsf"][t] = qs_f

            # potential runoff -- scale by the fraction

            # compute dynamic runoff capacity

            # -- includes P in the Qs capacity
            qs_cap = (ss_cap * dt) + sdata["p"][t]  # multiply by dt (figure out why!)

            # apply runoff fraction over Qs
            qs_pot = qs_f * qs_cap

            # Compute potential base flow
            # Qt = dt * St / k
            # useful for testing
            if self.shutdown_qb:
                qb_pot = np.full(self.slen, 0.0)
            else:
                qb_pot = compute_decay(s=sdata["s"][t], dt=dt, k=k)

            # Compute potential evaporation flow
            # Et = E_pot
            e_pot = sdata["e_pot"][t]

            # Compute Potential outflow O_pot
            o_pot = qs_pot + qb_pot + e_pot

            # Compute Maximum outflow Omax = St
            o_max = sdata["s"][t]

            # Compute actual outflow
            o_act = np.min([o_max, o_pot])

            # Allocate outflows
            with np.errstate(divide="ignore", invalid="ignore"):
                sdata["qs"][t] = o_act * np.where(o_pot == 0, 0, qs_pot / o_pot)
                sdata["qb"][t] = o_act * np.where(o_pot == 0, 0, qb_pot / o_pot)
                sdata["e"][t] = o_act * np.where(o_pot == 0, 0, e_pot / o_pot)

            # Compute full Q
            sdata["q"][t] = sdata["qs"][t] + sdata["qb"][t]

            # Apply Water balance
            # S(t + 1) = S(t) + P(t) - Qs(t) - Qb(t) - E(t)
            sdata["s"][t + 1] = (
                sdata["s"][t]
                + sdata["p"][t]
                - sdata["qs"][t]
                - sdata["qb"][t]
                - sdata["e"][t]
            )
        # reset data
        self.data = pd.DataFrame(sdata)
        # organize table
        ls_vars = [
            self.field_datetime,
            "t",
            "p",
            "e_pot",
            "e",
            "qs",
            "qsf",
            "qb",
            "q",
            "s",
            "ss",
        ]
        self.data = self.data[ls_vars].copy()

        return None

    def view(self, show=True, return_fig=False):
        # todo [docstring]
        specs = self.view_specs.copy()
        fig = super().view(show=False, return_fig=True)
        plt.suptitle("{} | Model LSFAS - R2: {}".format(self.name, round(self.rsq, 1)))
        axes = fig.get_axes()
        # add Qb
        ax = axes[1]
        q_sum = round(self.data["q"].sum(), 1)
        qb_sum = round(self.data["qb"].sum(), 1)
        ax.set_title(
            "$Q$ ({} mm)".format(q_sum)
            + ", $Q_b$ ({} mm)".format(qb_sum)
            + " and $Q_{obs}$",
            loc="left",
        )
        ax.plot(
            self.data[self.field_datetime],
            self.data["qb"] / self.params["dt"]["value"],
            c="navy",
            zorder=1,
        )
        ax.set_title("Runoff C", loc="right")
        ax2 = ax.twinx()  # Create a second y-axis that shares the same x-axis
        ax2.plot(self.data[self.field_datetime], self.data["qsf"], "--", zorder=2)
        ax2.set_ylim(0, 1)

        ax = axes[2]
        ax.fill_between(
            x=self.data[self.field_datetime],
            y1=self.data["s"] - self.data["ss"],
            y2=self.data["s"],
            color="lightsteelblue",
            label="Spill storage",
        )
        ax.legend()
        # handle return
        if return_fig:
            return fig
        else:
            if show:
                plt.show()
            else:
                file_path = "{}/{}.{}".format(
                    specs["folder"], specs["filename"], specs["fig_format"]
                )
                plt.savefig(file_path, dpi=specs["dpi"])
                plt.close(fig)
                return None


class Global(LSFAS):
    """
    This is a global Rainfall-Runoff model. Simulates the the catchment
    as if is a global system. Expected inputs:

    - `clim.csv` for Precipitation (P) and Potential Evapotranspiration (E_pot).
    - `path_areas.csv` for deriving the geomorphic unit hydrograph.

    # todo [major docstring] examples

    """

    def __init__(self, name="MyGlobal", alias="Glo001"):
        # todo [docstring]
        super().__init__(name=name, alias=alias)
        # overwriters
        self.object_alias = "Global"

        # simulation variables
        self.datakey = "value"  # this is used for accessing data in dicts

        # testing controllers
        self.shutdown_qif = False
        self.shutdown_qbf = False

        # Path-Area Histogram (PAH) -- input
        self.data_pah = None
        self.file_data_pah = None
        self.folder_data_pah = None
        self.filename_data_pah = "pah.csv"
        self.basins_ls = None

        # Time-Area Histogram (TAH) -- output
        self.data_tah = None
        self.filename_data_tah = "tah.csv"

        # Geomorphic Unit Hydrograph
        self.data_guh = None
        self.filename_data_guh = "guh.csv"

    def _set_model_vars(self):
        # todo [docstring]
        super()._set_model_vars()

        # clean some vars
        del self.vars["s"]
        del self.vars["q"]
        del self.vars["qb"]
        del self.vars["qsf"]
        del self.vars["qs"]
        del self.vars["ss"]

        # update old attributes
        for v in self.vars:
            self.vars[v].update(
                {
                    "canopy": True,
                    "surface": True,
                    "soil": True,
                }
            )
        self.vars["q_obs"].update(
            {
                "canopy": False,
                "surface": False,
                "soil": False,
            }
        )

        # set new entries
        self.new_vars = {
            #
            #
            # Canopy variables
            "c": {
                "units": "mm",
                "description": "Canopy storage",
                "kind": "level",
                "tex": "$C$",
                "canopy": True,
                "surface": False,
                "soil": False,
            },
            "ec": {
                "units": "mm/{dt_freq}",
                "description": "Canopy evaporation",
                "kind": "flow",
                "tex": "$E_{c}$",
                "canopy": True,
                "surface": False,
                "soil": False,
            },
            "ptf": {
                "units": "mm/{dt_freq}",
                "description": "Throughfall -- canopy spill water",
                "kind": "flow",
                "tex": "$P_{tf}$",
                "canopy": True,
                "surface": False,
                "soil": False,
            },
            "ptff": {
                "units": "mm/mm",
                "description": "Throughfall fraction",
                "kind": "constant",
                "tex": "$P_{tf, f}$",
                "canopy": True,
                "surface": False,
                "soil": False,
            },
            "psf": {
                "units": "mm/{dt_freq}",
                "description": "Stemflow -- canopy drained water",
                "kind": "flow",
                "tex": "$P_{sf}$",
                "canopy": True,
                "surface": False,
                "soil": False,
            },
            "pc": {
                "units": "mm/{dt_freq}",
                "description": "Effective precipitation on canopy",
                "kind": "flow",
                "tex": "$P_{c}$",
                "canopy": True,
                "surface": False,
                "soil": False,
            },
            "ps": {
                "units": "mm/{dt_freq}",
                "description": "Effective precipitation on surface",
                "kind": "flow",
                "tex": "$P_{s}$",
                "canopy": True,
                "surface": True,
                "soil": False,
            },
            #
            #
            # Surface variables
            "s": {
                "units": "mm",
                "description": "Surface storage",
                "kind": "level",
                "tex": "$S$",
                "canopy": False,
                "surface": True,
                "soil": False,
            },
            "es": {
                "units": "mm/{dt_freq}",
                "description": "Surface evaporation",
                "kind": "flow",
                "tex": "$E_{s}$",
                "canopy": False,
                "surface": True,
                "soil": False,
            },
            "qof": {
                "units": "mm/{dt_freq}",
                "description": "Overland flow  -- surface spill",
                "kind": "flow",
                "tex": "$Q_{of}$",
                "canopy": False,
                "surface": True,
                "soil": False,
            },
            "qoff": {
                "units": "mm/mm",
                "description": "Overland flow fraction",
                "kind": "constant",
                "tex": "$Q_{of, f}$",
                "canopy": False,
                "surface": True,
                "soil": False,
            },
            "quf": {
                "units": "mm/{dt_freq}",
                "description": "Underland flow -- lateral leak in topsoil",
                "kind": "flow",
                "tex": "$Q_{uf}$",
                "canopy": False,
                "surface": True,
                "soil": False,
            },
            "quff": {
                "units": "mm/mm",
                "description": "Underland flow fraction",
                "kind": "constant",
                "tex": "$Q_{uf, f}$",
                "canopy": False,
                "surface": True,
                "soil": False,
            },
            "qif": {
                "units": "mm/{dt_freq}",
                "description": "Infiltration flow -- drainage to mineral vadoze zone",
                "kind": "flow",
                "tex": "$Q_{if}$",
                "canopy": False,
                "surface": True,
                "soil": True,
            },
            #
            #
            # Vadose vars
            "v": {
                "units": "mm",
                "description": "Vadose zone storage",
                "kind": "level",
                "tex": "$V$",
                "canopy": False,
                "surface": False,
                "soil": True,
            },
            "qvf": {
                "units": "mm",
                "description": "Recharge flow -- vertical flow to phreatic zone",
                "kind": "flow",
                "tex": "$Q_{v}$",
                "canopy": False,
                "surface": False,
                "soil": True,
            },
            "qvff": {
                "units": "mm/mm",
                "description": "Recharge flow fraction",
                "kind": "constant",
                "tex": "$Q_{vf, f}$",
                "canopy": False,
                "surface": False,
                "soil": True,
            },
            "dv": {
                "units": "mm",
                "description": "Vadose zone storage deficit",
                "kind": "level",
                "tex": "$D_{v}$",
                "canopy": False,
                "surface": False,
                "soil": True,
            },
            #
            #
            # Phreatic vars
            "g": {
                "units": "mm",
                "description": "Phreatic zone storage",
                "kind": "level",
                "tex": "$G$",
                "canopy": False,
                "surface": False,
                "soil": True,
            },
            "d": {
                "units": "mm",
                "description": "Phreatic zone storage deficit",
                "kind": "level",
                "tex": "$D$",
                "canopy": False,
                "surface": False,
                "soil": True,
            },
            "eg": {
                "units": "mm/{dt_freq}",
                "description": "Phreatic zone transpiration",
                "kind": "flow",
                "tex": "$E_{g}$",
                "canopy": False,
                "surface": False,
                "soil": True,
            },
            "egf": {
                "units": "mm/{dt_freq}",
                "description": "Phreatic zone transpiration fraction",
                "kind": "constant",
                "tex": "$E_{t, f}$",
                "canopy": False,
                "surface": False,
                "soil": True,
            },
            "qgf": {
                "units": "mm/{dt_freq}",
                "description": "Groundwater flow (baseflow at hillslope scale)",
                "kind": "flow",
                "tex": "$Q_{gf}$",
                "canopy": False,
                "surface": False,
                "soil": True,
            },
            # routing
            "qhf": {
                "units": "mm/{dt_freq}",
                "description": "Hillslope flow (surface, subsurface and baseflow)",
                "kind": "flow",
                "tex": "$Q_{hf}$",
                "canopy": False,
                "surface": True,
                "soil": True,
            },
            "qbf": {
                "units": "mm/{dt_freq}",
                "description": "River baseflow (routed groundflow at river gauge)",
                "kind": "flow",
                "tex": "$Q_{bf}$",
                "canopy": False,
                "surface": False,
                "soil": True,
            },
            "q": {
                "units": "mm/{dt_freq}",
                "description": "Streamflow at river gauge",
                "kind": "flow",
                "tex": "$Q$",
                "canopy": False,
                "surface": True,
                "soil": True,
            },
        }
        # update new entries
        self.vars.update(self.new_vars.copy())
        # get useful lists
        self.vars_canopy = [self.field_datetime] + [
            v for v in self.vars if self.vars[v]["canopy"]
        ]
        self.vars_surface = [self.field_datetime] + [
            v for v in self.vars if self.vars[v]["surface"]
        ]
        self.vars_soil = [self.field_datetime] + [
            v for v in self.vars if self.vars[v]["soil"]
        ]
        self.vars_levels = ["c", "s", "v", "dv", "g", "d"]

        return None

    def _set_model_params(self):
        """
        Intenal method for setting up model parameters data

        :return: None
        :rtype: None
        """
        super()._set_model_params()
        # clean useless model parameters from upstream
        del self.params["k"]
        del self.params["s_a"]
        del self.params["s_c"]
        del self.params["s0"]

        # add new params
        self.params.update(
            {
                #
                #
                # initial conditions
                "c0": {
                    "value": None,
                    "units": "mm",
                    "dtype": np.float64,
                    "description": "Canopy storage initial conditions",
                    "kind": "conceptual",
                    "tex": "$C_{0}$",
                    "domain": "time",
                },
                "s0": {
                    "value": None,
                    "units": "mm",
                    "dtype": np.float64,
                    "description": "Surface storage initial conditions",
                    "kind": "conceptual",
                    "tex": "$S_{0}$",
                    "domain": "time",
                },
                "v0": {
                    "value": None,
                    "units": "mm",
                    "dtype": np.float64,
                    "description": "Vadose zone initial conditions",
                    "kind": "conceptual",
                    "tex": "$V_{0}$",
                    "domain": "time",
                },
                "g0": {
                    "value": None,
                    "units": "mm",
                    "dtype": np.float64,
                    "description": "Phreatic zone initial conditions",
                    "kind": "conceptual",
                    "tex": "$G_{0}$",
                    "domain": "time",
                },
                #
                #
                # Canopy parameters
                "ck": {
                    "value": None,
                    "units": "d",
                    "dtype": np.float64,
                    "description": "Canopy residence time",
                    "kind": "conceptual",
                    "tex": "$C_{k}$",
                    "domain": "lulc",
                },
                "ca": {
                    "value": None,
                    "units": "mm",
                    "dtype": np.float64,
                    "description": "Activation level for canopy spill",
                    "kind": "conceptual",
                    "tex": "$C_{a}$",
                    "domain": "lulc",
                },
                #
                #
                # Surface parameters
                "sk": {
                    "value": None,
                    "units": "d",
                    "dtype": np.float64,
                    "description": "Surface residence time",
                    "kind": "conceptual",
                    "tex": "$S_{k}$",
                    "domain": "lulc",
                },
                # subsurface spill
                "sufcap": {
                    "value": None,
                    "units": "mm",
                    "dtype": np.float64,
                    "description": "Subsurface storage capacity",
                    "kind": "conceptual",
                    "tex": "$S_{uf, cap}$",
                    "domain": "lulc",
                },
                "sufa": {
                    "value": None,
                    "units": "mm",
                    "dtype": np.float64,
                    "description": "Activation level for subsurface spill",
                    "kind": "conceptual",
                    "tex": "$S_{uf, a}$",
                    "domain": "lulc",
                },
                "sufc": {
                    "value": None,
                    "units": "mm",
                    "dtype": np.float64,
                    "description": "Fragmentation level for subsurface spill",
                    "kind": "conceptual",
                    "tex": "$S_{uf, c}$",
                    "domain": "lulc",
                },
                # surface spill
                "sofa": {
                    "value": None,
                    "units": "mm",
                    "dtype": np.float64,
                    "description": "Activation level for overland spill",
                    "kind": "conceptual",
                    "tex": "$S_{of, a}$",
                    "domain": "lulc",
                },
                "sofc": {
                    "value": None,
                    "units": "mm",
                    "dtype": np.float64,
                    "description": "Fragmentation level for overland spill",
                    "kind": "conceptual",
                    "tex": "$S_{of, c}$",
                    "domain": "lulc",
                },
                # recharge
                "kv": {
                    "value": None,
                    "units": "mm/D",
                    "dtype": np.float64,
                    "description": "Soil hydraulic conductivity",
                    "kind": "conceptual",
                    "tex": "$K_{V}$",
                    "domain": "soils",
                },
                # baseflow
                "dea": {
                    "value": None,
                    "units": "mm",
                    "dtype": np.float64,
                    "description": "Deficit limit for full evapotranspiration",
                    "kind": "level",
                    "tex": "$D_{e, a}$",
                    "domain": "lulc",
                },
                "ecap": {
                    "value": None,
                    "units": "mm",
                    "dtype": np.float64,
                    "description": "Evapotranspiration capacity at capilar zone",
                    "kind": "level",
                    "tex": "$G_{e, cap}$",
                    "domain": "soils",
                },
                "gcap": {
                    "value": None,
                    "units": "mm",
                    "dtype": np.float64,
                    "description": "Phreatic zone storage capacity",
                    "kind": "conceptual",
                    "tex": "$G_{cap}$",
                    "domain": "soils",
                },
                "gk": {
                    "value": None,
                    "units": "d",
                    "dtype": np.float64,
                    "description": "Phreatic zone residence time",
                    "kind": "conceptual",
                    "tex": "$G_{k}$",
                    "domain": "soils",
                },
                "kq": {
                    "value": None,
                    "units": "m/D",
                    "dtype": np.float64,
                    "description": "Channel water celerity",
                    "kind": "conceptual",
                    "tex": "$K_{Q}$",
                    "domain": "routing",
                },
            }
        )
        # reset reference
        self.reference_dt_param = "gk"
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

        # add new specs
        self.view_specs.update(
            {
                # new values
                "width": 10,
                "height": 6,
                "gs_left": 0.1,
                "gs_right": 0.9,
                # new params
                "color_P": "deepskyblue",
                "color_P_s": "blue",
                "color_P_sf": "green",
                "color_C": "black",
                "color_V": "steelblue",
                "color_G": "navy",
                "color_Q_if": "blue",
                "color_Q_hf": "blue",
                "color_Q_bf": "darkblue",
                "color_Q": "blue",
                "ymax_C": None,
                "ymax_V": None,
                "ymax_G": None,
                "ymax_Q_if": None,
                "ymax_Q": None,
                "ymax_Q_hf": None,
            }
        )
        return None

    def setter(self, dict_setter):
        """
        Set selected attributes based on an incoming dictionary.
        This is calling the superior method using load_data=False.

        :param dict_setter: incoming dictionary with attribute values
        :type dict_setter: dict
        :return: None
        :rtype: None
        """
        super().setter(dict_setter)

        # specific files
        self.folder_data_pah = self.folder_data  # same here

        # ... continues in downstream objects ... #
        return None

    def get_basins_list(self):
        # todo [docstring]
        ls_basins = []
        for c in self.data_pah.columns:
            if c == "path":
                pass
            else:
                ls_basins.append(c)
        return ls_basins

    def _setup_tah(self):
        # todo [docstring]
        # get path
        vct_paths = self.data_pah["path"].values
        # handle not starting in zero
        b_insert_zero = False
        if np.min(vct_paths) > 0:
            vct_paths = np.insert(vct_paths, 0, 0)
            b_insert_zero = True

        # compute delay
        vct_t = vct_paths / self.params["kq"]["value"]

        # set dataframe
        self.data_tah = pd.DataFrame(
            {
                "time": vct_t,
                "path": vct_paths,
            }
        )

        # setup basins list
        self.basins_ls = self.get_basins_list()

        # append areas
        for basin in self.basins_ls:
            vct_area = self.data_pah[basin].values
            # handle not starting in zero
            if b_insert_zero:
                vct_area = np.insert(vct_area, 0, 0)
            # append to dataframe
            self.data_tah[basin] = vct_area[:]

        return None

    def _setup_guh(self):
        # todo [docstring]
        from scipy.interpolate import CubicSpline

        # set the TAH data
        self._setup_tah()

        # compute unit hydrograph
        vct_t_src = self.data_tah["time"].values

        # set unit hydrograph dataframe
        self.data_guh = pd.DataFrame(
            {
                "t": self.sdata["t"],
            }
        )
        # append for each basin
        for basin in self.basins_ls:
            vct_q_src = self.data_tah[basin].values / self.data_tah[basin].sum()
            # smoothing
            window_size = 8  # make it more or less smooth
            # Create a kernel for the moving average
            kernel = np.ones(window_size) / window_size
            # Apply the convolution
            vct_q_src = np.convolve(vct_q_src, kernel, mode="same")

            # clip data
            t_max = np.max(vct_t_src)
            df_q = self.data_guh.query(f"t <= {t_max}").copy()
            vct_t_clip = df_q["t"].values

            # Cubic spline interpolation (smoother)
            f_cubic = CubicSpline(vct_t_src, vct_q_src)
            vct_q_clip = f_cubic(vct_t_clip)

            # add zeros at the tail
            vct_q_new = np.concatenate(
                [vct_q_clip, np.zeros(self.slen - len(vct_q_clip), dtype=np.float64)]
            )
            # normalize to sum = 1
            vct_q_new = vct_q_new / np.sum(vct_q_new)
            # append in guh
            self.data_guh[basin] = vct_q_new

        return None

    def _setup_start(self):
        # todo [docstring]
        # loop over vars
        for v in self.vars:
            # set initial conditions on storages
            if self.vars[v]["kind"] == "level":
                if v == "d" or v == "dv":
                    pass
                else:
                    self.sdata[v][0] = self.params["{}0".format(v)]["value"]

        # --- handle bad (unfeaseable) initial conditions

        # --- G0 storage must not exceed G_cap
        g_cap = self.params["gcap"]["value"]
        g0 = self.sdata["g"][0]
        if g0 > g_cap:
            self.params["g0"]["value"] = g_cap
            self.sdata["g"][0] = g_cap

        # --- V0 storage must not exceed D (Gcap - G)
        v0 = self.sdata["v"][0]
        g0 = self.sdata["g"][0]

        if v0 > (g_cap - g0):
            self.params["v0"]["value"] = g_cap
            self.sdata["v"][0] = g_cap - g0

        return None

    def _setup_params(self):
        # todo [docstring]
        # --- handle bad (unfeaseable) parameters

        # --- D_et_cap must not exceed G_cap
        g_cap = self.params["gcap"]["value"]
        d_et_a = self.params["dea"]["value"]
        self.params["dea"]["value"] = np.where(d_et_a > g_cap, g_cap, d_et_a)

        return None

    def _setup_steps(self):
        # todo [docstring]
        # [Testing feature] constrain simulation steps
        if self.n_steps is None:
            self.n_steps = self.slen
        return None

    def load_data(self):
        """
        Load simulation data. Expected to increment superior methods.

        :return: None
        :rtype: None
        """
        super().load_data()

        # -------------- load path areas inputs data -------------- #
        self.file_data_pah = Path(f"{self.folder_data_pah}/{self.filename_data_pah}")
        self.data_pah = pd.read_csv(
            self.file_data_pah,
            sep=self.file_csv_sep,
            encoding=self.file_encoding,
        )

        # -------------- update other mutables -------------- #
        # evaluate using self.update()

        # ... continues in downstream objects ... #

        return None

    def setup(self):
        """
        Set model simulation.

        .. warning::

            This method overwrites model data.


        :return: None
        :rtype: None
        """
        # setup superior object
        super().setup()

        # clear deprecated parent variables
        del self.sdata["qs"]
        del self.sdata["qsf"]
        del self.sdata["qb"]
        del self.sdata["s"]
        del self.sdata["ss"]
        del self.sdata["q"]

        # append new variables
        for v in self.new_vars:
            self.sdata[v] = np.full(self.slen, np.nan)

        #
        # ----------- simulation steps ------------- #
        #
        self._setup_steps()

        #
        # ----------- initial conditions ------------- #
        #
        self._setup_start()

        #
        # ---------------- parameters ---------------- #
        #
        self._setup_params()

        #
        # ------------- routing setup ---------------- #
        #
        self._setup_guh()

        #
        # ------------- set empty io data ---------------- #
        #
        self.data = pd.DataFrame(self.sdata)

        return None

    def solve(self):
        """
        Solve the model for inputs and initial conditions by numerical methods.

        .. warning::

            This method overwrites model data.

        :return: None
        :rtype: None
        """

        #
        # ---------------- simulation setup ----------------
        #

        # dt is the fraction of 1 Day/(1 simulation time step)
        dt = self.params["dt"]["value"]

        # full global processes data is a dataframe with numpy arrays
        gb = self.sdata

        #
        # ---------------- parameters variables ----------------
        # this section is for improving code readability only

        # [Canopy] canopy parameters
        c_k = self.params["ck"][self.datakey]
        c_a = self.params["ca"][self.datakey]

        # [Surface] surface parameters
        s_k = self.params["sk"][self.datakey]
        s_of_a = self.params["sofa"][self.datakey]
        s_of_c = self.params["sofc"][self.datakey]
        s_uf_a = self.params["sufa"][self.datakey]
        s_uf_c = self.params["sufc"][self.datakey]
        s_uf_cap = self.params["sufcap"][self.datakey]

        # [Soil] soil parameters
        g_cap = self.params["gcap"][self.datakey]
        k_v = self.params["kv"][self.datakey]
        g_k = self.params["gk"][self.datakey]
        g_e_cap = self.params["ecap"][self.datakey]
        d_e_a = self.params["dea"][self.datakey]

        #
        # ---------------- derived parameter variables ----------------
        #

        # [Surface] Conpute shutdown factor for underland flow
        s_uf_shutdown = Global.compute_s_uf_shutdown(s_uf_cap, s_uf_a)

        # [Surface] Compute effective overland flow activation level
        s_of_a_eff = Global.compute_sof_a_eff(s_uf_cap, s_of_a)

        #
        # ---------------- testing features ----------------
        #

        # [Testing feature] shutdown E_pot
        if self.shutdown_epot:
            gb["e_pot"] = np.full(self.slen, 0.0)

        #
        # ---------------- numerical solution ----------------
        #

        # ---------------- START TIME LOOP ---------------- #
        # loop over steps (Euler Method)
        for t in range(self.n_steps - 1):
            #
            # [Deficit] ---------- update deficits ---------- #
            #

            # [Deficit] Phreatic zone deficit
            gb["d"][t] = Global.compute_d(g_cap=g_cap, g=gb["g"][t])

            # [Deficit] Vadose zone deficit
            gb["dv"][t] = Global.compute_dv(d=gb["d"][t], v=gb["v"][t])

            #
            # [Evaporation] ---------- get evaporation flows first ---------- #
            #

            # [Evaporation] [Canopy] ---- evaporation from canopy

            # [Evaporation] [Canopy] compute potential flow
            e_c_pot = Global.compute_ec_pot(e_pot=gb["e_pot"][t])

            # [Evaporation] [Canopy] compute capacity flow
            e_c_cap = Global.compute_ec_cap(c=gb["c"][t], dt=dt)

            # [Evaporation] [Canopy] compute actual flow
            gb["ec"][t] = Global.compute_ec(e_c_pot, e_c_cap)

            # [Evaporation] [Soil] ---- transpiration from soil

            # [Evaporation] [Soil] compute potential flow
            e_t_pot = Global.compute_et_pot(e_pot=gb["e_pot"][t], ec=gb["ec"][t])

            # [Evaporation] [Soil] compute the root zone depth factor
            gb["egf"][t] = Global.compute_et_f(dv=gb["dv"][t], d_et_a=d_e_a)

            # [Evaporation] [Soil] compute capacity flow
            e_t_cap = Global.compute_et_cap(
                e_t_f=gb["egf"][t], g=gb["g"][t], g_et_cap=g_e_cap, dt=dt
            )

            # [Evaporation] [Soil] compute actual flow
            gb["eg"][t] = Global.compute_et(e_t_pot, e_t_cap)

            # [Evaporation] [Surface] ---- evaporation from surface

            # [Evaporation] [Surface] compute potential flow
            e_s_pot = Global.compute_es_pot(
                e_pot=gb["e_pot"][t], ec=gb["ec"][t], et=gb["eg"][t]
            )

            # [Evaporation] [Surface] compute capacity flow
            e_s_cap = Global.compute_es_cap(s=gb["s"][t], dt=dt)

            # [Evaporation] [Surface] compute actual flow
            gb["es"][t] = Global.compute_es(e_s_pot, e_s_cap)

            #
            # [Evaporation] [Balance] ---- a priori discounts ---------- #
            #

            # [Evaporation] [Balance] -- apply discount a priori
            gb["c"][t] = Global.compute_e_discount(
                storage=gb["c"][t], discount=gb["ec"][t]
            )

            # [Evaporation] [Balance] -- apply discount a priori
            gb["g"][t] = Global.compute_e_discount(
                storage=gb["g"][t], discount=gb["eg"][t]
            )

            # [Evaporation] [Balance] water balance -- apply discount a priori
            gb["s"][t] = Global.compute_e_discount(
                storage=gb["s"][t], discount=gb["es"][t]
            )

            #
            # [Canopy] ---------- Solve canopy water balance ---------- #
            #

            # [Canopy] [Throughfall] --

            # [Canopy] [Throughfall] Compute throughfall fraction
            gb["ptff"][t] = Global.compute_tf_f(c=gb["c"][t], ca=c_a)

            # [Canopy] [Throughfall] Compute throughfall capacity
            p_tf_cap = Global.compute_tf_cap(c=gb["c"][t], ca=c_a, p=gb["p"][t], dt=dt)

            # [Canopy] [Throughfall] Compute throughfall
            gb["ptf"][t] = Global.compute_tf(p_tf_cap=p_tf_cap, p_tf_f=gb["ptff"][t])

            # [Canopy] [Stemflow] --

            # [Canopy] [Stemflow] Compute potential stemflow -- only activated storage contributes
            c_sf_pot = Global.compute_sf_pot(c=gb["c"][t], ca=c_a)

            # [Canopy] [Stemflow] Compute actual stemflow
            gb["psf"][t] = compute_decay(s=c_sf_pot, dt=dt, k=c_k)

            # [Canopy] [Aggflows] --

            # [Canopy] [Aggflows] Compute effective rain on surface
            gb["ps"][t] = Global.compute_ps(sf=gb["psf"][t], tf=gb["ptf"][t])

            # [Canopy] [Aggflows] Compute effective rain on canopy
            gb["pc"][t] = Global.compute_pc(p=gb["p"][t], tf_f=gb["ptff"][t])

            # [Canopy] [Water Balance] ---- Apply water balance
            gb["c"][t + 1] = Global.compute_next_c(
                c=gb["c"][t], pc=gb["pc"][t], sf=gb["psf"][t]
            )

            #
            # [Surface] ---------- Solve surface water balance ---------- #
            #

            # [Surface] [Overland] -- Overland flow

            # [Surface] [Overland] Compute surface overland spill storage capacity
            sof_ss_cap = Global.compute_sof_cap(s=gb["s"][t], sof_a=s_of_a_eff)

            # [Surface] [Overland] Compute overland flow fraction
            gb["qoff"][t] = Global.compute_qof_f(sof_cap=sof_ss_cap, sof_c=s_of_c)

            # [Surface] [Overland] Compute overland flow capacity
            q_of_cap = Global.compute_qof_cap(sof_cap=sof_ss_cap, ps=gb["ps"][t], dt=dt)

            # [Surface] [Overland] Compute potential overland
            q_of_pot = Global.compute_qof_pot(qof_cap=q_of_cap, qof_f=gb["qoff"][t])

            # [Surface] [Underland] -- Underland flow

            # [Surface] [Underland] Compute surface underland spill storage capacity
            suf_ss_cap = Global.compute_suf_cap(
                s=gb["s"][t], suf_a=s_uf_a, shutdown=s_uf_shutdown
            )

            # [Surface] [Underland] Compute underland flow fraction
            gb["quff"][t] = Global.compute_quf_f(suf_cap=suf_ss_cap, suf_c=s_uf_c)

            # [Surface] [Underland] Compute underland flow capacity
            q_uf_cap = Global.compute_quf_cap(suf_cap=suf_ss_cap, dt=dt)

            # [Surface] [Underland] Compute potential underland flow
            q_uf_pot = Global.compute_quf_pot(quf_cap=q_uf_cap, quf_f=gb["quff"][t])

            # [Surface] [Infiltration] -- Infiltration flow

            # [Surface] [Infiltration] -- Potential infiltration from downstream (soil)
            q_if_pot_down = Global.compute_qif_pot_down(
                d=gb["d"][t], v=gb["v"][t], dt=dt
            )

            # [Surface] [Infiltration] -- Potential infiltration from upstream (hydraulic head)
            q_if_pot_up = Global.compute_qif_pot_up(s=gb["s"][t], sk=s_k, dt=dt)

            # [Surface] [Infiltration] -- Potential infiltration
            q_if_pot = Global.compute_qif_pot(if_down=q_if_pot_down, if_up=q_if_pot_up)

            # [Testing feature]
            if self.shutdown_qif:
                q_if_pot = 0.0 * q_if_pot

            # [Surface] -- Full potential outflow
            s_out_pot = q_of_pot + q_uf_pot + q_if_pot

            # [Surface] ---- Actual flows

            # [Surface] Compute surface outflow capacity
            s_out_cap = gb["s"][t]

            # [Surface] Compute Actual outflow
            s_out_act = np.where(s_out_cap > s_out_pot, s_out_pot, s_out_cap)

            # [Surface] Allocate outflows
            with np.errstate(divide="ignore", invalid="ignore"):
                gb["qof"][t] = s_out_act * np.where(
                    s_out_pot == 0.0, 0.0, q_of_pot / s_out_pot
                )
                gb["quf"][t] = s_out_act * np.where(
                    s_out_pot == 0.0, 0.0, q_uf_pot / s_out_pot
                )
                gb["qif"][t] = s_out_act * np.where(
                    s_out_pot == 0.0, 0.0, q_if_pot / s_out_pot
                )

            # [Surface Water Balance] ---- Apply water balance.
            gb["s"][t + 1] = Global.compute_next_s(
                s=gb["s"][t],
                ps=gb["ps"][t],
                qof=gb["qof"][t],
                quf=gb["quf"][t],
                qif=gb["qif"][t],
            )

            #
            # [Soil] ---------- Solve soil water balance ---------- #
            #

            # [Soil Vadose Zone]

            # [Soil Vadose Zone] Get Recharge Fraction
            gb["qvff"][t] = Global.compute_qvf_f(d=gb["d"][t], v=gb["v"][t])

            # [Soil Vadose Zone] Compute Potential Recharge
            q_vf_pot = Global.compute_qvf_pot(qvf_f=gb["qvff"][t], kv=k_v, dt=dt)

            # [Soil Vadose Zone] Compute Maximal Recharge
            q_vf_cap = Global.compute_qvf_cap(v=gb["v"][t], dt=dt)

            # [Soil Vadose Zone] Compute Actual Recharge
            gb["qvf"][t] = Global.compute_qvf(qvf_pot=q_vf_pot, qvf_cap=q_vf_cap)

            # [Vadose Water Balance] ---- Apply water balance
            gb["v"][t + 1] = Global.compute_next_v(
                v=gb["v"][t], qif=gb["qif"][t], qvf=gb["qvf"][t]
            )

            # [Soil Phreatic Zone]

            # [Soil Phreatic Zone] Compute Base flow (blue water -- discount on green water)
            # gb["qgf"][t] = (np.max([gb["g"][t] - g_et_cap, 0.0])) * dt / g_k
            gb["qgf"][t] = Global.compute_qgf(
                g=gb["g"][t], get_cap=g_e_cap, gk=g_k, dt=dt
            )

            # [Testing feature]
            if self.shutdown_qbf:
                gb["qgf"][t] = 0.0 * gb["qgf"][t]

            # [Phreatic Water Balance] ---- Apply water balance
            gb["g"][t + 1] = Global.compute_next_g(
                g=gb["g"][t], qvf=gb["qvf"][t], qgf=gb["qgf"][t]
            )

            # ---------------- END TIME LOOP ---------------- #

        #
        # [Total Flows] ---------- compute total flows ---------- #
        #

        # [Total Flows] Total E
        gb["e"] = Global.compute_e(ec=gb["ec"], es=gb["es"], eg=gb["eg"])

        # [Total Flows] Compute Hillslope flow
        gb["qhf"] = Global.compute_qhf(qof=gb["qof"], quf=gb["quf"], qgf=gb["qgf"])

        #
        # [Streamflow] ---------- Solve flow routing to basin gauge station ---------- #
        #

        # global basin is considered the first
        basin = self.basins_ls[0]

        # [Baseflow] Compute river base flow
        vct_inflow = gb["qgf"]
        gb["qbf"] = Global.propagate_inflow(
            inflow=vct_inflow,
            unit_hydrograph=self.data_guh[basin].values,
        )

        # [Fast Streamflow] Compute Streamflow
        # todo [feature] evaluate to split into more components
        vct_inflow = gb["quf"] + gb["qof"]
        q_fast = Global.propagate_inflow(
            inflow=vct_inflow, unit_hydrograph=self.data_guh[basin].values
        )
        gb["q"] = gb["qbf"] + q_fast

        # set data
        self.data = pd.DataFrame(gb)

        return None

    def export(self, folder, filename, views=False, mode=None):
        """
        Export object resources. Expected to be called after setup.

        :param folder: path to folder
        :type folder: str
        :param filename: file name without extension
        :type filename: str
        :return: None
        :rtype: None
        """
        # export model simulation data with views=False
        super().export(folder, filename=filename, views=False)

        # handle views
        if views:
            self.view_specs["folder"] = folder
            self.view_specs["filename"] = filename
            # handle view mode
            self.view(show=False, mode=mode)

        # export PAH Path Area Histogram
        fpath = Path(folder + "/" + filename + "_" + self.filename_data_pah)
        self.data_pah.to_csv(
            fpath, sep=self.file_csv_sep, encoding=self.file_encoding, index=False
        )
        # export TAH Time Area Histogram
        fpath = Path(folder + "/" + filename + "_" + self.filename_data_tah)
        self.data_tah.to_csv(
            fpath, sep=self.file_csv_sep, encoding=self.file_encoding, index=False
        )
        # export GUH Geomorphic Unit Hydrograph
        fpath = Path(folder + "/" + filename + "_" + self.filename_data_guh)
        self.data_guh.to_csv(
            fpath, sep=self.file_csv_sep, encoding=self.file_encoding, index=False
        )
        # ... continues in downstream objects ... #

    def view(self, show=True, return_fig=False, mode=None, basin=None):
        # todo [docstring]
        # todo [optimize for DRY]
        if basin is None:
            basin = "global"
        plt.rcParams["font.family"] = "Arial"
        specs = self.view_specs.copy()
        n_dt = self.params["dt"]["value"]
        # start plot
        fig = plt.figure(figsize=(specs["width"], specs["height"]))  # Width, Height
        plt.suptitle("{} | Model Global".format(self.name))
        # grid
        gs = mpl.gridspec.GridSpec(
            3,
            1,
            wspace=specs["gs_wspace"],
            hspace=specs["gs_hspace"],
            left=specs["gs_left"],
            right=specs["gs_right"],
            bottom=specs["gs_bottom"],
            top=specs["gs_top"],
        )  # nrows, ncols

        first_date = self.data[self.field_datetime].iloc[0]
        last_date = self.data[self.field_datetime].iloc[-1]
        ls_dates = [first_date, last_date]

        if mode is None:
            mode = "canopy"

        if mode == "river":
            # ------------ P plot ------------
            n_pmax = self.data["p"].max() / n_dt
            ax = fig.add_subplot(gs[0, 0])
            plt.plot(
                self.data[self.field_datetime],
                self.data["p"] / n_dt,
                color=specs["color_P"],
                zorder=2,
                label=self.vars["p"]["tex"],
            )
            plt.plot(
                self.data[self.field_datetime],
                self.data["qif"] / n_dt,
                color=specs["color_Q_if"],
                zorder=2,
                label=self.vars["qif"]["tex"],
            )
            s_title1 = "$P$ ({} mm)".format(round(self.data["p"].sum(), 1))
            plt.title(s_title1, loc="left")
            # normalize X axis
            plt.xlim(ls_dates)
            # normalize Y axis
            ymax_p = specs["ymax_P"]
            if ymax_p is None:
                ymax_p = 1.2 * n_pmax
            plt.ylim(0, ymax_p)
            plt.ylabel("mm/{}".format(self.params["dt"]["units"].lower()))

            # ------------ E plot ------------
            ax2 = ax.twinx()  # Create a second y-axis that shares the same x-axis
            e_sum = round(self.data["e"].sum(), 1)
            s_symbol4 = self.vars["e_pot"]["tex"]
            ax2.plot(
                self.data[self.field_datetime],
                self.data["e"] / n_dt,
                c="tab:red",
                zorder=1,
                label=self.vars["e"]["tex"],
            )
            ax2.plot(
                self.data[self.field_datetime],
                self.data["e_pot"] / n_dt,
                c="tab:gray",
                alpha=0.5,
                zorder=2,
                linestyle="--",
                label=s_symbol4,
            )
            e_max = self.data["e_pot"].max()
            if e_max == 0:
                ax2.set_ylim(-1, 1)
            else:
                ax2.set_ylim(0, 1.2 * e_max / n_dt)
            ax2.set_title(
                "{} ({} mm)".format(self.vars["e"]["tex"], e_sum), loc="right"
            )
            ax2.set_ylabel("mm/d")

            # ------------ Q plot ------------
            n_qmax = np.max(
                [self.data["qhf"].max() / n_dt, self.data_obs["q_obs"].max()]
            )
            # n_qmax = self.data["q"].max() / n_dt
            q_sum = round(self.data["q"].sum(), 1)
            ax = fig.add_subplot(gs[1, 0])
            s_symbol0 = self.vars["q"]["tex"]
            s_symbol1 = self.vars["qbf"]["tex"]
            s_symbol2 = self.vars["qhf"]["tex"]
            # titles
            plt.title("$Q$ ({} mm) ".format(q_sum), loc="left")
            plt.title(
                "$Q_{obs}$" + " ({} mm)".format(round(self.data_obs["q_obs"].sum(), 1)),
                loc="right",
            )
            # plots
            plt.plot(
                self.data[self.field_datetime],
                self.data["q"] / n_dt,
                color=specs["color_Q"],
                zorder=2,
                label=s_symbol0,
            )
            plt.plot(
                self.data[self.field_datetime],
                self.data["qbf"] / n_dt,
                color=specs["color_Q_bf"],
                zorder=1,
                label=s_symbol1,
            )
            plt.plot(
                self.data[self.field_datetime],
                self.data["qhf"] / n_dt,
                color="silver",
                zorder=0,
                label=s_symbol2,
            )
            plt.plot(
                self.data_obs[self.field_datetime],
                self.data_obs["q_obs"],
                ".",
                color=specs["color_Q_obs"],
            )
            plt.legend(loc="upper left")
            # tic labels
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
            ax.set_xticks(ls_dates)
            # normalize X axis
            plt.xlim(ls_dates)
            # normalize Y axis
            ymax_q = specs["ymax_Q_hf"]
            if ymax_q is None:
                ymax_q = 1.1 * n_qmax
            plt.ylim(0, 1.1 * ymax_q)
            plt.ylabel("mm/{}".format(self.params["dt"]["units"].lower()))

            # ------------ G plot ------------
            n_smax = self.data["g"].max()
            ax = fig.add_subplot(gs[2, 0])
            plt.title(
                r"$G$ ($\mu$ = {} mm)".format(round(self.data["g"].mean(), 1)),
                loc="left",
            )
            plt.plot(
                self.data[self.field_datetime],
                self.data["g"],
                color=specs["color_G"],
                label=self.vars["g"]["tex"],
            )
            plt.hlines(
                y=self.params["gcap"]["value"],
                xmin=self.data[self.field_datetime].min(),
                xmax=self.data[self.field_datetime].max(),
                colors="orange",
                linestyles="--",
                label=self.params["gcap"]["tex"],
            )
            plt.hlines(
                y=self.params["gcap"]["value"] - self.params["dea"]["value"],
                xmin=self.data[self.field_datetime].min(),
                xmax=self.data[self.field_datetime].max(),
                colors="green",
                linestyles="--",
                label=self.params["dea"]["tex"],
            )
            plt.legend(loc="upper left", ncols=1)

            # ticks
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
            ax.set_xticks(ls_dates)
            # normalize X axis
            plt.xlim(ls_dates)
            plt.ylabel("mm")
            # normalize Y axis
            ymax_s = specs["ymax_G"]
            if ymax_s is None:
                ymax_s = 1.1 * self.params["gcap"]["value"]
            plt.ylim(0, ymax_s)

        if mode == "canopy":
            # ------------ P plot ------------
            n_pmax = self.data["p"].max() / n_dt
            ax = fig.add_subplot(gs[0, 0])
            plt.plot(
                self.data[self.field_datetime],
                self.data["p"] / n_dt,
                color=specs["color_P"],
                zorder=2,
                label=self.vars["p"]["tex"],
            )
            s_title1 = "$P$ ({} mm)".format(round(self.data["p"].sum(), 1))
            plt.title(s_title1, loc="left")
            # normalize X axis
            plt.xlim(ls_dates)
            # normalize Y axis
            ymax_p = specs["ymax_P"]
            if ymax_p is None:
                ymax_p = 1.2 * n_pmax
            plt.ylim(0, ymax_p)
            plt.ylabel("mm/{}".format(self.params["dt"]["units"].lower()))

            # ------------ E plot ------------
            e_sum = round(self.data["ec"].sum(), 1)
            ax2 = ax.twinx()  # Create a second y-axis that shares the same x-axis
            ax2.plot(
                self.data[self.field_datetime],
                self.data["ec"] / n_dt,
                c="tab:red",
                zorder=1,
                label=self.vars["ec"]["tex"],
            )
            e_max = self.data["ec"].max()
            if e_max == 0:
                ax2.set_ylim(-1, 1)
            else:
                ax2.set_ylim(0, 1.2 * e_max / n_dt)
            ax2.set_title(
                "{} ({} mm)".format(self.vars["ec"]["tex"], e_sum), loc="right"
            )
            ax2.set_ylabel("mm/d")

            # ------------ Ps plot ------------
            n_emax = self.data["ps"].max() / n_dt
            ps_sum = round(self.data["ps"].sum(), 1)
            psf_sum = round(self.data["psf"].sum(), 1)
            ax = fig.add_subplot(gs[1, 0], sharex=ax)
            # titles
            s_symbol1 = self.vars["ps"]["tex"]
            s_symbol2 = self.vars["psf"]["tex"]
            plt.title(
                f"{s_symbol1} ({ps_sum} mm) and {s_symbol2} ({psf_sum} mm)", loc="left"
            )
            # plots
            plt.plot(
                self.data[self.field_datetime],
                self.data["ps"] / n_dt,
                color=specs["color_P_s"],
                label=s_symbol1,
            )
            plt.plot(
                self.data[self.field_datetime],
                self.data["psf"] / n_dt,
                color=specs["color_P_sf"],
                label=s_symbol2,
            )
            # normalize X axis
            plt.xlim(ls_dates)
            # normalize Y axis
            ymax_p = specs["ymax_P"]
            if ymax_p is None:
                ymax_p = 1.2 * n_pmax
            plt.ylim(0, ymax_p)
            plt.ylabel("mm/{}".format(self.params["dt"]["units"].lower()))

            # ------------ C plot ------------
            n_smax = self.data["c"].max()
            ax = fig.add_subplot(gs[2, 0], sharex=ax)
            s_symbol1 = self.vars["c"]["tex"]
            plt.title(
                r"{} ($\mu$ = {} mm)".format(
                    s_symbol1, round(self.data["c"].mean(), 1)
                ),
                loc="left",
            )
            plt.plot(
                self.data[self.field_datetime],
                self.data["c"],
                color=specs["color_C"],
                label=s_symbol1,
            )
            # normalize X axis
            plt.xlim(ls_dates)
            plt.ylabel("mm")
            # normalize Y axis
            ymax_s = specs["ymax_C"]
            if ymax_s is None:
                ymax_s = 1.2 * n_smax
            if ymax_s <= 0:
                plt.ylim(-1, 1)
            else:
                plt.ylim(0, ymax_s)

        if mode == "surface":
            # ------------ P plot ------------
            n_pmax = self.data["p"].max() / n_dt
            ax = fig.add_subplot(gs[0, 0])
            plt.plot(
                self.data[self.field_datetime],
                self.data["p"] / n_dt,
                color=specs["color_P"],
                zorder=2,
                label=self.vars["p"]["tex"],
            )
            s_title1 = "$P$ ({} mm)".format(round(self.data["p"].sum(), 1))
            plt.title(s_title1, loc="left")

            # normalize X axis
            plt.xlim(ls_dates)
            # normalize Y axis
            ymax_p = specs["ymax_P"]
            if ymax_p is None:
                ymax_p = 1.2 * n_pmax
            plt.ylim(0, ymax_p)
            plt.ylabel("mm/{}".format(self.params["dt"]["units"].lower()))

            # ------------ Ps plot ------------
            n_emax = self.data["ps"].max() / n_dt
            ps_sum = round(self.data["ps"].sum(), 1)
            # titles
            s_symbol1 = self.vars["ps"]["tex"]
            s_title2 = "{} ({} mm)".format(s_symbol1, round(self.data["ps"].sum(), 1))
            plt.title(f"{s_title1} and {s_title2}", loc="left")
            # plots
            plt.plot(
                self.data[self.field_datetime],
                self.data["ps"] / n_dt,
                color=specs["color_P_s"],
                label=s_symbol1,
            )
            plt.legend(loc="upper left")

            # ------------ E plot ------------
            s_symbol1 = self.vars["es"]["tex"]
            s_symbol2 = self.vars["ec"]["tex"]
            es_sum = round(self.data["es"].sum(), 1)
            ec_sum = round(self.data["ec"].sum(), 1)
            ax2 = ax.twinx()  # Create a second y-axis that shares the same x-axis
            ax2.plot(
                self.data[self.field_datetime],
                self.data["ec"] / n_dt,
                c="tab:orange",
                zorder=0,
                label=s_symbol1,
            )
            ax2.plot(
                self.data[self.field_datetime],
                self.data["es"] / n_dt,
                c="tab:red",
                zorder=1,
                label=s_symbol2,
            )
            es_max = np.max([self.data["es"].max(), self.data["ec"].max()])
            if es_max <= 0.001:
                ax2.set_ylim(-1, 1)
            else:
                ax2.set_ylim(0, 1.2 * es_max / n_dt)
            s_title1 = "{} ({} mm)".format(s_symbol1, ec_sum)
            s_title2 = "{} ({} mm)".format(s_symbol2, es_sum)
            ax2.set_title(f"{s_title1} and {s_title2}", loc="right")
            ax2.set_ylabel("mm/d")
            plt.legend(loc="upper right")

            # ------------ Qof, Quf, Qif plot ------------
            ax = fig.add_subplot(gs[1, 0], sharex=ax)
            s_symbol1 = self.vars["qof"]["tex"]
            s_symbol2 = self.vars["quf"]["tex"]
            s_symbol3 = self.vars["qif"]["tex"]
            s_symbol4 = self.vars["qhf"]["tex"]
            # titles
            s_title1 = "{} ({} mm)".format(s_symbol1, round(self.data["qof"].sum(), 1))
            s_title2 = "{} ({} mm)".format(s_symbol2, round(self.data["quf"].sum(), 1))
            s_title3 = "{} ({} mm)".format(s_symbol3, round(self.data["qif"].sum(), 1))
            plt.title(f"{s_title1}, {s_title2} and {s_title3}", loc="left")
            plt.plot(
                self.data[self.field_datetime],
                self.data["qhf"] / n_dt,
                color="navy",
                label=s_symbol4,
            )
            plt.plot(
                self.data[self.field_datetime],
                self.data["qof"] / n_dt,
                color="magenta",
                label=s_symbol1,
            )
            plt.plot(
                self.data[self.field_datetime],
                self.data["quf"] / n_dt,
                color="red",
                label=s_symbol2,
            )
            plt.plot(
                self.data[self.field_datetime],
                self.data["qif"] / n_dt,
                color="green",
                label=s_symbol3,
            )
            plt.ylim(0, ymax_p)
            ax.set_ylabel("mm/d")
            plt.legend(loc="upper left")

            # ------------ Runoff coef plot ------------
            ax2 = ax.twinx()
            s_symbol1 = self.vars["qoff"]["tex"]
            plt.plot(
                self.data[self.field_datetime],
                self.data["qoff"],
                color="gray",
                label=s_symbol1,
            )
            plt.ylim(-1, 2)
            ax2.set_yticks([0, 1])
            ax2.set_ylabel("mm/mm")
            f_mean = round(self.data["qoff"].mean(), 2)
            f_max = round(self.data["qoff"].max(), 2)
            ax2.set_title(
                rf"{s_symbol1} ($\mu$ = {f_mean}; max = {f_max})", loc="right"
            )
            plt.legend(loc="upper right")

            # ------------ S plot ------------
            n_smax = self.data["s"].max()
            ax = fig.add_subplot(gs[2, 0], sharex=ax)
            s_symbol1 = self.vars["s"]["tex"]
            plt.title(
                r"{} ($\mu$ = {} mm)".format(
                    s_symbol1, round(self.data["s"].mean(), 1)
                ),
                loc="left",
            )
            plt.plot(
                self.data[self.field_datetime],
                self.data["s"],
                color=specs["color_S"],
                label=s_symbol1,
            )
            plt.hlines(
                y=self.params["sufa"]["value"],
                xmin=self.data[self.field_datetime].min(),
                xmax=self.data[self.field_datetime].max(),
                colors="orange",
                label=self.params["sufa"]["tex"],
            )
            plt.hlines(
                y=self.params["sufcap"]["value"],
                xmin=self.data[self.field_datetime].min(),
                xmax=self.data[self.field_datetime].max(),
                colors="purple",
                label=self.params["sufcap"]["tex"],
            )
            plt.hlines(
                y=self.params["sofa"]["value"],
                xmin=self.data[self.field_datetime].min(),
                xmax=self.data[self.field_datetime].max(),
                colors="red",
                label=self.params["sofa"]["tex"],
            )
            plt.legend(loc="upper left")
            # ticks

            # normalize X axis
            plt.xlim(ls_dates)
            plt.ylabel("mm")
            # normalize Y axis
            ymax_s = specs["ymax_S"]
            if ymax_s is None:
                ymax_s = 1.2 * n_smax
            if ymax_s <= 0:
                plt.ylim(-1, 1)
            else:
                plt.ylim(0, ymax_s)

        if mode == "soil":
            # ------------ Qif plot ------------
            ax = fig.add_subplot(gs[0, 0])
            n_emax = self.data["qif"].max() / n_dt
            ps_sum = round(self.data["qif"].sum(), 1)
            # titles
            s_symbol0 = self.vars["ps"]["tex"]
            s_symbol1 = self.vars["qif"]["tex"]
            s_symbol2 = self.vars["qvf"]["tex"]
            s_title0 = "{} ({} mm)".format(s_symbol0, round(self.data["ps"].sum(), 1))
            s_title1 = "{} ({} mm)".format(s_symbol1, round(self.data["qif"].sum(), 1))
            s_title2 = "{} ({} mm)".format(s_symbol2, round(self.data["qvf"].sum(), 1))
            plt.title(f"{s_title0}, {s_title1} and {s_title2}", loc="left")
            # plots
            plt.plot(
                self.data[self.field_datetime],
                self.data["qif"] / n_dt,
                color=specs["color_Q_if"],
                label=s_symbol1,
            )
            plt.plot(
                self.data[self.field_datetime],
                self.data["qvf"] / n_dt,
                color="steelblue",
                label=s_symbol2,
            )
            plt.legend(loc="upper left", ncols=3)
            # normalize X axis
            plt.xlim(ls_dates)
            plt.ylabel("mm/d")
            # normalize Y axis
            ymax_qif = specs["ymax_Q_if"]
            if ymax_qif is None:
                ymax_qif = 1.2 * n_emax
            plt.ylim(0, ymax_qif)

            # ------------ E plot ------------
            s_symbol1 = self.vars["es"]["tex"]
            s_symbol2 = self.vars["ec"]["tex"]
            s_symbol3 = self.vars["eg"]["tex"]
            s_symbol4 = self.vars["e_pot"]["tex"]
            es_sum = round(self.data["es"].sum(), 1)
            ec_sum = round(self.data["ec"].sum(), 1)
            et_sum = round(self.data["eg"].sum(), 1)
            ax2 = ax.twinx()  # Create a second y-axis that shares the same x-axis
            ax2.plot(
                self.data[self.field_datetime],
                self.data["e_pot"] / n_dt,
                c="tab:gray",
                alpha=0.5,
                zorder=2,
                linestyle="--",
                label=s_symbol4,
            )
            ax2.plot(
                self.data[self.field_datetime],
                self.data["ec"] / n_dt,
                c="tab:orange",
                zorder=0,
                label=s_symbol1,
            )
            ax2.plot(
                self.data[self.field_datetime],
                self.data["es"] / n_dt,
                c="tab:red",
                zorder=1,
                label=s_symbol2,
            )
            ax2.plot(
                self.data[self.field_datetime],
                self.data["eg"] / n_dt,
                c="tab:green",
                zorder=1,
                label=s_symbol3,
            )

            es_max = np.max(
                [self.data["es"].max(), self.data["ec"].max(), self.data["eg"].max()]
            )
            if es_max <= 0.001:
                ax2.set_ylim(-1, 1)
            else:
                ax2.set_ylim(0, 1.2 * es_max / n_dt)
            s_title1 = "{} ({} mm)".format(s_symbol1, ec_sum)
            s_title2 = "{} ({} mm)".format(s_symbol2, es_sum)
            s_title3 = "{} ({} mm)".format(s_symbol3, et_sum)
            ax2.set_title(f"{s_title1}, {s_title2} and {s_title3}", loc="right")
            ax2.set_ylabel("mm/d")
            plt.legend(loc="upper right", ncols=4)

            # ------------ Qbf  ------------
            ax = fig.add_subplot(gs[1, 0], sharex=ax)
            s_symbol1 = self.vars["qbf"]["tex"]
            # titles
            s_title1 = "{} ({} mm)".format(s_symbol1, round(self.data["qbf"].sum(), 1))
            plt.title(f"{s_title1}", loc="left")
            plt.plot(
                self.data[self.field_datetime],
                self.data["qbf"] / n_dt,
                color="navy",
                label=s_symbol1,
            )
            qb_max = self.data["qbf"].max() / n_dt
            if qb_max == 0:
                plt.ylim(-1, 1)
            else:
                plt.ylim(0, 1.2 * qb_max)
            ax.set_ylabel("mm/d")
            plt.legend(loc="upper left", ncols=1)

            # ------------ G plot ------------
            n_smax = self.data["g"].max()
            ax = fig.add_subplot(gs[2, 0], sharex=ax)
            s_symbol1 = self.vars["v"]["tex"]
            s_symbol2 = self.vars["g"]["tex"]
            s_symbol3 = self.vars["d"]["tex"]
            s_symbol4 = self.vars["dv"]["tex"]
            s_title1 = r"{} ($\mu$ = {} mm)".format(
                s_symbol1, round(self.data["v"].mean(), 1)
            )
            s_title2 = r"{} ($\mu$ = {} mm)".format(
                s_symbol2, round(self.data["g"].mean(), 1)
            )
            s_title3 = r"{} ($\mu$ = {} mm)".format(
                s_symbol3, round(self.data["d"].mean(), 1)
            )
            plt.title(f"{s_title1}, {s_title2} and {s_title3}", loc="left")
            plt.plot(
                self.data[self.field_datetime],
                self.data["v"],
                color=specs["color_V"],
                label=s_symbol1,
            )
            plt.plot(
                self.data[self.field_datetime],
                self.data["g"],
                color=specs["color_G"],
                label=s_symbol2,
            )
            plt.plot(
                self.data[self.field_datetime],
                self.data["d"],
                color="black",
                label=s_symbol3,
            )
            plt.plot(
                self.data[self.field_datetime],
                self.data["dv"],
                color="black",
                linestyle="--",
                label=s_symbol4,
            )
            plt.hlines(
                y=self.params["gcap"]["value"],
                xmin=self.data[self.field_datetime].min(),
                xmax=self.data[self.field_datetime].max(),
                colors="orange",
                linestyles="--",
                label=self.params["gcap"]["tex"],
            )
            plt.hlines(
                y=self.params["gcap"]["value"] - self.params["dea"]["value"],
                xmin=self.data[self.field_datetime].min(),
                xmax=self.data[self.field_datetime].max(),
                colors="green",
                linestyles="--",
                label=self.params["dea"]["tex"],
            )
            plt.legend(loc="upper left", ncols=6)
            # normalize X axis
            plt.xlim(ls_dates)
            plt.ylabel("mm")
            # normalize Y axis
            ymax_s = specs["ymax_G"]
            if ymax_s is None:
                ymax_s = 1.2 * n_smax
            plt.ylim(0, ymax_s)

        ax.tick_params(axis="x", labelsize=10, labelcolor="black")

        # handle return
        if return_fig:
            return fig
        else:
            if show:
                plt.show()
            else:
                file_path = "{}/{}.{}".format(
                    specs["folder"], specs["filename"], specs["fig_format"]
                )
                plt.savefig(file_path, dpi=specs["dpi"])
                plt.close(fig)
                return None

    @staticmethod
    def propagate_inflow(inflow, unit_hydrograph):
        """
        Flow routing model based on provided unit hydrograph.
        Inflow and Unit Hydrograh arrays are expected to be the same size.
        # todo [feature] improve so it can handle a smaller Unit Hydrograph (using slicing, etc)

        :param inflow: 1d numpy array of inflow
        :type inflow: :class:`numpy.ndarray`
        :param unit_hydrograph: 1d numpy array of Unit Hydrograph (sum=1)
        :type unit_hydrograph: :class:`numpy.ndarray`
        :return: outflow array
        :rtype: :class:`numpy.ndarray`
        """
        size = len(inflow)
        uh = unit_hydrograph[:]
        # loop over time
        for t in range(0, size):
            if t == 0:
                # create outflow vector
                outflow = inflow[t] * uh
            else:
                # convolution over time
                outflow[t:] = outflow[t:] + (inflow[t] * uh[: size - t])
        return outflow

    @staticmethod
    def compute_s_uf_shutdown(s_uf_cap, s_uf_a):
        # todo [docstring]
        # this happens when topsoil capacity is lower than the activation level
        return np.where(s_uf_cap <= s_uf_a, 0.0, 1.0)

    @staticmethod
    def compute_sof_a_eff(s_uf_cap, s_of_a):
        # todo [docstring]
        # [Surface] Compute effective overland flow activation level
        output = s_uf_cap + s_of_a  # incremental with underland capacity (topsoil)
        r"""
        [Model Equation]
        $$$

        S_{of, a}^{*} = S_{uf, cap} + S_{of, a}

        $$$
        """
        return output

    @staticmethod
    def compute_d(g_cap, g):
        # todo [docstring]
        # [Deficit] Phreatic zone deficit
        output = g_cap - g
        r"""
        [Model Equation]
        Phreatic zone water deficit 
        $$$

        D(t) = G_{cap} + G(t) 

        $$$
        """
        return output

    @staticmethod
    def compute_dv(d, v):
        # todo [docstring]
        # [Deficit] Vadose zone deficit
        output = d - v
        r"""
        [Model Equation]
        Vadose zone water deficit 
        $$$

        D_{v}(t) = D(t) - V(t) 

        $$$
        """
        return output

    @staticmethod
    def compute_ec(e_c_pot, e_c_cap):
        # todo [docstring]
        # [Evaporation - Canopy] compute actual flow
        output = compute_flow(flow_pot=e_c_pot, flow_cap=e_c_cap)
        r"""
        [Model Equation]
        Actual Canopy Evaporation 
        $$$

        E_{c}(t) = \text{MIN}(E_{c, pot}, E_{c, cap}) 

        $$$
        """
        return output

    @staticmethod
    def compute_ec_pot(e_pot):
        # todo [docstring]
        # [Evaporation - Canopy] compute potential flow
        output = e_pot
        r"""
        [Model Equation]
        Potential Canopy Evaporation 
        $$$

        E_{c, pot}(t) = E_{pot}

        $$$
        """
        return output

    @staticmethod
    def compute_ec_cap(c, dt):
        # todo [docstring]
        # [Evaporation - Canopy] compute capacity flow
        output = c * dt
        r"""
        [Model Equation]
        Canopy Evaporation Capacity 
        $$$

        E_{c, cap}(t) = C(t) * dt 

        $$$
        """
        return output

    @staticmethod
    def compute_et(e_t_pot, e_t_cap):
        # todo [docstring]
        # [Evaporation - Soil] compute actual flow
        output = compute_flow(flow_pot=e_t_pot, flow_cap=e_t_cap)
        r"""
        [Model Equation]
        Actual Soil Evaporation 
        $$$

        E_{t}(t) = \text{MIN}(E_{t, pot}, E_{t, cap}) 

        $$$
        """
        return output

    @staticmethod
    def compute_et_f(dv, d_et_a):
        # todo [docstring]
        # [Evaporation - Soil] Compute the root zone depth factor
        output = 1 - (dv / (dv + d_et_a))
        r"""
        [Model Equation]
        Potential Soil Transpiration fraction
        $$$

        E_{t, f} = 1 - \frac{D_{v}}{D_{v} + D_{et, a}} 

        $$$
        """
        return output

    @staticmethod
    def compute_et_pot(e_pot, ec):
        # todo [docstring]
        # [Evaporation - Soil] Compute potential transpiration
        output = e_pot - ec  # discount canopy
        r"""
        [Model Equation]
        Potential Soil Transpiration
        $$$

        E_{t, pot} = E_{pot} - E_{c}

        $$$
        """
        return output

    @staticmethod
    def compute_et_cap(e_t_f, g, g_et_cap, dt):
        # todo [docstring]
        # [Evaporation - Soil] Compute the root zone depth factor
        output = e_t_f * np.min([g, g_et_cap]) * dt
        r"""
        [Model Equation]
        Potential Soil Tanspiration capacity
        $$$

        E_{t, cap} =  E_{t, f} * \text{MIN}(g, g_et_cap) * dt

        $$$
        """
        return output

    @staticmethod
    def compute_es(e_s_pot, e_s_cap):
        # todo [docstring]
        # [Evaporation - Surface] compute actual flow
        output = compute_flow(flow_pot=e_s_pot, flow_cap=e_s_cap)
        r"""
        [Model Equation]
        Actual Surface Evaporation 
        $$$

        E_{s}(t) = \text{MIN}(E_{s, pot}, E_{s, cap}) 

        $$$
        """
        return output

    @staticmethod
    def compute_es_pot(e_pot, ec, et):
        # todo [docstring]
        # [Evaporation - Surface] Compute potential evaporation
        output = e_pot - ec - et  # discount canopy and transpiration
        r"""
        [Model Equation]
        Potential Surface Evaporation
        $$$

        E_{s, pot} = E_{pot} - E_{c} - E_{t}

        $$$
        """
        return output

    @staticmethod
    def compute_es_cap(s, dt):
        # todo [docstring]
        # [Evaporation - Surface] Compute potential evaporation
        output = s * dt  # discount canopy and transpiration
        r"""
        [Model Equation]
        Surface Evaporation Capacity
        $$$

        E_{s, cap} = S * dt

        $$$
        """
        return output

    @staticmethod
    def compute_tf(p_tf_cap, p_tf_f):
        # todo [docstring]
        # [Canopy] throughfall flow
        output = p_tf_f * p_tf_cap
        r"""
        [Model Equation]
        throughfall flow
        $$$

        P_{tf} = P_{tf, f} * (P + C_{ss})

        $$$
        """
        return output

    @staticmethod
    def compute_tf_f(c, ca):
        # todo [docstring]
        # [Canopy] throughfall fraction
        # handle division by zero in the edge case when c_a = 0
        with np.errstate(divide="ignore", invalid="ignore"):
            output = np.where(ca <= 0.0, 1.0, np.where((c / ca) > 1.0, 1.0, (c / ca)))
        r"""
        [Model Equation]
        throughfall fraction
        $$$

        P_{tf, f} = \text{MIN}(1,  C(t)/C_{a}) 

        $$$
        """
        return output

    @staticmethod
    def compute_tf_cap(c, ca, p, dt):
        # todo [docstring]
        # [Canopy] Compute throughfall capacity
        ## c_ss_cap = np.max([0.0, c - ca]) * dt
        # [Canopy] Compute canopy spill storage capacity
        c_ss_cap = np.where((c - ca) < 0, 0.0, (c - ca)) * dt
        output = p + c_ss_cap
        r"""
        [Model Equation]
        Throughfall capacity
        $$$

        P_{tf, cap} = P + C_{ss}

        $$$
        """
        return output

    @staticmethod
    def compute_sf_pot(c, ca):
        # todo [docstring]
        # comment
        output = compute_flow(flow_pot=c, flow_cap=ca)
        r"""
        [Model Equation]
        Descr
        $$$

        values

        $$$
        """
        return output

    @staticmethod
    def compute_ps(sf, tf):
        # todo [docstring]
        # comment
        output = sf + tf
        r"""
        [Model Equation]
        todo [description]
        $$$

        todo [equation]

        $$$
        """
        return output

    @staticmethod
    def compute_pc(p, tf_f):
        # todo [docstring]
        # comment
        output = p * (1 - tf_f)
        r"""
        [Model Equation]
        todo [description]
        $$$

        todo [equation]

        $$$
        """
        return output

    @staticmethod
    def compute_e_discount(storage, discount):
        # todo [docstring]
        # comment
        output = storage - discount
        return output

    @staticmethod
    def compute_sof_cap(s, sof_a):
        # todo [docstring]
        # [Surface] [Overland] Compute surface overland spill storage capacity
        ss = s - sof_a
        output = np.where(ss < 0.0, 0.0, ss)
        r"""
        [Model Equation]
        todo [description]
        $$$

        todo [equation]

        $$$
        """
        return output

    @staticmethod
    def compute_qof_f(sof_cap, sof_c):
        # todo [docstring]
        # [Surface] [Overland] Compute overland flow fraction
        with np.errstate(divide="ignore", invalid="ignore"):
            output = np.where(
                (sof_cap + sof_c) == 0.0, 0.0, (sof_cap / (sof_cap + sof_c))
            )
        r"""
        [Model Equation]
        Overland flow fraction
        $$$

        Q_{of, f}(t) = \frac{S(t) - S_{of, a}(t)}{S(t) - S_{of, a}(t) + S_{of, c}(t)}

        $$$
        """
        return output

    @staticmethod
    def compute_qof_cap(sof_cap, ps, dt):
        # todo [docstring]
        # comment
        output = (sof_cap * dt) + ps
        r"""
        [Model Equation]
        todo [description]
        $$$

        todo [equation]

        $$$
        """
        return output

    @staticmethod
    def compute_qof_pot(qof_cap, qof_f):
        # todo [docstring]
        # comment
        output = qof_f * qof_cap
        r"""
        [Model Equation]
        Overland flow
        $$$

        Q_{of}(t) = Q_{of, f}(t) * (\frac{(S(t) - S_{of, a}(t))}{\Delta t} + P_{s})

        $$$
        """
        return output

    @staticmethod
    def compute_suf_cap(s, suf_a, shutdown):
        # todo [docstring]
        # [Surface] [Underland] Compute surface underland spill storage capacity
        ss = s - suf_a
        output = np.where(ss < 0.0, 0.0, ss) * shutdown
        r"""
        [Model Equation]
        todo [description]
        $$$

        todo [equation]

        $$$
        """
        return output

    @staticmethod
    def compute_quf_f(suf_cap, suf_c):
        # todo [docstring]
        # [Surface] [Underland] Compute underland flow fraction
        with np.errstate(divide="ignore", invalid="ignore"):
            output = np.where((suf_cap + suf_c) == 0, 0, (suf_cap / (suf_cap + suf_c)))
        r"""
        [Model Equation]
        Underland flow fraction
        $$$

        Q_{uf, f}(t) = \frac{S(t) - S_{uf, a}(t)}{S(t) - S_{uf, a}(t) + S_{uf, c}(t)}

        $$$
        """
        return output

    @staticmethod
    def compute_quf_cap(suf_cap, dt):
        # todo [docstring]
        # [Surface] [Underland] Compute underland flow capacity
        output = suf_cap * dt
        r"""
        [Model Equation]
        todo [description]
        $$$

        todo [equation]

        $$$
        """
        return output

    @staticmethod
    def compute_quf_pot(quf_cap, quf_f):
        # todo [docstring]
        # comment
        output = quf_f * quf_cap
        r"""
        [Model Equation]
        Underland flow
        $$$

        Q_{uf}(t) = Q_{uf, f}(t) * \frac{(S(t) - S_{uf, a}(t))}{\Delta t}

        $$$
        """
        return output

    @staticmethod
    def compute_qif_pot_up(s, sk, dt):
        # todo [docstring]
        # [Surface] [Infiltration] -- Potential infiltration
        # from upstream (hydraulic head)
        output = compute_decay(s=s, k=sk, dt=dt)
        r"""
        [Model Equation]
        Infiltration flow
        $$$

        Q_{if}(t) = \frac{1}{S_{k}} * S(t)

        $$$
        """
        return output

    @staticmethod
    def compute_qif_pot_down(d, v, dt):
        # todo [docstring]
        # [Surface] [Infiltration] --
        # Potential infiltration from downstream (soil)
        output = (d - v) * dt
        r"""
        [Model Equation]
        todo [description]
        $$$

        todo [equation]

        $$$
        """
        return output

    @staticmethod
    def compute_qif_pot(if_down, if_up):
        # todo [docstring]
        # [Surface] [Infiltration] -- Potential infiltration
        # constrained by two sides
        output = np.where(if_up > if_down, if_down, if_up)
        r"""
        [Model Equation]
        todo [description]
        $$$

        todo [equation]

        $$$
        """
        return output

    @staticmethod
    def compute_qvf_f(d, v):
        # todo [docstring]
        # [Soil Vadose Zone] Get Recharge Fraction
        with np.errstate(divide="ignore", invalid="ignore"):
            output = np.where(d <= 0.0, 1.0, (v / d))
        r"""
        [Model Equation]
        Vertical (Recharge) flow fraction
        $$$

        Q_{vf, f}(t) = \frac{V(t)}{D(t)}

        $$$
        """
        return output

    @staticmethod
    def compute_qvf_pot(qvf_f, kv, dt):
        # todo [docstring]
        # [Soil Vadose Zone] Compute Potential Recharge
        output = qvf_f * kv * dt
        r"""
        [Model Equation]
        Vertical (Recharge) flow
        $$$

        Q_{vf}(t) = Q_{vf, f}(t) * K

        $$$
        """
        return output

    @staticmethod
    def compute_qvf_cap(v, dt):
        # todo [docstring]
        # [Soil Vadose Zone] Compute Maximal Recharge
        output = v * dt
        r"""
        [Model Equation]
        todo [description]
        $$$

        todo [equation]

        $$$
        """
        return output

    @staticmethod
    def compute_qvf(qvf_pot, qvf_cap):
        # todo [docstring]
        # [Soil Vadose Zone] Compute Recharge Capacity
        output = compute_flow(flow_pot=qvf_pot, flow_cap=qvf_cap)
        r"""
        [Model Equation]
        todo [description]
        $$$

        todo [equation]

        $$$
        """
        return output

    @staticmethod
    def compute_qgf(g, get_cap, gk, dt):
        # todo [docstring]
        # [Soil Phreatic Zone] Compute Base flow
        # (blue water -- discount on green water)
        s0 = g - get_cap
        s = np.where(s0 > 0.0, s0, 0.0)
        output = compute_decay(s=s, k=gk, dt=dt)
        r"""
        [Model Equation]
        Baseflow
        $$$

        Q_{gf}(t) = \frac{1}{G_{k}} * (G(t) - G_{et, cap})

        $$$
        """
        return output

    @staticmethod
    def compute_next_c(c, pc, sf):
        # todo [docstring]
        # comment
        output = c + pc - sf
        r"""
        [Model Equation]
        Canopy water balance. $E_{c}$ is discounted earlier.
        $$$

        C(t + 1) = C(t) + P_{c}(t) - P_{sf}(t) 

        $$$
        """
        return output

    @staticmethod
    def compute_next_s(s, ps, qof, quf, qif):
        # todo [docstring]
        # comment
        output = s + ps - qof - quf - qif
        r"""
        [Model Equation]
        Surface water balance. $E_{c}$ is discounted earlier in procedure.
        $$$

        S(t + 1) = S(t) + P_{s}(t) - E_{s}(t) - Q_{if}(t) - Q_{uf}(t) - Q_{of}(t)

        $$$
        """
        return output

    @staticmethod
    def compute_next_v(v, qif, qvf):
        # todo [docstring]
        # [Vadose Water Balance] ---- Apply water balance
        output = v + qif - qvf
        r"""
        [Model Equation]
        Vadose zone water balance
        $$$

        V(t + 1) = V(t) + Q_{if}(t) - Q_{vf}(t)

        $$$
        """
        return output

    @staticmethod
    def compute_next_g(g, qvf, qgf):
        # todo [docstring]
        # [Phreatic Water Balance] ---- Apply water balance
        output = g + qvf - qgf
        r"""
        [Model Equation]
        Phreatic zone water balance. $E_{t}$ is discounted earlier in the procedure.
        $$$

        G(t + 1) = G(t) + Q_{vf}(t) - E_{t}(t) - Q_{bf}(t) 

        $$$
        """
        return output

    @staticmethod
    def compute_e(ec, es, eg):
        # todo [docstring]
        # [Total Flows] Total E
        output = ec + es + eg
        r"""
        [Model Equation]
        Total evaporation
        $$$

        E(t) =  E_{c}(t) + E_{s}(t) + E_{t}(t)

        $$$
        """
        return output

    @staticmethod
    def compute_qhf(qof, quf, qgf):
        # todo [docstring]
        # [Total Flows] Compute Hillslope flow
        output = qof + quf + qgf
        r"""
        [Model Equation]
        todo [description]
        $$$

        todo [equation]

        $$$
        """
        return output

    @staticmethod
    def demo():
        # todo [docstring]
        # comment
        output = None
        r"""
        [Model Equation]
        todo [description]
        $$$

        todo [equation]

        $$$
        """
        return output


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
