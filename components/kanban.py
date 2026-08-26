"""Read-only Kanban board renderer for the Sprint Board page (Phase 5).

Plain-Streamlit implementation (st.columns + st.container(border=True)) —
see pages/3_sprint_board.py's module docstring for why this was chosen over
streamlit-elements. Groups normalized work-item dicts (core.analysis._wi /
read_workbook_items shape) by their Azure `board_column` field and renders
one non-interactive card per item: no drag-and-drop, no state mutation, no
write-back to Azure DevOps — this mirrors board state for reading only.

Nothing here calls a Streamlit widget at import time, so it is safe to
import from app.py and from any page module (see the Phase 2 lesson in
pages/3_sprint_board.py / core/ui_helpers.py docstrings: pages must never
`from app import ...`).
"""

import datetime as dt
import html

import streamlit as st

from core.analysis import STALE_DAYS, is_open
from components.icons import icon_svg

# Work-item type -> icon name in components/icons.py's _ICONS table.
_TYPE_ICON = {
    "Epic": "epic",
    "Feature": "feature",
    "User Story": "story",
    "Task": "task",
    "Bug": "bug",
    "Test Case": "task",
    "Test Suite": "task",
    "Test Plan": "task",
}

# Deterministic column ordering: Azure board columns vary per project/team,
# so we cannot hardcode exact names. Instead, sort columns by the *typical*
# progression implied by each column's own items — the mean of
# board_column_done (True/False) and whether any item in it is "InProgress"
# — so a "Done"-ish column reliably lands last and a "To Do"-ish column
# lands first, without assuming specific Azure column labels.
def _column_sort_key(column_name, column_items):
    any_done = any(i.get("board_column_done") for i in column_items)
    any_active = any(i.get("state_category") == "InProgress" for i in column_items)
    if any_done:
        rank = 2
    elif any_active:
        rank = 1
    else:
        rank = 0
    return (rank, column_name)


# Distinct, deterministic avatar colors keyed by assignee name, cycling
# through the shared ACCENTS palette so avatars stay theme-consistent
# instead of introducing new hex literals (dashboard_theme.py's docstring:
# ACCENTS/PALETTES are the single source of truth for color).
_AVATAR_PALETTE_KEYS = ("blue", "green", "purple", "amber", "teal", "pink", "gold", "indigo", "red")


def _initials(name):
    if not name or name == "Unassigned":
        return "?"
    parts = [p for p in str(name).replace(".", " ").split() if p]
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


def _avatar_color(name, accents):
    key = _AVATAR_PALETTE_KEYS[hash(str(name)) % len(_AVATAR_PALETTE_KEYS)]
    return accents.get(key, accents["blue"])


def _age_days(item):
    if not item.get("created"):
        return None
    return (dt.date.today() - item["created"]).days


def _staleness_badge(item, is_ar, accents):
    """(label, color) for the age badge — reuses core.analysis.is_open() /
    STALE_DAYS exactly like components/grid.py's row-style rule, rather
    than reinventing what counts as stale."""
    age = _age_days(item)
    if age is None:
        return None, None
    if is_open(item) and age >= STALE_DAYS:
        color = accents["red"]
    elif is_open(item) and age >= STALE_DAYS // 2:
        color = accents["amber"]
    else:
        color = accents["green"]
    label = f"{age}d" if not is_ar else f"{age} يوم"
    return label, color


def _card_html(item, is_ar, accents):
    type_icon = icon_svg(_TYPE_ICON.get(item["type"], "task"), size=14)
    initials = _initials(item["assignee"])
    avatar_color = _avatar_color(item["assignee"], accents)
    age_label, age_color = _staleness_badge(item, is_ar, accents)
    age_html = (
        f'<span class="kb-age-badge" style="--age-color:{age_color}">{age_label}</span>'
        if age_label else ""
    )
    sp = item.get("sp")
    sp_html = f'<span class="kb-sp-badge">{sp:g} SP</span>' if sp not in (None, "") else ""
    tags = item.get("tags") or []
    tags_html = "".join(f'<span class="kb-tag">{html.escape(str(t))}</span>' for t in tags[:4])
    if len(tags) > 4:
        tags_html += f'<span class="kb-tag kb-tag-more">+{len(tags) - 4}</span>'
    title = html.escape(item["title"] or ("(untitled)" if not is_ar else "(بدون عنوان)"))
    assignee = html.escape(str(item["assignee"]))
    return f"""
    <div class="kb-card">
      <div class="kb-card-top">
        <span class="kb-type-icon">{type_icon}</span>
        <a class="kb-id" href="{item['url']}" target="_blank" rel="noopener">#{item['id']}</a>
        {age_html}
      </div>
      <div class="kb-title">{title}</div>
      <div class="kb-badges">{sp_html}{tags_html}</div>
      <div class="kb-card-bottom">
        <span class="kb-avatar" style="--avatar-color:{avatar_color}" title="{assignee}">{initials}</span>
        <span class="kb-assignee">{assignee}</span>
      </div>
    </div>
    """


_KANBAN_CSS = """
<style>
.kb-column-head {
    display:flex; align-items:center; justify-content:space-between;
    padding:.35rem .55rem; border-radius:8px 8px 0 0;
    background:var(--surface2); border:1px solid var(--line); border-bottom:none;
    font-weight:700; font-size:.78rem; color:var(--ink);
}
.kb-column-count {
    background:var(--surface); border:1px solid var(--line); border-radius:999px;
    padding:.05rem .5rem; font-size:.72rem; color:var(--muted); font-weight:600;
}
.kb-column-body {
    border:1px solid var(--line); border-top:none; border-radius:0 0 8px 8px;
    padding:.5rem; min-height:80px; background:var(--bg);
}
.kb-card {
    background:var(--surface); border:1px solid var(--line); border-radius:8px;
    padding:.5rem .6rem; margin-bottom:.5rem;
}
.kb-card-top { display:flex; align-items:center; gap:.35rem; margin-bottom:.3rem; }
.kb-type-icon { display:inline-flex; color:var(--muted); }
.kb-id { color:var(--muted); font-size:.72rem; text-decoration:none; font-weight:600; }
.kb-id:hover { color:var(--ink); text-decoration:underline; }
.kb-age-badge {
    margin-inline-start:auto; background:color-mix(in srgb, var(--age-color) 18%, transparent);
    color:var(--age-color); border-radius:999px; padding:.05rem .45rem;
    font-size:.68rem; font-weight:700;
}
.kb-title {
    font-size:.82rem; color:var(--ink); line-height:1.3; margin-bottom:.4rem;
    display:-webkit-box; -webkit-line-clamp:3; -webkit-box-orient:vertical; overflow:hidden;
}
.kb-badges { display:flex; flex-wrap:wrap; gap:.3rem; margin-bottom:.45rem; }
.kb-sp-badge {
    background:var(--surface2); border:1px solid var(--line); border-radius:5px;
    padding:.05rem .4rem; font-size:.68rem; color:var(--muted); font-weight:700;
}
.kb-tag {
    background:var(--surface2); border-radius:5px; padding:.05rem .4rem;
    font-size:.68rem; color:var(--muted);
}
.kb-tag-more { color:var(--muted2); }
.kb-card-bottom { display:flex; align-items:center; gap:.4rem; }
.kb-avatar {
    width:20px; height:20px; border-radius:50%; background:var(--avatar-color);
    color:#fff; font-size:.62rem; font-weight:800; display:flex; align-items:center;
    justify-content:center; flex-shrink:0;
}
.kb-assignee {
    font-size:.72rem; color:var(--muted); overflow:hidden; text-overflow:ellipsis;
    white-space:nowrap;
}
</style>
"""


def render_kanban(items, is_ar, accents, key="kanban"):
    """Render `items` (normalized work-item dicts) as a read-only Kanban
    board grouped by each item's `board_column` field, one st.column per
    board column and one st.container(border=True)-free HTML card per item
    inside. Purely visual — no drag/drop, no write-back to Azure DevOps.
    """
    st.markdown(_KANBAN_CSS, unsafe_allow_html=True)

    if not items:
        st.info(
            "No items match the current filters." if not is_ar
            else "لا توجد عناصر مطابقة للفلاتر الحالية."
        )
        return

    columns = {}
    for item in items:
        columns.setdefault(item.get("board_column") or item.get("state") or "Unknown", []).append(item)

    ordered_names = sorted(columns, key=lambda name: _column_sort_key(name, columns[name]))
    st_columns = st.columns(len(ordered_names))

    for st_col, col_name in zip(st_columns, ordered_names):
        col_items = columns[col_name]
        with st_col:
            st.markdown(
                f'<div class="kb-column-head"><span>{html.escape(str(col_name))}</span>'
                f'<span class="kb-column-count">{len(col_items)}</span></div>',
                unsafe_allow_html=True,
            )
            cards_html = "".join(_card_html(i, is_ar, accents) for i in col_items)
            st.markdown(f'<div class="kb-column-body">{cards_html}</div>', unsafe_allow_html=True)
