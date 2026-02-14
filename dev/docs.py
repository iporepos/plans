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

.. dropdown:: Build in silent mode
    :icon: code-square
    :open:

    .. code-block:: bash

        python -m dev.docs

.. dropdown:: Build and open website locally
    :icon: code-square
    :open:

    .. code-block:: bash

        python -m dev.docs --open


"""


# IMPORTS
# ***********************************************************************

# Native imports
# =======================================================================
import subprocess
import webbrowser
import glob, os
from pathlib import Path
import argparse

# External imports
# =======================================================================
# None required

# Project-level imports
# =======================================================================
# None required


# CONSTANTS
# ***********************************************************************

# CONSTANTS -- Project-level
# =======================================================================
DOCS_DIR = Path("docs")
BUILD_DIR = DOCS_DIR / "_build"
INDEX_FILE = BUILD_DIR / "index.html"


# FUNCTIONS
# ***********************************************************************


# FUNCTIONS -- Project-level
# =======================================================================
def build_docs(open_site=False):
    """
    Build Sphinx documentation and open the index.html file.

    This function runs the Sphinx build command with HTML output, then
    opens the generated index.html in the default web browser.
    """
    # Clean generated files
    delete_generated()
    # Run sphinx-build
    subprocess.run(
        ["sphinx-build", "-b", "html", str(DOCS_DIR), str(BUILD_DIR), "--write-all"],
        check=True,
    )

    # Open the generated index.html in the default web browser
    if open_site:
        webbrowser.open(INDEX_FILE.resolve().as_uri())
    print(f"Documentation built successfully! Open {INDEX_FILE}")


# FUNCTIONS -- Module-level
# =======================================================================
def delete_generated():
    """
    Delete all ``rst`` generated files prior to build.
    """
    ls_files = glob.glob("./generated/*.rst")
    if len(ls_files) == 0:
        pass
    else:
        for f in ls_files:
            os.remove(f)
    return None


# CLASSES
# ***********************************************************************
# No classes needed for this module


# SCRIPT
# ***********************************************************************
if __name__ == "__main__":

    # Handle parsing
    # ------------------------------------------------------------------
    parser = argparse.ArgumentParser(description="Build Sphinx HTML documentation.")

    parser.add_argument(
        "--open",
        "-o",
        action="store_true",
        default=False,
        help="Open index.html in the default browser after building.",
    )

    args = parser.parse_args()

    # Call the builder
    # ------------------------------------------------------------------
    build_docs(open_site=args.open)
