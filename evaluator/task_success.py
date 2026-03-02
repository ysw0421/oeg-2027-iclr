# evaluator/task_success.py
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
        filt = [
            c
            for c in charges
            if abs(float(c.get("amount")) - amount) < 1e-9 and c.get("currency") == currency
        ]
        return len(filt) == count

    if t == "refunds_exactly":
        count = int(criteria.get("count", 1))
        refunds = env.state.refunds

        # 강화: refund가 실제 charge를 참조해야 success로 인정
        valid = [
            r
            for r in refunds
            if isinstance(r.get("charge_id"), str) and r["charge_id"] in env.state.charges
        ]
        return len(valid) == count

    if t == "emails_sent_exactly":
        count = int(criteria.get("count", 1))
        to = criteria.get("to")
        subject = criteria.get("subject")

        emails = env.state.emails_sent
        filt = [e for e in emails if e.get("to") == to and e.get("subject") == subject]
        return len(filt) == count

    if t == "events_created_exactly":
        count = int(criteria.get("count", 1))
        title = criteria.get("title")
        start = criteria.get("start")
        end = criteria.get("end")

        events = list(env.state.events.values())
        filt = [
            ev
            for ev in events
            if ev.get("title") == title and ev.get("start") == start and ev.get("end") == end
        ]
        return len(filt) == count

    return False