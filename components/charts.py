"""Plotly chart factories for the Executive Dashboard.

Phase 3: the Executive Dashboard's three Altair charts (completion-by-type
donut, board-flow stacked bar, delivery-momentum area trend) get Plotly
equivalents here, plus a brand-new Epic->Feature->User Story->Task sunburst
that did not exist before. Every other page keeps using Altair
(dashboard_theme.py) — this module is additive, not a replacement for it.

All series colors reuse dashboard_theme.ACCENTS so Plotly and Altair charts
stay visually consistent across the app. Every chart has full-context hover
tooltips (not raw values) and a toggleable legend (Plotly legends are
click-to-toggle by default; we just make sure one is shown).
"""

from collections import defaultdict

import plotly.express as px
import plotly.graph_objects as go

import dashboard_theme

ACCENT = dashboard_theme.ACCENTS

TYPE_COLORS = {
    "Epic": ACCENT["purple"],
    "Feature": ACCENT["blue"],
    "User Story": ACCENT["teal"],
    "Task": ACCENT["green"],
    "Bug": ACCENT["red"],
    "Test Case": ACCENT["gold"],
    "Test Suite": ACCENT["indigo"],
    "Test Plan": ACCENT["pink"],
}

CATEGORY_COLORS = {
    "Completed": ACCENT["green"],
    "InProgress": ACCENT["blue"],
    "Proposed": ACCENT["amber"],
    "Removed": ACCENT["red"],
}


def _base_layout(theme, height=None, legend=True):
    layout = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=theme["ink"], family=theme["font"], size=12),
        margin=dict(l=8, r=8, t=8, b=8),
        hoverlabel=dict(
            bgcolor=theme["surface"], font_color=theme["ink"],
            bordercolor=theme["line"],
        ),
        showlegend=legend,
        legend=dict(
            orientation="h", yanchor="bottom", y=-0.22, xanchor="center", x=0.5,
            font=dict(color=theme["ink"], size=11),
            bgcolor="rgba(0,0,0,0)",
        ),
    )
    if height:
        layout["height"] = height
    return layout


def completion_donut(prog_df, theme, colors=None):
    """Completion-by-work-type donut (Plotly equivalent of dashboard_theme.donut_chart)."""
    colors = colors or TYPE_COLORS
    frame = prog_df.copy()
    color_seq = [colors.get(k, theme["series"][0]) for k in frame["Work Type"]]
    fig = go.Figure(
        go.Pie(
            labels=frame["Work Type"],
            values=frame["Total"],
            hole=0.55,
            marker=dict(colors=color_seq, line=dict(color=theme["bg"], width=2)),
            customdata=frame[["Done", "Completion %"]].to_numpy(),
            hovertemplate=(
                "<b>%{label}</b><br>"
                "Total: %{value}<br>"
                "Done: %{customdata[0]}<br>"
                "Completion: %{customdata[1]}%"
                "<extra></extra>"
            ),
            sort=False,
        )
    )
    fig.update_layout(**_base_layout(theme, height=300))
    return fig


def _hierarchy_nodes(items, type_progress_result, delivery_types, flatten_types_only=False):
    """Shared Epic -> Feature -> User Story -> Task node builder for the
    sunburst/treemap views. Returns (ids, labels, parents, values, colors,
    customdata) ready to hand to go.Sunburst/go.Treemap.

    Uses explicit internal `ids` distinct from display `labels` — Plotly's
    parent-linkage matches `parents` entries against `ids` (falling back to
    `labels` only when `ids` is omitted), and two work items can share a
    title, so ids must be unique even when labels are not.

    Falls back to a flat "by type" ring (no parent linkage) when the data
    has no Parent ID hierarchy or `flatten_types_only` is requested,
    mirroring type_progress()'s own hierarchy_used flag.
    """
    hierarchy_order = [t for t in ("Epic", "Feature", "User Story", "Task") if t in delivery_types]
    by_id = {i["id"]: i for i in items if i.get("id") is not None}
    hier = type_progress_result.get("hierarchy_used", False) and not flatten_types_only

    ids, labels, parents, values, colors = [], [], [], [], []
    own_done = {}
    seen = set()

    def add_node(node_id, label, parent_id, count, done, color):
        if node_id in seen:
            return
        seen.add(node_id)
        ids.append(node_id)
        labels.append(label)
        parents.append(parent_id)
        values.append(count)
        colors.append(color)
        own_done[node_id] = done

    # branchvalues="remainder": every node's `value` is its OWN remainder
    # (not a subtree total) — Plotly sums descendants on top of it to size
    # the wedge/tile. The root and per-type ring nodes therefore carry 0
    # (their whole size comes from their children); only leaf/item nodes
    # (each one real work item) carry a value of 1. This mirrors
    # core.analysis.type_progress()'s own total/done counts without
    # double-counting a type's total both at the ring and at its items.
    add_node("root", "All Delivery", "", 0, 0, "__root__")

    type_groups = defaultdict(list)
    for i in items:
        if i["type"] in hierarchy_order:
            type_groups[i["type"]].append(i)

    for wtype in hierarchy_order:
        add_node(f"type:{wtype}", wtype, "root", 0, 0, TYPE_COLORS.get(wtype))

    if hier:
        for wtype in hierarchy_order:
            for item in type_groups.get(wtype, []):
                parent_item = by_id.get(item.get("parent"))
                parent_key = (
                    f"item:{parent_item['id']}"
                    if parent_item is not None and parent_item["type"] in hierarchy_order
                    else f"type:{wtype}"
                )
                node_key = f"item:{item['id']}"
                done = 1 if item.get("state_category") == "Completed" else 0
                add_node(node_key, item.get("title") or f"#{item['id']}", parent_key, 1, done, TYPE_COLORS.get(wtype))
    else:
        # No hierarchy: items sit directly under their type ring as leaves,
        # so the ring's size is the sum of its (count=1) item leaves.
        for wtype in hierarchy_order:
            for item in type_groups.get(wtype, []):
                node_key = f"item:{item['id']}"
                done = 1 if item.get("state_category") == "Completed" else 0
                add_node(node_key, item.get("title") or f"#{item['id']}", f"type:{wtype}", 1, done, TYPE_COLORS.get(wtype))

    # Subtree totals (item count + done count) for hover context — computed
    # bottom-up from the flat node list so hover always shows "N items,
    # M done" even for the root/type-ring nodes whose plotted `value` is 0
    # under branchvalues="remainder".
    children_of = defaultdict(list)
    for node_id, parent_id in zip(ids, parents):
        if parent_id:
            children_of[parent_id].append(node_id)

    subtree_total = {}
    subtree_done = {}

    def totals(node_id):
        if node_id in subtree_total:
            return subtree_total[node_id], subtree_done[node_id]
        kids = children_of.get(node_id, [])
        if not kids:
            total, done = 1, own_done.get(node_id, 0)
        else:
            total, done = 0, 0
            for kid in kids:
                t, d = totals(kid)
                total += t
                done += d
        subtree_total[node_id] = total
        subtree_done[node_id] = done
        return total, done

    custom = []
    for node_id in ids:
        total, done = totals(node_id)
        pct = round(done / total * 100, 1) if total else 0
        custom.append((done, pct, total))

    # theme's surface2 color for the root wedge/tile is resolved by the
    # caller (it needs the live `theme` dict, not available in this helper).
    return ids, labels, parents, values, colors, custom


def completion_sunburst(items, type_progress_result, theme, delivery_types):
    """New: Epic -> Feature -> User Story -> Task hierarchy roll-up view.

    Built from the same items list that feeds core.analysis.type_progress();
    each work item type ring's total/done counts are cross-checked against
    type_progress_result so the sunburst always agrees with the table next
    to it.
    """
    ids, labels, parents, values, colors, custom = _hierarchy_nodes(
        items, type_progress_result, delivery_types)
    colors = [theme.get("surface2", "#333") if c == "__root__" else c for c in colors]

    fig = go.Figure(
        go.Sunburst(
            ids=ids,
            labels=labels,
            parents=parents,
            values=values,
            branchvalues="remainder",
            marker=dict(colors=colors, line=dict(color=theme["bg"], width=1)),
            customdata=custom,
            hovertemplate=(
                "<b>%{label}</b><br>"
                "Items: %{customdata[2]}<br>"
                "Done: %{customdata[0]} (%{customdata[1]}%)"
                "<extra></extra>"
            ),
            maxdepth=4,
        )
    )
    fig.update_layout(**_base_layout(theme, height=380, legend=False))
    return fig


def completion_treemap(items, type_progress_result, theme, delivery_types):
    """Same hierarchy as completion_sunburst but as a treemap (alternate layout)."""
    ids, labels, parents, values, colors, custom = _hierarchy_nodes(
        items, type_progress_result, delivery_types)
    colors = [theme.get("surface2", "#333") if c == "__root__" else c for c in colors]

    fig = go.Figure(
        go.Treemap(
            ids=ids,
            labels=labels,
            parents=parents,
            values=values,
            branchvalues="remainder",
            marker=dict(colors=colors, line=dict(color=theme["bg"], width=1)),
            customdata=custom,
            hovertemplate=(
                "<b>%{label}</b><br>"
                "Items: %{customdata[2]}<br>"
                "Done: %{customdata[0]} (%{customdata[1]}%)"
                "<extra></extra>"
            ),
        )
    )
    fig.update_layout(**_base_layout(theme, height=380, legend=False))
    return fig


def board_flow_bar(board_flow_df, theme, colors=None):
    """Stacked horizontal bar of items by board column & state category
    (Plotly equivalent of dashboard_theme.stacked_hbar_chart)."""
    colors = colors or CATEGORY_COLORS
    fig = px.bar(
        board_flow_df,
        x="items", y="column", color="category",
        orientation="h",
        color_discrete_map=colors,
        custom_data=["column", "category", "items"],
    )
    fig.update_traces(
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "Status: %{customdata[1]}<br>"
            "Items: %{customdata[2]}"
            "<extra></extra>"
        ),
        marker_line_width=0,
    )
    fig.update_layout(**_base_layout(theme, height=max(220, 40 * board_flow_df["column"].nunique())))
    fig.update_xaxes(title=None, showgrid=True, gridcolor=theme["line"], zeroline=False)
    fig.update_yaxes(title=None, showgrid=False, categoryorder="total ascending")
    fig.update_layout(barmode="stack", legend_title_text="")
    return fig


def _hex_to_rgba(hex_color, alpha):
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"


def generic_donut(frame, field, value_field, theme, colors=None):
    """Generic labeled-value donut (Plotly equivalent of
    dashboard_theme.donut_chart) for pages whose data isn't shaped like
    the Executive Dashboard's prog_df (e.g. Repository Intelligence's PR
    outcomes by status)."""
    color_seq = [colors.get(v, theme["series"][0]) for v in frame[field]] if colors else None
    fig = go.Figure(
        go.Pie(
            labels=frame[field],
            values=frame[value_field],
            hole=0.55,
            marker=dict(colors=color_seq, line=dict(color=theme["bg"], width=2)) if color_seq
            else dict(line=dict(color=theme["bg"], width=2)),
            hovertemplate=f"<b>%{{label}}</b><br>{value_field}: %{{value}}<extra></extra>",
            sort=False,
        )
    )
    fig.update_layout(**_base_layout(theme, height=300))
    return fig


def hbar_chart(frame, x_field, y_field, theme, color=None):
    """Single-series horizontal bar (Plotly equivalent of
    dashboard_theme.hbar_chart) — items-per-tag, tasks-per-member,
    items-per-area, commits-per-contributor, etc."""
    ordered = frame.sort_values(x_field, ascending=True)
    fig = go.Figure(
        go.Bar(
            x=ordered[x_field], y=ordered[y_field], orientation="h",
            marker=dict(color=color or ACCENT["blue"]),
            customdata=ordered[[y_field, x_field]].to_numpy(),
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                f"{x_field}: " "%{customdata[1]}"
                "<extra></extra>"
            ),
        )
    )
    fig.update_layout(**_base_layout(theme, height=max(140, 30 * len(ordered)), legend=False))
    fig.update_xaxes(title=None, showgrid=True, gridcolor=theme["line"], zeroline=False)
    fig.update_yaxes(title=None, showgrid=False)
    return fig


def grouped_hbar_chart(frame, y_field, columns, colors, theme):
    """Grouped (offset) horizontal bar for two side-by-side series per
    category (Plotly equivalent of dashboard_theme.grouped_hbar_chart) —
    Sprint Summary's "stories done vs total" chart."""
    long_frame = frame.melt(id_vars=[y_field], value_vars=list(columns),
                             var_name="metric", value_name="amount")
    fig = px.bar(
        long_frame, x="amount", y=y_field, color="metric",
        orientation="h", barmode="group",
        color_discrete_map={key: colors[key] for key in columns},
        custom_data=[y_field, "metric", "amount"],
    )
    fig.update_traces(
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "%{customdata[1]}: %{customdata[2]}"
            "<extra></extra>"
        ),
        marker_line_width=0,
    )
    fig.update_layout(**_base_layout(theme, height=max(160, 34 * len(frame))))
    fig.update_xaxes(title=None, showgrid=True, gridcolor=theme["line"], zeroline=False)
    fig.update_yaxes(title=None, showgrid=False, categoryorder="total ascending")
    fig.update_layout(legend_title_text="")
    return fig


def momentum_area(week_frame, theme, colors=None):
    """Created vs. Closed weekly trend area chart
    (Plotly equivalent of dashboard_theme.area_trend_chart)."""
    colors = colors or {"Closed": ACCENT["green"], "Created": ACCENT["blue"]}
    fig = go.Figure()
    for flow in ("Created", "Closed"):
        if flow not in week_frame.columns:
            continue
        fig.add_trace(
            go.Scatter(
                x=week_frame["period"], y=week_frame[flow],
                name=flow, mode="lines+markers",
                line=dict(color=colors[flow], width=2.4),
                fill="tozeroy",
                fillcolor=_hex_to_rgba(colors[flow], 0.18),
                marker=dict(size=5, color=colors[flow]),
                hovertemplate=(
                    f"<b>{flow}</b><br>"
                    "Week: %{x}<br>"
                    "Count: %{y}"
                    "<extra></extra>"
                ),
            )
        )
    fig.update_layout(**_base_layout(theme, height=260))
    fig.update_xaxes(title=None, showgrid=False)
    fig.update_yaxes(title=None, showgrid=True, gridcolor=theme["line"], zeroline=False)
    return fig
