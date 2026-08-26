"""
pages/1_executive_dashboard.py
-------------------------------
Executive Dashboard page. Rendering logic moved verbatim from
dashboard_app.py's render_executive() (Phase 2 multipage restructure —
structural move only, no behavior/styling changes).
"""

from collections import Counter

import pandas as pd
import streamlit as st

import dashboard_theme
from dashboard_styles import section_header
from app import tr, kpi_card, localized_frame, localized_label, percentage_columns, delivery_action
from core.analysis import DELIVERY_TYPES, PB, percent, weekly_creation_closure

ctx = st.session_state["app_ctx"]
is_ar = ctx["is_ar"]
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
    columns = st.columns(6, gap="small")
    kpi_card(columns[0], tr("Story scope done", "نطاق القصص المكتمل"), f"{scope['scope_pct'] or 0:.0%}", ACCENT["green"],
              icon="%", subcaption=tr(f"{scope['stories_done']} of {scope['stories']} stories", f"{scope['stories_done']} من {scope['stories']} قصة"))
    kpi_card(columns[1], tr("Task completion", "اكتمال المهام"), f"{scope['task_pct'] or 0:.0%}", ACCENT["blue"],
              icon="✓", subcaption=tr(f"{scope['tasks_done']} of {scope['tasks']} tasks", f"{scope['tasks_done']} من {scope['tasks']} مهمة"))
    kpi_card(columns[2], tr("Active now", "قيد التنفيذ"), all_m["active"], ACCENT["purple"],
              icon="⚡", subcaption=tr("items in progress", "عنصر نشط الآن"))
    kpi_card(columns[3], tr("Unassigned", "بدون مسؤول"), all_m["unassigned"], ACCENT["red"],
              icon="!", subcaption=tr("tasks need an owner", "مهمة تحتاج تعيين"))
    backlog_count = sum(1 for item in dev if item["sprint"] == PB)
    kpi_card(columns[4], tr("Product backlog", "قائمة المنتج"), backlog_count, ACCENT["gold"],
              icon="▤", subcaption=tr("items with no sprint", "عنصر بدون سبرينت"))
    kpi_card(columns[5], tr("Stale ≥14d", "متقادم ≥14 يوم"), all_m["stale"], ACCENT["amber"],
              icon="⏱", subcaption=tr("no delay" if not all_m["stale"] else "needs attention", "لا يوجد تأخير" if not all_m["stale"] else "يحتاج متابعة"))

    section_header(
        "Completion by work type",
        "الاكتمال حسب نوع عنصر العمل", "◈")
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
        type_colors = {
            "Epic": ACCENT["purple"], "Feature": ACCENT["blue"],
            "User Story": ACCENT["teal"], "Task": ACCENT["green"], "Bug": ACCENT["red"],
        }
        st.altair_chart(dashboard_theme.donut_chart(
            prog_df.rename(columns={"Work Type": "kind", "Total": "total"}),
            "kind", "total", chart_theme, colors=type_colors,
        ), width="stretch")
    hier_txt = tr(
        "child→parent roll-up active ✅",
        "تجميع نتائج الأبناء إلى العناصر الرئيسية مفعّل ✅",
    ) if prog["hierarchy_used"] else tr(
        "own-state (add Parent ID for roll-up)",
        "الاعتماد على حالة العنصر (أضف Parent ID لتفعيل التجميع)",
    )
    st.caption(tr(f"Hierarchy: {hier_txt}", f"التسلسل الهرمي: {hier_txt}"))

    section_header("Current board flow", "تدفق العمل الحالي", "▦")
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
        st.altair_chart(dashboard_theme.stacked_hbar_chart(
            board_flow, "column", "category", "items", chart_theme
        ), width="stretch")

    section_header("Delivery momentum", "زخم التسليم", "⚡")
    week_frame = weekly_creation_closure(dev)
    if week_frame.empty:
        st.info(tr("No dated items yet.", "لا توجد عناصر بتواريخ بعد."))
    else:
        st.altair_chart(dashboard_theme.area_trend_chart(
            week_frame, "period", ("Closed", "Created"),
            {"Closed": ACCENT["green"], "Created": ACCENT["blue"]}, chart_theme,
        ), width="stretch")
