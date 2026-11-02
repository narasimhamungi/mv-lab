from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config" / "mvlab.yml"
INVENTORY = ROOT / "inventory" / "models.yml"
SNAPSHOTS = ROOT / "data" / "snapshots"
OUTPUTS = ROOT / "outputs"


def load(path: Path = CONFIG) -> dict:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))
