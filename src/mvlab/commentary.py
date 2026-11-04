"""Grounded commentary: narrative rendered from a fact map, not an LLM call.

Same pattern as fpa-lab's commentary.py. build_var_fact_map() / build_pd_fact_map() are the single
source of every number a template may print; render_commentary() only formats and concatenates
those values, with no arithmetic of its own; check_grounding() mechanically verifies every number
in the rendered text traces back to some formatting of a fact-map value, so a template edit that
introduces a wrong or invented figure fails a test instead of shipping.
"""
from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

from mvlab.findings import Finding, conclusion


def _method_of(test_name: str) -> str:
    """Findings name their method in parentheses, e.g. "Kupiec POF (delta_hs, 99%)" -> "delta_hs".
    Same parse report.py uses to group findings by method."""
    return test_name.split("(")[-1].split(",")[0].rstrip(")")


def _by_method(findings: list[Finding]) -> dict[str, list[Finding]]:
    out: dict[str, list[Finding]] = {}
    for f in findings:
        out.setdefault(_method_of(f.test), []).append(f)
    return out


def build_var_fact_map(results: pd.DataFrame, findings: list[Finding]) -> dict:
    by_method = _by_method(findings)
    conclusions = {m: conclusion(by_method.get(m, [])) for m in results["method"]}
    fit_counts = Counter(conclusions.values())
    sev_counts = Counter(f.severity for f in findings)

    worst_kupiec = results.sort_values("kupiec_p").iloc[0]
    worst_independence = results.sort_values("independence_p").iloc[0]
    worst_z2 = results.sort_values("z2").iloc[0]  # most negative = worst

    return {
        "n_methods": len(results),
        "n_high": sev_counts.get("High", 0),
        "n_medium": sev_counts.get("Medium", 0),
        "n_low": sev_counts.get("Low", 0),
        "n_fit": fit_counts.get("Fit for use", 0),
        "n_fit_conditions": fit_counts.get("Fit for use with conditions", 0),
        "n_not_fit": fit_counts.get("Not fit for use as configured", 0),
        "worst_kupiec_method": worst_kupiec["method"],
        "worst_kupiec_p": worst_kupiec["kupiec_p"],
        "worst_kupiec_exceptions": worst_kupiec["exceptions"],
        "worst_kupiec_expected": worst_kupiec["expected"],
        "worst_independence_method": worst_independence["method"],
        "worst_independence_p": worst_independence["independence_p"],
        "worst_z2_method": worst_z2["method"],
        "worst_z2": worst_z2["z2"],
        "worst_z2_zone": worst_z2["z2_zone"],
    }


def build_pd_fact_map(summaries: dict[str, dict], findings: dict[str, list[Finding]], champion: str) -> dict:
    other = next(m for m in summaries if m != champion)
    champ_sev = Counter(f.severity for f in findings[champion])
    other_sev = Counter(f.severity for f in findings[other])
    cs, os_ = summaries[champion], summaries[other]

    return {
        "champion": champion,
        "challenger": other,
        "champion_conclusion": conclusion(findings[champion]),
        "challenger_conclusion": conclusion(findings[other]),
        "champion_loans": cs["loans"],
        "champion_default_rate": cs["default_rate"],
        "champion_mean_pd": cs["mean_pd"],
        "champion_auc_test": cs["auc_test"],
        "champion_auc_low": cs["auc_test_low"],
        "champion_auc_high": cs["auc_test_high"],
        "challenger_auc_test": os_["auc_test"],
        "champion_n_high": champ_sev.get("High", 0),
        "champion_n_medium": champ_sev.get("Medium", 0),
        "challenger_n_high": other_sev.get("High", 0),
        "challenger_n_medium": other_sev.get("Medium", 0),
    }


def _pct(v, d=1) -> str:
    return "n.a." if v is None or v != v else f"{v:.{d}%}"


def _num(v, d=3) -> str:
    return "n.a." if v is None or v != v else f"{v:.{d}f}"


def render_commentary(var_facts: dict, pd_facts: dict) -> str:
    v, p = var_facts, pd_facts
    lines = [
        "## VaR and ES validation",
        "",
        f"Across {v['n_methods']} methods, findings graded {v['n_high']} High, {v['n_medium']} Medium and "
        f"{v['n_low']} Low: {v['n_fit']} fit for use, {v['n_fit_conditions']} fit for use with conditions, "
        f"{v['n_not_fit']} not fit for use as configured.",
        "",
        f"{v['worst_kupiec_method']} has the weakest coverage test: Kupiec p {_num(v['worst_kupiec_p'], 4)} "
        f"on {int(v['worst_kupiec_exceptions'])} exceptions against {_num(v['worst_kupiec_expected'], 1)} expected.",
        "",
        f"{v['worst_independence_method']} has the weakest independence test, p {_num(v['worst_independence_p'], 4)} "
        "— evidence that exceptions cluster rather than spreading evenly.",
        "",
        f"{v['worst_z2_method']} has the weakest expected-shortfall backtest: Z2 {_num(v['worst_z2'], 2)} "
        f"({v['worst_z2_zone']} zone).",
        "",
        "## PD validation",
        "",
        f"The champion model ({p['champion']}) is {p['champion_conclusion'].lower()}; the challenger "
        f"({p['challenger']}) is {p['challenger_conclusion'].lower()}.",
        "",
        f"On {int(p['champion_loans']):,} out-of-time loans, the champion's AUC is {_num(p['champion_auc_test'])} "
        f"(95% interval {_num(p['champion_auc_low'])} to {_num(p['champion_auc_high'])}) against "
        f"{_num(p['challenger_auc_test'])} for the challenger; mean PD {_pct(p['champion_mean_pd'], 2)} against "
        f"an observed default rate of {_pct(p['champion_default_rate'], 2)}.",
        "",
        f"Findings: champion {p['champion_n_high']} High / {p['champion_n_medium']} Medium; "
        f"challenger {p['challenger_n_high']} High / {p['challenger_n_medium']} Medium.",
    ]
    return "\n".join(lines) + "\n"


_NUMBER_RE = re.compile(r"-?\d[\d,]*(?:\.\d+)?")


def _numbers_in_text(text: str) -> set[str]:
    return {m.replace(",", "") for m in _NUMBER_RE.findall(text)}


def _candidate_strings(v: float) -> set[str]:
    """Every plausible rendering of a single numeric fact: signed/unsigned, 0-4 decimal places,
    as itself and as a percentage (x100). Brute-force rather than trying to mirror render_commentary's
    exact format calls -- the point is that check_grounding and render_commentary can drift in their
    formatting without the grounding test silently losing coverage."""
    out = set()
    for scale in (1, 100):
        for d in range(0, 5):
            out.add(f"{v * scale:.{d}f}")
            out.add(f"{abs(v) * scale:.{d}f}")
    out.add(f"{v:,.0f}".replace(",", ""))
    return out


def check_grounding(text: str, *fact_maps: dict) -> list[str]:
    """Return numeric tokens in `text` that don't match any formatting of any numeric value across
    the given fact maps. Empty list == every number in the text traces to a fact."""
    allowed: set[str] = set()
    for facts in fact_maps:
        for v in facts.values():
            if isinstance(v, (int, float, np.integer, np.floating)):
                allowed |= _candidate_strings(float(v))
    # stated constants that appear in template prose, not fact-map values
    allowed |= {"0", "95", "99", "97.5", "250"}
    found = _numbers_in_text(text)
    return sorted(n for n in found if n not in allowed)


def run(var_results_csv: Path, var_findings_csv: Path, pd_summary_json: Path, pd_findings_csv: Path,
        champion: str, out_path: Path) -> Path:
    import json

    results = pd.read_csv(var_results_csv)
    var_findings = [Finding(**r) for r in pd.read_csv(var_findings_csv).to_dict(orient="records")]
    summaries = json.loads(pd_summary_json.read_text(encoding="utf-8"))
    pd_findings_df = pd.read_csv(pd_findings_csv)
    pd_findings: dict[str, list[Finding]] = {}
    for model in summaries:
        rows = pd_findings_df[pd_findings_df["test"].str.contains(re.escape(model), case=False, na=False)]
        pd_findings[model] = [Finding(**r) for r in rows.to_dict(orient="records")] if len(rows) else []
        if model not in pd_findings or not pd_findings[model]:
            pd_findings[model] = []

    var_facts = build_var_fact_map(results, var_findings)
    pd_facts = build_pd_fact_map(summaries, pd_findings, champion)
    text = render_commentary(var_facts, pd_facts)
    ungrounded = check_grounding(text, var_facts, pd_facts)
    if ungrounded:
        raise ValueError(f"ungrounded numbers in rendered commentary: {ungrounded}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        "# Validation commentary\n\n"
        "Rendered from a fact map built on var_results.csv, var_findings.csv, pd_summary.json and "
        "pd_findings.csv; every number below is checked to trace back to that fact map before this "
        "file is written (mvlab.commentary.check_grounding). No LLM call is involved.\n\n" + text,
        encoding="utf-8",
    )
    return out_path
