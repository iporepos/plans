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
