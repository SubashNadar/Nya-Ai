"""Azure OpenAI chat calls shared by the safety layer, the graph's writer and SQL picker, and the judge.

Every call returns None when Azure is not configured or the call fails, so callers fall back to
rules or a deterministic answer instead of raising.
"""

import json
import logging

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def azure_configured() -> bool:
    s = get_settings()
    return bool(s.AZURE_OPENAI_ENDPOINT and s.AZURE_OPENAI_API_KEY)


def azure_chat(messages: list[dict], deployment: str | None = None, json_mode: bool = False) -> str | None:
    """One Azure OpenAI chat completion, or None when Azure is not configured or the call fails."""
    s = get_settings()
    if not azure_configured():
        return None
    try:
        from openai import AzureOpenAI

        client = AzureOpenAI(
            azure_endpoint=s.AZURE_OPENAI_ENDPOINT,
            api_key=s.AZURE_OPENAI_API_KEY,
            api_version=s.AZURE_OPENAI_API_VERSION,
        )
        extra = {"response_format": {"type": "json_object"}} if json_mode else {}
        r = client.chat.completions.create(model=deployment or s.AZURE_SMALL_DEPLOYMENT, messages=messages, **extra)
        return r.choices[0].message.content
    except Exception:  # noqa: BLE001  # pylint: disable=broad-exception-caught  # callers fall back
        logger.exception("Azure chat call failed")
        return None


def azure_json(messages: list[dict], deployment: str | None = None) -> dict | None:
    """A JSON-mode completion parsed to a dict, or None."""
    raw = azure_chat(messages, deployment=deployment, json_mode=True)
    if raw is None:
        return None
    try:
        out = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return out if isinstance(out, dict) else None
