# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
Handle spatial datasets (maps).

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

from plans.datasets.core import *


# -----------------------------------------
# Derived Raster data structures


class Elevation(SciRaster):
    """
    Elevation (DEM) raster map dataset.

    """

    def __init__(self, name="DEM"):
        """
        Initialize dataset

        :param name: name of map
        :type name: str
        """
        super().__init__(name=name)
        self.cmap = "BrBG_r"
        self.varname = "Elevation"
        self.varalias = "DEM"
        self.description = "Height above sea level"
        self.units = "m"
        self.range_default = (0, 2000)
        self._set_view_specs()

    def get_tpi(self, cell_radius):
        # todo [DEV]
        print("hi")

    def get_tpi_landforms(self, radius_micro, radius_macro):
        # todo [DEV]
        print("hi")


class Slope(SciRaster):
    """
    Slope raster map dataset.
    """

    def __init__(self, name="Slope"):
        """
        Initialize dataset

        :param name: name of map
        :type name: str
        """

        super().__init__(name=name)
        self.range_default = (0, 60)
        self.cmap = "OrRd"
        self.varname = "Slope"
        self.varalias = "SLP"
        self.description = "Slope of terrain"
        self.units = "deg."
        self._set_view_specs()


class TWI(SciRaster):
    """
    TWI raster map dataset.

    """

    def __init__(self, name="TWI"):
        """
        Initialize dataset

        :param name: name of map
        :type name: str
        """
        super().__init__(name=name)
        self.cmap = "YlGnBu"
        self.varname = "TWI"
        self.varalias = "TWI"
        self.description = "Topographical Wetness Index"
        self.units = "index units"
        self.range_default = (0, 25)
        self._set_view_specs()


class HTWI(SciRaster):
    """
    HTWI (HAND-TWI) raster map dataset.
    """

    def __init__(self, name="HTWI"):
        """
        Initialize dataset

        :param name: name of map
        :type name: str
        """
        super().__init__(name=name)
        self.cmap = "YlGnBu"
        self.varname = "HTWI"
        self.varalias = "HTWI"
        self.description = "HAND-enhanced Topographical Wetness Index"
        self.units = "index units"
        self.range_default = (0, 1)
        self._set_view_specs()


class HAND(SciRaster):
    """
    HAND raster map dataset.
    """

    def __init__(self, name="HAND"):
        """
        Initialize dataset

        :param name: name of map
        :type name: str
        """
        super().__init__(name=name)
        self.cmap = "YlGnBu_r"
        self.varname = "HAND"
        self.varalias = "HAND"
        self.description = "Height Above the Nearest Drainage"
        self.units = "m"
        self.range_default = (0, 200)
        self._set_view_specs()


class DTO(SciRaster):
    """
    Distance to outlet raster map dataset.
    """

    def __init__(self, name="DTO"):
        """
        Initialize dataset

        :param name: name of map
        :type name: str
        """
        super().__init__(name=name)
        self.cmap = "rainbow"  # "gist_rainbow_r"
        self.varname = "DTO"
        self.varalias = "DTO"
        self.description = "Distance To Outlet"
        self.units = "meters"
        self.range_default = None
        self._set_view_specs()


class FAC(SciRaster):
    """
    Flow Accumulation raster map dataset.
    """

    def __init__(self, name):
        """
        Initialize dataset.

        :param name: name of map
        :type name: str
        """
        super().__init__(name=name)
        self.cmap = "plasma_r"
        self.varname = "FlowAcc"
        self.varalias = "FAC"
        self.description = "Flow Accumulation or Upstream Area"
        self.units = "sq. meters"
        self.range_default = None
        self._set_view_specs()


class NDVI(SciRaster):
    """
    NDVI raster map dataset.
    """

    def __init__(self, name, datetime):
        """
        Initialize dataset.

        :param name: name of map
        :type name: str
        :param datetime: date of map in ``yyyy-mm-dd``
        :type datetime: str
        """
        super().__init__(name=name)
        self.cmap = "RdYlGn"
        self.varname = "NDVI"
        self.varalias = "NDVI"
        self.description = "Normalized difference vegetation index"
        self.units = "index units"
        self.datetime = datetime
        self.range_default = (-1, 1)
        self._set_view_specs()

    def set_data(self, grid):
        super().set_data(grid)
        self.cut_edges(upper=1, lower=-1)
        return None


class ET24h(SciRaster):
    """
    ET 24h raster map dataset.
    """

    def __init__(self, name, date):
        """
        Initialize dataset.

        :param name: name of map
        :type name: str
        :param date: date of map in ``yyyy-mm-dd``
        :type date: str
        """
        import matplotlib as mpl
        from matplotlib.colors import ListedColormap

        super().__init__(name=name)
        self.varname = "Daily Evapotranspiration"
        self.varalias = "ET24h"
        self.description = "Daily Evapotranspiration"
        self.units = "mm"
        # set custom cmap
        jet_big = mpl.colormaps["jet_r"]
        self.cmap = ListedColormap(jet_big(np.linspace(0.3, 0.75, 256)))
        self.datetime = date
        # view specs
        self.range_default = (0, 15)
        self._set_view_specs()

    def set_data(self, grid):
        super().set_data(grid)
        self.cut_edges(upper=100, lower=0)
        return None


class Hydrology(SciRaster):
    """
    Primitive hydrology raster map dataset.
    """

    def __init__(self, name, varalias, datetime):
        """
        Initialize dataset

        :param name: name of map
        :type name: str
        """

        super().__init__(name=name)

        # initial setups
        self._set_cmaps()
        self._set_vars()

        self.varalias = varalias.lower()
        str_cmap_id = "{} {}".format(
            self.vars_dc[self.varalias]["type"], self.vars_dc[self.varalias]["subtype"]
        )
        self.cmap = self.cmaps_dc[str_cmap_id]
        self.varname = self.vars_dc[self.varalias][self.field_varname]
        self.description = self.vars_dc[self.varalias][self.field_description]
        self.units = "mm"
        self.datetime = datetime
        self.timescale = "annual"
        self.range_default = None
        self._set_view_specs()

    def _set_cmaps(self):
        """
        Sets predefined colormaps for different types of scientific data.

        :return: None
        :rtype: None
        """
        import matplotlib as mpl
        from matplotlib.colors import ListedColormap

        self.cmaps_dc = {
            "flow surface": "gist_earth_r",
            "flow vapor": ListedColormap(
                mpl.colormaps["jet_r"](np.linspace(0.3, 0.75, 256))
            ),
            "flow subsurface": "gist_earth_r",
            "stock surface": "",
            "stock subsurface": "",
            "stock deficit": "gist_earth",
        }
        return None

    def _set_vars(self):
        # todo evaluate load this from csv
        self.vars_dc = {
            "deficit": {
                self.field_varname: "Deficit",
                "description": "Soil water potential",
                "type": "stock",
                "subtype": "deficit",
            },
            "r": {
                self.field_varname: "Runoff",
                "description": "Combined overland flows",
                "type": "flow",
                "subtype": "surface",
            },
            "rie": {
                self.field_varname: "Runoff by Infiltration Excess",
                "description": "Hortonian overland flow",
                "type": "flow",
                "subtype": "surface",
            },
            "rse": {
                self.field_varname: "Runoff by Saturation Excess",
                "description": "Dunnean overland flow",
                "type": "flow",
                "subtype": "surface",
            },
            "ptf": {
                self.field_varname: "Throughfall",
                "description": "Effective precipitation at the surface",
                "type": "flow",
                "subtype": "surface",
            },
            "inf": {
                self.field_varname: "Infiltration",
                "description": "Water infiltration in soil",
                "type": "flow",
                "subtype": "subsurface",
            },
            "qv": {
                self.field_varname: "Recharge",
                "description": "Recharge of groundwater",
                "type": "flow",
                "subtype": "subsurface",
            },
            "et": {
                self.field_varname: "Evapotranspiration",
                "description": "Combined Evaporation and Transpiration flows",
                "type": "flow",
                "subtype": "vapor",
            },
            "evc": {
                self.field_varname: "Canopy evaporation",
                "description": "Direct evaporation from canopy",
                "type": "flow",
                "subtype": "vapor",
            },
            "evs": {
                self.field_varname: "Surface evaporation",
                "description": "Direct evaporation from soil surface",
                "type": "flow",
                "subtype": "vapor",
            },
            "tun": {
                self.field_varname: "Soil tranpiration",
                "description": "Transpiration from the water moisture in the soil",
                "type": "flow",
                "subtype": "vapor",
            },
            "tgw": {
                self.field_varname: "Groundwater transpiration",
                "description": "Transpiration from the saturated water zone",
                "type": "flow",
                "subtype": "vapor",
            },
        }


class HabQuality(SciRaster):
    """
    Habitat Quality raster map dataset.
    """

    def __init__(self, name, datetime):
        """Initialize dataset.

        :param name: name of map
        :type name: str
        :param datetime: date of map in ``yyyy-mm-dd``
        :type datetime: str
        """
        super().__init__(name=name)
        self.varname = "Habitat Quality"
        self.varalias = "HQ"
        self.description = "Habitat Quality from the InVEST model"
        self.units = "index units"
        self.cmap = "RdYlGn"
        self.datetime = datetime
        # view specs
        self._set_view_specs()
        # customize
        self.view_specs["vmin"] = 0
        self.view_specs["vmax"] = 1

    def get_biodiversity_area(self, b_a: float = 1.0) -> Raster:
        """
        Get a raster of Biodiversity Area
        :param b_a: model parameter
        :type b_a: float
        :return: Raster object of biodiversity area
        :rtype: Raster
        """
        s = self.cellsize
        grid_ba = b_a * np.square(s) * self.data / 10000
        # instantiate output
        output_raster = EBA(name=self.name, datetime=self.datetime, q_a=b_a)
        # set raster
        output_raster.set_raster_metadata(metadata=self.raster_metadata)
        output_raster.prj = self.prj
        # set grid
        output_raster.set_data(grid=grid_ba)
        return output_raster


class HabDegradation(SciRaster):
    """
    Habitat Degradation raster map dataset.
    """

    def __init__(self, name, datetime):
        """Initialize dataset.

        :param name: name of map
        :type name: str
        :param datetime: date of map in ``yyyy-mm-dd``
        :type datetime: str
        """
        super().__init__(name=name)
        self.varname = "Habitat Degradation"
        self.varalias = "HDeg"
        self.description = "Habitat Degradation from the InVEST model"
        self.units = "index units"
        self.cmap = "YlOrRd"
        self.datetime = datetime
        self._set_view_specs()
        self.view_specs["vmin"] = 0
        self.view_specs["vmax"] = 0.7


class EBA(SciRaster):
    """
    Equivalent Biodiversity Area raster map dataset.
    """

    def __init__(self, name, datetime, q_a=1.0):
        """Initialize dataset.

        :param name: name of map
        :type name: str
        :param datetime: date of map in ``yyyy-mm-dd``
        :type datetime: str
        :param q_a: habitat quality reference
        :type q_a: float
        """
        super().__init__(name=name)
        self.cmap = "YlGn"
        self.varname = "Equivalent Biodiversity Area"
        self.varalias = "EBA"
        self.description = "Equivalent Biodiversity Area in ha equivalents"
        self.units = "ha"
        self.datetime = datetime
        self.eba_global = None
        self._set_view_specs()

    def set_data(self, grid):
        super(EBA, self).set_data(grid)
        self.eba_global = np.sum(grid)
        return None


# -----------------------------------------
# Quali Raster data structures


class Basins(QualiRaster):
    """
    Basins map dataset
    """

    def __init__(self, name="BasinsMap"):
        super().__init__(name, dtype="uint32")
        self.varname = "Basin"
        self.varalias = "Bs"
        self.description = "Ids map of basins"
        self.units = "basin ID"
        self.table = None

    @staticmethod
    def get_upstream_ids(basin_id, topology_df, visited=None):
        """Recursive utility function for listing all upstream basins

        :param basin_id: basin id to start
        :type basin_id: int
        :param topology_df: dataframe with topology. expected to have Id and Downstream_Id columns
        :type topology_df: pandas.DataFrame
        :param visited: visited id (default=None)
        :type visited: list or None
        :return: upstream ids
        :rtype: list
        """
        if visited is None:
            visited = []
        _df = topology_df.query("Downstream_Id == {}".format(basin_id)).copy()
        if len(_df) > 0:
            for i in range(len(_df)):
                next_id = _df["Id"].values[i]
                visited.append(next_id)
                visited = Basins.get_upstream_ids(
                    basin_id=next_id, topology_df=topology_df, visited=visited
                )
        return visited

    def get_basin_aoi(self, basin_id):
        # set aoi map
        aoi = AOI(name=self.name + "_" + str(basin_id))
        aoi.prj = self.prj
        aoi.set_raster_metadata(metadata=self.raster_metadata)
        # get grid
        lst_ids = [basin_id]
        grd_aoi = 1.0 * (self.data == basin_id)
        # get extra upstream basins
        upstream_ids = Basins.get_upstream_ids(
            basin_id=basin_id, topology_df=self.table
        )
        if len(upstream_ids) > 0:
            for up_id in upstream_ids:
                grd_aoi = grd_aoi + (1 * (self.data == up_id))

        grd_aoi = grd_aoi.astype(np.uint16)
        aoi.set_data(grid=grd_aoi)
        return aoi


class LULC(QualiRaster):
    """
    Land Use and Land Cover map dataset
    """

    def __init__(self, name, datetime):
        """Initialize :class:`LULC`` map

        :param name: name of map
        :type name: str
        :param datetime: date of map in ``yyyy-mm-dd``
        :type datetime: str
        """
        super().__init__(name)
        self.cmap = "tab20b"
        self.varname = "Land Use and Land Cover"
        self.varalias = "LULC"
        self.description = "Classes of Land Use and Land Cover"
        self.units = "classes ID"
        self.datetime = datetime


class LULCChange(QualiRaster):
    """
    Land Use and Land Cover Change map dataset
    """

    def __init__(self, name, date_start, date_end, name_lulc):
        """Initialize :class:`LULCChange`` map

        :param name: name of map
        :type name: str
        :param date_start: date of map in ``yyyy-mm-dd``
        :type date_start: str
        :param date_end: date of map in ``yyyy-mm-dd``
        :type date_end: str
        :param name_lulc: name of lulc incoming map
        :type name_lulc: str
        """
        super().__init__(name)
        self.cmap = "tab20b"
        self.varname = "LULC Change"
        self.varalias = "LULCC"
        self.description = "Change of Land Use and Land Cover"
        self.units = "Change ID"
        self.date_start = date_start
        self.date_end = date_end
        self.datetime = date_end
        df_aux = pd.DataFrame(
            {
                self.field_id: [
                    1,
                    2,
                    3,
                ],
                self.field_name: ["Retraction", "Stable", "Expansion"],
                self.field_alias: ["Rtr", "Stb", "Exp"],
                self.field_color: ["tab:purple", "tab:orange", "tab:red"],
            }
        )
        self.set_table(dataframe=df_aux)


class Lithology(QualiRaster):
    """
    Lithology map dataset
    """

    def __init__(self, name="LitoMap"):
        """
        Initialize :class:`Lithology`` map

        :param name:
        :type name:
        """
        super().__init__(name)
        self.cmap = "tab20c"
        self.varname = "Litological Domains"
        self.varalias = "Lito"
        self.description = "Litological outgcrop domains"
        self.units = "types ID"


class Soils(QualiRaster):
    """
    Soils map dataset
    """

    def __init__(self, name="SoilsMap"):
        super().__init__(name)
        self.cmap = "tab20c"
        self.varname = "Soil Types"
        self.varalias = "Soils"
        self.description = "Types of Soils and Substrate"
        self.units = "types ID"

    def set_hydro_soils(self, map_lito, map_hand, map_slope, n_hand=2, n_slope=10):
        """
        Set hydrological soils based on lithology, Hand and Slope maps.

        :param map_lito: Lithology raster map
        :type map_lito: :class:`datasets.Lithology`
        :param map_hand: HAND raster map
        :type map_hand: :class:`datasets.HAND`
        :param map_slope: Slope raster map
        :type map_slope: :class:`datasets.Slope`
        :param n_hand: HAND threshold for alluvial definition
        :type n_hand: float
        :param n_slope: Slope threshold for colluvial definition
        :type n_slope: float
        :return: None
        :rtype: None
        """
        # process grid
        grd_soils = map_lito.data.copy()
        # this assumes that there is less than 10 lito classes:
        grd_slopes = 10 * (map_slope.data > n_slope)
        # append colluvial (+10)
        grd_soils = grd_soils + grd_slopes
        # append alluvial
        grd_soils = grd_soils * (map_hand.data > n_hand)
        n_all_id = np.max(grd_soils) + 1
        grd_alluvial = n_all_id * (map_hand.data <= n_hand)
        grd_soils = grd_soils + grd_alluvial
        self.set_data(grid=grd_soils)

        # edit table
        # get table copy from lito
        df_table_res = map_lito.table[["Id", "Alias", "Name", "Color"]].copy()
        df_table_col = map_lito.table[["Id", "Alias", "Name", "Color"]].copy()
        #
        df_table_res["Name"] = "Residual " + df_table_res["Name"]
        df_table_res["Alias"] = "R" + df_table_res["Alias"]
        #
        df_table_col["Name"] = "Colluvial " + df_table_col["Name"]
        df_table_col["Alias"] = "C" + df_table_col["Alias"]
        df_table_col["Id"] = 10 + df_table_col["Id"].values
        # new soil table
        df_table_all = pd.DataFrame(
            {"Id": [n_all_id], "Alias": ["Alv"], "Name": ["Alluvial"], "Color": ["tan"]}
        )
        # append
        df_new = pd.concat([df_table_res, df_table_col], ignore_index=True)
        df_new = pd.concat([df_new, df_table_all], ignore_index=True)
        # set table
        self.set_table(dataframe=df_new)
        # set colors
        self.set_random_colors()
        # set more attributes
        self.prj = map_lito.prj
        self.set_raster_metadata(metadata=map_lito.raster_metadata)

        # reclassify
        df_new_table = self.table.copy()
        df_new_table["Id"] = [i for i in range(1, len(df_new_table) + 1)]
        dict_ids = {
            "Old_Id": self.table["Id"].values,
            "New_Id": df_new_table["Id"].values,
        }
        self.reclassify(dict_ids=dict_ids, df_new_table=df_new_table)
        return None


class AOI(QualiHard):
    """
    AOI map dataset
    """

    def __init__(self, name="AOIMap"):
        super().__init__(name)
        self.varname = "Area Of Interest"
        self.varalias = "AOI"
        self.description = "Boolean map an Area of Interest"
        self.units = "classes ID"
        self.area = None
        self.set_table(dataframe=self.get_table())

    def update(self):
        """
        Refresh all mutable attributes based on data (includins paths).
        Expected to be incremented downstream.

        :return: None
        :rtype: None
        """
        super().update()
        # refresh all mutable attributes
        if self.data is not None:
            # data size
            self.set_area()

        # ... continues in downstream objects ... #
        return None

    def get_table(self):
        """
        Retrieves a sample DataFrame representing an AOI classification table.

        :return: A DataFrame with sample AOI classification data.
        :rtype: :class:`pandas.DataFrame`
        """
        df_aux = pd.DataFrame(
            {
                self.field_id: [1, 2],
                self.field_alias: ["AOI", "EZ"],
                self.field_name: ["Area of Interest", "Exclusion Zone"],
                self.field_color: ["magenta", "silver"],
            }
        )
        return df_aux

    def set_area(self):
        self.area = self.cellsize * np.nansum(self.data)
        return None

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
            self.field_area: self.area,
        }
        # update
        dict_meta.update(dict_meta_local)
        return dict_meta

    def view(
        self,
        show=True,
        folder="./output",
        filename=None,
        dpi=150,
        fig_format="jpg",
    ):
        """Plot a basic pannel of raster map.

        :param show: boolean to show plot instead of saving, defaults to False
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
        map_aoi_aux = QualiRaster(name=self.name)

        # set up
        map_aoi_aux.varname = self.varname
        map_aoi_aux.varalias = self.varalias
        map_aoi_aux.units = self.units
        map_aoi_aux.set_table(dataframe=self.table)
        map_aoi_aux.view_specs = self.view_specs
        map_aoi_aux.set_raster_metadata(metadata=self.raster_metadata)
        map_aoi_aux.prj = self.prj
        map_aoi_aux.update()

        # process grid
        self.insert_nodata()
        grd_new = 2 * np.ones(shape=self.data.shape, dtype="byte")
        grd_new = grd_new - (1 * (self.data == 1))
        self.mask_nodata()
        map_aoi_aux.set_data(grid=grd_new)
        # this will call the view

        map_aoi_aux.view_specs["folder"] = folder
        map_aoi_aux.view_specs["filename"] = filename
        map_aoi_aux.view_specs["fig_format"] = fig_format
        map_aoi_aux.view_specs["dpi"] = dpi

        map_aoi_aux.view(
            show=show,
        )
        del map_aoi_aux
        return None


class LDD(QualiHard):
    """
    LDD - Local Drain Direction map dataset

    LDD uses ``wbt`` convention derived from the WhiteboxTool.

    .. csv-table:: ``wbt`` convention
       :width: 30%

       64, 128, 1
       32, 0, 2
       16, 8, 4

    """

    def __init__(self, name="LDDMap"):
        super().__init__(name)
        self.varname = "Local Drain Direction"
        self.varalias = "LDD"
        self.description = "Direction of flux"
        self.units = "direction ID"
        self.set_table(dataframe=self.get_table())
        self.view_specs["legend_ncol"] = 2
        self.view_specs["legend_x"] = 0.5

    def get_table(self):
        df_aux = pd.DataFrame(
            {
                self.field_id: [16, 8, 4, 32, 0, 2, 64, 128, 1],
                self.field_alias: [
                    "16-SW",
                    "8-S",
                    "4-SE",
                    "32-W",
                    "0-C",
                    "2-E",
                    "64-NW",
                    "128-N",
                    "1-NE",
                ],
                self.field_name: [
                    "South-west",
                    "South",
                    "South-east",
                    "West",
                    "Center",
                    "East",
                    "North-west",
                    "North",
                    "North-east",
                ],
                self.field_color: [
                    "olive",
                    "blue",
                    "teal",
                    "orange",
                    "purple",
                    "green",
                    "orangered",
                    "red",
                    "goldenrod",
                ],
            }
        )
        df_aux = df_aux.sort_values(by=self.field_id).copy()
        return df_aux


class NDVISeries(RasterSeries):
    def __init__(self, name):
        # instantiate raster sample
        rst_aux = NDVI(name="dummy", datetime=None)
        super().__init__(
            name=name,
            varname=rst_aux.varname,
            varalias=rst_aux.varalias,
            units=rst_aux.units,
            dtype=rst_aux.dtype,
        )
        # remove
        del rst_aux

    def load_data(self, name, datetime, file_data, prj_file):
        """Load a :class:`NDVI`` object from a raster file.

        :param name: name attribute
        :type name: str
        :param datetime: :class:`Raster.date`` date attribute, defaults to None
        :type datetime: str
        :param file_data: path to ``.asc`` raster file
        :type file_data: str
        :param prj_file: path to ``.prj`` projection file
        :type prj_file: str
        :return: None
        :rtype: None
        """
        # create raster
        rst_aux = NDVI(name=name, datetime=datetime)
        # read file
        rst_aux.load_asc(file=file_data)
        # append to test_collection
        self.append(new_object=rst_aux)
        # load prj file
        rst_aux.load_prj(file=prj_file)
        # delete aux
        del rst_aux
        return None


class ETSeries(RasterSeries):
    def __init__(self, name):
        # instantiate raster sample
        rst_aux = ET24h(name="dummy", date=None)
        super().__init__(
            name=name,
            varname=rst_aux.varname,
            varalias=rst_aux.varalias,
            units=rst_aux.units,
            dtype=rst_aux.dtype,
        )
        # remove
        del rst_aux

    def load_data(self, name, datetime, file_data, prj_file):
        """
        Load a :class:`ET24h`` object from a raster file.

        :param name: name attribute
        :type name: str
        :param datetime: datetime attribute, defaults to None
        :type datetime: str
        :param file_data: path to raster file
        :type file_data: str
        :param prj_file: path to projection file
        :type prj_file: str
        :return: None
        :rtype: None
        """
        # create raster
        rst_aux = ET24h(name=name, date=datetime)
        # read file
        rst_aux.load_asc(file=file_data)
        # append to test_collection
        self.append(new_object=rst_aux)
        # load prj file
        rst_aux.load_prj(file=prj_file)
        # delete aux
        del rst_aux
        return None


class AOICollection(QualiRasterCollection):
    """
    A :class:`QualiRasterCollection`` for holding AOI maps
    """

    def __init__(self, name):
        # instantiate raster sample
        rst_aux = AOI(name="dummy")
        super().__init__(
            name=name,
        )
        # remove
        del rst_aux

    def load_data(self, name, file_data, file_prj=None):
        """
        Load a :class:`AOI`` object from raster file.

        :param name: name attribute
        :type name: str
        :param file_data: path to raster file
        :type file_data: str
        :param file_prj: path to projection file
        :type file_prj: str
        :param file_table: path to table file
        :type file_table: str
        :return: None
        :rtype: None
        """
        # create raster
        rst_aux = AOI(name=name)
        # read file
        rst_aux.load_data(
            file_data=file_data,
            file_prj=file_prj,
        )
        # append to test_collection
        self.append(raster=rst_aux)
        # delete aux
        del rst_aux
        return None


class LULCSeries(QualiRasterSeries):
    """
    A :class:`QualiRasterSeries`` for holding Land Use and Land Cover maps
    """

    def __init__(self, name):
        # instantiate raster sample
        rst_aux = LULC(name="dummy", datetime=None)
        super().__init__(
            name=name,
            varname=rst_aux.varname,
            varalias=rst_aux.varalias,
            dtype=rst_aux.dtype,
        )
        # remove
        del rst_aux

    def load_data(self, name, datetime, file_data, file_prj=None, file_table=None):
        """
        Load a :class:`LULC`` object from raster file.

        :param name: name attribute
        :type name: str
        :param datetime: date attribute
        :type datetime: str
        :param file_data: path to raster file
        :type file_data: str
        :param file_prj: path to projection file
        :type file_prj: str
        :param file_table: path to table file
        :type file_table: str
        :return: None
        :rtype: None
        """
        # create raster
        rst_aux = LULC(name=name, datetime=datetime)
        # read file
        rst_aux.load_data(
            file_data=file_data,
            file_table=file_table,
            file_prj=file_prj,
        )
        # append to test_collection
        self.append(raster=rst_aux)
        # delete aux
        del rst_aux
        return None

    def get_lulcc(self, date_start, date_end, by_lulc_id):
        """Get the :class:`LULCChange`` of a given time interval and LULC class Id

        :param date_start: start date of time interval
        :type date_start: str
        :param date_end: end date of time interval
        :type date_end: str
        :param by_lulc_id: LULC class Id
        :type by_lulc_id: int
        :return: map of LULC Change
        :rtype: :class:`LULCChange`
        """
        # set up
        s_name_start = self.catalog.loc[self.catalog["Date"] == date_start][
            "Name"
        ].values[
            0
        ]  #
        s_name_end = self.catalog.loc[self.catalog["Date"] == date_end]["Name"].values[
            0
        ]

        # compute lulc change grid
        grd_lulcc = (1 * (self.collection[s_name_end].data == by_lulc_id)) - (
            1 * (self.collection[s_name_start].data == by_lulc_id)
        )
        grd_all = (1 * (self.collection[s_name_end].data == by_lulc_id)) + (
            1 * (self.collection[s_name_start].data == by_lulc_id)
        )
        grd_all = 1 * (grd_all > 0)
        grd_lulcc = (grd_lulcc + 2) * grd_all

        # get names
        s_name = self.name
        s_name_lulc = self.table.loc[self.table["Id"] == by_lulc_id]["Name"].values[0]
        # instantiate
        map_lulc_change = LULCChange(
            name="{} of {} from {} to {}".format(
                s_name, s_name_lulc, date_start, date_end
            ),
            name_lulc=s_name_lulc,
            date_start=date_start,
            date_end=date_end,
        )
        map_lulc_change.set_data(grid=grd_lulcc)
        map_lulc_change.set_raster_metadata(
            metadata=self.collection[s_name_start].raster_metadata
        )
        map_lulc_change.prj = self.collection[s_name_start].prj

        return map_lulc_change

    def get_lulcc_series(self, by_lulc_id):
        """Get the :class:`QualiRasterSeries`` of LULC Change for the entire LULC series for a given LULC Id

        :param by_lulc_id: LULC class Id
        :type by_lulc_id: int
        :return: Series of LULC Change
        :rtype: :class:`QualiRasterSeries`
        """
        series_lulcc = QualiRasterSeries(
            name="{} - Change Series".format(self.name),
            varname="Land Use and Land Cover Change",
            varalias="LULCC",
        )
        # loop in catalog
        for i in range(1, len(self.catalog)):
            raster = self.get_lulcc(
                date_start=self.catalog["Date"].values[i - 1],
                date_end=self.catalog["Date"].values[i],
                by_lulc_id=by_lulc_id,
            )
            series_lulcc.append(raster=raster)
        return series_lulcc

    def get_conversion_matrix(self, date_start, date_end, talk=False):
        """Compute the conversion matrix, expansion matrix and retraction matrix for a given interval

        :param date_start: start date of time interval
        :type date_start: str
        :param date_end: end date of time interval
        :type date_end: str
        :param talk: option for printing messages
        :type talk: bool
        :return: dict of outputs
        :rtype: dict
        """
        # get dates
        s_date_start = date_start
        s_date_end = date_end
        # get raster names
        s_name_start = self.catalog.loc[self.catalog["Date"] == date_start][
            "Name"
        ].values[
            0
        ]  #
        s_name_end = self.catalog.loc[self.catalog["Date"] == date_end]["Name"].values[
            0
        ]

        # compute export_areas
        df_areas_start = self.collection[s_name_start].get_areas()
        df_areas_end = self.collection[s_name_end].get_areas()
        # deploy variables
        df_conv = self.table.copy()
        df_conv["Date_start"] = s_date_start
        df_conv["Date_end"] = s_date_end
        df_conv["Area_f_start"] = df_areas_start["Area_f"].values
        df_conv["Area_f_end"] = df_areas_end["Area_f"].values
        df_conv["Area_km2_start"] = df_areas_start["Area_km2"].values
        df_conv["Area_km2_end"] = df_areas_end["Area_km2"].values

        lst_cols = list()
        for i in range(len(df_conv)):
            _alias = df_conv["Alias"].values[i]
            s_field = "to_{}_f".format(_alias)
            df_conv[s_field] = 0.0
            lst_cols.append(s_field)

        if talk:
            print("processing...")

        grd_conv = np.zeros(shape=(len(df_conv), len(df_conv)))
        for i in range(len(df_conv)):
            _id = df_conv["Id"].values[i]
            #
            # instantiate new LULC map
            map_lulc = LULC(name="Conversion", datetime=s_date_end)
            map_lulc.set_data(grid=self.collection[s_name_end].data)
            map_lulc.set_raster_metadata(
                metadata=self.collection[s_name_start].raster_metadata
            )
            map_lulc.set_table(dataframe=self.collection[s_name_start].table)
            map_lulc.prj = self.collection[s_name_start].prj
            #
            # apply aoi
            grd_aoi = 1 * (self.collection[s_name_start].data == _id)
            map_lulc.apply_aoi_mask(grid_aoi=grd_aoi, inplace=True)
            #
            # bypass all-masked aois
            if np.sum(map_lulc.data) is np.ma.masked:
                grd_conv[i] = np.zeros(len(df_conv))
            else:
                df_areas = map_lulc.get_areas()
                grd_conv[i] = df_areas["{}_f".format(map_lulc.field_area)].values

        # append to dataframe
        grd_conv = grd_conv.transpose()
        for i in range(len(df_conv)):
            df_conv[lst_cols[i]] = grd_conv[i]

        # get expansion matrix
        grd_exp = np.zeros(shape=grd_conv.shape)
        for i in range(len(grd_exp)):
            grd_exp[i] = df_conv["Area_f_start"].values * df_conv[lst_cols[i]].values
        np.fill_diagonal(grd_exp, 0)

        # get retraction matrix
        grd_rec = np.zeros(shape=grd_conv.shape)
        for i in range(len(grd_rec)):
            grd_rec[i] = df_conv["Area_f_start"].values[i] * grd_conv.transpose()[i]
        np.fill_diagonal(grd_rec, 0)

        return {
            "Dataframe": df_conv,
            "Conversion_Matrix": grd_conv,
            "Conversion_index": np.prod(np.diagonal(grd_conv)),
            "Expansion_Matrix": grd_exp,
            "Retraction_Matrix": grd_rec,
            "Date_start": date_start,
            "Date_end": date_end,
        }


if __name__ == "__main__":
    import matplotlib.pyplot as plt

    plt.style.use("seaborn-v0_8")

    s = Slope()
    s.load_data(
        asc_file="C:/plans/docs/datasets/topo/slope.asc",
        prj_file="C:/plans/docs/datasets/topo/slope.prj",
    )
    s.view()

    t = TWI()
    t.load_data(
        asc_file="C:/plans/docs/datasets/topo/twi.asc",
        prj_file="C:/plans/docs/datasets/topo/twi.prj",
    )
    t.view()
