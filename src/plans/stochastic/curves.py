# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
Parametric curves and least-squares curve fitting.
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

__all__ = ["linear", "power", "power_zero", "fit_curve"]


# FUNCTIONS
# ***********************************************************************


def linear(x, c0, c1):
    """Linear function f(x) = c0 + c1 * x

    :param x: function inputs
    :type x: float | :class:`numpy.ndarray`
    :param c0: translational parameter
    :type c0: float
    :param c1: scaling parameter
    :type c1: float
    :return: function output
    :rtype: float | :class:`numpy.ndarray`
    """
    return c0 + (x * c1)


def power(x, c0, c1, c2):
    """Power function f(x) =  c2 * ((x + c0)^c1)

    :param x: function inputs
    :type x: float | :class:`numpy.ndarray`
    :param c0: translational parameter
    :type c0: float
    :param c1: exponent parameter
    :type c1: float
    :param c2: scaling parameter
    :type c2: float
    :return: function output
    :rtype: float | :class:`numpy.ndarray`
    """
    return c2 * (np.power((x + c0), c1))


def power_zero(x, c0, c1):
    """Power function with root in zero f(x) =  c1 * ((x)^c0)

    :param x: function inputs
    :type x: float | :class:`numpy.ndarray`
    :param c0: exponent parameter
    :type c0: float
    :param c1: scaling parameter
    :type c1: float
    :return: function output
    :rtype: float | :class:`numpy.ndarray`
    """
    return c1 * (np.power((x), c0))


def fit_curve(func, x, y, p0):
    """
    Fit a curve to paired data using least squares.

    :param func: curve function, taking ``x`` followed by its parameters
    :type func: callable
    :param x: vector of x values
    :type x: :class:`numpy.ndarray`
    :param y: vector of y values
    :type y: :class:`numpy.ndarray`
    :param p0: initial guess of parameters
    :type p0: :class:`numpy.ndarray`
    :return: fitted parameters and their standard deviations
    :rtype: tuple
    """
    from scipy.optimize import curve_fit

    popt, pcov = curve_fit(f=func, xdata=x, ydata=y, p0=p0)
    pstd = np.sqrt(np.diag(v=pcov))
    return popt, pstd
