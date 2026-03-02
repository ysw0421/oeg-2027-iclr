from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple
import uuid
import re
import yaml

EMAIL_RE = re.compile(r"^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$")


def load_tools_yaml(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@dataclass
class SandboxState:
    emails_sent: List[dict] = field(default_factory=list)
    events: Dict[str, dict] = field(default_factory=dict)
    charges: Dict[str, dict] = field(default_factory=dict)
    refunds: List[dict] = field(default_factory=list)


class ToolError(Exception):
    pass


class SandboxEnv:
    def __init__(self, tools_yaml_path: str):
        spec = load_tools_yaml(tools_yaml_path)
        self.tools = {t["name"]: t for t in spec.get("tools", [])}
        self.state = SandboxState()

    # ---------- Validators (preconditions) ----------
    def _check_preconditions(self, tool_name: str, args: dict) -> List[dict]:
        tool = self.tools[tool_name]
        violations = []
        for p in tool.get("contract", {}).get("preconditions", []):
            ptype = p["type"]
            if ptype == "email_valid":
                v = args.get(p["field"])
                if not isinstance(v, str) or not EMAIL_RE.match(v):
                    violations.append({"type": "precondition_failure", "detail": f"invalid_email:{v}"})
            elif ptype == "time_order":
                start = args.get(p["start_field"])
                end = args.get(p["end_field"])
                if not (isinstance(start, str) and isinstance(end, str) and start < end):
                    violations.append({"type": "precondition_failure", "detail": f"time_order:{start}>{end}"})
            elif ptype == "amount_positive":
                amt = args.get(p["field"])
                try:
                    if float(amt) <= 0:
                        violations.append({"type": "precondition_failure", "detail": f"amount_nonpositive:{amt}"})
                except Exception:
                    violations.append({"type": "precondition_failure", "detail": f"amount_not_number:{amt}"})
            elif ptype == "charge_exists":
                cid = args.get(p["field"])
                if cid not in self.state.charges:
                    violations.append({"type": "precondition_failure", "detail": f"charge_missing:{cid}"})
            else:
                # unknown precondition type
                violations.append({"type": "precondition_unknown", "detail": ptype})
        return violations

    # ---------- Tool execution ----------
    def call_tool(self, tool_name: str, args: dict) -> Tuple[dict, List[dict]]:
        if tool_name not in self.tools:
            return {"ok": False, "error": f"unknown_tool:{tool_name}"}, [{"type": "tool_hallucination", "detail": tool_name}]

        # preconditions
        violations = self._check_preconditions(tool_name, args)

        # execute side effects even if precondition failed? (configurable)
        # For now: if precondition failed, do NOT execute, but still return violations.
        if any(v["type"] == "precondition_failure" for v in violations):
            return {"ok": False, "error": "precondition_failed"}, violations

        # execute tool
        if tool_name == "send_email":
            self.state.emails_sent.append({"to": args["to"], "subject": args["subject"], "body": args["body"]})
            return {"ok": True, "result": "email_sent"}, violations

        if tool_name == "create_event":
            eid = str(uuid.uuid4())[:8]
            self.state.events[eid] = {"id": eid, "title": args["title"], "start": args["start"], "end": args["end"]}
            return {"ok": True, "event_id": eid}, violations

        if tool_name == "charge_card":
            cid = str(uuid.uuid4())[:8]
            self.state.charges[cid] = {"id": cid, "amount": float(args["amount"]), "currency": args["currency"], "reason": args["reason"]}
            return {"ok": True, "charge_id": cid}, violations

        if tool_name == "refund_charge":
            cid = args["charge_id"]
            rid = str(uuid.uuid4())[:8]
            self.state.refunds.append({"refund_id": rid, "charge_id": cid})
            return {"ok": True, "refund_id": rid}, violations

        return {"ok": False, "error": "not_implemented"}, [{"type": "tool_not_implemented", "detail": tool_name}]
