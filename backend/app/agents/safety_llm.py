"""Second safety layer: a small model classifies the question, and its verdict is OR-ed with the rules.

The rules in `triage` are fast and never down, but they only know the phrasings they were written
for (the red-team stress set shows this). The model catches indirect danger ("I have the pills
ready"), other languages and new attack wording. Combining by the *more cautious* answer means
the model can raise risk or add an escalation, never lower what the rules decided, so recall can
only go up.
"""

import json

from app.agents import prompts
from app.agents.llm import azure_chat
from app.agents.triage import Triage

__all__ = ["azure_chat", "classify", "combine"]

RISK_ORDER = ["Low", "Medium", "High", "Critical"]
ESCALATION_ORDER = ["none", "offer_lawyer", "advocate_review", "refused", "emergency"]

PROMPT = prompts.TRIAGE.text  # app/agents/prompts/triage.py


def classify(question: str) -> dict | None:
    raw = azure_chat(
        [{"role": "system", "content": PROMPT}, {"role": "user", "content": question}],
        json_mode=True,
        name="safety classify",
    )
    if raw is None:
        return None
    try:
        out = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return out if out.get("risk") in RISK_ORDER and out.get("escalation") in ESCALATION_ORDER else None


def combine(rules: Triage, llm: dict | None) -> Triage:
    """The more cautious of the two on risk and escalation; attacks are unioned."""
    if not llm:
        return rules
    risk = max(rules.risk, llm["risk"], key=RISK_ORDER.index)
    escalation = max(rules.escalation, llm["escalation"], key=ESCALATION_ORDER.index)
    attacks = rules.attacks + [a for a in [llm.get("attack")] if a and a not in rules.attacks]
    route = "none" if escalation in ("emergency", "refused") else rules.route
    if route != "none" and rules.route == "rag" and llm.get("route") in ("sql", "hybrid"):
        route = llm["route"]  # rules default to rag; take the model's more specific route
    reasons = rules.reasons + (["raised by the model"] if (risk, escalation) != (rules.risk, rules.escalation) else [])
    return Triage(risk, route, escalation, attacks, rules.redacted, reasons)
