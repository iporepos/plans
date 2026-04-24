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
import pandas as pd

# ... {develop}

# Project-level imports
# =======================================================================
from plans.hydrology.core import *

# ... {develop}


# CONSTANTS
# ***********************************************************************
# define constants in uppercase

# ---------------------------------------------------------------------
# NRCS (SCS) dimensionless cumulative distributions (24-hour storm)
# Values = cumulative fraction of total precipitation
# ---------------------------------------------------------------------
SCS_DISTRIBUTIONS = {
    "I": np.array(
        [
            0.000,
            0.017,
            0.035,
            0.054,
            0.076,
            0.100,
            0.125,
            0.156,
            0.194,
            0.254,
            0.515,
            0.623,
            0.684,
            0.732,
            0.770,
            0.802,
            0.832,
            0.860,
            0.886,
            0.910,
            0.932,
            0.952,
            0.970,
            0.986,
            1.000,
        ]
    ),
    "IA": np.array(
        [
            0.000,
            0.020,
            0.050,
            0.082,
            0.116,
            0.156,
            0.206,
            0.268,
            0.425,
            0.520,
            0.577,
            0.624,
            0.664,
            0.701,
            0.736,
            0.769,
            0.801,
            0.831,
            0.859,
            0.887,
            0.913,
            0.937,
            0.959,
            0.980,
            1.000,
        ]
    ),
    "II": np.array(
        [
            0.000,
            0.011,
            0.022,
            0.035,
            0.048,
            0.063,
            0.080,
            0.099,
            0.120,
            0.147,
            0.181,
            0.235,
            0.663,
            0.772,
            0.820,
            0.854,
            0.880,
            0.902,
            0.921,
            0.938,
            0.952,
            0.965,
            0.977,
            0.989,
            1.000,
        ]
    ),
    "III": np.array(
        [
            0.000,
            0.010,
            0.020,
            0.031,
            0.043,
            0.057,
            0.072,
            0.091,
            0.114,
            0.146,
            0.189,
            0.250,
            0.500,
            0.750,
            0.811,
            0.854,
            0.886,
            0.910,
            0.920,
            0.943,
            0.957,
            0.969,
            0.981,
            0.991,
            1.000,
        ]
    ),
}

# Corresponding time vector (hours)
SCS_TIME_HOURS = np.arange(0, 25, 1)

# =============================================================================
# CONSTANT: SCS DIMENSIONLESS UNIT HYDROGRAPH
# =============================================================================

SCS_T_TP = np.array(
    [
        0.0,
        0.1,
        0.2,
        0.3,
        0.4,
        0.5,
        0.6,
        0.7,
        0.8,
        0.9,
        1.0,
        1.1,
        1.2,
        1.3,
        1.4,
        1.5,
        1.6,
        1.7,
        1.8,
        1.9,
        2.0,
        2.2,
        2.4,
        2.6,
        2.8,
        3.0,
        3.2,
        3.4,
        3.6,
        3.8,
        4.0,
        4.5,
        5.0,
    ]
)

SCS_Q_QP = np.array(
    [
        0.000,
        0.030,
        0.100,
        0.190,
        0.310,
        0.470,
        0.660,
        0.820,
        0.930,
        0.990,
        1.000,
        0.990,
        0.930,
        0.860,
        0.780,
        0.680,
        0.560,
        0.460,
        0.390,
        0.330,
        0.280,
        0.207,
        0.147,
        0.107,
        0.077,
        0.055,
        0.040,
        0.029,
        0.021,
        0.015,
        0.011,
        0.005,
        0.000,
    ]
)

# FUNCTIONS
# ***********************************************************************

# FUNCTIONS -- Project-level
# =======================================================================


def uh_scs(dt: float, tc: float, duration: float | None = None) -> np.ndarray:
    """
    Generate an SCS synthetic unit hydrograph at a given time resolution.

    The hydrograph is derived from the dimensionless SCS curve:

    .. math::

        \\frac{Q(t)}{Q_p} = f\\left(\\frac{t}{t_p}\\right)

    with time to peak:

    .. math::

        t_p = 0.6 t_c + \\frac{D}{2}

    The resulting hydrograph is normalized such that:

    .. math::

        \\sum UH = 1

    :param dt: Time step in seconds.
    :type dt: float
    :param tc: Time of concentration in seconds.
    :type tc: float
    :param duration: Effective rainfall duration. Defaults to ``dt``.
    :type duration: float, optional

    :return: Unit hydrograph ordinates (sum = 1).
    :rtype: numpy.ndarray

    .. note::
        - Linear interpolation is used to resample the dimensionless curve.
        - No peak scaling is required due to normalization.
    """

    if duration is None:
        duration = dt

    tp = 0.6 * tc + duration / 2.0

    t_dim = SCS_T_TP * tp

    t = np.arange(0, t_dim.max() + dt, dt)

    q_interp = np.interp(t, t_dim, SCS_Q_QP)

    uh = q_interp / np.sum(q_interp)

    return uh


def propagate_scs(
    df: pd.DataFrame,
    tc: float,
    runoff_field: str = "r",
    datetime_field: str = "datetime",
    output_field: str = "q",
) -> pd.DataFrame:
    """
    Route a runoff time series using the SCS unit hydrograph,
    returning an extended hydrograph including the recession limb.

    The routed discharge is computed via full convolution:

    .. math::

        Q(t) = P_e(t) * UH(t)

    The unit hydrograph is constructed using the dataframe time step.

    :param df: Input dataframe with time series.
    :type df: pandas.DataFrame
    :param tc: Time of concentration in seconds.
    :type tc: float
    :param runoff_field: Column name for runoff input.
    :type runoff_field: str
    :param datetime_field: Column name for timestamps.
    :type datetime_field: str

    :return: Extended dataframe including routed hydrograph.
    :rtype: pandas.DataFrame

    :raises ValueError: If columns are missing or timestep is inconsistent.

    .. note::
        - Time step is inferred from the dataframe and used consistently.
        - Output includes full recession limb (mass-conserving).
    """

    if runoff_field not in df.columns:
        raise ValueError(f"Column '{runoff_field}' not found.")

    if datetime_field not in df.columns:
        raise ValueError(f"Column '{datetime_field}' not found.")

    # Ensure datetime
    time = pd.to_datetime(df[datetime_field])

    if len(time) < 2:
        raise ValueError("At least two timesteps are required.")

    # Infer timestep
    dt_timedelta = time.diff().iloc[1]

    if dt_timedelta <= pd.Timedelta(0):
        raise ValueError("Invalid or non-uniform timestep.")

    # Check uniformity
    if not (time.diff().dropna() == dt_timedelta).all():
        raise ValueError("Non-uniform timestep detected.")

    # Convert dt to numeric (seconds)
    dt = dt_timedelta.total_seconds()

    # Build UH using consistent dt
    uh = uh_scs(dt=dt, tc=tc)

    # Convolution (full)
    runoff = df[runoff_field].values
    routed = uh_convolution(runoff, uh)

    # Extend time index
    extra_steps = len(uh) - 1
    total_len = len(runoff) + extra_steps

    extended_time = pd.date_range(
        start=time.iloc[0], periods=total_len, freq=dt_timedelta
    )

    # Extend runoff with zeros
    runoff_extended = np.zeros(total_len)
    runoff_extended[: len(runoff)] = runoff

    # Output dataframe
    out = pd.DataFrame(
        {
            datetime_field: extended_time,
            runoff_field: runoff_extended,
            output_field: routed,
        }
    )

    return out


def hyetograph_scs(P, storm_type, start="2020-01-01 00:00:00", factor=1):
    """
    Generate a discrete rainfall time series (Hyetograph) using SCS dimensionless distributions.

    :param P: Total storm precipitation [mm]
    :type P: float
    :param storm_type: Storm distribution type. One of: "I", "IA", "II", "III"
    :type storm_type: str
    :param start: Start datetime of the storm (string or pandas.Timestamp). Defaults to "2000-01-01 00:00:00"
    :type start: str or pandas.Timestamp
    :param factor: Length multiplier of the time window (1=24h, 2=48h, 3=72h, ...)
    :type factor: int
    :returns: DataFrame with columns:
              - datetime: datetime series starting at ``start``
              - time: time since start [hr]
              - p: incremental precipitation [mm]
              - p_acc: cumulative precipitation [mm]
    :rtype: `pandas.DataFrame`
    """

    storm_type = storm_type.upper()
    if storm_type not in SCS_DISTRIBUTIONS:
        raise ValueError(
            f"Invalid storm_type '{storm_type}'. Use one of {list(SCS_DISTRIBUTIONS.keys())}"
        )

    if factor < 1 or not isinstance(factor, int):
        raise ValueError("factor must be an integer >= 1")

    # --- cumulative (25 points: 0–24) ---
    f = SCS_DISTRIBUTIONS[storm_type]
    p_acc_full = f * P

    # --- convert to 24 hourly increments ---
    # p[i] = rain during interval [i, i+1)
    p_24 = np.diff(p_acc_full)  # length = 24

    # --- total simulation length ---
    total_hours = 24 * factor
    time = np.arange(1, total_hours + 1)

    # --- embed storm at t=0 ---
    p = np.zeros(total_hours)
    p[:24] = p_24

    # cumulative
    p_acc = np.cumsum(p)

    # datetime
    start = pd.to_datetime(start)
    datetime = start + pd.to_timedelta(time, unit="h")

    df = pd.DataFrame({"datetime": datetime, "time": time, "p": p, "p_acc": p_acc})

    return df


def hydrograph_scs(df, CN):
    """
    Compute effective rainfall (runoff) from a hyetograph using the SCS Curve Number method (SI units).

    The method is applied to cumulative precipitation to ensure consistency with the
    analytical formulation, and incremental runoff is obtained by differencing the
    accumulated runoff.

    Incremental runoff is computed as:

    .. math::

        r_i = R(P_i) - R(P_{i-1})


    :param df: Input hyetograph with columns:
               - datetime
               - time
               - p (incremental rainfall) [mm]
               - p_acc (cumulative rainfall) [mm]
    :type df: pandas.DataFrame
    :param CN: SCS Curve Number [-]
    :type CN: int or float
    :returns: DataFrame with additional columns:
              - r: incremental runoff [mm]
              - r_acc: cumulative runoff [mm]
              - r_c: runoff coefficient (r / p), NaN where p = 0
    :rtype: pandas.DataFrame
    """

    df = df.copy()

    df = df.sort_values(by="time")

    # --- cumulative precipitation ---
    P_acc = df["p_acc"].values

    # --- accumulated runoff (use core SI function) ---
    R_acc = runoff_scs(P_acc, CN)

    # --- incremental runoff (mass-consistent) ---
    r = np.diff(R_acc, prepend=0.0)

    # --- runoff coefficient ---
    p = df["p"].values
    with np.errstate(divide="ignore", invalid="ignore"):
        r_c = np.where(p > 0, r / p, np.nan)

    # --- assign ---
    df["r"] = r
    df["r_acc"] = R_acc
    df["r_c"] = r_c

    return df


def runoff_scs(P, CN):
    """
    Calculates accumulated runoff depth using the SCS Curve Number method (SI units).

    .. math::

        R =
        \\begin{cases}
        0, & P \\leq I_a \\\\
        \\frac{(P - I_a)^2}{P + 0.8S}, & P > I_a
        \\end{cases}

    Where:

    .. math::

        S = \\frac{25400}{CN} - 254

    .. math::

        I_a = 0.2S


    :param P: Accumulated rainfall depth [mm]
    :type P: float or :class:`numpy.ndarray`
    :param CN: SCS Curve Number [-]
    :type CN: int or float or :class:`numpy.ndarray`
    :return: Accumulated runoff depth [mm]
    :rtype: float or :class:`numpy.ndarray`
    """

    P = np.asarray(P, dtype=float)
    CN = np.asarray(CN, dtype=float)

    # --- retention parameter (mm) ---
    S = (25400.0 / CN) - 254.0

    #
    # --- initial abstraction (mm) ---
    Ia = 0.2 * S

    # --- initialize runoff ---
    R = np.zeros_like(P, dtype=float)

    # --- apply condition ---
    mask = P > Ia
    R[mask] = ((P[mask] - Ia) ** 2) / (P[mask] + 0.8 * S)

    return R

    # R = ((P - (0.2*S)) ** 2) / (P + (0.8 * S))

    return R


def intensity_idf(recurrence, duration, parameters):
    """
    Calculates the average rain intensity given and IDF curve

    .. math::

        i = \\frac{k \\cdot T^{a}}{(d + b)^{c}}

    :param recurrence: recurrence time in years
    :type recurrence: float
    :param duration: event duration in minutes
    :type duration: float
    :param parameters: IDF dict of parameters in consistent units
    :type parameters: dict
    :return: IDF rain intensity in mm/h
    :rtype: float
    """
    k = parameters["k"]
    a = parameters["a"]
    b = parameters["b"]
    c = parameters["c"]

    return (k * np.power(recurrence, a)) / np.power((duration + b), c)


def velocity_manning(R, S, n):
    """
    Calculates flow velocity using the Manning equation.

    .. math::

        V = \\frac{1}{n} \\cdot R^{2/3} \\cdot S^{1/2}

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


def discharge_manning(A, P, S, n):
    """
    Calculates water discharge using the Manning equation.

    .. math::

        Q = \\frac{1}{n} \\cdot A \\cdot \\left(\\frac{A}{P}\\right)^{2/3} \\cdot S^{1/2}

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


def tc_scs(L, S, CN):
    """
    Calculates the time of concentration using the SCS Lag method.

    .. math::

        t_{c} = \\frac{100 \\cdot L^{0.8} \\cdot \\left(\\frac{1000}{CN} - 9\\right)^{0.7}}{1900 \\cdot S^{0.5}}

    .. warning::

        Input units must be in the S.I. Conversion is performed internally.

    :param L: Flow length in meters
    :type L: float or :class:`numpy.ndarray`
    :param S: Slope in degrees
    :type S: float or :class:`numpy.ndarray`
    :param CN: SCS Curve Number
    :type CN: int
    :return: Time of concentration in minutes
    :rtype: float or :class:`numpy.ndarray`
    """
    L_ft = convert_m_to_ft(L)
    S_per = convert_deg_to_percent(S)
    return (100 * (np.power(L_ft, 0.8)) * (np.power(((1000 / CN) - 9), 0.7))) / (
        1900 * (np.power(S_per, 0.5))
    )


def tc_kirpich(L, S):
    """
    Calculates the time of concentration using the Kirpich formula.

    .. math::

        t_{c} = 0.0078 \\cdot L^{0.77} \\cdot S^{-0.385}

    .. warning::

        Input units must be in the S.I. Conversion is performed internally.

    :param L: Maximum flow path length [m]
    :type L: float or :class:`numpy.ndarray`
    :param S: Watershed slope in degrees
    :type S: float or :class:`numpy.ndarray`
    :return: Time of concentration in minutes
    :rtype: float or :class:`numpy.ndarray`
    """
    L_ft = convert_m_to_ft(L)
    S_ratio = convert_deg_to_ratio(S)
    return 0.0078 * (np.power(L_ft, 0.77)) * (np.power(S_ratio, -0.385))


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
