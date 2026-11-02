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
* The ``GeoUnivar`` map panel is square and aligned, for any extent of the data.
* ``GeoUnivar`` sets data without changing the input, and views leave it untouched.
* The map draws other layers below the points, and all panels follow the classes.

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
import geopandas as gpd
from shapely.geometry import box
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection

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


def make_points(x, y):
    """
    Make points with the x coordinate as the value, in the ``soc`` column.
    """
    return gpd.GeoDataFrame(
        data={"soc": x},
        geometry=gpd.points_from_xy(x=x, y=y),
        crs="EPSG:4674",
    )


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

    def test_geo_map_panel(self):
        # the panel does not depend on the extent of the data
        ls_left = []
        for layout in ["full", "mini"]:
            for dx, dy in [(1.0, 0.1), (0.1, 1.0)]:
                with self.subTest(layout=layout, dx=dx, dy=dy):
                    gv = GeoUnivar(name="Geo")
                    gv.view_specs["layout"] = layout
                    vct_x = np.linspace(start=-51, stop=-51 + dx, num=20)
                    vct_y = np.linspace(start=-30, stop=-30 + dy, num=20)
                    gv.set_data(
                        input_df=make_points(x=vct_x, y=vct_y), input_varfield="soc"
                    )
                    fig = gv.view(show=False, return_fig=True)
                    fig.canvas.draw()
                    ax_map, ax_data = fig.get_axes()[:2]
                    box_map = ax_map.get_window_extent()
                    self.assertAlmostEqual(box_map.width, box_map.height, places=3)
                    self.assertAlmostEqual(
                        box_map.y1, ax_data.get_window_extent().y1, places=3
                    )
                    ls_left.append(box_map.x0)
                    # all points stay in view
                    self.assertLessEqual(ax_map.get_xlim()[0], vct_x.min())
                    self.assertGreaterEqual(ax_map.get_xlim()[1], vct_x.max())
                    self.assertLessEqual(ax_map.get_ylim()[0], vct_y.min())
                    self.assertGreaterEqual(ax_map.get_ylim()[1], vct_y.max())
                    plt.close(fig)
        self.assertAlmostEqual(min(ls_left), max(ls_left), places=3)

    def test_geo_set_data(self):
        vct_x = np.linspace(start=-51, stop=-50, num=10)
        gdf = make_points(x=vct_x, y=vct_x + 21)
        gdf["other"] = 1.0
        gdf.loc[0, "soc"] = np.nan
        ls_columns = list(gdf.columns)

        gv = GeoUnivar(name="Geo")
        gv.set_data(input_df=gdf, input_varfield="soc")
        self.assertListEqual(list(gv.data.columns), [gv.varfield, gv.field_geometry])
        self.assertEqual(gv.size, 9)
        self.assertEqual(gv.data.crs, gdf.crs)

        # the view leaves all data untouched
        ls_data = list(gv.data.columns)
        fig = gv.view(show=False, return_fig=True)
        plt.close(fig)
        self.assertListEqual(list(gv.data.columns), ls_data)
        self.assertListEqual(list(gdf.columns), ls_columns)

    def test_geo_layers(self):
        vct_x = np.linspace(start=-51, stop=-50, num=10)
        gv = GeoUnivar(name="Geo")
        gv.set_data(input_df=make_points(x=vct_x, y=vct_x + 21), input_varfield="soc")
        # the layer goes beyond the points
        layer = gpd.GeoDataFrame(geometry=[box(-52, -31, -49, -28)], crs="EPSG:4674")
        gv.view_specs["layers_map"] = [
            {"data": layer, "facecolor": "silver", "edgecolor": "black"}
        ]
        fig = gv.view(show=False, return_fig=True)
        fig.canvas.draw()
        ax = fig.get_axes()[0]
        coll_layer, coll_points = ax.collections
        self.assertLess(coll_layer.get_zorder(), coll_points.get_zorder())
        self.assertLessEqual(ax.get_xlim()[0], -52)
        self.assertGreaterEqual(ax.get_xlim()[1], -49)
        plt.close(fig)
        # the spec keeps its keys for the next view
        self.assertIn("data", gv.view_specs["layers_map"][0])

    def count_bars(self, ax):
        # pieces of a color bar, apart from scatters and mean lines
        return sum(isinstance(c, PolyCollection) for c in ax.collections)

    def test_n_classes(self):
        vct_x = np.linspace(start=-51, stop=-50, num=50)
        gv = GeoUnivar(name="Geo")
        gv.set_data(input_df=make_points(x=vct_x, y=vct_x + 21), input_varfield="soc")
        gv.view_specs["n_classes_cmap"] = 3
        fig = gv.view(show=False, return_fig=True)
        ax_map, ax_data, ax_hist = fig.get_axes()[:3]
        # colors in the map and pieces of the bars
        vct_colors = ax_map.collections[0].get_facecolor()
        self.assertEqual(len(np.unique(vct_colors, axis=0)), 3)
        self.assertEqual(self.count_bars(ax=ax_data), 3)
        self.assertEqual(self.count_bars(ax=ax_hist), 3)
        plt.close(fig)

        # colorized scatter of the parent class
        self.uv.view_specs["colorize_scatter"] = True
        self.uv.view_specs["n_classes_cmap"] = 3
        fig = self.uv.view(show=False, return_fig=True)
        ax_data = fig.get_axes()[0]
        self.assertEqual(len(np.unique(ax_data.collections[0].get_array())), 3)
        self.assertEqual(self.count_bars(ax=ax_data), 3)
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
