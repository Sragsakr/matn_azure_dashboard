"""
pages/9_data_quality.py
-------------------------
Data Quality page. Rendering logic moved verbatim from dashboard_app.py's
render_data_quality() (Phase 2 multipage restructure — structural move
only, no behavior/styling changes).
"""

import pandas as pd
import streamlit as st

from core.ui_helpers import tr as _ui_tr, localized_frame as _ui_localized_frame, require_app_ctx
from core.analysis import PB

ctx = require_app_ctx()
is_ar = ctx["is_ar"]
items = ctx["items"]
dev = ctx["dev"]
all_m = ctx["all_m"]
tr = lambda en, ar: _ui_tr(en, ar, is_ar)
localized_frame = lambda frame: _ui_localized_frame(frame, is_ar)

st.header(tr("Data Quality & Trust", "جودة وموثوقية البيانات"))
rows = [
    ("All Azure work items imported", len(items), "Exact"),
    ("Delivery scope (Epic+Feature+Story+Task+Bug)", len(dev), "Exact"),
    ("Test artifacts retained in Raw Data", len(items) - len(dev), "Excluded from delivery scope"),
    ("Items in real sprint paths", sum(1 for i in dev if i["sprint"] != PB), "Exact"),
    ("Product Backlog (no sprint)", sum(1 for i in dev if i["sprint"] == PB), "Exact"),
    ("Items without assignee", all_m["unassigned"], "Exact"),
    ("Items without tags", sum(1 for i in dev if not i["tags"]), "Exact"),
    ("User Stories without Story Points", sum(1 for i in dev if i["type"] == "User Story" and i["sp"] is None), "Exact"),
    ("Items with Parent ID", sum(1 for i in dev if i["parent"] is not None), "Enables hierarchy roll-up"),
]
st.dataframe(localized_frame(pd.DataFrame(rows, columns=["Check", "Count", "Interpretation"])),
             width="stretch", hide_index=True)
