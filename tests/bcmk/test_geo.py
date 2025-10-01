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

 - {feature 1}
 - {feature 2}
 - {feature 3}
 - {etc}

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
import glob
import os.path

# IMPORTS
# ***********************************************************************
# import modules from other libs

# Native imports
# =======================================================================
import unittest
from pathlib import Path

import pandas as pd

# ... {develop}

# External imports
# =======================================================================
# ... {develop}

# Project-level imports
# =======================================================================
import plans
from plans.datasets import LULC, AOI, SciRaster
from plans import geo
from tests import conftest
from tests.conftest import RUN_BENCHMARKS, RUN_BENCHMARKS_XXL, testprint, DATA_DIR

# ... {develop}


# CONSTANTS
# ***********************************************************************
# ... {develop}


# FUNCTIONS
# ***********************************************************************
# ... {develop}


# CLASSES
# ***********************************************************************


@unittest.skipUnless(RUN_BENCHMARKS, reason="skipping benchmarks")
class TestGeo(unittest.TestCase):

    # Setup methods
    # -------------------------------------------------------------------
    @classmethod
    def setUpClass(cls):
        """
        Prepare project
        """
        cls.project = plans.load_project(str(DATA_DIR / "biboca"))
        cls.project.talk = True

    def test_downscaling(self):
        # load data
        file_data = Path(self.project.folder_lulc) / "mb01/lulc_2023-01-01.tif"
        file_table = Path(self.project.folder_lulc) / "mb01/lulc_attributes.csv"
        lulc = LULC(name=self.project.name, datetime="2023-01-01")
        lulc.load_data(file_data, file_table)
        # lulc.view(show=True)

        covar_table = lulc.table[["id", "w_ca"]].copy()
        covar_table.rename(columns={"id": "v", "w_ca": "w"}, inplace=True)
        print("\n")
        print(covar_table)

        file_data = Path(self.project.folder_basins) / "main/basin.tif"
        basin = AOI()
        basin.load_data(file_data)
        # basin.view()

        file_data = Path(self.project.folder_data) / "parameters_info.csv"
        df = pd.read_csv(file_data, sep=";")
        upscaled_value = df.loc[df["field"] == "ca", "value"].values[0]
        print(f"\n >>> Upscaled: {upscaled_value}")

        array_output = geo.downscale_parameter_to_units(
            upscaled_value=upscaled_value,
            units=lulc.data,
            basin=basin.data,
            covariate_table=covar_table,
        )
        raster_parameter = SciRaster()
        raster_parameter.view_specs["cmap"] = "Greens"
        raster_parameter.set_data(grid=array_output)
        raster_parameter.set_raster_metadata(metadata=basin.raster_metadata)
        print(raster_parameter.get_metadata_df())

        raster_parameter.view()

        raster_parameter.apply_aoi_mask(grid_aoi=basin.data, inplace=True)

        raster_parameter.view()

        pass


# ... {develop}


# SCRIPT
# ***********************************************************************
# standalone behaviour as a script
if __name__ == "__main__":
    from tests.conftest import RUN_BENCHMARKS

    # RESET BENCHMARKS
    RUN_BENCHMARKS = True

    # Script section
    # ===================================================================
    unittest.main()
    # ... {develop}
