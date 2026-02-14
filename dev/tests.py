# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
Command-line interface for selecting and running unit and benchmark tests.

Examples
--------

Run unit tests::

    python -m tests.run

Run benchmark tests::

    python -m tests.run --which bcmk

Run all tests including XXL benchmarks::

    python -m tests.run --all -x


"""
# IMPORTS
# ***********************************************************************
# import modules from other libs

# Native imports
# =======================================================================
import argparse
import os, sys
import subprocess

# ... {develop}

# External imports
# =======================================================================
# import {module}
# ... {develop}

# Project-level imports
# =======================================================================
# import {module}
# ... {develop}


# CONSTANTS
# ***********************************************************************
# define constants in uppercase


# FUNCTIONS
# ***********************************************************************


def get_arguments():

    parser = argparse.ArgumentParser(
        description="Run tests",
        epilog="Usage example: python -m tests.run --all",
    )

    parser.add_argument(
        "--which", default="unit", help="Which tests to run [unit] [bcmk] [bcmkxxl]"
    )

    parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        help="Run all tests",
    )

    parser.add_argument(
        "-x",
        "--xxl",
        action="store_true",
        help="Include extra large tests",
    )

    args = parser.parse_args()

    return args


def main():

    args = get_arguments()

    run_unit = False
    run_bcmk = False

    if args.which == "unit":
        run_unit = True

    if args.which == "bcmk":
        run_bcmk = True

    if run_unit:
        s = "tests/unit"

    if run_bcmk:
        s = "tests/bcmk"
        os.environ["RUN_BENCHMARKS"] = "1"
        if args.xxl:
            os.environ["RUN_BENCHMARKS_XXL"] = "1"

    if args.all:
        s = "tests"
        os.environ["RUN_BENCHMARKS"] = "1"
        if args.xxl:
            os.environ["RUN_BENCHMARKS_XXL"] = "1"

    cmd = [
        sys.executable,
        "-m",
        "unittest",
        "discover",
        "-s",
        s,
        "-p",
        "test_*.py",
        "-v",
    ]

    subprocess.run(cmd, check=True)

    return None


# SCRIPT
# ***********************************************************************
# standalone behaviour as a script
if __name__ == "__main__":

    main()
