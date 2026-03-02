from __future__ import annotations
from typing import Dict, List, Tuple

# severity weights (tune later + sensitivity analysis)
DEFAULT_WEIGHTS: Dict[str, float] = {
    "tool_hallucination": 5.0,
    "schema_missing": 2.0,
    "schema_type": 2.0,
    "schema_extra_field": 1.0,
    "precondition_failure": 3.0,
    "postcondition_failure": 3.0,
    "policy_missing_confirmation": 4.0,
    "duplicate_side_effect": 5.0,
    "tool_not_implemented": 1.0,
    "precondition_unknown": 1.0,
}

def compute_ecs(violations: List[dict], *, weights: Dict[str, float] | None = None) -> Tuple[float, float]:
    """
    Returns (ecs, penalty).
    ecs in [0, 1], where 1 = perfect execution (no violations).
    penalty is weighted sum.
    """
    w = weights or DEFAULT_WEIGHTS
    penalty = 0.0
    for v in violations:
        penalty += float(w.get(v.get("type", ""), 1.0))

    # simple normalization: ECS = 1 / (1 + penalty)
    # (smooth, bounded, doesn't require knowing max possible)
    ecs = 1.0 / (1.0 + penalty)
    return ecs, penalty

def compute_success(trajectory: List[dict]) -> float:
    """
    Temporary success definition (MVP):
    success = 1 if all env_response.ok == True, else 0
    Later we will replace this with task-specific success validators.
    """
    for step in trajectory:
        resp = step.get("env_response", {})
        if not resp or resp.get("ok") is not True:
            return 0.0
    return 1.0
