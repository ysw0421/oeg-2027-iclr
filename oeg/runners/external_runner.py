from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from evaluator.scoring import compute_ecs
from evaluator.violation_checker import check_trajectory
from oeg.io import save_jsonl
from oeg.mitigation import mitigate_trajectory


def run_external(
    *,
    input_jsonl: str,
    tools_yaml: str,
    out_jsonl: str,
    adapter: Callable[[list[dict[str, Any]]], list[dict[str, Any]]],
    mitigate: bool,
) -> None:
    rows_out: list[dict[str, Any]] = []

    with open(input_jsonl, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            obj: dict[str, Any] = json.loads(line)
            actions = obj.get("actions") or obj.get("trajectory") or obj.get("steps") or []
            if not isinstance(actions, list):
                continue

            traj = adapter(actions)
            if mitigate:
                traj = mitigate_trajectory(tools_yaml, traj)

            violations = check_trajectory(tools_yaml, traj)
            ecs, penalty = compute_ecs(violations)

            rows_out.append(
                {
                    "episode_id": obj.get("episode_id", obj.get("id", "")),
                    "success": float(obj.get("success", obj.get("reward", 0.0)) or 0.0),
                    "ecs": ecs,
                    "penalty": penalty,
                    "n_violations": len(violations),
                    "trajectory": traj,
                    "violations": violations,
                    "source": obj.get("source", "external"),
                    "tools_yaml": tools_yaml,
                    "mitigated": bool(mitigate),
                }
            )

    Path(out_jsonl).parent.mkdir(parents=True, exist_ok=True)
    save_jsonl(out_jsonl, rows_out)
