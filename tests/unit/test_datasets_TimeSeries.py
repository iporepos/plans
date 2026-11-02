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
            {"noise_sd": 0.0, "peak_day": 200, "change_per_year": 0}
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
        ts.generator_specs["noise_sd"] = 0.0
        kwargs = {"start": "2000-01-01", "end": "2019-12-31"}
        daily = ts.generate(freq="D", **kwargs)[ts.varfield]
        monthly = ts.generate(freq="MS", **kwargs)[ts.varfield]
        self.assertAlmostEqual(monthly.mean() / daily.mean(), 365.2425 / 12, delta=0.1)

    def test_generate_floor(self):
        for ts in [RainSeries(), DischargeSeries()]:
            with self.subTest(name=type(ts).__name__):
                ts.generator_specs["noise_sd"] = 50.0
                df = ts.generate(start="2000-01-01", end="2000-12-31", seed=1)
                self.assertEqual(df[ts.varfield].min(), 0.0)
        # no floor by default
        ts = TimeSeries()
        ts.generator_specs["noise_sd"] = 50.0
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
