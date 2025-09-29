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
import datetime
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
from plans.root import FileSys
from plans.root import RecordTable

# ... {develop}


# CONSTANTS
# ***********************************************************************
# define constants in uppercase


# FUNCTIONS
# ***********************************************************************
def new_project(specs):
    """
    Create a new Project from a specification dictionary.

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

        # setup specs dictionary
        project_specs = {
            "folder_base": "path/to/base/folder",
            "name": "newProject",
            "alias": "NPrj",
            "source": "Me",
            "description": "Just a test"
        }

    Then call ``new_project()``

    .. code-block:: python

        # get project instance
        pj = plans.new_project(specs=project_specs)


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
        folder_base = Path(project_folder).parent
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
            p.export_metadata(folder=project_folder, filename=boot_file_name)
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
        file_data = os.path.abspath("./src/plans/data/files.csv")

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
        run_name = "demo"
        folder_run = os.path.abspath(self.make_run_folder(run_name=run_name))
        cmd = [
            sys.executable,
            "-m",
            "plans.tools",
            "demo",
            "--input1",
            "./tests/data/DataSet_data.csv",
            "--input2",
            "./tests/data/DataSet_data.csv",
            "--folder",
            folder_run,
        ]
        if self.talk:
            cmd.append("--talk")

        # Use Popen for async execution
        process = subprocess.Popen(cmd)
        return process, folder_run

    def run_dto_analysis(self):
        run_name = "dto"
        folder_run = os.path.abspath(self.make_run_folder(run_name=run_name))
        file_input1 = "C:/data/ldd.tif"
        cmd = [
            sys.executable,
            "-m",
            "plans.tools",
            "run_dto",
            "--input1",
            file_input1,
            "--folder",
            folder_run,
        ]
        if self.talk:
            cmd.append("--talk")

        # Use Popen for async execution
        process = subprocess.Popen(cmd)
        return process, folder_run

    @staticmethod
    def get_timestamp():
        # compute timestamp
        _now = datetime.datetime.now()
        return str(_now.strftime("%Y%m0%dT%H%M%S"))


# todo [refactor] -- here we got some very interesting stuff
class Project_(FileSys):

    def __init__(self, name, folder_base, alias=None):
        """Initiate a project

        :param name: unique object name
        :type name: str

        :param alias: unique object alias.
            If None, it takes the first and last characters from ``name``
        :type alias: str

        :param folder_base: path to base folder
        :type name: str
        """
        # ---------- call super -----------#
        super().__init__(name=name, folder_base=folder_base, alias=alias)

        # overwrite struture of the project
        self.structure = self.get_structure()

        self.topo_status = None
        # self.update_status_topo()

        self.topo = None
        self.soil = None
        self.lulc = None
        self.et = None
        self.ndvi = None

    def download_datasets(self, zip_url):
        """
        Download datasets from a URL.
        The download is expected to be a ZIP file. Note: requests library is required

        :param zip_url: url to dataset ZIP file
        :type zip_url: str
        :return: None
        :rtype: None
        """
        import requests

        # 1) download to main folder
        print("Downloading datasets from URL...")
        response = requests.get(zip_url)
        # just in case of any problem
        response.raise_for_status()
        _s_zipfile = "{}/samples.zip".format(self.path_main)
        with open(_s_zipfile, "wb") as file:
            file.write(response.content)
        # 2) extract to datasets folder
        self.extract_datasets(zip_file=_s_zipfile, remove=True)
        return None

    def download_default_datasets(self):
        """
        Download the default datasets for PLANS

        :return: None
        :rtype: None
        """
        zip_url = (
            "https://zenodo.org/record/8217681/files/default_samples.zip?download=1"
        )
        self.download_datasets(zip_url=zip_url)
        return None

    def extract_datasets(self, zip_file, remove=False):
        """
        Extract from ZIP file to datasets folder

        :param zip_file: path to zip file
        :type zip_file: str
        :param remove: option for deleting the zip file after extraction
        :type remove: bool
        :return: None
        :rtype: None
        """
        import zipfile

        print("Unzipping dataset files...")
        with zipfile.ZipFile(zip_file, "r") as zip_ref:
            zip_ref.extractall(self.path_ds)
        # 3) delete zip file
        if remove:
            os.remove(zip_file)
        return None


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
