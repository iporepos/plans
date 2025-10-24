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

* {feature 1}
* {feature 2}
* {feature 3}
* {etc}

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
import argparse

# ... {develop}

# External imports
# =======================================================================
import pandas as pd

# ... {develop}

# Project-level imports
# =======================================================================
from .core import Tool, ToolParser

# ... {develop}


# CLASSES
# ***********************************************************************

# CLASSES -- Module-level
# =======================================================================


class LocalParser(ToolParser):

    def __init__(self, parser):
        super().__init__(parser)
        # add extra arguments
        self.add_input1()
        self.add_input2()

    def add_input1(self):
        self.parser.add_argument(
            "--input1", "-i1", required=True, default=None, action=None, help="File 1"
        )

    def add_input2(self):
        self.parser.add_argument(
            "--input2", "-i2", required=True, default=None, action=None, help="File 2"
        )


class LocalTool(Tool):

    def __init__(self, folder_output):

        name = "plans.tools.demo"

        super().__init__(name=name, folder_output=folder_output)

        # overwrite base attributes
        self.sleeper = 0.5

        # setup new attributes
        self.file_input1 = None
        self.file_input2 = None

    def load_data(self):
        self.loaded_data = dict()
        self.loaded_data["df1"] = pd.read_csv(self.file_input1)
        self.loaded_data["df2"] = pd.read_csv(self.file_input2)
        self.sleep()
        return None

    def process_data(self):
        self.processed_data = pd.concat(
            [self.loaded_data["df1"], self.loaded_data["df2"]]
        )
        self.sleep()
        return None

    def export_data(self):
        file_out = self.folder_output / "demo_output.csv"
        self.processed_data.to_csv(file_out, sep=";", index=False)
        self.sleep()
        return None


# ... {develop}


# FUNCTIONS
# ***********************************************************************


def main():

    # parse arguments from cli
    # -------------------------------------------------------------------
    parser = argparse.ArgumentParser()
    p = LocalParser(parser)
    dc_args = p.get_args_as_dict()

    # instantiate tool
    # -------------------------------------------------------------------
    d = LocalTool(folder_output=dc_args["output"])

    # pass parameters
    # -------------------------------------------------------------------
    d.file_input1 = dc_args["input1"]
    d.file_input2 = dc_args["input2"]

    d.verbose = dc_args["verbose"]
    d.label = dc_args["label"]
    d.name_project = dc_args["project"]

    # run tool
    # -------------------------------------------------------------------
    d.run()

    return None


# ... {develop}

# SCRIPT
# ***********************************************************************
# standalone behaviour as a script
if __name__ == "__main__":

    # Call main
    # -------------------------------------------------------------------
    main()
