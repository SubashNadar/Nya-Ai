"""Limitation periods Nya-AI can flag from a question. Information only: an advocate confirms the date.

Each rule is matched on the question and the cited sections. The clock starts on the incident date
the user gave; with no date the clock is listed without a due date.
"""

import re
from dataclasses import dataclass
from datetime import date, timedelta


@dataclass(frozen=True)
class DeadlineRule:
    pattern: str
    title: str
    rule: str
    days: int = 0
    years: int = 0


RULES: tuple[DeadlineRule, ...] = (
    DeadlineRule(
        r"cheque|\b138\b",
        "Send the demand notice for the bounced cheque",
        "NI Act s.138(b) · within 30 days of the bank's return memo",
        days=30,
    ),
    DeadlineRule(
        r"\brti\b|right to information",
        "File the first RTI appeal",
        "RTI Act 2005 s.19(1) · within 30 days of the reply or the missed deadline",
        days=30,
    ),
    DeadlineRule(
        r"consumer|defective|fake product|seller|e-?commerce|warranty",
        "File a consumer complaint",
        "Consumer Protection Act 2019 s.69 · within 2 years of the cause of action",
        years=2,
    ),
    DeadlineRule(
        r"deposit|salary|wages|unpaid|owes? me|loan|recover (?:my )?money",
        "Claim the money in court",
        "Limitation Act 1963 · 3 years for most money claims",
        years=3,
    ),
)


def add_years(day: date, years: int) -> date:
    try:
        return day.replace(year=day.year + years)
    except ValueError:  # 29 February in a non-leap year
        return day.replace(year=day.year + years, day=28)


def match(text: str) -> DeadlineRule | None:
    lowered = text.lower()
    return next((r for r in RULES if re.search(r.pattern, lowered)), None)


def due_date(rule: DeadlineRule, start: date) -> date:
    return add_years(start, rule.years) + timedelta(days=rule.days)
