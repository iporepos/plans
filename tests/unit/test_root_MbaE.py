# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
Unit tests for the ``MbaE`` class.

This module validates the behavior of ``MbaE``, the most basic object in the
system. It ensures correct initialization, automatic alias creation, metadata
retrieval, attribute setting, CSV-based booting, export functionality, and
string representation.

Features
--------
The test suite verifies that:

* ``MbaE`` objects initialize with correct default name and alias.
* Aliases are auto-generated when not provided.
* Metadata is correctly returned as a dictionary or a pandas DataFrame.
* Attributes can be updated via the setter method.
* Booting from a CSV file properly updates object attributes.
* Exporting metadata creates a valid CSV file.
* The string representation contains the expected information.

"""
# IMPORTS
# ***********************************************************************
# import modules from other libs

# Native imports
# =======================================================================
import unittest
import shutil, os, tempfile
from pathlib import Path

# ... {develop}

# External imports
# =======================================================================
import pandas as pd

# ... {develop}

# Project-level imports
# =======================================================================
from tests.conftest import DATA_DIR
from plans.root import MbaE

# ... {develop}


# CONSTANTS
# ***********************************************************************
# define constants in uppercase

DATA_FILE_1 = DATA_DIR / "MbaE_boot.csv"

# ... {develop}

# FUNCTIONS
# ***********************************************************************


# CLASSES
# ***********************************************************************


class TestMbaE(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """
        Runs once before all tests in this class.
        """
        cls.temp_dir = tempfile.mkdtemp()
        cls.bootfile_csv = os.path.join(cls.temp_dir, "boot.csv")
        # save data
        df = pd.read_csv(DATA_FILE_1, sep=";")
        df.to_csv(cls.bootfile_csv, sep=";", index=False)
        return None

    @classmethod
    def tearDownClass(cls):
        """
        Runs once after all tests in this class.
        """
        shutil.rmtree(cls.temp_dir)
        return None

    def setUp(self):
        """
        Create a fresh MbaE object before each test.
        """
        self.mba = MbaE(name="Algo", alias="al")

    def test_initialization_defaults(self):
        # Check name and alias are correctly stored
        self.assertEqual(self.mba.name, "Algo")
        self.assertEqual(self.mba.alias, "al")
        # Check object-level attributes
        self.assertEqual(self.mba.object_name, "MbaE")
        self.assertEqual(self.mba.object_alias, "mbae")

    def test_alias_autocreation(self):
        # Alias should be created automatically when None is passed
        mba2 = MbaE(name="Test", alias=None)
        self.assertEqual(mba2.alias, "Tt")  # first and last letter of name

    def test_get_metadata_returns_dict(self):
        metadata = self.mba.get_metadata()
        self.assertIsInstance(metadata, dict)
        self.assertIn(self.mba.field_name, metadata)
        self.assertIn(self.mba.field_alias, metadata)

    def test_get_metadata_df_returns_dataframe(self):
        df = self.mba.get_metadata_df()
        self.assertIsInstance(df, pd.DataFrame)
        self.assertIn(self.mba.field_bootfile_attribute, df.columns)
        self.assertIn(self.mba.field_bootfile_value, df.columns)

    def test_setter_updates_values(self):
        new_values = {"name": "NewName", "alias": "NN"}
        self.mba.setter(new_values)
        self.assertEqual(self.mba.name, "NewName")
        self.assertEqual(self.mba.alias, "NN")

    def test_export_creates_csv(self):
        # Export should write a CSV file with metadata
        with tempfile.TemporaryDirectory() as tmpdir:
            out_file = Path(tmpdir) / "test_mbae.csv"
            self.mba.export(folder=tmpdir, filename="test_mbae")
            self.assertTrue(out_file.exists())

            # Load the CSV back to check contents
            df = pd.read_csv(out_file, sep=";")
            self.assertIn(self.mba.field_bootfile_attribute, df.columns)
            self.assertIn(self.mba.field_bootfile_value, df.columns)

    def test_boot_reads_csv_and_sets_attributes(self):
        # Create a temporary bootfile
        with tempfile.TemporaryDirectory() as tmpdir:
            self.mba.boot(bootfile=str(self.bootfile_csv))
            self.assertEqual(self.mba.name, "MyMbaE")
            self.assertEqual(self.mba.alias, "MM")
            self.assertEqual(self.mba.folder_bootfile, self.temp_dir)

    def test_str_representation(self):
        # __str__ should return a non-empty string with object name and alias
        str_out = str(self.mba)
        self.assertIn(self.mba.name, str_out)
        self.assertIn(self.mba.alias, str_out)


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
