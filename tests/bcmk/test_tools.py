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
import glob
import os.path

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
def cleanup_figs(folder, fig_format="jpg"):
    ls_figs = glob.glob(f"{folder}/*.{fig_format}")
    for f in ls_figs:
        Path(f).unlink()
    return None


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

    def cleanup_topo(self):
        cleanup_figs(self.project.folder_topo)
        Path(f"{self.project.folder_topo}/dto.tif").unlink(missing_ok=True)

    def cleanup_lulc_scenarios(self):
        ls_scenarios = self.project.list_scenarios_lulc()
        for scenario in ls_scenarios:
            folder_scenario = f"{self.project.folder_lulc}/{scenario}"
            cleanup_figs(folder_scenario)
            Path(f"{folder_scenario}/lulc_series.csv").unlink(missing_ok=True)

    def cleanup_climate_scenarios(self):
        ls_scenarios = self.project.list_scenarios_climate()
        for scenario in ls_scenarios:
            folder_scenario = f"{self.project.folder_climate}/{scenario}"
            ls_lulc_scenarios = self.project.list_scenarios_lulc()
            # cleanup_figs(folder_scenario)
            for scenario_lulc in ls_lulc_scenarios:
                Path(
                    f"{folder_scenario}/climate_series_lulc_{scenario_lulc}.csv"
                ).unlink(missing_ok=True)

    def test_demo(self):
        # Run tool
        subp, folder_run = self.project.run_demo()
        # Wait for subprocess to finish
        subp.wait()

        # Assertions
        folder_run = Path(folder_run)
        self.assertTrue(folder_run.exists())
        self.assertTrue((folder_run / "runtimes.csv").exists())
        self.assertTrue((folder_run / "demo_output.csv").exists())

    def test_get_dto(self):
        # clean up
        self.cleanup_topo()
        # call method
        self.project.get_dto()
        # assertions
        file_tif = Path(self.project.folder_topo) / "dto.tif"
        file_fig = Path(self.project.folder_topo) / "dto.jpg"
        self.assertTrue((file_tif).exists())
        self.assertTrue((file_fig).exists())

    def test_get_lulc_series(self):
        # clean up
        self.cleanup_lulc_scenarios()
        # call method
        skip_scenario = None
        self.project.get_lulc_series(skip_lulc_scenario=skip_scenario)
        # assertions
        ls_scenarios = self.project.list_scenarios_lulc()
        for scenario in ls_scenarios:
            if scenario == skip_scenario:
                pass
            else:
                # testprint(scenario)
                folder_scenario = Path(self.project.folder_lulc) / scenario
                file_csv = Path(folder_scenario) / "lulc_series.csv"
                self.assertTrue((file_csv).exists())
                # check figs
                ls_rasters = glob.glob(f"{folder_scenario}/lulc_*.tif")
                for f in ls_rasters:
                    basename = os.path.basename(f).replace(".tif", ".jpg")
                    file_fig = folder_scenario / f"{basename}"
                    # testprint(file_fig)
                    self.assertTrue((file_fig).exists())

    def test_get_climate_series_lulc(self):
        # clean up
        self.cleanup_climate_scenarios()
        # call method
        skip_scenario = None
        self.project.get_climate_lulc_series()
        # assertions
        ls_scenarios = self.project.list_scenarios_climate()
        for scenario in ls_scenarios:
            if scenario == skip_scenario:
                pass
            else:
                # testprint(scenario)
                folder_scenario = Path(self.project.folder_climate) / scenario
                ls_lulc_scenarios = self.project.list_scenarios_lulc()
                for scenario_lulc in ls_lulc_scenarios:
                    file_csv = (
                        Path(folder_scenario)
                        / f"climate_{scenario_lulc}_lulc_series.csv"
                    )
                    self.assertTrue((file_csv).exists())

    def test_analysis_dto(self, include_views=True, use_basin=None):
        # Run tool
        subp, folder_run = self.project.run_analysis_dto(include_views, use_basin)
        # Wait for subprocess to finish
        subp.wait()

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
            "mb01", include_views, use_basin
        )
        # Wait for subprocess to finish
        subp.wait()

        # Assertions
        folder_run = Path(folder_run)
        self.assertTrue(folder_run.exists())
        self.assertTrue((folder_run / "runtimes.csv").exists())
        self.assertTrue((folder_run / "lulc_series.csv").exists())

    def test_analysis_lulc_series_basins(self):
        self.test_analysis_lulc_series(use_basin="main")
        self.test_analysis_lulc_series(use_basin="sub01")
        self.test_analysis_lulc_series(use_basin="sub02")
        self.test_analysis_lulc_series(use_basin="sub03")

    def test_analysis_climate_series_lulc(self, include_views=True):
        # Run tool
        subp, folder_run = self.project.run_analysis_climate_series_lulc(
            climate_scenario="observed",
            lulc_scenario="mb01",
            include_views=include_views,
        )
        # Wait for subprocess to finish
        subp.wait()

        # Assertions
        folder_run = Path(folder_run)
        self.assertTrue(folder_run.exists())
        self.assertTrue((folder_run / "runtimes.csv").exists())
        # self.assertTrue((folder_run / "lulc_series.csv").exists())
        #


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
