"""VaR coverage tests on a series of exception indicators.

* Kupiec (1995) proportion of failures: is the exception rate the 1 - alpha the model claims?
* Christoffersen (1998) independence: do exceptions cluster (first-order Markov alternative)?
* Conditional coverage: the two together, chi-square with 2 degrees of freedom.
* Basel traffic light: exceptions in each trailing 250-day window against the 99% zones
  (green 0-4, yellow 5-9, red 10 or more), reported as the share of windows in each zone.

Inputs are boolean exception series in date order; nothing here knows how the VaR was made.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from scipy import stats


def _xlogy(x: float, y: float) -> float:
    return 0.0 if x == 0 else x * math.log(y)


@dataclass(frozen=True)
class TestResult:
    name: str
    statistic: float | None
    p_value: float | None
    detail: str

    def rejected(self, level: float = 0.05) -> bool | None:
        return None if self.p_value is None else self.p_value < level


def kupiec_pof(exceptions, alpha: float) -> TestResult:
    x = np.asarray(exceptions, dtype=bool)
    n, k = len(x), int(x.sum())
    p = 1 - alpha
    if n == 0:
        return TestResult("Kupiec POF", None, None, "no forecasts")
    ll0 = _xlogy(n - k, 1 - p) + _xlogy(k, p)
    phat = k / n
    ll1 = _xlogy(n - k, 1 - phat) + _xlogy(k, phat)
    lr = -2 * (ll0 - ll1)
    return TestResult("Kupiec POF", lr, float(stats.chi2.sf(lr, 1)),
                      f"{k} exceptions in {n} forecasts, {n * p:.1f} expected")


def christoffersen_independence(exceptions) -> TestResult:
    x = np.asarray(exceptions, dtype=bool).astype(int)
    if len(x) < 2:
        return TestResult("Christoffersen independence", None, None, "too few forecasts")
    prev, cur = x[:-1], x[1:]
    n00 = int(((prev == 0) & (cur == 0)).sum())
    n01 = int(((prev == 0) & (cur == 1)).sum())
    n10 = int(((prev == 1) & (cur == 0)).sum())
    n11 = int(((prev == 1) & (cur == 1)).sum())
    if n01 + n11 == 0:
        return TestResult("Christoffersen independence", 0.0, 1.0, "no exceptions after the first day")
    pi0 = n01 / (n00 + n01) if n00 + n01 else 0.0
    pi1 = n11 / (n10 + n11) if n10 + n11 else 0.0
    pi = (n01 + n11) / (n00 + n01 + n10 + n11)
    ll0 = _xlogy(n00 + n10, 1 - pi) + _xlogy(n01 + n11, pi)
    ll1 = _xlogy(n00, 1 - pi0) + _xlogy(n01, pi0) + _xlogy(n10, 1 - pi1) + _xlogy(n11, pi1)
    lr = -2 * (ll0 - ll1)
    return TestResult("Christoffersen independence", lr, float(stats.chi2.sf(lr, 1)),
                      f"{n11} exceptions followed an exception; exception rate after an exception day {pi1:.1%} "
                      f"against {pi0:.1%} otherwise")


def conditional_coverage(exceptions, alpha: float) -> TestResult:
    uc, ind = kupiec_pof(exceptions, alpha), christoffersen_independence(exceptions)
    if uc.statistic is None or ind.statistic is None:
        return TestResult("Conditional coverage", None, None, "not computable")
    lr = uc.statistic + ind.statistic
    return TestResult("Conditional coverage", lr, float(stats.chi2.sf(lr, 2)), "Kupiec + independence, 2 df")


def traffic_light(exceptions, window: int = 250) -> dict:
    """Share of trailing windows in each Basel zone (99% VaR zones), and the latest window's count."""
    x = np.asarray(exceptions, dtype=int)
    if len(x) < window:
        return {"windows": 0, "green": None, "yellow": None, "red": None, "latest": None, "max": None}
    counts = np.convolve(x, np.ones(window, dtype=int), mode="valid")
    return {"windows": len(counts), "green": float((counts <= 4).mean()),
            "yellow": float(((counts >= 5) & (counts <= 9)).mean()), "red": float((counts >= 10).mean()),
            "latest": int(counts[-1]), "max": int(counts.max())}
