"""Check every section the golden queries expect against the ingested text.

Reads the "Expected source" column of `evals/GOLDEN-QUERIES.md` (in legal-docs-platform) and
reports, per query, whether each cited section exists in the `sections` table. Sections of acts
outside the R0 library (RTI Act, NI Act and so on) are listed separately, not counted as missing.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path

from sqlalchemy.engine import Engine

from app.rag import tables
from app.rag.acts import ACTS

# "BNS §303", "BSA §§61, 63", "CPA 2019 §2(7)", "IPC for the offence, BNSS §531 savings".
CITE = re.compile(r"(?P<before>[^;+→§]*?)§§?\s*(?P<nums>\d[\d(),A-Z\s–-]*)")
DROP_WORDS = {"Explains", "the", "for", "procedure", "text", "savings", "dates", "and"}


@dataclass
class GoldenRef:
    query: int
    act: str
    section: str


@dataclass
class GoldenReport:
    found: list[GoldenRef] = field(default_factory=list)
    missing: list[GoldenRef] = field(default_factory=list)
    not_ingested: list[GoldenRef] = field(default_factory=list)  # act in R0 but not loaded yet
    outside_library: list[GoldenRef] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.missing and not self.not_ingested


def _numbers(spec: str) -> list[str]:
    spec = re.sub(r"\(\w+\)", "", spec)  # 318(4) -> 318; sub-sections are checked in R1
    out: list[str] = []
    for part in re.split(r"[,\s]+", spec.strip()):
        if not part:
            continue
        rng = re.fullmatch(r"(\d+)[–-](\d+)", part)
        if rng:
            out += [str(n) for n in range(int(rng.group(1)), int(rng.group(2)) + 1)]
        elif re.fullmatch(r"\d{1,3}[A-Z]{0,2}", part):
            out.append(part)
    return out


def parse_golden(path: Path) -> list[GoldenRef]:
    refs: list[GoldenRef] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 6 or not cells[0].isdigit():
            continue
        q, source = int(cells[0]), cells[-1].replace("`", "")
        for m in CITE.finditer(source):
            words = [w for w in re.split(r"[\s,]+", m.group("before")) if w and w not in DROP_WORDS]
            words = [w for w in words if not re.fullmatch(r"\d{4}", w)]  # "CPA 2019" -> "CPA"
            if not words:
                continue
            act = words[-1] if words[-1] in ACTS else " ".join(words[-3:])
            act = re.sub(r"^.*?\b([A-Z][\w]*(?: [A-Z][\w]*)* Act)$", r"\1", act)
            for num in _numbers(m.group("nums")):
                refs.append(GoldenRef(q, act, num))
    return refs


def check(engine: Engine, path: Path) -> GoldenReport:
    have = tables.existing_sections(engine)
    report = GoldenReport()
    for ref in parse_golden(path):
        if ref.act not in ACTS:
            report.outside_library.append(ref)
        elif ref.act not in have:
            report.not_ingested.append(ref)
        elif ref.section in have[ref.act]:
            report.found.append(ref)
        else:
            report.missing.append(ref)
    return report


def render(report: GoldenReport) -> str:
    def fmt(refs: list[GoldenRef]) -> str:
        return ", ".join(f"Q{r.query} {r.act} §{r.section}" for r in refs) or "none"

    return "\n".join(
        [
            f"found           {len(report.found):>3}  {fmt(report.found)}",
            f"MISSING         {len(report.missing):>3}  {fmt(report.missing)}",
            f"act not loaded  {len(report.not_ingested):>3}  {fmt(report.not_ingested)}",
            f"outside R0      {len(report.outside_library):>3}  {fmt(report.outside_library)}",
            "RESULT: " + ("PASS" if report.ok else "FAIL"),
        ]
    )
