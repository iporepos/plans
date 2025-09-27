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

 - {feature 1}
 - {feature 2}
 - {feature 3}
 - {etc}

Overview
--------
todo docstring
{Overview description}

Examples
--------
todo docstring

Print a message

.. code-block:: python

    # print message
    print("Hello world!")
    # [Output] >> 'Hello world!'


"""

# ***********************************************************************
# IMPORTS
# ***********************************************************************
# import modules from other libs


# Native imports
# =======================================================================
import os
from pathlib import Path

# ... {develop}

# External imports
# =======================================================================
import requests
import zipfile
import numpy as np
import pandas as pd

# ... {develop}

# Project-level imports
# =======================================================================
# import {module}
# ... {develop}


# ***********************************************************************
# CONSTANTS
# ***********************************************************************
# define constants in uppercase


# Project-level
# =======================================================================

# Paths
# -----------------------------------------------------------------------
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "outputs"
# ... {develop}

# Files
# -----------------------------------------------------------------------
DATA_FILE = DATA_DIR / "test_data.csv"
DATASETS_FILE = DATA_DIR / "datasets.csv"

# Other
# -----------------------------------------------------------------------
DATASETS_DF = pd.read_csv(DATASETS_FILE, sep=";")


# ... {develop}

# Names
# -----------------------------------------------------------------------
REPO_NAME = os.path.basename(Path(BASE_DIR).parent)
# ... {develop}

# Benchmark tests
# -----------------------------------------------------------------------
# benchmark tests disabled -- default to "0" (false)
RUN_BENCHMARKS = os.getenv("RUN_BENCHMARKS", "0") == "1"
# large benchmark tests disabled -- default to "0" (false)
RUN_BENCHMARKS_XXL = os.getenv("RUN_BENCHMARKS_XXL", "0") == "1"
# ... {develop}

# Module-level
# =======================================================================
# {develop}


# ***********************************************************************
# FUNCTIONS
# ***********************************************************************


# Project-level
# =======================================================================


def testmsg(s):
    # todo docstring
    s2 = f"{REPO_NAME} -- tests >>> {s}".lower()
    return s2


def testprint(s):
    s2 = testmsg(s)
    print(s2, flush=True)
    return s2


def make_output():
    # todo docstring
    testprint("making output dir")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    return None


def make_data(size=100):
    # todo docstring
    testprint("making data")
    if not os.path.isfile(DATA_FILE):
        v = np.random.randint(low=10, high=100, size=size)
        v2 = np.random.randint(low=10, high=100, size=size)
        v3 = v2 / v
        df = pd.DataFrame({"v1": v, "v2": v2, "v3": v3})
        df.to_csv(DATA_FILE, sep=";", index=False)
        testprint("data created")
    else:
        testprint("data already available")
    return None


def load_data():
    # todo docstring
    testprint("loading numbers data")
    df = pd.read_csv(DATA_FILE, sep=";")
    return df


# ... {develop}

# Module-level
# =======================================================================


def add(num1, num2):
    """
    Add two numbers

    :param num1: number 1
    :type num1: int or float
    :param num2: number 2
    :type num2: int or float
    :return: sum of numbers
    :rtype: int or float
    """
    return num1 + num2


def multiply(num1, num2):
    """
    Multiply two numbers

    :param num1: number 1
    :type num1: int or float
    :param num2: number 2
    :type num2: int or float
    :return: product of numbers
    :rtype: int or float
    """
    return num1 * num2


def retrieve_dataset(name):
    # todo docstring
    ls_datasets = DATASETS_DF["name"].unique()
    if name not in set(ls_datasets):
        testprint(f"dataset {name} not found")
        return False
    else:
        # install dataset
        dataset_dir = DATA_DIR / name
        if not os.path.exists(dataset_dir):
            dataset_dir = install_dataset(name)

        # get output
        output_path = OUTPUT_DIR / name
        os.makedirs(output_path, exist_ok=True)

        return (dataset_dir, output_path)


def install_dataset(name):
    # todo docstring
    dataset_dir = DATA_DIR / name
    os.makedirs(dataset_dir, exist_ok=True)
    dataset_url = DATASETS_DF.loc[DATASETS_DF["name"] == name, "url"].values[0]
    zip_path = os.path.join(dataset_dir, f"{name}.zip")

    testprint(f"donwloading dataset: {name} ...")
    download_file(dataset_url, dst=zip_path)

    testprint(f"extracting dataset '{name}'...")
    extract_zip(zip_path, dataset_dir)
    os.remove(zip_path)
    return dataset_dir


def download_file(url, dst):
    # todo docstring
    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open(dst, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    return None


def extract_zip(file_path, extract_to):
    # todo docstring
    with zipfile.ZipFile(file_path, "r") as zip_ref:
        zip_ref.extractall(extract_to)


# ... {develop}

# ***********************************************************************
# CLASSES
# ***********************************************************************

# Project-level
# =======================================================================
# {develop}

# Module-level
# =======================================================================


class DatasetDownloadError(Exception):
    """
    Custom exception for dataset download issues.
    """

    pass


# ... {develop}

# ***********************************************************************
# SCRIPT
# ***********************************************************************
# standalone behaviour as a script

if __name__ == "__main__":

    # Script section
    # ===================================================================
    testprint("conftest.py")

    # Make data
    # -------------------------------------------------------------------
    make_data(size=50)

    # ... {develop}

    # Script subsection
    # -------------------------------------------------------------------
    # ... {develop}
