"""Nya-AI architecture v10: users, agent system with tech callouts, MCP tools, knowledge base, observability."""
from draw_detail import icon, tile, txt, box, layer, step, arrow, item, mark_langflow
from draw import (AMBER, AMBER_T, BG, CLAY, EDGE, INK, LINE, MONO, MUTED, SAGE, SAGE_T, SANS, CARD,
                  defs, mark_azure, mark_calendar, mark_indiacode, mark_langfuse,
                  mark_langgraph, mark_llamaindex, mark_shield, simple)

W, H = 2400, 1115
JADE, JADE_L, JADE_T = "#1E6B5C", "#2C7D6C", "#D5EAE3"
VIO = "#5B4A9A"


def agent(x, y, w, h, ic, title, sub, tag=None):
    o = [f'<g transform="translate({x},{y})"><rect width="{w}" height="{h}" rx="12" fill="#FFFFFF" stroke="{JADE}" stroke-width="1.8" filter="url(#sh)"/>',
         f'<rect x="0" y="0" width="{w}" height="6" rx="3" fill="{JADE}"/>',
         f'<g transform="translate(10,14) scale(.85)">{ic}</g>',
         txt(56, 40, title, 15.5, 700, JADE), txt(12, 72, sub[0], 11.5, 400, MUTED, MONO)]
    if len(sub) > 1:
        o.append(txt(12, 90, sub[1], 11.5, 400, MUTED, MONO))
    return "".join(o) + "</g>"


def ctrl(x, y, w, h, ic, title, sub, dashed=False):
    stroke = f'stroke="{CLAY}" stroke-dasharray="6 4" stroke-width="1.5"' if dashed else f'stroke="#B9B3A6" stroke-width="1.2"'
    o = [f'<g transform="translate({x},{y})"><rect width="{w}" height="{h}" rx="12" fill="{CARD}" {stroke} filter="url(#sh)"/>',
         f'<g transform="translate(10,10) scale(.85)">{ic}</g>', txt(56, 36, title, 15, 700), txt(12, 68, sub[0], 11.5, 400, MUTED, MONO)]
    if len(sub) > 1:
        o.append(txt(12, 86, sub[1], 11.5, 400, MUTED, MONO))
    return "".join(o) + "</g>"


def chip(x, y, w, name, stage, logo=None):
    o = [f'<g transform="translate({x},{y})"><rect width="{w}" height="58" rx="10" fill="#FFFFFF" stroke="{VIO}" stroke-opacity=".45"/>']
    tx = 12
    if logo:
        o.append(f'<g transform="translate(10,8)">{logo}</g>')
        tx = 40
    o.append(txt(tx, 25, name, 14, 700, VIO))
    o.append(txt(12, 46, stage, 11.5, 400, MUTED, MONO))
    return "".join(o) + "</g>"


def pill(x, y, w, title, sub, col):
    return (f'<g transform="translate({x},{y})"><rect width="{w}" height="56" rx="10" fill="#FFFFFF" stroke="{col}" stroke-opacity=".5"/>'
            + txt(w / 2, 24, title, 13.5, 700, col, SANS, "middle") + txt(w / 2, 43, sub, 11, 400, MUTED, MONO, "middle") + "</g>")


def tcard(x, y, w, h, ic_svg, title, sub=None, mono=False, col=INK, st=None):
    o = [f'<g transform="translate({x},{y})"><rect width="{w}" height="{h}" rx="12" fill="#FFFFFF" stroke="{LINE}" filter="url(#sh)"/>',
         f'<g transform="translate({w / 2 - 20},12)">{ic_svg}</g>',
         txt(w / 2, 76, title, 14.5 if mono else 16, 700, col, MONO if mono else SANS, "middle")]
    if sub:
        o.append(txt(w / 2, 97, sub, 12, 400, MUTED, MONO, "middle"))
    if st:
        o.append(dot(w - 16, 16, st))
    return "".join(o) + "</g>"


def dot(x, y, st):
    return f'<circle cx="{x}" cy="{y}" r="6" fill="{SAGE if st == "b" else CLAY}"/>'


def tpill(x, y, w, title, col):
    return (f'<g transform="translate({x},{y})"><rect width="{w}" height="44" rx="22" fill="#FFFFFF" stroke="{col}" stroke-opacity=".55"/>'
            + txt(w / 2, 27, title, 13.5, 700, col, SANS, "middle") + "</g>")


def link(x1, y1, x2, y2):
    return f'<path d="M{x1},{y1} L{x2},{y2}" stroke="{VIO}" stroke-opacity=".5" stroke-width="1.4" stroke-dasharray="3 4" fill="none"/><circle cx="{x2}" cy="{y2}" r="3.5" fill="{VIO}"/>'


def build():
    b = [txt(W / 2, 62, "Nya-AI · Agentic Legal AI · Architecture", 36, 750, INK, SANS, "middle"),
         txt(W / 2, 98, "Grounded in official bare acts · agents work as a guarded loop · every claim cited · every step traced", 16, 400, MUTED, MONO, "middle")]
    LX, LW = 40, 330
    CX, CW = 410, 1500
    RX, RW = 1950, 410

    b.append(layer(LX, 130, LW, 510, 1, "Users", "#EAF4F0", SAGE))
    b.append(layer(CX, 130, CW, 510, 2, "Agent system · LangGraph · release R1   (technology for each step shown above it)", "#F6F2FB", VIO))
    b.append(layer(RX, 130, RW, 510, 5, "Observability · Langfuse", "#FBEFEC", "#A13D2D"))
    b.append(layer(CX, 670, 740, 375, 3, "MCP tools · read-only", "#EDF5F3", "#2B6E66"))
    b.append(layer(CX + 770, 670, 780, 375, 4, "Law data", "#F8F3E6", "#7A6224"))
    b.append(layer(1990, 670, RX + RW - 1990, 375, 6, "App data", "#EEF1F6", "#3E5A7A"))

    # ---- 1 users: one card ----
    ux, uy, uw = LX + 20, 180, LW - 40
    o = [f'<g transform="translate({ux},{uy})"><rect width="{uw}" height="440" rx="14" fill="{CARD}" stroke="{LINE}" filter="url(#sh)"/>']
    for i, g in enumerate([tile(simple("react", 0, 0, 28)), tile(icon("phone"), 0), tile(icon("globe"), 0), tile(mark_langflow(0, 0, 40), 0)]):
        o.append(f'<g transform="translate({16 + i * 50},16)">{g}</g>')
    o.append(txt(16, 92, "Citizens & advocates", 19, 700))
    o.append(txt(16, 116, "React web app · mobile or desktop", 12, 400, MUTED, MONO))
    o.append(txt(16, 136, "Langflow chat · planned", 12, 400, AMBER, MONO))
    o.append(f'<line x1="16" y1="156" x2="{uw - 16}" y2="156" stroke="{LINE}"/>')
    lines = [("Citizens", "ask · get cited answers"), ("Advocates", "briefs · consults"), ("Langflow", "visual demo chat")]
    yy = 186
    for head, rest in lines:
        o.append(txt(16, yy, head, 16, 700, SAGE))
        o.append(txt(16, yy + 24, rest, 13.5, 400, MUTED, MONO))
        yy += 70
    yy = 360
    o.append(f'<rect x="16" y="{yy + 14}" width="{uw - 32}" height="56" rx="10" fill="{SAGE_T}"/>')
    o.append(txt(28, yy + 38, "Legal information, not advice.", 13, 600, SAGE))
    o.append(txt(28, yy + 58, "Own-case questions → an advocate.", 12, 400, SAGE, MONO))
    b.append("".join(o) + "</g>")

    # ---- 2 agent system ----
    X = {"g": 430, "d": 635, "m": 840, "res": 1045, "w": 1310, "o": 1515, "a": 1720}
    Wd = {"g": 170, "d": 170, "m": 170, "res": 230, "w": 170, "o": 170, "a": 170}
    MY, MH = 300, 100
    my = MY + MH / 2
    chips = [("g", "gpt-5.4-nano", "guard prompt · PII", "azc1"), ("d", "gpt-5.4-nano", "date extract", "azc2"),
             ("m", "LangGraph", "supervisor · Send", "lg"), ("res", "LlamaIndex", "hybrid search · SQL", "li"),
             ("w", "gpt-5.4", "writer · critic judge", "azc3"), ("o", "Pydantic", "citation ↔ text", None), ("a", "SSE stream", "trace panel", None)]
    for k, name, stage, lg in chips:
        logo = None
        if lg == "lg":
            logo = f'<g transform="scale(.6)">{mark_langgraph(0, 0, 40)}</g>'
        elif lg == "li":
            logo = f'<g transform="scale(.6)">{mark_llamaindex(0, 0, 40, "llc")}</g>'
        elif lg:
            logo = f'<g transform="scale(.6)">{mark_azure(0, 0, 40, lg)}</g>'
        b.append(chip(X[k], 172, Wd[k], name, stage, logo))
        top = 236 if k in ("res", "w") else MY
        b.append(link(X[k] + Wd[k] / 2, 230, X[k] + Wd[k] / 2, top))

    b.append(ctrl(X["g"], MY, 170, MH, tile(mark_shield(0, 0, 40), 0), "Input guard", ["injection · PII mask", "unsafe intent"]))
    b.append(ctrl(X["d"], MY, 170, MH, tile(mark_calendar(0, 0, 40), 0), "Law in force", ["incident date →", "IPC or BNS"]))
    b.append(agent(X["m"], MY, 170, MH, icon("split"), "Manager", ["plans the research", "assigns the agents"]))
    # research group
    gx0, gw0 = X["res"], Wd["res"]
    b.append(f'<rect x="{gx0}" y="236" width="{gw0}" height="370" rx="14" fill="{JADE_T}" fill-opacity=".45" stroke="{JADE}" stroke-opacity=".45" stroke-dasharray="6 4"/>')
    b.append(txt(gx0 + gw0 / 2, 260, "Research agents · parallel", 12.5, 700, JADE, MONO, "middle"))
    res = [("Statute", ["bare acts", "meaning + keyword"], "gavel"), ("Case law", ["SC judgments", "cites ¶"], "brief"), ("SQL", ["fixed queries", "law tables only"], "table")]
    for n_, (t_, s_, ic) in enumerate(res):
        b.append(agent(gx0 + 12, 274 + n_ * 110, gw0 - 24, 100, icon(ic), t_, s_))
    b.append(agent(X["w"], 236, 170, MH, icon("pen"), "Writer", ["drafts only from", "retrieved text"]))
    b.append(agent(X["w"], 420, 170, MH, icon("check"), "Critic", ["claim ↔ section", "faithfulness"]))
    b.append(ctrl(X["o"], MY, 170, MH, tile(mark_shield(0, 0, 40), 0), "Output guard", ["citations match", "confidence ≥ 0.5"]))
    b.append(ctrl(X["a"], MY, 170, MH, tile(icon("brief"), 0), "Cited answer", ["¶ paragraphs", "act · section"]))
    b.append(agent(X["m"], 520, 170, MH, icon("brief"), "Escalation", ["drafts a case brief", "no database write"]))
    b.append(ctrl(X["d"], 520, 170, MH, tile(icon("hand"), 0), "Advocate", ["user confirms, then", "booking saves brief"]))
    b.append(chip(X["g"], 541, 180, "interrupt()", "graph waits", None))
    b.append(link(X["g"] + 180, 570, X["d"] - 4, 570))

    # connections: one clear lane, one arrow per hand-off
    b.append(arrow([(LX + LW, my), (X["g"] - 4, my)], main=True)); b.append(step(1, LX + LW + 34, my - 22))
    b.append(arrow([(X["g"] - 4, my + 34), (LX + LW + 4, my + 34)], dashed=True, label="answer", lx=LX + LW + 35, ly=my + 62))
    b.append(arrow([(X["g"] + 170, my), (X["d"] - 4, my)], main=True)); b.append(step(2, X["g"] + 187, my - 24))
    b.append(arrow([(X["d"] + 170, my), (X["m"] - 4, my)], main=True))
    b.append(arrow([(X["m"] + 170, my), (gx0 - 4, my)], main=True)); b.append(step(3, X["m"] + 187, my - 24))
    b.append(arrow([(gx0 + gw0, 286), (X["w"] - 4, 286)], main=True))
    b.append(arrow([(X["w"] + 120, 336), (X["w"] + 120, 416)], main=True))
    b.append(txt(X["w"] + 126, 382, "draft", 11, 600, JADE, MONO))
    b.append(arrow([(X["w"] + 45, 420), (X["w"] + 45, 340)], dashed=True))
    b.append(txt(X["w"] + 6, 382, "revise", 11, 600, CLAY, MONO))
    b.append(step(6, X["w"] - 16, 450))
    b.append(arrow([(X["w"] + 170, 470), (X["w"] + 188, 470), (X["w"] + 188, my), (X["o"] - 4, my)], main=True))
    b.append(arrow([(X["o"] + 170, my), (X["a"] - 4, my)], main=True)); b.append(step(7, X["o"] + 187, my - 24))
    b.append(arrow([(X["m"] + 85, MY + MH), (X["m"] + 85, 516)], dashed=True))
    b.append(txt(X["m"] + 93, 470, "own case", 11.5, 600, CLAY, MONO))
    b.append(arrow([(X["m"], 570), (X["d"] + 174, 570)], main=True))
    b.append(arrow([(CX + CW, 300), (RX - 4, 300)], dashed=True)); b.append(step(8, CX + CW + 20, 278))
    sx, sw = gx0, gw0

    # ---- 5 observability ----
    obs = [(tile(mark_langfuse(0, 0, 40), 0), "Traces", "per agent step", "BUILT"),
           (tile(icon("chart", "#FBEFEC", "#A13D2D"), 0), "Quality scores", "faithfulness", "R4"),
           (tile(icon("check", "#FBEFEC", "#A13D2D"), 0), "Ragas runs", "golden queries", "R4"),
           (tile(icon("prompt", "#FBEFEC", "#A13D2D"), 0), "Prompt versions", "per agent", "R1"),
           (tile(icon("fuse", "#FBEFEC", "#A13D2D"), 0), "Retry & fallback", "rule engine", "BUILT"),
           (tile(icon("bell", "#FBEFEC", "#A13D2D"), 0), "Alerts", "tool errors", "R4")]
    for i, (g, t, s_, tag) in enumerate(obs):
        c, r = i % 2, i // 2
        cw = (RW - 52) / 2
        b.append(tcard(RX + 20 + c * (cw + 12), 178 + r * 150, cw, 136, g, t, s_,
                       st="b" if tag == "BUILT" else "p"))

    # ---- 3 retrieval: MCP tools ----
    tools = [("law_search()", "search"), ("get_section()", "file"), ("search_judgments()", "gavel"),
             ("map_ipc_to_bns()", "fuse"), ("acts_in_force()", "table"), ("sql_lookup()", "dataset")]
    for i, (t_, ic_) in enumerate(tools):
        c, r = i % 3, i // 3
        b.append(tcard(CX + 22 + c * 240, 720 + r * 110, 216, 100, icon(ic_), t_, mono=True, col="#2B6E66", st="p"))
    b.append(txt(CX + 24, 958, "inside law_search()", 13, 600, MUTED, MONO))
    rchain = ["Exact section", "Dense + BM25", "Rank fusion", "In-force filter"]
    for i, a_ in enumerate(rchain):
        x = CX + 22 + i * 178
        b.append(tpill(x, 970, 150, a_, "#2B6E66"))
        if i:
            b.append(arrow([(x - 26, 992), (x - 3, 992)], main=True))

    # ---- 4 law data + ingestion ----
    kx, kwid = CX + 790, 740
    kw = (kwid - 24) / 3
    kb = [("Bare-act library", "BNS · BNSS · BSA · IPC", tile(mark_indiacode(0, 0, 40), 0), "b"),
          ("Vector index", "pgvector + BM25", tile(simple("postgresql", 0, 0, 28)), "p"),
          ("Law SQL tables", "IPC → BNS map", tile(icon("table"), 0), "p")]
    for i, (t_, sub, ic_, st) in enumerate(kb):
        b.append(tcard(kx + i * (kw + 12), 720, kw, 112, ic_, t_, sub, st=st))
        cxm = kx + i * (kw + 12) + kw / 2
        b.append(arrow([(cxm, 876), (cxm, 836)], dashed=True))
    b.append(f'<rect x="{kx - 8}" y="880" width="{kwid + 16}" height="140" rx="14" fill="#FFFFFF" fill-opacity=".55" stroke="#7A6224" stroke-opacity=".3" stroke-dasharray="6 5"/>')
    b.append(f'<g transform="translate({kx + 6},892) scale(.8)">{tile(mark_llamaindex(0, 0, 40, "ll9"), 0)}</g>')
    b.append(txt(kx + 48, 916, "Ingestion · offline", 15, 700, "#7A6224"))
    ichain = ["India Code PDF", "Section parser", "Embed", "pgvector + BM25", "SQL tables"]
    pw, pg = 134, 17
    for i, a_ in enumerate(ichain):
        x = kx + i * (pw + pg)
        b.append(tpill(x, 958, pw, a_, "#7A6224"))
        if i:
            b.append(arrow([(x - pg + 2, 980), (x - 3, 980)], main=True))

    # ---- 6 app data: direct, never via MCP ----
    ax, aw = 2010, RX + RW - 2030
    b.append(tcard(ax, 720, aw, 112, tile(simple("sqlite", 0, 0, 28)), "Chat memory", "via checkpointer", st="p"))
    b.append(tpill(ax, 856, aw, "FastAPI services", "#3E5A7A"))
    b.append(arrow([(ax + aw / 2, 900), (ax + aw / 2, 918)], main=True))
    b.append(tcard(ax, 922, aw, 112, tile(icon("db"), 0), "User store", "no agent access", st="b"))
    b.append(chip(1690, 560, 210, "Checkpointer", "state after each step", None))
    b.append(arrow([(1795, 618), (1795, 650), (1972, 650), (1972, 776), (ax - 4, 776)], main=True))
    b.append(arrow([(LX, 560), (22, 560), (22, 1090), (2380, 1090), (2380, 878), (ax + aw + 4, 878)], dashed=True,
                   label="login · bookings", lx=1200, ly=1090))
    b.append(arrow([(925, 620), (925, 661), (1984, 661), (1984, 878), (ax - 4, 878)], dashed=True,
                   label="brief · after user confirms", lx=1330, ly=661))

    # wiring
    b.append(arrow([(sx + 60, 606), (sx + 60, 714)], main=True)); b.append(step(4, sx + 84, 640))
    b.append(arrow([(CX + 740, 760), (kx - 4, 760)], main=True))
    b.append(arrow([(kx - 4, 810), (CX + 744, 810)], dashed=True)); b.append(step(5, CX + 755, 785))

    # ---- external (future) + legend ----
    b.append(f'<rect x="{LX}" y="670" width="{LW}" height="165" rx="18" fill="#FDF4EA" stroke="{CLAY}" stroke-dasharray="7 5" stroke-width="1.4"/>')
    b.append(txt(LX + 22, 702, "External · future scope", 17, 700, AMBER))
    b.append(box(LX + 20, 712, LW - 40, 112, "Razorpay", ["paid consults"],
                 [tile(simple("razorpay", 0, 0, 28, "#0C2451"))], "FUTURE", planned=True))
    b.append(f'<rect x="{LX}" y="850" width="{LW}" height="195" rx="18" fill="#FFFFFF" stroke="{LINE}"/>')
    b.append(txt(LX + 22, 882, "Legend", 17, 700))
    b.append(f'<rect x="{LX + 22}" y="904" width="30" height="22" rx="5" fill="#FFFFFF" stroke="{JADE}" stroke-width="1.8"/>' + txt(LX + 64, 921, "agent", 15))
    b.append(f'<rect x="{LX + 172}" y="904" width="30" height="22" rx="5" fill="#FFFFFF" stroke="#B9B3A6"/>' + txt(LX + 214, 921, "check step", 15))
    b.append(dot(LX + 37, 960, "b") + txt(LX + 64, 965, "built", 15))
    b.append(dot(LX + 187, 960, "p") + txt(LX + 214, 965, "planned", 15))
    b.append(f'<path d="M{LX + 22},1004 h30" stroke="{SAGE}" stroke-width="2.6"/>' + txt(LX + 64, 1009, "flow", 15))
    b.append(f'<path d="M{LX + 172},1004 h30" stroke="{EDGE}" stroke-width="1.6" stroke-dasharray="6 5"/>' + txt(LX + 214, 1009, "side path", 15))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
            f'aria-label="Nya-AI architecture"><rect width="{W}" height="{H}" fill="{BG}"/>{defs()}' + "\n".join(b) + "</svg>")


open("architecture-detailed.svg", "w").write(build())
print("ok")
