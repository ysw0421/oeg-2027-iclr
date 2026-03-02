from __future__ import annotations
from typing import Any, Dict
from sandbox.environment import SandboxEnv

def check_success(env: SandboxEnv, criteria: Dict[str, Any]) -> bool:
    t = criteria.get("type")

    if t == "charges_exactly":
        count = int(criteria.get("count", 1))
        amount = float(criteria.get("amount"))
        currency = criteria.get("currency")

        charges = list(env.state.charges.values())
        filt = [c for c in charges if abs(float(c.get("amount")) - amount) < 1e-9 and c.get("currency") == currency]
        return len(filt) == count

    return False
