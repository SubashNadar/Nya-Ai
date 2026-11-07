"""All model prompts in one place, versioned (docs/PROMPTS.md).

Each prompt is a `Prompt` in its own module. Callers use `prompts.WRITER.text` and so on; the old
constant names (`WRITER_PROMPT`, `PICKER_PROMPT`, ...) remain as aliases. `identify()` finds the
prompt behind a system message, so `azure_chat` can tag every Langfuse generation with the prompt's
name, version and hash without changing any caller.
"""

from app.agents.prompts.base import Prompt
from app.agents.prompts.basic_mode import PROMPT as BASIC_MODE
from app.agents.prompts.judge import PROMPT as JUDGE
from app.agents.prompts.planner import PROMPT as PLANNER
from app.agents.prompts.sql_picker import PROMPT as SQL_PICKER
from app.agents.prompts.triage import PROMPT as TRIAGE
from app.agents.prompts.writer import PROMPT as WRITER

REGISTRY: dict[str, Prompt] = {p.name: p for p in (WRITER, TRIAGE, SQL_PICKER, JUDGE, PLANNER, BASIC_MODE)}
_BY_TEXT = {p.text: p for p in REGISTRY.values()}


def get(name: str) -> Prompt:
    return REGISTRY[name]


def identify(messages: list[dict]) -> Prompt | None:
    """The registered prompt used as the system message of `messages`, if any."""
    for m in messages:
        if m.get("role") == "system":
            return _BY_TEXT.get(m.get("content", ""))
    return None


__all__ = ["BASIC_MODE", "JUDGE", "PLANNER", "REGISTRY", "SQL_PICKER", "TRIAGE", "WRITER", "Prompt", "get", "identify"]
