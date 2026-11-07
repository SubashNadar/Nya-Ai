"""Token usage and cost for every Azure call, recorded on Langfuse generations.

Prices come from settings (USD per 1M tokens, `PRICE_*` in `.env`). Usage is always recorded; cost is
computed here and sent as `cost_details`, so a trace shows its cost without relying on Langfuse's own
model table. `nya-agent cost --register-prices` also registers the same prices in Langfuse for its UI.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from functools import lru_cache
from typing import Any

from app.core.config import get_settings
from app.core.observability import langfuse


def prices() -> dict[str, tuple[float, float]]:
    """Deployment name -> (input, output) USD per 1M tokens."""
    s = get_settings()
    return {
        s.AZURE_STRONG_DEPLOYMENT: (s.PRICE_STRONG_INPUT_PER_1M, s.PRICE_STRONG_OUTPUT_PER_1M),
        s.AZURE_SMALL_DEPLOYMENT: (s.PRICE_SMALL_INPUT_PER_1M, s.PRICE_SMALL_OUTPUT_PER_1M),
        s.AZURE_EMBED_DEPLOYMENT: (s.PRICE_EMBED_INPUT_PER_1M, 0.0),
    }


def cost(model: str, input_tokens: int, output_tokens: int = 0) -> dict[str, float]:
    """Langfuse `cost_details` for one call, in USD."""
    pin, pout = prices().get(model, (0.0, 0.0))
    c_in = input_tokens * pin / 1_000_000
    c_out = output_tokens * pout / 1_000_000
    return {"input": c_in, "output": c_out, "total": c_in + c_out}


def usage(input_tokens: int, output_tokens: int = 0) -> dict[str, int]:
    return {"input": input_tokens, "output": output_tokens, "total": input_tokens + output_tokens}


class _NoGeneration:
    def update(self, **_: Any) -> None:
        pass


@contextmanager
def generation(name: str, model: str, **fields: Any) -> Iterator[Any]:
    """A Langfuse generation (nested under the current trace), or a no-op without Langfuse."""
    client = langfuse()
    if client is None:
        yield _NoGeneration()
        return
    with client.start_as_current_observation(name=name, as_type="generation", model=model, **fields) as gen:  # pylint: disable=not-context-manager
        yield gen


def record(gen: Any, model: str, input_tokens: int, output_tokens: int = 0, **fields: Any) -> None:
    """Attach usage and cost to a generation."""
    gen.update(
        usage_details=usage(input_tokens, output_tokens),
        cost_details=cost(model, input_tokens, output_tokens),
        **fields,
    )


@lru_cache
def _encoder():
    import tiktoken

    return tiktoken.get_encoding("cl100k_base")


def count_tokens(texts: list[str]) -> int:
    """Tokens for embedding inputs (text-embedding-3 uses cl100k_base)."""
    enc = _encoder()
    return sum(len(enc.encode(t)) for t in texts)


def record_embeddings(name: str, texts: list[str]) -> int:
    """One generation for a batch of embedding inputs; returns the token count (0 without Langfuse)."""
    if langfuse() is None:
        return 0
    model = get_settings().AZURE_EMBED_DEPLOYMENT
    tokens = count_tokens(texts)
    with generation(name, model, metadata={"inputs": len(texts)}) as gen:
        record(gen, model, tokens)
    return tokens
