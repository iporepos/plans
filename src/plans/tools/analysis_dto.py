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
import argparse
import os.path
import shutil
from pathlib import Path

# ... {develop}

# External imports
# =======================================================================
import numpy as np
import pandas as pd

# ... {develop}

# Project-level imports
# =======================================================================
from ..datasets import DTO, LDD, AOI, DC_NODATA
from ..geo import distance_to_outlet
from .core import Tool, ToolParser

# ... {develop}


# CLASSES
# ***********************************************************************

# CLASSES -- Module-level
# =======================================================================


class LocalParser(ToolParser):

    def __init__(self, parser):
        super().__init__(parser)

        # add extra arguments
        self.add_ldd()
        self.add_aoi()
        self.add_views()


class LocalTool(Tool):

    def __init__(self, folder_output):

        name = "plans.tools.dto"

        super().__init__(name=name, folder_output=folder_output)

        # overwrite base attributes
        self.sleeper = 0.5

        # setup new attributes
        self.file_ldd = None
        self.file_aoi = None

    def load_data(self):
        # handle ldd
        ldd = LDD(name=self.label)
        ldd.load_data(file_data=self.file_ldd)

        # handle basin
        basin = None
        if self.file_aoi is not None:
            basin = AOI(name=self.label)
            basin.load_data(file_data=self.file_aoi)

        self.loaded_data = {"ldd": ldd, "basin": basin}

        return None

    def process_data(self):
        self.processed_data = distance_to_outlet(
            grd_ldd=self.loaded_data["ldd"].data, n_res=self.loaded_data["ldd"].cellsize
        )
        return None

    def export_data(self):
        file_name_output = "dto"

        # setup output object
        dto = DTO(name=self.label)
        dto.data = self.processed_data.copy()
        dto.raster_metadata = self.loaded_data["ldd"].raster_metadata
        dto.raster_metadata["NODATA_value"] = DC_NODATA["float32"]

        # apply aoi mask
        if self.loaded_data["basin"] is not None:
            dto.apply_aoi_mask(grid_aoi=self.loaded_data["basin"].data, inplace=True)

        if self.views:
            dto.view_specs["folder"] = self.folder_output
            dto.view_specs["filename"] = file_name_output
            dto.view(show=False)

        file_output = dto.export_tif(
            folder=self.folder_output, filename=file_name_output
        )
        return None


# ... {develop}


# FUNCTIONS
# ***********************************************************************


def main():

    # parse arguments from cli
    # -------------------------------------------------------------------
    parser = argparse.ArgumentParser()
    p = LocalParser(parser)
    dc_args = p.get_args_as_dict()

    # instantiate tool
    # -------------------------------------------------------------------
    d = LocalTool(folder_output=dc_args["output"])

    # pass parameters
    # -------------------------------------------------------------------
    d.file_ldd = dc_args["ldd"]

    d.file_aoi = dc_args["aoi"]
    d.views = dc_args["views"]
    d.verbose = dc_args["verbose"]
    d.label = dc_args["label"]
    d.name_project = dc_args["project"]

    # run tool
    # -------------------------------------------------------------------
    d.run()

    return None


# ... {develop}

# SCRIPT
# ***********************************************************************
# standalone behaviour as a script


if __name__ == "__main__":

    # Call main
    # -------------------------------------------------------------------
    main()
