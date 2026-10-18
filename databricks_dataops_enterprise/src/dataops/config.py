from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def load_environment_config(environment: str) -> dict[str, Any]:
    if environment not in {"dev", "uat", "prd"}:
        raise ValueError(f"Unsupported environment: {environment}")
    path = ROOT / "config" / "environments" / f"{environment}.json"
    with path.open(encoding="utf-8") as handle:
        config = json.load(handle)
    if config.get("environment") != environment:
        raise ValueError(f"Config environment mismatch in {path}")
    return config
