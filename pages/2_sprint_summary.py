"""
pages/2_sprint_summary.py
--------------------------
Sprint Summary page. Rendering logic moved verbatim from
dashboard_app.py's render_sprint_summary() (Phase 2 multipage
restructure — structural move only, no behavior/styling changes).
"""

import streamlit as st

import dashboard_theme
from dashboard_styles import section_header
from app import tr, localized_frame, percentage_columns
from core.analysis import sprint_summary_df as _sprint_summary_df

ctx = st.session_state["app_ctx"]
chart_theme = ctx["chart_theme"]
ACCENT = ctx["ACCENT"]
dev = ctx["dev"]

st.header(tr("Sprint Summary", "ملخص السبرينت"))
st.caption(tr("One row per Azure iteration; Product Backlog is shown separately.", "صف لكل دورة Azure مع عرض Product Backlog بشكل منفصل."))
summary = _sprint_summary_df(dev)
chart_col, table_col = st.columns([1, 1.25])
with chart_col:
    section_header("Stories done vs total", "القصص المكتملة مقابل الإجمالي", "◷")
    story_chart = summary.rename(columns={
        "Iteration": "iteration", "Stories Done": "done", "User Stories": "total",
    })
    st.altair_chart(dashboard_theme.grouped_hbar_chart(
        story_chart, "iteration", ("done", "total"),
        {"done": ACCENT["green"], "total": ACCENT["blue"]}, chart_theme,
    ), width="stretch")
with table_col:
    st.dataframe(
        localized_frame(summary), width="stretch", hide_index=True,
        column_config=percentage_columns("Scope Done %", "Task Done %"),
    )
