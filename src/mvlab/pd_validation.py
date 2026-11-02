"""Validate a PD model from its loan-level scores: one row per loan with the window it belongs to
(train / valid / test), the issue date, the 12-month default outcome, and each model's raw score and
calibrated PD. Only aggregates leave this module.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from mvlab import pd_tests
from mvlab.findings import Finding

REQUIRED = ("split", "issue_d", "default_12m")


def load(path) -> pd.DataFrame:
    df = pd.read_parquet(path)
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise ValueError(f"PD scores file lacks columns {missing}")
    df["issue_d"] = pd.to_datetime(df["issue_d"])
    return df


def _grades(p: pd.Series, cfg: dict) -> pd.Series:
    edges = [-np.inf] + list(cfg["grade_upper_pd"]) + [np.inf]
    return pd.cut(p, edges, labels=cfg["grade_names"], right=True)


def validate(df: pd.DataFrame, cfg: dict, model_id: str, model: str) -> tuple[dict, pd.DataFrame, list[Finding]]:
    c = cfg["pd"]
    pd_col, raw_col = c["model_columns"][model], c["score_columns"][model]
    findings: list[Finding] = []
    test = df[df["split"] == c["primary_window"]]
    valid = df[df["split"] == "valid"]
    train = df[df["split"] == "train"]
    y = test["default_12m"].to_numpy()

    a_test = pd_tests.auc(y, test[raw_col])
    lo, hi = pd_tests.auc_interval(y, test[raw_col].to_numpy(), c["auc_bootstrap_draws"])
    a_valid = pd_tests.auc(valid["default_12m"], valid[raw_col]) if len(valid) else None
    a_train = pd_tests.auc(train["default_12m"], train[raw_col]) if len(train) else None
    hl = pd_tests.hosmer_lemeshow(y, test[pd_col])
    sp = pd_tests.spiegelhalter(y, test[pd_col])
    psi = pd_tests.psi(train[raw_col], test[raw_col]) if len(train) else None
    dr, mpd = float(y.mean()), float(test[pd_col].mean())
    summary = {"model": model, "window": c["primary_window"], "loans": int(len(test)), "defaults": int(y.sum()),
               "default_rate": dr, "mean_pd": mpd, "auc_train": a_train, "auc_valid": a_valid, "auc_test": a_test,
               "auc_test_low": lo, "auc_test_high": hi, "gini_test": 2 * a_test - 1,
               "hosmer_lemeshow": hl, "spiegelhalter": sp, "score_psi_train_to_test": psi}

    grades = pd_tests.grade_table(test.assign(grade=_grades(test[pd_col], c)), pd_col, "default_12m", "grade")
    grades["share"] = grades["n"] / grades["n"].sum()
    grades["relative_gap"] = grades["default_rate"] / grades["pd_mean"] - 1
    grades["conservative_p"] = [1 - p for p in grades["jeffreys_p"]]

    if a_valid is not None and a_valid - a_test > c["auc_drop_medium"]:
        findings.append(Finding(model_id, f"Discrimination ({model})", "Medium",
                                "Out-of-time AUC is materially below the validation-window AUC.",
                                f"AUC {a_valid:.3f} in validation, {a_test:.3f} out of time",
                                "Investigate drift in the features carrying the score."))
    for g, r in grades.iterrows():
        material = r["share"] >= c["material_share"]
        econ = abs(r["relative_gap"]) > c["material_relative_gap"]
        ev = (f"grade {g}: {int(r['defaults']):,} defaults in {int(r['n']):,} loans, default rate {r['default_rate']:.2%} "
              f"against mean PD {r['pd_mean']:.2%}")
        if r["jeffreys_p"] < 0.05 and econ:
            sev = "High" if (r["jeffreys_p"] < 0.01 and material) else "Medium"
            findings.append(Finding(model_id, f"Jeffreys test ({model}, grade {g})", sev,
                                    f"Grade {g}'s PD is too low out of time.", f"{ev}; p = {r['jeffreys_p']:.4f}",
                                    "Recalibrate on a later window or add a margin of conservatism to this grade."))
        elif r["conservative_p"] < 0.05 and econ:
            findings.append(Finding(model_id, f"Jeffreys test ({model}, grade {g})", "Low",
                                    f"Grade {g}'s PD is conservative out of time.", f"{ev}; p = {r['conservative_p']:.4f}",
                                    "Record; conservative PDs overprice this grade."))
    if hl["p_value"] < 0.05:
        econ = abs(dr / mpd - 1) > c["material_relative_gap"]
        findings.append(Finding(model_id, f"Hosmer-Lemeshow ({model})", "Medium" if econ else "Low",
                                "Calibration across deciles is rejected" + ("" if econ else
                                "; with this many loans small gaps are significant, and the portfolio-level gap is "
                                "not material") + ".",
                                f"HL = {hl['statistic']:.1f} on {hl['df']} df, p = {hl['p_value']:.2g}; default rate "
                                f"{dr:.2%} against mean PD {mpd:.2%}", "Review the grade table for where the gap sits."))
    if psi is not None and psi > c["psi_medium"]:
        findings.append(Finding(model_id, f"Population stability ({model})",
                                "High" if psi > c["psi_high"] else "Medium",
                                "The score distribution shifted between development and out-of-time samples.",
                                f"PSI {psi:.3f}", "Review the applicant mix and the features that moved."))

    by_q = (test.assign(q=test["issue_d"].dt.to_period("Q").astype(str))
            .groupby("q").apply(lambda d: pd.Series({"loans": len(d), "default_rate": d["default_12m"].mean(),
                                                    "mean_pd": d[pd_col].mean(),
                                                    "auc": pd_tests.auc(d["default_12m"], d[raw_col])}),
                                include_groups=False))
    summary["by_quarter"] = by_q.reset_index().to_dict(orient="records")
    return summary, grades.reset_index(), findings
