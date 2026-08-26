"""
pages/1_executive_dashboard.py
-------------------------------
Executive Dashboard page. Rendering logic moved verbatim from
dashboard_app.py's render_executive() (Phase 2 multipage restructure —
structural move only, no behavior/styling changes).

Phase 3 (component library reference implementation): this page is the
first to use the new components/ package — icons.py (stroke SVG icon set
replacing Unicode glyphs), kpi_card.py (stylable_container-based KPI
cards), and charts.py (Plotly versions of this page's three Altair charts,
plus a brand-new Epic->Feature->User Story->Task sunburst/treemap view).
No other page's rendering was touched in this phase.
"""

from collections import Counter

import pandas as pd
import streamlit as st

from dashboard_styles import section_header
from components.icons import icon_svg
from components.kpi_card import kpi_card
from components import charts as plotly_charts
from core.ui_helpers import (
    tr as _ui_tr,
    localized_frame as _ui_localized_frame,
    localized_label as _ui_localized_label,
    percentage_columns as _ui_percentage_columns,
    delivery_action as _ui_delivery_action,
)
from core.analysis import DELIVERY_TYPES, PB, percent, weekly_creation_closure

ctx = st.session_state["app_ctx"]
is_ar = ctx["is_ar"]
tr = lambda en, ar: _ui_tr(en, ar, is_ar)
localized_frame = lambda frame: _ui_localized_frame(frame, is_ar)
localized_label = lambda name: _ui_localized_label(name, is_ar)
percentage_columns = lambda *names: _ui_percentage_columns(*names, is_ar=is_ar)
delivery_action = lambda items, unassigned: _ui_delivery_action(items, unassigned, is_ar)
chart_theme = ctx["chart_theme"]
ACCENT = ctx["ACCENT"]
dev = ctx["dev"]
all_m = ctx["all_m"]
scope = ctx["scope"]
verdict = ctx["verdict"]
color = ctx["color"]
prog = ctx["prog"]


st.header(tr("Executive Delivery Overview", "النظرة التنفيذية للتسليم"))
st.caption(tr(
    "Live Azure DevOps delivery health, ownership and execution signals.",
    "مؤشرات حية لصحة التسليم والتنفيذ وتوزيع المسؤوليات من Azure DevOps.",
))
verdict_label = {
    "HEALTHY": tr("Healthy", "مستقر"),
    "AT RISK": tr("At risk", "معرّض للخطر"),
    "CRITICAL": tr("Critical", "حرج"),
}[verdict]
st.markdown(
    f"<div class='health-ribbon' style='--health:{color}'>"
    f"{verdict_label} · {delivery_action(dev, all_m['unassigned'])}</div>",
    unsafe_allow_html=True,
)

if not dev:
    st.warning(tr("No work items to chart yet.", "لا توجد عناصر عمل لعرضها."))
else:
    # Phase 6: fixed 2-row x 3-column KPI grid instead of a single 6-across
    # row. Streamlit's st.columns doesn't reflow at narrow viewports (columns
    # just shrink in place), so a single row of 6 becomes unreadably cramped
    # on mobile. Two rows of 3 "always looks intentional" (per the brief)
    # without needing any JS-based viewport detection.
    backlog_count = sum(1 for item in dev if item["sprint"] == PB)
    row1 = st.columns(3, gap="small")
    kpi_card(row1[0], tr("Story scope done", "نطاق القصص المكتمل"), f"{scope['scope_pct'] or 0:.0%}", ACCENT["green"],
              icon=icon_svg("percent"), subcaption=tr(f"{scope['stories_done']} of {scope['stories']} stories", f"{scope['stories_done']} من {scope['stories']} قصة"))
    kpi_card(row1[1], tr("Task completion", "اكتمال المهام"), f"{scope['task_pct'] or 0:.0%}", ACCENT["blue"],
              icon=icon_svg("check"), subcaption=tr(f"{scope['tasks_done']} of {scope['tasks']} tasks", f"{scope['tasks_done']} من {scope['tasks']} مهمة"))
    kpi_card(row1[2], tr("Active now", "قيد التنفيذ"), all_m["active"], ACCENT["purple"],
              icon=icon_svg("active"), subcaption=tr("items in progress", "عنصر نشط الآن"))
    row2 = st.columns(3, gap="small")
    kpi_card(row2[0], tr("Unassigned", "بدون مسؤول"), all_m["unassigned"], ACCENT["red"],
              icon=icon_svg("warning"), subcaption=tr("tasks need an owner", "مهمة تحتاج تعيين"))
    kpi_card(row2[1], tr("Product backlog", "قائمة المنتج"), backlog_count, ACCENT["gold"],
              icon=icon_svg("folder"), subcaption=tr("items with no sprint", "عنصر بدون سبرينت"))
    kpi_card(row2[2], tr("Stale ≥14d", "متقادم ≥14 يوم"), all_m["stale"], ACCENT["amber"],
              icon=icon_svg("clock"), subcaption=tr("no delay" if not all_m["stale"] else "needs attention", "لا يوجد تأخير" if not all_m["stale"] else "يحتاج متابعة"))

    section_header(
        "Completion by work type",
        "الاكتمال حسب نوع عنصر العمل", icon_svg("executive"))
    prog_df = pd.DataFrame([
        {"Work Type": work_type, "Total": prog[work_type]["total"],
         "Done": prog[work_type]["done"],
         "Completion %": percent(prog[work_type]["pct"])}
        for work_type in DELIVERY_TYPES
    ])
    table_col, chart_col = st.columns([1, 1.15])
    with table_col:
        st.dataframe(
            localized_frame(prog_df), width="stretch", hide_index=True,
            column_config={
                **percentage_columns("Completion %"),
                localized_label("Total"): st.column_config.NumberColumn(
                    localized_label("Total"), format="%d"),
                localized_label("Done"): st.column_config.NumberColumn(
                    localized_label("Done"), format="%d"),
            },
        )
    with chart_col:
        donut_tab, hierarchy_tab = st.tabs([
            tr("By type", "حسب النوع"),
            tr("Hierarchy", "التسلسل الهرمي"),
        ])
        with donut_tab:
            st.plotly_chart(
                plotly_charts.completion_donut(prog_df, chart_theme),
                width="stretch",
                config={"displaylogo": False},
            )
        with hierarchy_tab:
            layout_choice = st.radio(
                tr("Layout", "التخطيط"),
                [tr("Sunburst", "شعاعي"), tr("Treemap", "خريطة شجرية")],
                horizontal=True, label_visibility="collapsed",
                key="exec_hierarchy_layout",
            )
            if layout_choice == tr("Sunburst", "شعاعي"):
                hierarchy_fig = plotly_charts.completion_sunburst(
                    dev, prog, chart_theme, DELIVERY_TYPES)
            else:
                hierarchy_fig = plotly_charts.completion_treemap(
                    dev, prog, chart_theme, DELIVERY_TYPES)
            st.plotly_chart(hierarchy_fig, width="stretch", config={"displaylogo": False})
    hier_txt = tr(
        "child→parent roll-up active ✅",
        "تجميع نتائج الأبناء إلى العناصر الرئيسية مفعّل ✅",
    ) if prog["hierarchy_used"] else tr(
        "own-state (add Parent ID for roll-up)",
        "الاعتماد على حالة العنصر (أضف Parent ID لتفعيل التجميع)",
    )
    st.caption(tr(f"Hierarchy: {hier_txt}", f"التسلسل الهرمي: {hier_txt}"))

    section_header("Current board flow", "تدفق العمل الحالي", icon_svg("board"))
    state_df = pd.DataFrame([
        {"State": state, "Category": category, "Items": count}
        for (state, category), count in Counter(
            (i["state"], i["state_category"]) for i in dev
        ).most_common()
    ])
    table_col, chart_col = st.columns([1, 1.2])
    with table_col:
        st.caption(tr("Exact Azure states and canonical categories", "حالات Azure الفعلية وتصنيفاتها"))
        st.dataframe(localized_frame(state_df), width="stretch", hide_index=True)
    with chart_col:
        st.caption(tr("Items by Azure Board column and category", "العناصر حسب عمود اللوحة والتصنيف"))
        board_flow = pd.DataFrame([
            {"column": column_name, "category": category, "items": count}
            for (column_name, category), count in Counter(
                (i["board_column"], i["state_category"]) for i in dev
            ).most_common()
        ])
        st.plotly_chart(
            plotly_charts.board_flow_bar(board_flow, chart_theme),
            width="stretch",
            config={"displaylogo": False},
        )

    section_header("Delivery momentum", "زخم التسليم", icon_svg("active"))
    week_frame = weekly_creation_closure(dev)
    if week_frame.empty:
        st.info(tr("No dated items yet.", "لا توجد عناصر بتواريخ بعد."))
    else:
        st.plotly_chart(
            plotly_charts.momentum_area(week_frame, chart_theme),
            width="stretch",
            config={"displaylogo": False},
        )
