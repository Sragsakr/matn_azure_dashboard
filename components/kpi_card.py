"""KPI card component built on streamlit-extras' stylable_container.

Rebuilds core.ui_helpers.kpi_card's raw-HTML card as a styled container so
each card gets real hover elevation (CSS transform/box-shadow) and a
clickable affordance (cursor: pointer). No click handling is wired up yet
— actual click-to-filter behavior is Phase 4's global filter bar, out of
scope here. The function signature and visual info (label, value, icon,
subcaption, accent color) are unchanged from core.ui_helpers.kpi_card, so
every existing call site keeps working without modification.

Safe to import from app.py and any page: nothing here executes a widget
call at import time, only inside kpi_card() itself.
"""

import streamlit as st
from streamlit_extras.stylable_container import stylable_container

_CARD_CSS = """
{
    border-radius: 12px;
    padding: 0;
    transition: transform 120ms ease, box-shadow 120ms ease;
    cursor: pointer;
}
:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 24px -12px rgba(0, 0, 0, .45);
}
"""


def kpi_card(column, label, value, accent, icon="◆", subcaption=None, key=None):
    """Render one KPI card into `column` (a Streamlit column/container).

    Same signature/visual output as core.ui_helpers.kpi_card, plus hover
    elevation and a pointer cursor via stylable_container. `key` is
    optional and defaults to a slug of `label` so repeated calls across a
    page (e.g. the ~6 Executive Dashboard KPIs) don't collide.
    """
    container_key = key or "kpi-" + "".join(
        ch.lower() if ch.isalnum() else "-" for ch in str(label)
    ).strip("-")
    with column:
        with stylable_container(key=container_key, css_styles=_CARD_CSS):
            sub_html = f"<div class='kpi-sub'>{subcaption}</div>" if subcaption else ""
            st.markdown(
                f"<div class='kpi-card' style='--accent:{accent}'>"
                f"<div class='kpi-card-top'><span class='kpi-label'>{label}</span>"
                f"<span class='kpi-icon'>{icon}</span></div>"
                f"<div class='kpi-value'>{value}</div>{sub_html}</div>",
                unsafe_allow_html=True,
            )
