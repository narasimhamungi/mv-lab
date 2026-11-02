"""Frozen copies of a model's outputs, with a SHA-256 manifest.

Validation reads only these copies, never the model repository, so a validation result can always be tied
to the exact bytes it was run on. The VaR snapshot (daily forecasts and P&L) is committed; the PD snapshot
is loan-level and stays under data/snapshots/pd/, which is git-ignored.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import shutil
from pathlib import Path

from mvlab.settings import SNAPSHOTS


class SnapshotError(RuntimeError):
    pass


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def take(kind: str, source: Path, model_ref: str, root: Path = SNAPSHOTS) -> Path:
    source = Path(source)
    if not source.exists():
        raise SnapshotError(f"{source} not found")
    out = Path(root) / kind
    out.mkdir(parents=True, exist_ok=True)
    target = out / source.name
    shutil.copyfile(source, target)
    manifest = {"kind": kind, "file": source.name, "sha256": sha256(target), "bytes": target.stat().st_size,
                "model_ref": model_ref, "taken_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    return target


def load(kind: str, root: Path = SNAPSHOTS) -> tuple[Path, dict]:
    out = Path(root) / kind
    mpath = out / "manifest.json"
    if not mpath.exists():
        raise SnapshotError(f"no {kind} snapshot: run `mvlab snapshot {kind} <file>` first")
    m = json.loads(mpath.read_text(encoding="utf-8"))
    path = out / m["file"]
    if not path.exists() or sha256(path) != m["sha256"]:
        raise SnapshotError(f"{path} does not match its manifest hash: take the snapshot again")
    return path, m
