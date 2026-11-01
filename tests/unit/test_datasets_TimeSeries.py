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
import numpy as np
import pandas as pd

# ... {develop}

# Project-level imports
# =======================================================================
from plans.datasets import TimeSeries

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
