# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
Descriptive summaries of a sample.
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

__all__ = ["get_basic_stats", "qqplot", "trace_variance"]


# FUNCTIONS
# ***********************************************************************


def get_basic_stats(data):
    """
    Get basic statistics of a sample. An empty sample gives count 0 and NaN values.

    :param data: vector of data without nan values
    :type data: :class:`numpy.ndarray`
    :return: DataFrame with statistics and their values.
    :rtype: :class:`pandas.DataFrame`
    """

    def _compute(data):
        return {
            "count": len(data),
            "sum": np.sum(a=data),
            "mean": np.mean(a=data),
            "sd": np.std(a=data),
            "min": np.min(a=data),
            "p01": np.percentile(a=data, q=1),
            "p05": np.percentile(a=data, q=5),
            "p10": np.percentile(a=data, q=10),
            "p20": np.percentile(a=data, q=20),
            "p25": np.percentile(a=data, q=25),
            "p40": np.percentile(a=data, q=40),
            "p50": np.percentile(a=data, q=50),
            "p60": np.percentile(a=data, q=60),
            "p75": np.percentile(a=data, q=75),
            "p80": np.percentile(a=data, q=80),
            "p90": np.percentile(a=data, q=90),
            "p95": np.percentile(a=data, q=95),
            "p99": np.percentile(a=data, q=99),
            "max": np.max(a=data),
        }

    # handle void case
    if len(data) == 0:
        dct = _compute(data=[0])  # feed dummy values
        ls_values = [np.nan for key in dct]
        ls_values[0] = 0  # fix for count
    else:
        dct = _compute(data=data)
        ls_values = [dct[key] for key in dct]
    return pd.DataFrame({"statistic": list(dct.keys()), "value": ls_values})


def qqplot(data):
    """
    Calculate the QQ-plot of data against normal distribution

    :param data: vector of data without nan values
    :type data: :class:`numpy.ndarray`
    :return: dataframe of QQ plot
    :rtype: :class:`pandas.DataFrame`
    """
    from scipy.stats import norm

    # process quantiles
    _df = pd.DataFrame(
        {
            "Data": np.sort(a=data),
            "E-Quantiles": (np.arange(start=1, stop=len(data) + 1) - 0.5) / len(data),
        }
    )
    # get theoretical
    _df["T-Quantiles"] = norm.ppf(q=_df["E-Quantiles"])
    return _df


def trace_variance(data):
    """
    Trace the mean variance from sample

    :param data: vector of data without nan values
    :type data: :class:`numpy.ndarray`
    :return: dataframe of accumulated variance
    :rtype: :class:`pandas.DataFrame`
    """
    vct_variance_mean = np.zeros(shape=len(data))
    for i in range(2, len(data)):
        vct_variance_mean[i] = np.var(a=data[:i])

    # process quantiles
    _df = pd.DataFrame(
        {
            "Data": data,
            "Variance": vct_variance_mean,
        }
    )

    return _df
