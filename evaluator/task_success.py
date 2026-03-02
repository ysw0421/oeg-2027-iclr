from __future__ import annotations
from typing import Any, Dict

from sandbox.environment import SandboxEnv

def check_success(env: SandboxEnv, criteria: Dict[str, Any]) -> bool:
    t = criteria.get("type")

    if t == "emails_sent_exactly":
        to = criteria.get("to")
        count = int(criteria.get("count", 1))
        sent = [e for e in env.state.emails_sent if (to is None or e.get("to") == to)]
        return len(sent) == count

    if t == "charges_exactly":
        count = int(criteria.get("count", 1))
        amount = float(criteria.get("amount"))
        currency = criteria.get("currency")
        charges = list(env.state.charges.values())
        filt = [c for c in charges if abs(float(c.get("amount")) - amount) < 1e-9 and c.get("currency") == currency]
        return len(filt) == count

    if t == "event_exists":
        title = criteria.get("title")
        start = criteria.get("start")
        end = criteria.get("end")
        for ev in env.state.events.values():
            if ev.get("title") == title and ev.get("start") == start and ev.get("end") == end:
                return True
        return False

    # unknown criteria -> fail safe
    return False
