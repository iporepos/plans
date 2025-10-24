# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
Core tool objects

Features
--------
todo docstring

* {feature 1}
* {feature 2}
* {feature 3}
* {etc}

"""


# IMPORTS
# ***********************************************************************
# import modules from other libs

# Native imports
# =======================================================================
import os
import time
import logging
from pathlib import Path

# ... {develop}

# External imports
# =======================================================================
import pandas as pd

# ... {develop}

# Project imports
# =======================================================================
from plans.config import parse_files, parse_fields


# FUNCTIONS
# ***********************************************************************

# FUNCTIONS -- Project-level
# =======================================================================


def parse_spatial_parameters(title, file_parameters):
    # todo docstring
    df_files = parse_files()
    file_name = df_files.loc[df_files["title"] == title, "name"].values[0]

    df_fields = parse_fields()
    df_fields = df_fields.query(f"{file_name} == 'w'").copy()
    ls_parameters = list(df_fields["name"].values)

    ls_fields_parameters = ["w_{}".format(p) for p in ls_parameters]

    # get parameter set
    # ---------------------------------------------------------------
    df_params = pd.read_csv(file_parameters, sep=";")
    df_params_filter = df_params[df_params["field"].isin(ls_parameters)]
    ls_upscaled_values = list(df_params_filter["value"])

    df_parameters = pd.DataFrame(
        {
            "field": ls_fields_parameters,
            "name": ls_parameters,
            "value": ls_upscaled_values,
            "units": list(df_fields["units"].values),
            "description": list(df_fields["description"].values),
        }
    )
    return df_parameters


def export_parameters(folder_output, parameters, basin, views, prefix, label, logger):
    # todo docstring

    # export catalog
    # ---------------------------------------------------------------
    # todo docs -- add this file output index
    file_catalog = Path(folder_output) / f"{prefix}_parameters_catalog.csv"
    parameters.catalog.to_csv(file_catalog, sep=";", index=False)

    # export rasters
    # ---------------------------------------------------------------
    for k in parameters.collection:
        filename = parameters.collection[k].file_data
        logger.info(f"exporting maps >>> {label} {filename}.tif")
        parameters.collection[k].export_tif(folder=folder_output, filename=filename)

    # export views
    # ---------------------------------------------------------------
    if views:
        for k in parameters.collection:

            filename = parameters.collection[k].file_data
            logger.info(f"exporting figs >>> {label} {filename}.jpg")
            parameters.collection[k].view(show=False)
            parameters.collection[k].apply_aoi_mask(grid_aoi=basin.data)

            # mask by main basin
            filename2 = f"{filename}_main"
            logger.info(f"exporting figs >>> {label} {filename2}.jpg")
            s_title = parameters.collection[k].view_specs["title"]
            parameters.collection[k].view_specs["title"] = f"{s_title} | main basin"
            parameters.collection[k].view_specs["filename"] = filename2
            parameters.collection[k].view(show=False)

    return None


# CLASSES
# ***********************************************************************

# CLASSES -- Project-level
# =======================================================================


class ToolParser:
    # todo docstring

    def __init__(self, parser):
        self.parser = parser
        self.output_default = "C:/data"

        # call basic arguments
        self.add_output_folder()
        self.add_verbose()
        self.add_label()
        self.add_project()

    def add_output_folder(self):
        self.parser.add_argument(
            "--output",
            "-o",
            required=True,
            default=self.output_default,
            action=None,
            help="Output folder",
        )

    def add_verbose(self):
        self.parser.add_argument(
            "--verbose",
            "-v",
            required=False,
            default=False,
            action="store_true",
            help="Console output",
        )

    def add_views(self):
        self.parser.add_argument(
            "--views",
            "-vs",
            required=False,
            default=False,
            action="store_true",
            help="Option for include plots",
        )

    def add_label(self):
        self.parser.add_argument(
            "--label",
            "-lb",
            required=True,
            default="",
            action=None,
            help="Utility label",
        )

    def add_project(self):
        self.parser.add_argument(
            "--project",
            "-pro",
            required=False,
            default="",
            action=None,
            help="Project name",
        )

    # extra arguments

    def add_parameters(self):
        self.parser.add_argument(
            "--parameters",
            "-pr",
            required=True,
            default=None,
            action=None,
            help="File for simulation parameters",
        )

    def add_climate(self):
        self.parser.add_argument(
            "--climate",
            "-cl",
            required=True,
            default=None,
            action=None,
            help="File for climate series",
        )

    def add_lulc(self):
        self.parser.add_argument(
            "--lulc",
            "-lu",
            required=True,
            default=None,
            action=None,
            help="File for climate series",
        )

    def add_ldd(self):
        self.parser.add_argument(
            "--ldd",
            "-ld",
            required=True,
            default=None,
            action=None,
            help="File for LDD map file",
        )

    def add_aoi(self):
        self.parser.add_argument(
            "--aoi",
            "-a",
            required=False,
            default=None,
            action=None,
            help="File for AOI map",
        )

    def add_attributes(self):
        self.parser.add_argument(
            "--attributes",
            "-att",
            required=True,
            default=None,
            action=None,
            help="File for attributes table",
        )

    def add_scenario(self):
        self.parser.add_argument(
            "--scenario",
            "-scn",
            required=True,
            default=None,
            action=None,
            help="Folder for scenario",
        )

    def add_soils(self):
        self.parser.add_argument(
            "--soils",
            "-so",
            required=True,
            default=None,
            action=None,
            help="File for Soils map",
        )

    # get methods
    def get_args(self):
        return self.parser.parse_args()

    def get_args_as_dict(self):
        return vars(self.parser.parse_args())


class Tool:
    # todo docstring

    # Dunder methods
    # -------------------------------------------------------------------
    def __init__(self, name, folder_output):

        # setup basic attributes
        # ---------------------------------------------------------------
        self.name = name
        self.folder_output = Path(folder_output)
        os.makedirs(self.folder_output, exist_ok=True)
        self.file_logs = self.folder_output / "logs.txt"
        # todo develop robust options for report (e.g., md, html, tex, etc)
        self.file_report = self.folder_output / "report.txt"
        self.logger = None
        self.verbose = True
        self.views = True
        self.label = ""
        self.name_project = None

        self.loaded_data = None
        self.processed_data = None

        # setup strings
        # ---------------------------------------------------------------
        # labels
        self.label_starting = "starting"
        self.label_loading = "loading"
        self.label_processing = "processing"
        self.label_exporting = "exporting"
        self.label_run = "run"
        self.label_project = "project"
        self.label_results = "results available at:"

        self.msg = {
            "concluded": {
                self.label_loading: "loaded inputs",
                self.label_processing: "processed data",
                self.label_exporting: "exported outputs",
                self.label_run: "run completed",
            }
        }

        # setup lists
        # ---------------------------------------------------------------
        self.ls_steps = list()
        self.ls_times = list()

        # misc
        # ---------------------------------------------------------------
        self.runtimes = None
        self.filename_runtimes = "runtimes.csv"

        # setup lists
        # ---------------------------------------------------------------
        self.sleeper = 1.2

    # Set methods
    # -------------------------------------------------------------------
    def set_logger(self):

        name_logger = self.name

        if self.name_project is not None:
            name_logger = "{} @ {}".format(name_logger, self.name_project)

        self.logger = Tool.get_logger(
            name=name_logger, log_file=self.file_logs, talk=self.verbose
        )

    # Main tool method
    # -------------------------------------------------------------------
    def run(self):

        # setups
        # ---------------------------------------------------------------
        if self.logger is None:
            self.set_logger()

        # starting
        # ---------------------------------------------------------------
        self.logger.info(self.label_starting)

        # main steps
        # ---------------------------------------------------------------
        self.step(method=self.load_data, label=self.label_loading)

        self.step(method=self.process_data, label=self.label_processing)

        self.step(method=self.export_data, label=self.label_exporting)

        # concluding
        # ---------------------------------------------------------------

        self.export_runtimes()

        msg = self.msg["concluded"][self.label_run]
        total = self.runtimes["elapsed"].values[0]
        self.logger.info(Tool.format_msg_elapsed(msg, total))

        msg = f"{self.label_results}\n\n\t{self.folder_output}\n\n"
        self.logger.info(msg)

        self.make_readme_file()

        return None

    # Wrapper methods
    # -------------------------------------------------------------------
    def step(self, method, label):
        # start
        # ---------------------------------------------------------------
        start = time.time()
        msg = f"{label} ..."
        self.logger.info(msg)

        # execution
        # ---------------------------------------------------------------
        method()

        # conclusion
        # ---------------------------------------------------------------
        elapsed = time.time() - start
        msg = Tool.format_msg_elapsed(self.msg["concluded"][label], elapsed)
        self.logger.info(msg)

        # document
        # ---------------------------------------------------------------
        self.ls_steps.append(label)
        self.ls_times.append(elapsed)

        return None

    # Data main methods
    # -------------------------------------------------------------------
    def load_data(self):
        self.sleep()
        return None

    def process_data(self):
        self.sleep()
        return None

    def export_data(self):
        self.sleep()
        return None

    def export_runtimes(self):
        df1 = pd.DataFrame({"step": self.ls_steps[:], "elapsed": self.ls_times[:]})

        df2 = pd.DataFrame({"step": ["total"], "elapsed": df1["elapsed"].sum()})

        df = pd.concat([df2, df1]).reset_index(drop=True)
        df["elapsed_p"] = 100 * df["elapsed"] / df1["elapsed"].sum()
        df["elapsed_p"] = df["elapsed_p"].round(2)

        f = self.folder_output / self.filename_runtimes
        df.to_csv(f, sep=";", index=False)
        self.runtimes = df
        return None

    def format_runtimes_str(self):
        df_str = self.runtimes.round(3).map(lambda x: f"{x:<10}")
        new_cols = [f"{c.upper():<10}" for c in df_str.columns]
        df_str.columns = new_cols
        return df_str.to_string(index=False)

    # todo develop and make DRY
    def make_readme_file(self):
        # read current
        # ---------------------------------------------------------------
        with open(self.file_logs, "r") as file:
            lines = file.readlines()
            file.close()

        ls_header = list()

        # setup header
        # ---------------------------------------------------------------
        ls_header.append("")
        ls_header.append("")
        ls_header.append("PLANS --- Planning Nature-based Solutions".upper())
        ls_header.append("#" * 60)
        ls_header.append("")
        ls_header.append("")

        # tool specs
        # ---------------------------------------------------------------
        ls_header.append("")
        ls_header.append("SPECS".upper())
        ls_header.append("=" * 60)
        ls_header.append("")
        ls_header.append(f"Project: {self.name_project}")
        ls_header.append(f"Tool: {self.name}")
        ls_header.append(f"Output folder: {self.folder_output}")

        # runtimes
        # ---------------------------------------------------------------
        ls_header.append("")
        ls_header.append("RUNTIMES".upper())
        ls_header.append("=" * 60)
        ls_header.append("")
        ls_header.append(self.format_runtimes_str())
        ls_header.append("")

        # logs
        # ---------------------------------------------------------------
        ls_header.append("")
        ls_header.append("LOGS".upper())
        ls_header.append("=" * 60)
        ls_header.append("")
        ls_header.append("DATETIME                | LEVEL    | MESSAGE")

        # write back
        # ---------------------------------------------------------------
        ls_header = [line + "\n" for line in ls_header]
        ls_full = ls_header + lines
        with open(self.file_report, "w") as file:
            file.writelines(ls_full)
            file.close()
        return None

    # Util methods
    # -------------------------------------------------------------------
    def sleep(self):
        time.sleep(self.sleeper)

    # Static methods
    # -------------------------------------------------------------------
    @staticmethod
    def format_msg_elapsed(msg, time):
        return "{} in {:.2f} seconds".format(msg, time)

    @staticmethod
    def format_msg_output(folder):
        return "check results in:\n\n\t{}\n".format(folder)

    @staticmethod
    def get_logger(name="tool", log_file="run_log.txt", talk=True):
        # Create the logger
        # -------------------------------------------------------------------
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)  # capture all levels

        # Prevent duplicated handlers when re-calling get_logger
        # -------------------------------------------------------------------
        if logger.hasHandlers():
            logger.handlers.clear()

        # Format
        # -------------------------------------------------------------------
        log_format = logging.Formatter(
            fmt=f"%(asctime)s.%(msecs)03d | %(levelname)-8s | {name} >>> %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # console handler
        # -------------------------------------------------------------------
        if talk:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(log_format)
            logger.addHandler(console_handler)

        # file handler
        # -------------------------------------------------------------------
        file_handler = logging.FileHandler(log_file, mode="w")
        file_handler.setFormatter(log_format)
        logger.addHandler(file_handler)

        return logger


# SCRIPT
# ***********************************************************************
# standalone behaviour as a script
if __name__ == "__main__":

    # Script section
    # ===================================================================
    print("Hello world!")
    # ... {develop}
