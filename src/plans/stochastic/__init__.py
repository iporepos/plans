# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
Pure statistical functions on plain arrays.

Modules here depend only on external numerical libraries and on each other.
They never import ``plans.datasets``, ``plans.root``, ``plans.viewer`` or
``plans.geo``, so the dependency between objects and computations stays one-way.
"""
# EXPOSE MODULES FROM PACKAGE
# ***********************************************************************
from .metrics import *
from .binning import *
from .bayes import *
from .curves import *
from .descriptive import *
from .frequency import *
from .normality import *
from .sampling import *
from .arma import *
