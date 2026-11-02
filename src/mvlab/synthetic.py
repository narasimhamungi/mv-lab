"""Invented inputs with known defects, so every test can be shown to catch what it is meant to catch.

VaR: a well-specified method, one whose VaR is 25% too low, and one that is right on average but reacts
to nothing, so its exceptions cluster in a high-volatility regime.
PD: a model whose PD is right in development and too low by a third in the out-of-time year.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats


def var_backtest(days: int = 1500, seed: int = 11) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2019-01-02", periods=days)
    vol = np.where((np.arange(days) // 250) % 3 == 2, 2.0, 1.0)          # every third year is turbulent
    pnl = rng.standard_normal(days) * vol * 10_000
    rows = []
    for alpha in (0.99, 0.975):
        z, tail = stats.norm.ppf(alpha), stats.norm.pdf(stats.norm.ppf(alpha)) / (1 - alpha)
        for method, var_vol in (("well_specified", vol), ("too_low", 0.75 * vol),
                                ("static", np.full(days, np.sqrt((vol ** 2).mean())))):
            var, es = z * var_vol * 10_000, tail * var_vol * 10_000
            rows.append(pd.DataFrame({"date": dates.date, "method": method, "alpha": alpha, "var": var, "es": es,
                                      "realised_pnl": pnl, "exception": -pnl > var}))
    return pd.concat(rows, ignore_index=True)


def pd_scores(n: int = 60_000, seed: int = 5) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    split = rng.choice(["train", "valid", "test"], size=n, p=[0.5, 0.25, 0.25])
    year = np.select([split == "train", split == "valid"], [2014, 2016], 2017)
    issue = pd.to_datetime([f"{y}-{m:02d}-01" for y, m in zip(year, rng.integers(1, 13, n))])
    score = rng.standard_normal(n)
    true_logit = -3.0 + 0.9 * score + np.where(split == "test", 0.35, 0.0)       # the test year is riskier
    y = rng.random(n) < 1 / (1 + np.exp(-true_logit))
    model_pd = 1 / (1 + np.exp(-(-3.0 + 0.9 * score)))
    noisy = score + rng.standard_normal(n) * 0.8
    return pd.DataFrame({"split": split, "issue_d": issue.date, "default_12m": y.astype(int),
                         "gbm_raw": score, "gbm_pd": model_pd,
                         "scorecard_raw": noisy, "scorecard_pd": 1 / (1 + np.exp(-(-3.0 + 0.55 * noisy)))})
