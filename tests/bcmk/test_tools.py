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
import shutil

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
from plans.config import parse_fields, parse_files
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


def list_spatial_parameters(title):
    df_files = parse_files()
    file_name = df_files.loc[df_files["title"] == title, "name"].values[0]
    df_fields = parse_fields()
    df_fields = df_fields.query(f"{file_name} == 'w'").copy()
    return list(df_fields["name"].values)


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
        cls.project.verbose = True
        cls.soils_parameters = list_spatial_parameters(title="Soils Attributes")
        cls.lulc_parameters = list_spatial_parameters(title="Land Use Attributes")

    # Assertions methods
    # -------------------------------------------------------------------

    def assertions_basic(self, folder_run):
        folder_run = Path(folder_run)
        self.assertTrue(folder_run.exists())
        self.assertTrue((folder_run / "report.txt").exists())
        self.assertTrue((folder_run / "runtimes.csv").exists())

    # Cleanup methods
    # -------------------------------------------------------------------

    def cleanup_topo(self):
        cleanup_figs(self.project.folder_topo)
        Path(f"{self.project.folder_topo}/dto.tif").unlink(missing_ok=True)

    def cleanup_parameters(self, parent_folder):
        folder_parameters = Path(parent_folder) / "parameters"
        if os.path.isdir(folder_parameters):
            shutil.rmtree(folder_parameters)
        # make a again
        os.makedirs(folder_parameters, exist_ok=True)

    def cleanup_lulc_parameters(self):
        ls_lulc_scenarios = self.project.get_list_scenarios_lulc()
        for scenario in ls_lulc_scenarios:
            folder_scenario = Path(self.project.folder_lulc) / scenario
            self.cleanup_parameters(folder_scenario)

    def cleanup_lulc_scenarios(self):
        ls_scenarios = self.project.get_list_scenarios_lulc()
        for scenario in ls_scenarios:
            folder_scenario = f"{self.project.folder_lulc}/{scenario}"
            cleanup_figs(folder_scenario)
            Path(f"{folder_scenario}/lulc_series.csv").unlink(missing_ok=True)

    def cleanup_climate_scenarios(self):
        ls_scenarios = self.project.get_list_scenarios_climate()
        for scenario in ls_scenarios:
            folder_scenario = f"{self.project.folder_climate}/{scenario}"
            ls_lulc_scenarios = self.project.get_list_scenarios_lulc()
            # cleanup_figs(folder_scenario)
            for scenario_lulc in ls_lulc_scenarios:
                Path(
                    f"{folder_scenario}/climate_series_lulc_{scenario_lulc}.csv"
                ).unlink(missing_ok=True)

    # Test analysis_*() methods
    # -------------------------------------------------------------------
    def test_analysis(self):
        self.test_analysis_dto()
        self.test_analysis_dto_basins()
        self.test_analysis_lulc_series()
        self.test_analysis_climate_series_lulc()
        self.test_analysis_soils_parameters()
        self.test_analysis_lulc_parameters()

    def test_demo(self):
        """
        Run with:

        .. code-block:: python

            python -m unittest -v tests.bcmk.test_tools.TestTools.test_demo

        """
        # Call process
        # ---------------------------------------------------------------
        subp, folder_run = self.project.run_demo()
        # Wait for subprocess to finish
        subp.wait()

        # Assertions
        # ---------------------------------------------------------------
        folder_run = Path(folder_run)
        self.assertions_basic(folder_run=folder_run)
        self.assertTrue((folder_run / "demo_output.csv").exists())

    def test_analysis_dto(self, include_views=True, use_basin=None):
        """
        Run with:

        .. code-block:: python

            python -m unittest -v tests.bcmk.test_tools.TestTools.test_analysis_dto

        """
        print("\n")
        # Call process
        # ---------------------------------------------------------------
        subp, folder_run = self.project.run_analysis_dto(include_views, use_basin)
        # Wait for subprocess to finish
        subp.wait()

        # Assertions
        # ---------------------------------------------------------------
        folder_run = Path(folder_run)
        self.assertions_basic(folder_run=folder_run)
        self.assertTrue((folder_run / "dto.tif").exists())
        if include_views:
            self.assertTrue((folder_run / "dto.jpg").exists())

    def test_analysis_dto_basins(self):
        """
        Run with:

        .. code-block:: python

            python -m unittest -v tests.bcmk.test_tools.TestTools.test_analysis_dto_basins

        """
        # Call processes
        # ---------------------------------------------------------------
        self.test_analysis_dto(use_basin="main")
        self.test_analysis_dto(use_basin="sub01")
        self.test_analysis_dto(use_basin="sub02")
        self.test_analysis_dto(use_basin="sub03")

    def test_analysis_lulc_series(self, include_views=True, use_basin=None):
        """
        Run with:

        .. code-block:: python

            python -m unittest -v tests.bcmk.test_tools.TestTools.test_analysis_lulc_series


        """
        print("\n")
        # Call process
        # ---------------------------------------------------------------
        subp, folder_run = self.project.run_analysis_lulc_series(
            "mb01", include_views, use_basin
        )
        # Wait for subprocess to finish
        subp.wait()

        # Assertions
        # ---------------------------------------------------------------
        folder_run = Path(folder_run)
        self.assertions_basic(folder_run=folder_run)
        self.assertTrue((folder_run / "lulc_series.csv").exists())

    def test_analysis_lulc_series_basins(self):
        """
        Run with:

        .. code-block:: python

            python -m unittest -v tests.bcmk.test_tools.TestTools.test_analysis_dto

        """
        self.test_analysis_lulc_series(use_basin="main")
        self.test_analysis_lulc_series(use_basin="sub01")
        self.test_analysis_lulc_series(use_basin="sub02")
        self.test_analysis_lulc_series(use_basin="sub03")

    def test_analysis_climate_series_lulc(self, include_views=True):
        """
        Run with:

        .. code-block:: python

            python -m unittest -v tests.bcmk.test_tools.TestTools.test_analysis_climate_series_lulc

        """
        print("\n")
        lulc_scenario = "mb01"
        # Call process
        # ---------------------------------------------------------------
        subp, folder_run = self.project.run_analysis_climate_series_lulc(
            climate_scenario="observed",
            lulc_scenario=lulc_scenario,
            include_views=include_views,
        )
        # Wait for subprocess to finish
        subp.wait()

        # Assertions
        # ---------------------------------------------------------------
        folder_run = Path(folder_run)
        self.assertions_basic(folder_run=folder_run)
        self.assertTrue(
            (folder_run / f"climate_series_lulc_{lulc_scenario}.csv").exists()
        )

    def test_analysis_soils_parameters(self, include_views=True):
        """
        Run with:

        .. code-block:: python

            python -m unittest -v tests.bcmk.test_tools.TestTools.test_analysis_soils_parameters

        """
        print("\n")
        # Call process
        # ---------------------------------------------------------------
        subp, folder_run = self.project.run_analysis_soils_parameters(
            include_views=include_views,
        )
        # Wait for subprocess to finish
        subp.wait()

        # Assertions
        # ---------------------------------------------------------------
        self.assertions_basic(folder_run)
        # todo assertions!

    def test_analysis_lulc_parameters(self, include_views=True):
        """
        Run with:

        .. code-block:: python

            python -m unittest -v tests.bcmk.test_tools.TestTools.test_analysis_lulc_parameters

        """
        print("\n")
        # Call process
        # ---------------------------------------------------------------
        lulc_scenario = "mb01"
        subp, folder_run = self.project.run_analysis_lulc_parameters(
            lulc_scenario=lulc_scenario,
            include_views=include_views,
        )
        # Wait for subprocess to finish
        subp.wait()

        # Assertions
        # ---------------------------------------------------------------
        self.assertions_basic(folder_run)

        folder_lulc = self.project.folder_lulc
        s = lulc_scenario
        ls_lulcs = glob.glob(f"{folder_lulc}/{s}/lulc_*.tif")
        ls_names = [os.path.basename(f).replace(".tif", "") for f in ls_lulcs]
        for n in ls_names:
            for p in self.lulc_parameters:
                file_name = f"{n}_{p}.tif"
                f = Path(folder_run) / file_name
                self.assertTrue(f.exists())
                file_name = f"{n}_{p}.jpg"
                f = Path(folder_run) / file_name
                self.assertTrue(f.exists())
                file_name = f"{n}_{p}_main.jpg"
                f = Path(folder_run) / file_name
                self.assertTrue(f.exists())

    # Test get_*() methods
    # -------------------------------------------------------------------

    def _template_get(self):
        # Clean ups
        # ---------------------------------------------------------------

        # Call project method
        # ---------------------------------------------------------------

        # Assertions
        # ---------------------------------------------------------------
        pass
        return True

    def test_gets(self):
        self.test_get_dto()
        self.test_get_lulc_series()
        self.test_analysis_climate_series_lulc()
        self.test_get_soils_parameters()
        self.test_get_lulc_parameters()

    def test_get_dto(self):

        # Clean ups
        # ---------------------------------------------------------------
        self.cleanup_topo()

        # Call project method
        # ---------------------------------------------------------------
        self.project.generate_dto()

        # Assertions
        # ---------------------------------------------------------------
        file_tif = Path(self.project.folder_topo) / "dto.tif"
        file_fig = Path(self.project.folder_topo) / "dto.jpg"
        self.assertTrue((file_tif).exists())
        self.assertTrue((file_fig).exists())

    def test_get_lulc_series(self):
        # Clean ups
        # ---------------------------------------------------------------
        self.cleanup_lulc_scenarios()

        # Call project method
        # ---------------------------------------------------------------
        skip_scenario = "mapbiomas"
        self.project.generate_lulc_series(skip_lulc_scenario=skip_scenario)

        # Assertions
        # ---------------------------------------------------------------
        ls_scenarios = self.project.get_list_scenarios_lulc()
        for scenario in ls_scenarios:
            if scenario == skip_scenario:
                pass
            else:
                folder_scenario = Path(self.project.folder_lulc) / scenario
                file_csv = Path(folder_scenario) / "lulc_series.csv"
                self.assertTrue((file_csv).exists())
                # check figs
                ls_rasters = glob.glob(f"{folder_scenario}/lulc_*.tif")
                for f in ls_rasters:
                    basename = os.path.basename(f).replace(".tif", ".jpg")
                    file_fig = folder_scenario / f"{basename}"
                    self.assertTrue((file_fig).exists())

    def test_get_climate_series_lulc(self):
        # Clean ups
        # ---------------------------------------------------------------
        self.cleanup_climate_scenarios()
        # call method
        skip_scenario = None
        self.project.generate_climate_series_lulc()

        # Assertions
        # ---------------------------------------------------------------
        ls_scenarios = self.project.get_list_scenarios_climate()
        for scenario in ls_scenarios:
            if scenario == skip_scenario:
                pass
            else:
                # testprint(scenario)
                folder_scenario = Path(self.project.folder_climate) / scenario
                ls_lulc_scenarios = self.project.get_list_scenarios_lulc()
                for scenario_lulc in ls_lulc_scenarios:
                    file_csv = (
                        Path(folder_scenario)
                        / f"climate_series_lulc_{scenario_lulc}.csv"
                    )
                    self.assertTrue((file_csv).exists())

    def test_get_soils_parameters(self):
        # Clean ups
        # ---------------------------------------------------------------
        self.cleanup_parameters(self.project.folder_soils)

        # Call project method
        # ---------------------------------------------------------------
        self.project.generate_soils_parameters()

        # Assertions
        # ---------------------------------------------------------------
        for p in self.soils_parameters:
            file_name = f"parameters/soils_{p}.tif"
            f = Path(self.project.folder_soils) / file_name
            self.assertTrue(f.exists())

        return None

    def test_get_lulc_parameters(self):
        # Clean ups
        # ---------------------------------------------------------------
        self.cleanup_lulc_parameters()

        # Call project method
        # ---------------------------------------------------------------
        selected_lulc_scenario = "mb01"
        self.project.generate_lulc_parameters(lulc_scenario=selected_lulc_scenario)

        # Assertions
        # ---------------------------------------------------------------
        folder_lulc = self.project.folder_lulc
        if selected_lulc_scenario is None:
            ls_scenarios = self.project.get_list_scenarios_lulc()
        else:
            ls_scenarios = [selected_lulc_scenario]
        for s in ls_scenarios:
            ls_lulcs = glob.glob(f"{folder_lulc}/{s}/lulc_*.tif")
            ls_names = [os.path.basename(f).replace(".tif", "") for f in ls_lulcs]
            for n in ls_names:
                for p in self.lulc_parameters:
                    file_name = f"{s}/parameters/{n}_{p}.tif"
                    f = Path(folder_lulc) / file_name
                    self.assertTrue(f.exists())
                    file_name = f"{s}/parameters/{n}_{p}.jpg"
                    f = Path(folder_lulc) / file_name
                    self.assertTrue(f.exists())
                    file_name = f"{s}/parameters/{n}_{p}_main.jpg"
                    f = Path(folder_lulc) / file_name
                    self.assertTrue(f.exists())
        return None


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
