"""Cost tracking: price maths, what a generation records, and the cost report, offline."""

from app.core import costs
from app.evals import cost as report


class _Gen:
    def __init__(self):
        self.fields = {}

    def update(self, **fields):
        self.fields.update(fields)


def test_cost_uses_prices_per_million_tokens(monkeypatch):
    monkeypatch.setattr(costs, "prices", lambda: {"gpt-5.4": (2.0, 8.0)})
    got = costs.cost("gpt-5.4", 1_000, 500)
    assert got == {"input": 0.002, "output": 0.004, "total": 0.006}
    assert costs.cost("unknown-model", 1_000, 500)["total"] == 0


def test_record_sends_usage_and_cost(monkeypatch):
    monkeypatch.setattr(costs, "prices", lambda: {"gpt-5.4-nano": (1.0, 1.0)})
    gen = _Gen()
    costs.record(gen, "gpt-5.4-nano", 13, 4, output="ok")
    assert gen.fields["usage_details"] == {"input": 13, "output": 4, "total": 17}
    assert round(gen.fields["cost_details"]["total"], 9) == 0.000017
    assert gen.fields["output"] == "ok"


def test_embedding_usage_is_skipped_without_langfuse(monkeypatch):
    monkeypatch.setattr(costs, "langfuse", lambda: None)
    assert costs.record_embeddings("embed test", ["theft"]) == 0


def test_render_lists_days_and_traces(monkeypatch):
    monkeypatch.setattr(report, "prices", lambda: {"gpt-5.4": (0.0, 0.0)})
    days = [
        {
            "date": "2026-11-07",
            "countTraces": 2,
            "countObservations": 3,
            "totalCost": 0.5,
            "usage": [{"model": "gpt-5.4", "inputUsage": 100, "outputUsage": 20, "totalCost": 0.5}],
        }
    ]
    traces = [
        {
            "trace": "abc",
            "start": "2026-11-07T03:52:01",
            "calls": 1,
            "input": 13,
            "output": 4,
            "cost": 0.0,
            "models": ["gpt-5.4-nano"],
        }
    ]
    text = report.render(days, traces)
    assert "2026-11-07" in text and "gpt-5.4" in text and "abc" in text
    assert "Prices are not set" in text
