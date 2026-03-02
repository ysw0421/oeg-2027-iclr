from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class ToolDef:
    name: str
    schema: dict[str, Any]
    policy: dict[str, Any]


def load_toolspec(path: str) -> dict[str, ToolDef]:
    obj = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise ValueError("toolspec must be a dict at top-level")
    tools = obj.get("tools")
    if not isinstance(tools, list):
        raise ValueError("toolspec must contain a 'tools' list")

    out: dict[str, ToolDef] = {}
    for t in tools:
        if not isinstance(t, dict):
            continue
        name = t.get("name")
        if not isinstance(name, str) or not name:
            continue
        schema = t.get("schema") if isinstance(t.get("schema"), dict) else {}
        policy = t.get("policy") if isinstance(t.get("policy"), dict) else {}
        out[name] = ToolDef(name=name, schema=schema, policy=policy)
    return out


def allowed_arg_keys(td: ToolDef) -> set[str] | None:
    props = td.schema.get("properties")
    if isinstance(props, dict):
        return set(props.keys())
    return None


def requires_confirmation(td: ToolDef) -> bool:
    return bool(td.policy.get("requires_confirmation", False))


def is_idempotent(td: ToolDef) -> bool:
    return bool(td.policy.get("idempotent", False))