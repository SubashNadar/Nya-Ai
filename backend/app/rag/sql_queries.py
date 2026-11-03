"""Parameterized queries the SQL agent may run, instead of writing SQL itself.

The agent picks a template by name and fills its parameters; values are always bound, never
formatted into the SQL text. This keeps the "SQL agent" safe from injection and makes SQL
correctness measurable: each golden SQL question has one template call and a ground-truth result.
"""

from collections.abc import Callable
from datetime import date

from sqlalchemy import and_, func, or_, select
from sqlalchemy.engine import Engine

from app.rag.tables import acts, offence_class, section_map, sections


def replacement(engine: Engine, old_act: str, old_section: str) -> list[list[str]]:
    """New sections that replaced an old one (IPC 420 -> BNS 318(4))."""
    q = (
        select(section_map.c.new_act, section_map.c.new_section)
        .where(section_map.c.old_act == old_act, section_map.c.old_section == old_section)
        .order_by(section_map.c.new_act, section_map.c.new_section)
    )
    with engine.connect() as conn:
        return [list(r) for r in conn.execute(q)]


def new_offences(engine: Engine, act: str) -> list[str]:
    """Sections of a new code with no old section before them."""
    q = (
        select(section_map.c.new_section)
        .where(section_map.c.new_act == act, or_(section_map.c.old_act == "", section_map.c.old_act.is_(None)))
        .order_by(section_map.c.new_section)
    )
    with engine.connect() as conn:
        return [r[0] for r in conn.execute(q)]


def in_force_from(engine: Engine, code: str) -> str | None:
    with engine.connect() as conn:
        day = conn.execute(select(acts.c.in_force_from).where(acts.c.code == code)).scalar()
    return day.isoformat() if day else None


def acts_in_force_on(engine: Engine, day: str) -> list[str]:
    d = date.fromisoformat(day)
    q = (
        select(acts.c.code)
        .where(acts.c.in_force_from <= d, or_(acts.c.repealed_on.is_(None), acts.c.repealed_on > d))
        .order_by(acts.c.code)
    )
    with engine.connect() as conn:
        return [r[0] for r in conn.execute(q)]


def repealed_in(engine: Engine, year: int) -> list[list[str]]:
    q = (
        select(acts.c.code, acts.c.replaced_by)
        .where(and_(acts.c.repealed_on >= date(year, 1, 1), acts.c.repealed_on <= date(year, 12, 31)))
        .order_by(acts.c.code)
    )
    with engine.connect() as conn:
        return [list(r) for r in conn.execute(q)]


def offence(engine: Engine, act: str, section: str) -> dict | None:
    q = select(offence_class).where(offence_class.c.act == act, offence_class.c.section == section)
    with engine.connect() as conn:
        row = conn.execute(q).mappings().first()
    return dict(row) if row else None


def count_offences(engine: Engine, act: str, bailable: bool) -> int:
    q = select(func.count()).where(offence_class.c.act == act, offence_class.c.bailable.is_(bailable))
    with engine.connect() as conn:
        return int(conn.execute(q).scalar() or 0)


def life_or_death(engine: Engine, act: str) -> list[str]:
    q = (
        select(offence_class.c.section)
        .where(offence_class.c.act == act, offence_class.c.life_or_death.is_(True))
        .order_by(offence_class.c.section)
    )
    with engine.connect() as conn:
        return [r[0] for r in conn.execute(q)]


def section_count(engine: Engine, act: str) -> int:
    with engine.connect() as conn:
        return int(conn.execute(select(func.count()).where(sections.c.act == act)).scalar() or 0)


TEMPLATES: dict[str, Callable] = {
    f.__name__: f
    for f in (
        replacement,
        new_offences,
        in_force_from,
        acts_in_force_on,
        repealed_in,
        offence,
        count_offences,
        life_or_death,
        section_count,
    )
}


def run(engine: Engine, template: str, **params):
    if template not in TEMPLATES:
        raise ValueError(f"unknown SQL template {template!r}")
    return TEMPLATES[template](engine, **params)
