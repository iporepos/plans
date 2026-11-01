# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
r"""
Exceedance probabilities, return periods and the Gumbel model.

Formulas use :math:`r` for the rank (1 is the largest value), :math:`n` for the sample
size, :math:`s` for the standard deviation and :math:`T` for the return period.
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
    "get_tx",
    "gumbel_fx",
    "gumbel_tx",
    "gumbel_freqfactor",
    "gumbel_se",
    "empirical_px",
    "weibull_px",
    "gringorten_px",
    "get_frequency",
    "get_cdf_weibull",
    "get_cdf_gumbel",
]


# FUNCTIONS
# ***********************************************************************


def get_tx(fx):
    r"""
    Simple function for computing the Return Period from the CDF

    .. math::

        T = \frac{1}{1 - F}

    :param fx: CDF (FX)
    :type fx: float | :class:`numpy.ndarray`
    :return: Return Period
    :rtype: float | :class:`numpy.ndarray`
    """
    return 1 / (1 - fx)


def gumbel_fx(x, a, b):
    r"""
    Gumbel probability distribution F(X)

    .. math::

        F(x) = \exp\left[ -\exp\left( -\frac{x - a}{b} \right) \right]

    :param x: function inputs
    :type x: float | :class:`numpy.ndarray`
    :param a: distribution parameter a
    :type a: float
    :param b: distribution parameter b
    :type b: float
    :return: function output
    :rtype: float | :class:`numpy.ndarray`
    """
    aux_1 = (x - a) / b
    aux_2 = np.exp(-aux_1)
    g_fx = np.exp(-aux_2)
    return g_fx


def gumbel_tx(x, a, b):
    r"""
    Gumbel return period distribution T(X)

    .. math::

        T(x) = \frac{1}{1 - F(x)}

    :param x: function inputs
    :type x: float | :class:`numpy.ndarray`
    :param a: distribution parameter a
    :type a: float
    :param b: distribution parameter b
    :type b: float
    :return: function output
    :rtype: float | :class:`numpy.ndarray`
    """
    g_fx = gumbel_fx(x=x, a=a, b=b)
    return get_tx(fx=g_fx)


def gumbel_freqfactor(tx=2):
    r"""
    Gumbel Frequency Factor K(T)

    .. math::

        K_T = -\frac{\sqrt{6}}{\pi}
        \left[ 0.5772 + \ln \ln \left( \frac{T}{T - 1} \right) \right]

    :param tx: return period T
    :type tx: float | :class:`numpy.ndarray`
    :return: function output
    :rtype: float | :class:`numpy.ndarray`
    """
    aux1 = tx / (tx - 1)
    aux2 = np.log(aux1)
    aux3 = np.log(aux2)
    aux4 = 0.5772 + aux3
    aux5 = -np.sqrt(6) * aux4 / np.pi
    return aux5


def gumbel_se(std_sample, n_sample, tx):
    r"""
    Gumbel Standard Error for the MM fitted Gumbel function

    .. math::

        S_e = \frac{s}{\sqrt{n}} \sqrt{1 + 1.14 K_T + 1.1 K_T^2}

    :param std_sample: sample standard deviation
    :type std_sample: float
    :param n_sample: sample size
    :type n_sample: int
    :param tx: return period T
    :type tx: float | :class:`numpy.ndarray`
    :return: function output
    :rtype: float | :class:`numpy.ndarray`
    """
    aux1 = std_sample / np.sqrt(n_sample)
    k = gumbel_freqfactor(tx=tx)
    aux2 = 1 + (1.14 * k) + (1.1 * np.square(k))
    aux3 = np.sqrt(aux2)
    return aux1 * aux3


def empirical_px(ranks):
    r"""
    Get the empirical exceedance probability P(X)

    .. math::

        P(X) = \frac{r}{n}

    :param ranks: vector of ranks
    :type ranks: :class:`numpy.ndarray`
    :return: empirical exceedance probability P(X)
    :rtype: :class:`numpy.ndarray`
    """
    return ranks / len(ranks)


def weibull_px(ranks):
    r"""
    Get the Weibull exceedance probability P(X)

    .. math::

        P(X) = \frac{r}{n + 1}

    :param ranks: vector of ranks
    :type ranks: :class:`numpy.ndarray`
    :return: Weibull exceedance probability P(X)
    :rtype: :class:`numpy.ndarray`
    """
    return ranks / (len(ranks) + 1)


def gringorten_px(ranks):
    r"""
    Get the Gringorten exceedance probability P(X)

    .. math::

        P(X) = \frac{r - 0.44}{n + 0.12}

    :param ranks: vector of ranks
    :type ranks: :class:`numpy.ndarray`
    :return: Gringorten exceedance probability P(X)
    :rtype: :class:`numpy.ndarray`
    """
    return (ranks - 0.44) / (len(ranks) + 0.12)


def get_frequency(data):
    """
    Get data frequencies.

    :param data: vector of data without nan values
    :type data: :class:`numpy.ndarray`
    :return: result dataframe
    :rtype: :class:`pandas.DataFrame`
    """
    # compute percentiles intevarls
    vct_percentiles = np.arange(start=0, stop=100)

    # get CFC values
    vct_cfc = np.percentile(a=data, q=vct_percentiles)

    # reverse to get exceedance
    vct_exeed = 100 - vct_percentiles

    # get count
    vct_count = np.histogram(a=data, bins=len(vct_percentiles))[0]

    # get empirical prob in the histogram
    vct_empprob = vct_count / np.sum(a=vct_count)

    return pd.DataFrame(
        {
            "Percentiles": vct_percentiles,
            "Exceedance": vct_exeed,
            "Frequency": vct_count,
            "Empirical Probability": vct_empprob,
            "Values": vct_cfc,
        }
    )


def get_cdf_weibull(data):
    r"""
    Get the Weibull model for the data.

    .. math::

        P(X) = \frac{r}{n + 1}, \qquad F(X) = 1 - P(X)

    :param data: vector of data without nan values
    :type data: :class:`numpy.ndarray`
    :return: model dataframe
    :rtype: :class:`pandas.DataFrame`
    """
    v = np.sort(a=data)
    vr = v[::-1]
    r = np.arange(start=0, stop=len(data)) + 1
    px = weibull_px(ranks=r)

    return pd.DataFrame({"Data": vr, "P(X)": px, "F(X)": 1 - px})


def get_cdf_gumbel(df, varfield):
    r"""
    Get the Gumbel CDF for the data (it assumes that is a maxima dataset).

    Stages by return period use the frequency factor and the standard error, with
    Student's t bands at confidence :math:`c`:

    .. math::

        x_T = \bar{x} + K_T s, \qquad x_T \pm t_{(1 + c) / 2, \, n - 1} \, S_e

    :param df: dataframe without nan values. Other columns are kept in the output.
    :type df: :class:`pandas.DataFrame`
    :param varfield: name of the variable column
    :type varfield: str
    :return: multiple results from the assessment. Keys: Data, Data_T(X), Data_QQ, Metadata
    :rtype: dict
    """
    from scipy import stats

    # get extra values
    df = df.sort_values(by=varfield, ascending=False).reset_index(drop=True)
    df["Rank"] = df.index + 1
    df["P(X)_Empirical"] = empirical_px(ranks=df["Rank"].values)
    df["P(X)_Weibull"] = weibull_px(ranks=df["Rank"].values)
    df["T(X)_Weibull"] = 1 / df["P(X)_Weibull"]
    df["P(X)_Gringorten"] = gringorten_px(ranks=df["Rank"].values)

    # ---- model Gumbel using the method of moments ----

    # using scipy
    # Fit a Gumbel distribution to the data
    params = stats.gumbel_r.fit(data=df[varfield].values, method="MM")  # MLM or MM
    gumbel_a = params[0]
    gumbel_b = params[1]

    # compute fit gumbel values
    df["P(X)_Gumbel"] = 1 - gumbel_fx(x=df[varfield].values, a=gumbel_a, b=gumbel_b)
    # return period
    df["T(X)_Gumbel"] = 1 / df["P(X)_Gumbel"]

    # compute uncertainty 90% bands for T(X) in the Annual Series
    t = stats.t.ppf(q=(1 + 0.9) / 2, df=len(df) - 1)
    vct_se = gumbel_se(
        std_sample=np.std(a=df[varfield].values),
        n_sample=len(df),
        tx=df["T(X)_Gumbel"],
    )
    # Standar error analysis
    df["T(X)_Gumbel_SE90"] = t * vct_se
    h_max = df[varfield] + df["T(X)_Gumbel_SE90"]
    h_min = df[varfield] - df["T(X)_Gumbel_SE90"]
    df["T(X)_Gumbel_P05"] = gumbel_tx(x=h_min, a=gumbel_a, b=gumbel_b)
    df["T(X)_Gumbel_P95"] = gumbel_tx(x=h_max, a=gumbel_a, b=gumbel_b)

    # -------- Return Period analysis

    # evely spaced
    txs = np.arange(start=2, stop=1001, step=1)
    k = gumbel_freqfactor(tx=txs)

    # apply reverse formula
    stages = np.mean(a=df[varfield]) + k * np.std(a=df[varfield])

    # get standard error
    vct_se = gumbel_se(std_sample=np.std(a=df[varfield]), n_sample=len(df), tx=txs)
    # compute 50% uncertainty bands by Student's t distribution
    t_50 = stats.t.ppf(q=(1 + 0.5) / 2, df=len(df) - 1)
    h_range_50 = t_50 * vct_se

    # compute 90% uncertainty bands by Student's t distribution
    t_90 = stats.t.ppf(q=(1 + 0.9) / 2, df=len(df) - 1)
    h_range_90 = t_90 * vct_se

    # Set TX dataframe
    df_tx = pd.DataFrame(
        {
            "T(X)_Gumbel": txs,
            f"{varfield}": stages,
            f"{varfield}_P25": stages - h_range_50,
            f"{varfield}_P75": stages + h_range_50,
            f"{varfield}_P05": stages - h_range_90,
            f"{varfield}_P95": stages + h_range_90,
        }
    )

    # -------- QQ plots
    qq, qq_params = stats.probplot(
        x=df[varfield].values, dist="gumbel_r", sparams=params
    )
    # Set QQ dataframe
    df_qq = pd.DataFrame({varfield: qq[1], "T-Q": qq[0]})

    # -------- Goodness of fit tests
    ks_stat, ks_p_value = stats.kstest(
        rvs=df[varfield].values, cdf="gumbel_r", args=params
    )
    # accept Null Hypothesis
    is_gumbel = True
    if ks_p_value <= 0.05:
        is_gumbel = False

    # -------- Metadata dataframe
    df_meta = pd.DataFrame(
        {
            "Metadata": [
                "N",
                "Gumbel a",
                "Gumbel b",
                "KS-test s-value",
                "KS-test p-value",
                "KS-test Is Gumbel (NullH)",
                "QQ-plot c0",
                "QQ plot c1",
                "QQ-plot r2",
            ],
            "Value": [
                len(df),
                gumbel_a,
                gumbel_b,
                ks_stat,
                ks_p_value,
                is_gumbel,
                qq_params[1],
                qq_params[0],
                qq_params[2],
            ],
        }
    )

    return {"Data": df, "Data_T(X)": df_tx, "Data_QQ": df_qq, "Metadata": df_meta}
