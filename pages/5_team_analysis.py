"""
pages/5_team_analysis.py
--------------------------
Team Analysis page. Rendering logic moved verbatim from dashboard_app.py's
render_team_analysis() (Phase 2 multipage restructure — structural move
only, no behavior/styling changes).
"""

import streamlit as st

from dashboard_styles import section_header
from components.icons import icon_svg
from components import charts as plotly_charts
from components.grid import render_grid
from core.ui_helpers import (
    tr as _ui_tr,
    localized_frame as _ui_localized_frame,
    percentage_columns as _ui_percentage_columns,
    require_app_ctx,
)
from core.analysis import team_df as _team_df

ctx = require_app_ctx()
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
        st.caption(tr(
            "Click a row to filter the whole app to that member (Phase 4 click-to-filter).",
            "انقر على صف لتصفية التطبيق بالكامل حسب هذا العضو.",
        ))
        grid_response = render_grid(
            localized_frame(team), height=360, key="team_analysis_grid",
            selectable=True,
        )
        selected = grid_response.selected_rows
        # localized_frame() relabels headers for display (e.g. Arabic mode
        # renames "Assignee" via core.i18n's column_label), so read whichever
        # of the possible column labels is actually present in the grid's
        # returned selection rather than assuming "Assignee".
        if selected is not None and not selected.empty:
            label_col = next(
                (c for c in selected.columns if c in ("Assignee", "المسؤول")), None
            )
            if label_col is not None:
                picked_assignee = selected.iloc[0][label_col]
                current = st.session_state.get("global_filters", {})
                if current.get("assignees") != [picked_assignee]:
                    current = dict(current)
                    current["assignees"] = [picked_assignee]
                    st.session_state["global_filters"] = current
                    st.session_state["global_filters_gen"] = (
                        st.session_state.get("global_filters_gen", 0) + 1
                    )
                    st.rerun()
    with chart_col:
        section_header("Tasks per member", "المهام لكل عضو", icon_svg("contributor"))
        member_load = team.rename(columns={"Assignee": "member", "Tasks": "tasks"})[
            ["member", "tasks"]
        ]
        st.plotly_chart(
            plotly_charts.hbar_chart(
                member_load, "tasks", "member", chart_theme,
                color=ACCENT["purple"],
            ),
            width="stretch",
            config={"displaylogo": False},
        )
else:
    st.info(tr(
        "No team activity matches the current filters.",
        "لا يوجد نشاط فريق مطابق للفلاتر الحالية.",
    ))
