# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
Unit tests for the ``FileSys`` class.

This module validates the behavior of ``FileSys`` by creating a temporary file
system, loading sample data, and verifying folder creation, metadata generation,
and backup functionality.

Features
--------
This test suite ensures that:

* Initialization of ``FileSys`` correctly sets up base and root directories.
* CSV data is properly loaded into the ``FileSys`` object.
* Root and subfolders are created as expected.
* Metadata excludes unused fields and contains correct base path.
* Backup creates a ZIP archive of the file system.

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
from plans.root import FileSys

# ... {develop}


# CONSTANTS
# ***********************************************************************
# define constants in uppercase

FILE_1 = DATA_DIR / "FileSys_data.csv"
FILE_2 = DATA_DIR / "FileSys_boot.csv"

# ... {develop}

# FUNCTIONS
# ***********************************************************************


# CLASSES
# ***********************************************************************


class TestFileSys(unittest.TestCase):

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
        fs = FileSys(name="TestFS")
        fs.folder_base = self.temp_dir
        fs.update()
        # base and temp dir must be the same
        self.assertEqual(fs.folder_base, self.temp_dir)
        # root must match the name of the test
        self.assertEqual(fs.folder_root, os.path.join(self.temp_dir, "TestFS"))

    def test_load_data_and_setup_folders(self):
        fs = FileSys(name="TestFS")
        fs.folder_base = self.temp_dir
        fs.update()
        fs.file_data = self.data_csv
        fs.load_data(fs.file_data)
        fs.setup_root_folder()
        fs.setup_subfolders()

        # created folder
        self.assertTrue(os.path.isdir(fs.folder_root))

        # created all folders
        for folder in fs.data["folder"]:
            self.assertTrue(os.path.isdir(os.path.join(fs.folder_root, folder)))

    def test_get_metadata(self):
        fs = FileSys(name="MetaTest")
        fs.folder_base = self.temp_dir
        fs.update()
        meta = fs.get_metadata()
        # check if colors where removed
        self.assertNotIn(fs.field_color, meta)
        # check if base folder is the temp dir
        self.assertEqual(meta[fs.field_folder_base], self.temp_dir)

    def test_backup(self):
        fs = FileSys(name="ZipTest")
        fs.folder_base = self.temp_dir
        fs.update()
        fs.file_data = self.data_csv
        fs.load_data(fs.file_data)
        fs.setup()

        backup_folder = tempfile.mkdtemp()
        fs.backup(dst_folder=backup_folder)

        files = os.listdir(backup_folder)
        # check if there is a zip folder
        self.assertTrue(any(f.endswith(".zip") for f in files))
        # delete zip
        shutil.rmtree(backup_folder)

    def test_boot_process(self):
        """
        Test booting from a CSV template: should configure file_data and folder_base correctly.
        """
        fs = FileSys()
        fs.boot(self.bootfile_csv)

        # After booting, check if attributes match the boot file contents
        self.assertEqual(fs.file_data, self.data_csv)
        self.assertEqual(fs.folder_base, self.temp_dir)

        # Ensure that we can set up the file system after boot
        fs.load_data(fs.file_data)
        fs.setup_root_folder()
        self.assertTrue(os.path.isdir(fs.folder_root))


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
