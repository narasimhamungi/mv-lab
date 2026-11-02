"""The model inventory and the fields each entry must carry."""
from __future__ import annotations

from pathlib import Path

import yaml

from mvlab.settings import INVENTORY

FIELDS = ("model_id", "name", "repository", "version", "owner", "use", "tier", "methodology", "inputs", "outputs",
          "limitations", "validation_scope")


def load(path: Path = INVENTORY) -> dict[str, dict]:
    models = yaml.safe_load(Path(path).read_text(encoding="utf-8"))["models"]
    out = {}
    for m in models:
        missing = [f for f in FIELDS if not m.get(f)]
        if missing:
            raise ValueError(f"inventory entry {m.get('model_id', '?')} lacks {missing}")
        out[m["model_id"]] = m
    return out
