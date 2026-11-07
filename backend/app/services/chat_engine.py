"""Chat answer generation: keyword rule engine (always available) + optional Claude API.

The rule-engine copy below is reproduced verbatim from the original design spec
§"Rule-engine responses" — do not paraphrase it. Keyword groups are checked in the
exact order listed there; within a group, `message.lower()` substring match, first
group to match wins.
"""

import json
import logging

from app.agents import prompts
from app.core.config import get_settings

logger = logging.getLogger(__name__)

RULES: list[dict] = [
    {
        "keywords": ["theft", "stole", "stolen"],
        "text": (
            "Theft is defined under Section 378 of the Indian Penal Code and punished "
            "under Section 379. In plain language:"
        ),
        "points": [
            "Dishonestly taking movable property out of someone's possession, without consent — that's theft.",
            "Punishment: up to 3 years imprisonment, or a fine, or both.",
            "Theft in a dwelling house (Sec 380) carries up to 7 years.",
        ],
        "citation": "Sources: IPC §378, §379, §380",
    },
    {
        "keywords": ["deposit", "landlord", "rent"],
        "text": "Withheld security deposits are one of India's most common disputes. Your options:",
        "points": [
            "Send a written demand (email/WhatsApp counts) citing the deposit clause in your rent agreement.",
            "Under the Model Tenancy Act 2021, deposits must be returned within one month of vacating.",
            "If ignored, file in consumer or civil court — small claims usually resolve in 3–6 months.",
        ],
        "citation": "Sources: Model Tenancy Act 2021",
    },
    {
        "keywords": ["fir", "police", "complaint"],
        "text": "Filing an FIR is free, and the police are duty-bound to register it. Steps:",
        "points": [
            "Go to the police station with jurisdiction over where the incident happened.",
            "State the facts orally or in writing — under CrPC Section 154 a cognizable offence must be registered.",
            "Collect your free FIR copy. If refused, escalate to the Superintendent of "
            "Police or file online (most states allow it).",
        ],
        "citation": "Sources: CrPC §154",
    },
    {
        "keywords": ["divorce", "marriage"],
        "text": "For divorce, the route depends on your marriage law. The most common path:",
        "points": [
            "Mutual consent divorce (Sec 13B, Hindu Marriage Act) needs 1 year of separation and takes 6–18 months.",
            "Contested divorce requires grounds — cruelty, desertion, adultery — and takes longer.",
            "Maintenance, custody and property can be settled by agreement to speed things up.",
        ],
        "citation": "Sources: Hindu Marriage Act §13B",
    },
    {
        "keywords": ["salary", "notice", "employer", "job"],
        "text": (
            "Notice-period and final-settlement disputes are governed by your contract "
            "plus state Shops & Establishments law:"
        ),
        "points": [
            "Earned salary can never be withheld — it is legally recoverable.",
            "Notice-period buyout depends on your contract; many employers allow it.",
            "A lawyer's legal notice resolves most of these without going to court.",
        ],
        "citation": "Sources: State S&E Acts, Payment of Wages Act",
    },
]

FALLBACK = {
    "text": "Here's some general guidance while I understand your situation better:",
    "points": [
        "Keep every document, message and receipt related to the issue — evidence wins cases.",
        "Write down the timeline of events; dates matter a lot in law.",
        "Most disputes have a limitation period, so acting early protects your rights.",
    ],
    "citation": "",
}

ANTHROPIC_SYSTEM_PROMPT = prompts.BASIC_MODE.text  # app/agents/prompts/basic_mode.py


def rule_engine_answer(message: str) -> dict:
    lowered = message.lower()
    for rule in RULES:
        if any(keyword in lowered for keyword in rule["keywords"]):
            return {"text": rule["text"], "points": rule["points"], "citation": rule["citation"]}
    return dict(FALLBACK)


def _claude_answer(message: str) -> dict | None:
    settings = get_settings()
    if not settings.ANTHROPIC_API_KEY:
        return None
    try:
        from anthropic import Anthropic

        client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        response = client.messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=500,
            system=ANTHROPIC_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": message}],
        )
        raw = "".join(block.text for block in response.content if getattr(block, "type", None) == "text").strip()
        if raw.startswith("```"):
            raw = raw.strip("`")
            if raw.startswith("json"):
                raw = raw[4:]
        parsed = json.loads(raw)
        return {
            "text": str(parsed["text"]),
            "points": [str(p) for p in parsed.get("points", [])],
            "citation": str(parsed.get("citation", "")),
        }
    except Exception:  # noqa: BLE001  # pylint: disable=broad-exception-caught  # any failure falls back to the rule engine
        logger.exception("Anthropic chat call failed; falling back to rule engine")
        return None


def get_answer(message: str) -> dict:
    """Return {"text", "points", "citation"} for a user message.

    Uses the Anthropic API when ANTHROPIC_API_KEY is configured, otherwise (and on any
    API failure) falls back to the verbatim keyword rule engine, which always works
    standalone with zero config.
    """
    claude_result = _claude_answer(message)
    if claude_result is not None:
        return claude_result
    return rule_engine_answer(message)
