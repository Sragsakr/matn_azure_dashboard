"""Streamlit UI helpers shared by app.py and every page under pages/.

Pages must import from here, never from app — pages/*.py is exec()'d by
Streamlit's navigation as a standalone module, and `from app import ...`
re-imports and re-executes app.py's whole module body a second time,
colliding with widget keys already registered in the first run
(StreamlitDuplicateElementKey on "language_selector").
"""

import os

import streamlit as st

from core.analysis import is_open, scope_metrics
from core.i18n import tr as _tr, column_label as _column_label, localized_frame as _localized_frame


def pat():
    """PAT from Streamlit secrets first, then env var."""
    try:
        s = st.secrets.get("AZDO_PAT")
        if s:
            return s
    except Exception:
        pass
    return os.environ.get("AZDO_PAT")


def tr(english, arabic, is_ar):
    return _tr(english, arabic, is_ar)


def column_label(name, is_ar):
    return _column_label(name, is_ar)


def localized_frame(frame, is_ar):
    return _localized_frame(frame, is_ar)


def localized_label(name, is_ar):
    return column_label(name, is_ar)


def percentage_columns(*names, is_ar):
    """Streamlit table formatting for numeric 0..100 percentage columns."""
    return {
        column_label(name, is_ar): st.column_config.NumberColumn(
            column_label(name, is_ar), format="%.1f%%"
        )
        for name in names
    }


def delivery_action(items, unassigned, is_ar):
    open_count = sum(is_open(i) for i in items)
    if unassigned >= 25 and open_count:
        return tr(
            f"{unassigned} tasks are unassigned — assign owners first",
            f"يوجد {unassigned} مهمة بدون مسؤول — ابدأ بتحديد المسؤولين",
            is_ar,
        )
    scope_ = scope_metrics(items)
    if items and scope_["scope_pct"] == 0 and open_count:
        return tr(
            "Scope stalled — no fully-complete story yet",
            "النطاق متعطل — لا توجد قصة مكتملة بالكامل حتى الآن",
            is_ar,
        )
    if any(i["type"] == "User Story" and i["sp"] is None for i in items):
        return tr(
            "Add Story Points to unestimated stories",
            "أضف Story Points للقصص غير المقدّرة",
            is_ar,
        )
    return tr("Delivery on track", "التسليم يسير حسب الخطة", is_ar)


def theme_chart(chart):
    """Apply the active Altair theme to a chart before rendering."""
    return chart


def kpi_card(column, label, value, accent, icon="◆", subcaption=None):
    with column:
        sub_html = f"<div class='kpi-sub'>{subcaption}</div>" if subcaption else ""
        st.markdown(
            f"<div class='kpi-card' style='--accent:{accent}'>"
            f"<div class='kpi-card-top'><span class='kpi-label'>{label}</span>"
            f"<span class='kpi-icon'>{icon}</span></div>"
            f"<div class='kpi-value'>{value}</div>{sub_html}</div>",
            unsafe_allow_html=True,
        )
