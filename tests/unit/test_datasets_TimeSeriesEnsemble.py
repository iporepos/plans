# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
Unit tests for the ``TimeSeriesEnsemble`` class.

This module validates the reducers and views of ``TimeSeriesEnsemble``,
using small in-memory members with known values (no files are written).

Features
--------
The test suite verifies that:

* Reducers return exact values for members offset from each other.
* Reducers ignore missing values of members.
* Percentile outputs are named by their value (e.g., ``p05``).
* Reducers can be retrieved as series objects.
* The ``series`` view draws reducers and bands with their own legend entries.
* ``SeasonalEnsemble`` splits a series by year onto one reference year, for any
  first month of the year and any step that repeats each year.
* The ``SeasonalEnsemble`` view sets the x axis labels by mode.

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
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ... {develop}

# Project-level imports
# =======================================================================
from plans.datasets import (
    SeasonalEnsemble,
    TemperatureSeries,
    TimeSeries,
    TimeSeriesEnsemble,
)

# ... {develop}


# CONSTANTS
# ***********************************************************************
# define constants in uppercase

N_SIZE = 20
N_MEMBERS = 5

# ... {develop}

# FUNCTIONS
# ***********************************************************************


def make_ensemble(gap_member=None):
    """
    Make an ensemble of members ``base + k``, for k in 0..N_MEMBERS-1.
    Optionally, member ``gap_member`` has missing values on its first half.
    """
    tse = TimeSeriesEnsemble(name="TestEnsemble", base_object=TimeSeries)
    dates = pd.date_range(start="2021-01-01", periods=N_SIZE, freq="D")
    for k in range(N_MEMBERS):
        values = np.arange(N_SIZE, dtype=float) + k
        if k == gap_member:
            values[: N_SIZE // 2] = np.nan
        ts = TimeSeries(name=f"M{k}", alias=f"M{k}")
        ts.set_data(
            input_df=pd.DataFrame({"datetime": dates, "v": values}),
            input_dtfield="datetime",
            input_varfield="v",
            dropnan=False,
        )
        tse.append(new_object=ts)
    tse.update(details=True)
    return tse


def make_series(start, end, freq="D", cls=TimeSeries):
    """
    Make a series in which each step holds its calendar year as the value.
    """
    dates = pd.date_range(start=start, end=end, freq=freq)
    ts = cls(name="Source")
    ts.set_data(
        input_df=pd.DataFrame({"datetime": dates, "v": dates.year.astype(float)}),
        input_dtfield="datetime",
        input_varfield="v",
    )
    return ts


# CLASSES
# ***********************************************************************


class TestTimeSeriesEnsemble(unittest.TestCase):

    def setUp(self):
        self.tse = make_ensemble()
        self.base = np.arange(N_SIZE, dtype=float)

    def get_values(self, df):
        return df[df.columns[1]].values[:N_SIZE]

    def test_reducers(self):
        # members are base + 0..4
        np.testing.assert_allclose(self.get_values(self.tse.mean()), self.base + 2)
        np.testing.assert_allclose(self.get_values(self.tse.median()), self.base + 2)
        np.testing.assert_allclose(self.get_values(self.tse.min()), self.base)
        np.testing.assert_allclose(self.get_values(self.tse.max()), self.base + 4)
        np.testing.assert_allclose(self.get_values(self.tse.rng()), 4)
        np.testing.assert_allclose(
            self.get_values(self.tse.std()), np.std([0, 1, 2, 3, 4])
        )

    def test_reducers_ignore_nan(self):
        tse = make_ensemble(gap_member=4)
        vct = self.get_values(tse.mean())
        # first half: members 0..3 only
        np.testing.assert_allclose(vct[: N_SIZE // 2], self.base[: N_SIZE // 2] + 1.5)
        np.testing.assert_allclose(vct[N_SIZE // 2 :], self.base[N_SIZE // 2 :] + 2)

    def test_percentile_names(self):
        self.assertListEqual(list(self.tse.percentile(p=90).columns[1:]), ["Var_p90"])
        df = self.tse.percentiles(values=[5, 50, 2.5])
        self.assertListEqual(list(df.columns[1:]), ["Var_p05", "Var_p50", "Var_p2.5"])
        np.testing.assert_allclose(df["Var_p50"].values[:N_SIZE], self.base + 2)
        df = self.tse.stats(basic=True)
        self.assertListEqual(
            list(df.columns[1:]),
            [
                "Var_sum",
                "Var_mean",
                "Var_std",
                "Var_min",
                "Var_max",
                "Var_p25",
                "Var_p50",
                "Var_p75",
            ],
        )

    def test_get_reducer_series(self):
        ts = self.tse.get_reducer_series(name="p50")
        self.assertIsInstance(ts, TimeSeries)
        np.testing.assert_allclose(ts.data[ts.varfield].values, self.base + 2)
        with self.assertRaises(ValueError):
            self.tse.get_reducer_series(name="unknown")

    def test_view(self):
        self.tse.view_specs["reducers"] = ["mean", "p95"]
        self.tse.view_specs["bands"] = [[25, 75]]
        for layout, n_axes in [("series", 3), ("series-simple", 1)]:
            with self.subTest(layout=layout):
                self.tse.view_specs["layout"] = layout
                fig = self.tse.view(show=False, return_fig=True)
                self.assertEqual(len(fig.get_axes()), n_axes)
                legend = fig.get_axes()[0].get_legend()
                self.assertListEqual(
                    [t.get_text() for t in legend.get_texts()],
                    ["mean", "p95", "p25-p75"],
                )
                # legend above the panel, inside its width
                fig.canvas.draw()
                box_ax = fig.get_axes()[0].get_window_extent()
                box_legend = legend.get_window_extent()
                self.assertGreaterEqual(box_legend.y0, box_ax.y1)
                self.assertLessEqual(box_legend.x1, box_ax.x1)
                plt.close(fig)


class TestSeasonalEnsemble(unittest.TestCase):

    def setUp(self):
        # incomplete first and last years, each with its year as the value
        self.ts = make_series(start="2019-07-01", end="2021-03-31")
        self.se = self.ts.get_seasonal_ensemble()

    def get_rows(self, se):
        return se.merge_data()["datetime"]

    def test_get_seasonal_ensemble(self):
        ts = make_series(start="2019-07-01", end="2021-03-31", cls=TemperatureSeries)
        ts.varname = "Air"
        n_size = len(ts.data)
        se = ts.get_seasonal_ensemble(year_start=10)
        self.assertIsInstance(se, SeasonalEnsemble)
        self.assertEqual(se.name, ts.name)
        self.assertEqual(se.year_start, 10)
        self.assertEqual(se.varname, "Air")
        for member in se.collection.values():
            self.assertIsInstance(member, TemperatureSeries)
            self.assertEqual(member.units, ts.units)
        # the source series is untouched
        self.assertEqual(len(ts.data), n_size)
        self.assertEqual(ts.data[ts.dtfield].min(), pd.Timestamp("2019-07-01"))

    def test_members(self):
        self.assertListEqual(list(self.se.collection), ["2019", "2020", "2021"])
        ls_expected = [
            ("2019", "2000-07-01", "2000-12-31", 184),
            ("2020", "2000-01-01", "2000-12-31", 366),
            ("2021", "2000-01-01", "2000-03-31", 90),
        ]
        for name, start, end, n_size in ls_expected:
            with self.subTest(name=name):
                member = self.se.collection[name]
                dates = member.data[member.dtfield]
                self.assertEqual(dates.min(), pd.Timestamp(start))
                self.assertEqual(dates.max(), pd.Timestamp(end))
                self.assertEqual(len(dates), n_size)

    def test_reducers(self):
        df = self.se.mean().set_index("datetime")["Var_mean"]
        # only the leap year holds 29 Feb
        self.assertEqual(df["2000-02-29"], 2020)
        self.assertEqual(df["2000-02-28"], 2020.5)
        self.assertEqual(df["2000-07-01"], 2019.5)
        self.assertEqual(len(df), 366)

    def test_year_start(self):
        se = self.ts.get_seasonal_ensemble(year_start=10)
        self.assertListEqual(list(se.collection), ["2018-19", "2019-20", "2020-21"])
        member = se.collection["2019-20"]
        self.assertEqual(member.data[member.dtfield].min(), pd.Timestamp("1999-10-01"))
        self.assertEqual(member.data[member.dtfield].max(), pd.Timestamp("2000-09-30"))

        # any start gives one continuous year, holding 29 Feb
        for month in range(1, 13):
            with self.subTest(month=month):
                se = self.ts.get_seasonal_ensemble(year_start=month)
                rows = self.get_rows(se=se)
                self.assertEqual(rows.min().month, month)
                self.assertEqual(rows.max() - rows.min(), pd.Timedelta(days=365))
                self.assertEqual(((rows.dt.month == 2) & (rows.dt.day == 29)).sum(), 1)

    def test_steps(self):
        # monthly stamps are aligned, at any day of the month
        for freq in ["MS", "ME"]:
            with self.subTest(freq=freq):
                se = make_series(
                    start="2019-01-01", end="2021-12-31", freq=freq
                ).get_seasonal_ensemble()
                rows = self.get_rows(se=se)
                self.assertEqual(len(rows), 12)
                self.assertTrue(np.all(rows.dt.day == 1))
        # sub-daily steps keep their time
        se = make_series(
            start="2021-01-01", end="2022-12-31", freq="6h"
        ).get_seasonal_ensemble()
        self.assertEqual(len(self.get_rows(se=se)), 365 * 4)
        # a step that does not repeat each year
        ts = make_series(start="2019-01-01", end="2021-12-31", freq="7D")
        with self.assertRaisesRegex(ValueError, "does not repeat"):
            ts.get_seasonal_ensemble()

    def test_errors(self):
        for year_start in [0, 13]:
            with self.assertRaisesRegex(ValueError, "year_start"):
                self.ts.get_seasonal_ensemble(year_start=year_start)
        with self.assertRaisesRegex(ValueError, "No data"):
            TimeSeries(name="Empty").get_seasonal_ensemble()

    def test_set_series_replaces(self):
        self.se.set_series(ts=make_series(start="2005-01-01", end="2005-12-31"))
        self.assertListEqual(list(self.se.collection), ["2005"])
        self.assertEqual(len(self.se.catalog), 1)

    def test_view_xaxis(self):
        ls_cases = [
            ("days", "Day", ["1", "50", "100"]),
            ("month", "Month", ["1", "2", "3"]),
            ("month-letter", "Month", ["J", "F", "M"]),
            ("month-alias", "Month", ["Jan", "Feb", "Mar"]),
        ]
        for mode, xlabel, ls_ticks in ls_cases:
            with self.subTest(mode=mode):
                self.se.view_specs["xaxis"] = mode
                fig = self.se.view(show=False, return_fig=True)
                fig.canvas.draw()
                ax = fig.get_axes()[0]
                self.assertEqual(ax.get_xlabel(), xlabel)
                ls_labels = [t.get_text() for t in ax.get_xticklabels()]
                self.assertListEqual(ls_labels[:3], ls_ticks)
                plt.close(fig)
        self.se.view_specs["xaxis"] = "banana"
        with self.assertRaisesRegex(ValueError, "banana"):
            self.se.view(show=False, return_fig=True)
        plt.close("all")

    def test_view_highlight(self):
        self.se.view_specs["highlight"] = ["2020"]
        fig = self.se.view(show=False, return_fig=True)
        legend = fig.get_axes()[0].get_legend()
        self.assertListEqual(
            [t.get_text() for t in legend.get_texts()], ["2020", "mean", "p05-p95"]
        )
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
