# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.

"""
Utility routines for QGIS 3.x Python console

Overview
--------

Required dependencies in QGIS:

- pcraster
- saga
- gdal
- processing
- geopandas

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

# native imports
import glob, os, shutil
from pathlib import Path

# basic imports
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import geopandas as gpd

# qgis imports
import processing
from osgeo import gdal
from qgis.core import QgsCoordinateReferenceSystem

# plugin imports
from plans import geo
from plans.parsers import qgdal
from plans.datasets import Raster
from plans.datasets.core import DC_NODATA

# ----------------- MODULE CONSTANTS ----------------- #

# provider base
DC_PROVIDERS = {
    "4326": "EPSG",
    "31983": "EPSG",
    "31982": "EPSG",
    "31981": "EPSG",
    "5641": "EPSG",
    "102033": "ESRI",
}
# operations base (hard-coded catalog)
DC_OPERATIONS = {
    "31983": "+proj=pipeline +step +proj=unitconvert +xy_in=deg +xy_out=rad +step +proj=utm +zone=23 +south +ellps=GRS80",
    "31982": "+proj=pipeline +step +proj=unitconvert +xy_in=deg +xy_out=rad +step +proj=utm +zone=22 +south +ellps=GRS80",
    "31981": "+proj=pipeline +step +proj=unitconvert +xy_in=deg +xy_out=rad +step +proj=utm +zone=21 +south +ellps=GRS80",
    "5641": "+proj=pipeline +step +proj=unitconvert +xy_in=deg +xy_out=rad +step +proj=merc +lat_ts=-2 +lon_0=-43 +x_0=5000000 +y_0=10000000 +ellps=GRS80",
    "102033": "+proj=pipeline +step +proj=unitconvert +xy_in=deg +xy_out=rad +step +proj=push +v_3 +step +proj=cart +ellps=WGS84 +step +proj=helmert +x=57 +y=-1 +z=41 +step +inv +proj=cart +ellps=aust_SA +step +proj=pop +v_3 +step +proj=aea +lat_0=-32 +lon_0=-60 +lat_1=-5 +lat_2=-42 +x_0=0 +y_0=0 +ellps=aust_SA",
}

# -------------------------------------------------------------------------------------
# STANDALONE ROUTINES
# This routines work without expecting any sort of folder struture


def clip_layer(
    db_input, layer_input, db_overlay, layer_overlay, db_output, layer_output
):
    processing.run(
        "native:clip",
        {
            "INPUT": f"{db_input}|layername={layer_input}",
            "OVERLAY": f"{db_overlay}|layername={layer_overlay}",
            "OUTPUT": "ogr:dbname='{}' table=\"{}\" (geom)".format(
                db_output, layer_output
            ),
        },
    )
    return layer_output


def reproject_layer(
    db_input, layer_name, crs_target, db_output=None, layer_output=None
):
    """
    Reproject a vector layer

    :param db_input: path to geopackage database
    :type db_input: str
    :param crs_target: EPSG code (number only) for the target CRS
    :type crs_target: str
    :param layer_name: name of the layer in database
    :type layer_name: str
    :return: new layer name (echo)
    :rtype: str
    """
    input_file = "{}|layername={}".format(db_input, layer_name)
    if layer_output is None:
        layer_output = "{}_{}_{}".format(
            layer_name, DC_PROVIDERS[crs_target], crs_target
        )
    # handle if output is the same
    if db_output is None:
        db_output = db_input[:]
    output_file = "ogr:dbname='{}' table=\"{}\" (geom)".format(db_output, layer_output)
    processing.run(
        "native:reprojectlayer",
        {
            "INPUT": input_file,
            "TARGET_CRS": QgsCoordinateReferenceSystem(
                "{}:{}".format(DC_PROVIDERS[crs_target], crs_target)
            ),
            "OPERATION": DC_OPERATIONS[crs_target],
            "OUTPUT": output_file,
        },
    )
    return layer_output


def is_bounded_by(extent_a, extent_b):
    """
    Check if extent B is bounded by extent A

    :param extent_a: extent A
    :type extent_a: dict
    :param extent_b: extent B
    :type extent_b: dict
    :return: Case if bounded
    :rtype: bool
    """
    return (
        extent_a["xmin"] <= extent_b["xmin"] <= extent_b["xmax"] <= extent_a["xmax"]
        and extent_a["ymin"] <= extent_b["ymin"] <= extent_b["ymax"] <= extent_a["ymax"]
    )


def get_extent_from_raster(file_input):
    """
    Get the extent from a raster layer

    :param file_input: file path to raster layer
    :type file_input: str
    :return: dictionary of bouding box: xmin, xmax, ymin, ymax
    :rtype: dict
    """
    from qgis.core import QgsRasterLayer

    # Create a raster layer object
    raster_layer = QgsRasterLayer(file_input, "Raster Layer")
    layer_extent = raster_layer.extent()

    return {
        "xmin": layer_extent.xMinimum(),
        "xmax": layer_extent.xMaximum(),
        "ymin": layer_extent.yMinimum(),
        "ymax": layer_extent.yMaximum(),
    }


def get_extent_from_vector(db_input, layer_name):
    """
    Get the extent from a vector layer

    :param db_input: path to geopackage database
    :type db_input: str
    :param layer_name: name of the layer in geopackage database
    :type layer_name: str
    :return: dictionary of bouding box: xmin, xmax, ymin, ymax
    :rtype: dict
    """
    from qgis.core import QgsVectorLayer

    # Create the vector layer from the GeoPackage
    layer = QgsVectorLayer(
        "{}|layername={}".format(db_input, layer_name), layer_name, "ogr"
    )
    layer_extent = layer.extent()
    return {
        "xmin": layer_extent.xMinimum(),
        "xmax": layer_extent.xMaximum(),
        "ymin": layer_extent.yMinimum(),
        "ymax": layer_extent.yMaximum(),
    }


def count_vector_features(input_db, layer_name):
    """
    Get the number of features from a vector layer

    :param input_db: path to geopackage database
    :type input_db: str or Path
    :param layer_name: name of the layer in geopackage database
    :type layer_name: str
    :return: number of features
    :rtype: int
    """
    from qgis.core import QgsVectorLayer

    # Create the vector layer from the GeoPackage
    layer = QgsVectorLayer(
        "{}|layername={}".format(input_db, layer_name), layer_name, "ogr"
    )
    return int(layer.featureCount())


def retrieve_raster_tiles(
    db_aoi,
    layer_aoi,
    db_tiles,
    layer_tiles,
    folder_raster,
    folder_output,
    name_output,
    tile_field="tile_code",
):
    """
    Retrieve and merge raster tiles into single raster

    :param db_aoi: path to Area Of Interest database (geopackage)
    :type db_aoi: str
    :param layer_aoi: name of aoi layer
    :type layer_aoi: str
    :param db_tiles: path to tiles database (geopackage)
    :type db_tiles: str
    :param layer_tiles: name of tile layer
    :type layer_tiles: str
    :param folder_raster: path to input raster directory (tiles)
    :type folder_raster: str
    :param folder_output: path to output raster directory (merged)
    :type folder_output: str
    :param name_output: name of output raster file (merged) -- no extension
    :type name_output: str
    :param tile_field: name of tile field
    :type tile_field: str
    :return: path to output raster file (merged)
    :rtype: str


    Script example (for QGIS Python Console):

    .. code-block:: python

        # plans source code must be pasted to QGIS plugins directory
        from plans import qutils

        # call function
        dem_src = qutils.retrieve_raster_tiles(
            db_aoi="/path/to/aoi_database.gpkg",
            layer_aoi="layer",
            db_tiles="/path/to/tile_database.gpkg",
            layer_tiles="tiles",
            folder_raster="/path/to/folder",
            folder_output="/path/to/folder",
            name_output="src_dem"
        )


    """
    # handle folder

    print("retrieving tiles...")
    # extract tiles
    processing.run(
        "native:extractbylocation",
        {
            "INPUT": f"{db_tiles}|layername={layer_tiles}",
            "PREDICATE": [0],
            "INTERSECT": f"{db_aoi}|layername={layer_aoi}",
            "OUTPUT": f"ogr:dbname='{folder_output}/{name_output}.gpkg' table=\"tiles\" (geom)",
        },
    )

    # list tiles
    gdf = gpd.read_file(f"{folder_output}/{name_output}.gpkg", layer="tiles")
    ls_codes = list(gdf["tile_code"])
    ls_rasters = []
    for code in ls_codes:
        ls_raster = glob.glob(f"{folder_raster}/*{code}*.tif")
        for raster_file in ls_raster:
            rfile = str(Path(raster_file))
            ls_rasters.append(rfile)

    output_file = f"{folder_output}/{name_output}.tif"
    n_tiles = len(ls_rasters)
    if n_tiles == 1:
        print("one tile found, copying...")
        shutil.copy(src=ls_rasters[0], dst=output_file)
    else:
        print(f"merging {n_tiles} tiles...")
        processing.run(
            "gdal:merge",
            {
                "INPUT": ls_rasters,
                "PCT": False,
                "SEPARATE": False,
                "NODATA_INPUT": None,
                "NODATA_OUTPUT": None,
                "OPTIONS": "",
                "EXTRA": "",
                "DATA_TYPE": 5,
                "OUTPUT": output_file,
            },
        )
    print("merging --DONE")
    return output_file


def retrieve_upstream_basins(
    db_basins,
    layer_basin,
    db_gauges,
    layer_gauges,
    db_output,
    layer_output,
    field_gauge,
    field_basin,
    field_basin_down,
    field_geometry="geometry",
):
    """
    Retrieves and saves upstream basins for a given set of gauges.

    This function loads basin and gauge data from GeoPackage files, identifies the upstream basins for each gauge, and then saves the resulting GeoDataFrame to a new GeoPackage file. The upstream basins for each gauge are dissolved into a single feature before saving.

    :param db_basins: The path to the GeoPackage database containing the basin features.
    :type db_basins: str
    :param layer_basin: The name of the layer in `db_basins` containing the basin features.
    :type layer_basin: str
    :param db_gauges: The path to the GeoPackage database containing the gauge features.
    :type db_gauges: str
    :param layer_gauges: The name of the layer in `db_gauges` containing the gauge features.
    :type layer_gauges: str
    :param db_output: The path to the output GeoPackage database where the results will be saved.
    :type db_output: str
    :param layer_output: The name of the layer to be created in `db_output`.
    :type layer_output: str
    :param field_gauge: The name of the column in `gauges` that contains the unique identifier for each gauge.
    :type field_gauge: str
    :param field_basin: The name of the column in `basins` that contains the unique identifier for each basin.
    :type field_basin: str
    :param field_basin_down: The name of the column in `basins` that contains the unique identifier of the downstream basin.
    :type field_basin_down: str
    :param field_geometry: The name of the geometry column. Default value = "geometry"
    :type field_geometry: str
    :return: None
    :rtype: None
    """
    # load from geopackages
    basins = gpd.read_file(db_basins, layer=layer_basin)
    gauges = gpd.read_file(db_gauges, layer=layer_gauges)
    # get geodataframe
    basins_upstream = geo.get_basins_by_gauges(
        basins=basins,
        gauges=gauges,
        field_gauge=field_gauge,
        field_basin=field_basin,
        field_basin_down=field_basin_down,
        field_geometry=field_geometry,
        dissolve=True,
    )
    # export to file
    basins_upstream.to_file(db_output, layer=layer_output, driver="GPKG")

    return None


def get_basins_areas(file_basins, ids_basins):
    """
    Calculates the area of specified basins from a raster file.

    This function reads a raster file representing different basins, identifies the cells corresponding to each basin ID provided, calculates the total area for each basin in square kilometers, and returns the results in a dictionary.

    :param file_basins: The file path to the raster containing the basin IDs.
    :type file_basins: str
    :param ids_basins: A list of basin IDs for which to calculate the area.
    :type ids_basins: list
    :return: A dictionary containing the basin IDs and their corresponding upstream areas in square kilometers.
    :rtype: dict
    """
    # -------------------------------------------------------------------------
    # LOAD BASINS

    # Open the raster file using gdal
    raster_input = gdal.Open(file_basins)

    # Get the raster band
    band_input = raster_input.GetRasterBand(1)

    # Read the raster data as a numpy array
    grid_basins = band_input.ReadAsArray()
    # truncate to byte integer
    grid_basins = grid_basins.astype(np.uint8)

    # get the cell sizes
    raster_geotransform = raster_input.GetGeoTransform()
    cellsize = raster_geotransform[1]

    # -- Close the raster
    raster_input = None

    # -------------------------------------------------------------------------
    # PROCESS
    basin_areas = []
    for i in ids_basins:
        grid_basin = 1 * (grid_basins == i)
        area_sqkm = cellsize * cellsize * np.sum(grid_basin) / (1000 * 1000)
        basin_areas.append(area_sqkm)

    # -------------------------------------------------------------------------
    # RETURN
    return {"Id": ids_basins, "UpstreamArea": basin_areas}


def get_blank(file_input, file_output, blank_value=0, dtype="byte"):
    """
    Get a blank raster copy from other raster

    :param file_input: path to inputs raster file
    :type file_input: str
    :param file_output: path to output raster file
    :type file_output: str
    :param blank_value: value for constant blank raster
    :type blank_value: int
    :param dtype: output raster data type ("byte", "int" -- else defaults to float)
    :type dtype: str
    :return: file path of output (echo)
    :rtype: str

    # todo [script example]
    """

    # -------------------------------------------------------------------------
    # LOAD
    dc_raster = qgdal.read_raster(file_input=file_input)
    grid_input = dc_raster["data"]

    # -------------------------------------------------------------------------
    # PROCESS
    # get ones to byte integer
    grid_ones = np.ones(shape=grid_input.shape, dtype=np.uint8)
    grid_output = grid_ones * blank_value

    # -------------------------------------------------------------------------
    # EXPORT RASTER FILE
    # Get the driver to create the new raster
    # overwrite no data
    if dtype in DC_NODATA:
        dc_raster["metadata"]["NODATA_value"] = DC_NODATA[dtype]
    qgdal.write_raster(
        grid_output=grid_output,
        dc_metadata=dc_raster["metadata"],
        file_output=file_output,
        dtype=dtype,
    )

    return file_output


def get_boolean(file_input, file_output, bool_value, condition="ET"):
    """
    Generates a boolean raster based on a condition applied to an input raster.
    This function reads a raster, applies a user-defined condition (greater than, less than, or equal to)
    with a specified value, and creates a new raster where cells meeting the
    condition are set to 1 and all others are set to 0. The output is saved as a byte integer raster file.

    :param file_input: The file path to the input raster.
    :type file_input: str
    :param file_output: The file path where the output boolean raster will be saved.
    :type file_output: str
    :param bool_value: The value against which to apply the condition.
    :type bool_value: int or float
    :param condition: The condition to apply ("GT" for greater than, "LT" for less than, "ET" for equal to). Default value = "ET"
    :type condition: str
    :return: The file path of the created output raster.
    :rtype: str
    """
    # -------------------------------------------------------------------------
    # LOAD
    dc_raster = qgdal.read_raster(file_input=file_input)
    grid_input = dc_raster["data"]

    # -------------------------------------------------------------------------
    # PROCESS
    # get ones to byte integer
    if condition == "GT":
        grid_output = 1 * (grid_input > bool_value)
    elif condition == "LT":
        grid_output = 1 * (grid_input < bool_value)
    else:
        grid_output = 1 * (grid_input == bool_value)

    grid_output = grid_output.astype("byte")

    # -------------------------------------------------------------------------
    # EXPORT RASTER FILE
    # Get the driver to create the new raster
    # overwrite no data
    dc_raster["metadata"]["NODATA_value"] = DC_NODATA["byte"]
    qgdal.write_raster(
        grid_output=grid_output,
        dc_metadata=dc_raster["metadata"],
        file_output=file_output,
        dtype="byte",
    )
    return file_output


def get_fuzzy(file_input, file_output, low_bound, high_bound):
    """
    Get the Fuzzy map of a linear membership. Reverse bounds to reverse membership.

    :param file_input: path to raster file input
    :type file_input: str
    :param file_output: path to raster file output
    :type file_output: str
    :param low_bound: value of low bound
    :type low_bound: float
    :param high_bound: value of high bound
    :type high_bound: float
    :return: path of output (echo)
    :rtype: str

    # todo [script example]

    """
    processing.run(
        "native:fuzzifyrasterlinearmembership",
        {
            "INPUT": file_input,
            "BAND": 1,
            "FUZZYLOWBOUND": low_bound,
            "FUZZYHIGHBOUND": high_bound,
            "OUTPUT": file_output,
        },
    )
    return file_output


def get_dem(
    file_src_dem,
    file_output,
    target_crs,
    target_extent,
    target_cellsize=30,
    source_crs="4326",
):
    """
    Get a reprojected DEM raster from a larger DEM dataset

    :param file_src_dem: file path to sourced (larger) DEM dataset raster
    :type file_src_dem: str
    :param file_output: file path to output raster
    :type file_output: str
    :param target_crs: EPSG code (number only) for the target CRS
    :type target_crs: str
    :param target_extent: dictionary of bouding box: xmin, xmax, ymin, ymax
    :type target_extent: dict
    :param target_cellsize: target resolution of cellsize in map units (degrees or meters)
    :type target_cellsize: float
    :param source_crs: EPSG code (number only) for the source CRS. default is 4326 (WGS-84)
    :type source_crs: str
    :return: file path of output (echo)
    :rtype: str

    # todo [script example]

    """
    # get extent string
    target_extent_str = "{},{},{},{} [{}:{}]".format(
        target_extent["xmin"],
        target_extent["xmax"],
        target_extent["ymin"],
        target_extent["ymax"],
        DC_PROVIDERS[target_crs],
        target_crs,
    )
    # run warp
    processing.run(
        "gdal:warpreproject",
        {
            "INPUT": file_src_dem,
            "SOURCE_CRS": QgsCoordinateReferenceSystem(
                "{}:{}".format(DC_PROVIDERS[source_crs], source_crs)
            ),
            "TARGET_CRS": QgsCoordinateReferenceSystem(
                "{}:{}".format(DC_PROVIDERS[target_crs], target_crs)
            ),
            "RESAMPLING": 1,  # average=5; nearest=0, bilinear=1
            "NODATA": -1,
            "TARGET_RESOLUTION": target_cellsize,  # in meters
            "OPTIONS": "",
            "DATA_TYPE": 6,  # float32=6, byte=1
            "TARGET_EXTENT": target_extent_str,
            "TARGET_EXTENT_CRS": QgsCoordinateReferenceSystem(
                "{}:{}".format(DC_PROVIDERS[target_crs], target_crs)
            ),
            "MULTITHREADING": False,
            "EXTRA": "",
            "OUTPUT": file_output,
        },
    )
    return file_output


def get_downstream_ids(file_ldd, file_basins, file_outlets):
    """
    Get the basin Ids from downstream cells.

    ldd - Direction convention:

    .. code-block:: text

        7   8   9
        4   5   6
        1   2   3


    :param file_ldd: file path to LDD raster (map of LDD direction convention)
    :type file_ldd: str
    :param file_basins: file path to basins raster
    :type file_basins: str
    :param file_outlets: file path to outlets raster
    :type file_outlets: str
    :return: dictionaty with lists of "Id" and "Downstream_Id"
    :rtype: dict

    # todo [script example]

    """
    # todo [optimize] using qgdal
    # -------------------------------------------------------------------------
    # LOAD LDD

    # Open the raster file using gdal
    raster_input = gdal.Open(file_ldd)

    # Get the raster band
    band_input = raster_input.GetRasterBand(1)

    # Read the raster data as a numpy array
    grid_ldd = band_input.ReadAsArray()
    # truncate to byte integer
    grid_ldd = grid_ldd.astype(np.uint8)

    # -- Close the raster
    raster_input = None

    # -------------------------------------------------------------------------
    # LOAD OUTLETS

    # Open the raster file using gdal
    raster_input = gdal.Open(file_outlets)

    # Get the raster band
    band_input = raster_input.GetRasterBand(1)

    # Read the raster data as a numpy array
    grid_outlets = band_input.ReadAsArray()
    # truncate to byte integer
    grid_outlets = grid_outlets.astype(np.uint8)

    # -- Close the raster
    raster_input = None

    # -------------------------------------------------------------------------
    # LOAD BASINS

    # Open the raster file using gdal
    raster_input = gdal.Open(file_basins)

    # Get the raster band
    band_input = raster_input.GetRasterBand(1)

    # Read the raster data as a numpy array
    grid_basins = band_input.ReadAsArray()
    # truncate to byte integer
    grid_basins = grid_basins.astype(np.uint8)

    # -- Close the raster
    raster_input = None

    # -------------------------------------------------------------------------
    # PROCESS

    # Get the indices of non-zero elements
    nonzero_indices = np.nonzero(grid_outlets)
    # Create a list of tuples containing row and column indices
    list_positions = list(zip(nonzero_indices[0], nonzero_indices[1]))

    list_ids = list()
    list_ds_ids = list()
    for outlet in list_positions:
        i = outlet[0]
        j = outlet[1]
        # get the ID
        n_id = grid_outlets[i][j]
        # get the direction code (LDD)
        n_dir = grid_ldd[i][j]
        # get downstream coordinates
        dict_dc = geo.downstream_coordinates(n_dir=n_dir, i=i, j=j, s_convention="ldd")
        new_i = dict_dc["i"]
        new_j = dict_dc["j"]
        n_ds_id = grid_basins[new_i][new_j]
        list_ids.append(n_id)
        list_ds_ids.append(n_ds_id)

    return {"Id": list_ids, "Downstream_Id": list_ds_ids}


def get_carved_dem(file_dem, file_rivers, file_output, wedge_width=3, wedge_depth=10):
    """
    Apply a carving method to DEM raster

    :param file_dem: file path to DEM raster
    :type file_dem: str
    :param file_rivers: file path to main rivers pseudo-boolean raster
    :type file_rivers: str
    :param file_output: file path to output raster
    :type file_output: str
    :param wedge_width: width parameter in unit cells (pixels)
    :type wedge_width: int
    :param wedge_depth: depth parameter in dem units (e.g., meters)
    :type wedge_depth: float
    :return: file path of output (echo)
    :rtype: str

    # todo [script example]

    """
    # -------------------------------------------------------------------------
    # LOAD DEM
    dc_raster = qgdal.read_raster(file_input=file_dem)
    grd_dem = dc_raster["data"]

    # -------------------------------------------------------------------------
    # LOAD RIVERs
    dc_raster2 = qgdal.read_raster(file_input=file_rivers)
    grd_rivers = dc_raster2["data"]
    # truncate to byte integer
    grd_rivers = grd_rivers.astype(np.uint8)

    # -------------------------------------------------------------------------
    # PROCESS
    grid_output = geo.carve_dem(
        grd_dem=grd_dem,
        grd_rivers=grd_rivers,
        wedge_width=wedge_width,
        wedge_depth=wedge_depth,
    )

    # -------------------------------------------------------------------------
    # EXPORT RASTER FILE
    # Get the driver to create the new raster
    # overwrite no data
    dc_raster["metadata"]["NODATA_value"] = DC_NODATA["float32"]
    qgdal.write_raster(
        grid_output=grid_output,
        dc_metadata=dc_raster["metadata"],
        file_output=file_output,
        dtype="float32",
    )
    return file_output


def get_shalstab(
    file_slope,
    file_flowacc,
    output_folder,
    suffix,
    cellsize=30,
    soil_phi=15,
    soil_z=1,
    soil_p=1600,
    soil_c=1,
    water_p=997,
):
    # todo [docstring]
    # todo [optimize]
    # -------------------------------------------------------------------------
    # LOAD SLOPE

    # Open the raster file using gdal
    raster_slope = gdal.Open(file_slope)

    # Get the raster band
    band_slope = raster_slope.GetRasterBand(1)

    # Read the raster data as a numpy array
    grd_slope = band_slope.ReadAsArray()

    # -- Collect useful metadata

    raster_x_size = raster_slope.RasterXSize
    raster_y_size = raster_slope.RasterYSize
    raster_projection = raster_slope.GetProjection()
    raster_geotransform = raster_slope.GetGeoTransform()
    cellsize = raster_geotransform[1]
    # -- Close the raster
    raster_slope = None

    # -------------------------------------------------------------------------
    # LOAD Flowacc

    # Open the raster file using gdal
    raster_flowacc = gdal.Open(file_flowacc)

    # Get the raster band
    band_flowacc = raster_flowacc.GetRasterBand(1)

    # Read the raster data as a numpy array
    grd_flowacc = band_flowacc.ReadAsArray()

    # -- Close the raster
    raster_flowacc = None

    # -------------------------------------------------------------------------
    # PROCESS
    w1, w2 = geo.shalstab_wetness(
        flowacc=grd_flowacc,
        slope=grd_slope,
        cellsize=cellsize,
        soil_phi=soil_phi,
        soil_z=soil_z,
        soil_p=soil_p,
        soil_c=soil_c,
        water_p=water_p,
        kPa=True,
    )

    # -------------------------------------------------------------------------
    # EXPORT RASTER FILE
    # Get the driver to create the new raster
    driver = gdal.GetDriverByName("GTiff")

    # Create a new raster with the same dimensions as the original
    file_output1 = f"{output_folder}/{suffix}_qt.tif"
    raster_output1 = driver.Create(
        file_output1, raster_x_size, raster_y_size, 1, gdal.GDT_Float32
    )

    # Set the projection and geotransform of the new raster to match the original
    raster_output1.SetProjection(raster_projection)
    raster_output1.SetGeoTransform(raster_geotransform)

    # Write the new data to the new raster
    raster_output1.GetRasterBand(1).WriteArray(w1)

    # Create a new raster with the same dimensions as the original
    file_output2 = f"{output_folder}/{suffix}_cls.tif"
    raster_output2 = driver.Create(
        file_output2, raster_x_size, raster_y_size, 1, gdal.GDT_Byte
    )

    # Set the projection and geotransform of the new raster to match the original
    raster_output2.SetProjection(raster_projection)
    raster_output2.SetGeoTransform(raster_geotransform)

    # Write the new data to the new raster
    raster_output2.GetRasterBand(1).WriteArray(w2)

    # Close
    raster_output1 = None
    raster_output2 = None
    return file_output1, file_output2


def get_tps(
    file_tpi, file_upa, file_output, upa_min=0.01, upa_max=2, tpi_v=-2, tpi_r=10
):
    """
    Get the drainage boolean mask using TPS method

    :param file_tpi: path to tpi raster file
    :type file_tpi: str
    :param file_upa: path to upa raster file
    :type file_upa: str
    :param file_output: path to output raster file
    :type file_output: str
    :param tpi_v: TPI threshold for valley definition
    :type tpi_v: float
    :param upa_min: Upslope area for exclusion zone, in sqkm (0.01 = 1 ha)
    :type upa_min: float
    :param upa_max: Upslope area for inclusion zone, in sqkm (0.01 = 1 ha)
    :type upa_max: float
    :return: file path of output (echo)
    :rtype: str
    """
    # -------------------------------------------------------------------------
    # LOAD TPI
    dc_raster = qgdal.read_raster(file_input=file_tpi, metadata=True)
    grid_tpi = dc_raster["data"]

    # -------------------------------------------------------------------------
    # LOAD UPA
    dc_raster2 = qgdal.read_raster(file_input=file_upa, metadata=False)
    grid_upa = dc_raster2["data"]

    # -------------------------------------------------------------------------
    # PROCESS
    # convert to m2
    upa_min_m2 = upa_min * 1000 * 1000
    upa_max_m2 = upa_max * 1000 * 1000

    grid_valleys = 1.0 * (grid_tpi <= tpi_v)
    grid_valleys_2 = geo.buffer(grd_input=grid_valleys, n_radius=tpi_r)
    grid_large = 1.0 * (grid_upa >= upa_max_m2)
    grid_headwaters = 1 * (grid_upa < upa_max_m2) * (grid_upa >= upa_min_m2)
    grid_headwaters_valleys = grid_headwaters * grid_valleys_2
    grid_output = grid_headwaters_valleys + grid_large

    # -------------------------------------------------------------------------
    # EXPORT RASTER FILE
    # Get the driver to create the new raster
    dc_raster["metadata"]["NODATA_value"] = DC_NODATA["byte"]
    qgdal.write_raster(
        grid_output=grid_output,
        dc_metadata=dc_raster["metadata"],
        file_output=file_output,
        dtype="byte",
    )
    return file_output


def get_twi(file_slope, file_upa, file_output):
    """
    Get the TWI map from Slope and Upslope Area

    :param file_slope: file path to Slope raster map
    :type file_slope: str
    :param file_upa: file path to Upslope Area raster map
    :type file_upa: str
    :param file_output: file path to output raster
    :type file_output: str
    :return: file path of output (echo)
    :rtype: str

    """
    # -------------------------------------------------------------------------
    # LOAD SLOPE
    dc_raster = qgdal.read_raster(file_input=file_slope)
    grd_slope = dc_raster["data"]

    # -------------------------------------------------------------------------
    # LOAD UPA
    dc_raster2 = qgdal.read_raster(file_input=file_upa, metadata=False)
    grd_upa = dc_raster2["data"]

    # -------------------------------------------------------------------------
    # PROCESS
    cellsize = dc_raster["metadata"]["cellsize"]
    grid_output = geo.twi(slope=grd_slope, flowacc=grd_upa, cellsize=cellsize)

    # -------------------------------------------------------------------------
    # EXPORT RASTER FILE
    # Get the driver to create the new raster
    dc_raster["metadata"]["NODATA_value"] = DC_NODATA["float32"]
    qgdal.write_raster(
        grid_output=grid_output,
        dc_metadata=dc_raster["metadata"],
        file_output=file_output,
        dtype="float32",
    )
    return file_output


def get_dto(file_ldd, file_output):
    # todo [docstring]
    # -------------------------------------------------------------------------
    # LOAD LDD
    dc_raster = qgdal.read_raster(file_input=file_ldd)
    grd_ldd = dc_raster["data"]

    # -------------------------------------------------------------------------
    # PROCESS
    cellsize = dc_raster["metadata"]["cellsize"]
    grid_output = geo.distance_to_outlet(
        grd_ldd=grd_ldd, n_res=cellsize, s_convention="ldd"
    )

    # -------------------------------------------------------------------------
    # EXPORT RASTER FILE
    # Get the driver to create the new raster
    dc_raster["metadata"]["NODATA_value"] = DC_NODATA["float32"]
    qgdal.write_raster(
        grid_output=grid_output,
        dc_metadata=dc_raster["metadata"],
        file_output=file_output,
        dtype="float32",
    )
    return file_output


def get_path_areas(file_dto, dc_basins, file_output, n_bins=100):
    # todo [docstring]
    # -------------------------------------------------------------------------
    # LOAD DTO
    dc_raster = Raster.read_tif(
        file_input=file_dto,
    )
    grd_dto = dc_raster["data"]
    n_cell_size = dc_raster["metadata"]["cellsize"]
    # todo [DEV] -- develop feature for handling parameterized units
    n_cell_area = n_cell_size * n_cell_size / (100 * 100)  # ha units
    n_max = round(np.nanmax(grd_dto), 1) + 1.0
    vct_bins = np.linspace(start=0.0, stop=n_max, num=n_bins)
    dc_output = {
        "path (m)": vct_bins[1:],
    }
    for basin_code in dc_basins:
        # -------------------------------------------------------------------------
        # LOAD BASIN
        file_basin = dc_basins[basin_code]
        dc_raster2 = Raster.read_tif(file_input=file_basin, dtype="byte")
        grd_basin = dc_raster2["data"]
        # -------------------------------------------------------------------------
        # PROCESS
        grd_output = grd_dto * grd_basin
        # remove zeros
        grd_output = np.where(grd_output == 0, np.nan, grd_output)
        # get minimal distance
        n_min_dist = np.nanmin(grd_output)
        # correction of distance
        grd_output = grd_output - n_min_dist
        #
        vct_output = grd_output.ravel()[~np.isnan(grd_output.ravel())]
        counts, edges = np.histogram(a=vct_output, bins=vct_bins, density=False)
        vct_areas = n_cell_area * counts
        dc_output[f"basin_{basin_code} (ha)"] = vct_areas[:]

    df = pd.DataFrame(dc_output)
    df.to_csv(file_output, sep=";", index=False)
    return file_output


def get_htwi(file_ftwi, file_fhand, file_output, hand_w):
    """
    Get the HAND-enhanced TWI map from HAND, TWI and HAND weight

    :param file_ftwi: path to TWI raster (expected to be fuzzified)
    :type file_ftwi: str
    :param file_fhand: path to HAND raster (expected to be fuzzified)
    :type file_fhand: str
    :param file_output: path to output raster
    :type file_output: str
    :param hand_w: weight of HAND from 0 to 100
    :type hand_w: int
    :return: file path of output (echo)
    :rtype: str

    # todo [script example]

    """
    # -------------------------------------------------------------------------
    # LOAD F-TWI
    dc_raster = qgdal.read_raster(file_input=file_ftwi, metadata=True)
    grd_ftwi = dc_raster["data"]

    # -------------------------------------------------------------------------
    # LOAD F-HAND
    dc_raster2 = qgdal.read_raster(file_input=file_fhand, metadata=False)
    grd_fhand = dc_raster2["data"]

    # -------------------------------------------------------------------------
    # PROCESS
    # compute twi weight
    twi_w = 100 - hand_w
    # compute the weighted mean
    grid_output = ((hand_w * grd_fhand) + (twi_w * grd_ftwi)) / (hand_w + twi_w)

    # -------------------------------------------------------------------------
    # EXPORT RASTER FILE
    # Get the driver to create the new raster
    dc_raster["metadata"]["NODATA_value"] = DC_NODATA["float32"]
    qgdal.write_raster(
        grid_output=grid_output,
        dc_metadata=dc_raster["metadata"],
        file_output=file_output,
        dtype="float32",
    )
    return file_output


def get_htwi_list(file_ftwi, file_fhand, folder_output, ls_weights=[0, 50, 100]):
    """
    Get a list of HTWI based on many weights

    :param file_ftwi: path to TWI raster (expected to be fuzzified)
    :type file_ftwi: str
    :param file_fhand: path to HAND raster (expected to be fuzzified)
    :type file_fhand: str
    :param folder_output: path to output folder
    :type folder_output:
    :param ls_weights: list of weights to use for each raster
    :type ls_weights: list
    :return: None
    :rtype: None

    # todo [script example]

    """
    for w in ls_weights:
        s_w = str(w).zfill(3)
        print("[gdal] get HTWI for w = {}".format(s_w))
        get_htwi(
            file_ftwi=file_ftwi,
            file_fhand=file_fhand,
            file_output=f"{folder_output}/htwi_{s_w}.tif",
            hand_w=w,
        )
    return None


# -------------------------------------------------------------------------------------
# PROJECT-BASED ROUTINES
# This routines expect a pre-set folder structure


def get_hand(
    folder_project,
    file_dem_filled,
    file_dem_sample=None,
    file_drainage=None,
    hand_min_upa=0.01,
):
    """
    Get the HAND raster map from a DEM.
    The DEM must be hydrologically consistent (no sinks).
    PLANS-based folder structure is expected

    :param folder_project: path to output folder
    :type folder_project: str
    :param file_dem_filled: file path to filled DEM (no sinks)
    :type file_dem_filled: str
    :param file_dem_sample: file path to original DEM for sampling HAND
    :type file_dem_sample: str
    :param file_drainage: [optional] file path to drainage boolean map
    :type file_drainage: str
    :param hand_min_upa: minimal upslope area threshhold for HAND in sq km (0.01 sqkm = 1ha)
    :type hand_min_upa: float
    :return: dictionary with raster output paths. keys:
        "ldd", "material", "accflux", "threshold", "drainage", "hs_outlets_scalar",
        "hs_outlets_nominal", "hillslopes", "hs_zmin", "hand"

    :rtype: dict

    # todo [script example]

    """
    # expected folders
    folder_topo = f"{folder_project}/inputs/topo"
    folder_aux = f"{folder_project}/inputs/topo/_aux"

    # -- PCRaster - get LDD map
    file_ldd = "{}/ldd.map".format(folder_aux)
    print("[pc-raster] get LDD...")
    processing.run(
        "pcraster:lddcreate",
        {
            "INPUT": file_dem_filled,
            "INPUT0": 0,
            "INPUT1": 0,
            "INPUT2": 9999999,
            "INPUT4": 9999999,
            "INPUT3": 9999999,
            "INPUT5": 9999999,
            "OUTPUT": file_ldd,
        },
    )

    if file_drainage is None:
        # -- PCRaster - create material layer with cell x cell (area)
        cellsize = qgdal.get_cellsize(file_input=file_dem_filled)
        print("[pc-raster] get material (constant)...")
        file_material = "{}/material.map".format(folder_aux)
        processing.run(
            "pcraster:spatial",
            {
                "INPUT": cellsize * cellsize,
                "INPUT1": 3,
                "INPUT2": file_dem_filled,
                "OUTPUT": file_material,
            },
        )
        # -- PCRaster - accumulate flux
        print("[pc-raster] get upa...")
        file_accflux = "{}/upa.map".format(folder_aux)
        processing.run(
            "pcraster:accuflux",
            {
                "INPUT": file_ldd,
                "INPUT2": file_material,
                "OUTPUT": file_accflux,
            },
        )
        # -- PCRaster - create drainage threshold layer with
        print("[pc-raster] get threshold (constant)...")
        file_threshold = "{}/threshold.map".format(folder_aux)
        processing.run(
            "pcraster:spatial",
            {
                "INPUT": int(hand_min_upa * 1000 * 1000),  # convert to m2
                "INPUT1": 3,
                "INPUT2": file_dem_filled,
                "OUTPUT": file_threshold,
            },
        )
        # -- PCRaster - create drainage boolean
        print("[pc-raster] get drainage...")
        file_drainage = "{}/drainage.map".format(folder_aux)
        processing.run(
            "pcraster:comparisonoperators",
            {
                "INPUT": file_accflux,
                "INPUT1": 1,
                "INPUT2": file_threshold,
                "OUTPUT": file_drainage,
            },
        )

    # -- PCRaster - create unique ids Map
    print("[pc-raster] get outlets scalar...")
    file_outlets_1 = "{}/hsl_outlets_scalar.map".format(folder_aux)
    processing.run(
        "pcraster:uniqueid",
        {"INPUT": file_drainage, "OUTPUT": file_outlets_1},
    )

    # -- PCRaster - convert unique ids to nominal
    print("[pc-raster] get outlets nominal...")
    file_outlets_2 = "{}/hsl_outlets_nominal.map".format(folder_aux)
    processing.run(
        "pcraster:convertdatatype",
        {
            "INPUT": file_outlets_1,
            "INPUT1": 1,
            "OUTPUT": file_outlets_2,
        },
    )
    # -- PCRaster - create subcatchments
    print("[pc-raster] get hillslopes...")
    file_hillslopes = "{}/hillslopes.map".format(folder_aux)
    processing.run(
        "pcraster:subcatchment",
        {
            "INPUT1": file_ldd,
            "INPUT2": file_outlets_2,
            "OUTPUT": file_hillslopes,
        },
    )

    # -- PCRaster - sample z min by catchment
    print("[pc-raster] get zmin...")
    file_zmin = "{}/hs_zmin.map".format(folder_aux)
    if file_dem_sample is None:
        file_dem_sample = file_dem_filled
    processing.run(
        "pcraster:areaminimum",
        {
            "INPUT": file_hillslopes,
            "INPUT2": file_dem_sample,
            "OUTPUT": file_zmin,
        },
    )

    # -- GDAL- compute HAND
    print("[pc-raster] get hand...")
    file_hand = "{}/hnd.tif".format(folder_topo)
    processing.run(
        "gdal:rastercalculator",
        {
            "INPUT_A": file_dem_sample,
            "BAND_A": 1,
            "INPUT_B": file_zmin,
            "BAND_B": 1,
            "INPUT_C": None,
            "BAND_C": None,
            "INPUT_D": None,
            "BAND_D": None,
            "INPUT_E": None,
            "BAND_E": None,
            "INPUT_F": None,
            "BAND_F": None,
            "FORMULA": "A - B",
            "NO_DATA": None,
            "PROJWIN": None,
            "RTYPE": 5,  # float32
            "OPTIONS": "",
            "EXTRA": "",
            "OUTPUT": file_hand,
        },
    )
    d_files = {}
    d_files["hand"] = file_hand
    d_files["ldd"] = file_ldd
    return d_files


def setup_topo(
    folder_project,
    file_src_dem,
    crs_target,
    db_aoi,
    layer_aoi,
    db_rivers,
    layer_river_lines,
    layer_river_polygons=None,
    crs_source="4326",
    target_cellsize=30,
    translate_to_ascii=False,
):
    """
    Setup protocols for getting ``topo`` datasets.
    PLANS-based folder structure is expected

    :param folder_project: path to main plans project folder
    :type folder_project: str
    :param file_src_dem: file path to larger source DEM raster -- expected to be in WGS-84 (4326)
    :type file_src_dem: str
    :param crs_target: QGIS code (number only) for the target CRS
    :type crs_target: str
    :param db_aoi: path to AOI layer geopackage database
    :type db_aoi: str
    :param layer_aoi: name of Area Of Interest layer (polygon).
    :type layer_aoi: str
    :param db_rivers: path to rivers layer geopackage database
    :type db_rivers: str
    :param layer_river_lines: name of main rivers lines layer.
    :type layer_river_lines: str
    :param layer_river_polygons: name of main rivers polygon layer (optional).
    :type layer_river_polygons: str
    :param crs_source: QGIS code (number only) for the source CRS. default is WGS-84 (4326)
    :type crs_source: str
    :param translate_to_ascii: flag to convert to asc format
    :type translate_to_ascii: bool
    :return: dictionary of output resources
    :rtype: dict

    Script example (for QGIS Python Console):

    .. code-block:: python

        # plans source code must be pasted to QGIS plugins directory
        from plans import qutils

        # call function
        qutils.setup_topo(
            folder_project="/path/to/folder",
            file_src_dem="/path/to/src_dem.tif",
            crs_target="5641",
            db_aoi="/path/to/aoi_database.gpkg",
            layer_aoi="layer",
            db_rivers="/path/to/river_database.gpkg",
            layer_river_lines="river_lines",
            layer_river_polygons="river_pols",
            crs_source="4326",
        )

    """
    # folders are expected to exist
    # inputs
    folder_input = f"{folder_project}/inputs"
    # topo
    folder_topo = f"{folder_project}/inputs/topo"
    # intermediate
    output_folder_interm = "{}/_aux".format(folder_topo)

    # project vector db
    db_project = f"{folder_input}/vectors.gpkg"

    # reproject aoi to project database
    print("reproject aoi layer...")
    new_layer_aoi = reproject_layer(
        db_input=db_aoi,
        layer_name=layer_aoi,
        crs_target=crs_target,
        db_output=db_project,
        layer_output="aoi",
    )
    # reproject rivers to project database
    print("clip river lines layer...")
    clipped_layer_rivers = clip_layer(
        db_input=db_rivers,
        layer_input=layer_river_lines,
        db_overlay=db_aoi,
        layer_overlay=layer_aoi,
        db_output=db_project,
        layer_output="rivers_src",
    )
    print("reproject river lines layer...")
    # save to same database
    new_layer_rivers = reproject_layer(
        db_input=db_project,
        layer_name=clipped_layer_rivers,
        crs_target=crs_target,
        db_output=db_project,
        layer_output="rivers",
    )

    if layer_river_polygons is not None:
        # reproject rivers to project database
        print("clip rivers polygons layer...")
        clipped_layer_rivers2 = clip_layer(
            db_input=db_rivers,
            layer_input=layer_river_polygons,
            db_overlay=db_aoi,
            layer_overlay=layer_aoi,
            db_output=db_project,
            layer_output="rivers_src_polygons",
        )
        print("reproject river lines layer...")
        # save to same database
        new_layer_rivers_polygons = reproject_layer(
            db_input=db_project,
            layer_name=clipped_layer_rivers2,
            crs_target=crs_target,
            db_output=db_project,
            layer_output="rivers_polygons",
        )

    # get aoi extent
    print("get aoi extent...")
    dict_bbox = get_extent_from_vector(db_input=db_project, layer_name=new_layer_aoi)

    # clip and warp dem
    print(r"[gdal] clip-n-warp dem...")
    file_dem = get_dem(
        file_src_dem=file_src_dem,
        target_crs=crs_target,
        target_extent=dict_bbox,
        file_output=f"{folder_topo}/dem.tif",
        source_crs=crs_source,
        target_cellsize=target_cellsize,
    )

    if translate_to_ascii:
        print("translate...")
        processing.run(
            "gdal:translate",
            {
                "INPUT": file_dem,
                "TARGET_CRS": QgsCoordinateReferenceSystem(
                    "{}:{}".format(DC_PROVIDERS[crs_target], crs_target)
                ),
                "NODATA": -9999,
                "COPY_SUBDATASETS": False,
                "OPTIONS": "",
                "EXTRA": "",
                "DATA_TYPE": 6,
                "OUTPUT": "{}/dem.asc".format(folder_topo),
            },
        )
    return {
        "db": db_project,
        "aoi": new_layer_aoi,
        "rivers": new_layer_rivers,
        "file_dem": file_dem,
    }


def get_topo(
    folder_project,
    file_dem,
    db_rivers,
    layer_rivers,
    wedge_width=3,
    wedge_depth=10,
    hand_threshold=5,
    use_saga=False,
    fill_xxl=False,
    translate_to_ascii=False,
    style_folder=None,
):
    """
    Get all ``topo`` datasets for running PLANS.
    PLANS-based folder structure is expected.

    .. warning::

        run ``setup_topo()`` first.

    :param folder_project: path to project folder
    :type folder_project: str
    :param file_dem: file path to larger DEM dataset raster -- expected to be in WGS-84
    :type file_dem: str
    :param db_rivers: path to geopackage database
    :type db_rivers: str
    :param layer_rivers: name of main rivers layers (lines) in target CRS.
    :type layer_rivers: str
    :param wedge_width: carving dem parameter -- width parameter in unit cells
    :type wedge_width: int
    :param wedge_depth: carving dem parameter -- depth parameter in dem units (e.g., meters)
    :type wedge_depth: float
    :param hand_threshold: [hand parameter in sqkm] threshhold for HAND in number of maximum hillslope area
    :type hand_threshold: int
    :param translate_to_ascii: flag to convert to asc format
    :type translate_to_ascii: bool
    :param style_folder: path to folder containing style files
    :type style_folder: str
    :return: None
    :rtype: None

    Script example (for QGIS Python Console):

    .. code-block:: python

        # plans source code must be pasted to QGIS plugins directory
        from plans import qutils

        # call function
        qutils.get_topo(
            folder_project="/path/to/folder", # change paths!
            file_dem="/path/to/dem.tif",
            db_rivers="/path/to/database.gpkg",
            layer_rivers='rivers',
            wedge_width=3,
            wedge_depth=10,
            hand_threshold=5,
            translate_to_ascii=False,
        )

    """

    # ----- SETUP -----
    # folder are expected to exist
    folder_topo = "{}/inputs/topo".format(folder_project)
    folder_aux = "{}/inputs/topo/_aux".format(folder_project)

    dict_files = {
        "dem": file_dem,
        "main_rivers": "{}/main_rivers.tif".format(folder_aux),
        "dem_b": "{}/dem-carved.tif".format(folder_aux),
        "slope": "{}/slp.tif".format(folder_topo),
        "tpi": "{}/tpi.tif".format(folder_topo),
        "hsd": "{}/hsd.tif".format(folder_topo),
        "fill_saga": "{}/dem-filled.sdat".format(folder_aux),
        "fac_mfd_saga": "{}/fac_mfd.sdat".format(folder_aux),
        "fac": "{}/fac.tif".format(folder_topo),
        "upa": "{}/upa.tif".format(folder_topo),
        "tps": "{}/tps.tif".format(folder_topo),
        "twi": "{}/twi.tif".format(folder_topo),
        "dto": "{}/dto.tif".format(folder_topo),
        "ftwi": "{}/ftwi.tif".format(folder_topo),
        "ldd": "{}/ldd.tif".format(folder_topo),
        "hand": "{}/hnd.tif".format(folder_topo),
        "fhand": "{}/fhnd.tif".format(folder_topo),
        "dem_bf": "{}/dem-filled.tif".format(folder_aux),
        # "dem_bfb": "{}/dem_bfb.tif".format(output_folder_interm),
        "dem_pc": "{}/dem.map".format(folder_aux),
        "tps_pc": "{}/drainage.map".format(folder_aux),
        "dem_bf_pc": "{}/dem_bf.map".format(folder_aux),
    }

    # get cellsize
    cellsize = qgdal.get_cellsize(file_input=dict_files["dem"])

    # 4) get rivers blank
    print("get main rivers...")
    file_rivers = get_blank(
        file_input=file_dem, file_output=dict_files["main_rivers"], blank_value=0
    )

    # rasterize rivers
    print("[gdal] rasterize rivers...")
    processing.run(
        "gdal:rasterize_over_fixed_value",
        {
            "INPUT": "{}|layername={}".format(db_rivers, layer_rivers),
            "INPUT_RASTER": dict_files["main_rivers"],
            "BURN": 1,
            "ADD": False,
            "EXTRA": "",
        },
    )

    # get carved
    print("[gdal] carve dem...")
    file_burn = get_carved_dem(
        file_dem=dict_files["dem"],
        file_rivers=dict_files["main_rivers"],
        file_output=dict_files["dem_b"],
        wedge_width=wedge_width,
        wedge_depth=wedge_depth,
    )

    # get slope
    print("[gdal] get slope...")
    # use gdal
    processing.run(
        "gdal:slope",
        {
            "INPUT": dict_files["dem"],
            "BAND": 1,
            "SCALE": 1,
            "AS_PERCENT": False,
            "COMPUTE_EDGES": True,
            "ZEVENBERGEN": False,
            "OPTIONS": "",
            "EXTRA": "",
            "OUTPUT": dict_files["slope"],
        },
    )

    print("[gdal] get tpi")
    processing.run(
        "gdal:tpitopographicpositionindex",
        {
            "INPUT": dict_files["dem"],
            "BAND": 1,
            "COMPUTE_EDGES": True,
            "OPTIONS": "",
            "OUTPUT": dict_files["tpi"],
        },
    )

    print("[gdal] get hillshade...")
    processing.run(
        "gdal:hillshade",
        {
            "INPUT": dict_files["dem"],
            "BAND": 1,
            "Z_FACTOR": 2,
            "SCALE": 1,
            "AZIMUTH": 315,
            "ALTITUDE": 45,
            "COMPUTE_EDGES": True,
            "ZEVENBERGEN": False,
            "COMBINED": False,
            "MULTIDIRECTIONAL": False,
            "OPTIONS": "",
            "EXTRA": "",
            "OUTPUT": dict_files["hsd"],
        },
    )

    # SAGA processes
    if use_saga:
        # fill sinks
        if fill_xxl:
            print("[saga] fill sinks XXL...")
            processing.run(
                "sagang:fillsinksxxlwangliu",
                {
                    "ELEV": dict_files["dem_b"],
                    "FILLED": dict_files["fill_saga"],
                    "MINSLOPE": 0.01,
                },
            )
        else:
            print("[saga] fill sinks ...")
            processing.run(
                "sagang:fillsinksplanchondarboux2001",
                {
                    "DEM": dict_files["dem_b"],
                    "RESULT": dict_files["fill_saga"],
                    "MINSLOPE": 0.01,
                },
            )
        print("[saga] translate fill...")
        processing.run(
            "gdal:translate",
            {
                "INPUT": dict_files["fill_saga"],
                "TARGET_CRS": QgsCoordinateReferenceSystem(
                    "{}:{}".format(DC_PROVIDERS[target_crs], target_crs)
                ),
                "NODATA": None,
                "COPY_SUBDATASETS": False,
                "OPTIONS": "",
                "EXTRA": "",
                "DATA_TYPE": 6,
                "OUTPUT": dict_files["dem_bf"],
            },
        )
        # get flow acc
        print("[saga] get upslope area...")
        processing.run(
            "sagang:flowaccumulationparallelizable",
            {
                "DEM": dict_files["dem_bf"],
                "FLOW": dict_files["flowacc_mfd_saga"],
                "UPDATE": 0,
                "METHOD": 2,
                "CONVERGENCE": 1.1,
            },
        )
        # translate flow acc
        print("[saga] translate upslope area...")
        processing.run(
            "gdal:translate",
            {
                "INPUT": dict_files["flowacc_mfd_saga"],
                "TARGET_CRS": QgsCoordinateReferenceSystem(
                    "{}:{}".format(DC_PROVIDERS[target_crs], target_crs)
                ),
                "NODATA": None,
                "COPY_SUBDATASETS": False,
                "OPTIONS": "",
                "EXTRA": "",
                "DATA_TYPE": 6,
                "OUTPUT": dict_files["fac"],
            },
        )
    else:
        print("[wbt] fill sinks ...")
        # fill sinks
        processing.run(
            "wbt:FillDepressionsWangAndLiu",
            {
                "dem": dict_files["dem_b"],
                "fix_flats": True,
                "flat_increment": None,
                "output": dict_files["dem_bf"],
            },
        )
        # get flow acc
        print("[wbt] flow accumulation...")
        processing.run(
            "wbt:DInfFlowAccumulation",
            {
                "input": dict_files["dem_bf"],
                "out_type": 2,
                "threshold": None,
                "log": False,
                "clip": False,
                "pntr": False,
                "output": dict_files["fac"],
            },
        )
    print("[wbt] get upslope area...")
    # get upslope area
    processing.run(
        "wbt:D8FlowAccumulation",
        {
            "input": dict_files["dem_bf"],
            "out_type": 1,
            "log": False,
            "clip": False,
            "pntr": False,
            "esri_pntr": False,
            "output": dict_files["upa"],
        },
    )

    # get drainage mask
    print("[gdal] get TPS...")
    get_tps(
        file_tpi=dict_files["tpi"],
        file_upa=dict_files["upa"],
        file_output=dict_files["tps"],
        upa_min=0.1,
        upa_max=2,
        tpi_v=-2,
    )

    # todo [improvements] -- rasterize water mass polygons over the drainage map.
    #  This will require
    #  (1) rasterize polygons,
    #  (2) convert again to pcraster format and
    #  (3) overwrite file_drainage to the new version

    # get TWI
    print("[gdal] get TWI...")
    get_twi(
        file_slope=dict_files["slope"],
        file_upa=dict_files["fac"],
        file_output=dict_files["twi"],
    )
    print("[gdal] fuzzify TWI...")
    get_fuzzy(
        file_input=dict_files["twi"],
        file_output=dict_files["ftwi"],
        low_bound=0,
        high_bound=30,
    )

    # HAND
    # DEM PC-raster
    print("[pc-raster] convert dem to pcraster...")
    processing.run(
        "pcraster:converttopcrasterformat",
        {"INPUT": dict_files["dem"], "INPUT2": 3, "OUTPUT": dict_files["dem_pc"]},
    )
    # DEM_bf PC-raster
    print("[pc-raster] convert dem_bf to pcraster...")
    processing.run(
        "pcraster:converttopcrasterformat",
        {"INPUT": dict_files["dem_bf"], "INPUT2": 3, "OUTPUT": dict_files["dem_bf_pc"]},
    )

    print("[pc-raster] convert tps to pcraster...")
    processing.run(
        "pcraster:converttopcrasterformat",
        {"INPUT": dict_files["tps"], "INPUT2": 0, "OUTPUT": dict_files["tps_pc"]},
    )

    print("[pc-raster] get HAND...")
    dict_hand = get_hand(
        folder_project=folder_project,
        file_dem_filled=dict_files["dem_bf_pc"],
        file_dem_sample=dict_files["dem_pc"],
        file_drainage=dict_files["tps_pc"],
    )

    # convert LDD
    processing.run(
        "gdal:translate",
        {
            "INPUT": dict_hand["ldd"],
            "TARGET_CRS": None,
            "NODATA": 10,
            "COPY_SUBDATASETS": False,
            "OPTIONS": "",
            "EXTRA": "",
            "DATA_TYPE": 1,
            "OUTPUT": dict_files["ldd"],
        },
    )

    print("[gdal] fuzzify HAND...")
    get_fuzzy(
        file_input=dict_files["hand"],
        file_output=dict_files["fhand"],
        low_bound=20,
        high_bound=0,
    )

    print("[gdal] get HTWI...")
    get_htwi_list(
        file_ftwi=dict_files["ftwi"],
        file_fhand=dict_files["fhand"],
        folder_output=f"{folder_topo}/htwi",
        ls_weights=[0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
    )

    print("[geo] get DTO")
    get_dto(file_ldd=dict_files["ldd"], file_output=dict_files["dto"])

    # translate
    if translate_to_ascii:
        # append to dict
        for f in dict_hand:
            dict_files[f] = dict_hand[f]
        # translate all
        dict_raster = {"nodata": -9999, "data_type": 6}
        dict_qualiraster = {"nodata": 0, "data_type": 1}
        dict_translate = {
            "dem": dict_raster,
            "slope": dict_raster,
            "twi": dict_raster,
            "accflux": dict_raster,
            "ldd": dict_qualiraster,
        }
        # loop
        print("translating outputs...")
        for k in dict_translate:
            input_file = dict_files[k]
            processing.run(
                "gdal:translate",
                {
                    "INPUT": input_file,
                    "TARGET_CRS": None,
                    "NODATA": dict_translate[k]["nodata"],
                    "COPY_SUBDATASETS": False,
                    "OPTIONS": "",
                    "EXTRA": "",
                    "DATA_TYPE": dict_translate[k]["data_type"],
                    "OUTPUT": "{}/{}.asc".format(folder_topo, k),
                },
            )

    # todo [improvements] -- include a style handler
    if style_folder is not None:
        ls_styles = ["dem", "hand", "slope", "twi", "fac", "upa", "ldd"]

    print("get topo --DONE")
    return None


def retrieve_lulc(
    folder_src, folder_project, crs_target, crs_src, file_target, file_style_src=None
):
    """
    Retrieve lulc series maps from a source folder.
    PLANS-based folder structure is expected.

    :param folder_src: folder path to source maps -- Files are expected to end with _YYYY-MM-DD.tif
    :type folder_src: str
    :param folder_project: path to project folder
    :type folder_project: str
    :param crs_target: Code for CRS of target map
    :type crs_target: str
    :param crs_src: Code for CRS of sourced maps
    :type crs_src: str
    :param file_target: path to target map (eg, dem file)
    :type file_target: str
    :param file_style_src: path to QML style (optional)
    :type file_style_src: str
    :return: None
    :rtype: None

    Script example (for QGIS Python Console):

    .. code-block:: python

        # plans source code must be pasted to QGIS plugins directory
        from plans import qutils

        # call function
        qutils.retrieve_lulc(
            folder_src="/path/to/lulc/folder", # change paths!
            folder_project="/path/to/project",
            crs_target="5641",
            crs_src="4326",
            file_target="/path/to/dem.tif",
            file_style_src="/path/to/lulc_mapbiomas.qml"
        )


    """
    # handle folders
    folder_lulc = "{}/inputs/lulc/obs".format(folder_project)
    folder_aux = "{}/_aux".format(folder_lulc)

    # print("retrieve source-lulc years to intermediate folder -- align to dem raster")

    # ---------- warp lulc -----------

    # get extent in target crs
    target_extent_dict = get_extent_from_raster(file_input=file_target)

    # get extent string
    target_extent_str = "{},{},{},{} [{}:{}]".format(
        target_extent_dict["xmin"],
        target_extent_dict["xmax"],
        target_extent_dict["ymin"],
        target_extent_dict["ymax"],
        DC_PROVIDERS[crs_target],
        crs_target,
    )

    # find cellsize from target file
    cellsize = qgdal.get_cellsize(file_input=file_target)

    # loop over years
    list_main_files = glob.glob(f"{folder_src}/*_*.tif")

    print("clip-n-warp lulc ... ")
    for i in range(len(list_main_files)):
        file_main_lulc = str(Path(list_main_files[i]))
        date = (
            os.path.basename(file_main_lulc).replace(".tif", "").split("_")[-1]
            + "-01-01"
        )
        str_filename = "lulc_{}".format(date)
        file_output1 = "{}/src_raw_{}.tif".format(folder_aux, str_filename)
        # run warp
        print("[gdal] warp ... {}".format(str_filename))
        processing.run(
            "gdal:warpreproject",
            {
                "INPUT": file_main_lulc,
                "SOURCE_CRS": QgsCoordinateReferenceSystem(
                    "{}:{}".format(DC_PROVIDERS[crs_src], crs_src)
                ),
                "TARGET_CRS": QgsCoordinateReferenceSystem(
                    "{}:{}".format(DC_PROVIDERS[crs_target], crs_target)
                ),
                "RESAMPLING": 0,  # nearest
                "NODATA": 0,
                "TARGET_RESOLUTION": cellsize,
                "OPTIONS": "",
                "DATA_TYPE": 1,
                "TARGET_EXTENT": target_extent_str,
                "TARGET_EXTENT_CRS": QgsCoordinateReferenceSystem(
                    "{}:{}".format(DC_PROVIDERS[crs_target], crs_target)
                ),
                "MULTITHREADING": False,
                "EXTRA": "",
                "OUTPUT": file_output1,
            },
        )
        print("[gdal] fill ... {}".format(str_filename))
        # fill no data
        s_prefix = "src_fill"
        file_output = "{}/{}_{}.tif".format(folder_aux, s_prefix, str_filename)
        processing.run(
            "gdal:fillnodata",
            {
                "INPUT": file_output1,
                "BAND": 1,
                "DISTANCE": 10,
                "ITERATIONS": 0,
                "MASK_LAYER": None,
                "OPTIONS": "",
                "EXTRA": "-interp nearest",
                "OUTPUT": file_output,
            },
        )
        # handle style
        if file_style_src is not None:
            shutil.copy(
                src=file_style_src, dst=f"{folder_aux}/{s_prefix}_{str_filename}.qml"
            )
        # delete warp
        # os.remove(file_output1)
        # handle styles

    return folder_aux


def convert_lulc(
    folder_src,
    folder_project,
    file_conversion_table,
    prefix_src="src_fill",
    id_src="id_mapbiomas",
    file_style=None,
):
    """
    Convert lulc values from source map.
    PLANS-based folder structure is expected.

    :param folder_src: path to sourced maps
    :type folder_src: str
    :param folder_project: path to project
    :type folder_project: str
    :param file_conversion_table: path to CSV table for conversion ids
    :type file_conversion_table: str
    :param prefix_src: prefix in source maps
    :type prefix_src: str
    :param id_src: name of column storing the id field for source maps
    :type id_src: str
    :param file_style: path to converted style QML file
    :type file_style: str
    :return: None
    :rtype: None

    Script example (for QGIS Python Console):

    .. code-block:: python

        # plans source code must be pasted to QGIS plugins directory
        from plans import qutils

        # call function
        qutils.convert_lulc(
            folder_src="/path/to/folder", # change paths!
            folder_project=/path/to/folder,
            file_conversion_table="/path/to/folder/lulc_conversion.csv",
            prefix_src="src_fill",
            id_src="id_mapbiomas",
            file_style="/path/to/folder/lulc.qml"
        )

    """
    # handle folders
    folder_lulc = "{}/inputs/lulc/obs".format(folder_project)
    print("[pandas] read table")
    df = pd.read_csv(file_conversion_table, sep=";", encoding="utf-8")
    # print("get values lists")
    df = df.dropna().copy()
    ls_src_ids = list(df[id_src])
    ls_dst_ids = list(df["id"])
    # print("list all src lulc")
    if prefix_src is not None:
        prefix_src = f"{prefix_src}_"
    else:
        prefix_src = ""
    ls_src_files1 = glob.glob(f"{folder_src}/{prefix_src}lulc_*.tif")
    # fix path structure
    ls_src_files = [str(Path(src_file)) for src_file in ls_src_files1]
    # loop over
    for file_input in ls_src_files:
        s_date = os.path.basename(file_input).replace(".tif", "").split("_")[-1]
        print(f"[gdal] {s_date} -- load grid")
        #
        # -------------------------------------------------------------------------
        # LOAD
        # Open the raster file using gdal
        dc_raster = qgdal.read_raster(file_input=file_input)
        grid_input = dc_raster["data"]

        print(f"[geo] {s_date} -- apply conversion")
        #
        # -------------------------------------------------------------------------
        # PROCESS
        grid_output = geo.convert(
            array=grid_input, old_values=ls_src_ids, new_values=ls_dst_ids
        )
        print(f"[gdal] {s_date} -- save to geotiff")
        #
        # -------------------------------------------------------------------------
        # EXPORT RASTER FILE
        file_output_name = f"lulc_{s_date}"
        file_output = f"{folder_lulc}/{file_output_name}.tif"
        dc_raster["metadata"]["NODATA_value"] = DC_NODATA["byte"]
        qgdal.write_raster(
            grid_output=grid_output,
            dc_metadata=dc_raster["metadata"],
            file_output=file_output,
            dtype="byte",
        )
        #
        # handle style
        if file_style is not None:
            shutil.copy(src=file_style, dst=f"{folder_lulc}/{file_output_name}.qml")
    print("conversion --DONE")
    return None


# todo [develop]
"""
def rasterize_roads():    
    print("-- reproject from source to local vector database")
    print("rasterize to maps")
"""


def get_lulc(
    folder_src,
    folder_project,
    crs_target,
    file_target,
    file_conversion_table,
    crs_src="4326",
    id_src="id_mapbiomas",
    file_style_src=None,
    file_style=None,
    db_roads=None,
    layer_roads="roads",
):
    """
    Get lulc maps from source and convert to plans-format.
    PLANS-based folder structure is expected.

    :param folder_src: folder path to source maps -- Files are expected to end with _YYYY-MM-DD.tif
    :type folder_src: str
    :param folder_project: path to project folder
    :type folder_project: str
    :param crs_target: Code for CRS of target map
    :type crs_target: str
    :param crs_src: Code for CRS of sourced maps
    :type crs_src: str
    :param file_target: path to target map (eg, dem file)
    :type file_target: str
    :param file_style_src: path to QML style (optional)
    :type file_style_src: str
    :param file_conversion_table: path to CSV table for conversion ids
    :type file_conversion_table: str
    :param id_src: name of column storing the id field for source maps
    :type id_src: str
    :param file_style: path to converted style QML file
    :type file_style: str
    :return: None
    :rtype: None
    """

    print("retrieve lulc maps from source")
    folder_lulc = retrieve_lulc(
        folder_src=folder_src,
        folder_project=folder_project,
        crs_target=crs_target,
        crs_src=crs_src,
        file_target=file_target,
        file_style_src=file_style_src,
    )
    print("convert lulc indexing")
    convert_lulc(
        folder_src=folder_lulc,
        folder_project=folder_project,
        file_conversion_table=file_conversion_table,
        prefix_src="src_fill",
        id_src=id_src,
        file_style=file_style,
    )
    # clean up aux folder
    ls_files = glob.glob(f"{folder_lulc}/*_lulc_*.tif")
    for f in ls_files:
        os.remove(f)

    # todo [improvements] -- setup a way to rasterize OSM roads

    return None


def get_basins(folder_project, db_outlets, layer_outlets, code_outlets, crs_target):
    # todo [docstring]
    # ----- SETUP -----
    # these folders and files are expected to exist
    folder_topo = "{}/inputs/topo".format(folder_project)
    folder_basins = "{}/inputs/basins".format(folder_project)
    folder_aux = "{}/_aux".format(folder_basins)
    db_project = f"{folder_project}/inputs/vectors.gpkg"
    ldd_file_pc = f"{folder_topo}/_aux/ldd.map"
    dto_file = f"{folder_topo}/dto.tif"

    print("[gdal] reproject outlets layers")
    layer_outlets_project = reproject_layer(
        db_input=db_outlets,
        layer_name=layer_outlets,
        crs_target=crs_target,
        db_output=db_project,
        layer_output="outlets",
    )

    # add a id field
    print("[geopandas] assign id basin")
    gdf = gpd.read_file(filename=db_project, layer=layer_outlets_project)
    # Add a new field with unique IDs
    gdf["id_basin"] = np.arange(1, len(gdf) + 1).astype(
        int
    )  # Create unique integer IDs
    # Save the updated geopackage
    gdf.to_file(db_project, layer=layer_outlets_project, driver="GPKG")

    print("[gdal] get a blank copy")
    file_outlets_aprx = get_blank(
        file_input=f"{folder_topo}/dem.tif",
        file_output=f"{folder_aux}/outlets_aprx.tif",
        blank_value=0,
        dtype="uint16",
    )

    print("[gdal] rasterize outlets by id")
    processing.run(
        "gdal:rasterize_over",
        {
            "INPUT": "{}|layername={}".format(db_project, layer_outlets_project),
            "INPUT_RASTER": file_outlets_aprx,
            "FIELD": "id_basin",
            "ADD": False,
            "EXTRA": "",
        },
    )
    # enter loop
    # todo [improvement] -- implement a algorithm for handling bad-positioned outlets
    #  this wil require to first sample the UPA value at each point
    #  then select only those problematic that are below a certain are threshold
    #  for these selected, apply a searching procedure using proximity and map algebra
    #  save a new outlet_code.tif and delete the old one
    """
    print("-- compute the exact outlet map -- outlets")
    print("load aprox outlets grid")
    print("load upa grid")
    print("set a zero-grid for receiving the exact outlets")
    print("enter a loop for each outlet (pass lists of ids and codes)")
    print("enter in numpy processing")
    print("compute a boolean for the outlet")
    print("compute distance/proximity")
    print("compute a search radius boolean")
    print("multiply the radius to the upa -- upa_mask")
    print("compute the max value in the mask")
    print("compute the boolean of the max")
    print("multiply the max-bool to the outlet id")
    print("add to the exact outlet grid")
    print("save to geotiff with code -- outlet_<code>.tif")
    print("exit loop")    
    """
    dc_basins = {}
    for i in range(len(gdf)):
        id_basin = gdf["id_basin"].values[i]
        code_basin = gdf[code_outlets].values[i]
        print(f"[gdal] get boolean of outlet {code_basin}")
        file_outlet = get_boolean(
            file_input=file_outlets_aprx,
            file_output=f"{folder_aux}/outlet_{code_basin}.tif",
            bool_value=id_basin,
            condition="ET",
        )
        # convert to pc raster
        print("[pc-raster] get outlets...")
        outlets_raster_pc = "{}/outlet_{}.map".format(folder_aux, code_basin)
        processing.run(
            "pcraster:converttopcrasterformat",
            {"INPUT": file_outlet, "INPUT2": 1, "OUTPUT": outlets_raster_pc},
        )
        # get basins
        basins_file_pc = "{}/basin_{}.map".format(folder_aux, code_basin)
        print("[pc-raster] get basins...")
        processing.run(
            "pcraster:subcatchment",
            {
                "INPUT1": ldd_file_pc,
                "INPUT2": outlets_raster_pc,
                "OUTPUT": basins_file_pc,
            },
        )
        print("[gdal] convert basin...")
        basins_raster = "{}/basins_{}.tif".format(folder_basins, code_basin)
        processing.run(
            "gdal:translate",
            {
                "INPUT": basins_file_pc,
                "TARGET_CRS": QgsCoordinateReferenceSystem(
                    "EPSG:{}".format(crs_target)
                ),
                "NODATA": 255,
                "COPY_SUBDATASETS": False,
                "OPTIONS": "",
                "EXTRA": "",
                "DATA_TYPE": 1,
                "OUTPUT": basins_raster,
            },
        )
        dc_basins[code_basin] = basins_raster

    print("[plans] get path-areas")
    get_path_areas(
        file_dto=dto_file,
        dc_basins=dc_basins,
        file_output=f"{folder_basins}/path_areas.csv",
        n_bins=100,
    )

    print("basins -- DONE")
    return None


# ------------------------------------------------------------------------------------------
# code below is not deprecated but somehow outdated (seems too complicated)


def get_rain_old(
    output_folder,
    src_folder,
    input_db,
    target_file,
    target_crs,
    layer_aoi="aoi",
    layer_rain_gauges="rain",
):
    """Get ``rain`` datasets for running PLANS.

    :param output_folder: path to output folder
    :type output_folder: str
    :param src_folder: path to source folder for all csv series files. Files must be named by rain_<alias>.csv
    :type src_folder: str
    :param input_db: path to geopackage database with rain gauge layer
    :type input_db: str
    :param target_file: file path to target raster (e.g., the ``DEM`` raster)
    :type target_file: str
    :param target_crs: EPSG code (number only) for the target CRS
    :type target_crs: str
    :param layer_aoi: name of Area Of Interest layer (polygon). Default is "aoi"
    :type layer_aoi: str
    :param layer_rain_gauges: layer name of rain gauges layer.
        Required fields in layer:

            - ``Id``: int, required. Unique number id.
            - ``Name``: str, required. Simple name.
            - ``Alias``: str, required. Short nickname.
            - ``Rain_File``: str, required. Path to data time series ``csv`` source file.
            - ``X``: float, optional. Recomputed from layer. Longitude in WGS 84 Datum (EPSG4326).
            - ``Y``: float, optional. Recomputed from layer. Latitude in WGS 84 Datum (EPSG4326).
            - ``Code``: str, op
            - ``Source``: str, required
            - ``Description``: str, required
            - ``Color``: str, optional

    :type layer_rain_gauges: str
    :return: None
    :rtype: None

    Script example (for QGIS Python Console):

    .. code-block:: python

        # plans source code must be pasted to QGIS plugins directory
        from plans import qutils

        # call function
        qutils.get_rain(
            output_folder="path/to/rain", # change paths!
            src_folder="path/to/src",
            target_file="path/to/dem.asc",
            target_crs="31982",
            input_db="path/to/my_db.gpkg",
            layer_aoi="aoi",
            layer_rain_gauges="rain"
        )

    """
    from plans import datasets

    def calculate_buffer_ratios(box_small, box_large):
        delta_x_small = abs(box_small["xmax"] - box_small["xmin"])
        lower_x = abs(box_small["xmin"] - box_large["xmin"])
        upper_x = abs(box_small["xmax"] - box_large["xmax"])
        x_ratio = max(lower_x / delta_x_small, upper_x / delta_x_small)

        delta_y_small = abs(box_small["ymax"] - box_small["ymin"])
        lower_y = abs(box_small["ymin"] - box_large["ymin"])
        upper_y = abs(box_small["ymax"] - box_large["ymax"])
        y_ratio = max(lower_y / delta_y_small, upper_y / delta_y_small)

        return (x_ratio, y_ratio)

    # folders and file setup
    print("folder setup...")
    output_folder_interm = "{}/intermediate".format(output_folder)
    if os.path.isdir(output_folder_interm):
        pass
    else:
        os.mkdir(output_folder_interm)
    print("get info...")

    # ---------------- RAIN SERIES ----------------
    # load table
    rain_gdf = gpd.read_file(input_db, layer=layer_rain_gauges)

    # overwrite
    rain_gdf["Rain_Units"] = "mm"
    rain_gdf["Rain_DtField"] = "DateTime"
    rain_gdf["Rain_VarField"] = "P"

    # compute X and Y
    rain_gdf["X"] = rain_gdf.geometry.x
    rain_gdf["Y"] = rain_gdf.geometry.y
    if "Color" not in rain_gdf.columns:
        rain_gdf["Color"] = datasets.get_colors(size=len(rain_gdf))

    # rename files and copy
    lst_files_src = rain_gdf["Rain_File"].values
    lst_files_dst = [
        "{}/rain_{}.csv".format(output_folder, a) for a in rain_gdf["Alias"].values
    ]
    lst_new_files = []
    for i in range(len(rain_gdf)):
        if os.path.isfile(lst_files_src[i]):
            shutil.copy(src=lst_files_src[i], dst=lst_files_dst[i])
            new_file_name = "rain_{}.csv".format(rain_gdf["Alias"].values[i])
        else:
            new_file_name = ""
        lst_new_files.append(new_file_name)
    # reset File
    rain_gdf["Rain_File"] = lst_new_files

    # Drop the geometry column
    rain_gdf = rain_gdf.drop(columns=["geometry"])

    # organize columns
    rain_gdf = rain_gdf[
        [
            "Id",
            "Name",
            "Alias",
            "X",
            "Y",
            "Source",
            "Code",
            "Description",
            "Color",
            "Rain_Units",
            "Rain_VarField",
            "Rain_DtField",
            "Rain_File",
        ]
    ]

    # export csv file
    rain_info_file = "{}/rain_info.csv".format(output_folder)
    rain_gdf.to_csv(rain_info_file, sep=";", index=False)
    # print(rain_gdf.to_string())

    # ---------------- RAIN ZONES ----------------

    # first check number of features
    n_rain_gauges = count_vector_features(
        input_db=input_db, layer_name=layer_rain_gauges
    )
    dict_blank = {"constant": 0, "voronoi": 0}
    s_type = "voronoi"
    if n_rain_gauges < 2:
        print(" -- only one rain gauge found")
        s_type = "constant"
        # create constant raster layer based on target and Id

        # find rain id
        n_id = rain_gdf["Id"].values[0]
        # update dict
        dict_blank["constant"] = n_id
    else:
        # get voronoi zones

        # first validade extents
        dict_extent_aoi = get_extent_from_vector(
            db_input=input_db, layer_name=layer_aoi
        )
        dict_extent_rain = get_extent_from_vector(
            db_input=input_db, layer_name=layer_rain_gauges
        )

        # check is is bounded:
        if is_bounded_by(extent_a=dict_extent_rain, extent_b=dict_extent_aoi):
            n_buffer = 20
        else:
            n_buffer = (
                100
                * 1.2
                * max(
                    calculate_buffer_ratios(
                        box_small=dict_extent_rain, box_large=dict_extent_aoi
                    )
                )
            )

        # reproject rain
        layer_rain_gauges_2 = reproject_layer(
            db_input=input_db, layer_name=layer_rain_gauges, crs_target=target_crs
        )
        print("get voronoi polygons...")
        # run function
        zones_shp = "{}/rain_zones.shp".format(output_folder_interm)
        processing.run(
            "qgis:voronoipolygons",
            {
                "INPUT": "{}|layername={}".format(input_db, layer_rain_gauges_2),
                "BUFFER": n_buffer,
                "OUTPUT": zones_shp,
            },
        )
    print("get zones raster...")
    zones_raster = "{}/rain_zones.tif".format(output_folder_interm)
    # create constant raster layer
    get_blank(
        file_input=target_file, file_output=zones_raster, blank_value=dict_blank[s_type]
    )
    # rasterize target raster
    if s_type == "voronoi":
        # rasterize voronoi
        processing.run(
            "gdal:rasterize_over",
            {
                "INPUT": zones_shp,
                "INPUT_RASTER": zones_raster,
                "FIELD": "Id",
                "ADD": False,
                "EXTRA": "",
            },
        )
    print("translate...")
    # translante raster layer
    processing.run(
        "gdal:translate",
        {
            "INPUT": zones_raster,
            "TARGET_CRS": QgsCoordinateReferenceSystem("EPSG:{}".format(target_crs)),
            "NODATA": 0,
            "COPY_SUBDATASETS": False,
            "OPTIONS": "",
            "EXTRA": "",
            "DATA_TYPE": 1,
            "OUTPUT": "{}/rain_zones.asc".format(output_folder),
        },
    )
    print("end")
    return None


def get_lulc_old(
    list_main_files,
    list_dates,
    lulc_table,
    output_folder,
    target_file,
    crs_target,
    db_roads=None,
    layer_roads_dirty="roads_dirty",
    layer_roads_paved="roads_paved",
    source_crs="4326",
    qml_file=None,
    translate=True,
):
    """Get LULC maps from a larger main LULC dataset.

    :param list_main_files: list of file paths to main lulc rasters
    :type list_main_files: list
    :param list_dates: list of dates (YYYY-MM-DD) for each main raster
    :type list_dates: list
    :param lulc_table: path to parameter table file. Expected columns: Id, Name, Alias and Color
    :type lulc_table: str
    :param output_folder: path to output folder
    :type output_folder: str
    :param target_file: file path to target raster (e.g., the DEM raster)
    :type target_file: str
    :param crs_target: EPSG code (number only) for the target CRS
    :type crs_target: str
    :param db_roads: [optional] path to geopackage database with road layers
    :type db_roads: str
    :param layer_roads_dirty: layer name of dirty roads
    :type layer_roads_dirty: str
    :param layer_roads_paved: layer name of paved roads
    :type layer_roads_paved: str
    :param source_crs: EPSG code (number only) for the source CRS. default is WGS-84 (4326)
    :type source_crs: str
    :param qml_file: [optional] file path to QML style file
    :type qml_file: str
    :return: None
    :rtype: None

    Script example (for QGIS):

    .. code-block:: python

        # plans source code must be pasted to QGIS plugins directory
        from plans import qutils
        # set files
        lst_files = [
            "path/to/lulc_2015.tif",
            "path/to/lulc_2015.tif",
            "path/to/lulc_2016.tif",
        ]
        # set dates
        lst_dates = [
            "2014-01-01",
            "2015-01-01",
            "2016-01-01",
        ]
        # run function
        qutils.get_lulc(
            list_main_files=lst_files,
            list_dates=lst_dates,
            output_folder="path/to/output",
            target_file="/path/to/raster.tif",
            crs_target="5641",
            db_roads="path/to/input_db.gpkg",
            layer_roads_dirty='roads_dirty',
            layer_roads_paved='roads_paved',
            source_crs='4326',
            qml_file="path/to/style.qml"
        )

    """
    # folders and file setup
    if translate:
        output_folder_interm = "{}/intermediate".format(output_folder)
        if os.path.isdir(output_folder_interm):
            pass
        else:
            os.mkdir(output_folder_interm)
    else:
        output_folder_interm = output_folder
    # ---------- warp lulc -----------
    target_extent_dict = get_extent_from_raster(file_input=target_file)
    # get extent string
    target_extent_str = "{},{},{},{} [{}:{}]".format(
        target_extent_dict["xmin"],
        target_extent_dict["xmax"],
        target_extent_dict["ymin"],
        target_extent_dict["ymax"],
        DC_PROVIDERS[crs_target],
        crs_target,
    )
    cellsize = qgdal.get_cellsize(file_input=target_file)
    list_output_files = list()
    list_filenames = list()
    print("clip-n-warp lulc ... ")
    for i in range(len(list_main_files)):
        file_main_lulc = list_main_files[i]
        date = list_dates[i]
        str_filename = "lulc_{}".format(date)
        file_output1 = "{}/_{}.tif".format(output_folder_interm, str_filename)

        # run warp
        processing.run(
            "gdal:warpreproject",
            {
                "INPUT": file_main_lulc,
                "SOURCE_CRS": QgsCoordinateReferenceSystem(
                    "{}:{}".format(DC_PROVIDERS[source_crs], source_crs)
                ),
                "TARGET_CRS": QgsCoordinateReferenceSystem(
                    "{}:{}".format(DC_PROVIDERS[crs_target], crs_target)
                ),
                "RESAMPLING": 0,  # nearest
                "NODATA": 0,
                "TARGET_RESOLUTION": cellsize,
                "OPTIONS": "",
                "DATA_TYPE": 1,
                "TARGET_EXTENT": target_extent_str,
                "TARGET_EXTENT_CRS": QgsCoordinateReferenceSystem(
                    "{}:{}".format(DC_PROVIDERS[crs_target], crs_target)
                ),
                "MULTITHREADING": False,
                "EXTRA": "",
                "OUTPUT": file_output1,
            },
        )
        file_output = "{}/{}.tif".format(output_folder_interm, str_filename)
        list_output_files.append(file_output[:])
        list_filenames.append(str_filename[:])
        # fill no data
        processing.run(
            "gdal:fillnodata",
            {
                "INPUT": file_output1,
                "BAND": 1,
                "DISTANCE": 10,
                "ITERATIONS": 0,
                "MASK_LAYER": None,
                "OPTIONS": "",
                "EXTRA": "-interp nearest",
                "OUTPUT": file_output,
            },
        )
        # delete warp
        os.remove(file_output1)
    #
    # ---------- handle roads -----------
    if db_roads is None:
        pass
    else:
        print("reproject road layers...")
        # reproject dirty

        new_layer_dirty = reproject_layer(
            db_input=db_roads, layer_name=layer_roads_dirty, crs_target=crs_target
        )
        # reproject paved
        new_layer_paved = reproject_layer(
            db_input=db_roads, layer_name=layer_roads_paved, crs_target=crs_target
        )

        # rasterize loop
        print("rasterizing road layers...")
        for i in range(len(list_output_files)):
            input_raster = list_output_files[i]
            # dirty
            processing.run(
                "gdal:rasterize_over_fixed_value",
                {
                    "INPUT": "{}|layername={}".format(db_roads, new_layer_dirty),
                    "INPUT_RASTER": input_raster,
                    "BURN": 255,
                    "ADD": False,
                    "EXTRA": "",
                },
            )
            # paved
            processing.run(
                "gdal:rasterize_over_fixed_value",
                {
                    "INPUT": "{}|layername={}".format(db_roads, new_layer_paved),
                    "INPUT_RASTER": input_raster,
                    "BURN": 254,
                    "ADD": False,
                    "EXTRA": "",
                },
            )
    # ---------- translate all -----------
    for i in range(len(list_output_files)):
        input_file = list_output_files[i]
        filename = list_filenames[i]
        if translate:
            print("translate...")
            processing.run(
                "gdal:translate",
                {
                    "INPUT": input_file,
                    "TARGET_CRS": QgsCoordinateReferenceSystem(
                        "EPSG:{}".format(crs_target)
                    ),
                    "NODATA": 0,
                    "COPY_SUBDATASETS": False,
                    "OPTIONS": "",
                    "EXTRA": "",
                    "DATA_TYPE": 1,
                    "OUTPUT": "{}/{}.asc".format(output_folder, filename),
                },
            )

        # Handle style
        if qml_file is None:
            pass
        else:
            shutil.copy(src=qml_file, dst="{}/{}.qml".format(output_folder, filename))

    # Handle table
    print("table...")
    df_table = pd.read_csv(lulc_table, sep=";")
    df_roads = pd.DataFrame(
        {
            "Id": [254, 255],
            "Name": ["Paved roads", "Dirty roads"],
            "Alias": ["RdP", "RdD"],
            "Color": ["#611d1d", "#976d3f"],
        }
    )
    df_table = pd.concat([df_table, df_roads], ignore_index=True)
    df_table.to_csv(os.path.join(output_folder, "lulc_info.csv"), sep=";", index=False)

    return None


def get_basins_old(
    output_folder,
    input_db,
    ldd_file,
    target_crs,
    layer_stream_gauges="stream",
):
    """Get all ``basins`` datasets for running PLANS.

    :param output_folder: path to output folder
    :type output_folder: str
    :param input_db: path to geopackage database with streamflow gauges layer
    :type input_db: str
    :param ldd_file: file path to LDD raster
    :type ldd_file: str
    :param target_crs: EPSG code (number only) for the target CRS
    :type target_crs: str
    :param layer_stream_gauges: layer name of streamflow gauges layer
        Required fields in layer:

            - ``Id``: int, required. Unique number id.
            - ``Name``: str, required. Simple name.
            - ``Alias``: str, required. Short nickname.
            - ``X``: float, optional. Recomputed from layer. Longitude in WGS 84 Datum (EPSG4326).
            - ``Y``: float, optional. Recomputed from layer. Latitude in WGS 84 Datum (EPSG4326).
            - ``Code``: str, op
            - ``Source``: str, required
            - ``Description``: str, required
            - ``Color``: str, optional
            - ``Stage_File``: str, required. Path to data time series ``csv`` source file.
            - ``Flow_File``: str, required. Path to data time series ``csv`` source file.

    :type layer_stream_gauges: str
    :return: None
    :rtype: None

    Script example (for QGIS Python Console):

    .. code-block:: python

        # plans source code must be pasted to QGIS plugins directory
        from plans import qutils

        # call function
        qutils.get_basins(
            output_folder="path/to/basins",
            ldd_file="path/to/ldd.asc",
            target_crs="31982",
            input_db="path/to/my_db.gpkg",
            layer_stream_gauges="stream"
        )

    """
    from plans import datasets

    print("folder setup...")
    # folders and file setup
    output_folder_interm = "{}/intermediate".format(output_folder)
    if os.path.isdir(output_folder_interm):
        pass
    else:
        os.mkdir(output_folder_interm)

    # GDAL folder
    output_folder_gdal = "{}/gdal".format(output_folder_interm)
    if os.path.isdir(output_folder_gdal):
        pass
    else:
        os.mkdir(output_folder_gdal)

    # ------------------- BASIN MAPS ------------------- #

    # PCRASTER folder
    output_folder_pcraster = "{}/pcraster".format(output_folder_interm)
    if os.path.isdir(output_folder_pcraster):
        pass
    else:
        os.mkdir(output_folder_pcraster)
    print("reproject...")
    # reproject streams
    layer_stream_gauges_new = reproject_layer(
        db_input=input_db, crs_target=target_crs, layer_name=layer_stream_gauges
    )
    print("blank raster...")
    gauge_raster = "{}/gauges.tif".format(output_folder_gdal)
    # get blanks
    get_blank(
        file_input=ldd_file, file_output=gauge_raster, blank_value=0, dtype="float32"
    )
    print("rasterize...")
    # rasterize
    processing.run(
        "gdal:rasterize_over",
        {
            "INPUT": "{}|layername={}".format(input_db, layer_stream_gauges_new),
            "INPUT_RASTER": gauge_raster,
            "FIELD": "Id",
            "ADD": False,
            "EXTRA": "",
        },
    )
    # todo validate gauge positions

    # convert to pc raster
    print("get outlets...")
    outlets_raster_pc = "{}/outlets.map".format(output_folder_pcraster)
    processing.run(
        "pcraster:converttopcrasterformat",
        {"INPUT": gauge_raster, "INPUT2": 1, "OUTPUT": outlets_raster_pc},
    )
    # convert ldd
    print("get ldd...")
    ldd_file_pc = "{}/ldd.map".format(output_folder_pcraster)
    processing.run(
        "pcraster:converttopcrasterformat",
        {"INPUT": ldd_file, "INPUT2": 5, "OUTPUT": ldd_file_pc},
    )
    # get basins
    basins_file_pc = "{}/basins.map".format(output_folder_pcraster)
    print("get basins...")
    processing.run(
        "pcraster:subcatchment",
        {"INPUT1": ldd_file_pc, "INPUT2": outlets_raster_pc, "OUTPUT": basins_file_pc},
    )
    # translante raster layers
    outlets_raster = "{}/outlets.asc".format(output_folder)
    processing.run(
        "gdal:translate",
        {
            "INPUT": outlets_raster_pc,
            "TARGET_CRS": QgsCoordinateReferenceSystem("EPSG:{}".format(target_crs)),
            "NODATA": 0,
            "COPY_SUBDATASETS": False,
            "OPTIONS": "",
            "EXTRA": "",
            "DATA_TYPE": 1,
            "OUTPUT": outlets_raster,
        },
    )
    basins_raster = "{}/basins.asc".format(output_folder)
    processing.run(
        "gdal:translate",
        {
            "INPUT": basins_file_pc,
            "TARGET_CRS": QgsCoordinateReferenceSystem("EPSG:{}".format(target_crs)),
            "NODATA": 0,
            "COPY_SUBDATASETS": False,
            "OPTIONS": "",
            "EXTRA": "",
            "DATA_TYPE": 1,
            "OUTPUT": basins_raster,
        },
    )

    # ------------------- BASINS INFO ------------------- #
    # load table
    basins_gdf = gpd.read_file(input_db, layer=layer_stream_gauges)

    print("handle file series")

    # compute X and Y
    basins_gdf["X"] = basins_gdf.geometry.x
    basins_gdf["Y"] = basins_gdf.geometry.y

    if "Color" not in basins_gdf.columns:
        basins_gdf["Color"] = datasets.get_colors(size=len(basins_gdf))

    # fill attributes
    lst_aux = ["Units", "VarField", "DtField"]
    dct_vals = {
        "Stage": ["cm", "H", "DateTime"],
        "Flow": ["m3/s", "Q", "DateTime"],
    }
    # Iterate over the items in dct_vals
    for key, values in dct_vals.items():
        # Create the column name by combining the key and the first item in values
        for i in range(len(lst_aux)):
            column_name = f"{key}_{lst_aux[i]}"
            # Set the values in the GeoDataFrame
            basins_gdf[column_name] = values[i]

    lst_aux = ["Stage", "Flow"]
    for l in lst_aux:
        # rename files and copy
        print("{} files...".format(l))
        lst_files_src = basins_gdf["{}_File".format(l)].values
        lst_files_dst = [
            "{}/{}_{}.csv".format(output_folder, l.lower(), a)
            for a in basins_gdf["Alias"].values
        ]
        lst_new_files = []
        for i in range(len(basins_gdf)):
            if os.path.isfile(lst_files_src[i]):
                shutil.copy(src=lst_files_src[i], dst=lst_files_dst[i])
                new_file_name = "{}_{}.csv".format(
                    l.lower(), basins_gdf["Alias"].values[i]
                )
            else:
                new_file_name = ""
            lst_new_files.append(new_file_name)
        # reset File
        basins_gdf["{}_File".format(l)] = lst_new_files

    # Drop the geometry column
    basins_gdf = basins_gdf.drop(columns=["geometry"])

    print("compute basin topology")

    # This appends a "Downstream_Id" field
    dict_aux = get_downstream_ids(
        file_ldd=ldd_file, file_basins=basins_raster, file_outlets=outlets_raster
    )
    aux_gdf = gpd.GeoDataFrame.from_dict(dict_aux, geometry=None)
    basins_gdf = basins_gdf.merge(aux_gdf, on="Id")

    # GET UPSTREAM AREAS
    dict_aux = get_basins_areas(
        file_basins=basins_raster, ids_basins=list(basins_gdf["Id"])
    )
    aux_gdf = gpd.GeoDataFrame.from_dict(dict_aux, geometry=None)
    basins_gdf = basins_gdf.merge(aux_gdf, on="Id")

    # HOW to organize columns? Base attribute first, Stage and Flow last
    column_order = [
        # Base attributes
        "Id",
        "Name",
        "Alias",
        # Geo Attributes
        "X",
        "Y",
        "Downstream_Id",
        "UpstreamArea",
        # Extra Attributes
        "Code",
        "Source",
        "Description",
        "Color",
        # Stage attributes
        "Stage_Units",
        "Stage_VarField",
        "Stage_DtField",
        "Stage_File",
        # Flow attributes
        "Flow_Units",
        "Flow_VarField",
        "Flow_DtField",
        "Flow_File",
    ]

    # Reorder the columns
    basins_gdf = basins_gdf[column_order]

    # export csv file
    basins_gdf.to_csv("{}/basins_info.csv".format(output_folder), sep=";", index=False)

    print("end")
    return None


def testing():
    print("testing")
