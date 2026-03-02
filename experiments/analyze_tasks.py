from __future__ import annotations
import json
import os
import pandas as pd
import matplotlib.pyplot as plt

RUN_PATH = "runs/run_tasks_001.jsonl"

def load_jsonl(path: str):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows

def main():
    rows = load_jsonl(RUN_PATH)
    df = pd.DataFrame([{
        "task_id": r["task_id"],
        "agent_type": r["agent_type"],
        "success": r["success"],
        "ecs": r["ecs"],
        "penalty": r["penalty"],
        "n_violations": r["n_violations"],
    } for r in rows])

    os.makedirs("plots", exist_ok=True)
    df.to_csv("plots/summary_run_tasks_001.csv", index=False)

    plt.figure()
    plt.scatter(df["success"], df["ecs"])
    plt.xlabel("Task Success")
    plt.ylabel("Execution Correctness Score (ECS)")
    plt.title("OEG: Success vs Execution Correctness (task-driven)")
    plt.ylim(0, 1.05)
    plt.xlim(-0.05, 1.05)
    plt.savefig("plots/figure1_oeg_scatter_tasks.png", dpi=200)
    print("Saved plots/figure1_oeg_scatter_tasks.png")

    print(df.groupby(["agent_type","success"])["ecs"].describe())

if __name__ == "__main__":
    main()
