"""`nya-agent cost`: token use and cost per day and per trace, read back from Langfuse.

`--register-prices` also writes the `PRICE_*` settings into Langfuse's model table, so its own UI and
dashboards price generations by model name too.
"""

import re
from collections import defaultdict
from typing import Any

import httpx

from app.core.config import get_settings
from app.core.costs import prices


def _client() -> httpx.Client:
    s = get_settings()
    if not (s.LANGFUSE_PUBLIC_KEY and s.LANGFUSE_SECRET_KEY):
        raise RuntimeError("Langfuse is not configured: set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY in .env")
    return httpx.Client(
        base_url=s.LANGFUSE_HOST.rstrip("/") + "/api/public",
        auth=(s.LANGFUSE_PUBLIC_KEY, s.LANGFUSE_SECRET_KEY),
        timeout=30,
    )


def daily(days: int = 14) -> list[dict[str, Any]]:
    with _client() as c:
        r = c.get("/metrics/daily", params={"limit": days})
        r.raise_for_status()
        return r.json().get("data", [])


def per_trace(limit: int = 100) -> list[dict[str, Any]]:
    """Generations grouped by trace: tokens in/out and cost, newest first."""
    with _client() as c:
        r = c.get("/observations", params={"type": "GENERATION", "limit": limit})
        r.raise_for_status()
        rows = r.json().get("data", [])
    traces: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"input": 0, "output": 0, "cost": 0.0, "calls": 0, "models": set(), "start": ""}
    )
    for o in rows:
        t = traces[o.get("traceId") or "?"]
        u = o.get("usageDetails") or {}
        t["input"] += int(u.get("input", 0))
        t["output"] += int(u.get("output", 0))
        t["cost"] += float((o.get("costDetails") or {}).get("total", 0) or 0)
        t["calls"] += 1
        t["models"].add(o.get("model") or "?")
        t["start"] = max(t["start"], o.get("startTime") or "")
    out = [{"trace": k, **v, "models": sorted(v["models"])} for k, v in traces.items()]
    return sorted(out, key=lambda x: x["start"], reverse=True)


def register_prices() -> list[str]:
    """Create (or replace) a Langfuse model definition per deployment with the configured prices."""
    done = []
    with _client() as c:
        existing = c.get("/models", params={"limit": 100}).json().get("data", [])
        for model, (pin, pout) in prices().items():
            for m in existing:
                if m.get("modelName") == model and not m.get("isLangfuseManaged"):
                    c.delete(f"/models/{m['id']}").raise_for_status()
            body = {
                "modelName": model,
                "matchPattern": f"(?i)^{re.escape(model)}$",
                "unit": "TOKENS",
                "inputPrice": pin / 1_000_000,
                "outputPrice": pout / 1_000_000,
            }
            r = c.post("/models", json=body)
            r.raise_for_status()
            done.append(f"{model}: input ${pin}/1M, output ${pout}/1M")
    return done


def render(days: list[dict[str, Any]], traces: list[dict[str, Any]], top: int = 10) -> str:
    lines = ["Per day (Langfuse daily metrics)"]
    for d in days:
        lines.append(
            f"  {d.get('date')}  traces {d.get('countTraces', 0):>4}  "
            f"generations {d.get('countObservations', 0):>4}  cost ${float(d.get('totalCost') or 0):.4f}"
        )
        for u in d.get("usage", []):
            lines.append(
                f"      {u.get('model') or '?':<26} in {u.get('inputUsage', 0):>9} out {u.get('outputUsage', 0):>7}"
                f"  ${float(u.get('totalCost') or 0):.4f}"
            )
    lines.append(f"Per trace (latest {top})")
    for t in traces[:top]:
        lines.append(
            f"  {t['start'][:19]}  {t['trace'][:12]}  calls {t['calls']:>3}  in {t['input']:>8} out {t['output']:>6}"
            f"  ${t['cost']:.4f}  {', '.join(t['models'])}"
        )
    if all(p == (0.0, 0.0) for p in prices().values()):
        lines.append("Prices are not set (PRICE_* in .env are 0): usage is recorded, cost shows 0.")
    return "\n".join(lines)
