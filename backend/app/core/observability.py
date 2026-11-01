"""Langfuse client and masking, shared by ingestion now and the LangGraph graph in R1.

Tracing is off when no Langfuse keys are set, so tests and a first local run need nothing.
"""

import re
from collections.abc import Iterator
from contextlib import contextmanager
from functools import lru_cache
from typing import Any

from app.core.config import get_settings

# Anything that still looks like personal data after the guard node is masked before export.
_MASKS = [
    (re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b"), "[AADHAAR]"),
    (re.compile(r"(?<!\d)(?:\+91[\s-]?)?[6-9]\d{9}(?!\d)"), "[PHONE]"),
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"), "[EMAIL]"),
]


def mask_text(text: str) -> str:
    for pattern, label in _MASKS:
        text = pattern.sub(label, text)
    return text


def _mask(*, data: Any, **_: Any) -> Any:
    if isinstance(data, str):
        return mask_text(data)
    if isinstance(data, dict):
        return {k: _mask(data=v) for k, v in data.items()}
    if isinstance(data, list):
        return [_mask(data=v) for v in data]
    return data


@lru_cache
def langfuse():
    """The Langfuse client, or None when tracing is not configured."""
    s = get_settings()
    if not (s.LANGFUSE_PUBLIC_KEY and s.LANGFUSE_SECRET_KEY):
        return None
    from langfuse import Langfuse

    return Langfuse(
        public_key=s.LANGFUSE_PUBLIC_KEY, secret_key=s.LANGFUSE_SECRET_KEY, base_url=s.LANGFUSE_HOST, mask=_mask
    )


class _NoSpan:
    def update(self, **_: Any) -> None:
        pass


@contextmanager
def span(name: str, **fields: Any) -> Iterator[Any]:
    """A Langfuse span (a trace when it is the outermost), or a no-op without Langfuse."""
    client = langfuse()
    if client is None:
        yield _NoSpan()
        return
    with client.start_as_current_observation(name=name, as_type="span", **fields) as obs:  # pylint: disable=not-context-manager
        yield obs
