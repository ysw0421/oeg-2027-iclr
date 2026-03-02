from __future__ import annotations

import argparse

from oeg.runners.sandbox_runner import run_sandbox


def main() -> None:
    ap = argparse.ArgumentParser(description="Run sandbox OEG experiments (SSOT runner).")
    ap.add_argument("--tools", default="tools/tools_sandbox.yaml")
    ap.add_argument("--tasks", default="tasks/tasks.json")
    ap.add_argument("--out", default="runs/run_sandbox.jsonl")
    ap.add_argument("--weights", default="")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--n_per_task", type=int, default=40)
    ap.add_argument("--p_baseline", type=float, default=0.5)
    ap.add_argument("--p_careful", type=float, default=0.5)
    ap.add_argument("--p_mitigated", type=float, default=0.0)
    args = ap.parse_args()

    run_sandbox(
        tools_yaml=args.tools,
        tasks_json=args.tasks,
        out_jsonl=args.out,
        weights_path=args.weights or None,
        seed=args.seed,
        n_per_task=args.n_per_task,
        p_baseline=args.p_baseline,
        p_careful=args.p_careful,
        p_mitigated=args.p_mitigated,
    )


if __name__ == "__main__":
    main()