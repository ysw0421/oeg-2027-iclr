from __future__ import annotations
import json
import os
from typing import List

import matplotlib.pyplot as plt
import pandas as pd

from evaluator.scoring import compute_ecs, compute_success

RUN_PATH = "runs/run_001.jsonl"

def load_jsonl(path: str) -> List[dict]:
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows

def main():
    rows = load_jsonl(RUN_PATH)

    recs = []
    for i, r in enumerate(rows):
        traj = r["trajectory"]
        violations = r.get("violations", [])
        ecs, penalty = compute_ecs(violations)
        success = compute_success(traj)
        recs.append({
            "idx": i,
            "success": success,
            "ecs": ecs,
            "penalty": penalty,
            "n_violations": len(violations),
        })

    df = pd.DataFrame(recs)
    os.makedirs("plots", exist_ok=True)
    df.to_csv("plots/summary_run_001.csv", index=False)

    # scatter plot
    plt.figure()
    plt.scatter(df["success"], df["ecs"])
    plt.xlabel("Success (MVP)")
    plt.ylabel("Execution Correctness Score (ECS)")
    plt.title("Success vs Execution Correctness (run_001)")
    plt.ylim(0, 1.05)
    plt.xlim(-0.05, 1.05)
    plt.savefig("plots/figure1_scatter_run_001.png", dpi=200)
    print("Saved plots/figure1_scatter_run_001.png and plots/summary_run_001.csv")

    # quick stats
    print(df.describe())

if __name__ == "__main__":
    main()
