"""Input and output guardrails: the deterministic safety floor in front of and behind the LLM.

Input (before retrieval or any model call):
- attack detection by type: prompt injection, system-prompt extraction, jailbreak or role-play,
  requests for help with an illegal act, profiling judges, judging a document's authenticity;
- PII redaction (Aadhaar, PAN, phone, email) so neither the model nor Langfuse sees it.

Output (before the user sees an answer):
- source attribution: every citation must be one of the retrieved sections, and an answer must
  cite at least one;
- advice check: no outcome predictions or instructions about the user's own case.

Rules, not a model, so a blocked attack or a redaction never depends on a model being up. The
LLM router in the graph only sees what passes here.
"""

import re
from dataclasses import dataclass, field

ATTACK_TYPES = (
    "prompt_injection",
    "system_prompt_extraction",
    "jailbreak",
    "illegal_assistance",
    "judge_profiling",
    "document_authenticity",
    "pii",
)
BLOCKING = set(ATTACK_TYPES) - {"pii"}  # PII is redacted and the question still answered


def _rx(*patterns: str) -> list[re.Pattern]:
    return [re.compile(p, re.IGNORECASE) for p in patterns]


ATTACKS: dict[str, list[re.Pattern]] = {
    "prompt_injection": _rx(
        r"\b(ignore|disregard|forget|override)\b.{0,30}\b(previous|prior|above|earlier|all)\b.{0,20}"
        r"\b(instructions?|rules|prompts?|guidelines)\b",
        r"#+\s*system\b|\bsystem\s*:",
        r"\bnew (policy|instructions?)\b",
        r"\byou are now\b",
        r"\breveal\b.{0,40}\b(phone numbers?|users?|database|passwords?|api keys?)\b",
    ),
    "system_prompt_extraction": _rx(
        r"\b(print|show|reveal|repeat|tell me|output)\b.{0,30}\b(system prompt|hidden instructions|"
        r"your (instructions|prompt|rules))\b",
    ),
    "jailbreak": _rx(
        r"\brole-?\s?play\b",
        r"\bpretend (you are|to be|you're)\b",
        r"\bDAN\b",
        r"\b(no|without) (rules|restrictions|filters|disclaimers)\b",
        r"\bdeveloper mode\b",
    ),
    "illegal_assistance": _rx(
        r"\b(write|make|create|draft|prepare|generate|get)\b.{0,25}\b(fake|forged|false|bogus)\b",
        r"\bforge\b",
        r"\b(file|lodge|register)\b.{0,15}\bfalse\b.{0,10}\b(fir|complaint|case)\b",
        r"\b(destroy|delete|hide|tamper with)\b.{0,30}\bevidence\b",
        r"\bbribe\b",
        r"\b(threaten|intimidate|pay off)\b.{0,15}\bwitness",
        r"\blaunder\b",
        r"\bwithout (getting|being) caught\b",
    ),
    "judge_profiling": _rx(
        r"\bjudges?\b.{0,60}\b(lenient|strict|soft|harsh|always|never|favou?r|easy|biased|corrupt)\b",
    ),
    "document_authenticity": _rx(
        r"\b(is|if)\b.{0,15}\b(it|this|that|it's|this one)\b.{0,10}\b(genuine|forged|fake|authentic|real)\b",
        r"\b(genuine|authentic)\b.{0,5}\?",
    ),
}

PII: list[tuple[re.Pattern, str]] = [
    (re.compile(r"(?<!\d)\d{4}[\s-]?\d{4}[\s-]?\d{4}(?!\d)"), "[AADHAAR]"),
    (re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b"), "[PAN]"),
    (re.compile(r"(?<!\d)(?:\+91[\s-]?)?[6-9]\d{9}(?!\d)"), "[PHONE]"),
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"), "[EMAIL]"),
]


@dataclass
class InputCheck:
    text: str  # the question with PII redacted; the only form passed on
    attacks: list[str] = field(default_factory=list)
    pii: list[str] = field(default_factory=list)

    @property
    def blocked(self) -> bool:
        return any(a in BLOCKING for a in self.attacks)


def redact(text: str) -> tuple[str, list[str]]:
    found: list[str] = []
    for pattern, label in PII:
        text, n = pattern.subn(label, text)
        if n:
            found.append(label.strip("[]").lower())
    return text, found


def check_input(question: str) -> InputCheck:
    clean, pii = redact(question)
    attacks = [name for name, pats in ATTACKS.items() if any(p.search(clean) for p in pats)]
    if pii:
        attacks.append("pii")
    return InputCheck(text=clean, attacks=attacks, pii=pii)


# ---- output ----

ADVICE = _rx(
    r"\byou (will|would) (definitely |certainly |probably )?(win|lose|get|be (acquitted|convicted|granted))\b",
    r"\byour (case|chances) (is|are) (strong|weak|good|bad)\b",
    r"\byou should (sue|plead|confess|settle|not cooperate)\b",
    r"\b\d+ ?% chance\b",
)
CITATION = re.compile(r"\b(BNS|BNSS|BSA|IPC)\s*(?:§|section|sec\.?|s\.)?\s*(\d{1,3}[A-Z]{0,2})", re.IGNORECASE)


def citations(text: str) -> set[tuple[str, str]]:
    return {(a.upper(), s.upper()) for a, s in CITATION.findall(text)}


@dataclass
class OutputCheck:
    cited: set[tuple[str, str]]
    unsupported: set[tuple[str, str]]  # cited but not among the retrieved sections
    advice: list[str]

    @property
    def attributed(self) -> bool:
        """Source attribution: at least one citation, and every citation was retrieved."""
        return bool(self.cited) and not self.unsupported

    @property
    def ok(self) -> bool:
        return self.attributed and not self.advice


def check_output(answer: str, evidence: list[tuple[str, str]]) -> OutputCheck:
    cited = citations(answer)
    retrieved = {(a.upper(), s.upper()) for a, s in evidence}
    advice = [m.group(0) for p in ADVICE for m in [p.search(answer)] if m]
    return OutputCheck(cited=cited, unsupported=cited - retrieved, advice=advice)
