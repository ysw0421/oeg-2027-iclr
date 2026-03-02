from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

from evaluator.scoring import compute_ecs
from evaluator.task_success import check_success
from evaluator.violation_checker import check_trajectory
from oeg.io import save_jsonl
from oeg.mitigation import mitigate_trajectory
from oeg.toolspec import load_toolspec
from sandbox.environment import SandboxEnv


def load_tasks(path: str) -> list[dict[str, Any]]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def crit_type(task: dict[str, Any]) -> str:
    return str((task.get("criteria") or {}).get("type", ""))


def _load_weights(path: str | None) -> dict[str, float] | None:
    if not path:
        return None
    p = Path(path)
    txt = p.read_text(encoding="utf-8")
    if p.suffix.lower() in [".yaml", ".yml"]:
        import yaml

        obj = yaml.safe_load(txt)
    else:
        obj = json.loads(txt)
    if not isinstance(obj, dict):
        raise ValueError("weights file must be a dict")
    return {str(k): float(v) for k, v in obj.items()}


# -------------------------
# Agents (rule-based)
# -------------------------
def agent_baseline(task: dict[str, Any]) -> list[dict[str, Any]]:
    crit = task["criteria"]
    t = crit_type(task)

    if t == "charges_exactly":
        return [
            {
                "tool": "charge_card",
                "args": {"amount": crit["amount"], "currency": crit["currency"], "reason": "test"},
                "confirmed": False,
            }
        ]

    if t == "refunds_exactly":
        return [
            {"tool": "charge_card", "args": {"amount": 10, "currency": "USD", "reason": "tmp"}, "confirmed": False},
            {"tool": "refund_charge", "args": {"charge_id": "<filled_after_exec>"}, "confirmed": False},
        ]

    if t == "emails_sent_exactly":
        steps = []
        for _ in range(int(crit.get("count", 1))):
            steps.append(
                {
                    "tool": "send_email",
                    "args": {"to": crit["to"], "subject": crit["subject"], "body": "hi", "meta": "x"},
                    "confirmed": True,
                }
            )
        return steps

    if t == "events_created_exactly":
        return [
            {
                "tool": "create_event",
                "args": {
                    "title": crit["title"],
                    "start": crit["start"],
                    "end": crit["end"],
                    "meta": "x",
                },
                "confirmed": True,
            }
        ]

    return []


def agent_careful(task: dict[str, Any]) -> list[dict[str, Any]]:
    crit = task["criteria"]
    t = crit_type(task)

    if t == "charges_exactly":
        return [
            {
                "tool": "charge_card",
                "args": {"amount": crit["amount"], "currency": crit["currency"], "reason": "test"},
                "confirmed": True,
            }
        ]

    if t == "refunds_exactly":
        return [
            {"tool": "charge_card", "args": {"amount": 10, "currency": "USD", "reason": "tmp"}, "confirmed": True},
            {"tool": "refund_charge", "args": {"charge_id": "<filled_after_exec>"}, "confirmed": True},
        ]

    if t == "emails_sent_exactly":
        steps = []
        for _ in range(int(crit.get("count", 1))):
            steps.append(
                {
                    "tool": "send_email",
                    "args": {"to": crit["to"], "subject": crit["subject"], "body": "hi"},
                    "confirmed": True,
                }
            )
        return steps

    if t == "events_created_exactly":
        return [
            {
                "tool": "create_event",
                "args": {"title": crit["title"], "start": crit["start"], "end": crit["end"]},
                "confirmed": True,
            }
        ]

    return []


# -------------------------
# Execution
# -------------------------
def run_one(env: SandboxEnv, tools_yaml: str, traj: list[dict[str, Any]]) -> dict[str, Any]:
    executed: list[dict[str, Any]] = []
    last_charge_id: str | None = None

    for step in traj:
        step2 = dict(step)
        args = dict(step2.get("args", {}) or {})

        if step2.get("tool") == "refund_charge" and args.get("charge_id") == "<filled_after_exec>":
            args["charge_id"] = last_charge_id

        resp, env_v = env.call_tool(step2["tool"], args)

        if step2.get("tool") == "charge_card" and isinstance(resp, dict) and resp.get("ok"):
            cid = resp.get("charge_id")
            if isinstance(cid, str) and cid:
                last_charge_id = cid

        step2["args"] = args
        step2["env_response"] = resp
        step2["env_violations"] = env_v
        executed.append(step2)

    violations = check_trajectory(tools_yaml, executed)
    return {"trajectory": executed, "violations": violations}


def run_sandbox(
    *,
    tools_yaml: str,
    tasks_json: str,
    out_jsonl: str,
    weights_path: str | None,
    seed: int,
    n_per_task: int,
    p_baseline: float,
    p_careful: float,
    p_mitigated: float,
) -> None:
    """
    SSOT sandbox runner.
    Writes JSONL with fields:
      success, ecs, violations, agent_type, criteria_type, trajectory, ...
    """
    random.seed(seed)

    # early fail (toolspec must parse)
    _ = load_toolspec(tools_yaml)

    tasks = load_tasks(tasks_json)
    weights = _load_weights(weights_path)

    s = float(p_baseline) + float(p_careful) + float(p_mitigated)
    if abs(s - 1.0) > 1e-9:
        raise ValueError("p_baseline + p_careful + p_mitigated must sum to 1.0")

    rows: list[dict[str, Any]] = []

    for task in tasks:
        for _ in range(int(n_per_task)):
            rr = random.random()
            if rr < p_baseline:
                agent_type = "baseline"
                traj = agent_baseline(task)
            elif rr < p_baseline + p_careful:
                agent_type = "careful"
                traj = agent_careful(task)
            else:
                agent_type = "mitigated"
                traj = mitigate_trajectory(tools_yaml, agent_baseline(task))

            env = SandboxEnv(tools_yaml)
            row = run_one(env, tools_yaml, traj)

            ecs, penalty = compute_ecs(row["violations"], weights=weights)
            success = 1.0 if check_success(env, task["criteria"]) else 0.0

            rows.append(
                {
                    "task_id": task["task_id"],
                    "criteria_type": crit_type(task),
                    "agent_type": agent_type,
                    "success": success,
                    "ecs": ecs,
                    "penalty": penalty,
                    "n_violations": len(row["violations"]),
                    "trajectory": row["trajectory"],
                    "violations": row["violations"],
                    "seed": seed,
                    "tools_yaml": tools_yaml,
                    "tasks_path": tasks_json,
                    "weights_path": weights_path or "",
                }
            )

    save_jsonl(out_jsonl, rows)