"""Split a bare act into one node per section, the way India Code prints it.

India Code PDFs start a section with its number and marginal heading followed by an em dash,
for example `303. Theft.—(1) Whoever ...`. The "Arrangement of Sections" at the front lists the
same headings without the dash, so it is skipped. Explanations and illustrations stay with their
section. Sections longer than about `max_tokens` are split at sub-section markers `(1)`, `(2)`.
"""

import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from llama_index.core.node_parser import NodeParser
from llama_index.core.schema import BaseNode, Document, NodeRelationship, TextNode

# An amendment marker may come first ("1*[34. Acts done ..."), and the dash may follow the number
# directly ("255.—Public servant ..."). A long heading wraps onto up to two more lines, across a
# page number if a page breaks inside it ("69. Termination ... part\n112\n\nof fine.—"), as long
# as no line starts another numbered section or a sub-heading such as "B.—Imprisonment".
_PREFIX = r"^[ \t]*(?:\d{1,2}[ \t]*\*[ \t]*)?\[?[ \t]*(?P<num>\d{1,3}[A-Z]{0,2})\."
# Lookahead: the text here does not start another numbered section.
_NOT_SECTION = r"(?!(?:\d{1,2}[ \t]*\*[ \t]*)?\[?[ \t]*\d{1,3}[A-Z]{0,2}\.(?:\s|[—–]))"
_WRAP = (
    r"(?:\n[ \t]*\d{1,4}[ \t]*)?(?:\n[ \t]*(?=\n))*\n[ \t]*" + _NOT_SECTION + r"(?![A-Z]{1,3}\.[ \t]*[—–])"
    r"[^\s—–][^\n—–]{0,219}?"
)
SECTION_START = re.compile(
    _PREFIX + r"(?:\s*+[—–]\s*+|\s++)" + _NOT_SECTION + r"(?P<heading>[^\s—–][^\n—–]{1,219}?(?:" + _WRAP + r"){0,2})"
    r"\.?\s*(?:—|–|-{2}|-[ \t]+-|\.-)\s*",
    re.MULTILINE,
)
# A repealed section keeps its number and bracketed heading: "13.\n[Definition of "Queen".] Rep. by ...".
REPEALED = re.compile(_PREFIX + r"\s*\[(?P<heading>[^\]]{2,300}?)\.?\]\s*Rep\.", re.MULTILINE)
# Some PDFs drop the opening bracket: "16.\nDefinition of "Government of India".] Rep., ibid."
REPEALED_OPEN = re.compile(_PREFIX + r"[ \t]*\n?[ \t]*(?P<heading>[^\[\]\n]{2,200}?)\.?\]\s*Rep\.", re.MULTILINE)
# A run of sections repealed together: "161 to 165A.Rep. by the Prevention of Corruption Act, 1988".
REPEALED_RANGE = re.compile(
    r"^[ \t]*(?P<a>\d{1,3})[A-Z]{0,2}[ \t]+to[ \t]+(?P<b>\d{1,3})(?P<bl>[A-Z]{0,2})\.\s*\[?[^\n]{0,120}?Rep\.",
    re.MULTILINE,
)
# Misprints in the official PDFs, fixed before parsing. Each is the exact printed text and its fix.
ERRATA: dict[str, list[tuple[str, str]]] = {
    # The body of IPC 330 is printed as "320." (its margin note says 330).
    "IPC": [
        ("320. Voluntarily causing hurt to extort confession", "330. Voluntarily causing hurt to extort confession")
    ],
}
CHAPTER = re.compile(r"^\s*CHAPTER\s+(?P<num>[IVXLC]+[A-Z]?)\s*\n\s*(?P<title>[^\n]{3,200})", re.MULTILINE)
# Amendment footnotes India Code prints at the foot of a page, e.g. "1. Subs. by Act 5 of 2009".
FOOTNOTE = re.compile(r"^\s*\d{1,2}\.\s+(?:Subs|Ins|Omitted|Rep|Added|The words|Cl|Sub-section)\b.*$", re.MULTILINE)
SUBSECTION = re.compile(r"(?=\(\d{1,2}\)\s)")


@dataclass
class SectionStart:
    pos: int
    num: str
    heading: str


def section_key(num: str) -> tuple[int, str]:
    m = re.match(r"(\d+)([A-Z]*)", num)
    assert m
    return int(m.group(1)), m.group(2)


def approx_tokens(text: str) -> int:
    return int(len(text.split()) * 1.3)


class SectionNodeParser(NodeParser):
    """Turns one whole-act Document into section nodes with act and date metadata.

    The Document's metadata must carry `act`, `effective_from`, `effective_to` and `source_url`.
    It may carry `page_starts`: a list of `[char_offset, page_label]` so each node gets the page
    its section starts on.
    """

    max_tokens: int = 800

    def _parse_nodes(self, nodes: Sequence[BaseNode], show_progress: bool = False, **kwargs: Any) -> list[BaseNode]:
        out: list[BaseNode] = []
        for node in nodes:
            out.extend(self.split_act(node))
        return out

    def split_act(self, doc: BaseNode) -> list[TextNode]:
        meta = dict(doc.metadata)
        page_starts: list[list[Any]] = meta.pop("page_starts", None) or []
        act = meta["act"]
        text = FOOTNOTE.sub("", doc.get_content())
        for printed, fixed in ERRATA.get(act, []):
            text = text.replace(printed, fixed)

        chapters = [(m.start(), m.group("num"), m.group("title").strip()) for m in CHAPTER.finditer(text)]
        starts = self._section_starts(text)

        nodes: list[TextNode] = []
        for i, m in enumerate(starts):
            # Sections repealed as a range share one start; each gets the range's text.
            end = next((s.pos for s in starts[i + 1 :] if s.pos > m.pos), len(text))
            # A chapter heading printed between two sections belongs to the next one.
            end = min([end] + [pos for pos, _, _ in chapters if m.pos < pos < end])
            body = re.sub(r"[ \t]+", " ", text[m.pos : end]).strip()
            num, heading = m.num, m.heading
            chapter = next(((c, t) for pos, c, t in reversed(chapters) if pos < m.pos), (None, None))
            base = {
                **meta,
                "section": num,
                "heading": heading,
                "chapter": chapter[0],
                "chapter_title": chapter[1],
                "page": self._page_at(page_starts, m.pos),
            }
            parts = self._split_long(body)
            for p, part in enumerate(parts):
                node = TextNode(
                    id_=f"{act}-{num}" + (f"-p{p + 1}" if len(parts) > 1 else ""),
                    text=part,
                    metadata={**base, "part": p + 1, "parts": len(parts)},
                    excluded_embed_metadata_keys=[
                        "source_url",
                        "page",
                        "part",
                        "parts",
                        "effective_from",
                        "effective_to",
                    ],
                    excluded_llm_metadata_keys=["source_url", "part", "parts"],
                    # Links the node to its act, so re-ingesting a changed act deletes its old vectors.
                    relationships={NodeRelationship.SOURCE: doc.as_related_node_info()},
                )
                nodes.append(node)
        return nodes

    def _section_starts(self, text: str) -> list[SectionStart]:
        """Section heading matches in order, dropping false hits.

        Real section numbers rise through the act, so the longest run of matches whose numbers
        keep rising is kept. A stray hit, such as an "Arrangement of Sections" entry or a
        cross-reference at a line start, falls outside that run and is dropped without taking the
        sections after it down too.
        """
        found = [
            SectionStart(m.start(), m.group("num"), " ".join(m.group("heading").split()))
            for rx in (SECTION_START, REPEALED, REPEALED_OPEN)
            for m in rx.finditer(text)
        ]
        for m in REPEALED_RANGE.finditer(text):
            a, b, letters = int(m.group("a")), int(m.group("b")), m.group("bl")
            if a < b <= a + 50:
                nums = [str(n) for n in range(a, b + 1)] + ([f"{b}{letters}"] if letters else [])
                found += [SectionStart(m.start(), n, "Repealed") for n in nums]
        found.sort(key=lambda s: (s.pos, section_key(s.num)))
        keys = [section_key(s.num) for s in found]
        # Longest strictly increasing subsequence, O(n log n).
        tails: list[int] = []
        prev = [-1] * len(found)
        for i, key in enumerate(keys):
            lo, hi = 0, len(tails)
            while lo < hi:
                mid = (lo + hi) // 2
                if keys[tails[mid]] < key:
                    lo = mid + 1
                else:
                    hi = mid
            prev[i] = tails[lo - 1] if lo else -1
            if lo == len(tails):
                tails.append(i)
            else:
                tails[lo] = i
        kept: list[SectionStart] = []
        i = tails[-1] if tails else -1
        while i != -1:
            kept.append(found[i])
            i = prev[i]
        return kept[::-1]

    def _split_long(self, body: str) -> list[str]:
        if approx_tokens(body) <= self.max_tokens:
            return [body]
        pieces = [p for p in SUBSECTION.split(body) if p.strip()]
        # The section number and heading stay with sub-section (1).
        if len(pieces) > 1 and not pieces[0].lstrip().startswith("("):
            pieces[1] = pieces[0] + pieces[1]
            pieces = pieces[1:]
        parts: list[str] = []
        cur = ""
        for piece in pieces:
            if cur and approx_tokens(cur + piece) > self.max_tokens:
                parts.append(cur.strip())
                cur = piece
            else:
                cur += piece
        if cur.strip():
            parts.append(cur.strip())
        return parts

    @staticmethod
    def _page_at(page_starts: list[list[Any]], offset: int) -> str | None:
        page = None
        for start, label in page_starts:
            if start > offset:
                break
            page = str(label)
        return page


def merge_pages(pages: list[Document], metadata: dict[str, Any]) -> Document:
    """Join PDFReader's one-Document-per-page output into one act Document with page offsets."""
    text, page_starts = "", []
    for d in pages:
        page_starts.append([len(text), d.metadata.get("page_label", "")])
        text += d.get_content() + "\n"
    return Document(text=text, metadata={**metadata, "page_starts": page_starts})
