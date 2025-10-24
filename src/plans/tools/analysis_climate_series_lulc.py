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

# ... {develop}

# External imports
# =======================================================================
import pandas as pd

# ... {develop}

# Project-level imports
# =======================================================================
from ..datasets import RainSeries, ETSeries, TimeSeries
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
        self.add_climate()
        self.add_lulc()
        self.add_views()


class LocalTool(Tool):

    def __init__(self, folder_output):

        name = "plans.tools.climate_series_lulc"

        super().__init__(name=name, folder_output=folder_output)

        # overwrite base attributes
        self.sleeper = 0.5

        # setup new attributes
        self.file_parameters = None
        self.file_climate_series = None
        self.file_lulc_series = None

    def load_data(self):
        df_params = pd.read_csv(self.file_parameters, sep=";")
        dt_value = df_params.loc[df_params["field"] == "dt", "value"].values[
            0
        ]  # Minutes

        ppt = RainSeries()
        ppt.load_data(
            file_data=self.file_climate_series,
            input_dtfield="datetime",
            input_varfield="ppt",
        )

        pet = ETSeries()
        pet.load_data(
            file_data=self.file_climate_series,
            input_dtfield="datetime",
            input_varfield="pet",
        )

        df_lulc = pd.read_csv(
            self.file_lulc_series, sep=";", parse_dates=[TimeSeries().dtfield]
        )
        df_lulc.drop_duplicates(subset="id_lulc_raster", inplace=True)

        self.loaded_data = {
            "dt_value": dt_value,
            "ppt": ppt,
            "pet": pet,
            "df_lulc": df_lulc,
        }

        return None

    def process_data(self):
        ppt = self.loaded_data["ppt"]
        pet = self.loaded_data["pet"]
        dt_value = self.loaded_data["dt_value"]
        df_lulc = self.loaded_data["df_lulc"]

        # downscale
        df_downscaled_ppt = ppt.downscale(freq=f"{dt_value}min")
        df_downscaled_pet = pet.downscale(freq=f"{dt_value}min")
        df_downscaled = pd.merge(
            left=df_downscaled_ppt, right=df_downscaled_pet, on="datetime", how="left"
        )
        df_downscaled["date"] = df_downscaled["datetime"].dt.strftime("%Y-%m-%d")

        # handle lulc
        df_lulc = df_lulc[["datetime", "id_lulc_raster"]].copy()

        df_lulc.rename(columns={"datetime": "date"}, inplace=True)
        df_lulc["date"] = df_lulc["date"].dt.strftime("%Y-%m-%d")

        # merge
        df_downscaled = pd.merge(
            left=df_downscaled, right=df_lulc, on="date", how="left"
        )
        # interpolate voids using nearest method
        df_downscaled["id_lulc_raster"] = df_downscaled["id_lulc_raster"].interpolate(
            method="nearest"
        )
        df_downscaled.drop(columns="date", inplace=True)
        df_downscaled.dropna(subset="id_lulc_raster", inplace=True)
        df_downscaled["id_lulc_raster"] = df_downscaled["id_lulc_raster"].astype(
            dtype="int16"
        )
        df_downscaled.reset_index(drop=True, inplace=True)

        self.logger.info(
            "processed data:\n\n{}\n...\n{}\n\n".format(
                df_downscaled.head(5).to_string(index=False),
                df_downscaled.tail(5).to_string(index=False),
            )
        )

        self.processed_data = df_downscaled
        return None

    def export_data(self):
        filename = f"climate_series_lulc_{self.label}.csv"
        file_out = self.folder_output / filename
        self.processed_data.to_csv(file_out, sep=";", index=False)
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
    d.file_climate_series = dc_args["climate"]
    d.file_lulc_series = dc_args["lulc"]

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
