# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
Deprecated location. ``plans.analyst`` moved to ``plans.datasets.analyst``.
"""
import warnings

from plans.datasets.analyst import *  # noqa: F401,F403

warnings.warn(
    "plans.analyst moved to plans.datasets.analyst",
    DeprecationWarning,
    stacklevel=2,
)
