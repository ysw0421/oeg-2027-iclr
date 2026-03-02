from __future__ import annotations
import json, os, random
from typing import Dict, List

from sandbox.environment import SandboxEnv
from evaluator.violation_checker import check_trajectory
from evaluator.scoring import compute_ecs
from evaluator.task_success import check_success

TOOLS_YAML = "tools/tools.yaml"
TASKS_PATH = "tasks/tasks.json"

def load_tasks():
    with open(TASKS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def agent_baseline(task: Dict) -> List[Dict]:
    # succeed often, but violate policy (missing confirmation)
    crit = task["criteria"]
    amt = crit["amount"]; cur = crit["currency"]
    return [{"tool":"charge_card","args":{"amount":amt,"currency":cur,"reason":"test"}, "confirmed": False}]

def agent_careful(task: Dict) -> List[Dict]:
    crit = task["criteria"]
    amt = crit["amount"]; cur = crit["currency"]
    return [{"tool":"charge_card","args":{"amount":amt,"currency":cur,"reason":"test"}, "confirmed": True}]

def run_one(env: SandboxEnv, traj: List[Dict]) -> Dict:
    executed = []
    for step in traj:
        resp, env_v = env.call_tool(step["tool"], step.get("args", {}))
        s2 = dict(step)
        s2["env_response"] = resp
        s2["env_violations"] = env_v
        executed.append(s2)
    violations = check_trajectory(TOOLS_YAML, executed)
    return {"trajectory": executed, "violations": violations}

def main(n_per_task: int = 40):
    tasks = load_tasks()
    os.makedirs("runs", exist_ok=True)
    out_path = "runs/run_tasks_001.jsonl"

    rows = []
    for task in tasks:
        for _ in range(n_per_task):
            agent_type = random.choice(["baseline","careful"])
            env = SandboxEnv(TOOLS_YAML)
            traj = agent_baseline(task) if agent_type == "baseline" else agent_careful(task)

            row = run_one(env, traj)
            ecs, penalty = compute_ecs(row["violations"])
            success = 1.0 if check_success(env, task["criteria"]) else 0.0

            rows.append({
                "task_id": task["task_id"],
                "agent_type": agent_type,
                "success": success,
                "ecs": ecs,
                "penalty": penalty,
                "n_violations": len(row["violations"]),
                "trajectory": row["trajectory"],
                "violations": row["violations"],
            })

    with open(out_path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print("Saved:", out_path, "rows=", len(rows))

if __name__ == "__main__":
    main()
