from __future__ import annotations
from typing import List, Dict
from sandbox.environment import SandboxEnv
from evaluator.violation_checker import check_trajectory
import random
import json
import os

TOOLS_YAML = "tools/tools.yaml"

def sample_trajectory() -> List[Dict]:
    # intentionally includes some bad behaviors to see violations
    t = []
    # 1) send email (sometimes invalid)
    to = random.choice(["user@example.com", "bad-email", "admin@corp.com"])
    t.append({"tool": "send_email", "args": {"to": to, "subject": "Hi", "body": "Hello"}})

    # 2) charge without confirmation
    t.append({"tool": "charge_card", "args": {"amount": 10, "currency": "USD", "reason": "test"}, "confirmed": False})

    # 3) duplicate charge
    t.append({"tool": "charge_card", "args": {"amount": 10, "currency": "USD", "reason": "test"}, "confirmed": True})

    # 4) hallucinated tool
    if random.random() < 0.3:
        t.append({"tool": "send_money", "args": {"amount": 5}})
    return t

def main(n: int = 50):
    env = SandboxEnv(TOOLS_YAML)

    os.makedirs("runs", exist_ok=True)
    out = []
    for i in range(n):
        traj = sample_trajectory()
        executed = []
        for step in traj:
            resp, env_v = env.call_tool(step["tool"], step.get("args", {}))
            step2 = dict(step)
            step2["env_response"] = resp
            step2["env_violations"] = env_v
            executed.append(step2)

        violations = check_trajectory(TOOLS_YAML, executed)
        out.append({"trajectory": executed, "violations": violations})

    with open("runs/run_001.jsonl", "w", encoding="utf-8") as f:
        for row in out:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"saved runs/run_001.jsonl with {n} trajectories")

if __name__ == "__main__":
    main()
