"""
pages/12_raw_data.py
----------------------
Raw Data page. Rendering logic moved verbatim from dashboard_app.py's
render_raw_data() (Phase 2 multipage restructure — structural move only,
no behavior/styling changes).
"""

import pandas as pd
import streamlit as st

from components.grid import render_grid
from core.ui_helpers import tr as _ui_tr, localized_frame as _ui_localized_frame, require_app_ctx

ctx = require_app_ctx()
is_ar = ctx["is_ar"]
items = ctx["items"]
data_mode = ctx["data_mode"]
tr = lambda en, ar: _ui_tr(en, ar, is_ar)
localized_frame = lambda frame: _ui_localized_frame(frame, is_ar)

st.header(tr("Raw Data — all Azure work items", "البيانات الخام — جميع عناصر Azure"))
st.caption(tr(f"{len(items):,} items from the current {data_mode} source.", f"عدد {len(items):,} عنصر من مصدر البيانات الحالي."))
all_items = items  # already loaded by app.py
df = pd.DataFrame([{
    "Work Item ID": i["id"], "Title": i["title"], "Work Item Type": i["type"],
    "State": i["state"], "State Category": i["state_category"],
    "Board Column": i["board_column"], "Board Column Done": i["board_column_done"],
    "Board Lane": i["board_lane"], "Assigned To": i["assignee"],
    "Iteration Path": i["sprint"], "Area Path": i["area"],
    "Story Points": i["sp"], "Priority": i["priority"],
    "Created Date": i["created"], "Changed Date": i["changed"],
    "Tags": "; ".join(i["tags"]) or "Untagged", "Parent ID": i["parent"], "Azure Link": i["url"],
} for i in all_items])
if not df.empty:
    render_grid(localized_frame(df), items=all_items, height=520, key="raw_data_grid")
else:
    st.info(tr(
        "No raw data loaded. Sync Azure DevOps or provide a workbook.",
        "لا توجد بيانات خام. قم بمزامنة Azure DevOps أو أضف ملف البيانات.",
    ))
