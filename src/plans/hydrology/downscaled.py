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
from .upscaled import UpscaledModel

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


class DownscaledModel(UpscaledModel):
    """
    This is a local Rainfall-Runoff model. Simulates the the catchment globally and locally
    by applying downscaling methods. Expected inputs:

    - `clim.csv` for Precipitation (P) and Potential Evapotranspiration (E_pot).
    - `path_areas.csv` for deriving the geomorphic unit hydrograph.
    - # todo [complete]

    # todo [major docstring] examples

    """

    def __init__(self, name="MyLocal", alias="Loc001"):
        # todo [docstring]

        super().__init__(name=name, alias=alias)
        # overwriters
        self.object_alias = "Local"

        # simulation variables
        self.datakey = "map"
        self.use_g2g = True
        self.wmask = None

        # scenarios
        self.scenario_clim = "obs"
        self.scenario_lulc = "obs"

        self.folders = {}
        self.folders_ls = ["topo", "lulc", "clim", "basins", "soils"]

        # -------------- DATA -------------- #
        self.basemap = None

        # -------------- LOCAL INPUTS -------------- #

        # -------------- basins -------------- #

        # single basin data
        self.filename_data_basin = None
        self.data_basin = None

        # maps -- this will be a Collection
        self.data_basins = None
        self.file_data_basins_ls = None
        self.filename_data_basins = "basins_*.tif"
        # simulation basin
        self.sbasin = None

        # -------------- topographic saturation index -------------- #
        # tsi map
        self.data_tsi = None
        self.filename_data_tsi = "tsi.tif"
        self.tsi_n = 100  # default discretization for tsi

        # -------------- soils -------------- #

        # soil table
        self.data_soils_table = None
        self.data_soils_table_src = None
        self.file_data_soils_table = None
        self.filename_data_soils_table = "soils.csv"
        self.soils_n = None  # number of lulc classes

        # soil map
        self.data_soils = None
        self.file_data_soils = None
        self.filename_data_soils = "soils.tif"

        # -------------- lulc -------------- #

        # lulc table
        self.data_lulc_table = None
        self.data_lulc_table_src = None
        self.file_data_lulc_table = None
        self.filename_data_lulc_table = "lulc.csv"
        self.lulc_n = None  # number of lulc classes
        self.lulc_maps_ls = None
        self.lulc_maps_dc = None
        self.lulc_maps_dc_inv = None

        # lulc maps -- this will be a Collection
        self.data_lulc = None
        self.file_data_lulc_ls = None
        self.filename_data_lulc = "lulc_*.tif"

        """
        Instructions: make a model that handles both G2G and HRU approach.
        The trick seems to have a area matrix that is the same...   

        - Use downscale_values() functions from plans.geo
        - Downscaling may include parameter maps as proxys.
        - 

        """

    def _set_model_vars(self):
        # todo [docstring]
        super()._set_model_vars()
        # include local attribute
        ls_non_local = ["t", "p", "e_pot", "q_obs", "q", "qbf", "qhf", "qgf"]
        for v in self.vars:
            _b = True
            if v in set(ls_non_local):
                _b = False
            self.vars[v]["local"] = _b
        return None

    # todo [move upstream] -- evaluate to retrofit Global() so it can handle scenarios?
    def _set_scenario(self, scenario_clim="obs", scenario_lulc="obs"):
        # todo [docstring]
        if scenario_clim is not None:
            self.scenario_clim = scenario_clim
            self.folder_data_clim = Path(
                str(self.folders["clim"]) + f"/{self.scenario_clim}"
            )

        if scenario_lulc is not None:
            self.scenario_lulc = scenario_lulc
            self.folder_data_lulc = Path(
                str(self.folders["lulc"]) + f"/{self.scenario_lulc}"
            )

        return None

    def _set_sbasin(self, n=0):
        # todo [docstring]
        ls_cols = list(self.data_obs.columns)
        self.sbasin = ls_cols[n + 1]
        return None

    def _set_basemap(self):
        # todo [docstring]
        if self.use_g2g:
            shp = self.data_tsi.data.shape
        else:
            shp = (self.tsi_n, self.lulc_n * self.soils_n)
        self.basemap = np.ones(shape=shp, dtype=np.float32)
        return None

    def _setup_wmask(self):
        # todo [docstring]
        if self.use_g2g:
            self.wmask = self.data_basin.data.data
        else:
            # todo [develop] URH approach
            pass

        return None

    def _setup_vars(self):
        # todo [docstring]
        for v in self.vars:
            is_local = self.vars[v]["local"]
            if is_local:
                # append a zero 2d map with 2 rows
                self.vars[v]["map"] = np.array([self.basemap, self.basemap]) * 0.0
        return None

    def _setup_params(self):
        # todo [docstring]
        super()._setup_params()

        #
        # ---------------- parameter maps setup ----------------- #
        #
        dc_aux = {
            "lulc": {
                "table": self.data_lulc_table,
                "ids": self.data_lulc_table[self.field_id].values,
                "fields": set(self.data_lulc_table.columns),
            },
            "soils": {
                "table": self.data_soils_table,
                "ids": self.data_soils_table[self.field_id].values,
                "fields": set(self.data_soils_table.columns),
            },
        }

        # retrieve only conceptual parameters
        ls_params = []
        for p in self.params:
            p_kind = self.params[p]["kind"]
            if p_kind == "conceptual":
                ls_params.append(p)

        # loop over parameters
        for p in ls_params:
            p_domain = self.params[p]["domain"]
            # 1) weights
            if p_domain in set(dc_aux.keys()):

                # get ids
                vc_ids = dc_aux[p_domain]["ids"]

                # handle missing fields
                if p not in dc_aux[p_domain]["fields"]:
                    # set as constants
                    vc_weights = (vc_ids * 0.0) + 1.0
                else:
                    # grab from table
                    vc_weights = dc_aux[p_domain]["table"][p].values

                # downscale weights to match global mean
                vc_down = geo.downscale_linear(
                    scalar=self.params[p]["value"], array_covar=vc_weights, mode="mean"
                )
                # reset data table
                dc_aux[p_domain]["table"][p] = vc_down.copy()

            # [SOILS] parameter maps
            if p_domain == "soils":
                grd_src = self.data_soils.data.filled(fill_value=np.nan)
                # append as "map" key
                self.params[p]["map"] = geo.convert(
                    array=grd_src, old_values=vc_ids, new_values=vc_down
                )

            # [LULC] parameter maps
            if p_domain == "lulc":
                # run over all available lulcs
                for lulc in self.lulc_maps_ls:
                    grd_src = self.data_lulc.collection[lulc].data.filled(
                        fill_value=np.nan
                    )
                    # append as lulc name
                    self.params[p][lulc] = geo.convert(
                        array=grd_src, old_values=vc_ids, new_values=vc_down
                    )
            #

        return None

    def _setup_add_lulc_to_data(self):
        # todo [docstring]
        df_main = self.data.copy()
        df_lulc_meta = self.data_lulc.catalog.copy()

        # Convert 'datetime' columns to datetime objects
        df_main[self.field_datetime] = pd.to_datetime(df_main[self.field_datetime])
        df_lulc_meta[self.field_datetime] = pd.to_datetime(
            df_lulc_meta[self.field_datetime]
        )

        # Sort both DataFrames by 'datetime' for merge_asof
        df_main_sorted = df_main.sort_values(by=self.field_datetime)
        df_lulc_meta_sorted = df_lulc_meta.sort_values(by=self.field_datetime)

        # Perform a backward merge_asof to find the closest preceding or equal lulc entry
        merged_df = pd.merge_asof(
            df_main_sorted,
            df_lulc_meta_sorted[[self.field_datetime, self.field_name]],
            on=self.field_datetime,
            direction="backward",
        )
        # Rename the 'name' column to 'lulc'
        merged_df = merged_df.rename(columns={self.field_name: "lulc_map"})

        # get ids for lulc
        self.lulc_maps_dc = {}
        self.lulc_maps_dc_inv = {}
        for i in range(len(self.lulc_maps_ls)):
            self.lulc_maps_dc[self.lulc_maps_ls[i]] = i
            self.lulc_maps_dc_inv[i] = self.lulc_maps_ls[i]

        # handle fine tuning
        merged_df["lulc_map_id"] = (
            merged_df["lulc_map"].map(self.lulc_maps_dc).astype(np.int8)
        )
        merged_df.drop(columns=["lulc_map"], inplace=True)

        # reset clim data
        self.data = merged_df.copy()

        # append to simulation data also
        self.sdata["lulc_map_id"] = self.data["lulc_map_id"].values[:]

        return None

    def _setup_start(self):
        # todo [docstring]
        super()._setup_start()
        # loop over vars
        for v in self.vars:
            # set initial conditions on storages
            if self.vars[v]["kind"] == "level" and self.vars[v]["local"]:
                if v == "d" or v == "dv":
                    pass
                else:
                    self.vars[v]["map"][0] = (
                        self.vars[v]["map"][0] + self.params["{}0".format(v)]["value"]
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

        # folder parents
        for d in self.folders_ls:
            self.folders[d] = Path(str(self.folder_data) + "/" + d)
        # data folders
        self.folder_data_topo = self.folders["topo"]
        self.folder_data_soils = self.folders["soils"]
        self.folder_data_basins = self.folders["basins"]
        self.folder_data_obs = self.folders["basins"]
        self.folder_data_pah = self.folders["basins"]
        self._set_scenario(scenario_clim="obs", scenario_lulc="obs")

        self.folder_output = Path(str(self.folder_data.parent) + "/outputs")
        # ... continues in downstream objects ... #
        return None

    def get_evaldata(self):
        # todo [docstring]
        data_obs_src = self.data_obs.copy()
        s_standard = "{}_obs".format(self.var_eval)
        self.data_obs.rename(columns={self.sbasin: s_standard}, inplace=True)
        df = super().get_evaldata()
        # reset values
        self.data_obs = data_obs_src.copy()
        # df.rename(columns={s_standard: self.sbasin}, inplace=True)
        return df

    def load_basin(self):
        # todo [docstring]
        # set simulation basin
        self._set_sbasin()
        # load AOI map
        f = Path("{}/{}.tif".format(self.folders["basins"], self.sbasin))
        self.data_basin = ds.AOI(name=self.sbasin)
        self.data_basin.alias = self.sbasin
        self.data_basin.file_data = f
        self.data_basin.load_data(file_data=f)

        # todo [refactor]
        # this code is for multi-basin loading
        """
        # -------------- load available basins data -------------- #
        # map Collection
        self.file_data_basins_ls = glob.glob(f"{self.folder_data_basins}/{self.filename_data_basins}")
        self.data_basins = ds.QualiRasterCollection(name=self.name)
        # todo [DRY] -- optimize using a load_folder() approach
        #  self.data_basins.load_folder(folder=self.folder_data_basins, name_pattern=self.filename_data_basins)
        for f in self.file_data_basins_ls:
            # todo [DEV] -- feature for handling the file format (tif, etc)
            _name = os.path.basename(f).split("_")[-1].replace(".tif", "")
            _aoi = ds.AOI(name=_name)
            _aoi.alias = _name
            _aoi.file_data = f
            _aoi.load_data(file_data=f)
            self.data_basins.append(new_object=_aoi)
        """
        return None

    def load_tsi(self):
        # todo [docstring]
        # map
        self.file_data_tsi = Path(f"{self.folder_data_topo}/{self.filename_data_tsi}")
        self.data_tsi = ds.HTWI(name=self.name)
        self.data_tsi.load_data(file_data=self.file_data_tsi)
        return None

    def load_soils(self):
        # todo [docstring]
        # soils table
        self.file_data_soils_table = Path(
            "{}/{}".format(self.folders["soils"], self.filename_data_soils_table)
        )
        self.data_soils_table = pd.read_csv(
            self.file_data_soils_table,
            sep=self.file_csv_sep,
            encoding=self.file_encoding,
        )
        self.data_soils_table_src = self.data_soils_table.copy()
        self.soils_n = len(self.data_soils_table)

        # soils map
        self.file_data_soils = Path(
            f"{self.folder_data_soils}/{self.filename_data_soils}"
        )
        self.data_soils = ds.Soils(name=self.name)
        self.data_soils.load_data(
            file_data=self.file_data_soils, file_table=self.file_data_soils_table
        )
        return None

    def load_lulc(self):
        # todo [docstring]
        # lulc table
        self.file_data_lulc_table = Path(
            "{}/{}".format(self.folders["lulc"], self.filename_data_lulc_table)
        )
        self.data_lulc_table = pd.read_csv(
            self.file_data_lulc_table,
            sep=self.file_csv_sep,
            encoding=self.file_encoding,
        )
        self.data_lulc_table_src = self.data_lulc_table.copy()
        self.lulc_n = len(self.data_lulc_table)

        # lulc map collection
        self.data_lulc = ds.LULCSeries(name=self.name)
        # todo [develop] -- feature for handling the file format (tif, etc)
        self.data_lulc.load_folder(
            folder=self.folder_data_lulc,
            file_table=self.file_data_lulc_table,
            name_pattern=self.filename_data_lulc.replace(".tif", ""),
            talk=False,
        )
        self.lulc_maps_ls = list(self.data_lulc.collection.keys())
        return None

    def load_data(self):
        """
        Load simulation data. Expected to increment superior methods.

        :return: None
        :rtype: None
        """
        super().load_data()

        # -------------- load basin data -------------- #
        # todo [develop] multi-site simulation
        self.load_basin()

        # -------------- load topo data -------------- #
        self.load_tsi()

        # -------------- load soils data -------------- #
        self.load_soils()

        # -------------- load lulc data -------------- #
        self.load_lulc()

        # -------------- update other mutables -------------- #
        self._set_basemap()
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

        # set all local variables (this need to be only t and t+1)
        self._setup_vars()

        # setup superior object
        # this sets all global variables to the main data table
        super().setup()

        # add lulc to clim series
        self._setup_add_lulc_to_data()

        #
        # ---------------- parameter maps setup ----------------- #
        #

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
        #

        # [Soil] soil parameters
        g_cap = self.params["gcap"][self.datakey]
        # compute the global/basin gcap
        gb_g_cap = geo.upscale(array=g_cap, weights=self.wmask, mode="mean")
        k_v = self.params["kv"][self.datakey]
        g_k = self.params["gk"][self.datakey]
        # compute the global/basin gk
        gb_g_k = geo.upscale(array=g_k, weights=self.wmask, mode="mean")
        g_e_cap = self.params["ecap"][self.datakey]
        d_e_a = self.params["dea"][self.datakey]

        #
        # ---------------- derived parameter variables ----------------
        #

        # [Surface] Conpute shutdown factor for underland flow
        s_uf_shutdown = UpscaledModel.compute_s_uf_shutdown(s_uf_cap, s_uf_a)

        # [Surface] Compute effective overland flow activation level
        s_of_a_eff = UpscaledModel.compute_sof_a_eff(s_uf_cap, s_of_a)

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
            # reset i
            i = 0
            #
            # [LULC] ---------- variable parameters ---------- #
            #

            # access the current lulc epoch
            lulc_map_id = gb["lulc_map_id"][t]
            lulc_map_name = self.lulc_maps_dc_inv[lulc_map_id]

            # [Canopy] canopy parameters
            c_k = self.params["ck"][lulc_map_name]
            c_a = self.params["ca"][lulc_map_name]

            # [Surface] surface parameters
            s_k = self.params["sk"][lulc_map_name]
            s_of_a = self.params["sofa"][lulc_map_name]
            s_of_c = self.params["sofc"][lulc_map_name]
            s_uf_a = self.params["sufa"][lulc_map_name]
            s_uf_c = self.params["sufc"][lulc_map_name]
            s_uf_cap = self.params["sufcap"][lulc_map_name]

            #
            # [Deficit] ---------- update deficits ---------- #
            #

            # [Deficit] Phreatic zone deficit
            ## gb["d"][t] = Global.compute_d(g_cap=g_cap, g=gb["g"][t])
            gb["d"][t] = UpscaledModel.compute_d(g_cap=g_cap, g=gb["g"][t])

            # [Deficit] Vadose zone deficit
            gb["dv"][t] = UpscaledModel.compute_dv(d=gb["d"][t], v=gb["v"][t])

            #
            # [Evaporation] ---------- get evaporation flows first ---------- #
            #

            # [Evaporation] [Canopy] ---- evaporation from canopy

            # [Evaporation] [Canopy] compute potential flow
            e_c_pot = UpscaledModel.compute_ec_pot(e_pot=gb["e_pot"][t])

            # [Evaporation] [Canopy] compute capacity flow
            e_c_cap = UpscaledModel.compute_ec_cap(c=gb["c"][t], dt=dt)

            # [Evaporation] [Canopy] compute actual flow
            gb["ec"][t] = UpscaledModel.compute_ec(e_c_pot, e_c_cap)

            # [Evaporation] [Soil] ---- transpiration from soil

            # [Evaporation] [Soil] compute potential flow
            e_t_pot = UpscaledModel.compute_et_pot(e_pot=gb["e_pot"][t], ec=gb["ec"][t])

            # [Evaporation] [Soil] compute the root zone depth factor
            gb["egf"][t] = UpscaledModel.compute_et_f(dv=gb["dv"][t], d_et_a=d_e_a)

            # [Evaporation] [Soil] compute capacity flow
            e_t_cap = UpscaledModel.compute_et_cap(
                e_t_f=gb["egf"][t], g=gb["g"][t], g_et_cap=g_e_cap, dt=dt
            )

            # [Evaporation] [Soil] compute actual flow
            gb["eg"][t] = UpscaledModel.compute_et(e_t_pot, e_t_cap)

            # [Evaporation] [Surface] ---- evaporation from surface

            # [Evaporation] [Surface] compute potential flow
            e_s_pot = UpscaledModel.compute_es_pot(
                e_pot=gb["e_pot"][t], ec=gb["ec"][t], et=gb["eg"][t]
            )

            # [Evaporation] [Surface] compute capacity flow
            e_s_cap = UpscaledModel.compute_es_cap(s=gb["s"][t], dt=dt)

            # [Evaporation] [Surface] compute actual flow
            gb["es"][t] = UpscaledModel.compute_es(e_s_pot, e_s_cap)

            #
            # [Evaporation] [Balance] ---- a priori discounts ---------- #
            #

            # [Evaporation] [Balance] -- apply discount a priori
            gb["c"][t] = UpscaledModel.compute_e_discount(
                storage=gb["c"][t], discount=gb["ec"][t]
            )

            # [Evaporation] [Balance] -- apply discount a priori
            gb["g"][t] = UpscaledModel.compute_e_discount(
                storage=gb["g"][t], discount=gb["eg"][t]
            )

            # [Evaporation] [Balance] water balance -- apply discount a priori
            gb["s"][t] = UpscaledModel.compute_e_discount(
                storage=gb["s"][t], discount=gb["es"][t]
            )

            #
            # [Canopy] ---------- Solve canopy water balance ---------- #
            #

            # [Canopy] [Throughfall] --

            # [Canopy] [Throughfall] Compute throughfall fraction
            gb["ptff"][t] = UpscaledModel.compute_tf_f(c=gb["c"][t], ca=c_a)

            # [Canopy] [Throughfall] Compute throughfall capacity
            p_tf_cap = UpscaledModel.compute_tf_cap(
                c=gb["c"][t], ca=c_a, p=gb["p"][t], dt=dt
            )

            # [Canopy] [Throughfall] Compute throughfall
            gb["ptf"][t] = UpscaledModel.compute_tf(
                p_tf_cap=p_tf_cap, p_tf_f=gb["ptff"][t]
            )

            # [Canopy] [Stemflow] --

            # [Canopy] [Stemflow] Compute potential stemflow -- only activated storage contributes
            c_sf_pot = UpscaledModel.compute_sf_pot(c=gb["c"][t], ca=c_a)

            # [Canopy] [Stemflow] Compute actual stemflow
            gb["psf"][t] = compute_decay(s=c_sf_pot, dt=dt, k=c_k)

            # [Canopy] [Aggflows] --

            # [Canopy] [Aggflows] Compute effective rain on surface
            gb["ps"][t] = UpscaledModel.compute_ps(sf=gb["psf"][t], tf=gb["ptf"][t])

            # [Canopy] [Aggflows] Compute effective rain on canopy
            gb["pc"][t] = UpscaledModel.compute_pc(p=gb["p"][t], tf_f=gb["ptff"][t])

            # [Canopy] [Water Balance] ---- Apply water balance
            gb["c"][t + 1] = UpscaledModel.compute_next_c(
                c=gb["c"][t], pc=gb["pc"][t], sf=gb["psf"][t]
            )

            #
            # [Surface] ---------- Solve surface water balance ---------- #
            #

            # [Surface] [Overland] -- Overland flow

            # [Surface] [Overland] Compute surface overland spill storage capacity
            sof_ss_cap = UpscaledModel.compute_sof_cap(s=gb["s"][t], sof_a=s_of_a_eff)

            # [Surface] [Overland] Compute overland flow fraction
            gb["qoff"][t] = UpscaledModel.compute_qof_f(
                sof_cap=sof_ss_cap, sof_c=s_of_c
            )

            # [Surface] [Overland] Compute overland flow capacity
            q_of_cap = UpscaledModel.compute_qof_cap(
                sof_cap=sof_ss_cap, ps=gb["ps"][t], dt=dt
            )

            # [Surface] [Overland] Compute potential overland
            q_of_pot = UpscaledModel.compute_qof_pot(
                qof_cap=q_of_cap, qof_f=gb["qoff"][t]
            )

            # [Surface] [Underland] -- Underland flow

            # [Surface] [Underland] Compute surface underland spill storage capacity
            suf_ss_cap = UpscaledModel.compute_suf_cap(
                s=gb["s"][t], suf_a=s_uf_a, shutdown=s_uf_shutdown
            )

            # [Surface] [Underland] Compute underland flow fraction
            gb["quff"][t] = UpscaledModel.compute_quf_f(
                suf_cap=suf_ss_cap, suf_c=s_uf_c
            )

            # [Surface] [Underland] Compute underland flow capacity
            q_uf_cap = UpscaledModel.compute_quf_cap(suf_cap=suf_ss_cap, dt=dt)

            # [Surface] [Underland] Compute potential underland flow
            q_uf_pot = UpscaledModel.compute_quf_pot(
                quf_cap=q_uf_cap, quf_f=gb["quff"][t]
            )

            # [Surface] [Infiltration] -- Infiltration flow

            # [Surface] [Infiltration] -- Potential infiltration from downstream (soil)
            q_if_pot_down = UpscaledModel.compute_qif_pot_down(
                d=gb["d"][t], v=gb["v"][t], dt=dt
            )

            # [Surface] [Infiltration] -- Potential infiltration from upstream (hydraulic head)
            q_if_pot_up = UpscaledModel.compute_qif_pot_up(s=gb["s"][t], sk=s_k, dt=dt)

            # [Surface] [Infiltration] -- Potential infiltration
            q_if_pot = UpscaledModel.compute_qif_pot(
                if_down=q_if_pot_down, if_up=q_if_pot_up
            )

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
            gb["s"][t + 1] = UpscaledModel.compute_next_s(
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
            gb["qvff"][t] = UpscaledModel.compute_qvf_f(d=gb["d"][t], v=gb["v"][t])

            # [Soil Vadose Zone] Compute Potential Recharge
            q_vf_pot = UpscaledModel.compute_qvf_pot(qvf_f=gb["qvff"][t], kv=k_v, dt=dt)

            # [Soil Vadose Zone] Compute Maximal Recharge
            q_vf_cap = UpscaledModel.compute_qvf_cap(v=gb["v"][t], dt=dt)

            # [Soil Vadose Zone] Compute Actual Recharge
            gb["qvf"][t] = UpscaledModel.compute_qvf(qvf_pot=q_vf_pot, qvf_cap=q_vf_cap)

            # [Vadose Water Balance] ---- Apply water balance
            gb["v"][t + 1] = UpscaledModel.compute_next_v(
                v=gb["v"][t], qif=gb["qif"][t], qvf=gb["qvf"][t]
            )

            # [Soil Phreatic Zone]

            # [Soil Phreatic Zone] Compute Base flow (blue water -- discount on green water)
            # gb["qgf"][t] = (np.max([gb["g"][t] - g_et_cap, 0.0])) * dt / g_k
            gb["qgf"][t] = UpscaledModel.compute_qgf(
                g=gb["g"][t], get_cap=g_e_cap, gk=g_k, dt=dt
            )

            # [Testing feature]
            if self.shutdown_qbf:
                gb["qgf"][t] = 0.0 * gb["qgf"][t]

            # [Phreatic Water Balance] ---- Apply water balance
            gb["g"][t + 1] = UpscaledModel.compute_next_g(
                g=gb["g"][t], qvf=gb["qvf"][t], qgf=gb["qgf"][t]
            )

            # ---------------- END TIME LOOP ---------------- #

        #
        # [Total Flows] ---------- compute total flows ---------- #
        #

        # [Total Flows] Total E
        gb["e"] = UpscaledModel.compute_e(ec=gb["ec"], es=gb["es"], eg=gb["eg"])

        # [Total Flows] Compute Hillslope flow
        gb["qhf"] = UpscaledModel.compute_qhf(
            qof=gb["qof"], quf=gb["quf"], qgf=gb["qgf"]
        )

        #
        # [Streamflow] ---------- Solve flow routing to basin gauge station ---------- #
        #

        # global basin is considered the first
        basin = self.basins_ls[0]

        # [Baseflow] Compute river base flow
        vct_inflow = gb["qgf"]
        gb["qbf"] = UpscaledModel.propagate_inflow(
            inflow=vct_inflow,
            unit_hydrograph=self.data_guh[basin].values,
        )

        # [Fast Streamflow] Compute Streamflow
        # todo [feature] evaluate to split into more components
        vct_inflow = gb["quf"] + gb["qof"]
        q_fast = UpscaledModel.propagate_inflow(
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
        super().export(folder, filename=filename, views=views, mode=mode)

        # handle Local views
        if views:
            # todo [develop] local views
            pass

        # export Soils table data
        fpath = Path(folder + "/" + filename + "_" + self.filename_data_soils_table)
        self.data_soils_table.to_csv(
            fpath, sep=self.file_csv_sep, encoding=self.file_encoding, index=False
        )
        # export LULC table data
        fpath = Path(folder + "/" + filename + "_" + self.filename_data_lulc_table)
        self.data_lulc_table.to_csv(
            fpath, sep=self.file_csv_sep, encoding=self.file_encoding, index=False
        )
        # ... continues in downstream objects ... #

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
