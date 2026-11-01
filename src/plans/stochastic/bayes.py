# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
Bayes Theorem updating on a discrete hypothesis grid.
"""

# IMPORTS
# ***********************************************************************
# import modules from other libs

# External imports
# =======================================================================
import numpy as np

# CONSTANTS
# ***********************************************************************
# define constants in uppercase

__all__ = ["get_likelihood", "get_posterior", "get_accumulated", "get_band"]


# FUNCTIONS
# ***********************************************************************


def get_likelihood(evidence, weights, grid, baseline):
    """
    Get the likelihood on a hypothesis grid from a weighted evidence histogram.

    :param evidence: vector of evidence values
    :type evidence: :class:`numpy.ndarray`
    :param weights: vector of evidence weights
    :type weights: :class:`numpy.ndarray`
    :param grid: hypothesis grid, used as histogram edges
    :type grid: :class:`numpy.ndarray`
    :param baseline: value added to every grid point, so none has zero likelihood
    :type baseline: float
    :return: normalized likelihood, same size as ``grid``
    :rtype: :class:`numpy.ndarray`
    """
    hist, edges = np.histogram(a=evidence, bins=grid, weights=weights)
    hist = hist / np.sum(a=hist)
    # the last grid point closes the histogram and has no bin of its own
    v_like = np.append(arr=hist, values=0) + baseline
    return v_like / np.sum(a=v_like)


def get_posterior(prior, likelihood):
    """
    Get the posterior probability using the Bayes Theorem.

    :param prior: vector of prior probabilities
    :type prior: :class:`numpy.ndarray`
    :param likelihood: vector of likelihoods
    :type likelihood: :class:`numpy.ndarray`
    :return: normalized posterior
    :rtype: :class:`numpy.ndarray`
    """
    return (prior * likelihood) / np.sum(a=prior * likelihood)


def get_accumulated(probabilities):
    """
    Get the accumulated probability along the grid.

    :param probabilities: vector of probabilities
    :type probabilities: :class:`numpy.ndarray`
    :return: accumulated probabilities
    :rtype: :class:`numpy.ndarray`
    """
    return np.cumsum(a=probabilities)


def get_band(grid, accumulated, lower, upper):
    """
    Get the grid range where ``lower < accumulated <= upper``.

    :param grid: hypothesis grid
    :type grid: :class:`numpy.ndarray`
    :param accumulated: vector of accumulated probabilities
    :type accumulated: :class:`numpy.ndarray`
    :param lower: lower accumulated probability
    :type lower: float
    :param upper: upper accumulated probability
    :type upper: float
    :return: lowest and highest grid values, or NaN if no grid point qualifies
    :rtype: tuple
    """
    v = grid[(accumulated > lower) & (accumulated <= upper)]
    if len(v) == 0:
        return np.nan, np.nan
    return np.min(a=v), np.max(a=v)
