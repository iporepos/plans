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

Example
-------

# todo [major docstring improvement] -- examples
Lorem ipsum dolor sit amet, consectetur adipiscing elit.
Nulla mollis tincidunt erat eget iaculis. Mauris gravida ex quam,
in porttitor lacus lobortis vitae. In a lacinia nisl.

.. code-block:: python

    import numpy as np
    print("Hello World!")

Mauris gravida ex quam, in porttitor lacus lobortis vitae.
In a lacinia nisl. Mauris gravida ex quam, in porttitor lacus lobortis vitae.
In a lacinia nisl.
"""

# IMPORTS
# ***********************************************************************
# import modules from other libs

# Native imports
# =======================================================================
import os

# ... {develop}

# External imports
# =======================================================================
import pandas as pd

# ... {develop}

# Project-level imports
# =======================================================================
from plans.root import FileSys

# ... {develop}


# CONSTANTS
# ***********************************************************************
# define constants in uppercase


# FUNCTIONS
# ***********************************************************************


# CLASSES
# ***********************************************************************

# CLASSES -- Project-level
# =======================================================================


class Project(FileSys):

    def __init__(self):
        super().__init__(name="PlansProject", alias=None)

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
            "climate/{scenario}", "climate/observed"
        )
        df["folder"] = df["folder"].str.replace("lulc/{scenario}", "lulc/observed")
        df["folder"] = df["folder"].str.replace("basins/{basin}", "basins/main")
        df["file_template"] = None

        self.data = df.copy()

        # -------------- post-loading logic -------------- #
        """
        self.data = self.data[
            ["Folder", "File", "Format", "File_Source", "Folder_Source"]
        ].copy()
        """

        return None

    def setup(self):
        super().setup()
        df = self.get_metadata_df()
        df.to_csv(self.folder_root + "/project_info.csv", sep=";", index=False)
        return None


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
        """Download datasets from a URL. The download is expected to be a ZIP file. Note: requests library is required

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
        """Download the default datasets for PLANS

        :return: None
        :rtype: None
        """
        zip_url = (
            "https://zenodo.org/record/8217681/files/default_samples.zip?download=1"
        )
        self.download_datasets(zip_url=zip_url)
        return None

    def extract_datasets(self, zip_file, remove=False):
        """Extract from ZIP file to datasets folder

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
