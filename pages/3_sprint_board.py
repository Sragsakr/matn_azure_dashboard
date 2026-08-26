"""
pages/3_sprint_board.py
-------------------------
Sprint Board page. Rendering logic moved verbatim from dashboard_app.py's
render_sprint_board() (Phase 2 multipage restructure — structural move
only, no behavior/styling changes) for the Table view, plus a new Kanban
view added in Phase 5.

Dependency decision (Phase 5): the original brief suggested
`streamlit-elements` for the Kanban board. Investigated before adding it —
its last PyPI release is 0.1.0 from 2022-04-25 (over 4 years stale), pinned
only to `streamlit>=1.4.0` with no upper bound. A live-boot test against
this repo's actual Streamlit version (1.6x, per requirements.txt's
`streamlit>=1.30` floor) showed it *does* still import and render inside an
iframe custom component with no console/server errors — but inspecting the
installed package (streamlit_elements/modules/*.py: mui, nivo, html, media,
editors, dashboard, events) confirms it ships no Kanban/board primitive at
all, only generic MUI wrappers (mui.Box, mui.Card, ...). Building the board
with mui.Box/mui.Card would take the same hand-rolled column+card layout
work as plain Streamlit, but adds an iframe-hosted, unmaintained dependency
for zero functional gain. So this page uses the plain-Streamlit fallback
(components/kanban.py: st.columns + inline-styled containers) instead —
no new dependency, renders natively (no component-hydration risk), and is
inherently read-only since nothing drag-drop-capable is wired in.
"""

import datetime as dt

import pandas as pd
import streamlit as st

from components.grid import render_grid
from components.kanban import render_kanban
from core.ui_helpers import tr as _ui_tr, localized_frame as _ui_localized_frame

ctx = st.session_state["app_ctx"]
is_ar = ctx["is_ar"]
dev = ctx["dev"]
accents = ctx["ACCENT"]
tr = lambda en, ar: _ui_tr(en, ar, is_ar)
localized_frame = lambda frame: _ui_localized_frame(frame, is_ar)

st.header(tr("Sprint Board", "لوحة السبرينت"))
st.caption(tr("Delivery work grouped by iteration and assignee, with Azure links.", "عناصر التسليم مجمعة حسب الدورة والمسؤول مع روابط Azure."))

# Default to Kanban: it's the page's namesake view (mirrors the Azure
# DevOps board layout users already know) and surfaces workflow-stage
# distribution (board_column) at a glance, which the flat Table view
# cannot show without manual sorting/grouping. Table remains one click
# away for anyone who prefers the old sortable/filterable/CSV-exportable
# grid (e.g. bulk scanning many columns at once).
view = st.radio(
    tr("View", "العرض"),
    options=["kanban", "table"],
    format_func=lambda v: tr("Kanban", "لوحة كانبان") if v == "kanban" else tr("Table", "جدول"),
    horizontal=True,
    key="sprint_board_view",
)

if view == "kanban":
    render_kanban(dev, is_ar=is_ar, accents=accents, key="sprint_board_kanban")
else:
    df = pd.DataFrame([{
        "Iteration": i["sprint"], "ID": i["id"], "Title": i["title"], "Type": i["type"],
        "State": i["state"], "State Category": i["state_category"],
        "Board Column": i["board_column"], "Board Lane": i["board_lane"],
        "Assignee": i["assignee"], "Area": i["area"],
        "Tags": "; ".join(i["tags"]) or "Untagged", "SP": i["sp"],
        "Priority": i["priority"],
        "Created": i["created"], "Changed": i["changed"],
        "Age (d)": (dt.date.today() - i["created"]).days if i["created"] else None,
        "Parent ID": i["parent"], "Azure Link": i["url"],
    } for i in dev])
    render_grid(localized_frame(df), items=dev, height=500, key="sprint_board_grid")
