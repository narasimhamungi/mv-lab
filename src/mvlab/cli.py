"""Command line: mvlab <command>.

  snapshot var|pd FILE --ref REF   freeze a model output (hash recorded) for validation
  validate var|pd                  run the tests on the snapshot and write the report to outputs/
  demo                             the same on invented inputs with known defects -> outputs/synthetic/
  commentary                       render grounded narrative from the existing validate outputs -> outputs/commentary.md
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import pandas as pd

from mvlab import inventory, pd_validation, report, settings, snapshot, synthetic, var_validation

VAR_ID, PD_ID = "VAR-OPT-01", "PD-CONS-01"


def run_var(path: Path, manifest: dict, out: Path, cfg: dict, inv: dict) -> dict:
    df = var_validation.load(path)
    res, findings = var_validation.validate(df, cfg, VAR_ID)
    out.mkdir(parents=True, exist_ok=True)
    res.round(10).to_csv(out / "var_results.csv", index=False)
    write_findings(out / "var_findings.csv", findings)
    (out / "var_validation.md").write_text(report.var_report(inv[VAR_ID], manifest, res, findings, cfg), encoding="utf-8")
    return {"results": res, "findings": findings}


def run_pd(path: Path, manifest: dict, out: Path, cfg: dict, inv: dict, champion: str = "gbm") -> dict:
    df = pd_validation.load(path)
    summaries, grades, findings = {}, {}, {}
    for m in cfg["pd"]["model_columns"]:
        summaries[m], grades[m], findings[m] = pd_validation.validate(df, cfg, PD_ID, m)
    out.mkdir(parents=True, exist_ok=True)
    write_findings(out / "pd_findings.csv", [f for fs in findings.values() for f in fs])
    pd.concat({m: g for m, g in grades.items()}, names=["model", "row"]).to_csv(out / "pd_grades.csv")
    (out / "pd_summary.json").write_text(json.dumps(summaries, indent=1, default=str), encoding="utf-8")
    (out / "pd_validation.md").write_text(report.pd_report(inv[PD_ID], manifest, summaries, grades, findings, champion),
                                          encoding="utf-8")
    return {"summaries": summaries, "findings": [f for fs in findings.values() for f in fs]}


def write_findings(path: Path, findings: list) -> None:
    pd.DataFrame([f.row() for f in findings], columns=["model_id", "test", "severity", "statement", "evidence",
                                                        "action"]).to_csv(path, index=False)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="mvlab", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("snapshot")
    s.add_argument("kind", choices=["var", "pd"])
    s.add_argument("file")
    s.add_argument("--ref", required=True, help="model reference: repository tag or commit, and the run date")
    v = sub.add_parser("validate")
    v.add_argument("kind", choices=["var", "pd", "all"])
    v.add_argument("--champion", default="gbm", help="the model the PD model's owner uses (default gbm)")
    d = sub.add_parser("demo")
    d.add_argument("--out", default=str(settings.OUTPUTS / "synthetic"))
    k = sub.add_parser("commentary")
    k.add_argument("--champion", default="gbm")
    k.add_argument("--out", default=str(settings.OUTPUTS / "commentary.md"))
    a = ap.parse_args(argv)
    try:
        cfg, inv = settings.load(), inventory.load()
        if a.cmd == "snapshot":
            path = snapshot.take(a.kind, Path(a.file), a.ref)
            print(f"{a.kind} snapshot: {path}")
            return 0
        if a.cmd == "demo":
            out = Path(a.out)
            work = out / "_inputs"
            work.mkdir(parents=True, exist_ok=True)
            synthetic.var_backtest().to_csv(work / "var_backtest_daily.csv", index=False)
            synthetic.pd_scores().to_parquet(work / "pd_scores.parquet", index=False)
            fv = run_var(snapshot.take("var", work / "var_backtest_daily.csv", "synthetic", work),
                         snapshot.load("var", work)[1], out, cfg, inv)["findings"]
            fp = run_pd(snapshot.take("pd", work / "pd_scores.parquet", "synthetic", work),
                        snapshot.load("pd", work)[1], out, cfg, inv)["findings"]
            print(f"demo: {len(fv) + len(fp)} findings -> {out}")
            return 0
        if a.cmd == "commentary":
            from mvlab import commentary
            o = settings.OUTPUTS
            path = commentary.run(o / "var_results.csv", o / "var_findings.csv", o / "pd_summary.json",
                                   o / "pd_findings.csv", a.champion, Path(a.out))
            print(f"commentary -> {path}")
            return 0
        out = settings.OUTPUTS
        found = []
        if a.kind in ("var", "all"):
            path, m = snapshot.load("var")
            r = run_var(path, m, out, cfg, inv)
            found += r["findings"]
            for _, row in r["results"].iterrows():
                print(f"  {row['method']:22s} {int(row['exceptions'])} exceptions vs {row['expected']:.1f}, "
                      f"Kupiec p {row['kupiec_p']:.3f}, Z2 {row['z2']:.2f} ({row['z2_zone']})")
        if a.kind in ("pd", "all"):
            path, m = snapshot.load("pd")
            r = run_pd(path, m, out, cfg, inv, a.champion)
            found += r["findings"]
            for name, s in r["summaries"].items():
                print(f"  {name:10s} AUC {s['auc_test']:.3f} ({s['auc_test_low']:.3f}-{s['auc_test_high']:.3f}), "
                      f"default rate {s['default_rate']:.2%} vs mean PD {s['mean_pd']:.2%}")
        sev = pd.Series([f.severity for f in found]).value_counts().to_dict() if found else {}
        print(f"findings: {sev or 'none'} -> {out}")
        return 0
    except Exception as exc:  # noqa: BLE001
        if os.environ.get("MVLAB_DEBUG"):
            raise
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
