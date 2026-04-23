# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
{Short module description (1-3 sentences)}
todo docstring


"""
# IMPORTS
# ***********************************************************************
# import modules from other libs

# Native imports
# =======================================================================

# ... {develop}

# External imports
# =======================================================================
import numpy as np

# ... {develop}

# Project-level imports
# =======================================================================
# ... {develop}


# CONSTANTS
# ***********************************************************************
# define constants in uppercase

# CONSTANTS -- Project-level
# =======================================================================
# ... {develop}

# CONSTANTS -- Module-level
# =======================================================================
# ... {develop}


# FUNCTIONS
# ***********************************************************************

# FUNCTIONS -- Project-level
# =======================================================================


def idf_intensity(recurrence, duration, parameters):
    """

    :param recurrence: recurrence time in years
    :type recurrence: float
    :param duration: event duration in minutes
    :type duration: float
    :param parameters: IDF dict of parameters in consistent units
    :type parameters: dict
    :return: IDF duration intensity
    :rtype: float
    """
    k = parameters["k"]
    a = parameters["a"]
    b = parameters["b"]
    c = parameters["c"]

    return (k * np.power(recurrence, a)) / np.power((duration + b), c)


def manning_velocity(R, S, n):
    """
    Calculates flow velocity using the Manning equation.

    :param R: Hydraulic radius [m]
    :type R: float
    :param S: Energy slope [m/m]
    :type S: float
    :param n: Manning roughness coefficient [-]
    :type n: float
    :return: Velocity [m/s]
    :rtype: float
    """
    return (1.0 / n) * (R ** (2.0 / 3.0)) * (S**0.5)


def manning_discharge(A, P, S, n):
    """
    Calculates water discharge using the Manning equation.

    :param A: Cross-sectional area [m^2]
    :type A: float
    :param P: Wetted perimeter [m]
    :type P: float
    :param S: Energy slope [m/m]
    :type S: float
    :param n: Manning roughness coefficient [-]
    :type n: float
    :return: Discharge [m^3/s]
    :rtype: float
    """
    R = A / P
    return (1.0 / n) * A * (R ** (2.0 / 3.0)) * (S**0.5)


def kirpich_tc(L, S):
    """
    Calculates the time of concentration using the Kirpich formula.

    :param L: Maximum flow path length [m]
    :type L: float
    :param S: Watershed slope [m/m]
    :type S: float
    :return: Time of concentration [min]
    :rtype: float
    """
    return 0.0195 * (L**0.77) * (S**-0.385)


def slope_deg_to_ratio(theta_deg):
    """
    Convert slope from degrees to m/m using numpy (vectorized).

    Parameters
    ----------
    theta_deg : float or array-like
        Slope angle in degrees

    Returns
    -------
    float or np.ndarray
        Slope in m/m
    """
    return np.tan(np.deg2rad(theta_deg))


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
