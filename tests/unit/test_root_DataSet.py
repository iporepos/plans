# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
Unit tests for the ``DataSet`` class.

This module validates the behavior of ``DataSet``, ensuring proper initialization,
CSV data loading, metadata retrieval, and booting from a template CSV file.

Features
--------
The test suite verifies that:

* ``DataSet`` objects initialize correctly with given name and alias.
* CSV data is loaded into the ``data`` attribute as a pandas DataFrame with expected columns.
* Metadata is returned as a dictionary and contains all expected fields.
* Booting from a CSV template correctly updates object attributes, including ``file_data``.
* Temporary directories and files are used to avoid polluting the project folder.

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
import pandas as pd

# ... {develop}

# Project-level imports
# =======================================================================
from tests.conftest import DATA_DIR
from plans.root import DataSet

# ... {develop}


# CONSTANTS
# ***********************************************************************
# define constants in uppercase

FILE_1 = DATA_DIR / "DataSet_data.csv"
FILE_2 = DATA_DIR / "DataSet_boot.csv"

# ... {develop}

# FUNCTIONS
# ***********************************************************************


# CLASSES
# ***********************************************************************


class TestDataSet(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """
        Runs once before all tests in this class: create temp folder and CSV files.
        """
        cls.temp_dir = tempfile.mkdtemp()

        # data file
        cls.data_csv = os.path.join(cls.temp_dir, "data.csv")
        # save data
        df = pd.read_csv(FILE_1, sep=";")
        df.to_csv(cls.data_csv, sep=";", index=False)

        # boot file
        cls.bootfile_csv = os.path.join(cls.temp_dir, "boot.csv")
        df = pd.read_csv(FILE_2, sep=";")
        df.loc[df["field"] == "file_data", "value"] = str(cls.data_csv)
        df.loc[df["field"] == "folder_base", "value"] = str(cls.temp_dir)
        # save boot file
        df.to_csv(cls.bootfile_csv, sep=";", index=False)

    @classmethod
    def tearDownClass(cls):
        """
        Runs once after all tests in this class.
        """
        shutil.rmtree(cls.temp_dir)
        return None

    def test_initialization(self):
        ds = DataSet(name="TestDS", alias="DS1")
        # base and temp dir must be the same
        self.assertEqual(ds.name, "TestDS")
        self.assertEqual(ds.alias, "DS1")

    def test_load_data(self):
        ds = DataSet(name="TestDS")
        ds.file_data = self.data_csv
        ds.load_data(ds.file_data)
        self.assertIsInstance(ds.data, pd.DataFrame)
        self.assertIn("p", ds.data.columns)
        self.assertIn("rm", ds.data.columns)
        self.assertIn("tas", ds.data.columns)

    def test_get_metadata_returns_dict(self):
        ds = DataSet(name="TestDS")
        metadata = ds.get_metadata()
        self.assertIsInstance(metadata, dict)
        self.assertIn(ds.field_name, metadata)
        self.assertIn(ds.field_alias, metadata)
        self.assertIn(ds.field_source, metadata)
        self.assertIn(ds.field_color, metadata)
        self.assertIn(ds.field_description, metadata)
        self.assertIn(ds.field_size, metadata)

    def test_boot_process(self):
        """
        Test booting from a CSV template: should configure file_data and folder_base correctly.
        """
        ds = DataSet()
        ds.boot(self.bootfile_csv)
        # After booting, check if attributes match the boot file contents
        self.assertEqual(ds.file_data, self.data_csv)


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
