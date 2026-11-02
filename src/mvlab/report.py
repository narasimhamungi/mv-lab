"""Validation reports: one Markdown file per model, written from the computed results only."""
from __future__ import annotations

import pandas as pd

from mvlab.findings import Finding, conclusion

INDEPENDENCE = ("**Independence.** The validator is also the model's developer. SS1/23 expects validation to be "
                "independent of development; this report applies the tests and the rubric a second-line function "
                "would, on frozen outputs, without importing the model's code, but it is self-validation and says so.")


def _pct(v, d=1):
    return "n.a." if v is None or v != v else f"{v:.{d}%}"


def _num(v, d=3):
    return "n.a." if v is None or v != v else f"{v:.{d}f}"


def _table(head: list[str], rows: list[list]) -> list[str]:
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return out


def _findings(findings: list[Finding]) -> list[str]:
    if not findings:
        return ["No findings."]
    order = {"High": 0, "Medium": 1, "Low": 2}
    fs = sorted(findings, key=lambda f: order[f.severity])
    return _table(["Severity", "Test", "Finding", "Evidence", "Action"],
                  [[f.severity, f.test, f.statement, f.evidence, f.action] for f in fs])


def _header(model: dict, manifest: dict) -> list[str]:
    return [f"# Validation report: {model['model_id']}, {model['name']}", "",
            f"Model repository: {model['repository']}. Use: {model['use']}. Tier {model['tier']}.", "",
            f"Validated on a frozen snapshot: `{manifest['file']}`, SHA-256 `{manifest['sha256'][:16]}...`, taken "
            f"{manifest['taken_at']} (model reference: {manifest['model_ref']}).", "", INDEPENDENCE, ""]


def var_report(model: dict, manifest: dict, results: pd.DataFrame, findings: list[Finding], cfg: dict) -> str:
    v = cfg["var"]
    by_method = {}
    for f in findings:
        by_method.setdefault(f.test.split("(")[-1].split(",")[0].rstrip(")"), []).append(f)
    lines = _header(model, manifest)
    lines += ["## Conclusion", ""]
    for _, r in results.iterrows():
        lines.append(f"- **{r['method']}:** {conclusion(by_method.get(r['method'], []))}.")
    lines += ["", f"## Coverage at {v['coverage_alpha']:.0%}", ""]
    lines += _table(["Method", "Forecasts", "Exceptions", "Expected", "Kupiec p", "Independence p",
                     "Cond. coverage p", "Traffic light: green / yellow / red", "Latest window"],
                    [[r["method"], f"{int(r['forecasts']):,}", int(r["exceptions"]), f"{r['expected']:.1f}",
                      _num(r["kupiec_p"], 4), _num(r["independence_p"], 4), _num(r["cond_coverage_p"], 4),
                      f"{_pct(r['tl_green'], 0)} / {_pct(r['tl_yellow'], 0)} / {_pct(r['tl_red'], 0)}",
                      r["tl_latest"]] for _, r in results.iterrows()])
    lines += ["", f"Traffic light: share of trailing {v['traffic_light_window']}-day windows in each Basel zone "
                  "(green 0-4, yellow 5-9, red 10 or more exceptions at 99%).", "",
              f"## Expected shortfall at {v['es_alpha']:.1%}", ""]
    lines += _table(["Method", "Exceptions", "Z2", "Zone", "Mean exceedance residual", "Residual p", "Loss / ES"],
                    [[r["method"], int(r["es_exceptions"]), _num(r["z2"]), r["z2_zone"],
                      _num(r["exceed_resid_mean"], 3), _num(r["exceed_resid_p"], 3), _num(r["loss_over_es"], 2)]
                     for _, r in results.iterrows()])
    lines += ["", "Z2 (Acerbi and Szekely, 2014): 0 when the ES is right, negative when tail losses run larger; the "
                  "paper's approximate thresholds -0.70 (5%) and -1.80 (0.01%) set the yellow and red zones. "
                  "Exceedance residual: (loss - ES) / ES on exception days; the p-value is a one-sided bootstrap "
                  "test that the mean is above zero.", "", "## Findings", ""]
    lines += _findings(findings)
    lines += ["", "## Limits of this validation", "",
              f"- {model['limitations']}",
              "- The coverage and ES tests use the model's own forecasts and P&L; they do not re-derive the P&L.",
              "- Thresholds outside the Basel traffic light are this project's rubric (docs/rubric.md)."]
    return "\n".join(lines) + "\n"


def pd_report(model: dict, manifest: dict, summaries: dict[str, dict], grades: dict[str, pd.DataFrame],
              findings: dict[str, list[Finding]], champion: str) -> str:
    lines = _header(model, manifest)
    lines += ["## Conclusion", ""]
    for m in summaries:
        tag = " (champion)" if m == champion else " (challenger)"
        lines.append(f"- **{m}{tag}:** {conclusion(findings[m])}.")
    lines += ["", "## Discrimination and calibration, out-of-time window", ""]
    lines += _table(["Model", "Loans", "Default rate", "Mean PD", "AUC train", "AUC valid", "AUC test (95% interval)",
                     "Gini test", "HL p", "Spiegelhalter p", "Score PSI"],
                    [[m, f"{s['loans']:,}", _pct(s["default_rate"], 2), _pct(s["mean_pd"], 2), _num(s["auc_train"]),
                      _num(s["auc_valid"]), f"{_num(s['auc_test'])} ({_num(s['auc_test_low'])} to {_num(s['auc_test_high'])})",
                      _num(s["gini_test"]), f"{s['hosmer_lemeshow']['p_value']:.2g}",
                      f"{s['spiegelhalter']['p_value']:.2g}", _num(s["score_psi_train_to_test"])]
                     for m, s in summaries.items()])
    for m, g in grades.items():
        lines += ["", f"## Calibration by grade: {m}", ""]
        lines += _table(["Grade", "Loans", "Share", "Defaults", "Default rate", "Mean PD", "Gap (DR / PD - 1)",
                         "Jeffreys p (PD too low)"],
                        [[r["grade"], f"{int(r['n']):,}", _pct(r["share"]), f"{int(r['defaults']):,}",
                          _pct(r["default_rate"], 2), _pct(r["pd_mean"], 2), f"{r['relative_gap']:+.1%}",
                          f"{r['jeffreys_p']:.3g}"] for _, r in g.iterrows()])
    s = summaries[champion]
    lines += ["", f"## Stability by quarter of origination: {champion}", ""]
    lines += _table(["Quarter", "Loans", "Default rate", "Mean PD", "AUC"],
                    [[q["q"], f"{int(q['loans']):,}", _pct(q["default_rate"], 2), _pct(q["mean_pd"], 2), _num(q["auc"])]
                     for q in s["by_quarter"]])
    lines += ["", "## Findings", ""]
    for m in summaries:
        lines += [f"### {m}", ""] + _findings(findings[m]) + [""]
    lines += ["## Limits of this validation", "", f"- {model['limitations']}",
              "- Jeffreys test as described in the ECB guide to internal models; the grade scale is mv-lab's own.",
              "- With hundreds of thousands of loans, goodness-of-fit tests reject small gaps; the rubric asks for "
              "an economically material gap as well (docs/rubric.md)."]
    return "\n".join(lines) + "\n"
