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
def get_climate_series():
    trange = pd.date_range(start="2020-12-01", end="2021-04-01", freq="h")
    vct_z = np.zeros(shape=np.shape(trange))
    vct_ppt = vct_z.copy()
    day = 30 * 24
    vct_ppt[day] = 50
    vct_ppt[2 * day] = 50

    vct_ppt2 = gaussian_filter(input=vct_ppt, sigma=3)

    vct_epot = vct_z.copy() + (50 / len(vct_z))
    df = pd.DataFrame({"datetime": trange, "ppt": vct_ppt2, "e_pot": vct_epot})
    print(df)
    print(df["ppt"].sum())
    print(df["e_pot"].sum())
    plt.plot(df["datetime"], df["ppt"])
    plt.show()

    df.to_csv(DATA_DIR / "climate_bcmk01/climate_series.csv", sep=";", index=False)


# ... {develop}

# FUNCTIONS -- Module-level
# =======================================================================
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

    get_climate_series()

    # Script subsection
    # -------------------------------------------------------------------
    # ... {develop}
