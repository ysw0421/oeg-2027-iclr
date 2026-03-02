# experiments/run_task_experiment.py
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Dict, List, Tuple

import yaml

from evaluator.scoring import compute_ecs
from evaluator.task_success import check_success
from evaluator.violation_checker import check_trajectory
from sandbox.environment import SandboxEnv

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TOOLS_YAML = REPO_ROOT / "tools" / "tools.yaml"
DEFAULT_TASKS_PATH = REPO_ROOT / "tasks" / "tasks.json"
DEFAULT_OUT_PATH = REPO_ROOT / "runs" / "run_tasks_001.jsonl"


def load_tasks(tasks_path: Path) -> List[Dict]:
    with open(tasks_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _crit_type(task: Dict) -> str:
    crit = task.get("criteria", {}) or {}
    return str(crit.get("type", ""))


def load_weights(path: str | None) -> Dict[str, float] | None:
    """
    Load a weights dict from JSON or YAML.
    """
    if not path:
        return None
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(path)

    txt = p.read_text(encoding="utf-8")
    if p.suffix.lower() in [".yaml", ".yml"]:
        obj = yaml.safe_load(txt)
    else:
        obj = json.loads(txt)

    if not isinstance(obj, dict):
        raise ValueError("weights file must be a dict")

    return {str(k): float(v) for k, v in obj.items()}


def agent_baseline(task: Dict) -> List[Dict]:
    """
    Baseline agent: tries to succeed but intentionally violates policies/schemas
    so we can generate OEG examples (success=1 with violations>0).
    """
    crit = task["criteria"]
    t = _crit_type(task)

    if t == "charges_exactly":
        amt = crit["amount"]
        cur = crit["currency"]
        return [
            {
                "tool": "charge_card",
                "args": {"amount": amt, "currency": cur, "reason": "test"},
                "confirmed": False,  # policy_missing_confirmation
            }
        ]

    if t == "refunds_exactly":
        # Need a charge_id first, then refund it.
        # We'll fill "<filled_after_exec>" during execution.
        return [
            {
                "tool": "charge_card",
                "args": {"amount": 10, "currency": "USD", "reason": "tmp"},
                "confirmed": False,  # policy_missing_confirmation
            },
            {
                "tool": "refund_charge",
                "args": {"charge_id": "<filled_after_exec>"},
                "confirmed": False,  # policy_missing_confirmation
            },
        ]

    if t == "emails_sent_exactly":
        count = int(crit.get("count", 1))
        to = crit.get("to")
        subject = crit.get("subject")
        steps: List[Dict] = []
        for _ in range(count):
            steps.append(
                {
                    "tool": "send_email",
                    # Add an extra field to trigger schema_extra_field (violation_checker)
                    "args": {"to": to, "subject": subject, "body": "hi", "meta": "x"},
                    "confirmed": True,
                }
            )
        return steps

    if t == "events_created_exactly":
        title = crit.get("title")
        start = crit.get("start")
        end = crit.get("end")
        return [
            {
                "tool": "create_event",
                # Add an extra field to trigger schema_extra_field
                "args": {"title": title, "start": start, "end": end, "meta": "x"},
                "confirmed": True,
            }
        ]

    # Fallback: do nothing
    return []


def agent_careful(task: Dict) -> List[Dict]:
    """
    Careful agent: tries to succeed AND satisfy policies/schemas (higher ECS).
    """
    crit = task["criteria"]
    t = _crit_type(task)

    if t == "charges_exactly":
        amt = crit["amount"]
        cur = crit["currency"]
        return [
            {
                "tool": "charge_card",
                "args": {"amount": amt, "currency": cur, "reason": "test"},
                "confirmed": True,  # policy satisfied
            }
        ]

    if t == "refunds_exactly":
        return [
            {
                "tool": "charge_card",
                "args": {"amount": 10, "currency": "USD", "reason": "tmp"},
                "confirmed": True,
            },
            {
                "tool": "refund_charge",
                "args": {"charge_id": "<filled_after_exec>"},
                "confirmed": True,
            },
        ]

    if t == "emails_sent_exactly":
        count = int(crit.get("count", 1))
        to = crit.get("to")
        subject = crit.get("subject")
        steps: List[Dict] = []
        for _ in range(count):
            steps.append(
                {
                    "tool": "send_email",
                    "args": {"to": to, "subject": subject, "body": "hi"},
                    "confirmed": True,
                }
            )
        return steps

    if t == "events_created_exactly":
        title = crit.get("title")
        start = crit.get("start")
        end = crit.get("end")
        return [
            {
                "tool": "create_event",
                "args": {"title": title, "start": start, "end": end},
                "confirmed": True,
            }
        ]

    return []


def run_one(env: SandboxEnv, tools_yaml: str, traj: List[Dict]) -> Dict:
    """
    Execute a trajectory against the sandbox.
    Also patches placeholder values (e.g., refund_charge needs charge_id).
    """
    executed: List[Dict] = []
    last_charge_id: str | None = None

    for step in traj:
        step2 = dict(step)
        args = dict(step2.get("args", {}) or {})

        # Fill placeholder charge_id after we create a charge
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


def main(
    *,
    tools_yaml: Path,
    tasks_path: Path,
    out_path: Path,
    n_per_task: int,
    seed: int,
    agent_mix: Tuple[float, float],
    weights_path: Path | None,
) -> None:
    random.seed(seed)

    tasks = load_tasks(tasks_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    weights = load_weights(str(weights_path)) if weights_path else None

    rows: List[Dict] = []
    p_baseline, p_careful = agent_mix
    if abs((p_baseline + p_careful) - 1.0) > 1e-9:
        raise ValueError("agent_mix must sum to 1.0 (e.g., 0.5 0.5)")

    for task in tasks:
        for _ in range(n_per_task):
            r = random.random()
            agent_type = "baseline" if r < p_baseline else "careful"

            env = SandboxEnv(str(tools_yaml))
            traj = agent_baseline(task) if agent_type == "baseline" else agent_careful(task)

            row = run_one(env, str(tools_yaml), traj)
            ecs, penalty = compute_ecs(row["violations"], weights=weights)
            success = 1.0 if check_success(env, task["criteria"]) else 0.0

            rows.append(
                {
                    "task_id": task["task_id"],
                    "criteria_type": _crit_type(task),
                    "agent_type": agent_type,
                    "success": success,
                    "ecs": ecs,
                    "penalty": penalty,
                    "n_violations": len(row["violations"]),
                    "trajectory": row["trajectory"],
                    "violations": row["violations"],
                    "seed": seed,
                    "tools_yaml": str(tools_yaml),
                    "tasks_path": str(tasks_path),
                    "weights_path": str(weights_path) if weights_path else "",
                }
            )

    with open(out_path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print("Saved:", str(out_path), "rows=", len(rows))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--tools", type=str, default=str(DEFAULT_TOOLS_YAML))
    ap.add_argument("--tasks", type=str, default=str(DEFAULT_TASKS_PATH))
    ap.add_argument("--out", type=str, default=str(DEFAULT_OUT_PATH))
    ap.add_argument("--weights", type=str, default="")
    ap.add_argument("--n_per_task", type=int, default=40)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--p_baseline", type=float, default=0.5)
    ap.add_argument("--p_careful", type=float, default=0.5)
    args = ap.parse_args()

    weights_path = Path(args.weights) if args.weights else None

    main(
        tools_yaml=Path(args.tools),
        tasks_path=Path(args.tasks),
        out_path=Path(args.out),
        n_per_task=int(args.n_per_task),
        seed=int(args.seed),
        agent_mix=(float(args.p_baseline), float(args.p_careful)),
        weights_path=weights_path,
    )