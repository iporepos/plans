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

 - {feature 1}
 - {feature 2}
 - {feature 3}
 - {etc}

Overview
--------
todo docstring
{Overview description}

Examples
--------
todo docstring
{Examples in rST}

From the terminal, run:

.. code-block:: bash

    python ./tests/unit/test_module.py


"""

# ***********************************************************************
# IMPORTS
# ***********************************************************************
# import modules from other libs

# Native imports
# =======================================================================
# import {module}
import unittest

# ... {develop}

# External imports
# =======================================================================
# import {module}
# ... {develop}

# Project-level imports
# =======================================================================
from tests import conftest
from tests.conftest import testprint
from tests.conftest import add, multiply

# ... {develop}


# ***********************************************************************
# CONSTANTS
# ***********************************************************************
# define constants in uppercase

# CONSTANTS -- Project-level
# =======================================================================
# ... {develop}

# CONSTANTS -- Module-level
# =======================================================================
# ... {develop}


# ***********************************************************************
# FUNCTIONS
# ***********************************************************************

# FUNCTIONS -- Project-level
# =======================================================================
# ... {develop}

# FUNCTIONS -- Module-level
# =======================================================================
# ... {develop}


# ***********************************************************************
# CLASSES
# ***********************************************************************

# CLASSES -- Project-level
# =======================================================================


# Demo example
# -----------------------------------------------------------------------
class TestMyModule(unittest.TestCase):

    # Setup methods
    # -------------------------------------------------------------------

    @classmethod
    def setUpClass(cls):
        """
        Runs once before all tests in this class.
        """
        # ... {develop}
        return None

    def setUp(self):
        """
        Runs before each test method.
        """
        # ... {develop}
        return None

    # Testing methods
    # -------------------------------------------------------------------

    def test_add(self):
        """
        Test the add function
        """
        # testprint("add function")
        self.assertEqual(add(2, 3), 5)
        self.assertEqual(add(-1, 1), 0)

    def test_multiply(self):
        """
        Test the multiply function
        """
        # testprint("multiply function")
        self.assertEqual(multiply(2, 3), 6)
        self.assertEqual(multiply(0, 10), 0)

    # Tear down methods
    # -------------------------------------------------------------------
    def tearDown(self):
        """
        Runs after each test method.
        """
        # ... {develop}
        return None

    @classmethod
    def tearDownClass(cls):
        """
        Runs once after all tests in this class.
        """
        # ... {develop}
        return None


# ... {develop}

# CLASSES -- Module-level
# =======================================================================
# ... {develop}


# ***********************************************************************
# SCRIPT
# ***********************************************************************
# standalone behaviour as a script
if __name__ == "__main__":

    # Call all tests in the module
    # ===================================================================
    unittest.main()

    # ... {develop}
