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
from plans.datasets import TimeSeries, TimeSeriesEnsemble

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
