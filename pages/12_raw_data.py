"""
pages/12_raw_data.py
----------------------
Raw Data page. Rendering logic moved verbatim from dashboard_app.py's
render_raw_data() (Phase 2 multipage restructure — structural move only,
no behavior/styling changes).
"""

import pandas as pd
import streamlit as st

from app import tr, localized_frame

ctx = st.session_state["app_ctx"]
items = ctx["items"]
data_mode = ctx["data_mode"]

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
    st.dataframe(localized_frame(df), width="stretch", hide_index=True, height=520)
else:
    st.info(tr(
        "No raw data loaded. Sync Azure DevOps or provide a workbook.",
        "لا توجد بيانات خام. قم بمزامنة Azure DevOps أو أضف ملف البيانات.",
    ))
