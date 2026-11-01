# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
Statistical tests for distribution assumptions.
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
    "test_distribution",
    "test_normality_ks",
    "test_normality_sw",
    "test_normality_dp",
    "get_normality",
]


# FUNCTIONS
# ***********************************************************************


def test_distribution(test_name, stat, p, clevel=0.95, distr="normal"):
    """
    Util function for statistical testing

    The distribution is accepted when :math:`p > 1 - c`, at confidence level :math:`c`.

    :param test_name: name of test
    :type test_name: str
    :param stat: statistic
    :type stat: float
    :param p: p-value
    :type p: float
    :param clevel: confidence level
    :type clevel: float
    :param distr: name of distribution
    :type distr: str
    :return: summary of test
    :rtype: dict
    """
    # built output dict
    dct_out = {
        "Test": test_name,
        "Statistic": stat,
        "p-value": p,
        "Confidence": clevel,
    }

    if p > (1 - clevel):
        dct_out["is_{}".format(distr.lower())] = True
    else:
        dct_out["is_{}".format(distr.lower())] = False

    return dct_out


def test_normality_ks(data, clevel=0.95):
    r"""
    Test for normality using the Kolmogorov-Smirnov test

    Kolmogorov-Smirnov Test: This test compares the observed distribution with
    the expected normal distribution using a test statistic and a p-value.
    A p-value less than 0.05 indicates that the null hypothesis should be rejected.

    The sample is first standardized as :math:`z_i = (x_i - \bar{x}) / s`.

    :param data: vector of data without nan values
    :type data: :class:`numpy.ndarray`
    :param clevel: confidence level
    :type clevel: float
    :return: test result dictionary. Keys: Statistic, p-value and Is normal
    :rtype: dict
    """
    from scipy.stats import kstest

    vct_norm = (data - np.mean(a=data)) / np.std(a=data)

    # test
    result = kstest(rvs=vct_norm, cdf="norm")
    return test_distribution(
        test_name="Kolmogorov-Smirnov",
        stat=result.statistic,
        p=result.pvalue,
        clevel=clevel,
        distr="normal",
    )


def test_normality_sw(data, clevel=0.95):
    """
    Test for normality using the Shapiro-Wilk test.

    :param data: vector of data without nan values
    :type data: :class:`numpy.ndarray`
    :param clevel: confidence level
    :type clevel: float
    :return: test result dictionary. Keys: Statistic, p-value and Is normal
    :rtype: dict
    """
    from scipy.stats import shapiro

    # test
    stat, p = shapiro(x=data)

    return test_distribution(
        test_name="Shapiro-Wilk", stat=stat, p=p, clevel=clevel, distr="normal"
    )


def test_normality_dp(data, clevel=0.95):
    """
    Test for normality using the D'Agostino-Pearson test.

    :param data: vector of data without nan values
    :type data: :class:`numpy.ndarray`
    :param clevel: confidence level
    :type clevel: float
    :return: test result dictionary. Keys: Statistic, p-value and Is normal
    :rtype: dict
    """
    from scipy.stats import normaltest

    # test
    stat, p = normaltest(a=data)

    return test_distribution(
        test_name="D'Agostino-Pearson",
        stat=stat,
        p=p,
        clevel=clevel,
        distr="normal",
    )


def get_normality(data, clevel=0.95):
    """
    Get normality analysis using standard tests.

    :param data: vector of data without nan values
    :type data: :class:`numpy.ndarray`
    :param clevel: confidence level
    :type clevel: float
    :return: dataframe of assessment results
    :rtype: :class:`pandas.DataFrame`
    """
    # run tests
    lst_tests = [
        test_normality_ks(data=data, clevel=clevel),
        test_normality_sw(data=data, clevel=clevel),
        test_normality_dp(data=data, clevel=clevel),
    ]
    # create dataframe
    return pd.DataFrame(
        {
            "Test": [e["Test"] for e in lst_tests],
            "Statistic": [e["Statistic"] for e in lst_tests],
            "p-value": [e["p-value"] for e in lst_tests],
            "is_normal": [e["is_normal"] for e in lst_tests],
            "Confidence": [e["Confidence"] for e in lst_tests],
        }
    )
