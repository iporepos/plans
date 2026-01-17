# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
Testing routines for the qutils.py module

.. warning::

    Run this script in the QGIS python environment


"""
# IMPORTS
# ***********************************************************************
# import modules from other libs

# Native imports
# =======================================================================
import inspect
from pathlib import Path
from pprint import pprint
import importlib.util as iu

# CONSTANTS
# ***********************************************************************
# ... {develop}

here = Path(__file__).resolve()
FOLDER_ROOT = here.parent.parent.parent
DATA_DIR = FOLDER_ROOT / "tests/data/biboca/data"
OUTPUT_DIR = FOLDER_ROOT / "tests/data/outputs"

# define the paths to this module
# ----------------------------------------
FILE_MODULE = f"{FOLDER_ROOT}/src/plans/qutils.py"

# setup module with importlib
# ----------------------------------------
IU_SPEC = iu.spec_from_file_location("module", FILE_MODULE)
MODULE = iu.module_from_spec(IU_SPEC)
IU_SPEC.loader.exec_module(MODULE)


# FUNCTIONS
# ***********************************************************************
# ... {develop}

# Tests
# -----------------------------------------------------------------------


def test_get_extent_from_raster():
    func_name = inspect.currentframe().f_code.co_name
    util_print_func_name(func_name)

    # setup inputs and outputs
    # ----------------------------------------
    file_input = f"{DATA_DIR}/topo/ldd.tif"

    # call the function
    # ----------------------------------------
    output = MODULE.get_extent_from_raster(file_input)

    print("Output:")
    pprint(output)

    # Assertions
    # ----------------------------------------
    try:
        assert isinstance(output, dict)
        print("test passed")
    except AssertionError:
        print("test failed")


def test_get_extent_from_vector():
    func_name = inspect.currentframe().f_code.co_name
    util_print_func_name(func_name)

    # define input and outputs
    # ----------------------------------------
    input_db = f"{DATA_DIR}/biboca.gpkg"
    layer_name = "roads"

    # call the function
    # ----------------------------------------
    output = MODULE.get_extent_from_vector(input_db=input_db, layer_name=layer_name)

    print("Output:")
    pprint(output)

    # Assertions
    # ----------------------------------------
    try:
        assert isinstance(output, dict)
        print("test passed")
    except AssertionError:
        print("test failed")


def test_count_vector_features():
    func_name = inspect.currentframe().f_code.co_name
    util_print_func_name(func_name)

    # define input and outputs
    # ----------------------------------------
    input_db = f"{DATA_DIR}/biboca.gpkg"
    layer_name = "roads"

    # call the function
    # ----------------------------------------
    output = MODULE.count_vector_features(input_db=input_db, layer_name=layer_name)

    print("Output:")
    pprint(output)

    # Assertions
    # ----------------------------------------
    try:
        assert isinstance(output, int)
        print("test passed")
    except AssertionError:
        print("test failed")


def test_get_hillshade():
    func_name = inspect.currentframe().f_code.co_name
    util_print_func_name(func_name)

    # define the path to input DEM
    # ----------------------------------------
    input_dem = f"{DATA_DIR}/topo/_src/dem.tif"

    # define the model parameters
    # ----------------------------------------
    solar_altitude = 90
    solar_azimuth = 270
    vertical_exaggeration = 4

    # define the model output
    # ----------------------------------------
    # [change this]
    s1 = str(solar_altitude).zfill(3)
    s2 = str(solar_azimuth).zfill(3)
    s3 = str(vertical_exaggeration).zfill(3)
    file_output = f"{OUTPUT_DIR}/hillshade_{s1}_{s2}_{s3}.tif"

    # call the function
    # ----------------------------------------
    output = MODULE.get_hillshade(
        file_dem=input_dem,
        file_output=file_output,
        solar_altitude=solar_altitude,
        solar_azimuth=solar_azimuth,
        vertical_exaggeration=vertical_exaggeration,
    )

    print("Output:")
    pprint(output)

    # Assertions
    # ----------------------------------------
    try:
        assert isinstance(output, str)
        print("test passed")
    except AssertionError:
        print("test failed")


# Utils
# -----------------------------------------------------------------------


def util_print_func_name(func_name):
    src_func_name = func_name.replace("test_", "")
    print(f"\n\ntest: qutils.{func_name}()")


# ... {develop}


# SCRIPT
# ***********************************************************************
# standalone behaviour as a script

test_get_extent_from_raster()
test_get_extent_from_vector()
test_count_vector_features()
test_get_hillshade()


# ... {develop}
