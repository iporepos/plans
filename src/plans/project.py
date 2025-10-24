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
from plans.config import parse_files, parse_fields
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


# CLASSES
# ***********************************************************************

# CLASSES -- Project-level
# =======================================================================


class Project(FileSys):

    # Dunder methods
    # -------------------------------------------------------------------
    def __init__(self, name, alias=None):
        super().__init__(name=name, alias=alias)
        self.load_data()
        self.verbose = True

    def __str__(self):
        s = f"Project: {self.name}\nFolder base: {self.folder_base}\nFolder root: {self.folder_root}"
        return s

    # Internal methods
    # -------------------------------------------------------------------
    def _setup_run_folder(self, tool_name):
        folder_run = self.make_run_folder(run_name=tool_name.replace("_", "-"))
        return folder_run

    # Set methods
    # -------------------------------------------------------------------
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

    # Data methods
    # -------------------------------------------------------------------
    def load_data(self):
        # -------------- overwrite relative path inputs -------------- #

        # -------------- implement loading logic -------------- #

        # -------------- call loading function -------------- #
        self.files_df = parse_files()

        df = self.files_df[["folder", "name"]].copy()
        df.rename(columns={"name": "file"}, inplace=True)
        # handle modifications
        df["folder"] = df["folder"].str.replace("{project}/", "")
        df["folder"] = df["folder"].str.replace("outputs/{id}", "outputs")
        # handle default folders
        df["folder"] = df["folder"].str.replace(
            "climate/{scenario}", "climate/observed"
        )
        df["folder"] = df["folder"].str.replace("lulc/{scenario}", "lulc/observed")
        df["folder"] = df["folder"].str.replace("basins/{basin}", "basins/main")
        # set templates as none
        df["file_template"] = None

        self.data = df.copy()

        # -------------- post-loading logic -------------- #

        return None

    # Make methods
    # -------------------------------------------------------------------
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

        return os.path.abspath(folder_run)

    # Get methods
    # -------------------------------------------------------------------
    def get_metadata(self):
        # ------------ call super ----------- #
        dict_meta = super().get_metadata()

        # removals

        dict_meta.pop(self.field_size)
        dict_meta.pop(self.field_file_data)

        return dict_meta

    def get_list_basins(self):
        # todo docstring
        return os.listdir(self.folder_basins)

    def get_list_scenarios_climate(self):
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

    def get_list_scenarios_lulc(self):
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

    def get_file(self, title, extras=None):
        # todo docstring
        dc = {
            "project": self.folder_root,
        }
        if extras is not None:
            dc.update(extras)
        file_name = self.get_file_name(title=title)
        file_folder = self.get_folder(title=title, formatter=dc)
        return Path(file_folder) / file_name

    def get_file_name(self, title):
        file_name = self.files_df.loc[
            self.files_df["title"] == title, "file_name"
        ].values[0]
        return file_name

    def get_folder(self, title, formatter):
        folder = self.files_df.loc[self.files_df["title"] == title, "folder"].values[0]
        folder = folder.format(**formatter)
        return folder

    # Run methods
    # -------------------------------------------------------------------

    def run_demo(self):
        # todo docstring
        # set run
        # ---------------------------------------------------------------
        tool_name = str(self.run_demo.__name__).replace("run_", "")
        folder_run = self._setup_run_folder(tool_name=tool_name)
        # set iputs
        # ---------------------------------------------------------------

        # set command
        # ---------------------------------------------------------------
        cmd = [
            sys.executable,
            "-m",
            # tool name
            f"plans.tools.{tool_name}",
            # arguments
            "--output",
            folder_run,
            "--label",
            self.name,
            "--project",
            self.name,
            # special args
            "--input1",
            "./tests/data/DataSet_data.csv",
            "--input2",
            "./tests/data/DataSet_data.csv",
        ]
        if self.verbose:
            cmd.append("--verbose")

        # run async execution
        # ---------------------------------------------------------------
        process = subprocess.Popen(cmd)

        return process, folder_run

    def run_analysis_dto(self, include_views=True, use_basin=None):
        # todo docstring
        # set run
        # ---------------------------------------------------------------
        tool_name = str(self.run_analysis_dto.__name__).replace("run_", "")
        folder_run = self._setup_run_folder(tool_name=tool_name)

        # set iputs
        # ---------------------------------------------------------------
        file_ldd = self.get_file(title="Local Drain Direction", extras=None)
        Project.handle_input_file(file_ldd)

        if use_basin is not None:
            extras = {"basin": use_basin}
            file_basin = self.get_file(title="Basin Area", extras=extras)
            Project.handle_input_file(file_basin)

        # set command
        # ---------------------------------------------------------------
        cmd = [
            sys.executable,
            "-m",
            f"plans.tools.{tool_name}",
            # arguments
            "--output",
            folder_run,
            "--ldd",
            file_ldd,
            "--label",
            self.name,
            "--project",
            self.name,
        ]

        if use_basin is not None:
            cmd = cmd + ["--aoi", file_basin]

        if include_views:
            cmd.append("--views")

        if self.verbose:
            cmd.append("--verbose")

        # run async execution
        # ---------------------------------------------------------------
        process = subprocess.Popen(cmd)

        return process, folder_run

    def run_analysis_lulc_series(
        self, lulc_scenario, include_views=True, use_basin=None, use_old=False
    ):
        # todo docstring
        # set run
        # ---------------------------------------------------------------
        tool_name = str(self.run_analysis_lulc_series.__name__).replace("run_", "")
        folder_run = self._setup_run_folder(tool_name=tool_name)

        # set iputs
        # ---------------------------------------------------------------
        folder_lulc_scenario = Path(self.folder_lulc) / lulc_scenario
        extras = {"scenario": lulc_scenario}
        file_lulc_att = self.get_file(title="Land Use Attributes", extras=extras)
        Project.handle_input_file(file_lulc_att)

        if use_basin is not None:
            extras = {"basin": use_basin}
            file_basin = self.get_file(title="Basin Area", extras=extras)
            Project.handle_input_file(file_basin)

        # set command
        # ---------------------------------------------------------------
        cmd = [
            sys.executable,
            "-m",
            f"plans.tools.{tool_name}",
            "--output",
            folder_run,
            "--attributes",
            file_lulc_att,
            "--scenario",
            folder_lulc_scenario,
            "--project",
            self.name,
        ]

        if use_basin is not None:
            # customize label
            tool_label = f"{self.name} - {lulc_scenario} - {use_basin}"
            cmd = cmd + ["--label", tool_label]
            # add aoi to cmd
            cmd = cmd + ["--aoi", file_basin]
        else:
            tool_label = f"{self.name} - {lulc_scenario}"
            cmd = cmd + ["--label", tool_label]

        if include_views:
            cmd.append("--views")

        if self.verbose:
            cmd.append("--verbose")

        # run async execution
        # ---------------------------------------------------------------
        process = subprocess.Popen(cmd)

        return process, folder_run

    def run_analysis_climate_series_lulc(
        self,
        climate_scenario,
        lulc_scenario,
        include_views=True,
    ):
        # todo docstring
        # set run
        # ---------------------------------------------------------------
        tool_name = str(self.run_analysis_climate_series_lulc.__name__).replace(
            "run_", ""
        )
        folder_run = self._setup_run_folder(tool_name=tool_name)

        # set iputs
        # ---------------------------------------------------------------

        file_parameters = self.get_file(title="Parameters Info", extras=None)
        Project.handle_input_file(file_parameters)

        extras = {"scenario": climate_scenario}
        file_climate_series = self.get_file(title="Climate Series", extras=extras)
        Project.handle_input_file(file_climate_series)

        extras = {"scenario": lulc_scenario}
        file_lulc_series = self.get_file(title="Land Use Series", extras=extras)
        Project.handle_input_file(file_lulc_series)

        # set command
        # ---------------------------------------------------------------
        cmd = [
            sys.executable,
            "-m",
            f"plans.tools.{tool_name}",
            "--output",
            folder_run,
            "--parameters",
            file_parameters,
            "--climate",
            file_climate_series,
            "--lulc",
            file_lulc_series,
            "--label",
            f"{lulc_scenario}",
            "--project",
            self.name,
        ]

        if include_views:
            cmd.append("--views")

        if self.verbose:
            cmd.append("--verbose")

        # run async execution
        # ---------------------------------------------------------------
        process = subprocess.Popen(cmd)

        return process, folder_run

    def run_analysis_soils_parameters(self, include_views=True):
        # todo docstring
        # set run
        # ---------------------------------------------------------------
        tool_name = str(self.run_analysis_soils_parameters.__name__).replace("run_", "")
        folder_run = self._setup_run_folder(tool_name=tool_name)

        # set iputs
        # ---------------------------------------------------------------
        extras = None
        file_parameters = self.get_file(title="Parameters Info", extras=extras)
        Project.handle_input_file(file_parameters)

        extras = None
        file_soils_att = self.get_file(title="Soils Attributes", extras=extras)
        Project.handle_input_file(file_soils_att)

        extras = None
        file_soils = self.get_file(title="Soils Map", extras=extras)
        Project.handle_input_file(file_soils)

        extras = {"basin": "main"}
        file_basin = self.get_file(title="Basin Area", extras=extras)
        Project.handle_input_file(file_basin)

        # set command
        # ---------------------------------------------------------------
        cmd = [
            sys.executable,
            "-m",
            f"plans.tools.{tool_name}",
            "--output",
            folder_run,
            "--parameters",
            file_parameters,
            "--attributes",
            file_soils_att,
            "--soils",
            file_soils,
            "--aoi",
            file_basin,
            "--label",
            self.name,
            "--project",
            self.name,
        ]

        if include_views:
            cmd.append("--views")

        if self.verbose:
            cmd.append("--verbose")

        # run async execution
        # ---------------------------------------------------------------
        process = subprocess.Popen(cmd)

        return process, folder_run

    # todo refactor --- move to plans.tools
    def run_analysis_lulc_parameters(self, lulc_scenario, include_views=True):
        # todo docstring
        # set run
        # ---------------------------------------------------------------
        tool_name = str(self.run_analysis_lulc_parameters.__name__).replace("run_", "")
        folder_run = self._setup_run_folder(tool_name=tool_name)

        # set iputs
        # ---------------------------------------------------------------
        extras = None
        file_parameters = self.get_file(title="Parameters Info", extras=extras)
        Project.handle_input_file(file_parameters)

        extras = {"scenario": lulc_scenario}
        file_lulc_attr = self.get_file(title="Land Use Attributes", extras=extras)
        Project.handle_input_file(file_lulc_attr)

        folder_lulc_scenario = Path(self.folder_lulc) / lulc_scenario

        extras = {"basin": "main"}
        file_basin = self.get_file(title="Basin Area", extras=extras)
        Project.handle_input_file(file_basin)

        # set command
        # ---------------------------------------------------------------
        cmd = [
            sys.executable,
            "-m",
            f"plans.tools.{tool_name}",
            "--output",
            folder_run,
            "--parameters",
            file_parameters,
            "--attributes",
            file_lulc_attr,
            "--scenario",
            folder_lulc_scenario,
            "--aoi",
            file_basin,
            "--label",
            f"{self.name} - {lulc_scenario}",
            "--project",
            self.name,
        ]

        if include_views:
            cmd.append("--views")

        if self.verbose:
            cmd.append("--verbose")

        # run async execution
        # ---------------------------------------------------------------
        process = subprocess.Popen(cmd)

        return process, folder_run

    # Generate methods
    # -------------------------------------------------------------------
    def generate_dto(self):
        # todo docstring
        # run
        # ---------------------------------------------------------------
        subp, folder_run = self.run_analysis_dto(include_views=True, use_basin=None)
        subp.wait()

        # copy files
        # ---------------------------------------------------------------
        Project.copy_output_files(
            folder_output=folder_run,
            folder_dst=self.folder_topo,
            include_runfiles=False,
        )
        return None

    def generate_lulc_series(self, lulc_scenario=None, skip_lulc_scenario=None):
        # todo docstring
        # setup
        # ---------------------------------------------------------------
        ls_scenarios = self.get_list_scenarios_lulc()
        if lulc_scenario is not None:
            ls_scenarios = [lulc_scenario]
        ls_processes = []
        ls_folders_run = []
        ls_folders_scenarios = []

        # run loop
        # ---------------------------------------------------------------
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

        # copy files
        # ---------------------------------------------------------------
        for i in range(len(ls_folders_run)):
            folder_run = ls_folders_run[i]
            folder_scenario = ls_folders_scenarios[i]
            Project.copy_output_files(
                folder_output=folder_run,
                folder_dst=folder_scenario,
                include_runfiles=False,
            )

        return None

    def generate_climate_series_lulc(
        self,
        climate_scenario=None,
        lulc_scenario=None,
        skip_climate_scenario=None,
        skip_lulc_scenario=None,
    ):
        # todo docstring
        # setup
        # ---------------------------------------------------------------
        ls_lulc_scenarios = self.get_list_scenarios_lulc()
        if lulc_scenario is not None:
            ls_lulc_scenarios = [lulc_scenario]
        ls_climate_scenarios = self.get_list_scenarios_climate()
        if climate_scenario is not None:
            ls_climate_scenarios = [climate_scenario]

        # run loop
        # ---------------------------------------------------------------
        # setup lists
        ls_processes = []
        ls_folders_run = []
        ls_folders_scenarios = []
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
        for subp in ls_processes:
            subp.wait()

        # copy files
        # ---------------------------------------------------------------
        for i in range(len(ls_folders_run)):
            folder_run = ls_folders_run[i]
            folder_scenario = ls_folders_scenarios[i]
            Project.copy_output_files(
                folder_output=folder_run,
                folder_dst=folder_scenario,
                include_runfiles=False,
            )

        return None

    def generate_soils_parameters(self):
        # run
        # ---------------------------------------------------------------
        subp, folder_run = self.run_analysis_soils_parameters(
            include_views=self.verbose
        )
        subp.wait()

        # move files
        # ---------------------------------------------------------------

        folder_parameters = Path(self.folder_soils) / "parameters"
        os.makedirs(folder_parameters, exist_ok=True)

        Project.copy_output_files(
            folder_output=folder_run,
            folder_dst=folder_parameters,
            include_runfiles=False,
        )
        return None

    def generate_lulc_parameters(self, lulc_scenario=None, skip_lulc_scenario=None):

        ls_scenarios = self.get_list_scenarios_lulc()

        if lulc_scenario is not None:
            ls_scenarios = [lulc_scenario]

        ls_processes = []
        ls_folder_run = []
        # run loop
        # ---------------------------------------------------------------
        for s in ls_scenarios:
            if s == skip_lulc_scenario:
                pass
            else:
                subp, folder_run = self.run_analysis_lulc_parameters(
                    lulc_scenario=s, include_views=self.verbose
                )
                ls_processes.append(subp)
                ls_folder_run.append(folder_run)

        for sub in ls_processes:
            sub.wait()

        # move files
        # ---------------------------------------------------------------
        for i in range(len(ls_scenarios)):
            scenario = ls_scenarios[i]
            folder_run = ls_folder_run[i]
            folder_parameters = Path(self.folder_lulc) / f"{scenario}/parameters"
            os.makedirs(folder_parameters, exist_ok=True)

            Project.copy_output_files(
                folder_output=folder_run,
                folder_dst=folder_parameters,
                include_runfiles=False,
            )
            return None

    # Static methods
    # -------------------------------------------------------------------
    @staticmethod
    def copy_output_files(folder_output, folder_dst, include_runfiles=False):
        # list files
        ls_maps = glob.glob(f"{folder_output}/*.tif")
        ls_figs = glob.glob(f"{folder_output}/*.jpg")
        ls_tbls = glob.glob(f"{folder_output}/*.csv")

        # handle runfiles
        ls_runs = []
        ls_formats = ["txt", "rst", "md", "tex", "html"]
        if include_runfiles:
            for fmt in ls_formats:
                ls_lcl = glob.glob(f"{folder_output}/*.{fmt}")
                ls_runs = ls_runs[:] + ls_lcl[:]
        ls_files = ls_maps + ls_tbls + ls_figs + ls_runs

        if len(ls_files) == 0:
            return None

        # copy loop
        for f in ls_files:
            file_name = os.path.basename(f)
            f_dst = Path(folder_dst) / file_name
            shutil.copy(src=f, dst=f_dst)
        return None

    @staticmethod
    def move_output_files(folder_output, folder_dst, include_runfiles=False):
        Project.copy_output_files(
            folder_output=folder_output,
            folder_dst=folder_dst,
            include_runfiles=include_runfiles,
        )
        shutil.rmtree(folder_output)
        return None

    @staticmethod
    def handle_input_file(file_path):
        file_name = os.path.basename(file_path)
        parent_folder = Path(file_path).parent.absolute()
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f">>> check {file_name} in {parent_folder}")
        else:
            pass

    @staticmethod
    def get_timestamp():
        # compute timestamp
        now = datetime.datetime.now()
        return str(now.strftime("%Y-%m-%dT%H%M%S"))


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
