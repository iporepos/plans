# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
r"""
Histogram bin rules, class boundaries and classification.

Formulas use :math:`k` for the number of bins, :math:`w` for the bin width, :math:`n`
for the sample size and :math:`s` for the standard deviation.
"""

# IMPORTS
# ***********************************************************************
# import modules from other libs

# External imports
# =======================================================================
import numpy as np
import pandas as pd

# CONSTANTS
# ***********************************************************************
# define constants in uppercase

__all__ = [
    "get_nbins_fd",
    "get_nbins_sturges",
    "get_nbins_scott",
    "get_nbins_density",
    "get_nbins_by_rule",
    "get_histogram",
    "get_bins",
    "bins_equal",
    "bins_quantiles",
    "classify",
    "quantiles_classify",
]


# FUNCTIONS
# ***********************************************************************


def get_nbins_fd(data):
    r"""
    This function computes the number of bins for histograms using the Freedman-Diaconis rule, which takes into
    account the interquartile range (IQR) of the sample, in addition to its range.

    .. math::

        w = 2 \, \mathrm{IQR} \, n^{-1/3},
        \qquad k = \left\lceil \frac{\max(x) - \min(x)}{w} \right\rceil

    :param data: vector of data without nan values
    :type data: :class:`numpy.ndarray`
    :return: number of bins for histogram using the Freedman-Diaconis rule
    :rtype: int
    """
    iqr = np.subtract(*np.percentile(a=data, q=[75, 25]))
    binsize = 2 * iqr * len(data) ** (-1 / 3)
    # hack for non infinite values
    if binsize == 0:
        binsize = 100
    return int(np.ceil((max(data) - min(data)) / binsize))


def get_nbins_sturges(data):
    r"""
    This function computes the number of bins using the Sturges rule,
    which assumes that the data follows a normal distribution and computes
    the number of bins based on its data runsize.

    .. math::

        k = \left\lceil \log_2 n + 1 \right\rceil

    :param data: vector of data without nan values
    :type data: :class:`numpy.ndarray`
    :return: number of bins using the Sturges rule
    :rtype: int
    """
    return int(np.ceil(np.log2(len(data)) + 1))


def get_nbins_scott(data):
    r"""
    This function computes the number of bins using the Scott rule,
    which is similar to the Freedman-Diaconis rule, but uses the standard deviation
    of the data to compute the bin runsize.

    .. math::

        w = 3.5 \, s \, n^{-1/3},
        \qquad k = \left\lceil \frac{\max(x) - \min(x)}{w} \right\rceil

    :param data: vector of data without nan values
    :type data: :class:`numpy.ndarray`
    :return: number of bins using the Scott rule
    :rtype: int
    """
    binsize = 3.5 * np.nanstd(a=data) * len(data) ** (-1 / 3)
    return int(np.ceil((max(data) - min(data)) / binsize))


def get_nbins_density(n_units, data_range):
    r"""
    Compute the number of bins from a target bin width, with a minimum of one.

    .. math::

        k = \max\left( 1, \left\lfloor \frac{x_1 - x_0}{w} \right\rfloor \right)

    :param n_units: bin width, in data units
    :type n_units: float
    :param data_range: lower and upper values of the range
    :type data_range: list
    :return: number of bins
    :rtype: int
    """
    n_range = data_range[1] - data_range[0]
    bins = int(n_range / n_units)
    if bins < 1:
        return 1
    else:
        return bins


def get_nbins_by_rule(data, rule=None):
    """
    Util function for rule-based nbins computation

    :param data: vector of data without nan values
    :type data: :class:`numpy.ndarray`
    :param rule: rule code (sturges, fd, scott). Anything else gives 10 bins.
    :type rule: str
    :return: number of bins for histogram
    :rtype: int
    """
    bins = 10
    if rule is None:
        pass
    else:
        if rule.lower() == "sturges":
            bins = get_nbins_sturges(data=data)
        elif rule.lower() == "fd":
            bins = get_nbins_fd(data=data)
        elif rule.lower() == "scott":
            bins = get_nbins_scott(data=data)
        else:
            pass
    return bins


def get_histogram(data, bins=100, rule=None):
    """
    Compute the histogram of the sample

    :param data: vector of data without nan values
    :type data: :class:`numpy.ndarray`
    :param bins: number of bins
    :type bins: int
    :param rule: rule to define the number of bins. Only used when ``bins`` is None.
    :type rule: str
    :return: dataframe of histogram
    :rtype: :class:`pandas.DataFrame`
    """

    if bins is None:
        if rule is None:
            pass
        else:
            bins = get_nbins_by_rule(data=data, rule=rule)
    # compute histogram
    vct_hist, vct_bins = np.histogram(a=data, bins=bins)
    # get dataframe
    df_hist = pd.DataFrame({"Upper value": vct_bins[1:], "Count": vct_hist})
    return df_hist


def get_bins(data, n_bins=5, scheme="equal"):
    """
    Get class boundaries by scheme.

    :param data: vector of data without nan values
    :type data: :class:`numpy.ndarray`
    :param n_bins: number of classes
    :type n_bins: int
    :param scheme: scheme code. Options: equal, linear, quantiles, quantile
    :type scheme: str
    :return: class boundaries
    :rtype: :class:`numpy.ndarray`
    """
    dc = {
        "linear": bins_equal,
        "equal": bins_equal,
        "quantiles": bins_quantiles,
        "quantile": bins_quantiles,
    }
    v = dc[scheme](data=data, n_bins=n_bins)
    return v


def bins_equal(data, n_bins):
    """
    Calculates equally spaced (linear) bins for a 1D NumPy array.

    :param data: The 1D NumPy array to analyze.
    :type data: :class:`numpy.ndarray`
    :param n_bins: The desired number of bins/intervals.
    :type n_bins: int
    :return: A NumPy array containing the linear bin boundary values.
    :rtype: :class:`numpy.ndarray`
    """
    min_val = np.min(a=data)
    max_val = np.max(a=data)

    # np.linspace creates 'n_classes + 1' points to define 'n_classes' intervals
    linear_bins = np.linspace(start=min_val, stop=max_val, num=n_bins + 1)
    return linear_bins


def bins_quantiles(data, n_bins=5):
    """
    Calculates the numerical quantile boundaries (bins) for a 1D NumPy array.

    :param data: The 1D NumPy array to analyze.
    :type data: :class:`numpy.ndarray`
    :param n_bins: The number of quantile classes.
    :type n_bins: int
    :return: A NumPy array containing the quantile boundary values.
    :rtype: :class:`numpy.ndarray`
    """
    # pd.qcut with retbins=True returns (labels, bins)
    _, bins = pd.qcut(
        x=data,
        q=n_bins,
        retbins=True,
        duplicates="drop",  # Essential for handling non-unique quantiles
    )
    return bins


def classify(data, bins=None, n_classes=5, scheme="equal"):
    r"""
    Classifies a 1D NumPy array into 0-indexed bins based on provided bin boundaries.

    Values are assigned to class :math:`i` if :math:`b_i \le x < b_{i+1}`.
    Values below ``bins[0]`` are assigned to class 0.
    Values at or above ``bins[-1]`` are assigned to the last class (``len(bins) - 2``).

    :param data: The 1D NumPy array to classify.
    :type data: :class:`numpy.ndarray`
    :param bins: A 1D NumPy array specifying the sorted bin edges.
        Must contain at least two elements. If None, it is computed from the data.
    :type bins: :class:`numpy.ndarray`
    :param n_classes: number of classes, used only if ``bins`` is None
    :type n_classes: int
    :param scheme: scheme code, used only if ``bins`` is None. See :func:`get_bins`.
    :type scheme: str
    :return: A 1D NumPy array of integers representing the 0-indexed class for
        each element in ``data``.
    :rtype: :class:`numpy.ndarray`
    """
    # handle bins
    if bins is None:
        bins = get_bins(data=data, n_bins=n_classes, scheme=scheme)

    # Number of intervals (classes) will be one less than the number of bins
    num_classes = len(bins) - 1

    # side="right" places a value equal to an edge in the class above it
    classes = np.searchsorted(a=bins, v=data, side="right") - 1

    # Clamp values outside the bins range into the first or last class
    classified_array = np.clip(classes, 0, num_classes - 1)

    return classified_array


def quantiles_classify(data, n_classes=5):
    """
    Classifies a 1D NumPy array into quantile classes.

    :param data: The 1D NumPy array to classify.
    :type data: :class:`numpy.ndarray`
    :param n_classes: The number of quantile classes.
    :type n_classes: int
    :return: A 1D NumPy array containing the quantile class (0 to n_classes-1) for each element.
    :rtype: :class:`numpy.ndarray`
    """
    bins = get_bins(data=data, n_bins=n_classes, scheme="quantiles")
    return classify(data=data, bins=bins)
