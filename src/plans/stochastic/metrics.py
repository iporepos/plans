# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
r"""
Association and agreement metrics between two samples.

Formulas use :math:`o_i` for observed values and :math:`p_i` for predicted values.
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

__all__ = ["get_metrics", "pearson", "spearman", "rsq", "rmse", "mae", "bias"]


# FUNCTIONS
# ***********************************************************************


def get_metrics(observed, predicted):
    """
    Get all fit metrics between observed and predicted sample.

    :param observed: vector of observed values
    :type observed: :class:`numpy.ndarray`
    :param predicted: vector of predicted values
    :type predicted: :class:`numpy.ndarray`
    :return: dictionary of metrics (r, rho, R2, RMSE, MAE, Bias)
    :rtype: dict
    """
    # correlations
    dc_metrics = {
        "r": pearson(x=observed, y=predicted),
        "rho": spearman(x=observed, y=predicted),
    }
    # agreement
    dc_funcs = {
        "R2": rsq,
        "RMSE": rmse,
        "MAE": mae,
        "Bias": bias,
    }
    for k in dc_funcs:
        dc_metrics[k] = dc_funcs[k](observed=observed, predicted=predicted)
    return {k: float(dc_metrics[k]) for k in dc_metrics}


def pearson(x, y):
    r"""
    Compute the Pearson correlation coefficient (r), a measure of linear association.
    Symmetric: swapping ``x`` and ``y`` gives the same value.

    .. math::

        r = \frac{\sum_i (x_i - \bar{x})(y_i - \bar{y})}
        {\sqrt{\sum_i (x_i - \bar{x})^2} \sqrt{\sum_i (y_i - \bar{y})^2}}

    :param x: vector of x values
    :type x: :class:`numpy.ndarray`
    :param y: vector of y values
    :type y: :class:`numpy.ndarray`
    :return: r value, from -1 to 1
    :rtype: float
    """
    return np.corrcoef(x=x, y=y)[0, 1]


def spearman(x, y):
    r"""
    Compute the Spearman rank correlation coefficient (rho), a measure of
    monotonic association. It is the Pearson r of the ranks (ties averaged).
    Symmetric: swapping ``x`` and ``y`` gives the same value.

    .. math::

        \rho = r\left( \mathrm{rank}(x), \mathrm{rank}(y) \right)

    :param x: vector of x values
    :type x: :class:`numpy.ndarray`
    :param y: vector of y values
    :type y: :class:`numpy.ndarray`
    :return: rho value, from -1 to 1
    :rtype: float
    """
    from scipy.stats import rankdata

    return pearson(x=rankdata(a=x), y=rankdata(a=y))


def rsq(observed, predicted):
    r"""
    Compute the coefficient of determination (R2), as the fraction of
    observed variance explained: ``1 - SS_res / SS_tot``.

    .. note::

        Equals r squared only for least-squares linear models with intercept.
        For other models it can differ, and is negative when the model is worse
        than the observed mean.

    .. math::

        R^2 = 1 - \frac{\sum_i (p_i - o_i)^2}{\sum_i (o_i - \bar{o})^2}

    :param observed: vector of observed values
    :type observed: :class:`numpy.ndarray`
    :param predicted: vector of predicted values
    :type predicted: :class:`numpy.ndarray`
    :return: R2 value
    :rtype: float
    """
    return 1 - (
        np.sum(a=np.power(predicted - observed, 2))
        / np.sum(a=np.power(observed - np.mean(a=observed), 2))
    )


def rmse(observed, predicted):
    r"""
    Compute the Root Mean Squared Error (RMSE).

    .. math::

        \mathrm{RMSE} = \sqrt{\frac{1}{n} \sum_i (p_i - o_i)^2}

    :param observed: vector of observed values
    :type observed: :class:`numpy.ndarray`
    :param predicted: vector of predicted values
    :type predicted: :class:`numpy.ndarray`
    :return: RMSE value
    :rtype: float
    """
    return np.sqrt(np.sum(a=np.power(predicted - observed, 2)) / len(predicted))


def mae(observed, predicted):
    r"""
    Compute the Mean Absolute Error (MAE).

    .. math::

        \mathrm{MAE} = \frac{1}{n} \sum_i \lvert p_i - o_i \rvert

    :param observed: vector of observed values
    :type observed: :class:`numpy.ndarray`
    :param predicted: vector of predicted values
    :type predicted: :class:`numpy.ndarray`
    :return: MAE value
    :rtype: float
    """
    return np.sum(a=np.abs(predicted - observed)) / len(predicted)


def bias(observed, predicted):
    r"""
    Compute the Bias (%), positive when predicted overestimates observed.

    .. math::

        \mathrm{Bias} = 100 \, \frac{\sum_i (p_i - o_i)}{\sum_i o_i}

    :param observed: vector of observed values
    :type observed: :class:`numpy.ndarray`
    :param predicted: vector of predicted values
    :type predicted: :class:`numpy.ndarray`
    :return: Bias value
    :rtype: float
    """
    return 100 * np.sum(a=predicted - observed) / np.sum(a=observed)
