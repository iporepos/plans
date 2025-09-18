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
import shutil

# IMPORTS
# ***********************************************************************

# Native imports
# =======================================================================
import subprocess
import webbrowser
from pathlib import Path
import glob
import os

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

# Folders
DOCS_DIR = Path("docs")
FIGS_DIR = DOCS_DIR / "figs"
DOCS_DATA_DIR = DOCS_DIR / "data"
BUILD_DIR = DOCS_DIR / "_build"
GENERATED_DIR = DOCS_DIR / "generated"
TEMPLATES_DIR = DOCS_DIR / "_templates"

# Files
INDEX_FILE = BUILD_DIR / "index.html"
FIGS_DATA = DOCS_DATA_DIR / "figs.csv"
FIGS_TEMPLATE = TEMPLATES_DIR / "fig.rst"


# FUNCTIONS
# ***********************************************************************


# FUNCTIONS -- Project-level
# =======================================================================
def build_docs():
    """
    Build Sphinx documentation and open the index.html file.

    This function runs the Sphinx build command with HTML output, then
    opens the generated index.html in the default web browser.
    """
    # Clean generated files (in case of local build)
    delete_generated()

    # Run sphinx-build
    subprocess.run(
        ["sphinx-build", "-b", "html", str(DOCS_DIR), str(BUILD_DIR), "--write-all"],
        check=True,
    )

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


# CLASSES
# ***********************************************************************
# No classes needed for this module


# SCRIPT
# ***********************************************************************
if __name__ == "__main__":

    # Build figures from csv file
    # ===================================================================
    build_figs()

    # Build docs using sphinx
    # ===================================================================
    build_docs()
