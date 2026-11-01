# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
Random sampling and rescaling of samples.
"""

# IMPORTS
# ***********************************************************************
# import modules from other libs

# Native imports
# =======================================================================
import warnings

# External imports
# =======================================================================
import numpy as np

# CONSTANTS
# ***********************************************************************
# define constants in uppercase

__all__ = ["normalize", "sample_gamma"]

GAMMA_SHAPES = {
    "decay": 1,
    "asymmetrical_extra": 2,
    "asymmetrical": 3,
    "symmetrical": 20,
}


# FUNCTIONS
# ***********************************************************************


def normalize(array, min_value=0, max_value=100):
    """
    Normalize array between min and max values

    :param array: Input array or float
    :type array: float or :class:`numpy.ndarray`
    :param min_value: minimum vale
    :type min_value: float
    :param max_value: maximum value
    :type max_value: float
    :return: Output array or float
    :rtype: :class:`numpy.ndarray`
    """
    # Find the minimum and maximum values in the original array
    old_min = np.min(a=array)
    old_max = np.max(a=array)

    # Calculate the range of the original array
    old_range = old_max - old_min
    # Calculate the range of the desired new scale
    new_range = max_value - min_value

    # Apply the normalization formula using NumPy's broadcasting capabilities
    normalized = min_value + ((array - old_min) * new_range) / old_range
    return normalized


def sample_gamma(
    size, shape=3, scale=1, shape_mode=None, n_min=None, n_max=None, rng=None
):
    """
    Draw a gamma sample, then rescale it so its own extremes sit on the bounds.

    The sample minimum becomes ``n_min`` and the sample maximum becomes ``n_max``,
    so the result is a gamma-shaped sample, not a gamma sample with that ``scale``.
    A missing bound defaults to the sample's own extreme. When both bounds are given,
    ``scale`` has no effect because the rescaling cancels it.

    :param size: Sample size
    :type size: int
    :param shape: Shape parameter
    :type shape: float
    :param scale: Scale parameter
    :type scale: float
    :param shape_mode: Shape mode (overwrites shape value). See ``GAMMA_SHAPES``.
    :type shape_mode: str or None
    :param n_min: Normalization lower value
    :type n_min: float or None
    :param n_max: Normalization upper value
    :type n_max: float or None
    :param rng: Random generator. If None, uses the global numpy random state.
    :type rng: :class:`numpy.random.Generator` or None
    :return: Sampled array
    :rtype: :class:`numpy.ndarray`
    """
    # handle shapemode
    if shape_mode is not None:
        if shape_mode not in GAMMA_SHAPES:
            raise ValueError(
                f"Unknown shape_mode '{shape_mode}'. Options: {list(GAMMA_SHAPES)}"
            )
        shape = GAMMA_SHAPES[shape_mode]

    # validate
    if shape <= 0:
        raise ValueError("shape must be greater than zero")
    if scale <= 0:
        raise ValueError("scale must be greater than zero")
    if n_min is not None and n_max is not None:
        if n_min >= n_max:
            raise ValueError("n_min must be lower than n_max")
        if scale != 1:
            warnings.warn("scale has no effect when both n_min and n_max are given")

    # sample
    draw = np.random.gamma if rng is None else rng.gamma
    sample = draw(shape=shape, scale=scale, size=size)

    # a constant sample has no range to rescale
    if np.min(a=sample) == np.max(a=sample):
        raise ValueError("Cannot rescale a sample where all values are equal")

    # handle normalization
    if n_min is None:
        n_min = np.min(a=sample)
    if n_max is None:
        n_max = np.max(a=sample)

    # normalize
    return normalize(array=sample, min_value=n_min, max_value=n_max)
