# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
Hydrological modelling subpackage with core, upscaled, and downscaled model classes.
"""
# EXPOSE MODULES FROM PACKAGE
# ***********************************************************************
from .upscaled import UpscaledModel  # this works
from .downscaled import DownscaledModel  # but this does not
