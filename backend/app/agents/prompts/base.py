"""The `Prompt` record every Nya-AI prompt is stored as (docs/PROMPTS.md)."""

import hashlib
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Prompt:
    name: str  # stable id, used in Langfuse as `prompt` metadata and the generation name
    version: str  # semver: major = output schema change, minor = new rule, patch = wording
    pattern: str  # prompting technique(s): persona, zero-shot classifier, tool selection, LLM-as-judge ...
    purpose: str
    model: str  # which deployment calls it: small (gpt-5.4-nano), strong (gpt-5.4)
    text: str
    sha: str = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "sha", hashlib.sha256(self.text.encode()).hexdigest()[:12])

    @property
    def tag(self) -> str:
        return f"{self.name}@{self.version}"

    def metadata(self) -> dict[str, str]:
        """What a Langfuse generation records about the prompt it ran."""
        return {"prompt": self.name, "prompt_version": self.version, "prompt_sha": self.sha}
