# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
Unit tests for the ``Bivar`` class.

This module validates the behavior of ``Bivar``, ensuring proper initialization,
data setting and loading, model fitting and figure building.

Features
--------
The test suite verifies that:

* ``Bivar`` objects initialize correctly as a ``DataSet`` with no data.
* Paired data is cleaned (missing pairs dropped) and sorted by ``x``.
* CSV data is loaded with custom input column names.
* Metadata contains the ``Bivar`` fields.
* Fitting recovers known parameters and stores consistent fit metrics.
* Static metrics take ``observed`` and ``predicted`` and behave as expected.
* Figures are built for all layouts without writing files.

"""
# IMPORTS
# ***********************************************************************
# import modules from other libs

# Native imports
# =======================================================================
import unittest
import shutil, os, tempfile

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
from plans.root import DataSet
from plans.datasets.analyst import Bivar

# ... {develop}


# CONSTANTS
# ***********************************************************************
# define constants in uppercase

N_SIZE = 50
C0 = 2.0
C1 = 3.0

# ... {develop}

# FUNCTIONS
# ***********************************************************************


def get_sample():
    """
    Get a noiseless linear sample with shuffled x.
    """
    rng = np.random.default_rng(seed=42)
    x = rng.permutation(np.linspace(start=0, stop=10, num=N_SIZE))
    y = C0 + C1 * x
    return x, y


# CLASSES
# ***********************************************************************


class TestBivar(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """
        Runs once before all tests in this class: create temp folder and CSV file.
        """
        cls.temp_dir = tempfile.mkdtemp()
        cls.x, cls.y = get_sample()

        # data file with custom column names
        cls.data_csv = os.path.join(cls.temp_dir, "data.csv")
        df = pd.DataFrame({"h": cls.x, "q": cls.y})
        df.to_csv(cls.data_csv, sep=";", index=False)

    @classmethod
    def tearDownClass(cls):
        """
        Runs once after all tests in this class.
        """
        shutil.rmtree(cls.temp_dir)
        return None

    def setUp(self):
        self.bv = Bivar(name="TestBv", alias="Bv1")
        self.bv.set_data(x=self.x, y=self.y)

    def test_initialization(self):
        bv = Bivar(name="TestBv", alias="Bv1")
        self.assertIsInstance(bv, DataSet)
        self.assertEqual(bv.name, "TestBv")
        self.assertEqual(bv.alias, "Bv1")
        self.assertIsNone(bv.data)

    def test_set_data(self):
        x = np.array([3.0, 1.0, np.nan, 2.0])
        y = np.array([30.0, 10.0, 99.0, np.nan])
        bv = Bivar()
        bv.set_data(x=x, y=y)
        self.assertEqual(bv.size, 2)
        self.assertListEqual(list(bv.data[bv.xfield]), [1.0, 3.0])
        self.assertListEqual(bv.view_specs["range_x"], [1.0, 3.0])

    def test_load_data(self):
        bv = Bivar()
        bv.load_data(file_data=self.data_csv, input_xfield="h", input_yfield="q")
        self.assertListEqual(list(bv.data.columns), [bv.xfield, bv.yfield])
        self.assertEqual(bv.size, N_SIZE)
        self.assertTrue(bv.data[bv.xfield].is_monotonic_increasing)

    def test_get_metadata(self):
        metadata = self.bv.get_metadata()
        self.assertIn(self.bv.field_xunits, metadata)
        self.assertIn(self.bv.field_yunits, metadata)
        self.assertEqual(list(metadata.keys())[-1], self.bv.field_file_data)

    def test_fit(self):
        self.bv.fit(model_type="Linear")
        model = self.bv.models["Linear"]
        params = model["Setup"]["Mean"].values
        self.assertAlmostEqual(params[0], C0, places=4)
        self.assertAlmostEqual(params[1], C1, places=4)
        self.assertAlmostEqual(model["Metrics"]["RMSE"], 0.0, places=4)
        self.assertAlmostEqual(model["Metrics"]["R2"], 1.0, places=4)
        self.assertIn("e_Mean", model["Data"].columns)

    def test_correlation(self):
        # monotonic but non-linear: rho is perfect, r is not
        x = np.linspace(start=0, stop=10, num=N_SIZE)
        y = np.exp(x)
        self.assertAlmostEqual(Bivar.spearman(x=x, y=y), 1.0, places=6)
        self.assertLess(Bivar.pearson(x=x, y=y), 0.9)
        # symmetric
        self.assertAlmostEqual(Bivar.pearson(x=x, y=y), Bivar.pearson(x=y, y=x))

    def test_metrics(self):
        obs = np.array([1.0, 2.0, 3.0])
        pred = np.array([2.0, 2.0, 2.0])
        dc = Bivar.get_metrics(observed=obs, predicted=pred)
        self.assertAlmostEqual(dc["RMSE"], np.sqrt(2 / 3))
        self.assertAlmostEqual(dc["MAE"], 2 / 3)
        self.assertAlmostEqual(dc["Bias"], 0.0)
        self.assertAlmostEqual(dc["R2"], 0.0)  # constant at the mean
        # bias sign: overestimation is positive
        self.assertGreater(Bivar.bias(observed=obs, predicted=obs + 1), 0)

    def test_get_error_normality(self):
        # perturb to avoid zero-variance errors
        self.bv.update_model(params_mean=[C0, C1 * 1.01], model_type="Linear")
        df = self.bv.get_error_normality(model_type="Linear")
        self.assertIsInstance(df, pd.DataFrame)
        self.assertIn("is_normal", df.columns)

    def test_view(self):
        self.bv.update_model(params_mean=[C0, C1 * 1.01], model_type="Linear")
        self.bv.view_specs["layout"] = "banana"
        with self.assertRaisesRegex(ValueError, "banana"):
            self.bv.view(show=False, return_fig=True)
        for layout in ["full", "model"]:
            with self.subTest(layout=layout):
                self.bv.view_specs["layout"] = layout
                fig = self.bv.view(show=False, return_fig=True)
                self.assertEqual(len(fig.get_axes()), 3 if layout == "full" else 5)
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
