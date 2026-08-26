"""Phase 4: persistent global filter bar.

Renders ONCE in app.py, positioned after the enterprise header and before
`st.session_state["app_ctx"]` is built, so every page automatically reads
filtered data through the existing app_ctx mechanism without any
per-page changes.

Widget rendering only lives here; the actual filter predicate is the pure,
independently-testable `core.analysis.apply_global_filters()` so it can be
unit tested without Streamlit and reused by the click-to-filter grid
selection handler in pages/5_team_analysis.py.

Session-only persistence: selections live in
`st.session_state["global_filters"]` and reset on browser refresh, per the
Phase 4 scoping decision (no URL query param persistence).

Safe to import from app.py and any page: nothing here executes a widget
call at import time, only inside render_filter_bar() itself.
"""

import datetime as dt

import streamlit as st

from core.analysis import PB, apply_global_filters

_DEFAULT_FILTERS = {
    "sprints": [],
    "assignees": [],
    "types": [],
    "date_from": None,
    "date_to": None,
}

# Widget keys are versioned so "Clear filters" can force-reset every widget
# by bumping this suffix in session_state, rather than fighting Streamlit's
# rule that a widget's own session_state entry can't be reassigned directly
# once it has been instantiated with a `key=`.
_GEN_KEY = "global_filters_gen"


def _tr(is_ar, english, arabic):
    return arabic if is_ar else english


def _widget_key(base, gen):
    return f"{base}_{gen}"


def render_filter_bar(dev_items, is_ar=False):
    """Render the global filter bar and return the filtered item list.

    `dev_items` should be the full (unfiltered) `dev` list app.py already
    computes. Returns `apply_global_filters(dev_items, filters)` so
    app.py can re-derive all_m/scope/verdict/prog from the result before
    stashing app_ctx.
    """
    if "global_filters" not in st.session_state:
        st.session_state["global_filters"] = dict(_DEFAULT_FILTERS)
    if _GEN_KEY not in st.session_state:
        st.session_state[_GEN_KEY] = 0

    gen = st.session_state[_GEN_KEY]
    filters = st.session_state["global_filters"]

    sprint_options = sorted({i["sprint"] for i in dev_items if i.get("sprint")},
                             key=lambda s: (s == PB, s))
    assignee_options = sorted({i["assignee"] for i in dev_items if i.get("assignee")})
    type_options = sorted({i["type"] for i in dev_items if i.get("type")})
    created_dates = [i["created"] for i in dev_items if i.get("created")]
    min_date = min(created_dates) if created_dates else None
    max_date = max(created_dates) if created_dates else None

    with st.container():
        st.markdown(
            f'<div class="sidebar-label" style="margin-top:0">'
            f'{_tr(is_ar, "GLOBAL FILTERS", "عوامل التصفية العامة")}</div>',
            unsafe_allow_html=True,
        )
        sprint_col, assignee_col, type_col, date_col, clear_col = st.columns(
            [1.3, 1.3, 1.3, 1.6, 0.7]
        )

        with sprint_col:
            selected_sprints = st.multiselect(
                _tr(is_ar, "Sprint / Iteration", "السبرينت"),
                options=sprint_options,
                default=[s for s in filters.get("sprints", []) if s in sprint_options],
                key=_widget_key("gf_sprints", gen),
            )
        with assignee_col:
            selected_assignees = st.multiselect(
                _tr(is_ar, "Assignee", "المسؤول"),
                options=assignee_options,
                default=[a for a in filters.get("assignees", []) if a in assignee_options],
                key=_widget_key("gf_assignees", gen),
            )
        with type_col:
            selected_types = st.multiselect(
                _tr(is_ar, "Work Type", "نوع العمل"),
                options=type_options,
                default=[t for t in filters.get("types", []) if t in type_options],
                key=_widget_key("gf_types", gen),
            )
        with date_col:
            if min_date and max_date:
                default_from = filters.get("date_from") or min_date
                default_to = filters.get("date_to") or max_date
                default_from = max(min_date, min(default_from, max_date))
                default_to = max(min_date, min(default_to, max_date))
                date_range = st.date_input(
                    _tr(is_ar, "Created between", "تاريخ الإنشاء بين"),
                    value=(default_from, default_to),
                    min_value=min_date,
                    max_value=max_date,
                    key=_widget_key("gf_dates", gen),
                )
            else:
                date_range = ()
                st.date_input(
                    _tr(is_ar, "Created between", "تاريخ الإنشاء بين"),
                    value=(),
                    disabled=True,
                    key=_widget_key("gf_dates_disabled", gen),
                )
        with clear_col:
            st.markdown("<div style='height:1.85rem'></div>", unsafe_allow_html=True)
            clear_clicked = st.button(
                _tr(is_ar, "Clear filters", "مسح الفلاتر"),
                width="stretch",
                key=_widget_key("gf_clear", gen),
            )

    if clear_clicked:
        st.session_state["global_filters"] = dict(_DEFAULT_FILTERS)
        st.session_state[_GEN_KEY] = gen + 1
        st.rerun()

    # A user can select just one endpoint of the date_input range widget
    # mid-interaction (Streamlit returns a 1-tuple until the second date is
    # picked) — only treat it as an active bound once both ends are set.
    if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
        date_from, date_to = date_range
    else:
        date_from, date_to = filters.get("date_from"), filters.get("date_to")

    new_filters = {
        "sprints": selected_sprints,
        "assignees": selected_assignees,
        "types": selected_types,
        "date_from": date_from if date_from != min_date else None,
        "date_to": date_to if date_to != max_date else None,
    }
    st.session_state["global_filters"] = new_filters

    active_count = sum([
        bool(new_filters["sprints"]),
        bool(new_filters["assignees"]),
        bool(new_filters["types"]),
        new_filters["date_from"] is not None or new_filters["date_to"] is not None,
    ])
    if active_count:
        st.caption(_tr(
            is_ar,
            f"{active_count} filter group(s) active — every page reflects this selection.",
            f"{active_count} مجموعة فلاتر مفعّلة — تنعكس على جميع الصفحات.",
        ))

    st.divider()

    return apply_global_filters(dev_items, new_filters)
