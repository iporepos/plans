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
from platformdirs import user_data_dir

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

APP_NAME = "plans"

# App
APP_DIR = Path(str(user_data_dir(APP_NAME, appauthor=False)))
PROJECTS_ROOT_CONFIG = APP_DIR / "plans-projects-root.txt"
DEFAULT_PROJECTS_ROOT = Path.home() / "PlansProjects"

# Data
DATA_DIR = Path(__file__).parent / "data"
FILE_FIELDS = DATA_DIR / "fields.csv"
FILE_FILES = DATA_DIR / "files.csv"


# ... {develop}


# FUNCTIONS
# ***********************************************************************


def live_check():
    print(" >>> live check ")


def install_projects_root():
    """
    Execute the installer routine to create the application directory and default project path.

    .. note::

         This function persists the project root configuration by writing the resolved path
         to a ``plans-projects-root.txt`` file within the ``APP_DIR``.

    :return: None
    :rtype: None
    """
    print(APP_DIR)
    APP_DIR.mkdir(parents=True, exist_ok=True)
    DEFAULT_PROJECTS_ROOT.mkdir(parents=True, exist_ok=True)

    PROJECTS_ROOT_CONFIG.write_text(
        str(DEFAULT_PROJECTS_ROOT.resolve()), encoding="utf-8"
    )

    return None


def load_projects_root():
    """
    Retrieve the configured project root directory from the application settings.

    .. important::

         If the configuration file does not exist, the installer routine is triggered.
         Additionally, if the retrieved path does not exist on the file system, it is
         automatically created.

    :return: Path to the projects root of the application
    :rtype: :class:`pathlib.Path`
    """
    if not PROJECTS_ROOT_CONFIG.is_file():
        install_project_root()

    root_dir = Path(config_file.read_text(encoding="utf-8").strip())

    if not root_dir.is_dir():
        root_dir.mkdir(parents=True, exist_ok=True)

    return root_dir


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
