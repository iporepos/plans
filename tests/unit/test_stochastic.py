# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
Unit tests for the ``plans.stochastic`` package.

Golden values were recorded from the original implementations in
``plans.datasets.analyst`` before they moved to this package.

Features
--------
The test suite verifies that:

* The package source does not import other ``plans`` modules.
* Moved functions return the recorded golden values.
* Old static methods delegate and return identical results.
* Instance methods of ``Univar``, ``Bivar`` and ``Bayes`` still return them.
* Known bugs in binning and ``Bayes`` stay fixed.
* ``sample_gamma`` keeps its seeded results and validates its inputs.
* The ``arma`` model rebuilds series exactly and recovers known parameters.

"""
# IMPORTS
# ***********************************************************************
# import modules from other libs

# Native imports
# =======================================================================
import ast
import pathlib
import unittest
import warnings

# External imports
# =======================================================================
import numpy as np
import pandas as pd

# Project-level imports
# =======================================================================
import plans.geo
import plans.stochastic
from plans.datasets.analyst import Bayes, Bivar, Univar
from plans.stochastic import (
    arma,
    bayes,
    binning,
    curves,
    descriptive,
    frequency,
    metrics,
    normality,
    sampling,
)


# CONSTANTS
# ***********************************************************************
# define constants in uppercase

OBSERVED = np.array([1.0, 2.0, 2.0, 4.0, 7.0, 11.0, 3.5])
PREDICTED = np.array([1.5, 1.8, 2.6, 3.9, 8.0, 9.5, 3.0])

GOLDEN_METRICS = {
    "r": 0.9749524198004076,
    "rho": 0.9910312089651149,
    "R2": 0.9440537944284342,
    "RMSE": 0.7708992893275453,
    "MAE": 0.6285714285714287,
    "Bias": -0.6557377049180326,
}

DATA = np.array(
    [
        3.1,
        7.4,
        2.2,
        9.8,
        5.5,
        4.1,
        12.6,
        6.3,
        1.9,
        8.8,
        15.2,
        3.7,
        5.0,
        10.4,
        7.7,
        2.8,
        6.9,
        20.3,
        4.6,
        11.1,
    ]
)
RANKS = np.arange(start=1, stop=21)
TX = np.array([2.0, 10.0, 100.0])
EDGES = np.array([-1.0, 0.0, 5.0, 10.0, 15.0, 20.0, 25.0])

# curve fits stop at the solver tolerance, so they vary across library builds
TOL_EXACT = 1e-8
TOL_FIT = 1e-4

# size, first, last and sum of each output, flattened
GOLDEN = {
    "test_normality_ks": [4, 0.13010066682172883, 1.0, 2.875040153335374],
    "test_normality_sw": [4, 0.910011519786638, 0.0, 1.8737789959991225],
    "test_normality_dp": [4, 7.047887572247513, 0.0, 7.977370503458067],
    "get_tx": [3, 2.0, 99.99999999999991, 111.99999999999991],
    "gumbel_fx": [20, 0.07534259305171932, 0.9537450138007181, 11.047127162192178],
    "gumbel_tx": [20, 1.0814816303698669, 21.619290852053574, 2391.850331373526],
    "gumbel_freqfactor": [
        3,
        -0.16427204188374184,
        3.1366806436431847,
        4.276971814793655,
    ],
    "gumbel_se": [3, 0.8209329845348662, 3.5098100165085446, 6.198206683654961],
    "empirical_px": [20, 0.05, 1.0, 10.5],
    "weibull_px": [20, 0.047619047619047616, 0.9523809523809523, 10.0],
    "gringorten_px": [20, 0.027833001988071572, 0.9721669980119283, 10.0],
    "get_nbins_fd": [1, 5.0, 5.0, 5.0],
    "get_nbins_sturges": [1, 6.0, 6.0, 6.0],
    "get_nbins_scott": [1, 4.0, 4.0, 4.0],
    "get_nbins_density": [1, 8.0, 8.0, 8.0],
    "get_histogram": [12, 4.966666666666667, 1.0, 95.8],
    "get_bins_equal": [5, 1.9, 20.3, 55.5],
    "get_bins_quantiles": [5, 1.9, 20.3, 42.75],
    "classify_bins": [7, 0.0, 1.0, 4.0],
    "classify_scheme": [20, 0.0, 2.0, 20.0],
    "qqplot": [60, 1.9, 1.959963984540054, 159.4],
    "trace_variance": [40, 3.1, 21.632188365650972, 378.1586341349029],
    "sample_gamma": [8, 1.9758657874255257, 3.6786808210606616, 24.211363445759623],
    "sample_gamma_mode": [8, 56.313271184937136, 37.06049262132689, 338.77021307823503],
    "sample_gamma_bounds": [
        8,
        1.2846168281313812,
        6.737259118510652,
        37.18907041540918,
    ],
    "linear": [20, 7.2, 23.2, 318.8],
    "power": [20, 4.1509336299199, 21.044957828420564, 272.4741691471859],
    "power_zero": [20, 2.7290566135571463, 18.490747686343028, 231.78849517488948],
    "inst_normality": [12, 0.13010066682172883, 0.9, 12.726189652792565],
    "inst_frequency": [500, 0.0, 19.330999999999992, 10739.777],
    "inst_basic": [19, 20.0, 20.3, 305.69713223937003],
    "inst_weibull": [60, 20.3, 0.04761904761904767, 169.40000000000003],
    "inst_gumbel": [6263, 20.3, 0.9920277261185804, 635145.104738059],
    "fit_Linear": [6, 0.9943537021978035, 1.070282820716994e-07, 5.368793442336519],
    "fit_Power": [6, 0.9986176148937089, -0.021643485400669828, 4.149580706411347],
    "fit_Power_zero": [6, 0.9977128234354391, -0.5547522131860455, 4.011050160974915],
    "bayes": [609, 0.0, 0.9999999999999999, 530.7481007580849],
}


# FUNCTIONS
# ***********************************************************************


def _flatten(obj):
    """
    Flatten numeric content of a result into a list of floats.
    """
    if isinstance(obj, dict):
        return [v for k in obj for v in _flatten(obj=obj[k])]
    if isinstance(obj, (list, tuple)):
        return [v for e in obj for v in _flatten(obj=e)]
    if isinstance(obj, pd.DataFrame):
        ls = []
        for c in obj.columns:
            s = pd.to_numeric(obj[c], errors="coerce")
            ls = ls + [float(v) for v in s.values]
        return ls
    if isinstance(obj, np.ndarray):
        return [float(v) for v in obj.ravel()]
    if isinstance(obj, (bool, int, float, np.number, np.bool_)):
        return [float(obj)]
    return []


def fingerprint(obj):
    """
    Get size, first, last and sum of a result, ignoring NaN.
    """
    v = [e for e in _flatten(obj=obj) if not np.isnan(e)]
    return [len(v), v[0], v[-1], float(np.sum(a=v))]


def _trend(params):
    return {"start": params["start"], "slope": params["slope"]}


def get_univar():
    uv = Univar(name="g")
    uv.set_array(array=DATA)
    return uv


def fit_bivar(model_type):
    x = np.linspace(start=1, stop=10, num=20)
    y = 2.0 * np.power(x + 0.5, 1.3) + np.sin(x)
    bv = Bivar()
    bv.set_data(x=x, y=y)
    bv.fit(model_type=model_type)
    return bv.models[model_type]


def run_bayes():
    hyp = pd.DataFrame({"Name": ["H1"], "Min": [0.0], "Max": [10.0]})
    by = Bayes(df_hypotheses=hyp, nomenclature=None, gridsize=21)
    rng = np.random.default_rng(seed=3)
    for i in range(3):
        df = pd.DataFrame(
            {
                "E": rng.normal(loc=5, scale=1, size=200),
                "W": rng.uniform(low=0.5, high=1.5, size=200),
            }
        )
        by.conditionalize(dct_evidence={"H1": df})
    return by


def seeded_gamma(**kwargs):
    np.random.seed(7)
    return sampling.sample_gamma(**kwargs)


# outputs checked against golden values
CASES = {
    "test_normality_ks": lambda: normality.test_normality_ks(data=DATA, clevel=0.9),
    "test_normality_sw": lambda: normality.test_normality_sw(data=DATA, clevel=0.9),
    "test_normality_dp": lambda: normality.test_normality_dp(data=DATA, clevel=0.9),
    "get_tx": lambda: frequency.get_tx(fx=np.array([0.5, 0.9, 0.99])),
    "gumbel_fx": lambda: frequency.gumbel_fx(x=DATA, a=5.0, b=2.0),
    "gumbel_tx": lambda: frequency.gumbel_tx(x=DATA, a=5.0, b=2.0),
    "gumbel_freqfactor": lambda: frequency.gumbel_freqfactor(tx=TX),
    "gumbel_se": lambda: frequency.gumbel_se(std_sample=4.0, n_sample=20, tx=TX),
    "empirical_px": lambda: frequency.empirical_px(ranks=RANKS),
    "weibull_px": lambda: frequency.weibull_px(ranks=RANKS),
    "gringorten_px": lambda: frequency.gringorten_px(ranks=RANKS),
    "get_nbins_fd": lambda: binning.get_nbins_fd(data=DATA),
    "get_nbins_sturges": lambda: binning.get_nbins_sturges(data=DATA),
    "get_nbins_scott": lambda: binning.get_nbins_scott(data=DATA),
    "get_nbins_density": lambda: binning.get_nbins_density(
        n_units=2.5, data_range=[0, 20]
    ),
    "get_histogram": lambda: binning.get_histogram(data=DATA, bins=6),
    "get_bins_equal": lambda: binning.get_bins(data=DATA, n_bins=4, scheme="equal"),
    "get_bins_quantiles": lambda: binning.get_bins(
        data=DATA, n_bins=4, scheme="quantiles"
    ),
    "classify_bins": lambda: binning.classify(
        data=EDGES, bins=np.array([0.0, 10.0, 20.0])
    ),
    "classify_scheme": lambda: binning.classify(
        data=DATA, n_classes=3, scheme="quantiles"
    ),
    "qqplot": lambda: descriptive.qqplot(data=DATA),
    "trace_variance": lambda: descriptive.trace_variance(data=DATA),
    "sample_gamma": lambda: seeded_gamma(size=8),
    "sample_gamma_mode": lambda: seeded_gamma(
        size=8, shape_mode="symmetrical", scale=2
    ),
    "sample_gamma_bounds": lambda: seeded_gamma(size=8, n_min=0, n_max=10),
    "linear": lambda: curves.linear(x=DATA, c0=1.0, c1=2.0),
    "power": lambda: curves.power(x=DATA, c0=1.0, c1=1.5, c2=0.5),
    "power_zero": lambda: curves.power_zero(x=DATA, c0=1.5, c1=0.5),
    "inst_normality": lambda: get_univar().get_normality(clevel=0.9),
    "inst_frequency": lambda: get_univar().get_frequency(),
    "inst_basic": lambda: get_univar().get_basic_stats(),
    "inst_weibull": lambda: get_univar().get_cdf_weibull(),
    "inst_gumbel": lambda: get_univar().get_cdf_gumbel(),
    "fit_Linear": lambda: fit_bivar(model_type="Linear")["Metrics"],
    "fit_Power": lambda: fit_bivar(model_type="Power")["Metrics"],
    "fit_Power_zero": lambda: fit_bivar(model_type="Power_zero")["Metrics"],
    "bayes": lambda: [s["Omega"]["H1"] for s in run_bayes().steps],
}


# CLASSES
# ***********************************************************************


class TestIndependence(unittest.TestCase):

    def test_no_plans_imports(self):
        # intra-package relative imports have level > 0 and are allowed
        folder = pathlib.Path(plans.stochastic.__file__).parent
        for file in folder.glob("*.py"):
            tree = ast.parse(file.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                names = []
                if isinstance(node, ast.Import):
                    names = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom) and node.level == 0:
                    names = [node.module]
                for name in names:
                    with self.subTest(file=file.name, name=name):
                        self.assertNotEqual(name.split(".")[0], "plans")


class TestMetrics(unittest.TestCase):

    def test_golden(self):
        dc = metrics.get_metrics(observed=OBSERVED, predicted=PREDICTED)
        self.assertEqual(list(dc.keys()), list(GOLDEN_METRICS.keys()))
        for k in GOLDEN_METRICS:
            with self.subTest(metric=k):
                self.assertAlmostEqual(dc[k], GOLDEN_METRICS[k], places=12)

    def test_delegates(self):
        # correlations take x and y
        for name in ["pearson", "spearman"]:
            with self.subTest(name=name):
                self.assertEqual(
                    getattr(Bivar, name)(x=OBSERVED, y=PREDICTED),
                    getattr(metrics, name)(x=OBSERVED, y=PREDICTED),
                )
        # agreement takes observed and predicted
        for name in ["rsq", "rmse", "mae", "bias", "get_metrics"]:
            with self.subTest(name=name):
                self.assertEqual(
                    getattr(Bivar, name)(observed=OBSERVED, predicted=PREDICTED),
                    getattr(metrics, name)(observed=OBSERVED, predicted=PREDICTED),
                )

    def test_package_top(self):
        self.assertIs(plans.stochastic.rmse, metrics.rmse)


class TestGolden(unittest.TestCase):

    def test_cases_covered(self):
        self.assertEqual(set(CASES), set(GOLDEN))

    def test_golden(self):
        for key in CASES:
            with self.subTest(case=key):
                result = fingerprint(obj=CASES[key]())
                tol = TOL_FIT if key.startswith("fit_") else TOL_EXACT
                self.assertEqual(result[0], GOLDEN[key][0])
                for a, b in zip(result[1:], GOLDEN[key][1:]):
                    self.assertAlmostEqual(a, b, delta=tol * max(1.0, abs(b)))


class TestDelegates(unittest.TestCase):

    def test_univar_statics(self):
        ls_cases = [
            ("get_nbins_fd", binning, {"data": DATA}),
            ("get_bins", binning, {"data": DATA, "n_bins": 4}),
            ("classify", binning, {"data": DATA, "n_classes": 3}),
            ("quantiles_classify", binning, {"data": DATA, "n_classes": 3}),
            ("gumbel_tx", frequency, {"x": DATA, "a": 5.0, "b": 2.0}),
            ("weibull_px", frequency, {"ranks": RANKS}),
        ]
        for name, module, kwargs in ls_cases:
            with self.subTest(name=name):
                np.testing.assert_array_equal(
                    getattr(Univar, name)(**kwargs),
                    getattr(module, name)(**kwargs),
                )

    def test_univar_frames(self):
        pd.testing.assert_frame_equal(
            Univar.qqplot(data=DATA), descriptive.qqplot(data=DATA)
        )
        self.assertEqual(
            Univar.test_normality_sw(data=DATA),
            normality.test_normality_sw(data=DATA),
        )

    def test_old_names(self):
        import plans.datasets.analyst as analyst

        self.assertIs(analyst.power, curves.power)
        self.assertIs(plans.geo.normalize, sampling.normalize)


class TestBinning(unittest.TestCase):

    def test_nbins_by_rule(self):
        # these rules used to raise TypeError
        ls_cases = [
            ("sturges", binning.get_nbins_sturges),
            ("fd", binning.get_nbins_fd),
            ("scott", binning.get_nbins_scott),
        ]
        for rule, func in ls_cases:
            with self.subTest(rule=rule):
                self.assertEqual(
                    binning.get_nbins_by_rule(data=DATA, rule=rule),
                    func(data=DATA),
                )
        self.assertEqual(binning.get_nbins_by_rule(data=DATA), 10)
        self.assertEqual(binning.get_nbins_by_rule(data=DATA, rule="other"), 10)

    def test_histogram_by_rule(self):
        df = binning.get_histogram(data=DATA, bins=None, rule="sturges")
        self.assertEqual(len(df), binning.get_nbins_sturges(data=DATA))
        self.assertEqual(df["Count"].sum(), len(DATA))

    def test_quantiles_classify(self):
        # this function used to raise NameError
        result = binning.quantiles_classify(data=DATA, n_classes=4)
        self.assertEqual(set(result), {0, 1, 2, 3})
        self.assertEqual(np.sum(a=result == 0), 5)

    def test_classify_edges(self):
        # a value on an edge goes to the class above; extremes are clamped
        result = binning.classify(
            data=np.array([-1.0, 0.0, 10.0, 15.0, 20.0, 25.0]),
            bins=np.array([0.0, 10.0, 20.0]),
        )
        self.assertListEqual(list(result), [0, 0, 1, 1, 1, 1])


class TestSampling(unittest.TestCase):

    def test_rng(self):
        a = sampling.sample_gamma(size=8, rng=np.random.default_rng(seed=1))
        b = sampling.sample_gamma(size=8, rng=np.random.default_rng(seed=1))
        c = sampling.sample_gamma(size=8, rng=np.random.default_rng(seed=2))
        np.testing.assert_array_equal(a, b)
        self.assertFalse(np.array_equal(a, c))

    def test_bounds(self):
        v = sampling.sample_gamma(
            size=50, n_min=0, n_max=10, rng=np.random.default_rng(seed=1)
        )
        self.assertEqual(np.min(a=v), 0)
        self.assertAlmostEqual(np.max(a=v), 10)

    def test_invalid(self):
        ls_cases = [
            {"size": 5, "shape": 0},
            {"size": 5, "scale": 0},
            {"size": 5, "n_min": 2, "n_max": 1},
            {"size": 5, "shape_mode": "unknown"},
            {"size": 1},
        ]
        for kwargs in ls_cases:
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(ValueError):
                    sampling.sample_gamma(**kwargs)

    def test_scale_warning(self):
        with self.assertWarns(UserWarning):
            sampling.sample_gamma(size=5, scale=2, n_min=0, n_max=1)


class TestBayes(unittest.TestCase):

    def test_conditionalize(self):
        # this method used to raise ValueError under pandas 3
        by = run_bayes()
        self.assertEqual(len(by.steps), 4)
        df = by.steps[3]["Omega"]["H1"]
        self.assertAlmostEqual(df[by.spost].sum(), 1.0)
        self.assertAlmostEqual(df[by.spost + "_acc"].values[-1], 1.0)
        # evidence narrows the band as steps accumulate
        ls_bands = [by.steps[i]["Bands"]["H1"][by.spost] for i in [1, 3]]
        widths = [b["p95"] - b["p05"] for b in ls_bands]
        self.assertLess(widths[1], widths[0])

    def test_posterior(self):
        result = bayes.get_posterior(
            prior=np.array([0.5, 0.5]), likelihood=np.array([0.2, 0.6])
        )
        np.testing.assert_allclose(result, [0.25, 0.75])

    def test_band_empty(self):
        lo, hi = bayes.get_band(
            grid=np.array([1.0, 2.0]),
            accumulated=np.array([0.5, 1.0]),
            lower=0.6,
            upper=0.7,
        )
        self.assertTrue(np.isnan(lo) and np.isnan(hi))


class TestArma(unittest.TestCase):

    def setUp(self):
        self.temperature = arma.make_params(
            period=12,
            start=15.0,
            slope=0.01,
            amplitude=10.0,
            phase=3.0,
            phi=0.5,
            sigma=1.0,
        )
        self.rain = arma.make_params(
            period=12,
            start=100.0,
            amplitude=300.0,
            phase=2.0,
            power=3.0,
            phi=0.3,
            sigma=5.0,
        )

    def test_identity(self):
        x = arma.build(params=self.temperature, n=240, seed=1)
        shocks = arma.decompose(x=x, params=self.temperature)["shocks"]
        rebuilt = arma.build(params=self.temperature, n=240, shocks=shocks)
        np.testing.assert_allclose(rebuilt, x, atol=1e-10)

    def test_seed(self):
        a = arma.build(params=self.temperature, n=60, seed=1)
        b = arma.build(params=self.temperature, n=60, seed=1)
        c = arma.build(params=self.temperature, n=60, seed=2)
        np.testing.assert_array_equal(a, b)
        self.assertFalse(np.array_equal(a, c))

    def test_common_random_numbers(self):
        # a change in slope only adds the line to the same noise
        steeper = dict(self.temperature, slope=0.11)
        a = arma.build(params=self.temperature, n=60, seed=1)
        b = arma.build(params=steeper, n=60, seed=1)
        np.testing.assert_allclose(b - a, 0.1 * np.arange(start=0, stop=60))
        # after the first step, draws stay aligned when phi changes
        rng_a = np.random.default_rng(seed=1)
        rng_b = np.random.default_rng(seed=1)
        r_a = arma.simulate_ar1(n=30, phi=0.5, sigma=1.0, rng=rng_a)
        r_b = arma.simulate_ar1(n=30, phi=0.0, sigma=1.0, rng=rng_b)
        np.testing.assert_allclose(r_a[1:] - 0.5 * r_a[:-1], r_b[1:])

    def test_shape_mean(self):
        self.assertAlmostEqual(arma.shape_mean(power=1), 0.5)
        self.assertAlmostEqual(arma.shape_mean(power=2), 0.375)
        for power in [1.0, 2.5, 7.0]:
            with self.subTest(power=power):
                g = arma.cycle_shape(n=1000, period=1000, phase=0, power=power)
                self.assertAlmostEqual(np.mean(a=g), arma.shape_mean(power=power))

    def test_cycle(self):
        s = arma.cycle_component(n=12, amplitude=10.0, period=12, phase=3, power=1)
        expected = 5 * np.cos(2 * np.pi * (np.arange(start=0, stop=12) - 3) / 12)
        np.testing.assert_allclose(s, expected, atol=1e-12)
        s = arma.cycle_component(n=24, amplitude=10.0, period=24, phase=5, power=4)
        self.assertAlmostEqual(np.mean(a=s), 0.0)
        self.assertEqual(np.argmax(a=s), 5)

    def test_stationary(self):
        phi, sigma = 0.9, 2.0
        expected = sigma**2 / (1 - phi**2)
        r = arma.simulate_ar1(
            n=200000, phi=phi, sigma=sigma, rng=np.random.default_rng(seed=1)
        )
        self.assertAlmostEqual(np.var(a=r) / expected, 1.0, delta=0.05)
        # the variance holds from the first step, across many short runs
        r_0 = [
            arma.simulate_ar1(
                n=2, phi=phi, sigma=sigma, rng=np.random.default_rng(seed=i)
            )[0]
            for i in range(4000)
        ]
        self.assertAlmostEqual(np.var(a=r_0) / expected, 1.0, delta=0.1)

    def test_recovery(self):
        for truth in [self.temperature, self.rain]:
            x = arma.build(params=truth, n=2400, seed=1)
            fit = arma.fit_params(x=x, period=12)
            with self.subTest(power=truth["power"]):
                self.assertAlmostEqual(
                    fit["amplitude"] / truth["amplitude"], 1.0, delta=0.05
                )
                self.assertAlmostEqual(fit["power"], truth["power"], delta=0.3)
                self.assertAlmostEqual(fit["phase"], truth["phase"], delta=0.2)
                self.assertAlmostEqual(fit["phi"], truth["phi"], delta=0.06)
                self.assertAlmostEqual(fit["sigma"] / truth["sigma"], 1.0, delta=0.06)

    def test_phase_wraps(self):
        truth = dict(self.temperature, phase=11.5, sigma=0.1)
        x = arma.build(params=truth, n=240, seed=1)
        fit = arma.fit_params(x=x, period=12)
        self.assertGreaterEqual(fit["phase"], 0)
        self.assertLess(fit["phase"], 12)
        self.assertAlmostEqual(fit["phase"], 11.5, delta=0.2)

    def test_fit_errors(self):
        x = arma.build(params=self.temperature, n=60, seed=1)
        with self.assertRaises(ValueError):
            arma.fit_params(x=x[:35], period=12)
        with self.assertRaises(ValueError):
            arma.fit_params(x=x, period=0)
        x[5] = np.nan
        with self.assertRaises(ValueError):
            arma.fit_params(x=x, period=12)

    def test_phi_errors(self):
        for phi in [1.0, -1.0, 1.5]:
            with self.subTest(phi=phi):
                with self.assertRaises(ValueError):
                    arma.build(params=dict(self.temperature, phi=phi), n=10)
                with self.assertRaises(ValueError):
                    arma.make_params(period=12, phi=phi)

    def test_conversions(self):
        start = arma.start_from_average(average=15.0, slope=0.5, n=11)
        self.assertAlmostEqual(start, 12.5)
        self.assertAlmostEqual(
            arma.average_from_start(start=start, slope=0.5, n=11), 15.0
        )
        self.assertAlmostEqual(arma.slope_from_end(start=1.0, end=6.0, n=11), 0.5)
        self.assertAlmostEqual(
            arma.slope_from_cycle_change(change=0.04, period=12), 0.04 / 12
        )

    def test_make_params_modes(self):
        # worked example: monthly temperature with a yearly change
        p = arma.make_params(
            period=12,
            average=15.0,
            n=240,
            cycle_change=0.04,
            baseline=10.0,
            topline=20.0,
        )
        self.assertAlmostEqual(p["amplitude"], 10.0)
        self.assertAlmostEqual(p["slope"], 0.04 / 12)
        self.assertAlmostEqual(np.mean(a=arma.trend_line(n=240, **_trend(p))), 15.0)
        ls_invalid = [
            {"start": 1.0, "average": 1.0, "n": 10},
            {"slope": 1.0, "end": 1.0, "start": 0.0, "n": 10},
            {"slope": 1.0, "cycle_change": 1.0},
            {"amplitude": 1.0, "baseline": 0.0, "topline": 1.0},
            {"baseline": 0.0},
            {"average": 1.0},
            {"end": 1.0, "n": 10},
        ]
        for kwargs in ls_invalid:
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(ValueError):
                    arma.make_params(period=12, **kwargs)

    def test_stored_form_ignores_length(self):
        p = arma.make_params(period=12, start=1.0, end=11.0, n=11)
        short = arma.build(params=dict(p, sigma=0.0), n=11, seed=1)
        longer = arma.build(params=dict(p, sigma=0.0), n=21, seed=1)
        np.testing.assert_allclose(longer[:11], short)
        self.assertAlmostEqual(longer[-1], 21.0)

    def test_describe(self):
        s = arma.describe(params=self.temperature, n=240)
        for label in ["baseline", "topline", "slope per cycle", "floor", "phi"]:
            self.assertIn(label, s)

    def test_floor_warning(self):
        # the floor sits at trend - amplitude * shape mean
        low = arma.make_params(period=12, start=1.0, amplitude=10.0)
        self.assertAlmostEqual(arma.get_floor(params=low, n=12), -4.0)
        with self.assertWarns(UserWarning):
            s = arma.describe(params=low, n=12, positive=True)
        self.assertIn("WARNING", s)
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            arma.describe(params=low, n=12)
            arma.describe(params=dict(low, start=6.0), n=12, positive=True)

    def test_float_period(self):
        truth = dict(self.temperature, period=12.5)
        x = arma.build(params=truth, n=1000, seed=1)
        fit = arma.fit_params(x=x, period=12.5)
        self.assertEqual(fit["period"], 12.5)
        self.assertAlmostEqual(fit["amplitude"] / 10.0, 1.0, delta=0.05)

    def test_package_top(self):
        self.assertIs(plans.stochastic.fit_params, arma.fit_params)


# SCRIPT
# ***********************************************************************
# standalone behaviour as a script
if __name__ == "__main__":
    # Script section
    # ===================================================================
    unittest.main()
