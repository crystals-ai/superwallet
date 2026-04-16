from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml


BASE_DIR = Path(__file__).resolve().parents[2]
POLICY_PATH = BASE_DIR / "policies" / "wallet_policy.yaml"


def load_policy() -> Dict[str, Any]:
    with POLICY_PATH.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)
