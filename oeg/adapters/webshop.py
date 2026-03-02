from __future__ import annotations

from typing import Any


def to_oeg_step(action: dict[str, Any]) -> dict[str, Any]:
    """
    Map an external WebShop-like action dict to OEG step format.

    Accepts keys like:
      - action / tool / name / type
      - args / arguments / params
      - confirmed / confirmation
    """
    tool = (
        action.get("action")
        or action.get("tool")
        or action.get("name")
        or action.get("type")
    )

    args = (
        action.get("args")
        or action.get("arguments")
        or action.get("params")
        or {}
    )

    if tool is None:
        tool = "unknown_tool"

    if not isinstance(args, dict):
        args = {}

    confirmed = action.get("confirmed")
    if confirmed is None:
        confirmed = action.get("confirmation")
    confirmed = bool(confirmed) if confirmed is not None else False

    return {
        "tool": str(tool),
        "args": args,
        "confirmed": confirmed,
    }


def convert_trace(actions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for a in actions:
        if isinstance(a, dict):
            out.append(to_oeg_step(a))
    return out