# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
Parse raster data using gdal in QGIS python console

Overview
--------

Required dependencies in QGIS:

- gdal

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

"""
# todo ---- improve examples an docstrings
# todo ---- format module
# todo ---- refactor better names
# todo ---- refactor for root.DataSet inheritance
# todo ---- make unit tests

from osgeo import gdal

# setup types
DC_GDAL_TYPES = {
    "byte": gdal.GDT_Byte,
    "int": gdal.GDT_Int16,
    "uint16": gdal.GDT_UInt16,
    "int16": gdal.GDT_Int16,
    "float16": gdal.GDT_Float32,
    "float32": gdal.GDT_Float32,
}


def get_cellsize(file_input):
    """
    Get the cell size (resolution) of a raster file.

    :param file_input: Path to the input raster file.
    :param type: str
    :return: The cell size of the raster.
    :rtype: float
    """
    # Open the raster file using gdal
    raster_input = gdal.Open(file_input)
    raster_geotransform = raster_input.GetGeoTransform()
    cellsize = raster_geotransform[1]
    # -- Close the raster
    raster_input = None
    return cellsize


def read_raster(file_input, n_band=1, metadata=True):
    """
    Read a raster (GeoTIFF) file

    :param file_input: path to raster file
    :type file_input: str
    :param n_band: number of the band to read
    :type n_band: int
    :param metadata: option to return
    :type metadata: bool
    :return: dictionary with "data" and (optional) "metadata"
    :rtype: dict
    """
    # -------------------------------------------------------------------------
    # LOAD
    # Open the raster file using gdal
    raster_input = gdal.Open(file_input)
    # Get the raster band
    band_input = raster_input.GetRasterBand(1)
    # Read the raster data as a numpy array
    grid_input = band_input.ReadAsArray()
    dc_output = {"data": grid_input}
    # -- Collect useful metadata
    if metadata:
        dc_metadata = {}
        dc_metadata["raster_x_size"] = raster_input.RasterXSize
        dc_metadata["raster_y_size"] = raster_input.RasterYSize
        dc_metadata["raster_projection"] = raster_input.GetProjection()
        dc_metadata["raster_geotransform"] = raster_input.GetGeoTransform()
        dc_metadata["cellsize"] = dc_metadata["raster_geotransform"][1]
        # append to output
        dc_output["metadata"] = dc_metadata
    # -- Close the raster
    raster_input = None

    return dc_output


def write_raster(grid_output, dc_metadata, file_output, dtype="float32", n_band=1):
    """
    Write a numpy array to raster

    :param grid_output: 2D numpy array
    :type grid_output: :class:`numpy.ndarray`
    :param dc_metadata: dict with metadata
    :type dc_metadata: dict
    :param file_output: path to output raster file
    :type file_output: str
    :param dtype: output raster data type ("byte", "int" -- else defaults to float32)
    :type dtype: str
    :param n_band: number of the band to read
    :type n_band: int
    :return:
    :rtype:
    """
    # Get the driver to create the new raster
    driver = gdal.GetDriverByName("GTiff")

    # get metadata
    raster_x_size = grid_output.shape[1]  # dc_metadata["raster_x_size"]
    raster_y_size = grid_output.shape[0]  # dc_metadata["raster_y_size"]
    raster_projection = dc_metadata["raster_projection"]
    raster_geotransform = dc_metadata["raster_geotransform"]

    # create the raster
    raster_output = driver.Create(
        file_output, raster_x_size, raster_y_size, 1, DC_GDAL_TYPES[dtype]
    )
    # Set the projection and geotransform of the new raster to match the original
    raster_output.SetProjection(raster_projection)
    raster_output.SetGeoTransform(raster_geotransform)
    # Write the new data to the new raster
    raster_output.GetRasterBand(n_band).WriteArray(grid_output)
    # Close
    raster_output = None
    return file_output
