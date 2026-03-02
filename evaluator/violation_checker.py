from __future__ import annotations
from typing import Any, Dict, List
import yaml

def load_tools_yaml(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def _schema_check(schema: dict, args: dict) -> List[dict]:
    violations = []
    required = schema.get("required", [])
    props = schema.get("properties", {})

    for k in required:
        if k not in args:
            violations.append({"type": "schema_missing", "detail": k})

    for k, v in args.items():
        if k not in props:
            violations.append({"type": "schema_extra_field", "detail": k})
            continue
        t = props[k].get("type")
        if t == "string" and not isinstance(v, str):
            violations.append({"type": "schema_type", "detail": f"{k}:expected_string"})
        if t == "number":
            try:
                float(v)
            except Exception:
                violations.append({"type": "schema_type", "detail": f"{k}:expected_number"})
    return violations

def check_trajectory(tools_yaml_path: str, trajectory: List[dict]) -> List[dict]:
    spec = load_tools_yaml(tools_yaml_path)
    tools = {t["name"]: t for t in spec.get("tools", [])}
    violations: List[dict] = []

    seen_nonidempotent = set()

    for step_i, step in enumerate(trajectory):
        tool_name = step.get("tool")
        args = step.get("args", {})

        if tool_name not in tools:
            violations.append({"type": "tool_hallucination", "detail": tool_name, "step": step_i})
            continue

        tool = tools[tool_name]
        schema = tool.get("schema", {})
        violations.extend([{**v, "step": step_i, "tool": tool_name} for v in _schema_check(schema, args)])

        # policy: confirmation required
        if tool.get("policy", {}).get("requires_confirmation", False):
            if not step.get("confirmed", False):
                violations.append({"type": "policy_missing_confirmation", "detail": tool_name, "step": step_i})

        # side-effect: duplicates for non-idempotent tools
        se = tool.get("contract", {}).get("side_effect", {})
        if not se.get("idempotent", True):
            signature = (tool_name, str(args))
            if signature in seen_nonidempotent:
                violations.append({"type": "duplicate_side_effect", "detail": tool_name, "step": step_i})
            seen_nonidempotent.add(signature)

        # env-level violations from execution can be appended in step["env_violations"]
        for ev in step.get("env_violations", []):
            violations.append({**ev, "step": step_i, "tool": tool_name})

    return violations
