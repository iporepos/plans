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
from pathlib import Path

# ... {develop}

# External imports
# =======================================================================
import pandas as pd

# ... {develop}

# Project-level imports
# =======================================================================
# import {module}
# ... {develop}


# CONSTANTS
# ***********************************************************************
# define constants in uppercase

DATA_DIR = Path(__file__).parent / "data"
FILE_FIELDS = DATA_DIR / "fields.csv"
FILE_FILES = DATA_DIR / "files.csv"
# ... {develop}


# FUNCTIONS
# ***********************************************************************
def parse_files():
    df = pd.read_csv(FILE_FILES, sep=";")
    df["ext"] = df["structure"].apply(lambda x: ".tif" if "raster" in x else ".csv")
    df["file_name"] = df["name"] + df["ext"]
    return df


def parse_fields():
    return pd.read_csv(FILE_FIELDS, sep=";")


# CLASSES
# ***********************************************************************


# ... {develop}

# CLASSES -- Module-level
# =======================================================================
# ... {develop}


# SCRIPT
# ***********************************************************************
# standalone behaviour as a script
if __name__ == "__main__":

    # Script section
    # ===================================================================
    print("Hello world!")
    # ... {develop}
