"""
pages/10_repository_intelligence.py
--------------------------------------
Repository Intelligence page. Rendering logic moved verbatim from
dashboard_app.py's render_repository_intelligence() and its helper
functions (Phase 2 multipage restructure — structural move only, no
behavior/styling changes).
"""

from collections import Counter

import pandas as pd
import requests
import streamlit as st

from dashboard_styles import section_header
from components.icons import icon_svg
from components.kpi_card import kpi_card
from components.grid import render_grid
from components import charts as plotly_charts
from core.analysis import ORG, PROJECT
from core.ui_helpers import pat as _pat
from core.ui_helpers import tr as _ui_tr, localized_frame as _ui_localized_frame
from azure_repo_activity import AzureRepoActivityClient, contributor_rows

ctx = st.session_state["app_ctx"]
is_ar = ctx["is_ar"]
chart_theme = ctx["chart_theme"]
ACCENT = ctx["ACCENT"]
tr = lambda en, ar: _ui_tr(en, ar, is_ar)
localized_frame = lambda frame: _ui_localized_frame(frame, is_ar)


def _repository_rows(rows, selected_repositories):
    return [row for row in rows if row.get("Repository") in selected_repositories]


def _contributor_filter(rows, contributor, name_key):
    if contributor == "All":
        return rows
    return [row for row in rows if row.get(name_key) == contributor]


def _activity_table(title_en, title_ar, rows, height=420):
    st.subheader(tr(title_en, title_ar))
    if not rows:
        st.info(tr("No matching records.", "لا توجد سجلات مطابقة."))
        return
    # Commit/PR/push/file-change rows are repository activity, not work
    # items — no `items=` staleness tinting here (STALE_DAYS is a
    # work-item concept keyed off `created`/`state_category`, which these
    # rows don't have); render_grid is still used for the sortable,
    # filterable, CSV-exportable grid itself.
    render_grid(
        localized_frame(pd.DataFrame(rows)),
        height=height,
        key="repo_activity_" + "_".join(title_en.lower().split()),
    )


def _load_repository_activity():
    pat = _pat()
    if not pat:
        return None
    client = AzureRepoActivityClient(ORG, PROJECT, pat)
    return client.fetch_all()


def _clear_repository_cache_when_requested():
    label = tr("↻ Reload full repository history", "↻ إعادة تحميل كل تاريخ المستودعات")
    if not st.button(label):
        return
    st.session_state.pop("repository_activity", None)
    st.session_state.pop("repository_activity_error", None)


def _fetch_repository_cache():
    if "repository_activity" in st.session_state or not _pat():
        return
    message = tr(
        "Loading all repository history and file changes. This can take several minutes...",
        "جارٍ تحميل كل تاريخ المستودعات وتغييرات الملفات. قد يستغرق ذلك عدة دقائق...",
    )
    with st.spinner(message):
        try:
            st.session_state["repository_activity"] = _load_repository_activity()
        except requests.RequestException as exc:
            st.session_state["repository_activity_error"] = str(exc)


def _repository_cache():
    if not _pat():
        st.warning(tr(
            "AZDO_PAT with Code (Read) permission is required to load repository history.",
            "يلزم AZDO_PAT بصلاحية Code (Read) لتحميل تاريخ المستودعات.",
        ))
        return None
    error = st.session_state.get("repository_activity_error")
    if error:
        st.error(tr(
            f"Repository history could not be loaded: {error}",
            f"تعذر تحميل تاريخ المستودعات: {error}",
        ))
        return None
    activity = st.session_state.get("repository_activity")
    if not activity:
        st.info(tr("No repository activity loaded.", "لم يتم تحميل نشاط المستودعات."))
    return activity


def _repository_filter_controls(activity):
    repository_names = sorted(row["Repository"] for row in activity["repositories"])
    selected_repositories = st.multiselect(
        tr("Repositories", "المستودعات"), repository_names, default=repository_names
    )
    contributor_names = {
        row.get(key)
        for dataset_key, key in (("commits", "Author"), ("pushes", "Pushed By"),
                                 ("pull_requests", "Created By"))
        for row in activity[dataset_key] if row.get(key)
    }
    contributor = st.selectbox(
        tr("Contributor", "المساهم"), ["All", *sorted(contributor_names)],
        format_func=lambda value: tr(value, "الكل") if value == "All" else value,
    )
    statuses = sorted({row.get("Status", "") for row in activity["pull_requests"]})
    selected_statuses = st.multiselect(
        tr("Pull request status", "حالة Pull Request"), statuses, default=statuses
    )
    return selected_repositories, contributor, selected_statuses


def _filtered_repository_activity(activity, filter_values):
    repositories, contributor, statuses = filter_values
    selected = {
        key: _repository_rows(activity[key], repositories)
        for key in ("repositories", "commits", "pushes", "pull_requests", "changes")
    }
    selected["commits"] = _contributor_filter(selected["commits"], contributor, "Author")
    selected["pushes"] = _contributor_filter(selected["pushes"], contributor, "Pushed By")
    selected["pull_requests"] = _contributor_filter(
        selected["pull_requests"], contributor, "Created By"
    )
    selected["pull_requests"] = [
        row for row in selected["pull_requests"] if row.get("Status") in statuses
    ]
    selected["changes"] = _contributor_filter(selected["changes"], contributor, "Author")
    selected["contributors"] = contributor_rows(selected)
    return selected


def _render_repository_kpis(activity):
    columns = st.columns(6, gap="small")
    values = (
        (tr("Repositories", "المستودعات"), len(activity["repositories"]), ACCENT["blue"], "repo"),
        (tr("Contributors", "المساهمون"), len(activity["contributors"]), ACCENT["purple"], "contributor"),
        ("Commits", len(activity["commits"]), ACCENT["green"], "check"),
        (tr("Pushes", "عمليات الرفع"), len(activity["pushes"]), ACCENT["teal"], "refresh"),
        ("Pull Requests", len(activity["pull_requests"]), ACCENT["gold"], "pull-request"),
        (tr("Changed files", "الملفات المتغيرة"), len(activity["changes"]), ACCENT["pink"], "files"),
    )
    for column, (label, value, accent, icon) in zip(columns, values):
        kpi_card(column, label, value, accent, icon=icon_svg(icon))


def _render_repository_tables(activity, failures):
    table_col, chart_col = st.columns([1, 1.4])
    with table_col:
        _activity_table("Contributor summary", "ملخص المساهمين", activity["contributors"])
    with chart_col:
        section_header("Commits per contributor", "Commits لكل مساهم", icon_svg("repo"))
        if activity["contributors"]:
            commit_load = [
                {"member": row["Contributor"], "commits": row["Commits"]}
                for row in activity["contributors"]
            ]
            st.plotly_chart(
                plotly_charts.hbar_chart(
                    pd.DataFrame(commit_load), "commits", "member",
                    chart_theme, color=ACCENT["blue"],
                ),
                width="stretch",
                config={"displaylogo": False},
            )
    pr_status = Counter(row.get("Status", "") for row in activity["pull_requests"])
    status_col, inventory_col = st.columns([1, 1.4])
    with status_col:
        section_header("Pull request outcomes", "نتائج Pull Requests", icon_svg("pull-request"))
        if pr_status:
            st.plotly_chart(
                plotly_charts.generic_donut(
                    pd.DataFrame({"status": list(pr_status), "total": list(pr_status.values())}),
                    "status", "total", chart_theme,
                    colors={"completed": ACCENT["green"], "active": ACCENT["blue"],
                            "abandoned": ACCENT["red"]},
                ),
                width="stretch",
                config={"displaylogo": False},
            )
    with inventory_col:
        _activity_table("Repository inventory", "قائمة المستودعات", activity["repositories"])
    _activity_table("Complete commit history", "كل تاريخ Commits", activity["commits"], 520)
    _activity_table("Complete push history", "كل تاريخ عمليات الرفع", activity["pushes"], 480)
    _activity_table("All pull requests", "كل Pull Requests", activity["pull_requests"], 520)
    _activity_table("All changed files", "كل الملفات المتغيرة", activity["changes"], 600)
    if not failures:
        return
    st.warning(tr(
        "Some repository API calls failed; all successful data is still shown below.",
        "فشلت بعض استدعاءات المستودعات؛ ما زالت كل البيانات الناجحة معروضة.",
    ))
    _activity_table("Collection failures", "أخطاء جمع البيانات", failures)


st.header(tr("Repository Intelligence", "ذكاء المستودعات"))
st.caption(tr(
    "All-history Azure Repos inventory, contributor activity, commits, pushes, PRs and changed files.",
    "كل تاريخ مستودعات Azure: المساهمون وCommits وعمليات الرفع وPull Requests والملفات المتغيرة.",
))
_clear_repository_cache_when_requested()
_fetch_repository_cache()
activity = _repository_cache()
if activity:
    filtered = _filtered_repository_activity(
        activity, _repository_filter_controls(activity)
    )
    _render_repository_kpis(filtered)
    _render_repository_tables(filtered, activity["failures"])
