"""
pages/2_sprint_summary.py
--------------------------
Sprint Summary page. Rendering logic moved verbatim from
dashboard_app.py's render_sprint_summary() (Phase 2 multipage
restructure — structural move only, no behavior/styling changes).
"""

import streamlit as st

from dashboard_styles import section_header
from components.icons import icon_svg
from components import charts as plotly_charts
from core.ui_helpers import (
    tr as _ui_tr,
    localized_frame as _ui_localized_frame,
    percentage_columns as _ui_percentage_columns,
)
from core.analysis import sprint_summary_df as _sprint_summary_df

ctx = st.session_state["app_ctx"]
is_ar = ctx["is_ar"]
chart_theme = ctx["chart_theme"]
ACCENT = ctx["ACCENT"]
dev = ctx["dev"]
tr = lambda en, ar: _ui_tr(en, ar, is_ar)
localized_frame = lambda frame: _ui_localized_frame(frame, is_ar)
percentage_columns = lambda *names: _ui_percentage_columns(*names, is_ar=is_ar)

st.header(tr("Sprint Summary", "ملخص السبرينت"))
st.caption(tr("One row per Azure iteration; Product Backlog is shown separately.", "صف لكل دورة Azure مع عرض Product Backlog بشكل منفصل."))
summary = _sprint_summary_df(dev)
chart_col, table_col = st.columns([1, 1.25])
with chart_col:
    section_header("Stories done vs total", "القصص المكتملة مقابل الإجمالي", icon_svg("hourglass"))
    story_chart = summary.rename(columns={
        "Iteration": "iteration", "Stories Done": "done", "User Stories": "total",
    })
    st.plotly_chart(
        plotly_charts.grouped_hbar_chart(
            story_chart, "iteration", ("done", "total"),
            {"done": ACCENT["green"], "total": ACCENT["blue"]}, chart_theme,
        ),
        width="stretch",
        config={"displaylogo": False},
    )
with table_col:
    st.dataframe(
        localized_frame(summary), width="stretch", hide_index=True,
        column_config=percentage_columns("Scope Done %", "Task Done %"),
    )
