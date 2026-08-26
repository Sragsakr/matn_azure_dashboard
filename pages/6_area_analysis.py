"""
pages/6_area_analysis.py
--------------------------
Area Analysis page. Rendering logic moved verbatim from dashboard_app.py's
render_area_analysis() (Phase 2 multipage restructure — structural move
only, no behavior/styling changes).
"""

import streamlit as st

import dashboard_theme
from dashboard_styles import section_header
from core.ui_helpers import (
    tr as _ui_tr,
    localized_frame as _ui_localized_frame,
    percentage_columns as _ui_percentage_columns,
)
from core.analysis import area_df as _area_df

ctx = st.session_state["app_ctx"]
is_ar = ctx["is_ar"]
chart_theme = ctx["chart_theme"]
ACCENT = ctx["ACCENT"]
tr = lambda en, ar: _ui_tr(en, ar, is_ar)
localized_frame = lambda frame: _ui_localized_frame(frame, is_ar)
percentage_columns = lambda *names: _ui_percentage_columns(*names, is_ar=is_ar)
dev = ctx["dev"]

st.header(tr("Area Analysis", "تحليل المجالات"))
st.caption(tr("Scope and execution across Azure Area Paths.", "توزيع النطاق والتنفيذ حسب مسارات Azure."))
areas = _area_df(dev)
if not areas.empty:
    table_col, chart_col = st.columns([1, 1.4])
    with table_col:
        st.dataframe(
            localized_frame(areas), width="stretch", hide_index=True,
            column_config=percentage_columns("Scope %", "Task %"),
        )
    with chart_col:
        section_header("Delivery items per area", "عناصر التسليم لكل مجال", "◇")
        area_load = areas.rename(columns={"Area": "area", "Total": "total"})[
            ["area", "total"]
        ]
        st.altair_chart(dashboard_theme.hbar_chart(
            area_load, "total", "area", chart_theme, color=ACCENT["gold"],
        ), width="stretch")
else:
    st.dataframe(localized_frame(areas), width="stretch", hide_index=True)
