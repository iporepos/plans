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
        "tag": "io-raster",
    },
    "time raster": {
        "ext": "tif",
        "template": TEMPLATES_DIR / "file_entry_raster.rst",
        "tag": "io-timeraster",
    },
    "quali raster": {
        "ext": "tif",
        "template": TEMPLATES_DIR / "file_entry_raster.rst",
        "tag": "io-qualiraster",
    },
    "time quali raster": {
        "ext": "tif",
        "template": TEMPLATES_DIR / "file_entry_raster.rst",
        "tag": "io-timequaliraster",
    },
    "table": {
        "ext": "csv",
        "template": TEMPLATES_DIR / "file_entry_table.rst",
        "tag": "io-table",
    },
    "table": {
        "ext": "csv",
        "template": TEMPLATES_DIR / "file_entry_table.rst",
        "tag": "io-table",
    },
    "info table": {
        "ext": "csv",
        "template": TEMPLATES_DIR / "file_entry_infotable.rst",
        "tag": "io-infotable",
    },
    "attribute table": {
        "ext": "csv",
        "template": TEMPLATES_DIR / "file_entry_table.rst",
        "tag": "io-attribute",
    },
    "time series": {
        "ext": "csv",
        "template": TEMPLATES_DIR / "file_entry_table.rst",
        "tag": "io-timeseries",
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


def build_file_index():
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


def filter_files(df, workflow):
    df = df.query("workflow == '{}'".format(workflow)).copy()
    return df


def filter_fields(df, file_name, query="x"):
    df = df.query(f"{file_name} == '{query}'")
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


def add_extensions_table(df):
    # handle extension
    ls_ext = []
    for i in range(len(df)):
        structure = df["structure"].values[i]
        if "raster" in structure:
            ls_ext.append(DC_FILES_STRUCTURES["raster"]["ext"])
        else:
            ls_ext.append(DC_FILES_STRUCTURES["table"]["ext"])
    df["ext"] = ls_ext[:]
    return df


def format_monospaced(df, field):
    ls = []
    for i in range(len(df)):
        aux = df[field].values[i]
        ls.append("``{}``".format(aux))
    df[field] = ls[:]
    return df[field]


def format_math(df, field):
    ls = []
    for i in range(len(df)):
        aux = df[field].values[i]
        ls.append(":math:`{}`".format(aux))
    df[field] = ls[:]
    return df[field]


def format_links(df, field, tags_dc):
    ls = []
    for i in range(len(df)):
        aux = df[field].values[i]
        ls.append(":ref:`{}<{}>`".format(aux.title(), tags_dc[aux]))
    df[field] = ls[:]
    return df[field]


def format_files_table(df):
    # extension
    df = add_extensions_table(df)
    df["file"] = df["name"] + "." + df["ext"]
    # monospaced
    df["file"] = format_monospaced(df, field="file")

    # add links
    links_dc = {}
    for k in DC_FILES_STRUCTURES:
        links_dc[k] = DC_FILES_STRUCTURES[k]["tag"]
    df["structure"] = format_links(df, field="structure", tags_dc=links_dc)

    links_dc = {}
    for i in range(len(df)):
        links_dc[df["title"].values[i]] = "io-{}".format(df["name"].values[i])
    df["title"] = format_links(df, field="title", tags_dc=links_dc)

    # filter columns
    ls_cols = ["file", "title", "structure"]
    df = df[ls_cols].copy()

    # rename
    dc_renames = {
        "title": "Name",
        "name": "File",
    }
    df = df.rename(columns=dc_renames)
    # style
    df.columns = [s.title() for s in list(df.columns)]

    return df


def get_system_table():
    df = parse_fields_df()
    df = df.dropna(subset="system")

    dc_cols = {
        "description": "Name",
        "tex": "Symbol",
        "name": "Field",
        "units": "Units",
        "subsystem": "Hydrology",
        "system": "System",
    }

    df["name"] = format_monospaced(df, field="name")
    df["tex"] = format_math(df, field="tex")

    # print(df)
    dc = {
        "variable": "variables",
        "parameter": "parameters",
        "initial condition": "init",
        "boundary condition": "bounds",
    }
    for k in dc:
        df_q = df.query("category == '{}'".format(k))
        df_q = df_q[list(dc_cols.keys())]
        df_q = df_q.rename(columns=dc_cols)
        df_q.to_csv(DOCS_DATA_DIR / "system_{}.csv".format(dc[k]), sep=";", index=False)

    return None


def get_fields_table(name):
    df = parse_fields_df()
    df = filter_fields(df, file_name=name)
    df.to_csv(DOCS_DATA_DIR / f"fields_{name}.csv", sep=";", index=False)
    return None


def get_hfields_table(name):
    df = parse_fields_df()
    df = filter_fields(df, file_name=name, query="h")
    df.to_csv(DOCS_DATA_DIR / f"h_fields_{name}.csv", sep=";", index=False)
    return None


def get_files_tables():
    df = parse_files_df()
    ls_workflow = list(df["workflow"].unique())
    for w in ls_workflow:
        w2 = w.replace("-", "_")
        w3 = w2.replace(" ", "")
        df_q = filter_files(df, workflow=w)
        df_q = format_files_table(df_q)
        df_q.to_csv(DOCS_DATA_DIR / f"files_{w3}.csv", sep=";", index=False)
    return None


def make_file_entry(spec, verbose=False):

    # get abstract from file
    spec["abstract"] = parse_abstract(name=spec["name"])

    structure = spec["structure"]
    if "raster" not in structure:
        # get fields
        get_fields_table(name=spec["name"])

    if structure == "info table":
        get_hfields_table(name=spec["name"])

    # get extra info
    spec["ext"] = DC_FILES_STRUCTURES[structure]["ext"]
    file_template = DC_FILES_STRUCTURES[structure]["template"]
    tag = DC_FILES_STRUCTURES[structure]["tag"]
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
    # first get updated files tables
    get_system_table()
    get_files_tables()
    # then generate the index
    build_file_index()

    # Build docs using sphinx
    # ===================================================================
    build_docs()
