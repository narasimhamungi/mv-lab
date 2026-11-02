"""PD model validation on loan-level outcomes: discrimination, calibration, stability.

* Discrimination: AUC (Mann-Whitney) with a bootstrap interval; Gini = 2 AUC - 1.
* Calibration by grade: the Jeffreys test the ECB's guide to internal models (TRIM) describes for PD
  back-testing. With D defaults among N loans, the posterior for the true default rate is
  Beta(D + 1/2, N - D + 1/2); the one-sided p-value is P(rate <= mean predicted PD). A small p-value
  says the grade's PD is too low.
* Calibration overall: Hosmer-Lemeshow on deciles of predicted PD (chi-square, groups - 2 df) and the
  Spiegelhalter z-test, which does not depend on a grouping.
* Stability: population stability index between two score distributions.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats


def auc(y, score) -> float:
    y = np.asarray(y, dtype=int)
    s = np.asarray(score, dtype=float)
    ranks = stats.rankdata(s)
    n1 = y.sum()
    n0 = len(y) - n1
    if n1 == 0 or n0 == 0:
        return float("nan")
    return float((ranks[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def auc_interval(y, score, draws: int = 200, seed: int = 7, level: float = 0.95) -> tuple[float, float]:
    y = np.asarray(y, dtype=int)
    s = np.asarray(score, dtype=float)
    rng = np.random.default_rng(seed)
    vals = []
    for _ in range(draws):
        i = rng.integers(0, len(y), len(y))
        vals.append(auc(y[i], s[i]))
    lo, hi = np.nanquantile(vals, [(1 - level) / 2, 1 - (1 - level) / 2])
    return float(lo), float(hi)


def jeffreys(defaults: int, n: int, pd_mean: float) -> float:
    """One-sided p-value of H0: the true default rate is at most the predicted PD."""
    return float(stats.beta.cdf(pd_mean, defaults + 0.5, n - defaults + 0.5))


def grade_table(df: pd.DataFrame, pd_col: str, y_col: str, grade_col: str) -> pd.DataFrame:
    g = df.groupby(grade_col, observed=True).agg(n=(y_col, "size"), defaults=(y_col, "sum"), pd_mean=(pd_col, "mean"))
    g["default_rate"] = g["defaults"] / g["n"]
    g["jeffreys_p"] = [jeffreys(int(d), int(n), float(p)) for d, n, p in zip(g["defaults"], g["n"], g["pd_mean"])]
    g["binomial_p"] = [float(stats.binom.sf(int(d) - 1, int(n), float(p))) for d, n, p in
                       zip(g["defaults"], g["n"], g["pd_mean"])]
    return g


def hosmer_lemeshow(y, pd_hat, groups: int = 10) -> dict:
    df = pd.DataFrame({"y": np.asarray(y, dtype=int), "p": np.asarray(pd_hat, dtype=float)})
    df["g"] = pd.qcut(df["p"].rank(method="first"), groups, labels=False)
    t = df.groupby("g").agg(n=("y", "size"), obs=("y", "sum"), exp=("p", "sum"))
    pbar = t["exp"] / t["n"]
    stat = float((((t["obs"] - t["exp"]) ** 2) / (t["n"] * pbar * (1 - pbar))).sum())
    return {"statistic": stat, "df": groups - 2, "p_value": float(stats.chi2.sf(stat, groups - 2))}


def spiegelhalter(y, pd_hat) -> dict:
    y = np.asarray(y, dtype=float)
    p = np.clip(np.asarray(pd_hat, dtype=float), 1e-12, 1 - 1e-12)
    num = np.sum((y - p) * (1 - 2 * p))
    den = np.sqrt(np.sum(((1 - 2 * p) ** 2) * p * (1 - p)))
    z = float(num / den)
    return {"z": z, "p_value": float(2 * stats.norm.sf(abs(z)))}


def psi(expected, actual, bins: int = 10) -> float:
    e = np.asarray(expected, dtype=float)
    a = np.asarray(actual, dtype=float)
    edges = np.unique(np.quantile(e, np.linspace(0, 1, bins + 1)))
    edges[0], edges[-1] = -np.inf, np.inf
    pe = np.histogram(e, edges)[0] / len(e)
    pa = np.histogram(a, edges)[0] / len(a)
    pe, pa = np.clip(pe, 1e-6, None), np.clip(pa, 1e-6, None)
    return float(np.sum((pa - pe) * np.log(pa / pe)))
