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
* Figures are built for every layout, and bad layouts or missing data raise.

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
from plans.datasets.analyst import GeoUnivar, Univar

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

    def test_view_layouts(self):
        # layout, number of axes, statistics table
        ls_cases = [
            ("full", 3, True),
            ("mini", 3, False),
            ("simple", 1, False),
            ("simple-shallow", 1, False),
            ("qq", 1, False),
            ("default", 3, False),
        ]
        self.assertEqual(sorted(c[0] for c in ls_cases), sorted(self.uv.layouts))
        for layout, n_axes, has_stats in ls_cases:
            with self.subTest(layout=layout):
                self.uv.view_specs["layout"] = layout
                fig = self.uv.view(show=False, return_fig=True)
                axes = fig.get_axes()
                self.assertEqual(len(axes), n_axes)
                ls_text = [t.get_text() for ax in axes for t in ax.texts]
                self.assertEqual(any("mean:" in t for t in ls_text), has_stats)
                plt.close(fig)

    def test_view_qq(self):
        self.uv.view_specs["layout"] = "qq"
        fig = self.uv.view(show=False, return_fig=True)
        ax = fig.get_axes()[0]
        # sorted data against the normal reference line
        vct_y = ax.collections[0].get_offsets()[:, 1]
        self.assertEqual(len(vct_y), 200)
        self.assertTrue(np.all(np.diff(vct_y) >= 0))
        self.assertEqual(len(ax.lines), 1)
        self.assertEqual(ax.get_title(loc="left"), "Q-Q")
        plt.close(fig)

    def test_view_errors(self):
        self.uv.view_specs["layout"] = "banana"
        with self.assertRaisesRegex(ValueError, "banana"):
            self.uv.view(show=False, return_fig=True)
        with self.assertRaisesRegex(ValueError, "No data"):
            Univar(name="Empty").view(show=False, return_fig=True)

    def test_geo_layouts(self):
        gv = GeoUnivar(name="Geo")
        self.assertEqual(sorted(gv.layouts), ["full", "mini"])
        for layout in ["simple", "qq", "banana"]:
            with self.subTest(layout=layout):
                gv.view_specs["layout"] = layout
                with self.assertRaisesRegex(ValueError, layout):
                    gv._get_fig_specs()


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
