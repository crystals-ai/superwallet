from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


BASE_DIR = Path(__file__).resolve().parents[2]
BASE_POLICY_DOC_PATH = BASE_DIR / "policies" / "default_policy_document.txt"
UPLOADS_DIR = BASE_DIR / "policies" / "uploads"


def load_policy() -> Dict[str, Any]:
    policy = _default_policy()
    return _apply_policy_documents(policy, _policy_document_paths())


def list_policy_documents() -> List[Dict[str, Any]]:
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    documents: List[Dict[str, Any]] = []
    for path in reversed(_policy_document_paths()):
        stat = path.stat()
        documents.append(
            {
                "name": path.name,
                "size": stat.st_size,
                "updated_at": stat.st_mtime,
                "source": "bundled" if path == BASE_POLICY_DOC_PATH else "uploaded",
            }
        )
    return documents


def save_policy_document(filename: str, content: bytes) -> Path:
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r"[^A-Za-z0-9._-]", "-", filename).strip("-") or "policy.txt"
    destination = UPLOADS_DIR / safe_name
    destination.write_bytes(content)
    return destination


def _default_policy() -> Dict[str, Any]:
    return {
        "agents": {
            "research-agent": {
                "daily_limit": 50.0,
                "per_transaction_limit": 20.0,
                "allowed_categories": ["data_api", "web_search"],
                "allowed_vendors": [],
                "blocked_vendors": [],
            }
        },
        "review_rules": {
            "new_vendor_requires_review": True,
            "risk_score_review_threshold": 0.5,
        },
        "block_rules": {
            "semantic_mismatch_blocks": True,
            "over_limit_blocks": True,
            "blocklisted_vendor_blocks": True,
        },
    }


def _policy_document_paths() -> List[Path]:
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    paths = [BASE_POLICY_DOC_PATH]
    paths.extend(sorted(path for path in UPLOADS_DIR.iterdir() if path.is_file()))
    return paths


def _apply_policy_documents(policy: Dict[str, Any], paths: List[Path]) -> Dict[str, Any]:
    agent_policy = policy["agents"].get("research-agent", {})

    for path in paths:
        if not path.exists() or not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            parsed = _parse_directive(line)
            if parsed is None:
                continue

            key, value = parsed
            if key == "allow_vendor":
                agent_policy.setdefault("allowed_vendors", [])
                if value not in agent_policy["allowed_vendors"]:
                    agent_policy["allowed_vendors"].append(value)
            elif key == "block_vendor":
                agent_policy.setdefault("blocked_vendors", [])
                if value not in agent_policy["blocked_vendors"]:
                    agent_policy["blocked_vendors"].append(value)
            elif key == "allow_category":
                agent_policy.setdefault("allowed_categories", [])
                if value not in agent_policy["allowed_categories"]:
                    agent_policy["allowed_categories"].append(value)
            elif key == "daily_limit":
                agent_policy["daily_limit"] = float(value)
            elif key == "per_transaction_limit":
                agent_policy["per_transaction_limit"] = float(value)

    policy["agents"]["research-agent"] = agent_policy
    return policy


def _parse_directive(line: str) -> Optional[Tuple[str, str]]:
    if ":" not in line:
        return None

    key, value = line.split(":", 1)
    directive = key.strip().lower().replace(" ", "_")
    payload = value.strip()

    if directive in {
        "allow_vendor",
        "block_vendor",
        "allow_category",
        "daily_limit",
        "per_transaction_limit",
    } and payload:
        return directive, payload
    return None
