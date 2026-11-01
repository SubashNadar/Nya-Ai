"""Parser, date and citation logic, without a database."""

from datetime import date
from pathlib import Path

from llama_index.core.schema import Document

from app.evals.golden import parse_golden
from app.rag.acts import ACTS, OPEN_END, acts_in_force
from app.rag.parser import SectionNodeParser, merge_pages
from app.rag.retrieve import section_refs

FIXTURE = (Path(__file__).parent / "fixtures" / "sample_act.txt").read_text()
META = {"act": "BNS", "effective_from": "2024-07-01", "effective_to": OPEN_END, "source_url": "test"}


def _nodes(max_tokens: int = 800):
    half = len(FIXTURE) // 2
    pages = [
        Document(text=FIXTURE[:half], metadata={"page_label": "1"}),
        Document(text=FIXTURE[half:], metadata={"page_label": "2"}),
    ]
    return SectionNodeParser(max_tokens=max_tokens).split_act(merge_pages(pages, META))


def test_splits_one_node_per_section_and_skips_the_arrangement():
    nodes = _nodes()
    assert [n.metadata["section"] for n in nodes] == ["1", "2", "3", "3A", "4"]
    assert nodes[2].metadata["heading"] == "Taking of property"
    assert nodes[2].metadata["chapter"] == "II"
    assert nodes[2].id_ == "BNS-3"


def test_keeps_explanations_and_illustrations_and_drops_footnotes():
    by = {n.metadata["section"]: n for n in _nodes()}
    assert "Explanation.—A thing attached" in by["2"].text
    assert "Subs. by Act" not in by["2"].text
    assert "A moves a pen" in by["3"].text
    assert "CHAPTER II" not in by["2"].text  # chapter heading belongs to the next section


def test_heading_wrapped_onto_a_second_line():
    text = (
        "21. Admissions.—An admission is relevant.\n"
        "22. Confession caused by inducement, threat, coercion or promise, when irrelevant in criminal \n"
        "proceeding.—A confession made by an accused person is irrelevant.\n"
        "23. Next.—Text.\n"
    )
    nodes = SectionNodeParser().split_act(Document(text=text, metadata=META))
    assert [n.metadata["section"] for n in nodes] == ["21", "22", "23"]
    assert nodes[1].metadata["heading"] == (
        "Confession caused by inducement, threat, coercion or promise, when irrelevant in criminal proceeding"
    )


def _sections(text: str) -> dict[str, str]:
    return {
        n.metadata["section"]: n.metadata["heading"]
        for n in SectionNodeParser().split_act(Document(text=text, metadata=META))
    }


def test_layouts_seen_in_the_real_ipc_and_bns():
    text = (
        "12. Public.—The word public.\n"
        '13.\n[Definition of "Queen".] Rep. by the A. O. 1950.\n'
        "1*[34. Acts done by several persons in furtherance of common intention.--When a criminal act.\n"
        "69. Termination of imprisonment on payment of proportional part\n112\n\nof fine.—If, before the expiration.\n"
        "255.—Public servant framing incorrect record.—Whoever, being a public servant.\n"
    )
    assert _sections(text) == {
        "12": "Public",
        "13": 'Definition of "Queen"',
        "34": "Acts done by several persons in furtherance of common intention",
        "69": "Termination of imprisonment on payment of proportional part 112 of fine",
        "255": "Public servant framing incorrect record",
    }


def test_ipc_gaps_found_on_the_real_pdf():
    # Layouts from the India Code IPC that the parser missed: a repealed heading without its
    # opening bracket (16), a dash printed "- -" (158), a range repealed on one line (161 to 165A)
    # and section 330 misprinted as "320." in the body.
    text = (
        '15.\n[Definition of "British India".] Rep. by the A. O. 1937.\n'
        '16. \nDefinition of "Government of India".] Rep., ibid. \n'
        '17. "Government".—The word "Government" denotes.\n'
        "157. Harbouring persons hired for an unlawful assembly.—Whoever harbours.\n"
        "158. Being hired to take part in an unlawful assembly or riot;- -\nWhoever is engaged, or hired.\n\n"
        "159. Affray.—When two or more persons.\n"
        "161 to 165A. \n161 to 165A.Rep. by the Prevention of Corruption Act, 1988 (49 of \n1988), s. 31. \n"
        "166. Public servant disobeying law, with intent to cause injury to any person.—Whoever.\n"
        "320. Grievous hurt.—The following kinds of hurt.\n"
        "329. Voluntarily causing grievous hurt to extort property.—Whoever.\n"
        "330. \nVoluntarily causing hurt to extort confession or to compel \nrestoration of property. \n"
        "320. Voluntarily causing hurt to extort confession or to compel \n"
        "restoration of property.--Whoever voluntarily.\n"
        "331. Voluntarily causing grievous hurt to extort confession.—Whoever.\n"
    )
    nodes = SectionNodeParser().split_act(Document(text=text, metadata={**META, "act": "IPC"}))
    got = {n.metadata["section"]: n.metadata["heading"] for n in nodes}
    assert list(got) == [
        "15",
        "16",
        "17",
        "157",
        "158",
        "159",
        "161",
        "162",
        "163",
        "164",
        "165",
        "165A",
        "166",
        "320",
        "329",
        "330",
        "331",
    ]
    assert got["16"] == 'Definition of "Government of India"'
    assert got["158"] == "Being hired to take part in an unlawful assembly or riot;"
    assert got["163"] == "Repealed"
    assert got["330"].startswith("Voluntarily causing hurt to extort confession")
    assert got["320"] == "Grievous hurt"
    by = {n.metadata["section"]: n.text for n in nodes}
    assert "Prevention of Corruption Act" in by["161"] and "Prevention of Corruption Act" in by["165A"]


def test_a_stray_high_number_does_not_hide_the_sections_after_it():
    # The BNSS list of sections has entries followed by a sub-heading line such as "B.—Imprisonment".
    text = (
        "455. Sentence of death.\n456. Commutation of sentence of death on pregnant woman.\nB.—Imprisonment\n"
        "1. Short title.—(1) This Sanhita.\n2. Definitions.—In this Sanhita.\n3. Construction.—Words.\n"
    )
    assert list(_sections(text)) == ["1", "2", "3"]


def test_page_and_date_metadata():
    by = {n.metadata["section"]: n for n in _nodes()}
    assert by["1"].metadata["page"] == "1"
    assert by["4"].metadata["page"] == "2"
    assert by["4"].metadata["effective_to"] == OPEN_END


def test_long_sections_split_at_sub_sections():
    parts = [n for n in _nodes(max_tokens=25) if n.metadata["section"] == "4"]
    assert len(parts) == 2
    assert parts[1].text.startswith("(2)")
    assert parts[1].id_ == "BNS-4-p2"


def test_acts_in_force_switch_on_1_july_2024():
    assert acts_in_force(date(2024, 3, 12), ["IPC", "BNS"]) == ["IPC"]
    assert acts_in_force(date(2024, 6, 30), ["IPC", "BNS"]) == ["IPC"]
    assert acts_in_force(date(2024, 7, 1), ["IPC", "BNS"]) == ["BNS"]
    assert ACTS["IPC"].effective_to == "2024-06-30"


def test_section_refs():
    assert section_refs("Which BNS section replaced IPC 420?") == [("IPC", "420")]
    assert section_refs("what does section 138 say") == [(None, "138")]
    assert section_refs("Is s. 379 IPC bailable? And BNS §303?") == [("BNS", "303"), ("IPC", "379")]
    assert section_refs("How do I file an FIR?") == []


def test_parse_golden_table(tmp_path):
    md = tmp_path / "g.md"
    md.write_text(
        "| # | Query | Risk | Mode | Escalation | Expected source |\n|---|---|---|---|---|---|\n"
        "| 1 | Theft? | Low | rag | none | BNS §303 |\n"
        "| 15 | WhatsApp? | Medium | rag | none | BSA §§61, 63 |\n"
        "| 29 | 498A? | Medium | hybrid | none | `section_map` → BNS §§85–86 text |\n"
        "| 11 | Consumer? | Low | rag | none | CPA 2019 §2(7) |\n"
    )
    got = {(r.query, r.act, r.section) for r in parse_golden(md)}
    assert got == {
        (1, "BNS", "303"),
        (15, "BSA", "61"),
        (15, "BSA", "63"),
        (29, "BNS", "85"),
        (29, "BNS", "86"),
        (11, "CPA", "2"),
    }


def test_long_runs_of_blank_lines_parse_quickly():
    # PDF text can hold hundreds of whitespace-only lines; an earlier pattern took minutes on them.
    import time

    text = "1. Title.—Text.\n2.\n" + "   \n" * 3000 + "3. Next.—Text.\n"
    start = time.monotonic()
    assert list(_sections(text)) == ["1", "3"]
    assert time.monotonic() - start < 2
