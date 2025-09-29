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
# ... {develop}


# FUNCTIONS
# ***********************************************************************

# FUNCTIONS -- Project-level
# =======================================================================


def demo(input_file1, input_file2, output_folder, talk):
    # START UP
    # -------------------------------------------------------------------
    if talk:
        logger.setLevel(logging.INFO)  # show info + warnings
    else:
        logger.setLevel(logging.WARNING)  # silence info/debug

    start_start = time.time()
    tool_name = demo.__name__

    ls_steps = []
    ls_times = []

    # LOAD INPUTS
    # -------------------------------------------------------------------
    step_label = "loading"
    start_time = time.time()

    # load protocols
    time.sleep(0.2)
    df_data1 = pd.read_csv(input_file1)
    df_data2 = pd.read_csv(input_file2)

    end_time = time.time()
    elapsed_time_load = end_time - start_time

    ls_steps.append(step_label)
    ls_times.append(elapsed_time_load)

    logger.info("Loaded inputs in %.2f seconds", elapsed_time_load)

    # PROCESS DATA
    # -------------------------------------------------------------------
    step_label = "processing"
    start_time = time.time()

    # process protocols
    time.sleep(1)
    df_output = pd.concat([df_data1, df_data2])

    end_time = time.time()
    elapsed_time_process = end_time - start_time

    ls_steps.append(step_label)
    ls_times.append(elapsed_time_process)

    logger.info("Processed data in %.2f seconds", elapsed_time_process)

    # EXPORT OUTPUTS
    # -------------------------------------------------------------------
    step_label = "exporting"
    start_time = time.time()

    # export protocols
    time.sleep(0.3)
    file_output = Path(output_folder) / "demo_output.csv"
    df_output.to_csv(file_output, sep=";", index=False)

    end_time = time.time()
    elapsed_time_export = end_time - start_time

    ls_steps.append(step_label)
    ls_times.append(elapsed_time_export)
    logger.info(
        "Exported output in %.2f seconds to %s", elapsed_time_export, file_output
    )

    # SHUTDOWN
    # -------------------------------------------------------------------
    step_label = "run"
    end_end = time.time()
    elapsed_time = end_end - start_start
    ls_steps.append(step_label)
    ls_times.append(elapsed_time)

    df_run = pd.DataFrame({"step": ls_steps, "time": ls_times})
    file_output_runtimes = Path(output_folder) / "runtimes.csv"
    df_run.to_csv(file_output_runtimes, sep=";", index=False)

    logger.info("Run completed in %.2f seconds", elapsed_time)
    return True


def run_dto(file_ldd, output_folder, talk):
    from plans.datasets import Raster, LDD, DTO
    from plans.geo import distance_to_outlet

    # START UP
    # -------------------------------------------------------------------
    if talk:
        logger.setLevel(logging.INFO)  # show info + warnings
    else:
        logger.setLevel(logging.WARNING)  # silence info/debug

    start_start = time.time()

    ls_steps = []
    ls_times = []

    # LOAD INPUTS
    # -------------------------------------------------------------------
    step_label = "loading"
    start_time = time.time()

    # load protocols
    logger.info("Loading inputs ...")
    ldd = LDD()
    ldd.load_data(file_data=file_ldd)

    end_time = time.time()
    elapsed_time_load = end_time - start_time

    ls_steps.append(step_label)
    ls_times.append(elapsed_time_load)

    logger.info("Loaded inputs in %.2f seconds", elapsed_time_load)

    # PROCESS DATA
    # -------------------------------------------------------------------
    step_label = "processing"
    start_time = time.time()

    # process protocols
    logger.info("Processing ...")
    grd_outdist = distance_to_outlet(grd_ldd=ldd.data, n_res=ldd.cellsize)

    end_time = time.time()
    elapsed_time_process = end_time - start_time

    ls_steps.append(step_label)
    ls_times.append(elapsed_time_process)

    logger.info("Processed data in %.2f seconds", elapsed_time_process)

    # EXPORT OUTPUTS
    # -------------------------------------------------------------------
    step_label = "exporting"
    start_time = time.time()

    # export protocols
    logger.info("Exporting ...")

    dto = DTO()
    dto.data = grd_outdist.copy()
    dto.raster_metadata = ldd.raster_metadata
    dto.raster_metadata["NODATA_value"] = DC_NODATA["float32"]
    dto.view(show=True)
    file_output = dto.export_tif(folder=output_folder, filename="dto")

    end_time = time.time()
    elapsed_time_export = end_time - start_time

    ls_steps.append(step_label)
    ls_times.append(elapsed_time_export)
    logger.info(
        "Exported output in %.2f seconds to %s", elapsed_time_export, file_output
    )

    # SHUTDOWN
    # -------------------------------------------------------------------
    step_label = "run"
    end_end = time.time()
    elapsed_time = end_end - start_start
    ls_steps.append(step_label)
    ls_times.append(elapsed_time)

    df_run = pd.DataFrame({"step": ls_steps, "time": ls_times})
    file_output_runtimes = Path(output_folder) / "runtimes.csv"
    df_run.to_csv(file_output_runtimes, sep=";", index=False)

    logger.info("Run completed in %.2f seconds", elapsed_time)
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
    parser_dto = subparsers.add_parser("run_dto", help="Run dto()")
    parser_dto.add_argument(
        "--input1", required=True, help="Input file path to ldd.tif map"
    )
    parser_dto.add_argument("--folder", required=True, help="Output folder path")
    parser_dto.add_argument("--talk", action="store_true")  # flag

    # --- func2
    parser_f2 = subparsers.add_parser("func2", help="Run func2")
    parser_f2.add_argument("--path", required=True, help="Path to folder")
    parser_f2.add_argument("--flag", action="store_true", help="Enable optional flag")

    args = parser.parse_args()

    if args.command == "demo":
        demo(args.input1, args.input2, args.folder, args.talk)
    elif args.command == "run_dto":
        run_dto(args.input1, args.folder, args.talk)
    elif args.command == "func2":
        func2(args.path, args.flag)


# SCRIPT
# ***********************************************************************
# standalone behaviour as a script
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] plans.%(module)s.%(funcName)s: %(message)s",
    )
    # Call main
    # ===================================================================
    main()
