from __future__ import annotations

import json
from typing import Any

from oeg.toolspec import (
    allowed_arg_keys,
    is_idempotent,
    load_toolspec,
    requires_confirmation,
)


def mitigate_trajectory(toolspec_path: str, traj: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Contract-aware trajectory sanitizer (SSOT):

      - enforce confirmation if required
      - drop schema extra args
      - remove exact duplicates for non-idempotent tools
    """
    defs = load_toolspec(toolspec_path)

    out: list[dict[str, Any]] = []
    seen_non_idem: set[str] = set()

    for step in traj:
        step2 = dict(step)
        tool = step2.get("tool")

        if not isinstance(tool, str) or tool not in defs:
            out.append(step2)
            continue

        td = defs[tool]

        # 1) enforce confirmation
        if requires_confirmation(td):
            step2["confirmed"] = True

        # 2) drop schema extra args
        args = dict(step2.get("args", {}) or {})
        allowed = allowed_arg_keys(td)
        if allowed is not None:
            args = {k: v for k, v in args.items() if k in allowed}
        step2["args"] = args

        # 3) remove duplicates for non-idempotent tools
        if not is_idempotent(td):
            sig = json.dumps(
                {
                    "tool": tool,
                    "args": args,
                    "confirmed": step2.get("confirmed", None),
                },
                sort_keys=True,
                ensure_ascii=False,
            )
            if sig in seen_non_idem:
                continue
            seen_non_idem.add(sig)

        out.append(step2)

    return out