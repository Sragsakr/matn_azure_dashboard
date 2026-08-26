"""
pages/5_team_analysis.py
--------------------------
Team Analysis page. Rendering logic moved verbatim from dashboard_app.py's
render_team_analysis() (Phase 2 multipage restructure — structural move
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
from core.analysis import team_df as _team_df

ctx = st.session_state["app_ctx"]
is_ar = ctx["is_ar"]
chart_theme = ctx["chart_theme"]
ACCENT = ctx["ACCENT"]
tr = lambda en, ar: _ui_tr(en, ar, is_ar)
localized_frame = lambda frame: _ui_localized_frame(frame, is_ar)
percentage_columns = lambda *names: _ui_percentage_columns(*names, is_ar=is_ar)
dev = ctx["dev"]

st.header(tr("Team Delivery", "أداء الفريق"))
st.caption(tr("Team contribution is measured through completed Tasks.", "تُقاس مساهمة أعضاء الفريق من خلال المهام المكتملة."))
team = _team_df(dev)
if not team.empty:
    table_col, chart_col = st.columns([1, 1.4])
    with table_col:
        st.dataframe(
            localized_frame(team), width="stretch", hide_index=True,
            column_config=percentage_columns("Task Completion %"),
        )
    with chart_col:
        section_header("Tasks per member", "المهام لكل عضو", "◎")
        member_load = team.rename(columns={"Assignee": "member", "Tasks": "tasks"})[
            ["member", "tasks"]
        ]
        st.altair_chart(dashboard_theme.hbar_chart(
            member_load, "tasks", "member", chart_theme,
            color=ACCENT["purple"],
        ), width="stretch")
else:
    st.dataframe(localized_frame(team), width="stretch", hide_index=True)
