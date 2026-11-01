# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
Unit tests for the ``Univar`` class.

This module validates the behavior of ``Univar`` using a small in-memory
sample (no files are written).

Features
--------
The test suite verifies that:

* Figures are built for both data panel options (scatter and boxplot).

"""
# IMPORTS
# ***********************************************************************
# import modules from other libs

# Native imports
# =======================================================================
import unittest

# ... {develop}

# External imports
# =======================================================================
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ... {develop}

# Project-level imports
# =======================================================================
from plans.analyst import Univar

# ... {develop}


# CONSTANTS
# ***********************************************************************
# define constants in uppercase

# ... {develop}

# FUNCTIONS
# ***********************************************************************


# CLASSES
# ***********************************************************************


class TestUnivar(unittest.TestCase):

    def setUp(self):
        rng = np.random.default_rng(seed=42)
        self.uv = Univar(name="TestUv", alias="Uv1")
        self.uv.set_array(array=rng.gamma(shape=2, scale=10, size=200))

    def test_view_data_plot(self):
        for data_plot in ["scatter", "boxplot"]:
            with self.subTest(data_plot=data_plot):
                self.uv.view_specs["data_plot"] = data_plot
                fig = self.uv.view(show=False, return_fig=True)
                ax_data = fig.get_axes()[0]
                # boxplot draws one box patch, scatter draws a collection
                if data_plot == "boxplot":
                    self.assertEqual(len(ax_data.patches), 1)
                else:
                    self.assertEqual(len(ax_data.collections), 1)
                plt.close(fig)


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
    unittest.main()
    # ... {develop}
