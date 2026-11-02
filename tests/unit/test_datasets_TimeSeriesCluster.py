# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
Unit tests for the ``TimeSeriesCluster`` class.

This module validates the cross-site behavior of ``TimeSeriesCluster``,
using small in-memory series with known values (no files are written).

Features
--------
The test suite verifies that:

* ``TimeSeriesCluster`` initializes as a same-variable collection.
* ``TimeSeriesEnsemble`` does not inherit the cross-site methods.
* Correlation matrices are symmetric, exact for known series, and respect overlap.
* Interpolation weights are uniform or inverse-distance as requested.
* Gaps are filled from other sites, aligned by datetime, without touching observed values.
* Figures are built for the cluster layouts without writing files.
* The stacked layout of a collection follows its panels, and bad panels raise.

"""
# IMPORTS
# ***********************************************************************
# import modules from other libs

# Native imports
# =======================================================================
import unittest
import warnings

# ... {develop}

# External imports
# =======================================================================
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ... {develop}

# Project-level imports
# =======================================================================
from plans.datasets import (
    RainSeries,
    TimeSeries,
    TimeSeriesCollection,
    TimeSeriesCluster,
    TimeSeriesEnsemble,
)

# ... {develop}


# CONSTANTS
# ***********************************************************************
# define constants in uppercase

N_SIZE = 60
GAP = (20, 30)  # larger than the default gapsize, so not interpolated

# ... {develop}

# FUNCTIONS
# ***********************************************************************


def make_series(name, values, x=0.0, y=0.0, start="2020-01-01"):
    """
    Make a daily ``TimeSeries`` with the given values and coordinates.
    """
    ts = TimeSeries(name=name, alias=name)
    df = pd.DataFrame(
        {
            "datetime": pd.date_range(start=start, periods=len(values), freq="D"),
            "v": values,
        }
    )
    ts.set_data(
        input_df=df, input_dtfield="datetime", input_varfield="v", dropnan=False
    )
    ts.x = x
    ts.y = y
    return ts


def make_cluster(ls_series):
    """
    Make a ``TimeSeriesCluster`` from a list of series.
    """
    tsc = TimeSeriesCluster(name="TestCluster", base_object=TimeSeries)
    for ts in ls_series:
        tsc.append(new_object=ts)
    tsc.update(details=True)
    return tsc


def get_values(tsc, name):
    """
    Get values of a series indexed by datetime.
    """
    ts = tsc.collection[name]
    return ts.data.set_index(ts.dtfield)[ts.varfield]


# CLASSES
# ***********************************************************************


class TestTimeSeriesCluster(unittest.TestCase):

    def setUp(self):
        rng = np.random.default_rng(seed=42)
        self.signal = rng.normal(loc=10, scale=2, size=N_SIZE)

    def test_initialization(self):
        tsc = TimeSeriesCluster(name="TestCluster", base_object=TimeSeries)
        self.assertIsInstance(tsc, TimeSeriesCollection)
        self.assertEqual(tsc.varname, TimeSeries().varname)
        # ensemble is not a cluster
        tse = TimeSeriesEnsemble(name="TestEnsemble", base_object=TimeSeries)
        self.assertNotIsInstance(tse, TimeSeriesCluster)
        self.assertFalse(hasattr(tse, "regionalize"))

    def test_get_correlation(self):
        tsc = make_cluster(
            ls_series=[
                make_series(name="A", values=self.signal),
                make_series(name="B", values=2 * self.signal + 1),
                make_series(name="C", values=-self.signal),
            ]
        )
        df = tsc.get_correlation(method="pearson")
        self.assertListEqual(list(df.index), ["A", "B", "C"])
        np.testing.assert_allclose(df.values, df.values.T)
        self.assertAlmostEqual(df.loc["A", "B"], 1.0)
        self.assertAlmostEqual(df.loc["A", "C"], -1.0)
        # too little overlap gives NaN
        df = tsc.get_correlation(min_overlap=N_SIZE + 1)
        self.assertTrue(df.isna().all().all())

    def test_get_weights_by_name(self):
        tsc = make_cluster(
            ls_series=[
                make_series(name="A", values=self.signal, x=0),
                make_series(name="B", values=self.signal, x=1),
                make_series(name="C", values=self.signal, x=3),
            ]
        )
        w = tsc.get_weights_by_name(name="A", method="average")
        np.testing.assert_array_equal(w, [1, 1])
        w = tsc.get_weights_by_name(name="A", method="idw")
        self.assertAlmostEqual(np.sum(w), 100)
        self.assertGreater(w[0], w[1])  # B is closer than C

    def test_regionalize(self):
        vct_a = np.full(N_SIZE, 5.0)
        vct_a[GAP[0] : GAP[1]] = np.nan
        tsc = make_cluster(
            ls_series=[
                make_series(name="A", values=vct_a),
                make_series(name="B", values=np.full(N_SIZE, 10.0)),
                # shifted span: only covers the second half of the gap
                make_series(name="C", values=np.full(N_SIZE, 30.0), start="2020-01-26"),
            ]
        )
        tsc.regionalize(method="average")
        s = get_values(tsc=tsc, name="A")
        dates = pd.date_range(start="2020-01-01", periods=N_SIZE, freq="D")
        # observed values unchanged
        self.assertTrue((s.loc[dates[: GAP[0]]] == 5.0).all())
        # first half of gap: only B available
        self.assertTrue((s.loc[dates[GAP[0] : 25]] == 10.0).all())
        # second half of gap: B and C averaged
        self.assertTrue((s.loc[dates[25 : GAP[1]]] == 20.0).all())

    def test_regionalize_fills_small_gaps_from_others(self):
        # no interpolation first: a 2-day gap takes the value of the other series
        vct_a = np.full(N_SIZE, 5.0)
        vct_a[10:12] = np.nan
        tsc = make_cluster(
            ls_series=[
                make_series(name="A", values=vct_a),
                make_series(name="B", values=np.full(N_SIZE, 10.0)),
            ]
        )
        tsc.regionalize(method="average")
        s = get_values(tsc=tsc, name="A")
        self.assertTrue((s.iloc[10:12] == 10.0).all())

    def test_regionalize_idw(self):
        vct_a = np.full(N_SIZE, 5.0)
        vct_a[GAP[0] : GAP[1]] = np.nan
        tsc = make_cluster(
            ls_series=[
                make_series(name="A", values=vct_a, x=0),
                make_series(name="B", values=np.full(N_SIZE, 10.0), x=1),
                make_series(name="C", values=np.full(N_SIZE, 30.0), x=9),
            ]
        )
        tsc.regionalize(method="idw")
        s = get_values(tsc=tsc, name="A")
        # weights 0.9 and 0.1 -> 0.9 * 10 + 0.1 * 30
        self.assertAlmostEqual(s.iloc[GAP[0]], 12.0, places=2)

    def test_view(self):
        tsc = make_cluster(
            ls_series=[
                make_series(name="A", values=self.signal),
                make_series(name="B", values=self.signal + 1),
            ]
        )
        ls_cases = [("series", 3), ("series-simple", 1), ("correlation", 2)]
        for layout, n_axes in ls_cases:
            with self.subTest(layout=layout):
                tsc.view_specs["layout"] = layout
                fig = tsc.view(show=False, return_fig=True)
                self.assertEqual(len(fig.get_axes()), n_axes)
                plt.close(fig)

    def test_view_large(self):
        tsc = make_cluster(
            ls_series=[
                make_series(name="S{:02d}".format(i), values=self.signal + i)
                for i in range(12)
            ]
        )
        tsc.view_specs["n_series_max"] = 10
        # series: no legend above the limit
        tsc.view_specs["layout"] = "series"
        fig = tsc.view(show=False, return_fig=True)
        self.assertIsNone(fig.get_axes()[0].get_legend())
        plt.close(fig)
        # series: highlights get a legend
        tsc.view_specs["highlight"] = ["S01", "S05"]
        fig = tsc.view(show=False, return_fig=True)
        legend = fig.get_axes()[0].get_legend()
        self.assertListEqual([t.get_text() for t in legend.get_texts()], ["S01", "S05"])
        plt.close(fig)
        # gantt and correlation: no per-series labels
        for layout in ["full", "correlation"]:
            with self.subTest(layout=layout):
                tsc.view_specs["layout"] = layout
                fig = tsc.view(show=False, return_fig=True)
                self.assertEqual(len(fig.get_axes()[0].get_yticks()), 0)
                plt.close(fig)


class TestSeriesLegend(unittest.TestCase):

    def test_legend_clear_of_titles(self):
        # long names in a narrow panel, and many names in a wide one
        ls_cases = [
            ("series", "Long name of series {}", 4),
            ("series-simple", "Gauge {}", 10),
            ("series-simple", "Long name of series {}", 8),
        ]
        for layout, s_name, n_series in ls_cases:
            with self.subTest(layout=layout, name=s_name, n_series=n_series):
                tsc = make_cluster(
                    ls_series=[
                        make_series(name=s_name.format(i), values=np.arange(N_SIZE))
                        for i in range(n_series)
                    ]
                )
                tsc.view_specs["layout"] = layout
                fig = tsc.view(show=False, return_fig=True)
                self.addCleanup(plt.close, fig)
                fig.canvas.draw()
                axes = fig.get_axes()
                legend = axes[0].get_legend()
                self.assertEqual(len(legend.get_texts()), n_series)
                box_legend = legend.get_window_extent()
                self.assertGreater(
                    box_legend.x0, axes[0]._left_title.get_window_extent().x1
                )
                box_title = fig._suptitle.get_window_extent()
                self.assertLessEqual(box_legend.y1, box_title.y0 + 0.01)
                # all panels stay aligned
                for ax in axes:
                    self.assertAlmostEqual(
                        ax.get_position().y1, axes[0].get_position().y1, places=6
                    )


class TestStackedLayout(unittest.TestCase):

    def setUp(self):
        self.tsc = TimeSeriesCollection(name="Basin", base_object=TimeSeries)
        rng = np.random.default_rng(seed=1)
        for name, units in [("A", "mm"), ("B", "mm"), ("C", "m3/s")]:
            ts = make_series(name=name, values=rng.normal(size=N_SIZE))
            ts.units = units
            self.tsc.append(new_object=ts)
        self.tsc.update(details=True)
        self.tsc.view_specs["layout"] = "stacked-simple"

    def get_fig(self):
        fig = self.tsc.view(show=False, return_fig=True)
        fig.canvas.draw()
        self.addCleanup(plt.close, fig)
        return fig

    def test_default_panels(self):
        # one series per panel, in catalog order
        fig = self.get_fig()
        axes = fig.get_axes()
        self.assertEqual(len(axes), 3)
        self.assertListEqual([ax.get_title(loc="left") for ax in axes], ["A", "B", "C"])

    def test_panels(self):
        self.tsc.collection["A"].view_specs["color"] = "tab:red"
        self.tsc.view_specs["panels"] = [["A", "B"], ["C"]]
        ax_first, ax_last = self.get_fig().get_axes()
        self.assertEqual(len(ax_first.get_lines()), 2)
        # legend only where there is more than one series
        legend = ax_first.get_legend()
        self.assertListEqual([t.get_text() for t in legend.get_texts()], ["A", "B"])
        self.assertIsNone(ax_last.get_legend())
        # the range covers all series of the panel
        vmax = max(self.tsc.collection[n].data["v"].max() for n in ["A", "B"])
        self.assertGreaterEqual(ax_first.get_ylim()[1], vmax)
        # own color first, and repeated colors are replaced
        line_a, line_b = ax_first.get_lines()
        self.assertEqual(line_a.get_color(), "tab:red")
        self.assertNotEqual(line_b.get_color(), "tab:red")
        ax_lone = ax_last.get_lines()[0]
        self.assertEqual(ax_lone.get_color(), self.tsc.collection["C"].rawcolor)

    def test_standardize_keeps_gaps(self):
        ts = make_series(name="D", values=np.arange(1.0, N_SIZE + 1))
        ts.data.loc[10:11, ts.varfield] = np.nan
        self.tsc.append(new_object=ts)
        self.tsc.update(details=True)
        self.tsc.standardize()
        ts_d = self.tsc.collection["D"]
        self.assertEqual(ts_d.data[ts_d.varfield].isna().sum(), 2)

    def test_time_axis_defaults(self):
        # the largest range of all series, with padding, and no panel letters
        ts = make_series(name="D", values=np.arange(N_SIZE), start="2021-01-01")
        self.tsc.append(new_object=ts)
        self.tsc.update(details=True)
        vct_num = mdates.date2num([self.tsc.start, self.tsc.end])
        delta = 0.05 * (vct_num[1] - vct_num[0])
        for layout in ["full", "stacked"]:
            with self.subTest(layout=layout):
                self.tsc.view_specs["layout"] = layout
                ax = self.get_fig().get_axes()[0]
                np.testing.assert_allclose(
                    ax.get_xlim(), [vct_num[0] - delta, vct_num[1] + delta]
                )
                self.assertEqual(len(ax.get_xticks()), 5)
        self.tsc.view_specs["layout"] = "full"
        self.assertEqual(
            self.get_fig().get_axes()[0].get_title(loc="left")[:5], "Gantt"
        )

    def test_repeated_color_is_distinct(self):
        for name in ["A", "B"]:
            self.tsc.collection[name].view_specs["color"] = "blue"
        self.tsc.view_specs["panels"] = [["A", "B"], ["C"]]
        line_a, line_b = self.get_fig().get_axes()[0].get_lines()
        vct_a = matplotlib.colors.to_rgb(line_a.get_color())
        vct_b = matplotlib.colors.to_rgb(line_b.get_color())
        # tab:blue would be the next color of the map, at about 0.63
        self.assertGreater(np.linalg.norm(np.subtract(vct_a, vct_b)), 1)

    def test_view_leaves_series(self):
        ts = make_series(name="D", values=np.arange(1.0, N_SIZE + 1))
        vct_gap = ts.data[ts.varfield].values.copy()
        vct_gap[10:30] = np.nan
        ts.data[ts.varfield] = vct_gap
        self.tsc.append(new_object=ts)
        self.tsc.update(details=True)
        ts_d = self.tsc.collection["D"]
        ts_d.view_specs["color"] = "tab:green"
        df_before = ts_d.data.copy()
        for layout in ["full", "simple"]:
            with self.subTest(layout=layout):
                self.tsc.view_specs["layout"] = layout
                self.get_fig()
                pd.testing.assert_frame_equal(ts_d.data, df_before)
                self.assertEqual(ts_d.view_specs["color"], "tab:green")
                self.assertFalse(ts_d.is_standard)

    def test_view_shows_gaps_of_sums(self):
        vct_dates = pd.date_range(start="2020-01-01", periods=100, freq="D")
        vct_values = np.ones(100)
        vct_values[40:60] = np.nan
        tsc = TimeSeriesCollection(name="Sums", base_object=RainSeries)
        ts = RainSeries(name="Rain")
        ts.set_data(
            input_df=pd.DataFrame({"datetime": vct_dates, "x": vct_values}),
            input_dtfield="datetime",
            input_varfield="x",
            dropnan=False,
        )
        tsc.append(new_object=ts)
        tsc.update(details=True)
        fig = tsc.view(show=False, return_fig=True)
        self.addCleanup(plt.close, fig)
        ls_labels = [t.get_text() for t in fig.get_axes()[2].get_yticklabels()]
        self.assertListEqual(ls_labels, ["80.0%"])

    def test_epochs_see_missing_timestamps(self):
        # rows dropped on loading: the overlap still finds the gap
        vct_dates = pd.date_range(start="2020-01-01", periods=100, freq="D")
        vct_values = np.ones(100)
        vct_values[40:60] = np.nan
        ts = TimeSeries(name="Dropped")
        ts.set_data(
            input_df=pd.DataFrame({"datetime": vct_dates, "x": vct_values}),
            input_dtfield="datetime",
            input_varfield="x",
            dropnan=True,
        )
        tsc = TimeSeriesCollection(name="Dropped", base_object=TimeSeries)
        tsc.append(new_object=ts)
        tsc.update(details=True)
        df = tsc.get_epochs()
        self.assertEqual(len(df), 100)
        self.assertEqual((df[ts.epochs_id_field] == 0).sum(), 20)
        self.assertEqual(len(tsc.collection["Dropped"].data), 80)

    def test_no_date_warning(self):
        # records of nearly 3 years, the worst case for the date ticks
        ts = TimeSeries(name="Long")
        ts.generate(start="2019-01-01", end="2021-12-31", seed=1, inplace=True)
        tsc = TimeSeriesCollection(name="Long", base_object=TimeSeries)
        tsc.append(new_object=ts)
        tsc.update(details=True)
        tsc.view_specs["layout"] = "stacked-simple"
        fig = tsc.view(show=False, return_fig=True)
        self.addCleanup(plt.close, fig)
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            fig.canvas.draw()

    def test_shared_time_axis(self):
        ax_first, _, ax_last = self.get_fig().get_axes()
        self.assertEqual(ax_first.get_xlim(), ax_last.get_xlim())
        self.assertEqual(ax_first.get_xlabel(), "")
        self.assertEqual(ax_last.get_xlabel(), "Date")
        self.assertTrue(ax_first.xaxis.get_tick_params()["labelbottom"])
        self.assertTrue(ax_last.xaxis.get_tick_params()["labelbottom"])

    def test_side_panels_have_same_width(self):
        self.tsc.view_specs["layout"] = "stacked"
        axes = self.get_fig().get_axes()
        self.assertAlmostEqual(
            axes[1].get_position().width, axes[2].get_position().width
        )

    def test_tick_labels_on_all_panels(self):
        self.tsc.view_specs["layout"] = "stacked"
        fig = self.get_fig()
        fig.canvas.draw()
        axes = fig.get_axes()
        for ax in axes:
            self.assertTrue(any(t.get_text() for t in ax.get_xticklabels()))
            self.assertTrue(any(t.get_text() for t in ax.get_yticklabels()))
        # axis labels of the time, histogram and CDF only on the last panel
        for ax in axes[:-3]:
            self.assertEqual(ax.get_xlabel(), "")
        for ax in axes[-3:]:
            self.assertNotEqual(ax.get_xlabel(), "")
        # no y axis labels on the sides
        self.assertEqual(axes[1].get_ylabel(), "")
        self.assertEqual(axes[2].get_ylabel(), "")

    def test_lateral_panels(self):
        self.tsc.view_specs["layout"] = "stacked"
        self.tsc.view_specs["panels"] = [["A", "B"], ["C"]]
        axes = self.get_fig().get_axes()
        self.assertEqual(len(axes), 6)
        ax_series, ax_hist, ax_cdf = axes[:3]
        # titles once, and aligned with the series panel
        self.assertEqual(ax_hist.get_title(loc="left"), "Histogram")
        self.assertEqual(ax_cdf.get_title(loc="left"), "CDF")
        self.assertEqual(axes[4].get_title(loc="left"), "")
        self.assertEqual(ax_hist.get_ylim(), ax_series.get_ylim())
        self.assertEqual(ax_cdf.get_ylim(), ax_series.get_ylim())
        # shared panel: overlaid in the colors of the series
        line_a = ax_series.get_lines()[0]
        self.assertEqual(ax_cdf.get_lines()[0].get_color(), line_a.get_color())
        self.assertEqual(len(ax_hist.containers), 2)
        # lone series: colors of its own view specs
        ts = self.tsc.collection["C"]
        self.assertEqual(axes[5].get_lines()[0].get_color(), ts.view_specs["color_cdf"])
        # x labels only below the last panel
        self.assertEqual(ax_hist.get_xlabel(), "")
        self.assertEqual(axes[4].get_xlabel(), "%")
        self.assertEqual(ax_series.get_xlabel(), "")
        self.assertEqual(axes[3].get_xlabel(), "Date")

    def test_title_near_own_panel(self):
        self.tsc.view_specs["panels"] = [["A"], ["B"]]
        fig = self.get_fig()
        ax_first, ax_last = fig.get_axes()
        box_title = ax_last._left_title.get_window_extent()
        gap_own = box_title.y0 - ax_last.get_window_extent().y1
        gap_other = ax_first.get_window_extent().y0 - box_title.y1
        self.assertLess(gap_own, gap_other)

    def test_panel_heights(self):
        self.tsc.view_specs["panels"] = [["A"], ["B"]]
        self.tsc.view_specs["panel_heights"] = [3, 1]
        ax_first, ax_last = self.get_fig().get_axes()
        ratio = ax_first.get_position().height / ax_last.get_position().height
        self.assertGreater(ratio, 2.5)

    def test_figure_height(self):
        self.tsc.view_specs["panels"] = [["A"], ["B"]]
        h_two = self.get_fig().get_size_inches()[1]
        self.tsc.view_specs["panels"] = [["A"], ["B"], ["C"]]
        self.assertGreater(self.get_fig().get_size_inches()[1], h_two)

    def test_errors(self):
        ls_cases = [
            ({"panels": [["A"], ["banana"]]}, "banana"),
            ({"panels": [["A", "C"]]}, "same units"),
            ({"panels": [["A"], []]}, "Empty panel"),
            ({"panels": [["A"], ["B"]], "panel_heights": [1]}, "panel heights"),
            ({"panels": [["A"]], "panel_heights": [0]}, "positive"),
            ({"layout": "stacked-5"}, "stacked-5"),
        ]
        for dc_specs, regex in ls_cases:
            with self.subTest(regex=regex):
                self.tsc.view_specs.update(
                    {"layout": "stacked", "panels": None, "panel_heights": None}
                )
                self.tsc.view_specs.update(dc_specs)
                with self.assertRaisesRegex(ValueError, regex):
                    self.tsc.view(show=False, return_fig=True)


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
