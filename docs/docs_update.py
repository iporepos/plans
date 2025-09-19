# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
Sphinx Documentation Builder
----------------------------

A simple Python module to build Sphinx documentation and automatically
open the index.html in a web browser.

Features
--------
* Run Sphinx build command
* Automatically open index.html in default web browser
* Cross-platform support

Overview
--------
This module allows developers to quickly generate HTML documentation from
their Sphinx `.rst` or `.md` files and view the result without manually
navigating to the build folder.

Examples
--------
Build docs and open index.html:


.. code-block:: python

    from sphinx_builder import build_docs

    build_docs()


"""
import pprint
import shutil

# IMPORTS
# ***********************************************************************

# Native imports
# =======================================================================
import glob
import os
import re
import subprocess
import webbrowser
from pathlib import Path


# External imports
# =======================================================================
import pandas as pd

# Project-level imports
# =======================================================================
# None required


# CONSTANTS
# ***********************************************************************

# CONSTANTS -- Project-level
# =======================================================================

# Docs
# -----------------------------------------------------------------------
# Folders
DOCS_DIR = Path("docs")
FIGS_DIR = DOCS_DIR / "figs"
DOCS_DATA_DIR = DOCS_DIR / "data"
BUILD_DIR = DOCS_DIR / "_build"
GENERATED_DIR = DOCS_DIR / "generated"
TEMPLATES_DIR = DOCS_DIR / "_templates"
INCLUDES_DIR = DOCS_DIR / "includes"
AUX_DIR = DOCS_DIR / "_aux"

# Files
INDEX_FILE = BUILD_DIR / "index.html"
FIGS_DATA = DOCS_DATA_DIR / "figs.csv"
FIGS_TEMPLATE = TEMPLATES_DIR / "fig.rst"
IPSUM_FILE = INCLUDES_DIR / "ipsum.rst"
LIST_FILE = INCLUDES_DIR / "files_list.rst"

# Src
# -----------------------------------------------------------------------
# Folders
SRC_DIR = Path("src/plans/")
DATA_DIR = SRC_DIR / "data"
# Files
SRC_DATA_FILES = DATA_DIR / "files.csv"
SRC_DATA_FIELDS = DATA_DIR / "fields.csv"

DC_FILES_STRUCTURES = {
    "raster": {
        "ext": "tif",
        "template": TEMPLATES_DIR / "file_entry_raster.rst",
        "raster": "io-raster",
        "time raster": "io-timeseries",
        "quali raster": "io-qualiraster",
        "time quali raster": "io-timequaliraster",
    },
    "table": {
        "ext": "csv",
        "template": TEMPLATES_DIR / "file_entry_table.rst",
        "table": "io-table",
        "time series": "io-timeseries",
        "attribute table": "io-attribute",
    },
}


# FUNCTIONS
# ***********************************************************************


# FUNCTIONS -- Project-level
# =======================================================================
def build_docs(open_docs=False):
    """
    Build Sphinx documentation and open the index.html file.

    This function runs the Sphinx build command with HTML output, then
    opens the generated index.html in the default web browser.
    """
    # Clean generated files (in case of local build)
    delete_generated()

    # Run sphinx-build
    subprocess.run(
        [
            "sphinx-build",
            "-b",
            "html",
            "-v",
            str(DOCS_DIR),
            str(BUILD_DIR),
            "--write-all",
        ],
        check=True,
    )
    if open_docs:
        # Open the generated index.html in the default web browser
        webbrowser.open(INDEX_FILE.resolve().as_uri())
        # print(f"Documentation built successfully! Opened {INDEX_FILE}")
    return None


def build_figs():
    """
    Build figure ``rst`` files from template and ``csv`` listed urls.
    After building, this function adds files to git vsc
    """
    df = parse_figs_df()
    # Iterate over rows as dictionaries
    for row_dc in df.to_dict(orient="records"):
        make_fig(spec=row_dc)
    # add created files to git vcs
    subprocess.run(["git", "add", FIGS_DIR])
    return None


def build_catalog():
    # clean up
    delete_file_entries()
    delete_field_tables()

    df = parse_files_df()
    # Iterate over rows as dictionaries
    for row_dc in df.to_dict(orient="records"):
        make_file_entry(spec=row_dc)

    # merge all entries
    merge_file_entries()

    # add created files to git vcs
    subprocess.run(["git", "add", LIST_FILE])
    subprocess.run(["git", "add", DOCS_DATA_DIR])

    # clean up aux
    delete_file_entries()

    return None


# FUNCTIONS -- Module-level
# =======================================================================
def delete_generated():
    ls_files = glob.glob(str(GENERATED_DIR / "*.rst"))
    if len(ls_files) == 0:
        pass
    else:
        for f in ls_files:
            print(f"deleted {f}")
            os.remove(f)
    return None


# Figs
# -----------------------------------------------------------------------


def parse_figs_df():
    df = pd.read_csv(FIGS_DATA, sep=";")
    df["caption"] = df["caption"].fillna("")
    return df


def make_fig(spec):
    label = spec["label"]
    file_fig = FIGS_DIR / f"{label}.rst"

    # Read the template
    text = FIGS_TEMPLATE.read_text(encoding="utf-8")

    # Remove caption placeholder + leading spaces if empty
    if not spec.get("caption"):
        # keep template clean by removing the last blank line + {caption}
        text = text.replace("\n   {caption}", "")
    # handle if caption is the same as alt
    elif spec["caption"] == "alt":
        spec["caption"] = spec["alt"]

    # Replace placeholders with values from the dict
    filled = text.format_map(spec)
    # Save to a new file
    file_fig.write_text(filled, encoding="utf-8")
    return None


# Files
# -----------------------------------------------------------------------


def parse_ipsum():
    text = IPSUM_FILE.read_text(encoding="utf-8")
    # print(type(text))
    return text


def parse_files_df():
    df = pd.read_csv(SRC_DATA_FILES, sep=";")
    df = df.dropna(subset="name")
    df = df.sort_values(by="name")
    return df


def parse_fields_df():
    df = pd.read_csv(SRC_DATA_FIELDS, sep=";")
    df = df.dropna(subset="name")
    return df


def filter_fields(df, file_name):
    df = df.dropna(subset=file_name)
    dc_cols = {
        "name": "Name",
        "units": "Units",
        "dtype": "Data Type",
        "description": "Description",
    }
    df = df[list(dc_cols.keys())]
    df = df.rename(columns=dc_cols)
    df["Data Type"] = "``" + df["Data Type"] + "``"
    return df


def get_fields_table(name):
    df = parse_fields_df()
    df = filter_fields(df, file_name=name)
    df.to_csv(DOCS_DATA_DIR / f"fields_{name}.csv", sep=";", index=False)
    return None


def make_file_entry(spec, verbose=False):

    # get abstract from file
    spec["abstract"] = parse_abstract(name=spec["name"])

    structure = spec["structure"]
    if structure in list(DC_FILES_STRUCTURES["raster"].keys()):
        structure_primitive = "raster"
    else:
        structure_primitive = "table"
        # get fields
        get_fields_table(name=spec["name"])

    # get extra info
    spec["ext"] = DC_FILES_STRUCTURES[structure_primitive]["ext"]
    file_template = DC_FILES_STRUCTURES[structure_primitive]["template"]
    tag = DC_FILES_STRUCTURES[structure_primitive][structure]
    # structure link
    spec["structure link"] = ":ref:`{}<{}>`".format(structure.title(), tag)

    if verbose:
        print(spec["name"])
        pprint.pprint(spec)
        print("\n")

    spec["folder"] = "``{}``".format(spec["folder"])
    spec["dtype"] = "``{}``".format(spec["dtype"])
    spec["preview"] = "{>> todo preview}"

    # Read the template
    text = file_template.read_text(encoding="utf-8")
    # Replace placeholders with values from the dict
    filled = text.format_map(spec)

    # Save to a new file
    file_entry = AUX_DIR / "{}.rst".format(spec["name"])
    file_entry.write_text(filled, encoding="utf-8")

    return None


def merge_file_entries():
    folder = AUX_DIR
    rst_files = list(folder.glob("*.rst"))
    output_file = LIST_FILE

    # todo [develop] -- implement sorting

    with open(output_file, "w", encoding="utf-8") as out:
        for i, file in enumerate(rst_files):
            text = file.read_text(encoding="utf-8").strip()
            out.write(text)
            # Add spacing between files
            if i < len(rst_files) - 1:
                out.write("\n\n\n")


def parse_abstract(name):

    rst_path = INCLUDES_DIR / "files_abstracts.rst"
    text = Path(rst_path).read_text(encoding="utf-8")

    # Match heading + underline/overline styles
    pattern = rf"(?m)^(?P<title>{re.escape(name)})\n(?P<underline>[-=~`^\"'#*+]+)\n"
    match = re.search(pattern, text)
    if not match:
        return parse_ipsum()

    start = match.end()  # start of content after the heading
    # Find the next heading (any title followed by underline of same length)
    underline_len = len(match.group("underline"))
    next_heading_pattern = rf"(?m)^\S.*\n[-=~`^\"'#*+]{{{underline_len},}}\n"
    next_match = re.search(next_heading_pattern, text[start:])

    if next_match:
        end = start + next_match.start()
    else:
        end = len(text)

    return text[start:end].strip()


def delete_file_entries():
    ls_files = os.listdir(AUX_DIR)
    for f in ls_files:
        os.remove(AUX_DIR / f)


def delete_field_tables():
    ls_files = glob.glob(str(DOCS_DATA_DIR / "fields_*.csv"))
    for f in ls_files:
        os.remove(f)


# CLASSES
# ***********************************************************************
# No classes needed for this module


# SCRIPT
# ***********************************************************************
if __name__ == "__main__":

    # Build figures from csv file
    # ===================================================================
    build_figs()

    # Build catalog
    # ===================================================================
    build_catalog()

    # Build docs using sphinx
    # ===================================================================
    build_docs()
