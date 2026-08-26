"""
pages/8_risks_and_aging.py
----------------------------
Risks & Aging page. Rendering logic moved verbatim from dashboard_app.py's
render_risks() (Phase 2 multipage restructure — structural move only, no
behavior/styling changes).
"""

import datetime as dt

import pandas as pd
import streamlit as st

from app import tr, localized_frame
from core.analysis import STALE_DAYS, PB, is_open

ctx = st.session_state["app_ctx"]
dev = ctx["dev"]

st.header(tr("Risks & Aging", "المخاطر والتقادم"))
st.caption(tr("Open work ranked by days since creation.", "العمل المفتوح مرتب حسب عدد الأيام منذ الإنشاء."))
open_items = [i for i in dev if is_open(i)]
ordered = sorted(open_items, key=lambda i: (i["assignee"] != "Unassigned",
                                            -(i["created"] and (dt.date.today() - i["created"]).days or -1),
                                            i["id"]))
rows = []
for i in ordered:
    risk = []
    if i["assignee"] == "Unassigned":
        risk.append("Unassigned")
    if i["sprint"] == PB:
        risk.append("No sprint")
    if i["created"] and (dt.date.today() - i["created"]).days >= STALE_DAYS:
        risk.append(f"Age ≥{STALE_DAYS}d")
    if i["type"] == "User Story" and i["sp"] is None:
        risk.append("No SP")
    age = (dt.date.today() - i["created"]).days if i["created"] else None
    rows.append({
        "Risk": ", ".join(risk) or "Monitor", "Age": age, "ID": i["id"], "Title": i["title"],
        "Type": i["type"], "State": i["state"], "Assignee": i["assignee"],
        "Sprint": i["sprint"], "Area": i["area"], "Tags": "; ".join(i["tags"]) or "Untagged",
        "Azure Link": i["url"],
    })
st.dataframe(localized_frame(pd.DataFrame(rows)), width="stretch", hide_index=True, height=500)
