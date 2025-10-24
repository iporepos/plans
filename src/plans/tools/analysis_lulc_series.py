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
from ..datasets import LULCSeries, AOI
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
        self.add_attributes()
        self.add_scenario()
        self.add_aoi()
        self.add_views()


class LocalTool(Tool):

    def __init__(self, folder_output):

        name = "plans.tools.lulc_series"

        super().__init__(name=name, folder_output=folder_output)

        # overwrite base attributes
        self.sleeper = 0.5

        # setup new attributes
        self.file_lulc_attributes = None
        self.folder_lulc_scenario = None
        self.file_aoi = None

        self.name_pattern = "lulc_*"

    def load_data(self):
        msg = f"{self.label_loading} >>> {self.label} lulc maps ..."
        self.logger.info(msg)

        # setup
        lulc_series = LULCSeries(name=self.label)

        # load all files
        lulc_series.load_folder(
            folder=self.folder_lulc_scenario,
            file_table=self.file_lulc_attributes,
            name_pattern=self.name_pattern,
            verbose=self.verbose,
            logger=self.logger,
        )
        # handle basin
        aoi_map = None

        if self.file_aoi is not None:
            aoi_map = AOI(name=self.label)
            aoi_map.load_data(file_data=self.file_aoi)
            lulc_series.apply_aoi_masks(grid_aoi=aoi_map.data, inplace=True)

        # organize loaded data
        self.loaded_data = {"lulc_series": lulc_series, "aoi_map": aoi_map}

        return None

    def process_data(self):
        lulc_series = self.loaded_data["lulc_series"]
        df = lulc_series.get_series_areas()
        df.rename(columns={"id_raster": "id_lulc_raster"}, inplace=True)
        self.processed_data = df.copy()
        return None

    def export_data(self):

        lulc_series = self.loaded_data["lulc_series"]
        df = self.processed_data

        file_name_output = "lulc_series"
        file_output = Path(self.folder_output) / f"{file_name_output}.csv"

        msg = f"{self.label_exporting} >>> {self.label} {file_name_output}.csv"
        self.logger.info(msg)
        df.to_csv(file_output, sep=";", index=False)

        # handle views
        if self.views:
            # format titles
            for k in lulc_series.collection:
                dt = lulc_series.collection[k].datetime
                title = f"{self.label} | Land Use | {dt}"
                lulc_series.collection[k].view_specs["title"] = title

            # export views
            msg = f"{self.label_exporting} >>> {self.label} lulc map views ..."
            self.logger.info(msg)
            lulc_series.get_views(
                show=False,
                folder=self.folder_output,
                dpi=300,
                fig_format="jpg",
                talk=False,
                specs=None,
                suffix=None,
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

    d.file_lulc_attributes = dc_args["attributes"]
    d.folder_lulc_scenario = dc_args["scenario"]
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
