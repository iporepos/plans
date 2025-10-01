# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.

"""
Project-related classes and routines

Overview
--------

# todo [major docstring improvement] -- overview
Mauris gravida ex quam, in porttitor lacus lobortis vitae.
In a lacinia nisl. Pellentesque habitant morbi tristique senectus
et netus et malesuada fames ac turpis egestas.


"""
# IMPORTS
# ***********************************************************************
# import modules from other libs

# Native imports
# =======================================================================
import os, sys
import glob
import datetime
import shutil
import subprocess
import time
from pathlib import Path

# ... {develop}

# External imports
# =======================================================================
import pandas as pd

# ... {develop}

# Project-level imports
# =======================================================================
from plans.config import DATA_DIR
from plans.root import FileSys
from plans.root import RecordTable


# ... {develop}


# CONSTANTS
# ***********************************************************************
# define constants in uppercase


# FUNCTIONS
# ***********************************************************************

# Project-level functions
# =======================================================================


def new_project(specs):
    """
    Create a new Project from a specification dictionary.

    .. danger::

        This method overwrites all existing default files.

    :param specs: Dictionary containing project specifications.

        **Required keys**:

        - ``folder_base`` (*str*): Path where the project folder will be created.
        - ``name`` (*str*): Name of the project.

        **Optional keys**:

        - ``alias`` (*str*): Alternative identifier. Defaults to ``None``.
        - ``source`` (*str*): Source reference. Defaults to empty string.
        - ``description`` (*str*): Project description. Defaults to empty string.

    :type specs: dict
    :raises ValueError: If any required key is missing.
    :returns: A new `:class:`plans.Project` instance initialized with the given specifications.
    :rtype: :class:`plans.Project`


    **Examples**

    Import ``plans``

    .. code-block:: python

       import plans

    Create a new ``plans.Project``. First setup details.

    .. code-block:: python

        # [CHANGE THIS] setup specs dictionary
        project_specs = {
            "folder_base": "C:/plans", # change this path
            "name": "newProject",
            "alias": "NPrj",
            "source": "Me",
            "description": "Just a test"
        }

    Then call ``new_project()``

    .. code-block:: python

        plans.new_project(specs=project_specs)

    Create and get the project instance:

    .. code-block:: python

        prj = plans.new_project(specs=project_specs)


    """
    # --- Required keys ---
    required = ["folder_base", "name"]
    for key in required:
        if key not in specs:
            raise ValueError(f"Missing required key: '{key}'")

    # --- Optional keys with defaults ---
    defaults = {"alias": None, "source": "", "description": ""}
    merged = {**defaults, **specs}

    # --- Use merged dict safely ---
    # create base folder if not exists
    os.makedirs(merged["folder_base"], exist_ok=True)

    folder_root = Path(merged["folder_base"]) / merged["name"]
    if os.path.isdir(folder_root):
        raise ValueError(f"Project folder already exists '{folder_root}'")

    # instantiate project
    p = Project(name=merged["name"], alias=merged["alias"])
    p.source = merged["source"]
    p.description = merged["description"]
    p.folder_base = merged["folder_base"]
    p.update()
    p.setup()

    return p


def load_project(project_folder):
    """
    Loads a Project from folder

    :param project_folder: path to project root folder
    :type project_folder: str or Path
    :returns: A new `:class:`plans.Project` instance.
    :rtype: :class:`plans.Project`

    **Notes**

    .. warning::

       ``load_project()`` will overwrite the ``name`` attribute in ``project_info.csv``
       file to match current folder name.


    **Examples**

    Import ``plans``

    .. code-block:: python

        import plans


    Load an existing ``plans.Project``

    .. code-block:: python

        # get project instance
        pj = plans.load_project(project_folder="path/to/project/folder")


    """
    if os.path.isdir(project_folder):
        name = os.path.basename(project_folder)
        folder_base = os.path.abspath(Path(project_folder).parent)
        p = Project(name=name, alias=None)
        p.load_data()
        # load from boot file
        boot_file_name = "project_info"
        boot_file = Path(project_folder) / "data/{}.csv".format(boot_file_name)
        if os.path.isfile(boot_file):
            p.boot(bootfile=boot_file)
            # update attributes
            p.name = name
            p.folder_base = folder_base
            # update project
            p.update()
            # update metadata file
            p.export_metadata(folder=f"{project_folder}/data", filename=boot_file_name)
            # setup
            p.setup()
        else:
            new_project(
                specs={
                    "name": name,
                    "folder_base": folder_base,
                }
            )
        return p
    else:
        raise ValueError(f"Project folder not found: {project_folder}'")


# Module-level functions
# =======================================================================


def handle_input_file(file_path, msg=""):
    if not os.path.isfile(file_path):
        raise FileNotFoundError(msg)
    else:
        pass


# CLASSES
# ***********************************************************************

# CLASSES -- Project-level
# =======================================================================


class Project(FileSys):

    def __init__(self, name, alias=None):
        super().__init__(name=name, alias=alias)
        self.load_data()
        self.talk = True

    def get_metadata(self):
        # ------------ call super ----------- #
        dict_meta = super().get_metadata()

        # removals

        dict_meta.pop(self.field_size)
        dict_meta.pop(self.field_file_data)

        return dict_meta

    def setter(self, dict_setter, load_data=False):
        # ignores
        dict_setter[self.field_size] = None
        dict_setter[self.field_file_data] = None

        # -------------- super -------------- #
        super().setter(dict_setter=dict_setter, load_data=False)

        # ---------- set basic attributes --------- #
        # set base folder
        self.folder_base = dict_setter[self.field_folder_base]

        # -------------- update other mutables -------------- #
        self.update()

        # ... continues in downstream objects ... #

    def load_data(self):
        """
        Load data from file. Expected to overwrite superior methods.

        :param file_data: file path to data.
        :type file_data: str
        :return: None
        :rtype: None
        """
        # -------------- overwrite relative path inputs -------------- #
        file_data = DATA_DIR / "files.csv"

        # -------------- implement loading logic -------------- #

        # -------------- call loading function -------------- #
        df = pd.read_csv(file_data, sep=self.file_csv_sep)
        df = df[["folder", "name"]].copy()
        df.rename(columns={"name": "file"}, inplace=True)
        # handle modifications
        df["folder"] = df["folder"].str.replace("{project}/", "")
        df["folder"] = df["folder"].str.replace("outputs/{id}", "outputs")
        # handle default folders
        df["folder"] = df["folder"].str.replace(
            "climate/{climate-scenario}", "climate/observed"
        )
        df["folder"] = df["folder"].str.replace("lulc/{lulc-scenario}", "lulc/observed")
        df["folder"] = df["folder"].str.replace("basins/{basin}", "basins/main")
        # set templates as none
        df["file_template"] = None

        self.data = df.copy()

        # -------------- post-loading logic -------------- #

        return None

    def setup(self):
        super().setup()
        df = self.get_metadata_df()
        df.to_csv(self.folder_data + "/project_info.csv", sep=";", index=False)
        return None

    def update(self):
        super().update()
        if self.folder_root is not None:

            self.folder_data = str(Path(self.folder_root) / "data")

            self.folder_outputs = str(Path(self.folder_root) / "outputs")
            self.folder_topo = str(Path(self.folder_data) / "topo")
            self.folder_soils = str(Path(self.folder_data) / "soils")
            self.folder_basins = str(Path(self.folder_data) / "basins")
            self.folder_climate = str(Path(self.folder_data) / "climate")
            self.folder_lulc = str(Path(self.folder_data) / "lulc")

    def list_basins(self):
        # todo docstring
        return os.listdir(self.folder_basins)

    def list_scenarios_climate(self):
        # todo docstring
        ls_folder_names = os.listdir(self.folder_climate)
        ls_folders = [Path(self.folder_climate) / folder for folder in ls_folder_names]
        # check if has climate series
        ls_scenarios = []
        for folder in ls_folders:
            file_csv = folder / "climate_series.csv"
            if os.path.exists(file_csv):
                ls_scenarios.append(os.path.basename(folder))
        return ls_scenarios

    def list_scenarios_lulc(self):
        # todo docstring
        ls_folder_names = os.listdir(self.folder_lulc)
        ls_folders = [Path(self.folder_lulc) / folder for folder in ls_folder_names]
        # check if has lulc-style raster maps
        ls_scenarios = []
        for folder in ls_folders:
            ls_tifs = glob.glob(f"{folder}/lulc_*.tif")
            if len(ls_tifs) > 0:
                ls_scenarios.append(os.path.basename(folder))
        return ls_scenarios

    def make_run_folder(self, run_name):
        # todo docstring
        while True:
            ts = Project.get_timestamp()
            folder_run = Path(self.folder_outputs) / f"{run_name}_{ts}"
            if os.path.exists(folder_run):
                time.sleep(1)
            else:
                os.mkdir(folder_run)
                break

        return folder_run

    def run_demo(self):
        # todo docstring
        run_name = str(self.run_demo.__name__).replace("run_", "")
        folder_run = os.path.abspath(
            self.make_run_folder(run_name=run_name.replace("_", "-"))
        )
        cmd = [
            sys.executable,
            "-m",
            # tool name
            "plans.tools",
            run_name,
            # arguments
            "--folder",
            folder_run,
            "--input1",
            "./tests/data/DataSet_data.csv",
            "--input2",
            "./tests/data/DataSet_data.csv",
        ]
        if self.talk:
            cmd.append("--talk")

        # Use Popen for async execution
        process = subprocess.Popen(cmd)
        return process, folder_run

    def run_analysis_dto(self, include_views=True, use_basin=None):
        # todo docstring
        run_name = str(self.run_analysis_dto.__name__).replace("run_", "")
        folder_run = os.path.abspath(
            self.make_run_folder(run_name=run_name.replace("_", "-"))
        )

        # set iputs
        file_ldd = Path(self.folder_topo) / "ldd.tif"
        handle_input_file(file_ldd, ">> check ldd.tif")
        if use_basin is not None:
            file_basin = Path(self.folder_basins) / f"{use_basin}/basin.tif"
            handle_input_file(file_basin, ">> check basin")

        cmd = [
            sys.executable,
            "-m",
            # tool name
            "plans.tools",
            run_name,
            # arguments
            "--folder",
            folder_run,
            "--ldd",
            file_ldd,
            "--label",
            self.name,
        ]

        if use_basin is not None:
            cmd = cmd + ["--basin", file_basin]

        if include_views:
            cmd.append("--views")

        if self.talk:
            cmd.append("--talk")

        # Use Popen for async execution
        process = subprocess.Popen(cmd)
        return process, folder_run

    def run_analysis_lulc_series(
        self, lulc_scenario, include_views=True, use_basin=None
    ):
        # todo docstring
        run_name = str(self.run_analysis_lulc_series.__name__).replace("run_", "")
        folder_run = os.path.abspath(
            self.make_run_folder(run_name=run_name.replace("_", "-"))
        )

        # set iputs
        folder_lulc_scenario = Path(self.folder_lulc) / lulc_scenario
        file_lulc = Path(folder_lulc_scenario) / "lulc_attributes.csv"
        handle_input_file(file_lulc, ">> check lulc_attributes")
        if use_basin is not None:
            file_basin = Path(self.folder_basins) / f"{use_basin}/basin.tif"
            handle_input_file(file_basin, ">> check basin")

        cmd = [
            sys.executable,
            "-m",
            "plans.tools",
            run_name,
            "--folder",
            folder_run,
            "--attributes",
            file_lulc,
            "--scenario",
            folder_lulc_scenario,
        ]

        if use_basin is not None:
            cmd = cmd + ["--label", f"{self.name} - {use_basin}"]
            cmd = cmd + ["--aoi", file_basin]
        else:
            cmd = cmd + ["--label", self.name]

        if include_views:
            cmd.append("--views")

        if self.talk:
            cmd.append("--talk")

        # Use Popen for async execution
        process = subprocess.Popen(cmd)
        return process, folder_run

    def run_analysis_climate_series_lulc(
        self,
        climate_scenario,
        lulc_scenario,
        include_views=True,
    ):
        # todo docstring
        run_name = str(self.run_analysis_climate_series_lulc.__name__).replace(
            "run_", ""
        )
        folder_run = os.path.abspath(
            self.make_run_folder(run_name=run_name.replace("_", "-"))
        )

        # set iputs

        file_parameters = Path(self.folder_data) / "parameters_info.csv"
        handle_input_file(file_parameters, ">> check parameters_info")

        folder_climate_scenario = Path(self.folder_climate) / climate_scenario
        file_climate = Path(folder_climate_scenario) / "climate_series.csv"
        handle_input_file(
            file_climate, f">> check climate_series in {climate_scenario}"
        )

        folder_lulc_scenario = Path(self.folder_lulc) / lulc_scenario
        file_lulc = Path(folder_lulc_scenario) / "lulc_series.csv"
        handle_input_file(file_lulc, f">> check lulc_series in {lulc_scenario}")

        cmd = [
            sys.executable,
            "-m",
            "plans.tools",
            run_name,
            "--folder",
            folder_run,
            "--parameters",
            file_parameters,
            "--climate",
            file_climate,
            "--lulc",
            file_lulc,
            "--label",
            f"{lulc_scenario}",
        ]

        if include_views:
            cmd.append("--views")

        if self.talk:
            cmd.append("--talk")

        # Use Popen for async execution
        process = subprocess.Popen(cmd)
        return process, folder_run

    def get_dto(self):
        # todo docstring
        subp, folder_run = self.run_analysis_dto(include_views=True, use_basin=None)
        subp.wait()
        shutil.copy(src=f"{folder_run}/dto.tif", dst=f"{self.folder_topo}/dto.tif")
        shutil.copy(src=f"{folder_run}/dto.jpg", dst=f"{self.folder_topo}/dto.jpg")
        ## shutil.rmtree(folder_run)
        return None

    def get_climate_lulc_series(
        self,
        climate_scenario=None,
        lulc_scenario=None,
        skip_climate_scenario=None,
        skip_lulc_scenario=None,
    ):
        # todo docstring
        # set lists of scenarios
        ls_lulc_scenarios = self.list_scenarios_lulc()
        if lulc_scenario is not None:
            ls_lulc_scenarios = [lulc_scenario]
        ls_climate_scenarios = self.list_scenarios_climate()
        if climate_scenario is not None:
            ls_climate_scenarios = [climate_scenario]

        # setup lists
        ls_processes = []
        ls_folders_run = []
        ls_folders_scenarios = []
        ls_l_cenarios = []
        for c_scenario in ls_climate_scenarios:
            for l_scenario in ls_lulc_scenarios:
                if c_scenario == skip_climate_scenario:
                    pass
                elif l_scenario == skip_lulc_scenario:
                    pass
                else:
                    folder_scenario = Path(self.folder_climate) / c_scenario
                    subp, folder_run = self.run_analysis_climate_series_lulc(
                        climate_scenario=c_scenario,
                        lulc_scenario=l_scenario,
                        include_views=True,
                    )
                    ls_processes.append(subp)
                    ls_folders_run.append(folder_run)
                    ls_folders_scenarios.append(folder_scenario)
                    ls_l_cenarios.append(l_scenario)
        for subp in ls_processes:
            subp.wait()

        # move files
        for i in range(len(ls_folders_run)):
            folder_run = ls_folders_run[i]
            folder_scenario = ls_folders_scenarios[i]
            scenario_lulc = ls_l_cenarios[i]
            file_name = "climate_series_lulc_{}.csv".format(scenario_lulc)
            shutil.copy(
                src=f"{folder_run}/{file_name}", dst=f"{folder_scenario}/{file_name}"
            )
            ## shutil.rmtree(folder_run)

        return None

    def get_lulc_series(self, lulc_scenario=None, skip_lulc_scenario=None):
        # todo docstring
        ls_scenarios = self.list_scenarios_lulc()
        if lulc_scenario is not None:
            ls_scenarios = [lulc_scenario]
        ls_processes = []
        ls_folders_run = []
        ls_folders_scenarios = []
        # run analysis for all scenarios
        for scenario_name in ls_scenarios:
            if scenario_name == skip_lulc_scenario:
                pass
            else:
                folder_scenario = Path(self.folder_lulc) / scenario_name
                subp, folder_run = self.run_analysis_lulc_series(
                    lulc_scenario=scenario_name, include_views=True, use_basin=None
                )
                ls_processes.append(subp)
                ls_folders_run.append(folder_run)
                ls_folders_scenarios.append(folder_scenario)
        for subp in ls_processes:
            subp.wait()
        # move files
        for i in range(len(ls_folders_run)):
            folder_run = ls_folders_run[i]
            folder_scenario = ls_folders_scenarios[i]
            file_name = "lulc_series.csv"
            shutil.copy(
                src=f"{folder_run}/{file_name}", dst=f"{folder_scenario}/{file_name}"
            )
            ls_figs = glob.glob(f"{folder_run}/*.jpg")
            for f in ls_figs:
                file_fig_name = os.path.basename(f)
                shutil.copy(f, f"{folder_scenario}/{file_fig_name}")
            ## shutil.rmtree(folder_run)

        return None

    @staticmethod
    def get_timestamp():
        # compute timestamp
        _now = datetime.datetime.now()
        return str(_now.strftime("%Y-%m-%dT%H%M%S"))


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
    print("Hello world!")
    # ... {develop}

    # Script subsection
    # -------------------------------------------------------------------
    # ... {develop}
