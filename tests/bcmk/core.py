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
import os

# IMPORTS
# ***********************************************************************
# import modules from other libs

# Native imports
# =======================================================================
# import {module}
# ... {develop}

# External imports
# =======================================================================
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from scipy.ndimage import gaussian_filter

# ... {develop}

# Project-level imports
# =======================================================================
from tests.conftest import DATA_DIR

# ... {develop}


# CONSTANTS
# ***********************************************************************
# define constants in uppercase

# CONSTANTS -- Project-level
# =======================================================================
# ... {develop}

# Subsubsection example
# -----------------------------------------------------------------------
HELLO = "Hello World!"  # example
# ... {develop}

# CONSTANTS -- Module-level
# =======================================================================
# ... {develop}


# FUNCTIONS
# ***********************************************************************


# FUNCTIONS -- Project-level
# =======================================================================
def get_climate_series(
    dataset, scenario, ppt_params, epot_params, start="2020-12-01", end="2021-04-01"
):
    # get t range
    trange = pd.date_range(start=start, end=end, freq="h")
    # get ppt and e_pot
    ppt = get_ppt(
        date_index=trange,
        values=ppt_params["values"],
        sigmas=ppt_params["sigmas"],
        days=ppt_params["days"],
    )
    epot = get_epot(
        date_index=trange,
        total_value=epot_params["value"],
    )
    df = pd.DataFrame({"datetime": trange, "ppt": ppt, "epot": epot})
    os.makedirs(f"{dataset}/data/climate/{scenario}", exist_ok=True)
    df.to_csv(
        DATA_DIR / f"{dataset}/data/climate/{scenario}/climate_series.csv",
        sep=";",
        index=False,
    )
    return None


# ... {develop}

# FUNCTIONS -- Module-level
# =======================================================================


def get_ppt(date_index, values, sigmas, days):
    vct_zeros = np.zeros(shape=np.shape(date_index))
    vct_ppt = vct_zeros.copy()
    ls_vectors = []
    for i in range(len(values)):
        lcl_vector = vct_zeros.copy()
        lcl_vector[24 * days[i]] = values[i]
        lcl_vector = gaussian_filter(input=lcl_vector, sigma=sigmas[i])
        vct_ppt = vct_ppt + lcl_vector.copy()

    return vct_ppt


def get_epot(date_index, total_value, peak_hour=15, period_hours=24):
    """
    Generate a sinusoidal series with one cycle per day.

    :param date_index: Time index (e.g., hourly data range).
    :type date_index: pandas.DatetimeIndex
    :param total_value: total accumulated value.
    :type total_value: float
    :param peak_hour: Hour of the day when the wave reaches its maximum. Defaults to 12.
    :type peak_hour: int or float, optional
    :param period_hours: Duration of one full cycle, normally 24 for daily. Defaults to 24.
    :type period_hours: int or float, optional

    :return: Sinusoidal values aligned with ``date_index``.
    :rtype: pandas.Series
    """
    # fractional hour of day
    hours = date_index.hour + date_index.minute / 60 + date_index.second / 3600

    # shift so that maximum occurs at peak_hour
    radians = 2 * np.pi * (hours - peak_hour) / period_hours

    # build wave
    mean_value = total_value / len(date_index)
    amplitude = mean_value / 5
    values = mean_value + amplitude * np.cos(radians)

    return values


# ... {develop}


# CLASSES
# ***********************************************************************

# CLASSES -- Project-level
# =======================================================================
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

    ppt_params = {"values": [50, 50], "sigmas": [3, 4], "days": [30, 60]}
    epot_params = {"value": 50}
    get_climate_series(
        dataset="climate_bcmk01", ppt_params=ppt_params, epot_params=epot_params
    )

    # Script subsection
    # -------------------------------------------------------------------
    # ... {develop}
