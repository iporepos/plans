# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
Unit tests for the ``TimeSeries`` class.

This module validates the behavior of ``TimeSeries`` using small in-memory
series (no files are written).

Features
--------
The test suite verifies that:

* ``standardize`` builds a regular grid at day resolution, padding sub-daily
  series to whole days without spilling into the next day.
* ``interpolate_gaps`` fills small gaps without losing the edge values.

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
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd

# ... {develop}

# Project-level imports
# =======================================================================
from plans import viewer
from plans.datasets import (
    DischargeSeries,
    RainSeries,
    TemperatureSeries,
    TimeSeries,
)

# ... {develop}


# CONSTANTS
# ***********************************************************************
# define constants in uppercase

# ... {develop}

# FUNCTIONS
# ***********************************************************************


def make_series(dates):
    """
    Make a ``TimeSeries`` with ones on the given dates.
    """
    ts = TimeSeries(name="TestTS", alias="TS")
    df = pd.DataFrame({"datetime": dates, "v": np.ones(len(dates))})
    ts.set_data(input_df=df, input_dtfield="datetime", input_varfield="v")
    return ts


# CLASSES
# ***********************************************************************


class TestTimeSeries(unittest.TestCase):

    def get_gap_series(self, cls, dropnan):
        # daily series without values in March
        vct_dates = pd.date_range(start="2020-01-01", end="2020-06-30", freq="D")
        vct_values = np.ones(len(vct_dates))
        is_march = (vct_dates >= "2020-03-01") & (vct_dates <= "2020-03-31")
        vct_values[is_march] = np.nan
        ts = cls(name="Gap")
        ts.set_data(
            input_df=pd.DataFrame({"datetime": vct_dates, "x": vct_values}),
            input_dtfield="datetime",
            input_varfield="x",
            dropnan=dropnan,
        )
        return ts

    def test_standardize_keeps_gaps(self):
        for cls in [RainSeries, TemperatureSeries]:
            for dropnan in [True, False]:
                with self.subTest(cls=cls.__name__, dropnan=dropnan):
                    ts = self.get_gap_series(cls=cls, dropnan=dropnan)
                    ts.standardize()
                    vct = ts.data[ts.varfield]
                    self.assertEqual(vct.isna().sum(), 31)
                    self.assertEqual((vct == 0).sum(), 0)

    def test_scale_up_keeps_gaps(self):
        for dropnan in [True, False]:
            for bad_max in [0, 100]:
                with self.subTest(dropnan=dropnan, bad_max=bad_max):
                    ts = self.get_gap_series(cls=RainSeries, dropnan=dropnan)
                    ts.scale_up(freq="MS", bad_max=bad_max, inplace=True)
                    vct = ts.data[ts.varfield].values
                    self.assertTrue(np.isnan(vct[2]))
                    self.assertEqual(vct[0], 31)

    def test_gaps_stay_after_set_data(self):
        ts = self.get_gap_series(cls=TimeSeries, dropnan=False)
        ts_default = TimeSeries(name="Default")
        ts_default.set_data(
            input_df=ts.data, input_dtfield=ts.dtfield, input_varfield=ts.varfield
        )
        self.assertEqual(ts_default.data[ts.varfield].isna().sum(), 31)

    def test_reads_leave_series(self):
        # missing timestamps, and the gaps still found
        ts = self.get_gap_series(cls=TimeSeries, dropnan=True)
        ts.view_specs["color"] = "tab:green"
        df_before = ts.data.copy()
        df_epochs = ts.get_epochs()
        df_interp = ts.interpolate_gaps(inplace=False)
        ts.update_epochs_stats()
        pd.testing.assert_frame_equal(ts.data, df_before)
        self.assertFalse(ts.is_standard)
        self.assertEqual(ts.view_specs["color"], "tab:green")
        self.assertEqual((df_epochs[ts.epochs_id_field] == 0).sum(), 31)
        self.assertEqual(len(df_interp), len(df_epochs))
        self.assertEqual(ts.epochs_n, 2)

    def test_update_keeps_user_specs(self):
        ts = self.get_gap_series(cls=RainSeries, dropnan=False)
        s_title = ts.view_specs["title"]
        ts.view_specs["color"] = "tab:green"
        ts.view_specs["range"] = [0, 5]
        ts.name = "Other"
        ts.standardize()
        self.assertEqual(ts.view_specs["color"], "tab:green")
        self.assertEqual(ts.view_specs["range"], [0, 5])
        # the defaults still follow the object
        self.assertNotEqual(ts.view_specs["title"], s_title)

    def test_update_refreshes_default_limits(self):
        ts = self.get_gap_series(cls=TimeSeries, dropnan=False)
        ts.data[ts.varfield] = ts.data[ts.varfield] * 10
        ts.update()
        self.assertEqual(ts.view_specs["ymax"], 10)

    def test_interpolate_inplace_standardizes(self):
        ts = self.get_gap_series(cls=TimeSeries, dropnan=True)
        n_size = len(ts.data)
        ts.interpolate_gaps(inplace=True)
        self.assertTrue(ts.is_standard)
        self.assertEqual(len(ts.data), n_size + 31)

    def test_set_data_resets_standard(self):
        ts = self.get_gap_series(cls=TimeSeries, dropnan=False)
        ts.standardize()
        df = ts.data.copy()
        ts.set_data(input_df=df, input_dtfield=ts.dtfield, input_varfield=ts.varfield)
        self.assertFalse(ts.is_standard)

    def test_fit_rejects_gaps(self):
        ts = self.get_gap_series(cls=TimeSeries, dropnan=False)
        with self.assertRaises(ValueError):
            ts.fit()

    def get_generated(self):
        ts = TimeSeries(name="Generated")
        ts.generate(start="2015-01-01", end="2019-12-31", seed=1, inplace=True)
        return ts

    def get_fig(self, ts, layout):
        ts.view_specs["layout"] = layout
        fig = ts.view(show=False, return_fig=True)
        self.addCleanup(plt.close, fig)
        fig.canvas.draw()
        return fig

    def test_y_title_only_on_data_panel(self):
        ax_data, ax_hist, ax_cdf = self.get_fig(
            ts=self.get_generated(), layout="mini"
        ).get_axes()
        self.assertNotEqual(ax_data.get_ylabel(), "")
        self.assertEqual(ax_hist.get_ylabel(), "")
        self.assertEqual(ax_cdf.get_ylabel(), "")

    def test_side_panels_have_same_width(self):
        ts = self.get_generated()
        for layout in ["full", "mini"]:
            with self.subTest(layout=layout):
                _, ax_hist, ax_cdf = self.get_fig(ts=ts, layout=layout).get_axes()
                self.assertAlmostEqual(
                    ax_hist.get_position().width, ax_cdf.get_position().width
                )

    def test_shallow_titles_are_stacked(self):
        fig = self.get_fig(ts=self.get_generated(), layout="simple-shallow")
        box_title = fig.get_axes()[0]._left_title.get_window_extent()
        self.assertLess(box_title.y1, fig._suptitle.get_window_extent().y0)

    def test_time_axis_defaults(self):
        ts = self.get_generated()
        ax = self.get_fig(ts=ts, layout="simple").get_axes()[0]
        self.assertEqual(len(ax.get_xticks()), 5)
        vct_num = mdates.date2num([ts.start, ts.end])
        delta = 0.05 * (vct_num[1] - vct_num[0])
        np.testing.assert_allclose(
            ax.get_xlim(), [vct_num[0] - delta, vct_num[1] + delta]
        )

    def test_range_x_has_no_padding(self):
        ts = self.get_generated()
        ls_range = [pd.Timestamp("2016-01-01"), pd.Timestamp("2017-01-01")]
        ts.view_specs["range_x"] = ls_range
        ax = self.get_fig(ts=ts, layout="simple").get_axes()[0]
        np.testing.assert_allclose(ax.get_xlim(), mdates.date2num(ls_range))

    def test_epochs_layout(self):
        ts = self.get_gap_series(cls=TimeSeries, dropnan=True)
        df_before = ts.data.copy()
        fig = self.get_fig(ts=ts, layout="epochs")
        ax, ax_legend = fig.get_axes()
        # two epochs on the series panel, and the list on the side
        self.assertEqual(len(ax.get_lines()), 2)
        ls_labels = [t.get_text() for t in ax_legend.get_legend().get_texts()]
        self.assertListEqual(ls_labels, ["Gaps", "Epoch 1", "Epoch 2"])
        pd.testing.assert_frame_equal(ts.data, df_before)

    def test_decompose(self):
        ts = self.get_generated()
        df_before = ts.data.copy()
        df = ts.decompose()
        vct_sum = df["trend"] + df["cycle"] + df["remainder"]
        np.testing.assert_allclose(vct_sum, ts.data[ts.varfield])
        pd.testing.assert_frame_equal(ts.data, df_before)

    def test_decompose_rejects_gaps(self):
        ts = self.get_gap_series(cls=TimeSeries, dropnan=False)
        with self.assertRaises(ValueError):
            ts.decompose(params=self.get_generated().fit())

    def test_decompose_moves_params(self):
        # the same parts for the same dates, whatever the origin of the parameters
        ts = self.get_generated()
        params = ts.fit()
        df_new = ts.generate(start="2017-01-01", end="2017-12-31", seed=2)
        ts_new = TimeSeries(name="New")
        ts_new.set_data(
            input_df=df_new, input_dtfield=ts.dtfield, input_varfield=ts.varfield
        )
        df_all = ts.decompose(params=params).set_index(ts.dtfield)
        df = ts_new.decompose(params=params).set_index(ts.dtfield)
        np.testing.assert_allclose(
            df["trend"], df_all.loc[df.index, "trend"], atol=1e-6
        )

    def get_hourly_gaps(self):
        # small gap, large gap and a large gap at the end
        vct_dates = pd.date_range(start="2020-01-01", periods=200, freq="h")
        vct_values = np.arange(200.0)
        vct_values[50:52] = np.nan
        vct_values[100:120] = np.nan
        vct_values[180:] = np.nan
        ts = TimeSeries(name="Gaps")
        ts.set_data(
            input_df=pd.DataFrame({"datetime": vct_dates, "x": vct_values}),
            input_dtfield="datetime",
            input_varfield="x",
        )
        return ts

    def test_gap_at_the_end_is_not_filled(self):
        ts = self.get_hourly_gaps()
        df = ts.interpolate_gaps(inplace=False)
        s_filled = df[f"{ts.varfield}_interpolation"]
        self.assertTrue(s_filled.iloc[180:].isna().all())
        self.assertTrue((ts.get_epochs()[ts.epochs_id_field].iloc[180:] == 0).all())

    def test_edges_are_not_extrapolated(self):
        # last two records are missing, which is below the gap size
        ts = self.get_hourly_gaps()
        ts.data.loc[120:, ts.varfield] = np.arange(120.0, 200.0)
        ts.data.loc[198:, ts.varfield] = np.nan
        df = ts.interpolate_gaps(inplace=False)
        self.assertTrue(df[f"{ts.varfield}_interpolation"].iloc[198:].isna().all())

    def test_flag_marks_only_filled_records(self):
        ts = self.get_hourly_gaps()
        df = ts.interpolate_gaps(inplace=False)
        self.assertListEqual(list(df.index[df["is_interpolation"] == 1]), [50, 51])
        np.testing.assert_allclose(
            df[f"{ts.varfield}_interpolation"].iloc[50:52], [50, 51]
        )

    def test_epochs_layout_shows_small_gaps(self):
        ts = self.get_hourly_gaps()
        ax = self.get_fig(ts=ts, layout="epochs").get_axes()[0]
        coll = ax.collections[-1]
        self.assertGreater(coll.get_linewidth()[0], 0)
        # one area for each run of missing records
        self.assertEqual(len(coll.get_paths()), 2)

    def test_generate_returns_dataframe(self):
        ts = TemperatureSeries(name="Sim")
        df = ts.generate(start="2000-01-01", end="2000-12-31", seed=1)
        self.assertIsNone(ts.data)
        self.assertListEqual(list(df.columns), [ts.dtfield, ts.varfield])
        self.assertEqual(len(df), 366)

    def test_generate_inplace(self):
        ts = TemperatureSeries(name="Sim")
        output = ts.generate(start="2000-01-01", end="2000-12-31", seed=1, inplace=True)
        self.assertIsNone(output)
        self.assertEqual(len(ts.data), 366)
        self.assertEqual(ts.dtfreq, "D")

    def test_generate_seed(self):
        ts = TimeSeries()
        kwargs = {"start": "2000-01-01", "end": "2001-12-31"}
        a = ts.generate(seed=1, **kwargs)[ts.varfield].values
        b = ts.generate(seed=1, **kwargs)[ts.varfield].values
        c = ts.generate(seed=2, **kwargs)[ts.varfield].values
        np.testing.assert_array_equal(a, b)
        self.assertFalse(np.array_equal(a, c))

    def test_generate_specs_by_step(self):
        # the season follows the calendar at any step, and the specs can be edited
        ts = TemperatureSeries()
        ts.generator_specs.update(
            {"remainder_sd": 0.0, "peak_day": 200, "change_per_year": 0}
        )
        for freq, tolerance in [("D", 1), ("7D", 7), ("MS", 31)]:
            with self.subTest(freq=freq):
                df = ts.generate(start="2001-03-10", end="2002-03-09", freq=freq)
                peak = df.loc[df[ts.varfield].idxmax(), ts.dtfield]
                self.assertLessEqual(abs(peak.dayofyear - 200), tolerance)
                self.assertAlmostEqual(df[ts.varfield].max(), 28.0, delta=0.5)

    def test_generate_memory_by_step(self):
        ts = TimeSeries()
        for freq, step_days in [("D", 1.0), ("h", 1 / 24)]:
            with self.subTest(freq=freq):
                params = ts._get_generator_params(
                    start=pd.Timestamp("2000-01-01"), freq=freq, n=10
                )
                self.assertAlmostEqual(params["phi"], np.exp(-step_days / 5.0))

    def test_generate_sum_scales_with_step(self):
        # variables aggregated by sum are given per day
        ts = RainSeries()
        ts.generator_specs["remainder_sd"] = 0.0
        kwargs = {"start": "2000-01-01", "end": "2019-12-31"}
        daily = ts.generate(freq="D", **kwargs)[ts.varfield]
        monthly = ts.generate(freq="MS", **kwargs)[ts.varfield]
        self.assertAlmostEqual(monthly.mean() / daily.mean(), 365.2425 / 12, delta=0.1)

    def test_generate_floor(self):
        for ts in [RainSeries(), DischargeSeries()]:
            with self.subTest(name=type(ts).__name__):
                ts.generator_specs["remainder_sd"] = 50.0
                df = ts.generate(start="2000-01-01", end="2000-12-31", seed=1)
                self.assertEqual(df[ts.varfield].min(), 0.0)
        # no floor by default
        ts = TimeSeries()
        ts.generator_specs["remainder_sd"] = 50.0
        df = ts.generate(start="2000-01-01", end="2000-12-31", seed=1)
        self.assertLess(df[ts.varfield].min(), 0.0)

    def test_generate_errors(self):
        ts = TimeSeries()
        with self.assertRaises(ValueError):
            ts.generate(start="2000-01-01", end="2010-01-01", freq="YS")
        with self.assertRaises(ValueError):
            ts.generate(start="2001-01-01", end="2000-01-01")
        params = {"freq": "MS"}
        with self.assertRaises(ValueError):
            ts.generate(start="2000-01-01", end="2001-01-01", freq="D", params=params)

    def test_fit_recovery(self):
        ts = TemperatureSeries()
        ts.generate(start="2000-01-01", end="2019-12-31", seed=1, inplace=True)
        before = ts.data.copy()
        params = ts.fit()
        pd.testing.assert_frame_equal(ts.data, before)
        self.assertEqual(params["freq"], "D")
        self.assertEqual(params["origin"], "2000-01-01 00:00:00")
        self.assertAlmostEqual(params["amplitude"], 10.0, delta=0.5)
        self.assertAlmostEqual(params["phi"], np.exp(-1 / 3.0), delta=0.03)
        # peak of the season at day 15 of the year
        self.assertAlmostEqual(params["phase"], 14.0, delta=2.0)

    def test_fit_measures_step(self):
        # dtfreq labels this data as hourly, while its step is 3 hours
        ts = TimeSeries()
        ts.generate(
            start="2000-01-01", end="2003-12-31", freq="3h", seed=1, inplace=True
        )
        self.assertEqual(ts.dtfreq, "h")
        params = ts.fit()
        self.assertEqual(params["freq"], "3h")
        self.assertAlmostEqual(params["period"], 365.2425 * 8)

    def test_fit_three_years(self):
        # three non-leap years are slightly under 3 cycles of 365.2425 days
        ts = TimeSeries()
        ts.generate(start="2001-01-01", end="2003-12-31", seed=1, inplace=True)
        self.assertEqual(len(ts.data), 1095)
        self.assertEqual(ts.fit()["freq"], "D")

    def test_fit_errors(self):
        with self.assertRaises(ValueError):
            TimeSeries().fit()
        # rows dropped by set_data leave no NaN behind, only a jump in the timestamps
        for freq in ["D", "MS"]:
            with self.subTest(freq=freq):
                ts = TimeSeries()
                ts.generate(
                    start="2000-01-01",
                    end="2009-12-31",
                    freq=freq,
                    seed=1,
                    inplace=True,
                )
                ts.data = ts.data.drop(index=[20, 21, 22])
                with self.assertRaises(ValueError):
                    ts.fit()
        # too short
        ts = TimeSeries()
        ts.generate(start="2000-01-01", end="2001-12-31", seed=1, inplace=True)
        with self.assertRaises(ValueError):
            ts.fit()

    def test_fit_generate_any_start(self):
        # without noise, a later start continues the same trend and season
        ts = TimeSeries()
        ts.generator_specs["change_per_year"] = 0.5
        for freq, delta in [("D", 1e-6), ("MS", 0.5)]:
            with self.subTest(freq=freq):
                ts.generate(
                    start="2000-01-01",
                    end="2019-12-31",
                    freq=freq,
                    seed=1,
                    inplace=True,
                )
                params = dict(ts.fit(), sigma=0.0)
                long = ts.generate(start="2000-01-01", end="2039-12-31", params=params)
                late = ts.generate(start="2030-01-01", end="2039-12-31", params=params)
                df = late.merge(long, on=ts.dtfield, suffixes=("_late", "_long"))
                self.assertEqual(len(df), len(late))
                diff = df[f"{ts.varfield}_late"] - df[f"{ts.varfield}_long"]
                self.assertLess(diff.abs().max(), delta)

    def test_view_range(self):
        ts = TimeSeries(name="Outlier")
        ts.generate(start="2020-01-01", end="2021-12-31", seed=1, inplace=True)
        ts.data.loc[100, ts.varfield] = 100.0
        ts.update()

        # all panels share the y limits and show the highest value
        fig = ts.view(show=False, return_fig=True)
        axes = fig.get_axes()
        for ax in axes:
            self.assertEqual(ax.get_ylim(), axes[0].get_ylim())
            self.assertLessEqual(ax.get_ylim()[0], ts.view_specs["range"][0])
            self.assertEqual(ax.get_ylim()[1], ts.view_specs["range"][1])
            self.assertGreater(ax.get_ylim()[1], 100.0)
        plt.close(fig)

    def test_clear_xticks(self):
        def get_gap(ax):
            # distance in points of the lowest y grid line to the bottom
            y0, y1 = ax.get_ylim()
            px = ax.get_yaxis_transform().transform
            ls = [px((0, y))[1] for y in ax.get_yticks() if y0 <= y < y1]
            return (min(ls) - px((0, y0))[1]) * 72 / ax.figure.dpi

        viewer.set_style(style="wien")
        length = plt.rcParams["xtick.major.size"]

        # a grid line across the ticks moves away, the others stay
        fig, axes = plt.subplots(ncols=2)
        for ax in axes:
            ax.set_ylim(12.35, 33.6)
        self.assertLess(get_gap(ax=axes[0]), length)
        viewer.clear_xticks(axes=list(axes))
        self.assertGreaterEqual(get_gap(ax=axes[0]), length)
        self.assertEqual(axes[0].get_ylim(), axes[1].get_ylim())
        self.assertEqual(axes[0].get_ylim()[1], 33.6)
        plt.close(fig)

        # far from the bottom or right at it: limits stay
        for ylim in [(11.0, 33.6), (10.0, 35.0)]:
            fig, ax = plt.subplots()
            ax.set_ylim(ylim)
            viewer.clear_xticks(axes=[ax])
            self.assertEqual(ax.get_ylim(), ylim)
            plt.close(fig)

    def test_compare_range(self):
        low, high = TimeSeries(name="Low"), TimeSeries(name="High")
        high.generator_specs.update(baseline=30.0, topline=40.0)
        for ts in (low, high):
            ts.generate(start="2020-01-01", end="2021-12-31", seed=1, inplace=True)

        # both series fit on every panel, in either order
        for first, second in [(low, high), (high, low)]:
            fig = TimeSeries.view_compare_times_series(
                first, second, specs={"title": "Compare"}, return_fig=True
            )
            for ax in fig.get_axes():
                y0, y1 = ax.get_ylim()
                self.assertLess(y0, low.var_min)
                self.assertGreater(y1, high.var_max)
            plt.close(fig)

        # a given range wins
        fig = TimeSeries.view_compare_times_series(
            low, high, specs={"title": "Compare", "range": [0, 50]}, return_fig=True
        )
        for ax in fig.get_axes():
            self.assertEqual(ax.get_ylim(), (0.0, 50.0))
        plt.close(fig)

    def test_standardize_grid(self):
        # frequency, data dates, expected grid start, expected grid end
        ls_cases = [
            (
                "D",
                pd.date_range(start="2021-01-01", end="2021-01-31", freq="D"),
                "2021-01-01",
                "2021-01-31",
            ),
            (
                "h",
                pd.date_range(
                    start="2021-01-01 10:00", end="2021-01-03 15:00", freq="h"
                ),
                "2021-01-01 00:00",
                "2021-01-03 23:00",
            ),
            (
                "MS",
                pd.date_range(start="2021-01-01", end="2021-12-01", freq="MS"),
                "2021-01-01",
                "2021-12-01",
            ),
        ]
        for freq, dates, start, end in ls_cases:
            with self.subTest(freq=freq):
                ts = make_series(dates=dates)
                ts.standardize()
                vct_dt = ts.data[ts.dtfield]
                self.assertEqual(vct_dt.min(), pd.Timestamp(start))
                self.assertEqual(vct_dt.max(), pd.Timestamp(end))
                # no gaps inside the data span
                s = ts.data.set_index(ts.dtfield)[ts.varfield]
                self.assertFalse(s.loc[dates[0] : dates[-1]].isna().any())

    def test_interpolate_gaps_keeps_edges(self):
        dates = pd.date_range(start="2021-01-01", periods=30, freq="D")
        ts = make_series(dates=dates)
        ts.data.loc[10:11, ts.varfield] = np.nan  # small gap
        ts.interpolate_gaps(inplace=True)
        vct = ts.data[ts.varfield].values
        # small gap filled and edges kept
        self.assertFalse(np.isnan(vct).any())
        self.assertEqual(vct[0], 1.0)
        self.assertEqual(vct[-1], 1.0)


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
