from __future__ import annotations

from collections import Counter
from typing import Any

import numpy as np


def corr_success_ecs(rows: list[dict[str, Any]]) -> float | None:
    if len(rows) < 2:
        return None
    s = np.array([float(r.get("success", 0.0)) for r in rows], float)
    e = np.array([float(r.get("ecs", 0.0)) for r in rows], float)
    if np.std(s) < 1e-12 or np.std(e) < 1e-12:
        return None
    return float(np.corrcoef(s, e)[0, 1])


def mean_ecs_success(rows: list[dict[str, Any]]) -> float | None:
    srows = [r for r in rows if float(r.get("success", 0.0)) == 1.0]
    if not srows:
        return None
    e = np.array([float(r.get("ecs", 0.0)) for r in srows], float)
    return float(e.mean())


def oeg(rows: list[dict[str, Any]], tau: float = 0.5) -> float | None:
    srows = [r for r in rows if float(r.get("success", 0.0)) == 1.0]
    if not srows:
        return None
    e = np.array([float(r.get("ecs", 0.0)) for r in srows], float)
    return float((e < tau).mean())


def top_violations(rows: list[dict[str, Any]], k: int = 10) -> list[tuple[str, int]]:
    vt: list[str] = []
    for r in rows:
        for v in r.get("violations", []) or []:
            t = v.get("type")
            if isinstance(t, str):
                vt.append(t)
    return Counter(vt).most_common(k)


def summarize(rows: list[dict[str, Any]], tau: float = 0.5) -> dict[str, Any]:
    n = len(rows)
    succ = sum(float(r.get("success", 0.0)) == 1.0 for r in rows)
    ecs = np.array([float(r.get("ecs", 0.0)) for r in rows], float) if rows else np.array([])

    return {
        "rows": n,
        "success_rate": float(succ / n) if n else None,
        "ecs_mean_all": float(ecs.mean()) if n else None,
        "ecs_mean_success": mean_ecs_success(rows),
        "oeg_tau": oeg(rows, tau=tau),
        "corr_success_ecs": corr_success_ecs(rows),
        "top_violations": top_violations(rows, k=8),
    }


def summarize_by_agent(rows: list[dict[str, Any]], tau: float = 0.5) -> list[dict[str, Any]]:
    agents = sorted({str(r.get("agent_type", "")) for r in rows})
    out: list[dict[str, Any]] = []
    for a in agents:
        sub = [r for r in rows if str(r.get("agent_type", "")) == a]
        s = summarize(sub, tau=tau)
        s["agent_type"] = a
        out.append(s)
    return out