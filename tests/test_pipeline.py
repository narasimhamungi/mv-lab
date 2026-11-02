import ast
import json
from pathlib import Path

import pandas as pd
import pytest

from mvlab import cli, findings, inventory, settings, snapshot

MODEL_PACKAGES = {"derivlab", "creditlab", "market_risk_lab", "techdeal", "bankcredit", "fundfinancelab"}


def test_no_import_of_model_repo_statistics():
    """Independence by construction: the validator reads frozen outputs, never the model's code."""
    for path in (settings.ROOT / "src" / "mvlab").glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            names = [a.name for a in node.names] if isinstance(node, ast.Import) else \
                [node.module or ""] if isinstance(node, ast.ImportFrom) else []
            assert not any(n.split(".")[0] in MODEL_PACKAGES for n in names), f"{path.name} imports {names}"


def test_inventory_entries_are_complete():
    inv = inventory.load()
    assert set(inv) == {"VAR-OPT-01", "PD-CONS-01"}


def test_snapshot_refuses_changed_bytes(tmp_path):
    src = tmp_path / "x.csv"
    src.write_text("a\n1\n", encoding="utf-8")
    snapshot.take("var", src, "ref", tmp_path / "snaps")
    path, m = snapshot.load("var", tmp_path / "snaps")
    assert m["model_ref"] == "ref"
    path.write_text("a\n2\n", encoding="utf-8")
    with pytest.raises(snapshot.SnapshotError, match="hash"):
        snapshot.load("var", tmp_path / "snaps")


def test_conclusion_rule():
    f = lambda s: findings.Finding("M", "t", s, "x", "y", "z")
    assert findings.conclusion([]) == "Fit for use"
    assert findings.conclusion([f("Low"), f("Medium")]) == "Fit for use with conditions"
    assert findings.conclusion([f("High")]) == "Not fit for use as configured"
    with pytest.raises(ValueError):
        f("Critical")


def test_demo_catches_each_planted_defect(tmp_path, capsys):
    assert cli.main(["demo", "--out", str(tmp_path)]) == 0
    var_md = (tmp_path / "var_validation.md").read_text(encoding="utf-8")
    assert "**well_specified:** Fit for use." in var_md
    assert "**too_low:** Not fit for use as configured." in var_md
    f = pd.concat([pd.read_csv(tmp_path / "var_findings.csv"), pd.read_csv(tmp_path / "pd_findings.csv")])
    static = f[f["test"].str.contains("static")]
    assert "Christoffersen independence (static)" in set(static["test"])        # the clustering is found
    assert not f["test"].str.contains("well_specified").any()
    gbm = f[f["test"].str.contains("gbm")]
    assert (gbm["severity"] == "High").any()                                   # the out-of-time drift is found
    summ = json.loads((tmp_path / "pd_summary.json").read_text(encoding="utf-8"))
    assert summ["gbm"]["auc_test"] > summ["scorecard"]["auc_test"]
    assert "|" not in "".join(f["evidence"])                                   # evidence never breaks a table


def test_validate_without_a_snapshot_is_a_clean_error(tmp_path, monkeypatch, capsys):
    def missing(kind, root=None):
        raise snapshot.SnapshotError(f"no {kind} snapshot: run `mvlab snapshot {kind} <file>` first")
    monkeypatch.setattr(cli.snapshot, "load", missing)
    assert cli.main(["validate", "var"]) == 2
    assert "no var snapshot" in capsys.readouterr().err
