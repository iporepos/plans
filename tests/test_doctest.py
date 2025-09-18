# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
Standard script for loading all doctests from /src modules in the unittest suite
"""
# IMPORTS
# ***********************************************************************
# import modules from other libs

# Native imports
# =======================================================================
import doctest
import unittest
import pathlib
import importlib.util
import sys


# CONSTANTS
# ***********************************************************************
# define constants in uppercase

# CONSTANTS -- Project-level
# =======================================================================
# ... {develop}

# CONSTANTS -- Module-level
# =======================================================================
SRC_DIR = pathlib.Path(__file__).resolve().parents[1] / "src"
EXCLUDED_FILES = {"qutils.py", "qgdal.py"}


# FUNCTIONS
# ***********************************************************************

# FUNCTIONS -- Project-level
# =======================================================================
# ... {develop}


# FUNCTIONS -- Module-level
# =======================================================================
def load_tests(loader, tests, pattern):
    suite = unittest.TestSuite()

    # Find all Python source files under src/
    for path in SRC_DIR.rglob("*.py"):
        if path.name in EXCLUDED_FILES or path.name == "__init__.py":
            continue

        # Turn file path into module name
        rel_path = path.relative_to(SRC_DIR)
        module_name = ".".join(rel_path.with_suffix("").parts)

        # Import the module
        spec = importlib.util.spec_from_file_location(module_name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        # Add doctests from that module
        suite.addTests(doctest.DocTestSuite(module))

    return suite


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
