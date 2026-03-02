from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np

from oeg.io import load_jsonl


def fig1_scatter_success_ecs(rows: list[dict[str, Any]], out_path: str) -> None:
    ecs = np.array([float(r.get("ecs", 0.0)) for r in rows], float)
    succ = np.array([float(r.get("success", 0.0)) for r in rows], float)

    plt.figure(figsize=(5, 4))
    plt.scatter(ecs, succ, alpha=0.3)
    plt.xlabel("ECS")
    plt.ylabel("Success")
    plt.title("Sandbox: Success vs ECS")
    plt.ylim(-0.05, 1.05)
    plt.tight_layout()
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=200)
    plt.close()
    print("saved:", out_path)


def fig2_external_before_after(before: list[dict[str, Any]], after: list[dict[str, Any]], out_path: str) -> None:
    b_s = [r for r in before if float(r.get("success", 0.0)) == 1.0]
    a_s = [r for r in after if float(r.get("success", 0.0)) == 1.0]
    b = np.array([float(r.get("ecs", 0.0)) for r in b_s], float)
    a = np.array([float(r.get("ecs", 0.0)) for r in a_s], float)

    plt.figure(figsize=(5, 3.5))
    plt.scatter(b, np.zeros_like(b), alpha=0.8, label="before")
    plt.scatter(a, np.ones_like(a), alpha=0.8, label="after")
    plt.yticks([0, 1], ["before", "after"])
    plt.xlabel("ECS (success=1)")
    plt.title("External: ECS Before vs After Mitigation")
    plt.xlim(-0.05, 1.05)
    plt.tight_layout()
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=200)
    plt.close()
    print("saved:", out_path)


def fig3_density_oeg(d1: list[dict[str, Any]], d2: list[dict[str, Any]], d3: list[dict[str, Any]], out_path: str, tau: float) -> None:
    def oeg_tau(rows: list[dict[str, Any]]) -> float:
        s = [r for r in rows if float(r.get("success", 0.0)) == 1.0]
        if not s:
            return float("nan")
        ecs = np.array([float(r.get("ecs", 0.0)) for r in s], float)
        return float((ecs < tau).mean())

    xs = np.array([0.0, 1.0, 2.0])
    ys = np.array([oeg_tau(d1), oeg_tau(d2), oeg_tau(d3)])

    plt.figure(figsize=(5, 3.5))
    plt.plot(xs, ys, marker="o")
    plt.xticks(xs, ["d1", "d2", "d3"])
    plt.xlabel("Constraint density level")
    plt.ylabel(f"OEG(tau={tau})")
    plt.title("Constraint Density Sweep: OEG increases")
    plt.ylim(-0.05, 1.05)
    plt.tight_layout()
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=200)
    plt.close()
    print("saved:", out_path)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sandbox", default="runs/run_sandbox.jsonl")
    ap.add_argument("--webshop_before", default="runs/webshop_before.jsonl")
    ap.add_argument("--webshop_after", default="runs/webshop_after.jsonl")
    ap.add_argument("--d1", default="runs/d1.jsonl")
    ap.add_argument("--d2", default="runs/d2.jsonl")
    ap.add_argument("--d3", default="runs/d3.jsonl")
    ap.add_argument("--tau", type=float, default=0.5)
    ap.add_argument("--outdir", default="plots")
    args = ap.parse_args()

    outdir = Path(args.outdir)

    fig1_scatter_success_ecs(load_jsonl(args.sandbox), str(outdir / "fig1_sandbox_success_vs_ecs.png"))
    fig2_external_before_after(
        load_jsonl(args.webshop_before),
        load_jsonl(args.webshop_after),
        str(outdir / "fig2_external_before_after_ecs.png"),
    )
    fig3_density_oeg(
        load_jsonl(args.d1),
        load_jsonl(args.d2),
        load_jsonl(args.d3),
        str(outdir / "fig3_density_oeg.png"),
        tau=float(args.tau),
    )


if __name__ == "__main__":
    main()