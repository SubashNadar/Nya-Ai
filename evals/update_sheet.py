"""Write the latest `nya-agent slo` results into the "SLO matrix" sheet of slo-test-sheet.xlsx.

Run from backend/ after a run:  uv run python ../evals/update_sheet.py
It also keeps the targets on the "SLO definitions" sheet equal to the course matrix.
"""

import json
import sys
from datetime import date
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "backend"))
from app.evals.slo import METRICS, fmt, met  # noqa: E402  # pylint: disable=wrong-import-position

COURSE = {  # the course matrix wording, unchanged
    1: "Correctness of generated answers",
    2: "Usefulness of the retrieved chunks and generated output to the query",
    3: "Quality of retrieved documents — proportion that are relevant",
    4: "End-to-end request latency from query submission to response delivery",
    5: "Overall correctness of the system's answers against ground truth",
    6: "Completeness — proportion of relevant documents successfully retrieved",
    7: "LLM-as-judge confidence score evaluating overall output quality",
    8: "Measures whether the system produced a correct outcome",
    9: "Measures whether parameterized query results match ground truth on the golden set",
    10: "The system proves its answer is grounded in retrieved evidence rather than hallucination",
    11: "Measures how often a Critical ticket is not classified as Critical (false negative)",
    12: "100% recall is the only acceptable target — missing a single mandatory escalation is a system failure",
    13: "Any cross-customer data access is a data breach with regulatory and legal consequences",
    14: "Measured against defined attack types",
    15: "Queries are routed to the correct service or agent",
    16: "Correctly identifies and classifies risk levels",
}
BLOCKED = "Not run: needs the ingested library, the R1 agent graph and the Azure key (run on the owner's PC)."
DEF_TARGETS = {3: 0.80, 4: 0.75, 5: 0.70, 6: 0.75, 11: 2}  # rows on "SLO definitions"

NAVY, CREAM, YELLOW = "FF0A1424", "FFF6EEDF", "FFFFF2B3"
GREEN, RED, GREY = "FFD9EAD3", "FFF4CCCC", "FFEEEEEE"
thin = Side(style="thin", color="FFBBBBBB")
BOX = Border(left=thin, right=thin, top=thin, bottom=thin)


def evidence(no: int, details: dict) -> str:
    t = details["triage"]
    split = {
        11: ("critical_miss_rate", "critical_cases"),
        12: ("escalation_recall", "escalation_cases"),
        14: ("guardrail_effectiveness", "attack_cases"),
        15: ("routing_accuracy", "cases"),
        16: ("risk_accuracy", "cases"),
    }
    if no in split:
        key, n = split[no]
        parts = [f"{s} {t[s][key]:.0%} (n={t[s][n]})" for s in ("golden", "holdout", "stress") if t[s][key] is not None]
        return "Rules only. " + "; ".join(parts) + ". Achieved = held-out + stress (unseen)."
    if no == 9:
        s = details["sql"]
        if s.get("error"):
            return s["error"]
        return (
            f"{s['cases']} template calls; failing {', '.join(f['id'] for f in s['failures']) or 'none'} "
            "(data gaps: new offences, offence_class empty, CrPC/IEA not registered)."
        )
    if no == 13:
        bad = [p["name"] for p in details["rbac"] if p["violated"]]
        return f"{len(details['rbac'])} cross-account API probes; " + (
            "violations: " + ", ".join(bad) if bad else "all denied"
        )
    return BLOCKED


def main() -> None:
    results = json.loads((HERE / "slo-results.json").read_text(encoding="utf-8"))
    values, details = results["values"], results["details"]
    wb = load_workbook(HERE / "slo-test-sheet.xlsx")
    if "SLO matrix" in wb.sheetnames:
        del wb["SLO matrix"]
    ws = wb.create_sheet("SLO matrix", 0)
    wb.active = 0

    ws["A1"] = "Nya-AI against the course SLO matrix"
    ws["A1"].font = Font(name="Arial", size=14, bold=True)
    ws["A2"] = f"Run {date.today():%d %b %Y} with `nya-agent slo`. Green met, red not met, grey not run yet."
    ws["A2"].font = Font(name="Arial", size=10, italic=True)
    head = ["S.No", "SLO metric", "Category", "Description", "Expected Target", "Achieved Value", "Status",
            "How Nya-AI measures it", "Evidence"]  # fmt: skip
    for col, h in enumerate(head, 1):
        cell = ws.cell(4, col, h)
        cell.font = Font(name="Arial", bold=True, color=CREAM)
        cell.fill = PatternFill("solid", fgColor=NAVY)
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = BOX
    for i, m in enumerate(METRICS):
        r = 5 + i
        v = values.get(m.key)
        ok = met(m, v)
        status = {True: "Met", False: "Not met", None: "Not run"}[ok]
        row = [m.no, m.name, m.category, COURSE[m.no], m.target, fmt(m, v), status, m.how, evidence(m.no, details)]
        for col, val in enumerate(row, 1):
            cell = ws.cell(r, col, val)
            cell.font = Font(name="Arial", size=10, bold=col in (2, 6))
            cell.alignment = Alignment(
                wrap_text=True, vertical="top", horizontal="center" if col in (1, 5, 6, 7) else "left"
            )
            cell.border = BOX
        ws.cell(r, 7).fill = PatternFill("solid", fgColor={True: GREEN, False: RED, None: GREY}[ok])
        # numeric copies for the chart (hidden columns K, L)
        if v is not None and m.key not in ("latency_p95_s", "rbac_violations", "critical_miss_rate"):
            ws.cell(r, 11, m.name)
            ws.cell(r, 12, round(v, 3))
            ws.cell(r, 13, m.value)
    for col, w in zip("ABCDEFGHIJKLM", [6, 30, 14, 40, 13, 15, 10, 52, 60, 2, 30, 10, 10], strict=True):
        ws.column_dimensions[col].width = w
    ws.freeze_panes = "C5"
    ws.row_dimensions[4].height = 30
    for r in range(5, 21):
        ws.row_dimensions[r].height = 66  # fixed, so the chart anchor below lands where it says

    rows = [r for r in range(5, 21) if ws.cell(r, 12).value is not None]
    if rows:
        out = 23
        ws.cell(out, 11, "Measured SLO")
        ws.cell(out, 12, "Achieved")
        ws.cell(out, 13, "Target")
        for k, r in enumerate(rows, 1):
            for col in (11, 12, 13):
                ws.cell(out + k, col, ws.cell(r, col).value)
                ws.cell(r, col).value = None
        chart = BarChart()
        chart.type = "bar"
        chart.title = "Measured SLOs: achieved vs target"
        chart.y_axis.number_format = "0%"
        chart.y_axis.scaling.min, chart.y_axis.scaling.max = 0, 1
        data = Reference(ws, min_col=12, max_col=13, min_row=out, max_row=out + len(rows))
        chart.add_data(data, titles_from_data=True)
        chart.set_categories(Reference(ws, min_col=11, min_row=out + 1, max_row=out + len(rows)))
        chart.height, chart.width = 9, 22
        ws.add_chart(chart, "B23")

    defs = wb["SLO definitions"]
    for row, target in DEF_TARGETS.items():
        defs.cell(row, 5, target)
    defs["A14"] = (
        "Faithfulness, answer relevancy, context precision, context recall and latency targets follow the course "
        "SLO matrix (3 Nov 2026); see the 'SLO matrix' sheet for all 16. Confidence, citation, escalation, "
        "guardrail and cost rows are Nya-AI's own extra checks."
    )
    wb.save(HERE / "slo-test-sheet.xlsx")
    print("updated", HERE / "slo-test-sheet.xlsx")


if __name__ == "__main__":
    main()
