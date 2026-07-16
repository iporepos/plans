# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
Core tool objects for the PLANS toolset.

This module provides the base building blocks shared by PLANS
command-line tools:

* :class:`ToolParser` -- a thin wrapper around :class:`argparse.ArgumentParser`
  that registers the arguments common to every PLANS tool and offers
  convenience methods to add tool-specific arguments.
* :class:`Tool` -- a base pipeline class implementing a generic
  ``load -> process -> export`` workflow, with per-step logging,
  elapsed-time tracking and a plain-text run report.
* :func:`parse_spatial_parameters` and :func:`export_parameters` -- helper
  functions to assemble and export spatialized parameter sets.

Features
--------

* Standardized CLI argument parsing shared across PLANS tools.
* A base tool pipeline handling logging, step timing and report generation.
* Helpers to parse spatial parameter tables and export parameter rasters,
  catalogs and figures.

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
    """Build a spatial parameters table for a given file type.

    Looks up the internal file name associated with ``title`` in the
    files specification table, selects the fields flagged for that file
    in the fields specification table, and merges them with the values
    provided in ``file_parameters`` to assemble a parameters table ready
    for spatialization.

    :param title: title of the target file, as registered in the files
        specification table (see :func:`plans.config.parse_files`).
    :type title: str
    :param file_parameters: path to the ``;``-separated CSV file holding
        the parameter values, with at least ``field`` and ``value``
        columns.
    :type file_parameters: str
    :return: table with columns ``field`` (prefixed with ``w_``), ``name``,
        ``value``, ``units`` and ``description`` for each parameter
        associated with the target file.
    :rtype: pandas.DataFrame
    """
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
    """Export a parameters catalog, raster maps and optional figures.

    Writes the parameters catalog to a CSV file and exports each
    parameter raster as a GeoTIFF. If ``views`` is enabled, also
    generates a figure for the full raster extent plus a second figure
    masked to the main basin extent.

    :param folder_output: output folder where files are written.
    :type folder_output: str or pathlib.Path
    :param parameters: parameters collection object exposing a ``catalog``
        (:class:`pandas.DataFrame`) and a ``collection`` mapping of raster
        objects (each exposing ``file_data``, ``export_tif``, ``view``,
        ``apply_aoi_mask`` and ``view_specs``).
    :type parameters: object
    :param basin: basin/raster object providing the ``data`` mask used to
        clip parameters to the main basin extent.
    :type basin: object
    :param views: whether to export figures in addition to the raster
        catalog.
    :type views: bool
    :param prefix: filename prefix for the parameters catalog file.
    :type prefix: str
    :param label: label used in log messages.
    :type label: str
    :param logger: logger instance used to report progress.
    :type logger: logging.Logger
    :return: ``None``
    :rtype: None
    """

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
    """Wrapper around :class:`argparse.ArgumentParser` for PLANS CLI tools.

    On instantiation, registers the arguments shared by every PLANS tool
    (``--output``, ``--verbose``, ``--label`` and ``--project``).
    Tool-specific arguments can be added afterwards through the ``add_*``
    methods (e.g. :meth:`add_parameters`, :meth:`add_climate`,
    :meth:`add_lulc`).

    :param parser: argument parser instance to configure.
    :type parser: argparse.ArgumentParser

    :ivar parser: the wrapped argument parser.
    :vartype parser: argparse.ArgumentParser
    :ivar output_default: default value shown for the ``--output`` argument.
    :vartype output_default: str
    """

    def __init__(self, parser):
        """Initialize the wrapper and register the base arguments.

        :param parser: argument parser instance to configure.
        :type parser: argparse.ArgumentParser
        """
        self.parser = parser
        self.output_default = "C:/data"

        # call basic arguments
        self.add_output_folder()
        self.add_verbose()
        self.add_label()
        self.add_project()

    def add_output_folder(self):
        """Register the required ``--output``/``-o`` output folder argument.

        :return: ``None``
        :rtype: None
        """
        self.parser.add_argument(
            "--output",
            "-o",
            required=True,
            default=self.output_default,
            action=None,
            help="Output folder",
        )

    def add_verbose(self):
        """Register the ``--verbose``/``-v`` console output flag.

        :return: ``None``
        :rtype: None
        """
        self.parser.add_argument(
            "--verbose",
            "-v",
            required=False,
            default=False,
            action="store_true",
            help="Console output",
        )

    def add_views(self):
        """Register the ``--views``/``-vs`` flag to enable plot exports.

        :return: ``None``
        :rtype: None
        """
        self.parser.add_argument(
            "--views",
            "-vs",
            required=False,
            default=False,
            action="store_true",
            help="Option for include plots",
        )

    def add_label(self):
        """Register the required ``--label``/``-lb`` utility label argument.

        :return: ``None``
        :rtype: None
        """
        self.parser.add_argument(
            "--label",
            "-lb",
            required=True,
            default="",
            action=None,
            help="Utility label",
        )

    def add_project(self):
        """Register the optional ``--project``/``-pro`` project name argument.

        :return: ``None``
        :rtype: None
        """
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
        """Register the required ``--parameters``/``-pr`` argument.

        Points to the file holding the simulation parameters.

        :return: ``None``
        :rtype: None
        """
        self.parser.add_argument(
            "--parameters",
            "-pr",
            required=True,
            default=None,
            action=None,
            help="File for simulation parameters",
        )

    def add_climate(self):
        """Register the required ``--climate``/``-cl`` argument.

        Points to the file holding the climate series.

        :return: ``None``
        :rtype: None
        """
        self.parser.add_argument(
            "--climate",
            "-cl",
            required=True,
            default=None,
            action=None,
            help="File for climate series",
        )

    def add_lulc(self):
        """Register the required ``--lulc``/``-lu`` argument.

        Points to the file holding the land use / land cover data.

        :return: ``None``
        :rtype: None
        """
        self.parser.add_argument(
            "--lulc",
            "-lu",
            required=True,
            default=None,
            action=None,
            help="File for climate series",
        )

    def add_ldd(self):
        """Register the required ``--ldd``/``-ld`` argument.

        Points to the LDD (flow direction) map file.

        :return: ``None``
        :rtype: None
        """
        self.parser.add_argument(
            "--ldd",
            "-ld",
            required=True,
            default=None,
            action=None,
            help="File for LDD map file",
        )

    def add_aoi(self):
        """Register the optional ``--aoi``/``-a`` argument.

        Points to the area-of-interest (AOI) map file.

        :return: ``None``
        :rtype: None
        """
        self.parser.add_argument(
            "--aoi",
            "-a",
            required=False,
            default=None,
            action=None,
            help="File for AOI map",
        )

    def add_attributes(self):
        """Register the required ``--attributes``/``-att`` argument.

        Points to the attributes table file.

        :return: ``None``
        :rtype: None
        """
        self.parser.add_argument(
            "--attributes",
            "-att",
            required=True,
            default=None,
            action=None,
            help="File for attributes table",
        )

    def add_scenario(self):
        """Register the required ``--scenario``/``-scn`` argument.

        Points to the scenario folder.

        :return: ``None``
        :rtype: None
        """
        self.parser.add_argument(
            "--scenario",
            "-scn",
            required=True,
            default=None,
            action=None,
            help="Folder for scenario",
        )

    def add_soils(self):
        """Register the required ``--soils``/``-so`` argument.

        Points to the soils map file.

        :return: ``None``
        :rtype: None
        """
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
        """Parse and return the command-line arguments.

        :return: parsed arguments namespace.
        :rtype: argparse.Namespace
        """
        return self.parser.parse_args()

    def get_args_as_dict(self):
        """Parse the command-line arguments and return them as a dictionary.

        :return: mapping of argument destination names to parsed values.
        :rtype: dict
        """
        return vars(self.parser.parse_args())


class Tool:
    """Base class for PLANS command-line processing tools.

    Implements a generic ``load -> process -> export`` pipeline with
    per-step logging, elapsed-time tracking and a plain-text run report
    (log echo preceded by a specs and runtimes header). Subclasses are
    expected to override :meth:`load_data`, :meth:`process_data` and
    :meth:`export_data` with their actual logic.

    :param name: name of the tool, used in log messages and the report header.
    :type name: str
    :param folder_output: output folder where logs, report and runtime
        files are written. Created if it does not already exist.
    :type folder_output: str or pathlib.Path

    :ivar name: tool name.
    :vartype name: str
    :ivar folder_output: output folder for this run.
    :vartype folder_output: pathlib.Path
    :ivar file_logs: path to the raw log file.
    :vartype file_logs: pathlib.Path
    :ivar file_report: path to the final assembled report file.
    :vartype file_report: pathlib.Path
    :ivar logger: logger used by the tool, set via :meth:`set_logger`.
    :vartype logger: logging.Logger or None
    :ivar verbose: whether the logger also writes to the console.
    :vartype verbose: bool
    :ivar views: whether the tool should also export figures.
    :vartype views: bool
    :ivar label: utility label for this run.
    :vartype label: str
    :ivar name_project: optional project name, included in the logger name.
    :vartype name_project: str or None
    :ivar runtimes: table of step runtimes, set by :meth:`export_runtimes`.
    :vartype runtimes: pandas.DataFrame or None
    :ivar sleeper: seconds slept by the default pipeline steps.
    :vartype sleeper: float
    """

    # Dunder methods
    # -------------------------------------------------------------------
    def __init__(self, name, folder_output):
        """Initialize the tool and create the output folder.

        :param name: name of the tool, used in log messages and the
            report header.
        :type name: str
        :param folder_output: output folder where logs, report and
            runtime files are written. Created if it does not already
            exist.
        :type folder_output: str or pathlib.Path
        """

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
        """Instantiate and assign the tool's logger.

        Builds the logger name from :attr:`name` (and :attr:`name_project`,
        when set) and assigns the result to :attr:`logger` via
        :meth:`get_logger`.

        :return: ``None``
        :rtype: None
        """

        name_logger = self.name

        if self.name_project is not None:
            name_logger = "{} @ {}".format(name_logger, self.name_project)

        self.logger = Tool.get_logger(
            name=name_logger, log_file=self.file_logs, talk=self.verbose
        )

    # Main tool method
    # -------------------------------------------------------------------
    def run(self):
        """Execute the full tool pipeline.

        Ensures a logger is set, then runs :meth:`load_data`,
        :meth:`process_data` and :meth:`export_data` in sequence (each
        wrapped by :meth:`step` for logging and timing). Afterwards,
        exports the runtimes table, logs the total elapsed time and the
        output location, and writes the final report file via
        :meth:`make_readme_file`.

        :return: ``None``
        :rtype: None
        """

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
        """Run a single pipeline step with logging and timing.

        Logs the start of the step, executes ``method``, logs its
        completion with the elapsed time, and appends the step label and
        elapsed time to :attr:`ls_steps` and :attr:`ls_times`.

        :param method: no-argument callable implementing the step
            (e.g. :meth:`load_data`).
        :type method: callable
        :param label: step label, used for logging and as the key into
            ``self.msg["concluded"]``.
        :type label: str
        :return: ``None``
        :rtype: None
        """
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
        """Load input data.

        Placeholder implementation that only sleeps for :attr:`sleeper`
        seconds. Subclasses should override this method with actual
        data-loading logic.

        :return: ``None``
        :rtype: None
        """
        self.sleep()
        return None

    def process_data(self):
        """Process previously loaded data.

        Placeholder implementation that only sleeps for :attr:`sleeper`
        seconds. Subclasses should override this method with actual
        processing logic.

        :return: ``None``
        :rtype: None
        """
        self.sleep()
        return None

    def export_data(self):
        """Export processed data.

        Placeholder implementation that only sleeps for :attr:`sleeper`
        seconds. Subclasses should override this method with actual
        export logic.

        :return: ``None``
        :rtype: None
        """
        self.sleep()
        return None

    def export_runtimes(self):
        """Build and export the runtimes table.

        Assembles a table with one row per executed step plus a
        ``total`` row, computes each step's percentage share of the
        total elapsed time, writes it to :attr:`filename_runtimes`
        inside :attr:`folder_output`, and stores the result in
        :attr:`runtimes`.

        :return: ``None``
        :rtype: None
        """
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
        """Format the runtimes table as a fixed-width text block.

        :return: column-aligned, uppercase-headed string representation
            of :attr:`runtimes`, rounded to three decimal places.
        :rtype: str
        """
        df_str = self.runtimes.round(3).map(lambda x: f"{x:<10}")
        new_cols = [f"{c.upper():<10}" for c in df_str.columns]
        df_str.columns = new_cols
        return df_str.to_string(index=False)

    # todo develop and make DRY
    def make_readme_file(self):
        """Assemble the final run report file.

        Reads the raw log file, prepends a header block (title, run
        specs and formatted runtimes table), and writes the combined
        content to :attr:`file_report`.

        :return: ``None``
        :rtype: None
        """
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
        """Pause execution for :attr:`sleeper` seconds.

        Used as a placeholder delay by the default :meth:`load_data`,
        :meth:`process_data` and :meth:`export_data` implementations.

        :return: ``None``
        :rtype: None
        """
        time.sleep(self.sleeper)

    # Static methods
    # -------------------------------------------------------------------
    @staticmethod
    def format_msg_elapsed(msg, time):
        """Format a message with an elapsed-time suffix.

        :param msg: base message.
        :type msg: str
        :param time: elapsed time, in seconds.
        :type time: float
        :return: formatted message, e.g. ``"<msg> in 1.23 seconds"``.
        :rtype: str
        """
        return "{} in {:.2f} seconds".format(msg, time)

    @staticmethod
    def format_msg_output(folder):
        """Format a message pointing the user to an output folder.

        :param folder: output folder path to display.
        :type folder: str or pathlib.Path
        :return: formatted message.
        :rtype: str
        """
        return "check results in:\n\n\t{}\n".format(folder)

    @staticmethod
    def get_logger(name="tool", log_file="run_log.txt", talk=True):
        """Create (or reconfigure) a :class:`logging.Logger`.

        Clears any handlers already attached to a logger of the same
        name, then attaches a file handler (always) and, when ``talk``
        is ``True``, a console handler as well. Both handlers share a
        timestamped ``DEBUG``-level format that includes the logger
        name.

        :param name: logger name.
        :type name: str
        :param log_file: path to the log file to write to.
        :type log_file: str or pathlib.Path
        :param talk: whether to also emit log records to the console.
        :type talk: bool
        :return: configured logger instance, set to ``DEBUG`` level.
        :rtype: logging.Logger
        """
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
