# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
r"""
Trend, season and AR(1) memory model for synthetic series.

A series is the sum of a linear trend, a mean-zero seasonal term and an AR(1)
remainder driven by Gaussian shocks. For steps :math:`t = 0, 1, \dots, n-1`:

.. math::

    x_t = \underbrace{b + a t}_{\text{trend}}
    + \underbrace{A (g_t - m_k)}_{\text{season}} + R_t,
    \qquad R_t = \varphi R_{t-1} + \varepsilon_t,
    \qquad \varepsilon_t \sim \mathcal{N}(0, \sigma^2)

Parameters map to symbols as ``start`` :math:`b`, ``slope`` :math:`a`, ``amplitude``
:math:`A`, ``period`` :math:`P`, ``phase`` :math:`t_0`, ``power`` :math:`k`, ``phi``
:math:`\varphi` and ``sigma`` :math:`\sigma`. Functions take plain arrays and an
integer ``period`` (steps per cycle), so they know nothing about dates or units.

Three operations link observed data, parameters and synthetic data:
:func:`fit_params` goes from data to parameters, :func:`decompose` splits data into
components given the parameters, and :func:`build` makes a series from parameters.
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

__all__ = [
    "trend_line",
    "season_shape",
    "shape_mean",
    "season_component",
    "draw_shocks",
    "ar1_from_shocks",
    "simulate_ar1",
    "fit_params",
    "decompose",
    "build",
    "get_floor",
    "describe",
    "make_params",
    "start_from_average",
    "average_from_start",
    "slope_from_end",
    "slope_from_cycle_change",
]

POWER_MIN = 1.0
POWER_MAX = 10.0
# starting shapes of the fit, so a sharp season is not missed
POWER_STARTS = (1.0, 3.0, 6.0)
MIN_CYCLES = 3


# FUNCTIONS
# ***********************************************************************

# FUNCTIONS -- Module-level
# =======================================================================


def _check_period(period):
    """Raise an error if the period is not a positive integer."""
    if not isinstance(period, (int, np.integer)) or period < 1:
        raise ValueError("period must be a positive integer")


def _check_phi(phi):
    """Raise an error if the AR(1) memory is not stationary."""
    if np.abs(phi) >= 1:
        raise ValueError("phi must be inside (-1, 1)")


def _ols(design, x):
    """Get ordinary least squares coefficients."""
    return np.linalg.lstsq(a=design, b=x, rcond=None)[0]


# FUNCTIONS -- Components
# =======================================================================


def trend_line(n, start, slope):
    r"""
    Get the linear trend.

    .. math::

        T_t = b + a t

    :param n: number of steps
    :type n: int
    :param start: trend value at step 0
    :type start: float
    :param slope: trend change per step
    :type slope: float
    :return: trend values
    :rtype: :class:`numpy.ndarray`
    """
    return start + slope * np.arange(start=0, stop=n)


def season_shape(n, period, phase, power):
    r"""
    Get the seasonal shape, a raised cosine to a power.

    .. math::

        g_t = \left[ \frac{1 + \cos\theta_t}{2} \right]^{k},
        \qquad \theta_t = \frac{2 \pi (t - t_0)}{P}

    :param n: number of steps
    :type n: int
    :param period: steps per cycle
    :type period: int
    :param phase: step at which the season peaks
    :type phase: float
    :param power: shape. 1 gives a plain cosine, larger gives a sharper peak.
    :type power: float
    :return: shape values, from 0 to 1
    :rtype: :class:`numpy.ndarray`
    """
    theta = 2 * np.pi * (np.arange(start=0, stop=n) - phase) / period
    return np.power((1 + np.cos(theta)) / 2, power)


def shape_mean(power):
    r"""
    Get the average of the seasonal shape over a cycle.

    .. math::

        m_k = \frac{\Gamma(k + \tfrac{1}{2})}{\sqrt{\pi} \, \Gamma(k + 1)}

    It equals 0.5 for :math:`k = 1` and 0.375 for :math:`k = 2`.

    :param power: shape
    :type power: float
    :return: average of the shape
    :rtype: float
    """
    from scipy.special import gammaln

    return float(np.exp(gammaln(power + 0.5) - gammaln(power + 1)) / np.sqrt(np.pi))


def season_component(n, amplitude, period, phase, power):
    r"""
    Get the seasonal term, which averages zero over a cycle.

    .. math::

        S_t = A (g_t - m_k)

    For :math:`k = 1` this is a plain cosine of half-range :math:`A / 2`.

    :param n: number of steps
    :type n: int
    :param amplitude: peak-to-trough range of the seasonal term
    :type amplitude: float
    :param period: steps per cycle
    :type period: int
    :param phase: step at which the season peaks
    :type phase: float
    :param power: shape
    :type power: float
    :return: seasonal values
    :rtype: :class:`numpy.ndarray`
    """
    g = season_shape(n=n, period=period, phase=phase, power=power)
    return amplitude * (g - shape_mean(power=power))


def draw_shocks(n, sigma, rng):
    r"""
    Draw independent Gaussian shocks.

    .. math::

        \varepsilon_t \sim \mathcal{N}(0, \sigma^2)

    :param n: number of steps
    :type n: int
    :param sigma: shock standard deviation
    :type sigma: float
    :param rng: random generator
    :type rng: :class:`numpy.random.Generator`
    :return: shocks
    :rtype: :class:`numpy.ndarray`
    """
    return sigma * rng.standard_normal(size=n)


def ar1_from_shocks(shocks, phi):
    r"""
    Get the AR(1) remainder from given shocks, with the first value set to the
    first shock.

    .. math::

        R_0 = \varepsilon_0, \qquad R_t = \varphi R_{t-1} + \varepsilon_t

    :param shocks: shocks
    :type shocks: :class:`numpy.ndarray`
    :param phi: AR(1) memory
    :type phi: float
    :return: remainder
    :rtype: :class:`numpy.ndarray`
    """
    r = np.zeros(shape=len(shocks))
    r[0] = shocks[0]
    for t in range(1, len(shocks)):
        r[t] = phi * r[t - 1] + shocks[t]
    return r


def simulate_ar1(n, phi, sigma, rng):
    r"""
    Simulate an AR(1) remainder that is stationary from the first step.

    The first shock is scaled to the stationary variance instead of discarding a
    burn-in. Draws therefore stay aligned when ``phi`` changes, so the same generator
    state isolates the effect of ``phi``.

    .. math::

        R_0 = \frac{\varepsilon_0}{\sqrt{1 - \varphi^2}},
        \qquad \mathrm{Var}(R_t) = \frac{\sigma^2}{1 - \varphi^2}

    :param n: number of steps
    :type n: int
    :param phi: AR(1) memory, inside (-1, 1)
    :type phi: float
    :param sigma: shock standard deviation
    :type sigma: float
    :param rng: random generator
    :type rng: :class:`numpy.random.Generator`
    :return: remainder
    :rtype: :class:`numpy.ndarray`
    """
    _check_phi(phi=phi)
    shocks = draw_shocks(n=n, sigma=sigma, rng=rng)
    shocks[0] = shocks[0] / np.sqrt(1 - phi**2)
    return ar1_from_shocks(shocks=shocks, phi=phi)


# FUNCTIONS -- Triangle
# =======================================================================


def fit_params(x, period):
    r"""
    Fit the model to a series.

    Trend and season are fitted jointly by nonlinear least squares from several
    starting shapes, keeping the best. ``power`` is bounded by ``POWER_MIN`` and
    ``POWER_MAX``, so a season with a sharp trough and a flat top cannot be represented.

    Memory and shocks come from the remainder :math:`R_t`, after removing its mean.
    The memory is a regression through the origin, and :math:`\hat{\sigma}` is the
    standard deviation of the residuals of that regression:

    .. math::

        \hat{\varphi} = \frac{\sum_t R_{t-1} R_t}{\sum_t R_{t-1}^2},
        \qquad \hat{\sigma} = \mathrm{sd}\left( R_t - \hat{\varphi} R_{t-1} \right)

    .. warning::

        Trend and season estimates ignore the memory, so they are less precise than
        they could be, and ``phi`` tends to be low on short series.

    :param x: series without nan values
    :type x: :class:`numpy.ndarray`
    :param period: steps per cycle
    :type period: int
    :return: parameters. Keys: start, slope, amplitude, period, phase, power, phi, sigma
    :rtype: dict
    """
    from scipy.optimize import least_squares

    _check_period(period=period)
    x = np.asarray(x, dtype=float)
    if np.any(np.isnan(x)):
        raise ValueError("x has NaN values. Fill or remove them first")
    if len(x) < MIN_CYCLES * period:
        raise ValueError(f"x must have at least {MIN_CYCLES} cycles of data")

    n = len(x)
    t = np.arange(start=0, stop=n)
    theta = 2 * np.pi * t / period

    # phase from a linear harmonic fit
    design = np.column_stack(
        [np.ones(shape=n), t, np.cos(theta), np.sin(theta)],
    )
    c = _ols(design=design, x=x)
    phase_0 = np.arctan2(c[3], c[2]) * period / (2 * np.pi)

    def _residuals(p):
        trend = trend_line(n=n, start=p[0], slope=p[1])
        season = season_component(
            n=n, amplitude=p[2], period=period, phase=p[3], power=p[4]
        )
        return trend + season - x

    # joint fit from each starting shape
    bounds = (
        [-np.inf, -np.inf, 0.0, -np.inf, POWER_MIN],
        [np.inf, np.inf, np.inf, np.inf, POWER_MAX],
    )
    best = None
    for power_0 in POWER_STARTS:
        g = season_shape(n=n, period=period, phase=phase_0, power=power_0)
        design = np.column_stack(
            [np.ones(shape=n), t, g - shape_mean(power=power_0)],
        )
        c = _ols(design=design, x=x)
        p_0 = [c[0], c[1], max(c[2], 0.0), phase_0, power_0]
        result = least_squares(fun=_residuals, x0=p_0, bounds=bounds, x_scale="jac")
        if best is None or result.cost < best.cost:
            best = result
    start, slope, amplitude, phase, power = best.x

    if power >= POWER_MAX * (1 - 1e-6):
        warnings.warn(f"power reached its upper bound of {POWER_MAX}")

    # memory and shocks from the centered remainder
    r = -_residuals(p=best.x)
    r = r - np.mean(a=r)
    denominator = np.sum(a=r[:-1] ** 2)
    phi = 0.0 if denominator == 0 else np.sum(a=r[:-1] * r[1:]) / denominator
    if np.abs(phi) >= 1:
        raise ValueError(f"The remainder is not stationary: phi = {phi}")
    sigma = np.std(a=r[1:] - phi * r[:-1])

    return {
        "start": float(start),
        "slope": float(slope),
        "amplitude": float(amplitude),
        "period": int(period),
        "phase": float(phase % period),
        "power": float(power),
        "phi": float(phi),
        "sigma": float(sigma),
    }


def decompose(x, params):
    r"""
    Split a series into components, given the parameters.

    .. math::

        R_t = x_t - T_t - S_t,
        \qquad \varepsilon_0 = R_0,
        \qquad \varepsilon_t = R_t - \varphi R_{t-1}

    :param x: series
    :type x: :class:`numpy.ndarray`
    :param params: parameters. See :func:`fit_params`.
    :type params: dict
    :return: arrays by component. Keys: trend, season, remainder, shocks
    :rtype: dict
    """
    x = np.asarray(x, dtype=float)
    n = len(x)
    trend = trend_line(n=n, start=params["start"], slope=params["slope"])
    season = season_component(
        n=n,
        amplitude=params["amplitude"],
        period=params["period"],
        phase=params["phase"],
        power=params["power"],
    )
    r = x - trend - season
    # the first shock is the first remainder, as in ar1_from_shocks
    shocks = r.copy()
    shocks[1:] = r[1:] - params["phi"] * r[:-1]
    return {"trend": trend, "season": season, "remainder": r, "shocks": shocks}


def build(params, n, seed=None, shocks=None):
    """
    Make a series from the parameters.

    To isolate the effect of one parameter, change it and build again with the same
    ``seed`` or the same ``shocks``.

    :param params: parameters. See :func:`fit_params`.
    :type params: dict
    :param n: number of steps
    :type n: int
    :param seed: random seed, used when ``shocks`` is None
    :type seed: int or None
    :param shocks: shocks to use instead of drawing them, of size ``n``
    :type shocks: :class:`numpy.ndarray` or None
    :return: series
    :rtype: :class:`numpy.ndarray`
    """
    _check_phi(phi=params["phi"])
    if shocks is None:
        r = simulate_ar1(
            n=n,
            phi=params["phi"],
            sigma=params["sigma"],
            rng=np.random.default_rng(seed=seed),
        )
    else:
        if len(shocks) != n:
            raise ValueError("shocks must have size n")
        r = ar1_from_shocks(shocks=shocks, phi=params["phi"])
    trend = trend_line(n=n, start=params["start"], slope=params["slope"])
    season = season_component(
        n=n,
        amplitude=params["amplitude"],
        period=params["period"],
        phase=params["phase"],
        power=params["power"],
    )
    return trend + season + r


# FUNCTIONS -- Presenting
# =======================================================================


def get_floor(params, n):
    r"""
    Get the lowest value of trend plus season, :math:`\min_t (T_t + S_t)`.

    .. note::

        This is the deterministic floor. Shocks are Gaussian and additive, so a
        synthetic series can still fall below it.

    :param params: parameters. See :func:`fit_params`.
    :type params: dict
    :param n: number of steps
    :type n: int
    :return: lowest value of trend plus season
    :rtype: float
    """
    trend = trend_line(n=n, start=params["start"], slope=params["slope"])
    season = season_component(
        n=n,
        amplitude=params["amplitude"],
        period=params["period"],
        phase=params["phase"],
        power=params["power"],
    )
    return float(np.min(a=trend + season))


def describe(params, n, positive=False):
    r"""
    Get a printout with all views of the same model.

    Baseline and topline are the extremes of the deterministic cycle, at the trend
    average :math:`\bar{T}`. Noise moves the observed extremes beyond them.

    .. math::

        \text{baseline} = \bar{T} - A m_k,
        \qquad \text{topline} = \bar{T} + A (1 - m_k)

    :param params: parameters. See :func:`fit_params`.
    :type params: dict
    :param n: number of steps, used by the views that depend on the length
    :type n: int
    :param positive: set True for variables that must stay positive. It warns if the
        deterministic floor is below zero.
    :type positive: bool
    :return: formatted text
    :rtype: str
    """
    start, slope = params["start"], params["slope"]
    amplitude, period = params["amplitude"], params["period"]
    m = shape_mean(power=params["power"])
    average = average_from_start(start=start, slope=slope, n=n)
    floor = get_floor(params=params, n=n)

    ls_rows = [
        ("start", start),
        ("slope per step", slope),
        ("slope per cycle", slope * period),
        (f"trend end (n={n})", start + slope * (n - 1)),
        (f"trend average (n={n})", average),
        ("amplitude", amplitude),
        ("baseline (at trend average)", average - amplitude * m),
        ("topline (at trend average)", average + amplitude * (1 - m)),
        ("period", period),
        ("phase", params["phase"]),
        ("power", params["power"]),
        ("phi", params["phi"]),
        ("sigma", params["sigma"]),
        (f"floor (n={n})", floor),
    ]
    s = "\n".join(f"{k:<30}{v:>14.6g}" for k, v in ls_rows)

    if positive and floor < 0:
        s_warn = f"Floor of trend + season is below zero: {floor:.6g}"
        warnings.warn(s_warn)
        s = s + f"\nWARNING: {s_warn}"
    return s


# FUNCTIONS -- Conversions
# =======================================================================


def start_from_average(average, slope, n):
    r"""
    Get the trend start from the trend average over the record.

    .. math::

        b = \bar{T} - a \frac{n - 1}{2}

    :param average: trend average
    :type average: float
    :param slope: trend change per step
    :type slope: float
    :param n: number of steps
    :type n: int
    :return: trend value at step 0
    :rtype: float
    """
    return average - slope * (n - 1) / 2


def average_from_start(start, slope, n):
    r"""
    Get the trend average over the record from the trend start.

    .. math::

        \bar{T} = b + a \frac{n - 1}{2}

    :param start: trend value at step 0
    :type start: float
    :param slope: trend change per step
    :type slope: float
    :param n: number of steps
    :type n: int
    :return: trend average
    :rtype: float
    """
    return start + slope * (n - 1) / 2


def slope_from_end(start, end, n):
    r"""
    Get the slope from the trend values at the first and last steps.

    .. math::

        a = \frac{T_{n-1} - b}{n - 1}

    :param start: trend value at step 0
    :type start: float
    :param end: trend value at the last step
    :type end: float
    :param n: number of steps
    :type n: int
    :return: trend change per step
    :rtype: float
    """
    return (end - start) / (n - 1)


def slope_from_cycle_change(change, period):
    r"""
    Get the slope from the trend change per cycle :math:`\Delta T`.

    .. math::

        a = \frac{\Delta T}{P}

    :param change: trend change per cycle
    :type change: float
    :param period: steps per cycle
    :type period: int
    :return: trend change per step
    :rtype: float
    """
    return change / period


def make_params(
    period,
    start=None,
    average=None,
    slope=None,
    end=None,
    cycle_change=None,
    n=None,
    amplitude=None,
    baseline=None,
    topline=None,
    phase=0.0,
    power=1.0,
    phi=0.0,
    sigma=0.0,
):
    r"""
    Make the parameters from what is known, converting to the stored form.

    The trend level comes from ``start`` or ``average``, its change from ``slope``,
    ``end`` or ``cycle_change``, and the season from ``amplitude`` or from both
    ``baseline`` and ``topline``, with :math:`A = \text{topline} - \text{baseline}`.
    Giving more than one option for the same item raises an error. Length-based
    conversions apply once here, so a longer series continues the same line.

    See :func:`start_from_average`, :func:`slope_from_end` and
    :func:`slope_from_cycle_change` for the formulas.

    :param period: steps per cycle
    :type period: int
    :param start: trend value at step 0
    :type start: float
    :param average: trend average over the record. Requires ``n``.
    :type average: float
    :param slope: trend change per step
    :type slope: float
    :param end: trend value at the last step. Requires ``start`` and ``n``.
    :type end: float
    :param cycle_change: trend change per cycle
    :type cycle_change: float
    :param n: number of steps, used only by the length-based conversions
    :type n: int
    :param amplitude: peak-to-trough range of the seasonal term
    :type amplitude: float
    :param baseline: lowest value of the deterministic cycle
    :type baseline: float
    :param topline: highest value of the deterministic cycle
    :type topline: float
    :param phase: step at which the season peaks
    :type phase: float
    :param power: shape
    :type power: float
    :param phi: AR(1) memory, inside (-1, 1)
    :type phi: float
    :param sigma: shock standard deviation
    :type sigma: float
    :return: parameters. See :func:`fit_params`.
    :rtype: dict
    """
    _check_period(period=period)
    _check_phi(phi=phi)

    # one option per item
    if start is not None and average is not None:
        raise ValueError("Give only one of: start, average")
    if sum(v is not None for v in [slope, end, cycle_change]) > 1:
        raise ValueError("Give only one of: slope, end, cycle_change")
    if amplitude is not None and (baseline is not None or topline is not None):
        raise ValueError("Give amplitude or baseline and topline, not both")
    if (baseline is None) != (topline is None):
        raise ValueError("baseline and topline must be given together")

    # requirements of the length-based options
    if (average is not None or end is not None) and n is None:
        raise ValueError("average and end require n")
    if end is not None and start is None:
        raise ValueError("end requires start")

    # trend change
    if end is not None:
        slope = slope_from_end(start=start, end=end, n=n)
    elif cycle_change is not None:
        slope = slope_from_cycle_change(change=cycle_change, period=period)
    elif slope is None:
        slope = 0.0

    # trend level
    if average is not None:
        start = start_from_average(average=average, slope=slope, n=n)
    elif start is None:
        start = 0.0

    # season
    if baseline is not None:
        amplitude = topline - baseline
    elif amplitude is None:
        amplitude = 0.0

    return {
        "start": float(start),
        "slope": float(slope),
        "amplitude": float(amplitude),
        "period": int(period),
        "phase": float(phase),
        "power": float(power),
        "phi": float(phi),
        "sigma": float(sigma),
    }
