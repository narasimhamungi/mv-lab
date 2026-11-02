"""Validate a VaR/ES engine from its daily backtest: one row per date, method and level with the forecast
VaR and ES (positive losses), the realised P&L, as the model wrote them.

Expected columns: date, method, alpha, var, es, realised_pnl. The exception flag is recomputed here
(loss above VaR) rather than taken from the model's own column, and any disagreement is a finding.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from mvlab import coverage, es_tests
from mvlab.findings import Finding

REQUIRED = ("date", "method", "alpha", "var", "es", "realised_pnl")


def load(path) -> pd.DataFrame:
    df = pd.read_csv(path)
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise ValueError(f"VaR backtest file lacks columns {missing}")
    df["date"] = pd.to_datetime(df["date"])
    df["loss"] = -df["realised_pnl"]
    df["exception_recomputed"] = df["loss"] > df["var"]
    return df.sort_values(["method", "alpha", "date"]).reset_index(drop=True)


def validate(df: pd.DataFrame, cfg: dict, model_id: str) -> tuple[pd.DataFrame, list[Finding]]:
    v = cfg["var"]
    rows, findings = [], []
    if "exception" in df.columns:
        bad = int((df["exception"].astype(bool) != df["exception_recomputed"]).sum())
        if bad:
            findings.append(Finding(model_id, "Data integrity", "Medium",
                                    f"The model's exception flag disagrees with loss > VaR on {bad} rows.",
                                    "exception vs realised_pnl and var", "Correct the flag in the model's output."))
    for method, g in df.groupby("method", sort=False):
        cov = g[np.isclose(g["alpha"], v["coverage_alpha"])]
        tail = g[np.isclose(g["alpha"], v["es_alpha"])]
        row = {"method": method, "start": g["date"].min().date().isoformat(), "end": g["date"].max().date().isoformat()}
        if len(cov):
            exc = cov["exception_recomputed"].to_numpy()
            uc = coverage.kupiec_pof(exc, v["coverage_alpha"])
            ind = coverage.christoffersen_independence(exc)
            cc = coverage.conditional_coverage(exc, v["coverage_alpha"])
            tl = coverage.traffic_light(exc, v["traffic_light_window"])
            row.update({"forecasts": len(cov), "exceptions": int(exc.sum()),
                        "expected": len(cov) * (1 - v["coverage_alpha"]), "kupiec_p": uc.p_value,
                        "independence_p": ind.p_value, "cond_coverage_p": cc.p_value,
                        "tl_green": tl["green"], "tl_yellow": tl["yellow"], "tl_red": tl["red"],
                        "tl_latest": tl["latest"], "tl_max": tl["max"]})
            lvl = f"{v['coverage_alpha']:.0%}"
            if uc.p_value is not None and uc.p_value < 0.01:
                findings.append(Finding(model_id, f"Kupiec POF ({method}, {lvl})", "High",
                                        f"{method}: the exception rate is inconsistent with {lvl} coverage.",
                                        f"{uc.detail}; p = {uc.p_value:.4f}",
                                        "Do not use this method for limits or capital until coverage is restored."))
            elif uc.p_value is not None and uc.p_value < 0.05:
                findings.append(Finding(model_id, f"Kupiec POF ({method}, {lvl})", "Medium",
                                        f"{method}: the exception rate is borderline for {lvl} coverage.",
                                        f"{uc.detail}; p = {uc.p_value:.4f}", "Monitor quarterly; review the method."))
            if ind.p_value is not None and ind.p_value < 0.05:
                findings.append(Finding(model_id, f"Christoffersen independence ({method})", "Medium",
                                        f"{method}: exceptions cluster in time.", f"{ind.detail}; p = {ind.p_value:.4f}",
                                        "Add volatility scaling or a shorter look-back so the VaR reacts to regimes."))
            if tl["latest"] is not None and tl["latest"] >= 10:
                findings.append(Finding(model_id, f"Traffic light ({method})", "High",
                                        f"{method}: the latest 250-day window is in the red zone.",
                                        f"{tl['latest']} exceptions in the latest window", "Escalate; recalibrate."))
            elif tl["red"]:
                findings.append(Finding(model_id, f"Traffic light ({method})", "Medium",
                                        f"{method}: {tl['red']:.0%} of 250-day windows were in the red zone, though "
                                        "the latest is not.", f"maximum {tl['max']} exceptions in a window; latest "
                                        f"{tl['latest']}", "Document the episode and the model's response to it."))
        if len(tail):
            z = es_tests.acerbi_szekely_z2(tail["loss"], tail["var"], tail["es"], v["es_alpha"])
            ex = es_tests.exceedance_residuals(tail["loss"], tail["var"], tail["es"], v["exceedance_bootstrap_draws"])
            row.update({"es_forecasts": len(tail), "es_exceptions": z["exceptions"], "z2": z["z2"], "z2_zone": z["zone"],
                        "exceed_resid_mean": ex["mean"], "exceed_resid_p": ex["p_value"],
                        "loss_over_es": ex.get("loss_over_es")})
            lvl = f"{v['es_alpha']:.1%}"
            if z["zone"] in ("red", "yellow"):
                findings.append(Finding(model_id, f"Acerbi-Szekely Z2 ({method}, {lvl})",
                                        "High" if z["zone"] == "red" else "Medium",
                                        f"{method}: realised tail losses exceed what the ES forecast ({z['zone']} zone).",
                                        f"Z2 = {z['z2']:.3f} (thresholds -0.70 and -1.80)",
                                        "Review the tail model; ES understates the loss in the tail."))
            if ex["p_value"] is not None and ex["p_value"] < 0.05:
                findings.append(Finding(model_id, f"Exceedance residuals ({method}, {lvl})", "Medium",
                                        f"{method}: on exception days the loss runs above the ES forecast.",
                                        f"mean residual {ex['mean']:+.2f} over {ex['n']} exceptions; p = {ex['p_value']:.3f}",
                                        "Review the tail model."))
        rows.append(row)
    return pd.DataFrame(rows), findings
