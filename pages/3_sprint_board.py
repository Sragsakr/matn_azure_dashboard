"""
pages/3_sprint_board.py
-------------------------
Sprint Board page. Rendering logic moved verbatim from dashboard_app.py's
render_sprint_board() (Phase 2 multipage restructure — structural move
only, no behavior/styling changes).
"""

import datetime as dt

import pandas as pd
import streamlit as st

from components.grid import render_grid
from core.ui_helpers import tr as _ui_tr, localized_frame as _ui_localized_frame

ctx = st.session_state["app_ctx"]
is_ar = ctx["is_ar"]
dev = ctx["dev"]
tr = lambda en, ar: _ui_tr(en, ar, is_ar)
localized_frame = lambda frame: _ui_localized_frame(frame, is_ar)

st.header(tr("Sprint Board", "لوحة السبرينت"))
st.caption(tr("Delivery work grouped by iteration and assignee, with Azure links.", "عناصر التسليم مجمعة حسب الدورة والمسؤول مع روابط Azure."))
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
