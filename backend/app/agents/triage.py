"""Triage: risk level, route and escalation for a question, decided before any model runs.

- Risk: Critical (someone is in danger now), High (the user's own case, an attack, PII),
  Medium (depends on a date, a state law outside the library, or a sensitive offence), Low.
- Route: `none` (no retrieval: emergency or refusal), `sql` (structured lookup), `rag` (section
  text), `hybrid` (both).
- Escalation: `emergency` (112 and 181 first), `refused`, `advocate_review` (held for an advocate),
  `offer_lawyer`, `none`.

Critical and escalation are rules on purpose: a missed emergency or hand-over must not depend on a
model. The graph's LLM router may refine the route of a `rag`/`sql`/`hybrid` question but can
never lower risk or remove an escalation decided here.
"""

import re
from dataclasses import dataclass, field

from app.agents.guards import InputCheck, check_input


def _rx(*patterns: str) -> list[re.Pattern]:
    return [re.compile(p, re.IGNORECASE) for p in patterns]


def _any(pats: list[re.Pattern], text: str) -> bool:
    return any(p.search(text) for p in pats)


# Danger now, to the user or someone close. First person or present tense, so "what is the
# punishment for attempt to murder" stays Low.
CRITICAL = _rx(
    r"\b(kill|kills|killing|murder|hurt|attack)\b.{0,12}\b(me|us|my \w+|myself)\b",
    r"\bkill (myself|me)\b|\bend (my|his|her) life\b|\b(commit|attempt(ed)?) suicide\b|\bwant to die\b",
    r"\b(beating|hitting|choking|strangling|burning) (me|us|my)\b",
    r"\b(kidnapped|abducted|missing)\b.{0,20}\b(my|our)\b|\bmy \w+\b.{0,20}\b(kidnapped|abducted)\b",
    r"\b(abusing|molesting|assaulting) my\b|\b(raped|molested|sexually assaulted)\b",
    r"\b(has|with|carrying|holding) (an? )?(acid|gun|knife|weapon|pistol)\b",
    r"\b(took|drank|swallowed) poison\b",
    r"\blocked (me|us) (in|up)\b|\bnot giving (me|us) food\b",
    r"\bmaar (raha|rahi|rahe)\b|\bbachao\b",
)

ADVOCATE_REVIEW = _rx(
    r"\b(was|were|been|got|is|are) (arrested|detained)\b|\b(arrested|detained) (my|him|her|them|us)\b",
    r"\bin (police )?custody\b|\bpicked up by (the )?police\b",
    r"\bcustody of\b|\btook (our|my) (son|daughter|child|kids?)\b",
    r"\bsummons\b|\bbail hearing\b|\bhearing (is )?(tomorrow|today|next)\b",
    r"\b(received|got) a legal notice\b|\breply within \d+ days\b",
)
OFFER_LAWYER = _rx(
    r"\bwill i (win|lose)\b|\bshould i sue\b|\bif i sue\b|\bwill the court\b",
    r"\bavoid (being )?arrest",
    r"\bdraft\b.{0,30}\b(for me|my|to my)\b",
    r"\b(talk to|speak to|need|find|book|want) an? (\w+ )?(lawyer|advocate)\b",
    r"\bmy (employer|landlord|landlord's|tenant|company|boss)\b",
)
# State laws and acts outside the R0 library: say so and offer a lawyer instead of guessing.
STATES = (
    r"tamil nadu|karnataka|kerala|maharashtra|delhi|gujarat|rajasthan|punjab|haryana|bihar|"
    r"west bengal|telangana|andhra|odisha|assam|uttar pradesh|madhya pradesh"
)
STATE_LAW = _rx(rf"\b({STATES})\b.{{0,30}}\b(act|law|rules?)\b")

MONTH = (
    r"jan(uary)?|feb(ruary)?|mar(ch)?|apr(il)?|may|june?|july?|aug(ust)?|sep(tember)?|oct(ober)?|"
    r"nov(ember)?|dec(ember)?"
)
INCIDENT_DATE = _rx(rf"\b(\d{{1,2}} )?({MONTH}) (\d{{1,2}}, )?(19|20)\d\d\b", r"\b\d{1,2}[/-]\d{1,2}[/-](19|20)?\d\d\b")
WHICH_LAW = _rx(r"\bwhich laws? appl(y|ies)\b", r"\bis it (the )?(ipc|bns)\b", r"\b(ipc|bns) or (ipc|bns)\b")
SENSITIVE = _rx(r"\b498 ?a\b|\bdowry\b|\bcruelty\b|\blynching\b|\badmissible\b")

SQL = _rx(
    r"\b(which|what) (\w+ )?sections? replaced\b|\bwhat replaced\b|\breplaced (ipc|crpc)\b",
    r"\bcome into force\b|\bin force (from|since)\b|\bwhen did\b",
    r"\bhow many\b|\bcount\b",
    r"\blist (the )?\w*\s?(offences|acts|sections)\b",
    r"\b(cognizable|bailable|non-bailable)\b",
    r"\b(repealed|no equivalent|new in the bns|new offences?|new provision)\b",
    r"\b(talk to|speak to|need|find|book|want) an? (\w+ )?(lawyer|advocate)\b",
)
TEXT = _rx(
    r"\bwhat (exactly )?does (the|this|that|it|bns|bnss|bsa|ipc)?\s?(new )?(section|act|law)? ?(say|\w+ say)\b",
    r"\bwhat is the punishment\b|\bexplain\b|\bwhat they held\b|\bwhat the section says\b",
)
COMPARE = _rx(
    r"\bcompare\b.{0,60}\b(ipc|bns)\b.{0,20}\b(ipc|bns)\b",
    r"\bjudgments?\b.{0,80}\b(and|what)\b",
    r"\b(cases|judgments?)\b.{0,80}\bwhat (they|it|the court) held\b",
)


@dataclass
class Triage:
    risk: str
    route: str
    escalation: str
    attacks: list[str] = field(default_factory=list)
    redacted: str = ""
    reasons: list[str] = field(default_factory=list)

    @property
    def critical(self) -> bool:
        return self.risk == "Critical"


def _route(q: str) -> str:
    dated = _any(INCIDENT_DATE, q) or _any(WHICH_LAW, q)
    sql, text = _any(SQL, q), _any(TEXT, q)
    if dated or _any(COMPARE, q) or (sql and text):
        return "hybrid"
    return "sql" if sql else "rag"


def triage(question: str, guard: InputCheck | None = None) -> Triage:
    guard = guard or check_input(question)
    q = guard.text
    if _any(CRITICAL, q):
        return Triage("Critical", "none", "emergency", guard.attacks, q, ["danger now"])
    if guard.blocked:
        return Triage("High", "none", "refused", guard.attacks, q, ["attack: " + ", ".join(guard.attacks)])

    route = _route(q)
    reasons: list[str] = []
    if _any(ADVOCATE_REVIEW, q):
        escalation = "advocate_review"
        reasons.append("live matter: arrest, custody, court date or notice")
    elif _any(OFFER_LAWYER, q) or _any(STATE_LAW, q):
        escalation = "offer_lawyer"
        reasons.append("own case, lawyer request or law outside the library")
    else:
        escalation = "none"

    own_case = escalation == "advocate_review" or (escalation == "offer_lawyer" and not _lawyer_or_state(q))
    if own_case or guard.pii or re.search(r"\bhow many years will i\b", q, re.IGNORECASE):
        risk = "High"
    elif escalation == "offer_lawyer" or _any(INCIDENT_DATE, q) or _any(WHICH_LAW, q) or _any(SENSITIVE, q):
        risk = "Medium"
    else:
        risk = "Low"
    if guard.pii:
        reasons.append("PII redacted: " + ", ".join(guard.pii))
    return Triage(risk, route, escalation, guard.attacks, q, reasons)


def _lawyer_or_state(q: str) -> bool:
    """A plain request for a lawyer, or a state law: offer a lawyer, but nothing personal at stake."""
    lawyer = re.search(r"\b(talk to|speak to|need|find|book|want) an? (\w+ )?(lawyer|advocate)\b", q, re.IGNORECASE)
    return bool(lawyer or _any(STATE_LAW, q))
