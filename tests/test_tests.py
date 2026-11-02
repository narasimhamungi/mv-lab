import math

import numpy as np
import pytest

from mvlab import coverage, es_tests, pd_tests


def test_kupiec_matches_the_likelihood_ratio_by_hand():
    exc = np.zeros(250, bool)
    exc[:8] = True
    r = coverage.kupiec_pof(exc, 0.99)
    p, ph = 0.01, 8 / 250
    lr = -2 * ((242 * math.log(1 - p) + 8 * math.log(p)) - (242 * math.log(1 - ph) + 8 * math.log(ph)))
    assert r.statistic == pytest.approx(lr) and r.p_value == pytest.approx(0.00542, abs=5e-5)
    assert coverage.kupiec_pof(np.zeros(250, bool), 0.99).p_value == pytest.approx(0.02498, abs=5e-5)


def test_independence_sees_clustering_and_not_spread():
    spread = np.zeros(1000, bool)
    spread[::100] = True
    clustered = np.zeros(1000, bool)
    clustered[500:510] = True
    assert coverage.christoffersen_independence(spread).p_value > 0.5
    assert coverage.christoffersen_independence(clustered).p_value < 0.001


def test_traffic_light_zones():
    x = np.zeros(300, bool)
    x[-12:] = True                                         # 12 exceptions in the latest window: red
    tl = coverage.traffic_light(x)
    assert tl["windows"] == 51 and tl["latest"] == 12 and tl["red"] > 0
    assert coverage.traffic_light(np.zeros(100, bool))["windows"] == 0


def test_z2_is_near_zero_for_a_right_es_and_red_for_a_low_one():
    rng = np.random.default_rng(1)
    loss = rng.standard_normal(20000)
    from scipy import stats
    a = 0.975
    var = np.full_like(loss, stats.norm.ppf(a))
    es = np.full_like(loss, stats.norm.pdf(stats.norm.ppf(a)) / (1 - a))
    assert abs(es_tests.acerbi_szekely_z2(loss, var, es, a)["z2"]) < 0.1
    assert es_tests.acerbi_szekely_z2(loss, 0.7 * var, 0.7 * es, a)["zone"] == "red"
    ok = es_tests.exceedance_residuals(loss, var, es)
    bad = es_tests.exceedance_residuals(loss, var, 0.8 * es)
    assert ok["p_value"] > 0.05 and bad["p_value"] < 0.01


def test_auc_against_counting_pairs():
    rng = np.random.default_rng(3)
    y = rng.integers(0, 2, 300)
    s = rng.standard_normal(300) + y
    pos, neg = s[y == 1], s[y == 0]
    brute = np.mean([(p > n) + 0.5 * (p == n) for p in pos for n in neg])
    assert pd_tests.auc(y, s) == pytest.approx(brute)


def test_jeffreys_direction():
    assert pd_tests.jeffreys(30, 1000, 0.01) < 0.001          # 3% observed against a 1% PD: PD too low
    assert pd_tests.jeffreys(5, 1000, 0.01) > 0.9             # 0.5% observed: not too low


def test_hosmer_lemeshow_and_spiegelhalter_accept_a_calibrated_model():
    rng = np.random.default_rng(9)
    p = rng.uniform(0.01, 0.3, 20000)
    y = rng.random(20000) < p
    assert pd_tests.hosmer_lemeshow(y, p)["p_value"] > 0.01
    assert pd_tests.spiegelhalter(y, p)["p_value"] > 0.01
    assert pd_tests.hosmer_lemeshow(y, p * 0.7)["p_value"] < 0.001


def test_psi_zero_for_same_distribution_and_large_for_a_shift():
    rng = np.random.default_rng(2)
    a = rng.standard_normal(5000)
    assert pd_tests.psi(a, a) == pytest.approx(0.0, abs=1e-9)
    assert pd_tests.psi(a, a + 1.0) > 0.25
