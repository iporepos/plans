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
import time, logging
from pathlib import Path
import argparse

# ... {develop}

# External imports
# =======================================================================
import pandas as pd

# ... {develop}

# Project-level imports
# =======================================================================
from plans.datasets import DC_NODATA

# ... {develop}


# CONSTANTS
# ***********************************************************************
# define constants in uppercase

# CONSTANTS -- Project-level
# =======================================================================
# ... {develop}

# CONSTANTS -- Module-level
# =======================================================================
logger = logging.getLogger(__name__)
LABEL_LOADING = "loading"
LABEL_PROCESSING = "processing"
LABEL_EXPORTING = "exporting"
LABEL_RUN = "run"

DC_MSG = {
    LABEL_LOADING: "loaded inputs",
    LABEL_PROCESSING: "processed data",
    LABEL_EXPORTING: "exported outputs",
    LABEL_RUN: "run completed",
}
# ... {develop}


# FUNCTIONS
# ***********************************************************************

# FUNCTIONS -- utilities
# =======================================================================


def setup_logger(label, talk):
    s = "%(asctime)s [%(levelname)s] plans.tools.{}: %(message)s".format(label)
    logging.basicConfig(level=logging.INFO, format=s)
    logger.setLevel(logging.INFO if talk else logging.WARNING)


# step decorator
def step(label):
    def decorator(func):
        def wrapper(*args, **kwargs):
            start = time.time()
            logger.info(f"{label} ...")

            result = func(*args, **kwargs)  # <--- your unique protocol here

            elapsed = time.time() - start
            logger.info(format_msg_elapsed(DC_MSG[label], elapsed))
            return result, elapsed

        return wrapper

    return decorator


def format_msg_elapsed(msg, time):
    return "{} in {:.2f} seconds".format(msg, time)


def save_runtime_data(steps, times, folder_output):
    df_run = pd.DataFrame({"step": steps, "time": times})
    file_output_runtimes = Path(folder_output) / "runtimes.csv"
    df_run.to_csv(file_output_runtimes, sep=";", index=False)
    return file_output_runtimes


# FUNCTIONS -- Project-level
# =======================================================================


def demo(file_input1, file_input2, folder_output, talk):
    # todo docstring
    # LOGGING
    # -------------------------------------------------------------------
    tool_name = demo.__name__
    setup_logger(label=tool_name, talk=talk)

    # DEFINE PROTOCOLS
    # -------------------------------------------------------------------
    @step(LABEL_LOADING)
    def load_inputs(f1, f2):
        df1 = pd.read_csv(f1)
        df2 = pd.read_csv(f2)
        time.sleep(1)
        return df1, df2

    @step(LABEL_PROCESSING)
    def process_data(df1, df2):
        time.sleep(3)
        return pd.concat([df1, df2])

    @step(LABEL_EXPORTING)
    def export_data(df, folder):
        time.sleep(2)
        file_out = Path(folder) / "demo_output.csv"
        df.to_csv(file_out, sep=";", index=False)
        return file_out

    # START UP
    # -------------------------------------------------------------------
    start_total = time.time()
    ls_steps, ls_times = [], []

    # LOADING INPUTS
    # -------------------------------------------------------------------
    (df1, df2), t = load_inputs(file_input1, file_input2)

    ls_steps.append(LABEL_LOADING)
    ls_times.append(t)

    # PROCESSING DATA
    # -------------------------------------------------------------------
    df_out, t = process_data(df1, df2)

    ls_steps.append(LABEL_PROCESSING)
    ls_times.append(t)

    # EXPORTING OUTPUTS
    # -------------------------------------------------------------------
    file_out, t = export_data(df_out, folder_output)

    ls_steps.append(LABEL_EXPORTING)
    ls_times.append(t)

    # SHUTDOWN
    # -------------------------------------------------------------------
    total_elapsed = time.time() - start_total
    logger.info(format_msg_elapsed(DC_MSG[LABEL_RUN], total_elapsed))

    # record it in your steps/times lists
    ls_steps.append(LABEL_RUN)
    ls_times.append(total_elapsed)

    # Save all runtime data including total
    runtimes_file = save_runtime_data(
        steps=ls_steps, times=ls_times, folder_output=folder_output
    )
    return True


def analysis_dto(file_ldd, file_basin, folder_output, label, views, talk):
    # todo docstring
    from plans.datasets import Raster, LDD, DTO, AOI
    from plans.geo import distance_to_outlet

    # LOGGING
    # -------------------------------------------------------------------
    tool_name = analysis_dto.__name__
    setup_logger(label=tool_name, talk=talk)

    # DEFINE PROTOCOLS
    # -------------------------------------------------------------------
    @step(LABEL_LOADING)
    def load_inputs(file_ldd, file_basin):
        # handle ldd
        ldd = LDD(name=label)
        ldd.load_data(file_data=file_ldd)

        # handle basin
        basin = None
        if file_basin is not None:
            basin = AOI(name=label)
            basin.load_data(file_data=file_basin)

        return ldd, basin

    @step(LABEL_PROCESSING)
    def process_data(ldd):
        grd_outdist = distance_to_outlet(grd_ldd=ldd.data, n_res=ldd.cellsize)
        return grd_outdist

    @step(LABEL_EXPORTING)
    def export_data(ldd, basin, grd_outdist):
        file_name_output = "dto"
        # setup output object
        dto = DTO(name=label)
        dto.data = grd_outdist.copy()
        dto.raster_metadata = ldd.raster_metadata
        dto.raster_metadata["NODATA_value"] = DC_NODATA["float32"]

        # apply aoi mask
        if basin is not None:
            dto.apply_aoi_mask(grid_aoi=basin.data, inplace=True)

        if views:
            dto.view_specs["folder"] = folder_output
            dto.view_specs["filename"] = file_name_output
            dto.view(show=False)
        file_output = dto.export_tif(folder=folder_output, filename=file_name_output)
        return file_output

    # START UP
    # -------------------------------------------------------------------
    start_total = time.time()
    ls_steps, ls_times = [], []

    # LOADING INPUTS
    # -------------------------------------------------------------------
    (ldd, basin), t = load_inputs(file_ldd, file_basin)

    ls_steps.append(LABEL_LOADING)
    ls_times.append(t)

    # PROCESSING DATA
    # -------------------------------------------------------------------
    grd_outdist, t = process_data(ldd)

    ls_steps.append(LABEL_EXPORTING)
    ls_times.append(t)

    # EXPORTING OUTPUTS
    # -------------------------------------------------------------------
    file_output, t = export_data(ldd, basin, grd_outdist)

    ls_steps.append(LABEL_EXPORTING)
    ls_times.append(t)

    # SHUTDOWN
    # -------------------------------------------------------------------
    total_elapsed = time.time() - start_total
    logger.info(format_msg_elapsed(DC_MSG[LABEL_RUN], total_elapsed))

    # record it in your steps/times lists
    ls_steps.append(LABEL_RUN)
    ls_times.append(total_elapsed)

    # Save all runtime data including total
    runtimes_file = save_runtime_data(
        steps=ls_steps, times=ls_times, folder_output=folder_output
    )
    return True


def analysis_lulc_series(
    file_lulc, folder_lulc, file_aoi, folder_output, label, views, talk
):
    # todo docstring
    from plans.datasets import Raster, LULCSeries, AOI

    # LOGGING
    # -------------------------------------------------------------------
    tool_name = analysis_lulc_series.__name__
    setup_logger(label=tool_name, talk=talk)

    # DEFINE PROTOCOLS
    # -------------------------------------------------------------------
    @step(LABEL_LOADING)
    def load_inputs(file_lulc, folder_lulc, file_aoi):
        # handle ldd
        lulc_series = LULCSeries(name=label)
        lulc_series.load_folder(
            folder=folder_lulc, file_table=file_lulc, name_pattern="lulc_*", talk=True
        )

        # handle basin
        aoi_map = None
        if file_aoi is not None:
            aoi_map = AOI(name=label)
            aoi_map.load_data(file_data=file_aoi)
            lulc_series.apply_aoi_masks(grid_aoi=aoi_map.data, inplace=True)

        return lulc_series, aoi_map

    @step(LABEL_PROCESSING)
    def process_data(lulc_series):
        print("hello")
        print(lulc_series.catalog.info())
        for k in lulc_series.collection:
            lulc_series.collection[k].view(show=True)

        df = lulc_series.get_series_areas()
        return df

    @step(LABEL_EXPORTING)
    def export_data(df):
        file_name_output = "lulc_series"
        print(df.info())
        print(df.head())
        time.sleep(1)
        return None

    # START UP
    # -------------------------------------------------------------------
    start_total = time.time()
    ls_steps, ls_times = [], []

    # LOADING INPUTS
    # -------------------------------------------------------------------
    (lulc_series, aoi_map), t = load_inputs(file_lulc, folder_lulc, file_aoi)

    ls_steps.append(LABEL_LOADING)
    ls_times.append(t)

    # PROCESSING DATA
    # -------------------------------------------------------------------
    df, t = process_data(lulc_series)

    ls_steps.append(LABEL_EXPORTING)
    ls_times.append(t)

    # EXPORTING OUTPUTS
    # -------------------------------------------------------------------
    file_output, t = export_data(df)

    ls_steps.append(LABEL_EXPORTING)
    ls_times.append(t)

    # SHUTDOWN
    # -------------------------------------------------------------------
    total_elapsed = time.time() - start_total
    logger.info(format_msg_elapsed(DC_MSG[LABEL_RUN], total_elapsed))

    # record it in your steps/times lists
    ls_steps.append(LABEL_RUN)
    ls_times.append(total_elapsed)

    # Save all runtime data including total
    runtimes_file = save_runtime_data(
        steps=ls_steps, times=ls_times, folder_output=folder_output
    )
    return True


def func2(path: str, flag: bool):
    print(f"func2 running: path={path}, flag={flag}")


# ... {develop}

# FUNCTIONS -- Module-level
# =======================================================================
# ... {develop}


def main():
    parser = argparse.ArgumentParser(description="Tools runner")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- demo
    parser_demo = subparsers.add_parser("demo", help="Run demo()")
    parser_demo.add_argument("--input1", required=True, help="Input file path")
    parser_demo.add_argument("--input2", required=True, help="Input file path")
    parser_demo.add_argument("--folder", required=True, help="Output folder path")
    parser_demo.add_argument("--talk", action="store_true")  # flag

    # --- dto
    parser_dto = subparsers.add_parser("analysis_dto", help="Run dto()")
    parser_dto.add_argument("--ldd", required=True, help="path to ldd.tif map")
    parser_dto.add_argument(
        "--basin", required=False, help="path to basin.tif map", default=None
    )
    parser_dto.add_argument("--folder", required=True, help="path to output folder")
    parser_dto.add_argument("--label", required=True, help="Label")
    parser_dto.add_argument("--views", action="store_true")  # flag
    parser_dto.add_argument("--talk", action="store_true")  # flag

    # --- lulc series
    parser_dto = subparsers.add_parser(
        "analysis_lulc_series", help="Analysis of LULC series"
    )
    parser_dto.add_argument(
        "--attributes", required=True, help="path to lulc_attributes csv"
    )
    parser_dto.add_argument("--scenario", required=True, help="path to lulc map folder")
    parser_dto.add_argument(
        "--basin", required=False, help="path to basin.tif map", default=None
    )
    parser_dto.add_argument("--folder", required=True, help="path to output folder")
    parser_dto.add_argument("--label", required=True, help="Label")
    parser_dto.add_argument("--views", action="store_true")  # flag
    parser_dto.add_argument("--talk", action="store_true")  # flag

    # --- func2
    parser_f2 = subparsers.add_parser("func2", help="Run func2")
    parser_f2.add_argument("--path", required=True, help="Path to folder")
    parser_f2.add_argument("--flag", action="store_true", help="Enable optional flag")

    args = parser.parse_args()

    if args.command == "demo":
        demo(args.input1, args.input2, args.folder, args.talk)
    elif args.command == "analysis_dto":
        analysis_dto(
            args.ldd, args.basin, args.folder, args.label, args.views, args.talk
        )
    elif args.command == "analysis_lulc_series":
        analysis_lulc_series(
            args.attributes,
            args.scenario,
            args.basin,
            args.folder,
            args.label,
            args.views,
            args.talk,
        )
    elif args.command == "func2":
        func2(args.path, args.flag)


# SCRIPT
# ***********************************************************************
# standalone behaviour as a script
if __name__ == "__main__":

    # Call main
    # ===================================================================
    main()
