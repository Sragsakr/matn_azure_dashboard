"""
pages/4_tag_analysis.py
-------------------------
Tag Analysis page. Rendering logic moved verbatim from dashboard_app.py's
render_tag_analysis() (Phase 2 multipage restructure — structural move
only, no behavior/styling changes).
"""

from collections import defaultdict

import pandas as pd
import streamlit as st

import dashboard_theme
from dashboard_styles import section_header
from app import tr, localized_frame, percentage_columns
from core.analysis import STALE_DAYS, item_metrics, scope_metrics, percent

ctx = st.session_state["app_ctx"]
chart_theme = ctx["chart_theme"]
ACCENT = ctx["ACCENT"]
dev = ctx["dev"]

st.header(tr("Tag Analysis", "تحليل الوسوم"))
st.caption(tr("Multi-tag items are counted once per tag; untagged work is explicit.", "يتم احتساب العنصر تحت كل وسم مع إظهار العناصر غير المصنفة."))
tag_map = defaultdict(list)
for i in dev:
    for t in (i["tags"] or ["Untagged"]):
        tag_map[t].append(i)
rows = []
for tag, members in sorted(tag_map.items(), key=lambda x: -len(x[1])):
    sc = scope_metrics(members)
    im = item_metrics(members)
    rows.append({
        "Tag": tag, "Items": len(members),
        "Stories": sc["stories"], "Stories Done": sc["stories_done"],
        "Scope %": percent(sc["scope_pct"]),
        "Tasks": sc["tasks"], "Tasks Done": sc["tasks_done"],
        "Task %": percent(sc["task_pct"]),
        "Active": im["active"], "Unassigned": im["unassigned"],
        f"Open ≥{STALE_DAYS}d": im["stale"],
        "Areas": ", ".join(sorted({i["area"] for i in members})),
    })
tag_frame = pd.DataFrame(rows)
chart_col, table_col = st.columns([1, 1.3])
with chart_col:
    section_header("Items per tag", "العناصر لكل وسم", "#")
    if not tag_frame.empty:
        tag_counts = tag_frame.rename(columns={"Tag": "tag", "Items": "items"})[
            ["tag", "items"]
        ]
        st.altair_chart(dashboard_theme.hbar_chart(
            tag_counts, "items", "tag", chart_theme, color=ACCENT["teal"],
        ), width="stretch")
with table_col:
    st.dataframe(
        localized_frame(tag_frame), width="stretch", hide_index=True,
        column_config=percentage_columns("Scope %", "Task %"),
    )
