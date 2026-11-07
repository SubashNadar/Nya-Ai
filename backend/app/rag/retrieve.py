"""Hybrid retrieval over the law library, called by the LangGraph researcher nodes in R1.

Order, as in the agent plan: filter by the acts in force on the date, fetch any section the
question names exactly, then run vector search and Postgres full-text search together and merge
them by reciprocal rank fusion. The top 5 go back as `Evidence`.
"""

import re
from datetime import date

from llama_index.core import VectorStoreIndex
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.llms import MockLLM
from llama_index.core.retrievers import QueryFusionRetriever
from llama_index.core.vector_stores import (
    FilterCondition,
    FilterOperator,
    MetadataFilter,
    MetadataFilters,
)
from pydantic import BaseModel
from sqlalchemy.engine import Engine

from app.core import costs
from app.rag import tables
from app.rag.acts import ACTS, acts_in_force

ACT_NAMES = {
    "BNS": r"BNS|Bharatiya Nyaya Sanhita",
    "BNSS": r"BNSS|Bharatiya Nagarik Suraksha Sanhita",
    "BSA": r"BSA|Bharatiya Sakshya Adhiniyam",
    "IPC": r"IPC|Indian Penal Code",
}
_ACT = "|".join(f"(?P<{k}>{v})" for k, v in ACT_NAMES.items())
_NUM = r"(?P<num>\d{1,3}[A-Z]{0,2})"
# "IPC 420", "BNS §303", "section 138", "s. 379 IPC", "Sec 154 of the BNSS".
REF_PATTERNS = [
    re.compile(rf"\b(?:{_ACT})\s*(?:section|sec\.?|s\.|§)?\s*{_NUM}\b", re.IGNORECASE),
    re.compile(rf"(?:\bsection|\bsec\.?|\bs\.|§)\s*{_NUM}\b(?:\s*(?:of\s+(?:the\s+)?)?(?:{_ACT}))?", re.IGNORECASE),
]


class Evidence(BaseModel):
    act: str
    section: str
    heading: str
    text: str
    page: str | None = None
    source_url: str | None = None
    score: float
    found_by: str  # "exact" or "hybrid"


def section_refs(question: str) -> list[tuple[str | None, str]]:
    """Sections the question names, with the act when it says which one."""
    refs: list[tuple[str | None, str]] = []
    for pat in REF_PATTERNS:
        for m in pat.finditer(question):
            act = next((k for k in ACT_NAMES if m.groupdict().get(k)), None)
            ref = (act, m.group("num").upper())
            if ref not in refs and (None, ref[1]) not in refs:
                refs.append(ref)
    # Prefer the act-qualified form when the same number appears both ways.
    return [r for r in refs if r[0] or not any(o[1] == r[1] and o[0] for o in refs)]


def date_filters(acts: list[str], as_of: date) -> MetadataFilters:
    day = as_of.isoformat()
    return MetadataFilters(
        filters=[
            MetadataFilter(key="act", value=acts, operator=FilterOperator.IN),
            MetadataFilter(key="effective_from", value=day, operator=FilterOperator.LTE),
            MetadataFilter(key="effective_to", value=day, operator=FilterOperator.GTE),
        ],
        condition=FilterCondition.AND,
    )


class LawLibrary:
    def __init__(self, engine: Engine, embed: BaseEmbedding, vector_store=None, top_k: int = 5):
        from app.rag import index

        self.engine, self.top_k = engine, top_k
        self.index = VectorStoreIndex.from_vector_store(vector_store or index.vector_store(), embed_model=embed)

    def exact(self, refs: list[tuple[str | None, str]], acts: list[str]) -> list[Evidence]:
        out = []
        for act, num in refs:
            for code in [act] if act else acts:
                if act and code not in acts:
                    continue  # named act not in force on the date; the temporal node explains why
                row = tables.get_section(self.engine, code, num)
                if row:
                    out.append(
                        Evidence(
                            act=code,
                            section=num,
                            heading=row["heading"],
                            text=row["text"],
                            page=row["page"],
                            score=1.0,
                            found_by="exact",
                        )
                    )
        return out

    def search(self, question: str, as_of: date | None = None, acts: list[str] | None = None) -> list[Evidence]:
        as_of = as_of or date.today()
        scope = acts_in_force(as_of, acts)
        if not scope:
            return []
        evidence = self.exact(section_refs(question), scope)

        filters = date_filters(scope, as_of)
        vector = self.index.as_retriever(similarity_top_k=10, filters=filters)
        text = self.index.as_retriever(vector_store_query_mode="text_search", sparse_top_k=10, filters=filters)
        fused = QueryFusionRetriever(
            [vector, text],
            mode="reciprocal_rerank",
            num_queries=1,
            similarity_top_k=self.top_k * 2,
            use_async=False,
            # The LLM only rewrites queries, which num_queries=1 turns off; this stops LlamaIndex
            # from loading its default OpenAI model.
            llm=MockLLM(),
        ).retrieve(question)
        costs.record_embeddings("embed query", [question])

        seen = {(e.act, e.section) for e in evidence}
        for hit in fused:
            m = hit.node.metadata
            key = (m["act"], m["section"])
            if key in seen:
                continue
            seen.add(key)
            evidence.append(
                Evidence(
                    act=m["act"],
                    section=m["section"],
                    heading=m["heading"],
                    text=hit.node.get_content(),
                    page=m.get("page"),
                    source_url=m.get("source_url") or None,
                    score=float(hit.score or 0),
                    found_by="hybrid",
                )
            )
        return evidence[: self.top_k]


def act_title(code: str) -> str:
    return ACTS[code].title if code in ACTS else code
