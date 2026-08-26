"""
core/analysis.py
-----------------
Pure data-analysis functions extracted from dashboard_app.py (Phase 1
extraction). Zero Streamlit imports — every function here must be
independently unit-testable without importing streamlit.

Business rules preserved exactly as they were in the original
dashboard_app.py (do not "fix" or "improve" these — they are intentional):
  - STALE_DAYS = 14
  - A Task is the unassigned risk, not a Story.
  - A Story is Done only when all linked Tasks are Done (hierarchy roll-up).
"""

import datetime as dt
from collections import Counter, defaultdict

import pandas as pd

import dashboard_theme

# ---------------------------------------------------------------- constants
ORG = "matnsolutions"
PROJECT = "Hoteliana"

# Fallbacks keep older workbook caches useful. Live pulls use Azure's canonical
# state categories, so newly-added custom states are classified correctly.
DONE = {"Closed", "Done", "Resolved", "Completed"}
ACTIVE = {"Active", "In Progress", "Committed"}
TERMINAL_CATEGORIES = {"Completed", "Removed"}
DELIVERY_TYPES = ("Epic", "Feature", "User Story", "Task", "Bug",
                  "Test Case", "Test Suite", "Test Plan")
DEV_TYPES = set(DELIVERY_TYPES)
STALE_DAYS = 14
PB = "Product Backlog"  # project-only iteration label


# ---------------------------------------------------------------- normalization helpers
def _leaf(path):
    if not path:
        return ""
    return str(path).replace("\\\\", "\\").split("\\")[-1]


def _sprint(path):
    if not path:
        return PB
    p = str(path).replace("\\\\", "\\")
    return p.split("\\")[-1] if "\\" in p else PB


def _parse_date(v):
    if not v:
        return None
    if isinstance(v, dt.datetime):
        return v.date()
    if isinstance(v, dt.date):
        return v
    try:
        return dt.datetime.fromisoformat(str(v)[:10]).date()
    except ValueError:
        return None


def _category(state, category=None):
    if category:
        return category
    if state in DONE:
        return "Completed"
    if state in ACTIVE:
        return "InProgress"
    if str(state).lower() in {"removed", "deleted", "cut"}:
        return "Removed"
    return "Proposed"


def _wi(w):
    """Convert a raw Azure work item JSON to our normalized dict."""
    f = w.get("fields", {})
    state = f.get("System.State") or "Unknown"
    return {
        "id": w.get("id"),
        "title": (f.get("System.Title") or ""),
        "type": (f.get("System.WorkItemType") or "Unknown"),
        "state": state,
        "state_category": _category(state, w.get("_state_category")),
        "board_column": f.get("System.BoardColumn")
        or f.get("_board_column")
        or state,
        "board_column_done": bool(
            f.get("System.BoardColumnDone")
            or f.get("_board_column_done")
            or (f.get("System.BoardColumn") or f.get("_board_column")) in
            {"Closed", "Done", "Resolved", "Completed"}
        ),
        "board_lane": f.get("System.BoardLane") or "Default",
        "assignee": (f.get("System.AssignedTo") or {}).get("displayName")
        if isinstance(f.get("System.AssignedTo"), dict) else (f.get("System.AssignedTo") or "Unassigned"),
        "sprint": _sprint(f.get("System.IterationPath")),
        "area": _leaf(f.get("System.AreaPath") or PROJECT),
        "sp": f.get("Microsoft.VSTS.Scheduling.StoryPoints"),
        "priority": f.get("Microsoft.VSTS.Common.Priority"),
        "created": _parse_date(f.get("System.CreatedDate")),
        "changed": _parse_date(f.get("System.ChangedDate")),
        "parent": f.get("System.Parent"),
        "tags": [t.strip() for t in str(f.get("System.Tags") or "").split(";") if t.strip()],
        "url": f"https://dev.azure.com/{ORG}/{PROJECT}/_workitems/edit/{w.get('id')}",
    }


# ---------------------------------------------------------------- analysis
def is_done(i):
    return i.get("state_category") == "Completed"


def is_open(i):
    return i.get("state_category") not in TERMINAL_CATEGORIES


def is_active(i):
    return i.get("state_category") == "InProgress"


def item_metrics(items):
    total = len(items)
    done = sum(is_done(i) for i in items)
    active = sum(is_active(i) for i in items)
    return {
        "total": total,
        "done": done,
        "active": active,
        "open": sum(is_open(i) for i in items),
        # User Stories are intentionally shared across task owners; only an
        # unassigned Task is an actionable ownership risk.
        "unassigned": sum(
            i["type"] == "Task" and i["assignee"] == "Unassigned"
            for i in items
        ),
        "stale": sum(is_open(i) and i["created"] and (dt.date.today() - i["created"]).days >= STALE_DAYS for i in items),
        "done_pct": done / total if total else 0,
    }


def type_progress(items):
    """Independent % per type with child->parent roll-up when Parent ID present."""
    children = defaultdict(list)
    for i in items:
        if i["parent"] is not None:
            children[i["parent"]].append(i)
    hier = any(i["parent"] is not None for i in items)

    memo = {}
    visiting = set()

    def effective(item):
        item_id = item["id"]
        if item_id in memo:
            return memo[item_id]
        if item_id in visiting:
            # Malformed Azure hierarchy cycle: do not count it as complete.
            return False
        visiting.add(item_id)
        child_items = children.get(item_id, [])
        result = (
            all(effective(child) for child in child_items)
            if child_items
            else is_done(item)
        )
        visiting.remove(item_id)
        memo[item_id] = result
        return result

    agg = defaultdict(lambda: {"total": 0, "done": 0})
    for t in DELIVERY_TYPES:
        agg[t] = {"total": 0, "done": 0}
    for i in items:
        d = effective(i) if hier else is_done(i)
        agg[i["type"]]["total"] += 1
        agg[i["type"]]["done"] += 1 if d else 0
    out = {}
    for t, m in agg.items():
        out[t] = {"total": m["total"], "done": m["done"],
                  "pct": m["done"] / m["total"] if m["total"] else None}
    out["hierarchy_used"] = hier
    return out


def scope_metrics(items):
    """Story Done when closed AND all child Tasks done (when hierarchy present)."""
    stories = [i for i in items if i["type"] == "User Story"]
    tasks = [i for i in items if i["type"] == "Task"]
    tasks_by_parent = defaultdict(list)
    hier = any(i["parent"] is not None for i in items)
    for t in tasks:
        if t["parent"] is not None:
            tasks_by_parent[t["parent"]].append(t)
    done_story_items = []
    for story in stories:
        child_tasks = tasks_by_parent.get(story["id"])
        # A parent with children rolls up from them. A story without linked
        # children falls back to its own Azure state.
        story_done = (
            all(is_done(task) for task in child_tasks)
            if child_tasks and hier
            else is_done(story)
        )
        if story_done:
            done_story_items.append(story)

    task_done_count = sum(is_done(task) for task in tasks)
    total_sp = sum(float(story["sp"] or 0) for story in stories)
    done_sp = sum(float(story["sp"] or 0) for story in done_story_items)
    return {
        "stories": len(stories),
        "stories_done": len(done_story_items),
        "scope_pct": len(done_story_items) / len(stories) if stories else None,
        "tasks": len(tasks),
        "tasks_done": task_done_count,
        "task_pct": task_done_count / len(tasks) if tasks else None,
        "total_sp": total_sp,
        "done_sp": done_sp,
        "velocity_pct": done_sp / total_sp if total_sp else None,
        "hier": hier,
    }


def percent(value):
    """Convert a 0..1 ratio to a display-ready numeric percentage."""
    return round(value * 100, 1) if value is not None else None


def ribbon(scope, task, unassigned, stale):
    red = 0
    if (scope or 0) < 0.4:
        red += 1
    if (task or 0) < 0.4:
        red += 1
    if unassigned and unassigned >= 25:
        red += 1
    if stale and stale >= 10:
        red += 1
    if red >= 3:
        return "CRITICAL", dashboard_theme.ACCENTS["red"]
    if red >= 2:
        return "AT RISK", dashboard_theme.ACCENTS["amber"]
    return "HEALTHY", dashboard_theme.ACCENTS["green"]


def weekly_creation_closure(delivery_items):
    """Weekly created vs closed item counts from Azure dates."""
    created = Counter()
    closed = Counter()
    for item in delivery_items:
        if not item.get("created"):
            continue
        monday = item["created"] - dt.timedelta(days=item["created"].weekday())
        created[monday] += 1
        closure = item.get("changed") if is_done(item) else None
        if closure:
            closed_monday = closure - dt.timedelta(days=closure.weekday())
            closed[closed_monday] += 1
    weeks = sorted(set(created) | set(closed))
    return pd.DataFrame([
        {
            "period": week.strftime("%d %b"),
            "Created": created.get(week, 0),
            "Closed": closed.get(week, 0),
        }
        for week in weeks[-12:]
    ])


# ---------------------------------------------------------------- sprint / team / area aggregation
def sprint_summary_df(dev):
    groups = defaultdict(list)
    for i in dev:
        groups[i["sprint"]].append(i)
    rows = []
    for sprint in sorted(groups, key=lambda s: (s == PB, s)):
        m = groups[sprint]
        scg = scope_metrics(m)
        im = item_metrics(m)
        rows.append({
            "Iteration": sprint,
            "Total Dev Items": len(m),
            "User Stories": scg["stories"],
            "Stories Done": scg["stories_done"],
            "Scope Done %": percent(scg["scope_pct"]),
            "Tasks": scg["tasks"],
            "Tasks Done": scg["tasks_done"],
            "Task Done %": percent(scg["task_pct"]),
            "Active": im["active"],
            "Unassigned": im["unassigned"],
            f"Open ≥{STALE_DAYS}d": im["stale"],
            "Iteration Meaning": "No sprint assigned" if sprint == PB else "Committed iteration",
        })
    return pd.DataFrame(rows)


def team_df(dev):
    """Task-only ownership metrics; stories are shared through child Tasks."""
    tasks = [item for item in dev if item["type"] == "Task"]
    tasks_by_assignee = defaultdict(list)
    tasks_by_story = defaultdict(list)
    for task in tasks:
        tasks_by_assignee[task["assignee"]].append(task)
        if task["parent"] is not None:
            tasks_by_story[task["parent"]].append(task)

    completed_story_ids = {
        story_id
        for story_id, child_tasks in tasks_by_story.items()
        if child_tasks and all(is_done(task) for task in child_tasks)
    }

    rows = []
    ordered_groups = sorted(
        tasks_by_assignee.items(), key=lambda group: (-len(group[1]), group[0])
    )
    for assignee, owned_tasks in ordered_groups:
        done_count = sum(is_done(task) for task in owned_tasks)
        involved_story_ids = {
            task["parent"] for task in owned_tasks if task["parent"] is not None
        }
        rows.append({
            "Assignee": assignee,
            "Tasks": len(owned_tasks),
            "Tasks Done": done_count,
            "Task Completion %": percent(done_count / len(owned_tasks)),
            "Active": sum(is_active(task) for task in owned_tasks),
            "Open": sum(is_open(task) for task in owned_tasks),
            f"Open ≥{STALE_DAYS}d": item_metrics(owned_tasks)["stale"],
            "Stories Involved": len(involved_story_ids),
            "Stories Fully Done": len(involved_story_ids & completed_story_ids),
            "Areas": ", ".join(sorted({task["area"] for task in owned_tasks})),
        })
    return pd.DataFrame(rows)


def apply_global_filters(items, filters):
    """Filter normalized work-item dicts against the Phase 4 global filter
    bar's selections. Pure/testable — no Streamlit imports.

    `filters` is a dict (typically st.session_state["global_filters"]) with
    any subset of these keys (missing/empty/None means "no restriction"):
      - "sprints":   list of `sprint` values to keep (matches core's own
                     sprint normalization, i.e. _sprint()/PB values already
                     present on each item)
      - "assignees": list of `assignee` values to keep
      - "types":     list of `type` values to keep
      - "date_from": inclusive lower bound (datetime.date) on `created`
      - "date_to":   inclusive upper bound (datetime.date) on `created`

    Items with `created is None` are excluded whenever a date bound is
    active (there is nothing to compare), but are kept when no date filter
    is set — this mirrors how the rest of the app treats missing dates
    (e.g. weekly_creation_closure() simply skips them) rather than
    silently dropping otherwise-matching rows when no date filter applies.
    """
    if not filters:
        return list(items)

    sprints = filters.get("sprints") or None
    assignees = filters.get("assignees") or None
    types = filters.get("types") or None
    date_from = filters.get("date_from")
    date_to = filters.get("date_to")

    sprints_set = set(sprints) if sprints else None
    assignees_set = set(assignees) if assignees else None
    types_set = set(types) if types else None

    out = []
    for item in items:
        if sprints_set is not None and item.get("sprint") not in sprints_set:
            continue
        if assignees_set is not None and item.get("assignee") not in assignees_set:
            continue
        if types_set is not None and item.get("type") not in types_set:
            continue
        if date_from is not None or date_to is not None:
            created = item.get("created")
            if created is None:
                continue
            if date_from is not None and created < date_from:
                continue
            if date_to is not None and created > date_to:
                continue
        out.append(item)
    return out


def area_df(dev):
    rows = []
    for area in sorted({i["area"] for i in dev}, key=lambda a: -sum(1 for i in dev if i["area"] == a)):
        members = [i for i in dev if i["area"] == area]
        sc = scope_metrics(members)
        im = item_metrics(members)
        rows.append({
            "Area": area, "Total": len(members),
            "Stories": sc["stories"], "Stories Done": sc["stories_done"],
            "Scope %": percent(sc["scope_pct"]),
            "Tasks": sc["tasks"], "Tasks Done": sc["tasks_done"],
            "Task %": percent(sc["task_pct"]),
            "SP": sc["total_sp"], "Done SP": sc["done_sp"],
            "Active": im["active"], "Unassigned": im["unassigned"],
            f"Open ≥{STALE_DAYS}d": im["stale"],
        })
    return pd.DataFrame(rows)
