# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.

"""
This module provides a set of the primitive classes used.

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
import glob, re
import os, copy, shutil, datetime, pprint
from pathlib import Path

# ... {develop}

# External imports
# =======================================================================
import pandas as pd
import matplotlib.pyplot as plt

# ... {develop}

# Project-level imports
# =======================================================================
# import {module}
# ... {develop}

# CONSTANTS
# ***********************************************************************
# define constants in uppercase

# CONSTANTS -- Project-level
# =======================================================================
# ... {develop}

# CONSTANTS -- Module-level
# =======================================================================
# ... {develop}


# FUNCTIONS
# ***********************************************************************

# FUNCTIONS -- Project-level
# =======================================================================
# ... {develop}

# FUNCTIONS -- Module-level
# =======================================================================
# ... {develop}


# CLASSES
# ***********************************************************************

# CLASSES -- Project-level
# =======================================================================


class MbaE:
    """
    **Mba'e** in Guarani means **Thing**.

    .. important::

        **Mba'e is the origin**. The very-basic almost-zero level object.
        Deeper than here is only the Python builtin ``object`` class.


    **Examples:**

    Here's how to use the ``MbaE`` class:

    Import ``MbaE``:

    .. code-block:: python

        # import the object
        from plans.root import MbaE

    ``MbaE`` instantiation

    .. code-block:: python

        # MbaE instantiation
        m0 = MbaE(name="Algo", alias="al")

    Retrieve metadata (not all attributes)

    .. code-block:: python

        # Retrieve metadata (not all attributes)
        d = m0.get_metadata()
        print(d)

    Retrieve metadata in a :class:`pandas.DataFrame`

    .. code-block:: python

        # Retrieve metadata in a :class:`pandas.DataFrame`
        df = m0.get_metadata_df()
        print(df.to_string(index=False))

    Set new values for metadata

    .. code-block:: python

        # Set new values for metadata
        d2 = {"Name": "Algo2", "Alias": "al2"}
        m0.set(dict_setter=d2)

    Boot attributes from csv file:

    .. code-block:: python

        # Boot attributes from csv file:
        m0.boot(bootfile="/content/metadata.csv")


    """

    def __init__(self, name="MyMbaE", alias=None):
        """Initialize the ``MbaE`` object.

        :param name: unique object name
        :type name: str
        :param alias: unique object alias.
            If None, it takes the first and last characters from ``name``
        :type alias: str

        """
        # ------------ pseudo-static ----------- #
        self.object_name = self.__class__.__name__
        self.object_alias = "mbae"
        self.name = name
        self.alias = alias

        # handle None alias
        if self.alias is None:
            self._create_alias()

        # fields
        self._set_fields()

        # defaults
        self.file_csv_sep = ";"
        self.file_csv_ext = ".csv"
        self.file_encoding = "utf-8"

        # ------------ set mutables ----------- #
        self.bootfile = None
        self.folder_bootfile = "./"  # start in the local place

        # ... continues in downstream objects ... #

    def __str__(self):
        """The ``MbaE`` string"""
        str_type = str(type(self))
        str_df_metadata = self.get_metadata_df().to_string(index=False)
        str_out = "[{} ({})]\n{} ({}):\t{}\n{}".format(
            self.name,
            self.alias,
            self.object_name,
            self.object_alias,
            str_type,
            str_df_metadata,
        )
        return str_out

    def _create_alias(self):
        """
        If ``alias`` is ``None``, it takes the first and last characters from ``name``
        """
        if len(self.name) >= 2:
            self.alias = self.name[0] + self.name[len(self.name) - 1]
        else:
            self.alias = self.name[:]

    def _set_fields(self):
        """
        Set fields names
        """

        # Attribute fields
        self.field_name = "name"
        self.field_alias = "alias"

        # Bootfile fields
        self.field_bootfile_attribute = "attribute"
        self.field_bootfile_value = "value"
        # ... continues in downstream objects ... #

    def get_metadata(self):
        """
        Get a dictionary with object metadata.

        :return: dictionary with all metadata
        :rtype: dict

        .. warning::

            Metadata does not necessarily include all object attributes.

        """
        dict_meta = {
            self.field_name: self.name,
            self.field_alias: self.alias,
        }
        return dict_meta

    def get_metadata_df(self):
        """
        Get a :class:`pandas.DataFrame` created from the metadata dictionary.

        :return: :class:`pandas.DataFrame` with ``Attribute`` and ``Value``
        :rtype: :class:`pandas.DataFrame`
        """
        dict_metadata = self.get_metadata()
        df_metadata = pd.DataFrame(
            {
                self.field_bootfile_attribute: [k for k in dict_metadata],
                self.field_bootfile_value: [dict_metadata[k] for k in dict_metadata],
            }
        )
        return df_metadata

    def setter(self, dict_setter):
        """
        Set selected attributes based on an incoming dictionary.

        :param dict_setter: incoming dictionary with attribute values
        :type dict_setter: dict
        """
        # ---------- set basic attributes --------- #
        self.name = dict_setter[self.field_name]
        self.alias = dict_setter[self.field_alias]

        # ... continues in downstream objects ... #

    def boot(self, bootfile):
        """
        Boot basic attributes from a ``csv`` table.

        :param bootfile: file path to ``csv`` table with booting information.
        :type bootfile: str



        **Notes**

        Expected ``bootfile`` format:

        .. code-block:: text

            Attribute;Value
            Name;ResTia
            Alias;Ra
            ...;...


        """
        # ---------- update file attributes ---------- #
        self.bootfile = Path(bootfile[:])
        self.folder_bootfile = os.path.dirname(bootfile)

        # get expected fields
        list_columns = [self.field_bootfile_attribute, self.field_bootfile_value]

        # read info table from ``csv`` file. metadata keys are the expected fields
        df_boot_table = pd.read_csv(bootfile, sep=";", usecols=list_columns)

        # setter loop
        dict_setter = {}
        for i in range(len(df_boot_table)):
            # build setter from row
            dict_setter[df_boot_table[self.field_bootfile_attribute].values[i]] = (
                df_boot_table[self.field_bootfile_value].values[i]
            )

        # pass setter to set() method
        # pprint.pprint(dict_setter)
        self.setter(dict_setter=dict_setter)

        return None

    def export(self, folder, filename):
        """
        Export object resources to destination file.

        :param folder: path to folder
        :type folder: str
        :param filename: file name without extension
        :type filename: str
        """
        df_metadata = self.get_metadata_df()
        # handle filename
        fpath = Path(folder + "/" + filename + self.file_csv_ext)
        # export
        df_metadata.to_csv(
            fpath, sep=self.file_csv_sep, encoding=self.file_encoding, index=False
        )
        # ... continues in downstream objects ... #
        return None

    def save(self):
        """
        Save object resources to sourced files.

        .. danger::

            This method overwrites the sourced data file.

        """
        folder = os.path.dirname(self.bootfile)
        filename = os.path.basename(self.bootfile).split(".")[0]
        self.export(folder=folder, filename=filename)
        # ... continues in downstream objects ... #
        return None


class Collection(MbaE):
    """
    A collection of primitive ``MbaE`` objects with associated metadata.
    Useful for large scale manipulations in ``MbaE``-based objects.
    Expected to have custom methods and attributes downstream.

    **Main Attributes**

    - ``catalog`` (:class:`pandas.DataFrame`): A catalog containing metadata of the objects in the test_collection.
    - ``collection`` (dict): A dictionary containing the objects in the ``Collection``.
    - name (str): The name of the ``Collection``.
    - alias (str): The name of the ``Collection``.
    - baseobject: The class of the base object used to initialize the ``Collection``.

    **Main Methods**

    - __init__(self, base_object, name="myCatalog"): Initializes a new ``Collection`` with a base object.
    - update(self, details=False): Updates the ``Collection`` catalog.
    - append(self, new_object): Appends a new object to the ``Collection``.
    - remove(self, name): Removes an object from the ``Collection``.

    **Examples**

    Here's how to use the ``Collection`` class:

    Import objects:

    .. code-block:: python

        # import MbaE-based object
        from plans.root import MbaE

        # import Collection
        from plans.root import Collection

    Instantiate ``Collection``:

    .. code-block:: python

        # instantiate Collection object
        c = Collection(base_object=MbaE, name="Collection")

    Append a new object to the ``Collection``:

    .. code-block:: python

        # append a new object
        m1 = MbaE(name="Thing1", alias="al1")
        c.append(m1)  # use .append()

    Append extra objects:

    .. code-block:: python

        # append extra objects
        m2 = MbaE(name="Thing2", alias="al2")
        c.append(m2)  # use .append()
        m3 = MbaE(name="Res", alias="r")
        c.append(m3)  # use .append()

    Print the catalog :class:`pandas.DataFrame`:

    .. code-block:: python

        # print catalog :class:`pandas.DataFrame`
        print(c.catalog)

    Print the collection dict:

    .. code-block:: python

        # print collection dict
        print(c.collection)

    Remove an object by using object name:

    .. code-block:: python

        # remove object by object name
        c.remove(name="Thing1")

    Apply MbaE-based methods for Collection

    .. code-block:: python

        # -- apply MbaE methods for Collection

        # reset metadata
        c.set(dict_setter={"Name": "Coll", "Alias": "C1"})

        # Boot attributes from csv file:
        c.boot(bootfile="/content/metadata_coll.csv")


    """

    def __init__(self, base_object, name="MyCollection", alias="Col0"):
        """
        Initialize the ``Collection`` object.

        :param base_object: ``MbaE``-based object for collection
        :type base_object: :class:`MbaE`
        :param name: unique object name
        :type name: str
        :param alias: unique object alias.
            If None, it takes the first and last characters from name
        :type alias: str
        """
        # ------------ call super ----------- #
        super().__init__(name=name, alias=alias)
        # ------------ set pseudo-static ----------- #
        self.object_alias = "COL"
        # Set the name and baseobject attributes
        self.baseobject = base_object
        self.baseobject_name = base_object.__name__

        # Initialize the catalog with an empty DataFrame
        dict_metadata = self.baseobject().get_metadata()

        self.catalog = pd.DataFrame(columns=dict_metadata.keys())

        # Initialize the ``Collection`` as an empty dictionary
        self.collection = dict()

        # ------------ set mutables ----------- #
        self.size = 0

        self._set_fields()
        # ... continues in downstream objects ... #

    def __str__(self):
        str_type = str(type(self))
        str_df_metadata = self.get_metadata_df().to_string(index=False)
        str_df_data = self.catalog.to_string(index=False)
        str_out = "{}:\t{}\nMetadata:\n{}\nCatalog:\n{}\n".format(
            self.name, str_type, str_df_metadata, str_df_data
        )
        return str_out

    def _set_fields(self):
        # ------------ call super ----------- #
        super()._set_fields()

        # Attribute fields
        self.field_size = "Size"
        self.field_baseobject = "Base_Object"  # self.baseobject().__name__

        # ... continues in downstream objects ... #

    def get_metadata(self):
        """
        Get a dictionary with object metadata.


        .. note::

            Metadata does **not** necessarily inclue all object attributes.

        :return: dictionary with all metadata
        :rtype: dict
        """
        # ------------ call super ----------- #
        dict_meta = super().get_metadata()

        # customize local metadata:
        dict_meta_local = {
            self.field_size: self.size,
            self.field_baseobject: self.baseobject_name,
        }

        # update
        dict_meta.update(dict_meta_local)
        return dict_meta

    def update(self, details=False):
        """
        Update the ``Collection`` catalog.

        :param details: Option to update catalog details, defaults to False.
        :type details: bool
        """

        # Update details if specified
        if details:
            # Create a new empty catalog
            # df_new_catalog = pd.DataFrame(columns=self.catalog.columns)

            # retrieve details from collection
            ls_dfs = list()
            for name in self.collection:
                # retrieve updated metadata from base object
                dct_meta = self.collection[name].get_metadata()

                # set up a single-row helper dataframe
                lst_keys = dct_meta.keys()
                _dct = dict()
                for k in lst_keys:
                    _dct[k] = [dct_meta[k]]

                # Set new information
                df_aux = pd.DataFrame(_dct)
                df_aux = df_aux[self.catalog.columns]
                ls_dfs.append(df_aux)

            # concat new catalog
            df_new_catalog = pd.concat(ls_dfs, ignore_index=True)

            # consider if the name itself has changed in the
            old_key_names = list(self.collection.keys())[:]
            new_key_names = list(df_new_catalog[self.catalog.columns[0]].values)

            # loop for checking consistency in collection keys
            for i in range(len(old_key_names)):
                old_key = old_key_names[i]
                new_key = new_key_names[i]
                # name change condition
                if old_key != new_key:
                    # rename key in the collection dictionary
                    self.collection[new_key] = self.collection.pop(old_key)

            # Update the catalog with the new details
            self.catalog = df_new_catalog.copy()
            # clear
            del df_new_catalog

        # Basic updates
        # --- the first row is expected to be the Unique name
        str_unique_name = self.catalog.columns[0]
        self.catalog = self.catalog.drop_duplicates(subset=str_unique_name, keep="last")
        self.catalog = self.catalog.sort_values(by=str_unique_name).reset_index(
            drop=True
        )
        self.size = len(self.catalog)
        return None

    # review ok
    def append(self, new_object):
        """
        Append a new object to the ``Collection``.

        :param new_object: Object to append.
        :type new_object: object


        .. important::

            The object is expected to have a ``.get_metadata()`` method that
            returns a dictionary with metadata keys and values.


        """
        # Append a copy of the object to the ``Collection``
        copied_object = copy.deepcopy(new_object)
        self.collection[new_object.name] = copied_object

        # Update the catalog with the new object's metadata
        dct_meta = new_object.get_metadata()
        dct_meta_df = dict()
        for k in dct_meta:
            dct_meta_df[k] = [dct_meta[k]]
        df_aux = pd.DataFrame(dct_meta_df)

        # Check if self.catalog is empty before concatenation
        if self.catalog.empty:
            # If it's empty, just assign df_aux to self.catalog
            self.catalog = df_aux
        else:
            # If it's not empty, perform the concatenation
            self.catalog = pd.concat([self.catalog, df_aux], ignore_index=True)

        self.update()
        return None

    def remove(self, name):
        """
        Remove an object from the ``Collection`` by the name.

        :param name: Name attribute of the object to remove.
        :type name: str

        """
        # Delete the object from the ``Collection``
        del self.collection[name]
        # Delete the object's entry from the catalog
        str_unique_name = self.catalog.columns[
            0
        ]  # assuming the first column is the unique name
        self.catalog = self.catalog.drop(
            self.catalog[self.catalog[str_unique_name] == name].index
        ).reset_index(drop=True)
        self.update()
        return None


class DataSet(MbaE):
    """
    The core ``DataSet`` base class.

    **Notes**

    Expected to hold one :class:`pandas.DataFrame`.
    This is a Base and Dummy object. Expected to be implemented downstream for
    custom applications.

    **Examples**

    Import ``Dataset``

    .. code-block:: python

        # import Dataset
        from plans.root import DataSet

    Instantiate ``Dataset`` Object

    .. code-block:: python

        # instantiate DataSet object
        ds = DataSet(name="DataSet_1", alias="DS1")

    Set object and load data

    .. code-block:: python

        # set object and load data.
        # Note: this dummy object expects "RM", "P", and "TempDB" as columns in data
        ds.set(
            dict_setter={
                "Name": "DataSet_2",
                "Alias": "DS2",
                "Color": "red",
                "Source": "",
                "Description": "This is DataSet Object",
                "File_Data": "/content/data_ds1.csv"
            },
            load_data=True
        )

    Check data

    .. code-block:: python

        # check data :class:`pandas.DataFrame`
        print(ds.data.head())

    Reload new data from file

    .. code-block:: python

        # re-load new data from file
        ds.load_data(file_data="/content/data_ds2.csv")

    Get view

    .. code-block:: python

        # get basic visual
        ds.view(show=True)

    Customize view specifications

    .. code-block:: python

        # customize view parameters via the view_specs attribute:
        ds.view_specs["title"] = "My Custom Title"
        ds.view(show=True)

    Save the view

    .. code-block:: python

        # save the figure
        ds.view_specs["folder"] = "path/to/folder"
        ds.view_specs["filename"] = "my_visual"
        ds.view_specs["fig_format"] = "png"
        ds.view(show=False)


    """

    def __init__(self, name="MyDataSet", alias="DS0"):
        """
        Initialize the ``DataSet`` object.

        :param name: unique object name
        :type name: str
        :param alias: unique object alias. If None, it takes the first and last characters from name
        :type alias: str

        """
        # ------------ call super ----------- #
        super().__init__(name=name, alias=alias)
        # overwriters
        self.object_alias = "DS"

        # ------------ set mutables ----------- #
        self.file_data = None
        self.folder_data = None
        self.data = None
        self.size = None

        # descriptors
        self.source = None
        self.description = None

        # ------------ set defaults ----------- #
        self.color = "blue"

        # UPDATE
        self.update()

        # ... continues in downstream objects ... #

    def __str__(self):
        str_super = super().__str__()
        if self.data is None:
            str_df_data = "None"
            str_out = "{}\nData:\n{}\n".format(str_super, str_df_data)
        else:
            # first 5 rows
            str_df_data_head = self.data.head().to_string(index=False)
            str_df_data_tail = self.data.tail().to_string(index=False)
            str_out = "{}\nData:\n{}\n ... \n{}\n".format(
                str_super, str_df_data_head, str_df_data_tail
            )
        return str_out

    def _set_fields(self):
        # ------------ call super ----------- #
        super()._set_fields()
        # Attribute fields
        self.field_file_data = "file_data"
        self.field_size = "size"
        self.field_color = "color"
        self.field_source = "source"
        self.field_description = "description"
        # ... continues in downstream objects ... #

    def _set_view_specs(self):
        """
        Set view specifications.

        """
        self.view_specs = {
            "folder": self.folder_data,
            "filename": self.name,
            "style": "wien",
            "fig_format": "jpg",
            "dpi": 300,
            "title": self.name,
            "width": 5 * 1.618,
            "height": 5 * 1.618,
            "xvar": "RM",
            "yvar": "TempDB",
            "xlabel": "RM",
            "ylabel": "TempDB",
            "color": self.color,
            "xmin": None,
            "xmax": None,
            "ymin": None,
            "ymax": None,
            "gs_wspace": 0.2,
            "gs_hspace": 0.1,
            "gs_left": 0.05,
            "gs_right": 0.98,
            "gs_bottom": 0.15,
            "gs_top": 0.9,
        }
        return None

    def get_metadata(self):
        # ------------ call super ----------- #
        dict_meta = super().get_metadata()

        # customize local metadata:
        dict_meta_local = {
            self.field_size: self.size,
            self.field_color: self.color,
            self.field_source: self.source,
            self.field_description: self.description,
            self.field_file_data: self.file_data,
        }
        # update
        dict_meta.update(dict_meta_local)
        return dict_meta

    def update(self):
        """
        Refresh all mutable attributes based on data (including paths).
        """
        # refresh all mutable attributes

        # set fields
        self._set_fields()

        if self.data is not None:
            # data size (rows)
            self.size = len(self.data)

        # update data folder
        if self.file_data is not None:
            # set folder
            self.folder_data = os.path.abspath(os.path.dirname(self.file_data))
        else:
            self.folder_data = None

        # view specs at the end
        self._set_view_specs()

        # ... continues in downstream objects ... #
        return None

    def setter(self, dict_setter, load_data=True):
        super().setter(dict_setter=dict_setter)

        # ---------- settable attributes --------- #
        self.color = dict_setter[self.field_color]
        self.source = dict_setter[self.field_source]
        self.description = dict_setter[self.field_description]

        # option for data loading on setting
        if load_data:
            # handle if only filename is provided
            if os.path.isfile(dict_setter[self.field_file_data]):
                file_data = dict_setter[self.field_file_data][:]
            else:
                # assumes file is in the same folder as the boot-file
                file_data = os.path.join(
                    self.folder_bootfile, dict_setter[self.field_file_data][:]
                )
            self.file_data = os.path.abspath(file_data)

            # -------------- set data logic here -------------- #
            self.load_data(file_data=self.file_data)

        # -------------- update other mutables -------------- #
        self.update()

        # ... continues in downstream objects ... #

    def load_data(self, file_data):
        """
        Load data from file.

        :param file_data: file path to data.
        :type file_data: str
        """

        # -------------- overwrite relative path inputs -------------- #
        self.file_data = os.path.abspath(file_data)

        # -------------- implement loading logic -------------- #
        default_columns = {
            #'DateTime': 'datetime64[1s]',
            "P": float,
            "RM": float,
            "TempDB": float,
        }
        # -------------- call loading function -------------- #
        self.data = pd.read_csv(
            self.file_data,
            sep=self.file_csv_sep,
            dtype=default_columns,
            usecols=list(default_columns.keys()),
        )

        # -------------- post-loading logic -------------- #
        self.data.dropna(inplace=True)

        # -------------- update other mutables -------------- #
        self.update()

        # ... continues in downstream objects ... #

        return None

    def export(self, folder, filename, data_suffix=None):
        """
        Export object resources (e.g., data and metadata).

        :param folder: path to folder
        :type folder: str
        :param filename: file name without extension
        :type filename: str
        :param data_suffix: suffix for file names
        :type data_suffix: Union[str, None]

        """
        super().export(folder, filename=filename + "_bootfile")
        if data_suffix is None:
            data_suffix = ""
        elif "_" not in data_suffix:
            data_suffix = "_" + data_suffix

        fpath = Path(folder + "/" + filename + data_suffix + self.file_csv_ext)
        self.data.to_csv(
            fpath, sep=self.file_csv_sep, encoding=self.file_encoding, index=False
        )
        # ... continues in downstream objects ... #

    def view(self, show=True):
        """
        Get the basic visualization.

        :param show: option for showing instead of saving.
        :type show: bool

        .. note::

            Uses values in the ``view_specs()`` attribute for plotting.

        """
        # get specs
        specs = self.view_specs.copy()

        # --------------------- figure setup --------------------- #
        fig = plt.figure(figsize=(specs["width"], specs["height"]))  # Width, Height

        # --------------------- plotting --------------------- #
        plt.scatter(
            self.data[specs["xvar"]],
            self.data[specs["yvar"]],
            marker=".",
            color=specs["color"],
        )

        # --------------------- post-plotting --------------------- #
        # set basic plotting stuff
        plt.title(specs["title"])
        plt.ylabel(specs["ylabel"])
        plt.xlabel(specs["xlabel"])

        # handle min max
        if specs["xmin"] is None:
            specs["xmin"] = self.data[specs["xvar"]].min()
        if specs["ymin"] is None:
            specs["ymin"] = self.data[specs["yvar"]].min()
        if specs["xmax"] is None:
            specs["xmax"] = self.data[specs["xvar"]].max()
        if specs["ymax"] is None:
            specs["ymax"] = self.data[specs["yvar"]].max()

        plt.xlim(specs["xmin"], specs["xmax"])
        plt.ylim(specs["ymin"], 1.2 * specs["ymax"])

        # Adjust layout to prevent cutoff
        plt.tight_layout()

        # --------------------- end --------------------- #
        # show or save
        if show:
            plt.show()
            return None
        else:
            file_path = "{}/{}.{}".format(
                specs["folder"], specs["filename"], specs["fig_format"]
            )
            plt.savefig(file_path, dpi=specs["dpi"])
            plt.close(fig)
            return file_path

    # todo [refactor] -- consider move to a utils.py module
    @staticmethod
    def dc2df(dc, name="main"):
        # todo [docstring]
        ls_main = list(dc.keys())
        dc_main = {}
        dc_main[name] = ls_main
        ls_fields = list(dc[ls_main[0]].keys())
        for f in ls_fields:
            _ls = []
            for m in ls_main:
                _ls.append(dc[m].get(f, None))
            dc_main[f] = _ls[:]
        return pd.DataFrame(dc_main)


# todo [refactor] -- consider remove from plans lib
class Note(MbaE):
    # todo [docstring]

    def __init__(self, name="MyNote", alias="Nt1"):
        # set attributes
        self.file_note = None
        self.metadata = None
        self.data = None
        super().__init__(name=name, alias=alias)
        # ... continues in downstream objects ... #

    def _set_fields(self):
        """Set fields names"""
        super()._set_fields()
        # Attribute fields
        self.field_file_note = "file_note"

        # Metadata fields

        # ... continues in downstream objects ... #

    def get_metadata(self):
        """Get a dictionary with object metadata.


        .. note::

            Metadata does **not** necessarily inclue all object attributes.

        :return: dictionary with all metadata
        :rtype: dict
        """
        # ------------ call super ----------- #
        dict_meta = super().get_metadata()

        # customize local metadata:
        dict_meta_local = {
            self.field_file_note: self.file_note,
        }
        # update
        dict_meta.update(dict_meta_local)
        return dict_meta

    def load_metadata(self):
        self.metadata = Note.parse_metadata(self.file_note)

    def load_data(self):
        self.data = Note.parse_note(self.file_note)

    def load(self):
        self.load_metadata()
        self.load_data()

    def save(self):
        self.to_file(file_path=self.file_note)

    def to_file(self, file_path, cleanup=True):
        """Export Note to markdown

        :param file_path: path to file
        :type file_path: str
        :return:
        :rtype:
        """
        ls_metadata = Note.metadata_to_list(self.metadata)
        # clear "None" values
        for i in range(len(ls_metadata)):
            ls_metadata[i] = ls_metadata[i].replace("None", "")

        ls_data = Note.data_to_list(self.data)
        # append to metadata list
        for l in ls_data:
            ls_metadata.append(l[:])
        ls_all = [line + "\n" for line in ls_metadata]
        with open(file_path, "w", encoding="utf-8") as file:
            file.writelines(ls_all)

        # clean up excessive lines
        if cleanup:
            Note.remove_excessive_blank_lines(file_path)

    @staticmethod
    def remove_excessive_blank_lines(file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            lines = file.readlines()

        cleaned_lines = []
        previous_line_blank = False

        for line in lines:
            if line.strip() == "":
                if not previous_line_blank:
                    cleaned_lines.append(line)
                    previous_line_blank = True
            else:
                cleaned_lines.append(line)
                previous_line_blank = False

        with open(file_path, "w", encoding="utf-8") as file:
            file.writelines(cleaned_lines)

    @staticmethod
    def parse_metadata(note_file):
        """Extracts YAML metadata from the header of a Markdown file.

        :param note_file: str, path to the Markdown file
        :return: dict, extracted YAML metadata
        """
        with open(note_file, "r", encoding="utf-8") as file:
            content = file.read()

        # Regular expression to match the YAML header
        yaml_header_regex = r"^---\s*\n(.*?)\n---\s*\n"

        # Search for the YAML header in the content
        match = re.search(yaml_header_regex, content, re.DOTALL)

        if match:
            yaml_content = match.group(1)
            return Note.parse_yaml(yaml_content)
        else:
            return None

    @staticmethod
    def parse_yaml(yaml_content):
        """Parses YAML content into a dictionary.

        :param yaml_content: str, YAML content as string
        :return: dict, parsed YAML content
        """
        metadata = {}
        lines = yaml_content.split("\n")
        current_key = None
        current_list = None

        for line in lines:
            if line.strip() == "":
                continue
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()
                if value == "":  # start of a list
                    current_key = key
                    current_list = []
                    metadata[current_key] = current_list
                else:
                    if key == "tags":
                        metadata[key] = [
                            v.strip() for v in value.split("-") if v.strip()
                        ]
                    else:
                        metadata[key] = value
            elif current_list is not None and line.strip().startswith("-"):
                current_list.append(line.strip()[1:].strip())

        # fix empty lists
        for e in metadata:
            if len(metadata[e]) == 0:
                metadata[e] = None

        # fix text fields
        for e in metadata:
            if metadata[e]:
                size = len(metadata[e]) - 1
                if metadata[e][0] == '"' and metadata[e][size] == '"':
                    # slice it
                    metadata[e] = metadata[e][1:size]

        return metadata

    @staticmethod
    def metadata_to_list(metadata_dict):
        ls_metadata = []
        ls_metadata.append("---")
        for e in metadata_dict:
            if isinstance(metadata_dict[e], list):
                ls_metadata.append("{}:".format(e))
                for i in metadata_dict[e]:
                    ls_metadata.append(" - {}".format(i))
            else:
                aux0 = metadata_dict[e]
                if aux0 is None:
                    aux0 = ""
                aux1 = "{}: {}".format(e, aux0)
                ls_metadata.append(aux1)
        ls_metadata.append("---")

        return ls_metadata

    @staticmethod
    def data_to_list(data_dict):
        ls_out = []
        for level in data_dict:
            ls_out = ls_out + data_dict[level][:]
            ls_out.append("")
            ls_out.append("---")
            ls_out.append("")
        return ls_out

    @staticmethod
    def parse_note(file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            lines = file.readlines()

        # Skip YAML header if present
        if lines[0].strip() == "---":
            yaml_end_index = lines.index("---\n", 1) + 1
            lines = lines[yaml_end_index:]

        # Find all separator positions (lines with "---")
        separator_indices = [i for i, line in enumerate(lines) if line.strip() == "---"]

        # Default values for Head, Body, and Tail
        head, body, tail = [], [], []

        if len(separator_indices) == 0:
            # No separators, the whole content is the Body
            body = lines
        elif len(separator_indices) == 1:
            # One separator: Head is before, Body is between, Tail is after
            head = lines[: separator_indices[0]]
            body = lines[separator_indices[0] + 1 :]
        elif len(separator_indices) == 2:
            # Two separators: Head, Body, and Tail
            head = lines[: separator_indices[0]]
            body = lines[separator_indices[0] + 1 : separator_indices[1]]
            tail = lines[separator_indices[1] + 1 :]
        else:
            # More than two separators: Head is before the first, Body is between the first and last, Tail is after the last
            head = lines[: separator_indices[0]]
            body = lines[separator_indices[0] + 1 : separator_indices[-1]]
            tail = lines[separator_indices[-1] + 1 :]

        # Clean up any extra newlines from the content
        head = [line.strip() for line in head]
        body = [line.strip() for line in body]
        tail = [line.strip() for line in tail]

        return {"Head": head, "Body": body, "Tail": tail}

    @staticmethod
    def list_by_pattern(md_dict, patt_type="tag"):
        """Retrieve a list of patterns from the note dictionary.

        :param md_dict: Dictionary containing note sections.
        :type md_dict: dict
        :param patt_type: Type of pattern to search for, either "tag" or "related". Defaults to "tag".
        :type patt_type: str
        :return: List of found patterns or None if no patterns are found.
        :rtype: list or None
        """

        if patt_type == "tag":
            pattern = re.compile(r"#\w+")
        elif patt_type == "related":
            pattern = re.compile(r"\[\[.*?\]\]")
        else:
            pattern = re.compile(r"#\w+")

        patts = []
        # run over all sections
        for s in md_dict:
            content = md_dict[s]["Content"]
            for line in content:
                patts.extend(pattern.findall(line))

        if len(patts) == 0:
            patts = None

        return patts


class RecordTable(DataSet):
    """
    The base class for ``RecordTable``.

    A Record is expected to keep adding stamped records
    in order to keep track of large inventories, catalogs, etc.
    All records are expected to have a unique Id. It is considered to be a relational table.

    **Examples**

    Instantiate ``RecordTable`` Object

    .. code-block:: python

        # Instantiate RecordTable object
        rt = RecordTable(name="RecTable_1", alias="RT1")

    Setup custom columns for the data

    .. code-block:: python

        # Setup custom columns for the data
        rt.columns_data_main = ["Name", "Size"]  # main data
        rt.columns_data_extra = ["Type"]  # extra data
        rt.columns_data_files = ["File_P"]  # file-related
        rt.columns_data = rt.columns_data_main + rt.columns_data_extra + rt.columns_data_files

    Set Object Metadata and Load Data

    .. code-block:: python

        # Set object metadata and load data.
        # Note: this dummy object expects the following columns in data
        rt.set(
            dict_setter={
                "Name": "RecTable_01",
                "Alias": "RT01",
                "Color": "red",
                "Source": "-",
                "Description": "This is RecordTable Object",
                "File_Data": "/content/data_rt1.csv"
            },
            load_data=True
        )


    Check Data

    .. code-block:: python

        # Check data :class:`pandas.DataFrame`
        print(rt.data.head())

    Load More Data from Other File

    .. code-block:: python

        # Load more new data from other file
        rt.load_data(file_data="/content/data_rt2.csv")

    Insert New Record

    .. code-block:: python

        # Insert new record from incoming dict
        d2 = {
            "Name": "k",
            "Size": 177,
            "Type": 'inputs',
            "File_P": "/filee.pdf",
        }
        rt.insert_record(dict_rec=d2)

    Edit Record

    .. code-block:: python

        # Edit record based on ``RecId`` and new dict
        d = {
            "Size": 34,
            "Name": "C"
        }
        rt.edit_record(rec_id="Rec0002", dict_rec=d)

    Archive a Record

    .. code-block:: python

        # Archive a record in the RT, that is ``RecStatus`` = ``Off``
        rt.archive_record(rec_id="Rec0003")

    Get a Record Dict by ID

    .. code-block:: python

        # Get a record dict by id
        d = rt.get_record(rec_id="Rec0001")
        print(d)

    Get a Record DataFrame by ID

    .. code-block:: python

        # Get a record :class:`pandas.DataFrame` by id
        df = rt.get_record_df(rec_id="Rec0001")
        print(df.to_string(index=False))

    Load Record Data from CSV

    .. code-block:: python

        # Load record data from a ``csv`` file to a dict
        d = rt.load_record_data(file_record_data="/content/rec_rt2.csv")
        print(d)

    Export a Record to CSV

    .. code-block:: python

        # Export a record from the table to a ``csv`` file
        f = rt.export_record(
            rec_id="Rec0001",
            folder_export="/content",
            filename="export_rt2"
        )
        print(f)


    """

    def __init__(self, name="MyRecordTable", alias="RcT"):
        """
        Initialize the object.

        :param name: unique object name
        :type name: str
        :param alias: unique object alias. If None, it takes the first and last characters from name
        :type alias: str

        """
        # prior attributes

        # ------------ call super ----------- #
        super().__init__(name=name, alias=alias)
        # overwriters
        self.object_alias = "FS"

        # --------- defaults --------- #
        self.id_size = 4  # for zfill

        # --------- customizations --------- #
        self._set_base_columns()
        self._set_data_columns()
        self._set_operator()

        # UPDATE
        self.update()

    def _set_fields(self):
        # ------------ call super ----------- #
        super()._set_fields()
        # base columns fields
        self.field_recid = "RecId"
        self.field_rectable = "RecTable"
        self.field_rectimestamp = "RecTimestamp"
        self.field_recstatus = "RecStatus"
        # ... continues in downstream objects ... #

    def _set_base_columns(self):
        """
        Set base columns names.

        .. note::

            Base method. See downstream classes for actual implementation.

        """
        self.columns_base = [
            self.field_recid,
            self.field_rectable,
            self.field_rectimestamp,
            self.field_recstatus,
        ]
        # ... continues in downstream objects ... #

    def _set_data_columns(self):
        """
        Set specifics data columns names.

        .. note::

            Base method. See downstream classes for actual implementation.


        """
        # Main data columns
        self.columns_data_main = [
            "Kind",
            "Value",
        ]
        # Extra data columns
        self.columns_data_extra = [
            "Category",
        ]
        # File-related columns
        self.columns_data_files = ["File_NF", "File_Invoice"]
        # concat all lists
        self.columns_data = (
            self.columns_data_main + self.columns_data_extra + self.columns_data_files
        )
        # ... continues in downstream objects ... #

    def _set_operator(self):
        """
        Set the builtin operator for automatic column calculations.

        .. note::

            Base method. See downstream classes for actual implementation.

        """

        # ------------- define sub routines here ------------- #

        def func_file_status():
            return FileSys.check_file_status(files=self.data["File"].values)

        def func_sum():
            return None

        def func_age():
            return RecordTable.running_time(
                start_datetimes=self.data["Date_Birth"], kind="human"
            )

        # ---------------- the operator ---------------- #
        self.operator = {
            "Sum": func_sum,
            "Age": func_age,
            "File_Status": func_file_status,
        }
        # remove here for downstream objects!
        self.operator = None
        return None

    def _get_organized_columns(self):
        """
        Return the organized columns (base + data columns)

        :return: organized columns (base + data columns)
        :rtype: list
        """
        return self.columns_base + self.columns_data

    def _get_timestamp(self):
        """
        Return a string timestamp

        :return: full timestamp text %Y-%m0-%d %H:%M:%S
        :rtype: str
        """
        # compute timestamp
        _now = datetime.datetime.now()
        return str(_now.strftime("%Y-%m0-%d %H:%M:%S"))

    def _last_id_int(self):
        """
        Compute the last ID integer in the record data table.

        :return: last Id integer from the record data table.
        :rtype: int
        """
        if self.data is None:
            return 0
        else:
            df = self.data.sort_values(by=self.field_recid, ascending=True)
            return int(df[self.field_recid].values[-1].replace("Rec", ""))

    def _next_recid(self):
        """
        Get the next record id string based on the existing ids.

        :return: next record id
        :rtype: str
        """
        last_id_int = self._last_id_int()
        next_id = "Rec" + str(last_id_int + 1).zfill(self.id_size)
        return next_id

    def _filter_dict_rec(self, input_dict):
        """
        Filter inputs record dictionary based on the expected table data columns.

        :param input_dict: inputs record dictionary
        :type input_dict: dict
        :return: filtered record dictionary
        :rtype: dict
        """
        # ------ parse expected fields ------- #
        # filter expected columns
        dict_rec_filter = {}
        for k in self.columns_data:
            if k in input_dict:
                dict_rec_filter[k] = input_dict[k]
        return dict_rec_filter

    def update(self):
        super().update()
        # ... continues in downstream objects ... #
        return None

    def save(self):
        if self.file_data is not None:
            # handle filename
            filename = os.path.basename(self.file_data).split(".")[0]
            # handle folder
            self.export(
                folder_export=os.path.dirname(self.file_data), filename=filename
            )
            return 0
        else:
            return 1

    def export(self, folder_export=None, filename=None, filter_archive=False):
        """
        Export the ``RecordTable`` data.

        :param folder_export: folder to export
        :type folder_export: str
        :param filename: file name (name alone, without file extension)
        :type filename: str
        :param filter_archive: option for exporting only records with ``RecStatus`` = ``On``
        :type filter_archive: bool
        :return: file path is export is successfull (1 otherwise)
        :rtype: str or int
        """
        if filename is None:
            filename = self.name
        # append extension
        filename = filename + ".csv"
        if self.data is not None:
            # handle folders
            if folder_export is not None:
                filepath = os.path.join(folder_export, filename)
            else:
                filepath = os.path.join(self.folder_data, filename)
            # handle archived records
            if filter_archive:
                df = self.data.query("RecStatus == 'On'")
            else:
                df = self.data.copy()
            # filter default columns:
            df = df[self._get_organized_columns()]
            df.to_csv(filepath, sep=self.file_csv_sep, index=False)
            return filepath
        else:
            return 1

    def setter(self, dict_setter, load_data=True):
        # ignore color
        dict_setter[self.field_color] = None
        super().setter(dict_setter=dict_setter, load_data=False)

        # ---------- set basic attributes --------- #

        # -------------- set data logic here -------------- #
        if load_data:
            self.load_data(file_data=self.file_data)
            self.refresh_data()

        # -------------- update other mutables -------------- #
        self.update()

        # ... continues in downstream objects ... #

    def refresh_data(self):
        """
        Refresh data method for the object operator.
        Performs spreadsheet-like formulas for columns.

        """
        if self.operator is not None:
            for c in self.operator:
                self.data[c] = self.operator[c]()
        # update object
        self.update()

    def load_data(self, file_data):
        # -------------- overwrite relative path inputs -------------- #
        self.file_data = os.path.abspath(file_data)
        # -------------- implement loading logic -------------- #

        # -------------- call loading function -------------- #
        df = pd.read_csv(self.file_data, sep=self.file_csv_sep)

        # -------------- post-loading logic -------------- #
        self.set_data(input_df=df)

        return None

    def set_data(self, input_df, append=True, inplace=True):
        """
        Set ``RecordTable`` data from incoming :class:`pandas.DataFrame`.


        :param input_df: incoming :class:`pandas.DataFrame`
        :type input_df: :class:`pandas.DataFrame`
        :param append: option for appending the :class:`pandas.DataFrame` to existing data. Default True
        :type append: bool
        :param inplace: option for overwrite data. Else return :class:`pandas.DataFrame`. Default True
        :type inplace: bool

        **Notes**

        It handles if the :class:`pandas.DataFrame` has or not the required RT columns
        Base Method.



        """
        list_input_cols = list(input_df.columns)

        # overwrite RecTable column
        input_df[self.field_rectable] = self.name

        # handle RecId
        if self.field_recid not in list_input_cols:
            # enforce Id based on index
            n_last_id = self._last_id_int()
            n_incr = n_last_id + 1
            input_df[self.field_recid] = [
                "Rec" + str(_ + n_incr).zfill(self.id_size) for _ in input_df.index
            ]
        else:
            # remove incoming duplicates
            input_df.drop_duplicates(subset=self.field_recid, inplace=True)

        # handle timestamp
        if self.field_rectimestamp not in list_input_cols:
            input_df[self.field_rectimestamp] = self._get_timestamp()

        # handle timestamp
        if self.field_recstatus not in list_input_cols:
            input_df[self.field_recstatus] = "On"

        # Add missing columns with default values
        for column in self._get_organized_columns():
            if column not in input_df.columns:
                input_df[column] = ""
        df_merged = input_df[self._get_organized_columns()]

        # concatenate dataframes
        if append:
            if self.data is not None:
                df_merged = pd.concat([self.data, df_merged], ignore_index=True)

        if inplace:
            # pass copy
            self.data = df_merged.copy()
            return None
        else:
            return df_merged

    def insert_record(self, dict_rec):
        """Insert a record in the RT

        :param dict_rec: inputs record dictionary
        :type dict_rec: dict


        """

        # ------ parse expected fields ------- #
        # filter expected columns
        dict_rec_filter = self._filter_dict_rec(input_dict=dict_rec)
        # ------ set default fields ------- #
        # set table field
        dict_rec_filter[self.field_rectable] = self.name
        # create index
        dict_rec_filter[self.field_recid] = self._next_recid()
        # compute timestamp
        dict_rec_filter[self.field_rectimestamp] = self._get_timestamp()
        # set active
        dict_rec_filter[self.field_recstatus] = "On"

        # ------ merge ------- #
        # create single-row :class:`pandas.DataFrame`
        df = pd.DataFrame({k: [dict_rec_filter[k]] for k in dict_rec_filter})
        # concat to data
        self.data = pd.concat([self.data, df]).reset_index(drop=True)

        self.update()
        return None

    def edit_record(self, rec_id, dict_rec, filter_dict=True):
        """Edit RT record

        :param rec_id: record id
        :type rec_id: str
        :param dict_rec: incoming record dictionary
        :type dict_rec: dict
        :param filter_dict: option for filtering incoming record
        :type filter_dict: bool


        """
        # inputs dict rec data
        if filter_dict:
            dict_rec_filter = self._filter_dict_rec(input_dict=dict_rec)
        else:
            dict_rec_filter = dict_rec
        # include timestamp for edit operation
        dict_rec_filter[self.field_rectimestamp] = self._get_timestamp()

        # get data
        df = self.data.copy()
        # set index
        df = df.set_index(self.field_recid)
        # get filter series by rec id
        sr = df.loc[rec_id].copy()

        # update edits
        for k in dict_rec_filter:
            sr[k] = dict_rec_filter[k]

        # set in row
        df.loc[rec_id] = sr
        # restore index
        df.reset_index(inplace=True)
        self.data = df.copy()

        return None

    def archive_record(self, rec_id):
        """Archive a record in the RT, that is ``RecStatus`` = ``Off``

        :param rec_id: record id
        :type rec_id: str


        """
        dict_rec = {self.field_recstatus: "Off"}
        self.edit_record(rec_id=rec_id, dict_rec=dict_rec, filter_dict=False)
        return None

    def get_record(self, rec_id):
        """Get a record dict by id

        :param rec_id: record id
        :type rec_id: str
        :return: record dictionary
        :rtype: dict
        """
        # set index
        df = self.data.set_index(self.field_recid)

        # locate series by index and convert to dict
        dict_rec = {self.field_recid: rec_id}
        dict_rec.update(dict(df.loc[rec_id].copy()))
        return dict_rec

    def get_record_df(self, rec_id):
        """Get a record :class:`pandas.DataFrame` by id

        :param rec_id: record id
        :type rec_id: str
        :return: record dictionary
        :rtype: dict
        """
        # get dict
        dict_rec = self.get_record(rec_id=rec_id)
        # convert in vertical dataframe
        dict_df = {
            "Field": [k for k in dict_rec],
            "Value": [dict_rec[k] for k in dict_rec],
        }
        return pd.DataFrame(dict_df)

    def load_record_data(
        self, file_record_data, input_field="Field", input_value="Value"
    ):
        """Load record data from a ``csv`` file to a dict

        .. note::

            This method **does not insert** the record data to the ``RecordTable``.


        :param file_record_data: file path to ``csv`` file.
        :type file_record_data: str
        :param input_field: Name of ``Field`` column in the file.
        :type input_field:
        :param input_value: Name of ``Value`` column in the file.
        :type input_value:
        :return: record dictionary
        :rtype: dict
        """
        # load record from file
        df = pd.read_csv(
            file_record_data, sep=self.file_csv_sep, usecols=[input_field, input_value]
        )
        # convert into a dict
        dict_rec_raw = {
            df[input_field].values[i]: df[input_value].values[i] for i in range(len(df))
        }

        # filter for expected data columns
        dict_rec = {}
        for c in self.columns_data:
            if c in dict_rec_raw:
                dict_rec[c] = dict_rec_raw[c]

        return dict_rec

    def export_record(self, rec_id, filename=None, folder_export=None):
        """Export a record from the table to a ``csv`` file.

        :param rec_id: record id
        :type rec_id: str
        :param filename: file name (name alone, without file extension)
        :type filename: str
        :param folder_export: folder to export
        :type folder_export: str
        :return: path to exported file
        :rtype: str
        """
        # retrieve :class:`pandas.DataFrame`
        df = self.get_record_df(rec_id=rec_id)
        # handle filename and folder
        if filename is None:
            filename = self.name + "_" + rec_id
        if folder_export is None:
            folder_export = self.folder_data
        filepath = os.path.join(folder_export, filename + ".csv")
        # save
        df.to_csv(filepath, sep=self.file_csv_sep, index=False)
        return filepath

    # ----------------- STATIC METHODS ----------------- #
    @staticmethod
    def timedelta_disagg(timedelta):
        """Util static method for dissaggregation of time delta

        :param timedelta: TimeDelta object from pandas
        :type timedelta: :class:`pandas.TimeDelta`
        :return: dictionary of time delta
        :rtype: dict
        """
        days = timedelta.days
        years, days = divmod(days, 365)
        months, days = divmod(days, 30)
        hours, remainder = divmod(timedelta.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return {
            "Years": years,
            "Months": months,
            "Days": days,
            "Hours": hours,
            "Minutes": minutes,
            "Seconds": seconds,
        }

    @staticmethod
    def timedelta_to_str(timedelta, dct_struct):
        """Util static method for string conversion of timedelta

        :param timedelta: TimeDelta object from pandas
        :type timedelta: :class:`pandas.TimeDelta`
        :param dct_struct: Dictionary of string strucuture. Ex: {'Expected days': 'Days'}
        :type dct_struct: dict
        :return: text of time delta
        :rtype: str
        """
        dct_td = RecordTable.timedelta_disagg(timedelta=timedelta)
        parts = []
        for k in dct_struct:
            parts.append("{}: {}".format(dct_struct[k], dct_td[k]))
        return ", ".join(parts)

    @staticmethod
    def running_time(start_datetimes, kind="raw"):
        """Util static method for computing the runnning time for a list of starting dates

        :param start_datetimes: List of starting dates
        :type start_datetimes: list
        :param kind: mode for output format ('raw', 'human' or 'age')
        :type kind: str
        :return: list of running time
        :rtype: list
        """
        # Convert 'start_datetimes' to datetime format
        start_datetimes = pd.to_datetime(start_datetimes)
        # Calculate the running time as a timedelta
        current_datetime = pd.to_datetime("now")
        running_time = current_datetime - start_datetimes
        # Apply the custom function to create a new column
        if kind == "raw":
            running_time = running_time.tolist()
        elif kind == "human":
            dct_str = {"Years": "yr", "Months": "mth"}
            running_time = running_time.apply(
                RecordTable.timedelta_to_str, args=(dct_str,)
            )
        elif kind == "age":
            running_time = [int(e.days / 365) for e in running_time]

        return running_time


class Budget(RecordTable):

    def __init__(self, name="MyBudget", alias="Bud"):
        super().__init__(name=name, alias=alias)

        # ------------- specifics attributes ------------- #
        self.total_revenue = None
        self.total_expenses = None
        self.total_net = None
        self.summary_ascend = False

    def _set_fields(self):
        """Set fields names."""
        # ------------ call super ----------- #
        super()._set_fields()
        # set temporary util fields
        self.sign_field = "Sign"
        self.value_signed = "Value_Signed"
        # ... continues in downstream objects ... #

    def _set_data_columns(self):
        """Set specifics data columns names.
        Base Dummy Method. Expected to be incremented in superior methods.

        """
        # Main data columns
        self.columns_data_main = [
            "Type",
            "Status",
            "Contract",
            "Name",
            "Value",
        ]
        # Extra data columns
        self.columns_data_extra = [
            # Status extra
            "Date_Due",
            "Date_Exe",
            # Name extra
            # tags
            "Tags",
            # Values extra
            # Payment details
            "Method",
            "Protocol",
        ]
        # File columns
        self.columns_data_files = [
            "File_Receipt",
            "File_Invoice",
            "File_NF",
        ]
        # concat all lists
        self.columns_data = (
            self.columns_data_main + self.columns_data_extra + self.columns_data_files
        )

        # variations
        self.columns_data_status = self.columns_data_main + [
            self.columns_data_extra[0],
            self.columns_data_extra[1],
        ]

        # ... continues in downstream objects ... #

    def _set_operator(self):
        """Private method for Budget operator"""

        # ------------- define sub routines here ------------- #
        def func_file_status():
            return FileSys.check_file_status(files=self.data["File"].values)

        def func_update_status():
            # filter relevante data
            df = self.data[["Status", "Method", "Date_Due"]].copy()
            # Convert 'Date_Due' to datetime format
            df["Date_Due"] = pd.to_datetime(self.data["Date_Due"])
            # Get the current date
            current_dt = datetime.datetime.now()

            # Update 'Status' for records with 'Automatic' method and 'Expected' status based on the condition
            condition = (
                (df["Method"] == "Automatic")
                & (df["Status"] == "Expected")
                & (df["Date_Due"] <= current_dt)
            )
            df.loc[condition, "Status"] = "Executed"

            # return values
            return df["Status"].values

        # todo implement all operations
        # ---------------- the operator ---------------- #

        self.operator = {
            "Status": func_update_status,
        }

    def _get_total_expenses(self, filter=True):
        filtered_df = self._filter_prospected_cancelled() if filter else self.data
        _n = filtered_df[filtered_df["Type"] == "Expense"]["Value_Signed"].sum()
        return round(_n, 3)

    def _get_total_revenue(self, filter=True):
        filtered_df = self._filter_prospected_cancelled() if filter else self.data
        _n = filtered_df[filtered_df["Type"] == "Revenue"]["Value_Signed"].sum()
        return round(_n, 3)

    def _filter_prospected_cancelled(self):
        return self.data[
            (self.data["Status"] != "Prospected") & (self.data["Status"] != "Cancelled")
        ]

    def update(self):
        super().update()
        if self.data is not None:
            self.total_revenue = self._get_total_revenue(filter=True)
            self.total_expenses = self._get_total_expenses(filter=True)
            self.total_net = self.total_revenue + self.total_expenses
            if self.total_net > 0:
                self.summary_ascend = False
            else:
                self.summary_ascend = True

        # ... continues in downstream objects ... #
        return None

    def set_data(self, input_df):
        """Set RecordTable data from incoming :class:`pandas.DataFrame`.
        Expected to be incremented downstream.

        :param input_df: incoming :class:`pandas.DataFrame`
        :type input_df: :class:`pandas.DataFrame`


        """
        super().set_data(input_df=input_df)
        # convert to numeric
        self.data["Value"] = pd.to_numeric(self.data["Value"])
        # compute temporary field

        # sign and value_signed
        self.data["Sign"] = self.data["Type"].apply(
            lambda x: 1 if x == "Revenue" else -1
        )
        self.data["Value_Signed"] = self.data["Sign"] * self.data["Value"]

    @staticmethod
    def parse_annual_budget(self, year, budget_df, freq_field="Freq"):
        start_date = "{}-01-01".format(year)
        end_date = "{}-01-01".format(int(year) + 1)

        annual_budget = pd.DataFrame()

        for _, row in budget_df.iterrows():
            # Generate date range based on frequency
            dates = pd.date_range(start=start_date, end=end_date, freq=row["Freq"])

            # Replicate the row for each date
            replicated_data = pd.DataFrame(
                {col: [row[col]] * len(dates) for col in df.columns}
            )
            replicated_data["Date"] = dates

            # Append to the expanded budget
            annual_budget = pd.concat(
                [annual_budget, replicated_data], ignore_index=True
            )

        return annual_budget

    def get_summary_by_type(self):
        summary = pd.DataFrame(
            {
                "Total_Expenses": [self.total_expenses],
                "Total_Revenue": [self.total_revenue],
                "Total_Net": [self.total_net],
            }
        )
        summary = summary.apply(
            lambda x: x.sort_values(ascending=self.summary_ascend), axis=1
        )
        return summary

    def get_summary_by_status(self, filter=True):
        filtered_df = self._filter_prospected_cancelled() if filter else self.data
        return (
            filtered_df.groupby("Status")["Value_Signed"]
            .sum()
            .sort_values(ascending=self.summary_ascend)
        )

    def get_summary_by_contract(self, filter=True):
        filtered_df = self._filter_prospected_cancelled() if filter else self.data
        return (
            filtered_df.groupby("Contract")["Value_Signed"]
            .sum()
            .sort_values(ascending=self.summary_ascend)
        )

    def get_summary_by_tags(self, filter=True):
        filtered_df = self._filter_prospected_cancelled() if filter else self.data
        tags_summary = (
            filtered_df.groupby("Tags")["Value_Signed"]
            .sum()
            .sort_values(ascending=self.summary_ascend)
        )
        tags_summary = tags_summary.sort()
        separate_tags_summary = (
            filtered_df["Tags"].str.split(expand=True).stack().value_counts()
        )
        print(type(separate_tags_summary))
        return tags_summary, separate_tags_summary


class FileSys(DataSet):
    """
    The core ``FileSys`` base class. Handles files and folder organization,

    **Notes**

    This class is useful for complex folder structure setups and controlling the status
    of expected file.

    .. warning::

        This is a Base and Dummy object. Expected to be implemented downstream for
        custom applications.


    """

    def __init__(self, folder_base, name="MyFS", alias="FS0"):
        """
        Initialize the ``FileSys`` object.

        :param folder_base: path to File System folder location
        :type folder_base: str
        :param name: unique class name
        :type name: str
        :param alias: unique object alias. If None, it takes the first and last characters from name
        :type alias: str

        """
        # prior attributes
        self.folder_base = folder_base

        # ------------ call super ----------- #
        super().__init__(name=name, alias=alias)

        # overwriters
        self.object_alias = "FS"

        # ------------ set mutables ----------- #
        self.folder_main = os.path.join(self.folder_base, self.name)
        self._set_view_specs()

        # ... continues in downstream objects ... #

    def _set_fields(self):
        # ------------ call super ----------- #
        super()._set_fields()

        # Attribute fields
        self.folder_base_field = "Folder_Base"

        # ... continues in downstream objects ... #

    def _set_view_specs(self):
        self.view_specs = {
            "folder": self.folder_data,
            "filename": self.name,
            "fig_format": "jpg",
            "dpi": 300,
            "title": self.name,
            "width": 5 * 1.618,
            "height": 5 * 1.618,
            # todo include more view specs
        }
        return None

    #
    def get_metadata(self):
        # ------------ call super ----------- #
        dict_meta = super().get_metadata()

        # customize local metadata:
        dict_meta_local = {self.folder_base_field: self.folder_base}

        # update
        dict_meta.update(dict_meta_local)

        # removals

        # remove color
        dict_meta.pop(self.field_color)
        # remove source
        dict_meta.pop(self.field_source)

        return dict_meta

    def get_structure(self):
        """
        Get ``FileSys`` structure dictionary.

        :return: structure dictionary
        :rtype: dict
        """
        # get pandas DataFrame
        df = self.data.copy()

        # Initialize the nested dictionary
        dict_structure = {}

        # Iterate over the rows of the DataFrame
        for index, row in df.iterrows():
            current_dict = dict_structure

            # Split the folder path into individual folder names
            folders = row["Folder"].split("/")

            # Iterate over the folders to create the nested structure
            for folder in folders:
                current_dict = current_dict.setdefault(folder, {})

            # If a file is present, add it to the nested structure
            if pd.notna(row["File"]):
                current_dict[row["File"]] = [
                    row["Format"],
                    row["File_Source"] if pd.notna(row["File_Source"]) else "",
                    row["Folder_Source"] if pd.notna(row["Folder_Source"]) else "",
                ]
        return dict_structure

    def get_status(self, folder_name):
        # todo dosctring
        dict_status = {}
        # get full folder path
        folder = self.folder_main + "/" + folder_name
        # filter expected files
        df = self.data.copy()
        df = df.query("Folder == '{}'".format(folder_name))
        df = df.dropna(subset=["File"])
        if len(df) == 0:
            return None
        else:
            dict_status["Folder"] = df.copy()
            dict_status["Files"] = {}
            dict_files = {}
            for i in range(len(df)):
                # get file name
                lcl_file_name = df["File"].values[i]
                dict_files[lcl_file_name] = {}
                # get file format
                lcl_file_format = df["Format"].values[i]
                # get extensions:
                dict_extensions = self.get_extensions()
                #
                list_lcl_extensions = dict_extensions[lcl_file_format]
                # print(list_lcl_extensions)
                for ext in list_lcl_extensions:
                    lcl_path = os.path.join(folder, lcl_file_name + "." + ext)
                    list_files = glob.glob(lcl_path)
                    lst_filenames_found = [os.path.basename(f) for f in list_files]
                    dict_files[lcl_file_name][ext] = lst_filenames_found
            for k in dict_files:
                # Convert each list in the dictionary to a pandas Series and then create a DataFrame
                _df = pd.DataFrame(
                    {key: pd.Series(value) for key, value in dict_files[k].items()}
                )
                if len(_df) == 0:
                    for c in _df.columns:
                        _df[c] = [None]
                _df = _df.fillna("missing")
                dict_status["Files"][k] = _df.copy()

            return dict_status

    def update(self):
        super().update()
        # set main folder
        self.folder_main = os.path.join(self.folder_base, self.name)
        # ... continues in downstream objects ... #

    def setter(self, dict_setter, load_data=True):
        # ignore color
        dict_setter[self.field_color] = None

        # -------------- super -------------- #
        super().setter(dict_setter=dict_setter, load_data=False)

        # ---------- set basic attributes --------- #
        # set base folder
        self.folder_base = dict_setter[self.folder_base_field]

        # -------------- set data logic here -------------- #
        if load_data:
            self.load_data(file_data=self.file_data)

        # -------------- update other mutables -------------- #
        self.update()

        # ... continues in downstream objects ... #

    def load_data(self, file_data):
        """Load data from file.

        :param file_data: file path to data.
        :type file_data: str


        """
        # -------------- overwrite relative path inputs -------------- #
        file_data = os.path.abspath(file_data)

        # -------------- implement loading logic -------------- #

        # -------------- call loading function -------------- #
        self.data = pd.read_csv(file_data, sep=self.file_csv_sep)

        # -------------- post-loading logic -------------- #

        return None

    def setup(self):
        """
        This method sets up all the FileSys structure (default folders and files)

        .. danger::

            This method overwrites all existing default files.

        """
        # update structure
        self.structure = self.get_structure()

        # make main dir
        self.make_dir(str_path=self.folder_main)

        # fill structure
        FileSys.fill(dict_struct=self.structure, folder=self.folder_main)

    def backup(
        self,
        location_dir,
        version_id="v-0-0",
    ):  # todo docstring
        dst_dir = os.path.join(location_dir, self.name + "_" + version_id)
        FileSys.archive_folder(src_dir=self.folder_main, dst_dir=dst_dir)
        return None

    # ----------------- STATIC METHODS ----------------- #
    @staticmethod
    def archive_folder(src_dir, dst_dir):
        """archive to a zip folder

        :param src_dir: source directory
        :type src_dir: str
        :param dst_dir: destination directory
        :type dst_dir: str


        """
        # Create a zip archive from the directory
        shutil.make_archive(dst_dir, "zip", src_dir)
        return None

    @staticmethod
    def get_extensions():
        list_basics = [
            "pdf",
            "docx",
            "xlsx",
            "bib",
            "tex",
            "svg",
            "png",
            "jpg",
            "txt",
            "csv",
            "qml",
            "tif",
            "gpkg",
        ]
        dict_extensions = {e: [e] for e in list_basics}
        dict_aliases = {
            "table": ["csv"],
            "raster": ["asc", "prj", "qml"],
            "qraster": ["asc", "prj", "csv", "qml"],
            "fig": ["jpg"],
            "vfig": ["svg"],
            "receipt": ["pdf", "jpg"],
        }
        dict_extensions.update(dict_aliases)
        return dict_extensions

    @staticmethod
    def check_file_status(files):
        """Static method for file existing checkup

        :param files: iterable with file paths
        :type files: list
        :return: list status ('ok' or 'missing')
        :rtype: list
        """
        list_status = []
        for f in files:
            str_status = "missing"
            if os.path.isfile(f):
                str_status = "ok"
            list_status.append(str_status)
        return list_status

    @staticmethod
    def make_dir(str_path):
        """Util function for making a diretory

        :param str_path: path to dir
        :type str_path: str


        """
        if os.path.isdir(str_path):
            pass
        else:
            os.mkdir(str_path)
        return None

    @staticmethod
    def copy_batch(dst_pattern, src_pattern):
        """Util static method for batch-copying pattern-based files.

        .. note::

            Pattern is expected to be a prefix prior to ``*`` suffix.

        :param dst_pattern: destination path with file pattern. Example: path/to/dst_file_*.csv
        :type dst_pattern: str
        :param src_pattern: source path with file pattern. Example: path/to/src_file_*.csv
        :type src_pattern: str


        """
        # handle destination variables
        dst_basename = os.path.basename(dst_pattern).split(".")[0].replace("*", "")  # k
        dst_folder = os.path.dirname(dst_pattern)  # folder

        # handle sourced variables
        src_extension = os.path.basename(src_pattern).split(".")[1]
        src_prefix = os.path.basename(src_pattern).split(".")[0].replace("*", "")

        # get the list of sourced files
        list_files = glob.glob(src_pattern)
        # copy loop
        if len(list_files) != 0:
            for _f in list_files:
                _full = os.path.basename(_f).split(".")[0]
                _suffix = _full[len(src_prefix) :]
                _dst = os.path.join(
                    dst_folder, dst_basename + _suffix + "." + src_extension
                )
                shutil.copy(_f, _dst)
        return None

    @staticmethod
    def fill(dict_struct, folder, handle_files=True):
        """Recursive function for filling the ``FileSys`` structure

        :param dict_struct: dicitonary of directory structure
        :type dict_struct: dict

        :param folder: path to local folder
        :type folder: str



        """

        def handle_file(dst_name, lst_specs, dst_folder):
            """Sub routine for handling expected files in the FileSys structure.

            :param dst_name: destination filename
            :type dst_name: str
            :param lst_specs: list for expected file specifications
            :type lst_specs: list
            :param dst_folder: destination folder
            :type dst_folder: str


            """
            dict_exts = FileSys.get_extensions()
            lst_exts = dict_exts[lst_specs[0]]
            src_name = lst_specs[1]
            src_dir = lst_specs[2]

            # there is a sourcing directory
            if os.path.isdir(src_dir):
                # extension loop:
                for extension in lst_exts:
                    # source
                    src_file = src_name + "." + extension
                    src_filepath = os.path.join(src_dir, src_file)
                    # destination
                    dst_file = dst_name + "." + extension
                    dst_filepath = os.path.join(dst_folder, dst_file)
                    #
                    # there might be a sourced file
                    if os.path.isfile(src_filepath):
                        shutil.copy(src=src_filepath, dst=dst_filepath)
                    elif "*" in src_name:
                        # is a pattern file
                        FileSys.copy_batch(
                            src_pattern=src_filepath, dst_pattern=dst_filepath
                        )
                    else:
                        pass

            return None

        # structure loop:
        for k in dict_struct:
            # get current folder or file
            _d = folder + "/" + str(k)

            # [case 1] bottom is a folder
            if isinstance(dict_struct[k], dict):
                # make a dir
                FileSys.make_dir(str_path=_d)
                # now move down:
                FileSys.fill(
                    dict_struct=dict_struct[k], folder=_d, handle_files=handle_files
                )

            # bottom is an expected file
            else:
                if handle_files:
                    print("HEY")
                    handle_file(dst_name=k, lst_specs=dict_struct[k], dst_folder=folder)

        return None


# --------- DEPRECATED ---------


class _Note0(MbaE):
    """
    DEPRECATED CLASS
    """

    def __init__(self, name="MyNote", alias="Nt1"):

        # attributes
        self.title = None
        self.tags_head = None
        self.tags_etc = None
        self.related_head = None
        self.related_etc = None
        self.summary = None
        self.timestamp = None

        # file paths
        self.file_note = None
        # note dict
        self.note_dict = None

        super().__init__(name=name, alias=alias)
        # ... continues in downstream objects ... #

    def _set_fields(self):
        """Set fields names"""
        super()._set_fields()
        # Attribute fields
        self.title_field = "title"
        self.tags_head_field = "tags_head"
        self.tags_etc_field = "tags_etc"
        self.related_head_field = "related_head"
        self.related_etc_field = "related_etc"
        self.summary_field = "summary"
        self.timestamp_field = "timestamp"
        self.file_note_field = "file_note"

        # Metadata fields

        # ... continues in downstream objects ... #

    def get_metadata(self):
        """Get a dictionary with object metadata.


        .. note::

            Metadata does **not** necessarily inclue all object attributes.

        :return: dictionary with all metadata
        :rtype: dict
        """
        # ------------ call super ----------- #
        dict_meta = super().get_metadata()

        # customize local metadata:
        dict_meta_local = {
            self.title_field: self.title,
            self.summary_field: self.summary,
            self.timestamp_field: self.timestamp,
            self.tags_head_field: self.tags_head,
            self.tags_etc_field: self.tags_etc,
            self.related_head_field: self.related_head,
            self.related_etc_field: self.related_etc,
            self.file_note_field: self.file_note,
        }
        # update
        dict_meta.update(dict_meta_local)
        return dict_meta

    def load(self):
        self.note_dict = Note.parse_note(file_path=self.file_note)
        self.update()

    def update(self):

        # get first section name
        # Warning: assume it is the first item
        self.title = next(iter(self.note_dict))

        # patterns

        # Create a copy of the original dictionary
        new_dict = self.note_dict.copy()
        # Remove the specified key from the new dictionary
        del new_dict[self.title]

        # head tags
        self.tags_head = Note.list_by_pattern(
            md_dict={self.title: self.note_dict[self.title]}, patt_type="tag"
        )
        # head related:
        self.related_head = Note.list_by_pattern(
            md_dict={self.title: self.note_dict[self.title]}, patt_type="related"
        )
        # etc tags:
        self.tags_etc = Note.list_by_pattern(md_dict=new_dict, patt_type="tag")

        self.related_etc = Note.list_by_pattern(md_dict=new_dict, patt_type="related")

        # summary
        lst_summaries = Note.list_by_intro(
            md_dict={self.title: self.note_dict[self.title]}, intro_type="summary"
        )
        self.summary = lst_summaries[0]

        # datetime
        lst_datetimes = Note.list_by_intro(
            md_dict={self.title: self.note_dict[self.title]}, intro_type="timestamp"
        )
        self.timestamp = lst_datetimes[0]

    @staticmethod
    def list_by_pattern(md_dict, patt_type="tag"):
        """Retrieve a list of patterns from the note dictionary.

        :param md_dict: Dictionary containing note sections.
        :type md_dict: dict
        :param patt_type: Type of pattern to search for, either "tag" or "related". Defaults to "tag".
        :type patt_type: str
        :return: List of found patterns or None if no patterns are found.
        :rtype: list or None
        """

        if patt_type == "tag":
            pattern = re.compile(r"#\w+")
        elif patt_type == "related":
            pattern = re.compile(r"\[\[.*?\]\]")
        else:
            pattern = re.compile(r"#\w+")

        patts = []
        # run over all sections
        for s in md_dict:
            content = md_dict[s]["Content"]
            for line in content:
                patts.extend(pattern.findall(line))

        if len(patts) == 0:
            patts = None

        return patts

    @staticmethod
    def list_by_intro(md_dict, intro_type="summary"):
        """List introduction contents based on the specified type.

        :param md_dict: Dictionary containing note sections.
        :type md_dict: dict
        :param intro_type: Type of introduction to search for, currently supports "summary". Defaults to "summary".
        :type intro_type: str
        :return: List of found introductions or None if no introductions are found.
        :rtype: list or None
        """
        if intro_type == "summary":
            pattern = r"\*\*Summary:\*\*\s*(.*)"
        elif intro_type == "timestamp":
            pattern = r"created in:\s*(.*)"
        # develop more options

        summaries = []
        # run over all sections
        for s in md_dict:
            content = md_dict[s]["Content"]
            for line in content:
                match = re.search(pattern, line)
                if match:
                    summaries.append(match.group(1))
        if len(summaries) == 0:
            summaries = None
        return summaries

    @staticmethod
    def parse_note(file_path):
        """Parse a Markdown file into a dictionary structure.

        :param file_path: Path to the Markdown file.
        :type file_path: str
        :return: Dictionary representing the note structure.
        :rtype: dict
        """

        with open(file_path, "r", encoding="utf-8") as file:
            lines = file.readlines()

        markdown_dict = {}
        current_section = None
        parent_section = None
        section_stack = []

        section_pattern = re.compile(r"^(#+)\s+(.*)")

        for line in lines:
            match = section_pattern.match(line)
            if match:
                level = len(match.group(1))
                section_title = match.group(2).strip()

                if current_section is not None:
                    markdown_dict[current_section]["Content"] = section_content

                while section_stack and section_stack[-1][1] >= level:
                    section_stack.pop()

                parent_section = section_stack[-1][0] if section_stack else None
                current_section = section_title
                section_stack.append((current_section, level))
                markdown_dict[current_section] = {
                    "Parent Section": parent_section,
                    "Content": [],
                }
                section_content = []
            else:
                section_content.append(line.strip())

        if current_section is not None:
            markdown_dict[current_section]["Content"] = section_content

        return markdown_dict

    @staticmethod
    def to_md(md_dict, output_dir, filename):
        """Convert a note dictionary to a Markdown file and save it to the specified directory.

        :param md_dict: Dictionary containing note sections.
        :type md_dict: dict
        :param output_dir: Directory where the output Markdown file will be saved.
        :type output_dir: str
        :param filename: Name of the output Markdown file (without extension).
        :type filename: str


        """

        def write_section(file, section, level=1):
            # Write the section header
            file.write(f"{'#' * level} {section}\n")

            # Write the section content
            for line in md_dict[section]["Content"]:
                file.write(line + "\n")

            # Find and write subsections
            subsections = [
                key for key in md_dict if md_dict[key]["Parent Section"] == section
            ]
            for subsection in subsections:
                # recursive step:
                write_section(file, subsection, level + 1)

        # Find top-level sections (sections with no parent)
        top_sections = [
            key for key in md_dict if md_dict[key]["Parent Section"] is None
        ]

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        output_file = os.path.join(output_dir, f"{filename}.md")

        with open(output_file, "w", encoding="utf-8") as file:
            for section in top_sections:
                write_section(file, section)
        return output_file

    @staticmethod
    def find_and_replace(note_file, old, new, line_n=None):
        # Load the Markdown file
        with open(note_file, "r", encoding="utf-8") as file:
            lines = file.readlines()

        # Find and replace old by new strings
        if line_n is None:
            # Replace in all lines
            lines = [line.replace(old, new) for line in lines]
        else:
            # Replace only in the specified line number
            if 0 <= line_n < len(lines):
                lines[line_n] = lines[line_n].replace(old, new)

        # Overwrite the file
        with open(note_file, "w", encoding="utf-8") as file:
            file.writelines(lines)


class _Note1(MbaE):

    def __init__(self, name="MyNote", alias="Nt1"):
        # set attributes
        self.file_note = None
        self.metadata = None
        self.data = None
        super().__init__(name=name, alias=alias)
        # ... continues in downstream objects ... #

    def _set_fields(self):
        """Set fields names"""
        super()._set_fields()
        # Attribute fields
        self.file_note_field = "file_note"

        # Metadata fields

        # ... continues in downstream objects ... #

    def get_metadata(self):
        """Get a dictionary with object metadata.


        .. note::

            Metadata does **not** necessarily inclue all object attributes.

        :return: dictionary with all metadata
        :rtype: dict
        """
        # ------------ call super ----------- #
        dict_meta = super().get_metadata()

        # customize local metadata:
        dict_meta_local = {
            self.file_note_field: self.file_note,
        }
        # update
        dict_meta.update(dict_meta_local)
        return dict_meta

    def load_metadata(self):
        self.metadata = Note.parse_metadata(self.file_note)

    def load_data(self):
        self.data = Note.parse_note(self.file_note)

    def load(self):
        self.load_metadata()
        self.load_data()

    def save(self):
        self.to_file(file_path=self.file_note)

    def to_file(self, file_path, cleanup=True):
        """Export Note to markdown

        :param file_path: path to file
        :type file_path: str
        :return:
        :rtype:
        """
        ls_metadata = Note.metadata_to_list(self.metadata)
        # clear "None" values
        for i in range(len(ls_metadata)):
            ls_metadata[i] = ls_metadata[i].replace("None", "")

        ls_data = Note.data_to_list(self.data)
        for l in ls_data:
            ls_metadata.append(l[:])
        ls_all = [line + "\n" for line in ls_metadata]
        with open(file_path, "w", encoding="utf-8") as file:
            file.writelines(ls_all)

        # clean up excessive lines
        if cleanup:
            Note.remove_excessive_blank_lines(file_path)

    @staticmethod
    def remove_excessive_blank_lines(file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            lines = file.readlines()

        cleaned_lines = []
        previous_line_blank = False

        for line in lines:
            if line.strip() == "":
                if not previous_line_blank:
                    cleaned_lines.append(line)
                    previous_line_blank = True
            else:
                cleaned_lines.append(line)
                previous_line_blank = False

        with open(file_path, "w", encoding="utf-8") as file:
            file.writelines(cleaned_lines)

    @staticmethod
    def parse_metadata(note_file):
        """Extracts YAML metadata from the header of a Markdown file.

        :param note_file: str, path to the Markdown file
        :return: dict, extracted YAML metadata
        """
        with open(note_file, "r", encoding="utf-8") as file:
            content = file.read()

        # Regular expression to match the YAML header
        yaml_header_regex = r"^---\s*\n(.*?)\n---\s*\n"

        # Search for the YAML header in the content
        match = re.search(yaml_header_regex, content, re.DOTALL)

        if match:
            yaml_content = match.group(1)
            return Note.parse_yaml(yaml_content)
        else:
            return None

    @staticmethod
    def parse_yaml(yaml_content):
        """Parses YAML content into a dictionary.

        :param yaml_content: str, YAML content as string
        :return: dict, parsed YAML content
        """
        metadata = {}
        lines = yaml_content.split("\n")
        current_key = None
        current_list = None

        for line in lines:
            if line.strip() == "":
                continue
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()
                if value == "":  # start of a list
                    current_key = key
                    current_list = []
                    metadata[current_key] = current_list
                else:
                    if key == "tags":
                        metadata[key] = [
                            v.strip() for v in value.split("-") if v.strip()
                        ]
                    else:
                        metadata[key] = value
            elif current_list is not None and line.strip().startswith("-"):
                current_list.append(line.strip()[1:].strip())

        # fix empty lists
        for e in metadata:
            if len(metadata[e]) == 0:
                metadata[e] = None

        # fix text fields
        for e in metadata:
            if metadata[e]:
                size = len(metadata[e]) - 1
                if metadata[e][0] == '"' and metadata[e][size] == '"':
                    # slice it
                    metadata[e] = metadata[e][1:size]

        return metadata

    @staticmethod
    def metadata_to_list(metadata_dict):
        ls_metadata = []
        ls_metadata.append("---")
        for e in metadata_dict:
            if isinstance(metadata_dict[e], list):
                ls_metadata.append("{}:".format(e))
                for i in metadata_dict[e]:
                    ls_metadata.append(" - {}".format(i))
            else:
                aux0 = metadata_dict[e]
                if aux0 is None:
                    aux0 = ""
                aux1 = "{}: {}".format(e, aux0)
                ls_metadata.append(aux1)
        ls_metadata.append("---")

        return ls_metadata

    @staticmethod
    def data_to_list(data_dict):
        ls_out = []
        for h in data_dict:
            level = data_dict[h]["Level"]
            # section header
            ls_out.append("\n{} {}\n".format("#" * level, h))
            # content
            for line in data_dict[h]["Content"]:
                ls_out.append(line)
        return ls_out

    @staticmethod
    def parse_note(file_path):
        """Parse a Markdown file into a dictionary structure, skipping any YAML header.

        :param file_path: Path to the Markdown file.
        :type file_path: str
        :return: Dictionary representing the note structure.
        :rtype: dict
        """
        with open(file_path, "r", encoding="utf-8") as file:
            lines = file.readlines()

        # Skip YAML header if present
        if lines[0].strip() == "---":
            yaml_end_index = lines.index("---\n", 1) + 1
            lines = lines[yaml_end_index:]

        sections = {}
        current_section = None
        parent_section = None

        for line in lines:
            header_match = re.match(r"^(#{1,6})\s+(.*)", line)
            if header_match:
                level = len(header_match.group(1))
                section_name = header_match.group(2).strip()

                # Determine parent section
                parent_section = None
                for section in reversed(sections.keys()):
                    if sections[section]["Level"] < level:
                        parent_section = section
                        break

                sections[section_name] = {
                    "Parent": parent_section,
                    "Content": [],
                    "Level": level,
                }
                current_section = section_name
            elif current_section:
                sections[current_section]["Content"].append(line.strip())

        # Remove the 'Level' key from the final output
        return sections

    @staticmethod
    def list_by_pattern(md_dict, patt_type="tag"):
        """Retrieve a list of patterns from the note dictionary.

        :param md_dict: Dictionary containing note sections.
        :type md_dict: dict
        :param patt_type: Type of pattern to search for, either "tag" or "related". Defaults to "tag".
        :type patt_type: str
        :return: List of found patterns or None if no patterns are found.
        :rtype: list or None
        """

        if patt_type == "tag":
            pattern = re.compile(r"#\w+")
        elif patt_type == "related":
            pattern = re.compile(r"\[\[.*?\]\]")
        else:
            pattern = re.compile(r"#\w+")

        patts = []
        # run over all sections
        for s in md_dict:
            content = md_dict[s]["Content"]
            for line in content:
                patts.extend(pattern.findall(line))

        if len(patts) == 0:
            patts = None

        return patts


if __name__ == "__main__":
    print("hello world!")
