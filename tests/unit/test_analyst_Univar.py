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
* The map draws the helper geometry, and all panels follow the color scheme.
* The color bar sits beside the map, with classes or a continuous scale.

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
from plans import viewer
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
                ls_text = [t.get_text() for t in fig.texts]
                self.assertEqual(any("Mean:" in t for t in ls_text), has_stats)
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

    def get_geo(self, num=50):
        vct_x = np.linspace(start=-51, stop=-50, num=num)
        gv = GeoUnivar(name="Geo")
        gv.set_data(input_df=make_points(x=vct_x, y=vct_x + 21), input_varfield="soc")
        return gv

    def test_geo_helper_geometry(self):
        gv = self.get_geo()
        # the helper goes beyond the points
        helper = gpd.GeoDataFrame(geometry=[box(-52, -31, -49, -28)], crs="EPSG:4674")
        gv.view_specs["helper_geometry"] = helper
        fig = gv.view(show=False, return_fig=True)
        fig.canvas.draw()
        ax = fig.get_axes()[0]
        coll_points, coll_helper = ax.collections
        # an outline above the data
        self.assertGreater(coll_helper.get_zorder(), coll_points.get_zorder())
        self.assertEqual(len(coll_helper.get_facecolor()), 0)
        self.assertLessEqual(ax.get_xlim()[0], -52)
        self.assertGreaterEqual(ax.get_xlim()[1], -49)
        plt.close(fig)

        # a fill goes below the data
        gv.view_specs["facecolor_helper"] = "silver"
        gv.view_specs["zorder_helper"] = 1
        fig = gv.view(show=False, return_fig=True)
        coll_points, coll_helper = fig.get_axes()[0].collections
        self.assertLess(coll_helper.get_zorder(), coll_points.get_zorder())
        plt.close(fig)

    def get_cbar_axis(self, gv):
        fig = gv.view(show=False, return_fig=True)
        fig.canvas.draw()
        ax_map = fig.get_axes()[0]
        return fig, ax_map, fig.get_axes()[4:]

    def test_geo_cbar_classes(self):
        # values with usual labels, such as 10.00
        vct_x = np.linspace(start=9, stop=10, num=50)
        gv = GeoUnivar(name="Geo")
        gv.set_data(input_df=make_points(x=vct_x, y=vct_x), input_varfield="soc")
        for layout in ["full", "mini"]:
            with self.subTest(layout=layout):
                gv.view_specs["layout"] = layout
                fig, ax_map, ls_children = self.get_cbar_axis(gv=gv)
                # the last axis, between the map and the data
                self.assertEqual(len(fig.get_axes()), 5)
                self.assertEqual(len(ls_children), 1)
                ax_cbar = ls_children[0]
                ax_data, ax_hist, ax_cdf = fig.get_axes()[1:4]
                # same place and same y axis of the panels at its right
                for ax in [ax_data, ax_hist, ax_cdf]:
                    box_ax = ax.get_window_extent()
                    box_cbar = ax_cbar.get_window_extent()
                    self.assertAlmostEqual(box_cbar.y0, box_ax.y0, places=3)
                    self.assertAlmostEqual(box_cbar.y1, box_ax.y1, places=3)
                    np.testing.assert_allclose(ax_cbar.get_ylim(), ax.get_ylim())
                # all of the bar, its labels and title
                box_tight = ax_cbar.get_tightbbox()
                self.assertGreater(box_tight.x0, ax_map.get_window_extent().x1)
                self.assertEqual(ax_cbar.yaxis.get_ticks_position(), "left")
                self.assertEqual(ax_cbar.yaxis.get_label_position(), "left")
                box_data = fig.get_axes()[1].yaxis.get_tightbbox()  # labels of y axis
                self.assertLess(box_tight.x1, box_data.x0)
                self.assertEqual(ls_children[0].get_ylabel(), gv.view_specs["ylabel"])
                # the y axis lives on the bar
                self.assertEqual(ax_data.get_ylabel(), "")
                self.assertEqual(ax_data.get_xlabel(), "")
                self.assertEqual(ax_data.get_title(loc="left"), "Data")
                # labels at the 6 boundaries of the 5 classes, up to the ends of the range
                vct_ticks = ls_children[0].get_yticks()
                np.testing.assert_allclose(vct_ticks[[0, -1]], ax_data.get_ylim())
                self.assertEqual(len(vct_ticks), 6)
                plt.close(fig)

    def test_geo_cbar_options(self):
        gv = self.get_geo()

        # no lines between classes
        fig, _, ls_children = self.get_cbar_axis(gv=gv)
        self.assertEqual(len(ls_children[0]._colorbar.dividers.get_segments()), 0)
        plt.close(fig)

        # the map is still there without its bar, and the y axis goes back to the data
        gv.view_specs["cbar_map"] = False
        fig, ax_map, ls_children = self.get_cbar_axis(gv=gv)
        self.assertEqual(len(ls_children), 0)
        self.assertEqual(len(ax_map.collections), 1)
        self.assertEqual(fig.get_axes()[1].get_ylabel(), gv.view_specs["ylabel"])
        plt.close(fig)

        # no data, no bar
        gv.view_specs["cbar_map"] = True
        gv.view_specs["empty_map"] = True
        fig, _, ls_children = self.get_cbar_axis(gv=gv)
        self.assertEqual(len(ls_children), 0)
        plt.close(fig)

    def test_geo_cbar_tips(self):
        # data from -51 to -50, and where the range clips it
        ls_cases = [
            (None, "neither"),
            ([-52, -49], "neither"),
            ([-52, -50.5], "max"),
            ([-50.5, -49], "min"),
            ([-50.8, -50.2], "both"),
        ]
        for scheme in ["equal", "quantiles", "continuous"]:
            for v_range, s_extend in ls_cases:
                with self.subTest(scheme=scheme, v_range=v_range):
                    gv = self.get_geo()
                    gv.view_specs["scheme_cmap"] = scheme
                    if v_range is not None:
                        gv.view_specs["range"] = v_range
                    fig, _, ls_children = self.get_cbar_axis(gv=gv)
                    ax_cbar = ls_children[0]
                    self.assertEqual(ax_cbar._colorbar.extend, s_extend)
                    # tips do not touch the alignment with the panels
                    ax_data = fig.get_axes()[1]
                    box_cbar = ax_cbar.get_window_extent()
                    box_data = ax_data.get_window_extent()
                    self.assertAlmostEqual(box_cbar.y0, box_data.y0, places=3)
                    self.assertAlmostEqual(box_cbar.y1, box_data.y1, places=3)
                    np.testing.assert_allclose(ax_cbar.get_ylim(), ax_data.get_ylim())
                    plt.close(fig)

    def test_scatter_band(self):
        # share of the x axis taken by the points
        def get_share(obj, n_ax):
            fig = obj.view(show=False, return_fig=True)
            ax = fig.get_axes()[n_ax]
            n_lim = ax.get_xlim()[1] - ax.get_xlim()[0]
            vct_x = ax.collections[0].get_offsets()[:, 0]
            plt.close(fig)
            return (vct_x.max() - vct_x.min()) / n_lim

        self.assertAlmostEqual(get_share(obj=self.get_geo(), n_ax=1), 1 / 3, delta=0.01)
        # Univar stays as it is
        self.assertAlmostEqual(get_share(obj=self.uv, n_ax=0), 1 / 9, delta=0.01)

    def test_geo_continuous(self):
        gv = self.get_geo()
        gv.view_specs["scheme_cmap"] = "continuous"
        gv.view_specs["range"] = [-52, -49]
        fig, ax_map, ls_children = self.get_cbar_axis(gv=gv)
        # all colors are different, and the bar follows the range
        self.assertEqual(
            len(np.unique(ax_map.collections[0].get_facecolor(), axis=0)), 50
        )
        np.testing.assert_allclose(ls_children[0].get_ylim(), [-52, -49])
        self.assertEqual(len(ls_children[0]._colorbar.dividers.get_segments()), 0)
        plt.close(fig)

        # strips and colored scatter follow the scheme
        gv.view_specs["cbar_histh"] = True
        gv.view_specs["colorize_scatter"] = True
        fig = gv.view(show=False, return_fig=True)
        fig.canvas.draw()
        ax_data, ax_hist = fig.get_axes()[1:3]
        self.assertEqual(self.count_bars(ax=ax_hist), 100)
        self.assertEqual(
            len(np.unique(ax_data.collections[0].get_facecolor(), axis=0)), 50
        )
        plt.close(fig)

    def test_geo_repeated_values(self):
        # classes collapse without failing
        gv = GeoUnivar(name="Geo")
        vct_x = np.array([1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 2.0])
        gdf = make_points(x=vct_x, y=vct_x + np.arange(8))
        gv.set_data(input_df=gdf, input_varfield="soc")
        for scheme in ["equal", "quantiles"]:
            with self.subTest(scheme=scheme):
                gv.view_specs["scheme_cmap"] = scheme
                fig, _, ls_children = self.get_cbar_axis(gv=gv)
                self.assertEqual(len(ls_children), 1)
                plt.close(fig)
        gv.set_data(
            input_df=make_points(x=vct_x * 0 + 1, y=vct_x), input_varfield="soc"
        )
        gv.view_specs["scheme_cmap"] = "equal"
        fig, _, ls_children = self.get_cbar_axis(gv=gv)
        self.assertEqual(len(ls_children), 1)
        plt.close(fig)

    def test_geo_map_coordinates(self):
        gv = self.get_geo()
        for n_ticks in [3, 4]:
            for layout in ["full", "mini"]:
                with self.subTest(n_ticks=n_ticks, layout=layout):
                    gv.view_specs["layout"] = layout
                    gv.view_specs["n_ticks_map"] = n_ticks
                    fig = gv.view(show=False, return_fig=True)
                    fig.canvas.draw()
                    ax_map = fig.get_axes()[0]
                    for axis, lims in [
                        (ax_map.xaxis, ax_map.get_xlim()),
                        (ax_map.yaxis, ax_map.get_ylim()),
                    ]:
                        vct_ticks = axis.get_ticklocs()
                        self.assertEqual(len(vct_ticks), n_ticks)
                        self.assertGreaterEqual(vct_ticks[0], lims[0])
                        self.assertLessEqual(vct_ticks[-1], lims[1])
                        # nearly centered
                        self.assertAlmostEqual(
                            np.mean(vct_ticks),
                            np.mean(lims),
                            delta=0.1 * (lims[1] - lims[0]),
                        )
                    plt.close(fig)

    def test_coordinate_locator(self):
        locator = viewer.CoordinateLocator(n_ticks=3)
        # large coordinates snap to integers, and stay centered
        vct = locator.tick_values(vmin=5680993.86, vmax=5683753.86)
        np.testing.assert_allclose(vct, [5681400, 5682400, 5683400])
        # degrees
        vct = locator.tick_values(vmin=-51.53, vmax=-50.89)
        np.testing.assert_allclose(vct, [-51.4, -51.2, -51.0])
        # any view gives all ticks inside, away from the ends
        rng = np.random.default_rng(seed=1)
        for vmin, n_range in zip(
            rng.normal(0, 1e4, 200), 10 ** rng.uniform(-4, 5, 200)
        ):
            vct = locator.tick_values(vmin=vmin, vmax=vmin + n_range)
            self.assertEqual(len(vct), 3)
            self.assertAlmostEqual(
                np.mean(vct), vmin + n_range / 2, delta=0.11 * n_range
            )
            self.assertGreater(vct[0], vmin)
            self.assertLess(vct[-1], vmin + n_range)

    def test_layers(self):
        # one case for each kind of panel
        gv = self.get_geo()
        gv.view_specs["helper_geometry"] = gpd.GeoDataFrame(
            geometry=[box(-51, -30, -50, -29)], crs="EPSG:4674"
        )
        for obj in [self.uv, gv]:
            with self.subTest(obj=obj.name):
                fig = obj.view(show=False, return_fig=True)
                fig.canvas.draw()
                for ax in fig.get_axes():
                    ls_grids = [a for a in ax.artists if isinstance(a, viewer.AxisGrid)]
                    ls_plots = ax.collections + ax.lines + ax.patches + ax.texts
                    n_low = min(a.get_zorder() for a in ls_plots) if ls_plots else 1
                    n_high = max(a.get_zorder() for a in ls_plots) if ls_plots else 1
                    for grid in ls_grids:
                        self.assertLess(grid.get_zorder(), n_low)
                    for artist in [ax.xaxis, ax.yaxis, *ax.spines.values()]:
                        self.assertGreater(artist.get_zorder(), n_high)
                    # the only grid is the one below
                    self.assertFalse(any(g.get_visible() for g in ax.get_xgridlines()))
                    self.assertFalse(any(g.get_visible() for g in ax.get_ygridlines()))
                # the grid of the map, on both axes
                ax_first = fig.get_axes()[0]
                n_grids = sum(isinstance(a, viewer.AxisGrid) for a in ax_first.artists)
                self.assertEqual(n_grids, 2 if obj is gv else 1)
                plt.close(fig)

    def test_mean_label(self):
        fig = self.uv.view(show=False, return_fig=True)
        ax_hist, ax_cdf = fig.get_axes()[1:3]
        for ax in [ax_hist, ax_cdf]:
            text = ax.texts[0]
            self.assertEqual(text.get_color(), viewer.COLOR_ANNOTATION)
            self.assertAlmostEqual(text.get_fontsize(), plt.rcParams["font.size"] - 1)
        # away from the bars of the histogram
        self.assertEqual(ax_hist.texts[0].get_ha(), "right")
        fig.canvas.draw()
        box_text = ax_hist.texts[0].get_window_extent()
        self.assertAlmostEqual(box_text.x1, ax_hist.get_window_extent().x1, delta=5)
        # the statistics have the same style
        for text in fig.texts:
            if ":" in text.get_text():
                self.assertEqual(text.get_color(), viewer.COLOR_ANNOTATION)
                self.assertAlmostEqual(
                    text.get_fontsize(), plt.rcParams["font.size"] - 1
                )
        self.assertTrue(any("Mean:" in t.get_text() for t in fig.texts))
        plt.close(fig)

    def test_hist_xaxis(self):
        # share of the largest bar, as percent, and the labels
        ls_cases = [
            (0.3, ["0%", "1%", "2%"]),
            (2.0, ["0%", "1%", "2%"]),
            (2.1, ["0%", "2%", "4%"]),
            (11.3, ["0%", "10%", "20%"]),
            (30, ["0%", "20%", "40%"]),
            (100, ["0%", "50%", "100%"]),
        ]
        for n_max, ls_labels in ls_cases:
            with self.subTest(n_max=n_max):
                fig, ax = plt.subplots()
                Univar.set_hist_xaxis(ax=ax, hist_max=n_max / 100)
                fig.canvas.draw()
                self.assertEqual(
                    [t.get_text() for t in ax.get_xticklabels()], ls_labels
                )
                self.assertEqual(ax.get_xlim()[0], 0)
                self.assertGreaterEqual(ax.get_xlim()[1], n_max / 100)
                plt.close(fig)
        # in a view, with skewed and with constant data
        rng = np.random.default_rng(seed=1)
        for vct in [rng.gamma(shape=1, size=500), np.ones(50)]:
            uv = Univar(name="Hist")
            uv.set_array(array=vct)
            fig = uv.view(show=False, return_fig=True)
            fig.canvas.draw()
            ax_hist = fig.get_axes()[1]
            self.assertEqual(len(ax_hist.get_xticks()), 3)
            self.assertEqual(ax_hist.get_xlim()[0], 0)
            for t in ax_hist.get_xticklabels():
                self.assertNotIn(".", t.get_text())
            # no bar is cut
            n_max = max(p.get_width() for p in ax_hist.patches)
            self.assertLessEqual(n_max, ax_hist.get_xlim()[1])
            plt.close(fig)

    def test_dynamic_alpha(self):
        self.assertEqual(Univar.get_dynamic_alpha(n_points=10), 0.8)
        self.assertLess(
            Univar.get_dynamic_alpha(n_points=9000),
            Univar.get_dynamic_alpha(n_points=1000),
        )
        self.assertEqual(Univar.get_dynamic_alpha(n_points=10**8), 0.02)
        # off by default, and available on request
        fig = self.uv.view(show=False, return_fig=True)
        self.assertEqual(fig.get_axes()[0].collections[0].get_alpha(), 0.8)
        plt.close(fig)
        self.uv.view_specs["alpha"] = None
        fig = self.uv.view(show=False, return_fig=True)
        self.assertEqual(
            fig.get_axes()[0].collections[0].get_alpha(),
            Univar.get_dynamic_alpha(n_points=200),
        )
        plt.close(fig)

    def test_geo_data_panel_is_narrow(self):
        gv = self.get_geo()
        # 20% off the cell of the panel, which is 3 columns wide in the full layout
        fig = gv.view(show=False, return_fig=True)
        ax_data, ax_hist = fig.get_axes()[1:3]
        # the histogram takes 5 columns
        n_ratio = ax_data.get_position().width / ax_hist.get_position().width
        self.assertAlmostEqual(n_ratio, 0.8 * 3 / 5, delta=0.02)
        plt.close(fig)

    def test_geo_annotations(self):
        gv = self.get_geo()
        fig = gv.view(show=False, return_fig=True)
        fig.canvas.draw()
        ax_map, ax_data, ax_hist = fig.get_axes()[:3]
        box_map = ax_map.get_window_extent()
        # all but the title
        ls_notes = [t for t in fig.texts if ":" in t.get_text()]
        ls_boxes = [t.get_window_extent() for t in ls_notes]
        self.assertEqual(len(ls_boxes), 13)
        # below the side panels and their labels, and never below the map
        n_top = min(ax_hist.get_tightbbox().y0, ax_data.get_tightbbox().y0)
        for box in ls_boxes:
            self.assertLessEqual(box.y1, n_top)
            self.assertGreaterEqual(box.y0, box_map.y0)
            self.assertGreater(box.x0, box_map.x1)
            self.assertLessEqual(box.x1, fig.bbox.width)
        # no median, which is the P50
        ls_text = [t.get_text() for t in fig.texts]
        self.assertFalse(any("median" in t for t in ls_text))
        self.assertTrue(any("P50" in t for t in ls_text))
        # the figure ends at the labels of the map, with little to spare
        n_low = ax_map.get_tightbbox().y0
        self.assertGreaterEqual(n_low, 0)
        n_mm = n_low / fig.dpi * 25.4
        self.assertLess(n_mm, 2)
        plt.close(fig)

    def test_text_columns_stay_above_limit(self):
        fig = plt.figure(figsize=(6, 3))
        ls_lines = [f"line {i}" for i in range(20)]
        Univar.plot_text_columns(
            fig=fig, ls_columns=[ls_lines], x=0.1, y=0.5, sep=0.2, y_min=0.2
        )
        fig.canvas.draw()
        self.assertEqual(len(fig.texts), 20)
        for t in fig.texts:
            n_y0 = t.get_window_extent().y0 / fig.bbox.height
            self.assertGreaterEqual(n_y0, 0.195)
        plt.close(fig)

    def test_geo_side_panels_have_same_width(self):
        gv = self.get_geo()
        for layout in ["full", "mini"]:
            with self.subTest(layout=layout):
                gv.view_specs["layout"] = layout
                fig = gv.view(show=False, return_fig=True)
                ax_hist, ax_cdf = fig.get_axes()[2:4]
                self.assertAlmostEqual(
                    ax_hist.get_position().width, ax_cdf.get_position().width
                )
                plt.close(fig)

    def count_bars(self, ax):
        # pieces of a color bar, apart from scatters and mean lines
        return sum(isinstance(c, PolyCollection) for c in ax.collections)

    def test_n_classes(self):
        vct_x = np.linspace(start=-51, stop=-50, num=50)
        gv = GeoUnivar(name="Geo")
        gv.set_data(input_df=make_points(x=vct_x, y=vct_x + 21), input_varfield="soc")
        gv.view_specs["n_classes_cmap"] = 3
        gv.view_specs["cbar_scatter"] = True
        gv.view_specs["cbar_histh"] = True
        fig = gv.view(show=False, return_fig=True)
        fig.canvas.draw()
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
        fig.canvas.draw()
        ax_data = fig.get_axes()[0]
        vct_colors = ax_data.collections[0].get_facecolor()
        self.assertEqual(len(np.unique(vct_colors, axis=0)), 3)
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
