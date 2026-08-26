"""
pages/7_active_now.py
-----------------------
Active Now page. Rendering logic moved verbatim from dashboard_app.py's
render_active_now() (Phase 2 multipage restructure — structural move
only, no behavior/styling changes).
"""

import datetime as dt

import pandas as pd
import streamlit as st

from components.grid import render_grid
from core.ui_helpers import tr as _ui_tr, localized_frame as _ui_localized_frame, require_app_ctx
from core.analysis import STALE_DAYS, is_open, is_active

ctx = require_app_ctx()
is_ar = ctx["is_ar"]
dev = ctx["dev"]
tr = lambda en, ar: _ui_tr(en, ar, is_ar)
localized_frame = lambda frame: _ui_localized_frame(frame, is_ar)

st.header(tr("Active & Open Work", "العمل الحالي والمفتوح"))
st.caption(tr("Open work ordered by ownership and aging risk.", "العمل المفتوح مرتب حسب المسؤولية وخطر التقادم."))
open_items = [i for i in dev if is_open(i)]


def priority(item):
    if item["assignee"] == "Unassigned":
        return "Critical"
    if is_active(item):
        return "Doing"
    if item["created"] and (dt.date.today() - item["created"]).days >= STALE_DAYS:
        return "Aging"
    if item["type"] == "User Story":
        return "Scope"
    return "High"


ordered_items = sorted(open_items, key=lambda x: priority(x))
rows = []
for i in ordered_items:
    rows.append({
        "Priority": priority(i), "ID": i["id"], "Title": i["title"], "Type": i["type"],
        "State": i["state"], "Board Column": i["board_column"],
        "Assignee": i["assignee"], "Sprint": i["sprint"],
        "Area": i["area"], "Tags": "; ".join(i["tags"]) or "Untagged",
        "Age (d)": (dt.date.today() - i["created"]).days if i["created"] else None,
        "Azure Link": i["url"],
    })
if rows:
    render_grid(
        localized_frame(pd.DataFrame(rows)), items=ordered_items,
        height=500, key="active_now_grid",
    )
else:
    st.success(tr("No open work — all done!", "لا يوجد عمل مفتوح — كل العناصر مكتملة!"))
