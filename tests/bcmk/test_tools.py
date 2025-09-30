# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
{Short module description (1-3 sentences)}
todo docstring

Features
--------
todo docstring

 - {feature 1}
 - {feature 2}
 - {feature 3}
 - {etc}

Overview
--------
todo docstring
{Overview description}

Examples
--------
todo docstring
{Examples in rST}

Print a message

.. code-block:: python

    # print message
    print("Hello world!")
    # [Output] >> 'Hello world!'


"""


# IMPORTS
# ***********************************************************************
# import modules from other libs

# Native imports
# =======================================================================
import unittest
from pathlib import Path

# ... {develop}

# External imports
# =======================================================================
# ... {develop}

# Project-level imports
# =======================================================================
import plans
from tests import conftest
from tests.conftest import RUN_BENCHMARKS, RUN_BENCHMARKS_XXL, testprint, DATA_DIR

# ... {develop}


# CONSTANTS
# ***********************************************************************
# ... {develop}


# FUNCTIONS
# ***********************************************************************
# ... {develop}


# CLASSES
# ***********************************************************************


@unittest.skipUnless(RUN_BENCHMARKS, reason="skipping benchmarks")
class TestTools(unittest.TestCase):

    # Setup methods
    # -------------------------------------------------------------------
    @classmethod
    def setUpClass(cls):
        """
        Prepare project
        """
        cls.project = plans.load_project(str(DATA_DIR / "biboca"))
        cls.project.talk = True

    def test_demo(self):
        # Run tool
        subp, folder_run = self.project.run_demo()
        # Wait for subprocess to finish
        subp.wait()

        testprint(s=f"folder: {folder_run}")

        # Assertions
        folder_run = Path(folder_run)
        self.assertTrue(folder_run.exists())
        self.assertTrue((folder_run / "runtimes.csv").exists())
        self.assertTrue((folder_run / "demo_output.csv").exists())

    def test_analysis_dto(self, include_views=True, use_basin=None):
        # Run tool
        subp, folder_run = self.project.run_analysis_dto(include_views, use_basin)
        # Wait for subprocess to finish
        subp.wait()

        testprint(s=f"folder: {folder_run}")

        # Assertions
        folder_run = Path(folder_run)
        self.assertTrue(folder_run.exists())
        self.assertTrue((folder_run / "runtimes.csv").exists())
        self.assertTrue((folder_run / "dto.tif").exists())
        if include_views:
            self.assertTrue((folder_run / "dto.jpg").exists())

    def test_analysis_dto_basins(self):
        self.test_analysis_dto(use_basin="main")
        self.test_analysis_dto(use_basin="sub01")
        self.test_analysis_dto(use_basin="sub02")
        self.test_analysis_dto(use_basin="sub03")

    def test_analysis_lulc_series(self, include_views=True, use_basin=None):
        # Run tool
        subp, folder_run = self.project.run_analysis_lulc_series(
            "mapbiomas_short", include_views, use_basin
        )
        # Wait for subprocess to finish
        subp.wait()

        testprint(s=f"folder: {folder_run}")

        # Assertions
        folder_run = Path(folder_run)
        self.assertTrue(folder_run.exists())
        self.assertTrue((folder_run / "runtimes.csv").exists())
        # todo more assertions


# ... {develop}


# SCRIPT
# ***********************************************************************
# standalone behaviour as a script
if __name__ == "__main__":
    from tests.conftest import RUN_BENCHMARKS

    # RESET BENCHMARKS
    RUN_BENCHMARKS = True

    # Script section
    # ===================================================================
    unittest.main()
    # ... {develop}
