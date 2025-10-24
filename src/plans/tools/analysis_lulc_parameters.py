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

# ... {develop}

# External imports
# =======================================================================
import numpy as np
import pandas as pd

# ... {develop}

# Project-level imports
# =======================================================================
from ..datasets import LULCSeries, AOI, RasterCollection, SciRaster
from ..geo import downscale_parameter_to_units
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
        self.add_parameters()
        self.add_attributes()
        self.add_scenario()
        self.add_aoi()
        self.add_views()


class LocalTool(Tool):

    def __init__(self, folder_output):

        name = "plans.tools.analysis_lulc_parameters"

        super().__init__(name=name, folder_output=folder_output)

        # setup new attributes
        self.file_parameters = None
        self.file_attributes = None
        self.folder_scenario = None
        self.file_aoi = None

    def load_data(self):
        from .core import parse_spatial_parameters

        # list lulc parameters
        # ---------------------------------------------------------------
        msg = f"{self.label_loading} >>> parameters table ..."
        self.logger.info(msg)
        df_parameters = parse_spatial_parameters(
            title="Land Use Attributes", file_parameters=self.file_parameters
        )

        # load maps
        # ---------------------------------------------------------------
        msg = f"{self.label_loading} >>> lulc maps ..."
        self.logger.info(msg)
        lulc_series = LULCSeries(name=self.label)
        lulc_series.load_folder(
            folder=self.folder_scenario,
            file_table=self.file_attributes,
            name_pattern="lulc_*",
            verbose=self.verbose,
            logger=self.logger,
        )

        msg = f"{self.label_loading} >>> basin map ..."
        self.logger.info(msg)
        basin = AOI(name=self.label)
        basin.load_data(file_data=self.file_aoi)

        self.loaded_data = {
            "df_parameters": df_parameters,
            "lulc_series": lulc_series,
            "basin": basin,
        }

        return None

    def process_data(self):
        lulc_series = self.loaded_data["lulc_series"]
        df_values = self.loaded_data["df_parameters"]
        basin = self.loaded_data["basin"]

        # downscaling loop
        # ---------------------------------------------------------------
        parameters = RasterCollection()
        for k in lulc_series.collection:
            for row in df_values.to_dict(orient="records"):
                raster_name = f"{k}_{row['name']}"

                upscaled_value = row["value"]
                covar_table = (
                    lulc_series.collection[k].table[["id", row["field"]]].copy()
                )
                covar_table.rename(columns={"id": "v", row["field"]: "w"}, inplace=True)

                # downscale
                # -----------------------------------------------------------
                downscaled_map = downscale_parameter_to_units(
                    upscaled_value=row["value"],
                    units=lulc_series.collection[k].data,
                    basin=basin.data,
                    covariate_table=covar_table,
                    mode="mean",
                )

                # set-up
                # -----------------------------------------------------------
                self.logger.info(
                    f"processing >>> {self.label} building raster {raster_name} ..."
                )
                parameter = SciRaster(name=raster_name)
                parameter.alias = row["name"]
                parameter.varname = row["name"]
                parameter.varalias = row["name"]
                parameter.units = row["units"]
                parameter.description = row["description"]

                parameter.file_data = raster_name
                parameter.datetime = lulc_series.collection[k].datetime

                # inject data
                # -----------------------------------------------------------
                parameter.set_data(grid=downscaled_map)
                parameter.set_raster_metadata(
                    metadata=lulc_series.collection[k].raster_metadata
                )
                parameter.get_stats(inplace=True)
                parameter.update()

                # view specs
                # -----------------------------------------------------------
                s_title = f"{self.label} | {parameter.name} | {parameter.description} {parameter.units}"
                parameter.view_specs["title"] = s_title
                parameter.view_specs["cmap"] = "Oranges"
                parameter.view_specs["ylabel"] = parameter.units
                parameter.view_specs["range"] = [0, 1.1 * parameter.stats["max"]]
                parameter.view_specs["folder"] = self.folder_output
                parameter.view_specs["filename"] = raster_name

                # append
                # -----------------------------------------------------------
                parameters.append(new_object=parameter)

        self.processed_data = parameters
        return None

    def export_data(self):
        from .core import export_parameters

        export_parameters(
            folder_output=self.folder_output,
            parameters=self.processed_data,
            basin=self.loaded_data["basin"],
            views=self.views,
            prefix="lulc",
            label=self.label,
            logger=self.logger,
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
    d.file_parameters = dc_args["parameters"]
    d.file_attributes = dc_args["attributes"]
    d.folder_scenario = dc_args["scenario"]
    d.file_aoi = dc_args["aoi"]

    d.label = dc_args["label"]
    d.name_project = dc_args["project"]
    d.views = dc_args["views"]
    d.verbose = dc_args["verbose"]

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
