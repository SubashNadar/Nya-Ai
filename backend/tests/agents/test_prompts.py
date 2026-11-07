"""The prompt registry (docs/PROMPTS.md): versions, contracts, and Langfuse tagging."""

import re

from app.agents import graph, llm, prompts, safety_llm, sql_agent

# A prompt's text may change only with a new version. Changing the text changes its hash, which fails
# this test until the version (and this table) are bumped together.
PINNED = {
    "writer": ("1.0.0", "eb42b42dd286"),
    "triage": ("1.0.0", "64719b83794e"),
    "sql_picker": ("1.0.0", "62929473eab8"),
    "judge": ("1.0.0", "6400374556cf"),
    "planner": ("1.0.0", "a8ba0007d991"),
    "basic_mode": ("1.0.0", "4758bbbfbce1"),
}


def test_every_prompt_is_registered_versioned_and_pinned():
    assert {name: (p.version, p.sha) for name, p in prompts.REGISTRY.items()} == PINNED
    for p in prompts.REGISTRY.values():
        assert re.fullmatch(r"\d+\.\d+\.\d+", p.version)
        assert p.pattern and p.purpose and p.model


def test_every_prompt_asks_for_json_and_forbids_advice_where_it_answers():
    for p in prompts.REGISTRY.values():
        assert "JSON" in p.text, p.name
    for p in (prompts.WRITER, prompts.PLANNER, prompts.BASIC_MODE):
        assert "advice" in p.text.lower(), p.name
    assert "Never cite a section from memory" in prompts.WRITER.text
    assert "never write SQL" in prompts.SQL_PICKER.text


def test_callers_use_the_registry_text():
    assert graph.WRITER_PROMPT is prompts.WRITER.text
    assert safety_llm.PROMPT is prompts.TRIAGE.text
    assert sql_agent.PICKER_PROMPT is prompts.SQL_PICKER.text


def test_identify_tags_generations(monkeypatch):
    msgs = [{"role": "system", "content": prompts.TRIAGE.text}, {"role": "user", "content": "q"}]
    assert prompts.identify(msgs) is prompts.TRIAGE
    assert prompts.identify([{"role": "system", "content": "something else"}]) is None
    assert prompts.TRIAGE.metadata() == {
        "prompt": "triage",
        "prompt_version": "1.0.0",
        "prompt_sha": prompts.TRIAGE.sha,
    }

    seen = {}

    class Gen:
        def update(self, **_):
            pass

    class Ctx:
        def __init__(self, name, model, **fields):
            seen.update(name=name, model=model, **fields)

        def __enter__(self):
            return Gen()

        def __exit__(self, *_):
            return False

    class Usage:
        prompt_tokens, completion_tokens = 5, 1

    class Resp:
        usage = Usage()
        choices = [type("C", (), {"message": type("M", (), {"content": '{"risk": "Low"}'})()})()]

    class Client:
        def __init__(self, **_):
            self.chat = type(
                "Chat", (), {"completions": type("Cmp", (), {"create": staticmethod(lambda **_: Resp())})()}
            )()

    import openai

    monkeypatch.setattr(llm, "azure_configured", lambda: True)
    monkeypatch.setattr(llm.costs, "generation", Ctx)
    monkeypatch.setattr(openai, "AzureOpenAI", Client)
    assert llm.azure_chat(msgs, deployment="nano") == '{"risk": "Low"}'
    assert seen["name"] == "triage" and seen["metadata"]["prompt_version"] == "1.0.0"
