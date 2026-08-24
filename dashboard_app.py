"""
Delivery Manager - Streamlit Web Dashboard
------------------------------------------
Pulls live data from Azure DevOps ("Hoteliana") and renders an interactive
Delivery Manager dashboard in the browser. Refresh pulls fresh Azure data.

If the AZDO_PAT environment variable is not set, it falls back to whatever is
already in the local workbook's "Raw Data" sheet so the UI still opens without
secrets. Set AZDO_PAT (env var / secret) to enable live pulls.
"""

import os
import base64
import datetime as dt
from collections import Counter, defaultdict

import openpyxl
import pandas as pd
import requests
import streamlit as st

# ---------------------------------------------------------------- constants
ORG = "matnsolutions"
PROJECT = "Hoteliana"
API_VERSION = "7.1"
WORKBOOK = "Delivery_Manager_Dashboard.xlsx"

DONE = {"Closed", "Done", "Resolved", "Completed"}
ACTIVE = {"Active", "In Progress", "Committed"}
DEV_TYPES = {"Epic", "Feature", "User Story", "Task"}
STALE_DAYS = 14
PB = "Product Backlog"  # project-only iteration label

C = {
    "green": "#25A66A",
    "amber": "#F4B942",
    "red": "#E85D5D",
    "navy": "#17243B",
    "blue": "#2F75B5",
    "cyan": "#23A6D5",
    "purple": "#7057D9",
    "light": "#F5F7FB",
    "mut": "#64748B",
}


# ---------------------------------------------------------------- data layer
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


def _auth_header(pat):
    return {
        "Authorization": "Basic " + base64.b64encode(f":{pat}".encode()).decode(),
        "Content-Type": "application/json",
    }


def _pat():
    """PAT from Streamlit secrets first, then env var."""
    try:
        s = st.secrets.get("AZDO_PAT")
        if s:
            return s
    except Exception:
        pass
    return os.environ.get("AZDO_PAT")


def pull_from_azure():
    """Pull latest work items from Azure DevOps and return item dicts.
    Raises requests.HTTPError on failure."""
    pat = _pat()
    if not pat:
        raise ValueError("AZDO_PAT not set — cannot pull live data")

    base = f"https://dev.azure.com/{ORG}/{PROJECT}/_apis"
    hdr = _auth_header(pat)
    query = {
        "query": (
            "SELECT [System.Id] FROM WorkItems "
            f"WHERE [System.TeamProject] = '{PROJECT}' "
            "AND [System.WorkItemType] <> '' "
            "ORDER BY [System.ChangedDate] DESC"
        )
    }
    resp = requests.post(f"{base}/wit/wiql?api-version={API_VERSION}",
                         headers=hdr, json=query, timeout=30)
    resp.raise_for_status()
    ids = [item["id"] for item in resp.json().get("workItems", [])]

    fields = [
        "System.Id", "System.Title", "System.WorkItemType", "System.State",
        "System.AssignedTo", "System.IterationPath", "System.AreaPath",
        "System.Parent", "Microsoft.VSTS.Scheduling.StoryPoints",
        "Microsoft.VSTS.Common.Priority", "System.CreatedDate",
        "System.ChangedDate", "System.Tags",
    ]
    all_items = []
    for i in range(0, len(ids), 200):
        chunk = ids[i:i + 200]
        resp = requests.post(
            f"{base}/wit/workitemsbatch?api-version={API_VERSION}",
            headers=hdr, json={"ids": chunk, "fields": fields}, timeout=30)
        resp.raise_for_status()
        all_items.extend(resp.json().get("value", []))
    return all_items


def _wi(w):
    """Convert a raw Azure work item JSON to our normalized dict."""
    f = w.get("fields", {})
    return {
        "id": w.get("id"),
        "title": (f.get("System.Title") or ""),
        "type": (f.get("System.WorkItemType") or "Unknown"),
        "state": (f.get("System.State") or "Unknown"),
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


def read_workbook_items():
    """Fallback: read normalized items from the local workbook's Raw Data.
    Returns [] when the workbook is absent (e.g. on a cloud host)."""
    if not os.path.exists(WORKBOOK):
        return []
    wb = openpyxl.load_workbook(WORKBOOK, data_only=True)
    ws = wb["Raw Data"]
    hdrs = {}  # name -> index handled by positions below
    header = [c.value for c in ws[5]]
    idx = {name: i for i, name in enumerate(header) if name}
    items = []
    for row in ws.iter_rows(min_row=6, values_only=True):
        if not row or row[0] is None and (row[1] is None):
            continue
        def g(name, default=None):
            i = idx.get(name)
            return row[i] if i is not None and i < len(row) else default
        created = _parse_date(g("Created Date"))
        items.append({
            "id": g("Work Item ID"),
            "title": g("Title") or "",
            "type": g("Work Item Type") or "Unknown",
            "state": g("State") or "Unknown",
            "assignee": g("Assigned To") or "Unassigned",
            "sprint": _sprint(g("Iteration Path")),
            "area": _leaf(g("Area Path") or PROJECT),
            "sp": g("Story Points"),
            "priority": g("Priority"),
            "created": created,
            "changed": _parse_date(g("Changed Date")),
            "parent": g("Parent ID"),
            "tags": [t.strip() for t in str(g("Tags") or "").split(";") if t.strip()],
            "url": f"https://dev.azure.com/{ORG}/{PROJECT}/_workitems/edit/{g('Work Item ID')}",
        })
    return items


def load_items(force_pull=True):
    """Try live Azure pull; fall back to workbook Raw Data.
    Returns (items, mode). mode in {'live','workbook','empty'}."""
    if force_pull and _pat():
        try:
            raw = pull_from_azure()
            items = [_wi(w) for w in raw]
            return items, "live"
        except Exception as exc:
            # keep the real error visible (for debugging), fall back to cache
            st.session_state["last_pull_error"] = str(exc)
    items = read_workbook_items()
    if items:
        return items, "workbook"
    return [], "empty"


# ---------------------------------------------------------------- analysis
def is_done(i):
    return i["state"] in DONE


def item_metrics(items):
    total = len(items)
    done = sum(is_done(i) for i in items)
    active = sum(i["state"] in ACTIVE for i in items)
    return {
        "total": total,
        "done": done,
        "active": active,
        "open": total - done,
        "unassigned": sum(i["assignee"] == "Unassigned" for i in items),
        "stale": sum(not is_done(i) and i["created"] and (dt.date.today() - i["created"]).days >= STALE_DAYS for i in items),
        "done_pct": done / total if total else 0,
    }


def type_progress(items):
    """Independent % per type with child->parent roll-up when Parent ID present."""
    children = defaultdict(list)
    for i in items:
        if i["parent"] is not None:
            children[i["parent"]].append(i)
    hier = any(i["parent"] is not None for i in items)

    mem = {}
    def effective(item):
        if item["id"] in mem:
            return mem[item["id"]]
        res = is_done(item)
        for ch in children.get(item["id"], []):
            if not effective(ch):
                res = False
                break
        mem[item["id"]] = res
        return res

    agg = defaultdict(lambda: {"total": 0, "done": 0})
    for t in ("Epic", "Feature", "User Story", "Task"):
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
    done_stories = 0
    for s in stories:
        if not is_done(s):
            continue
        kids = tasks_by_parent.get(s["id"])
        if kids and hier:
            if all(is_done(k) for k in kids):
                done_stories += 1
        else:
            done_stories += 1
    return {
        "stories": len(stories),
        "stories_done": done_stories,
        "scope_pct": done_stories / len(stories) if stories else None,
        "tasks": len(tasks),
        "tasks_done": sum(is_done(t) for t in tasks),
        "task_pct": (sum(is_done(t) for t in tasks) / len(tasks)) if tasks else None,
        "hier": hier,
    }


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
        return "CRITICAL", C["red"]
    if red >= 2:
        return "AT RISK", C["amber"]
    return "HEALTHY", C["green"]


def delivery_action(items, unassigned):
    open_count = sum(not is_done(i) for i in items)
    if unassigned >= 25 and open_count:
        return f"{unassigned} items are unassigned — assign owners first"
    scope = scope_metrics(items)
    if items and scope["scope_pct"] == 0 and open_count:
        return "Scope stalled — no fully-complete story yet"
    if any(i["type"] == "User Story" and i["sp"] is None for i in items):
        return "Add Story Points to unestimated stories"
    return "Delivery on track"


# ============================================================ UI HELPERS
def apply_theme():
    st.markdown(
        """
        <style>
        .block-container { padding-top: 1.2rem; }
        div[data-testid="stSidebar"] { background: #F4F6FB; }
        div[data-testid="stMetric"] {
            background: white; border: 1px solid #E2E8F0; border-radius: 12px;
            padding: 12px 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }
        div[data-testid="stMetric"] label { color: #64748B; font-weight:600; }
        div[data-testid="stMetric"] [data-testid="stMetricValue"] { font-weight:700; }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------- rendering
st.set_page_config(page_title="Delivery Manager — Hoteliana", layout="wide",
                   initial_sidebar_state="expanded")

st.title("🚀 Delivery Manager — Hoteliana")
st.caption("Azure DevOps delivery control tower. Smart task-centric scope, child→parent roll-up.")

apply_theme()

user_missing = not _pat()
if user_missing:
    st.sidebar.warning("AZDO_PAT not set — showing data from the local workbook. "
                       "Set it (env var/secret) to enable live Azure pulls.")

refresh = st.sidebar.button("🔄 Refresh from Azure DevOps", type="primary")

data_mode = "workbook"
items = []
if refresh and _pat():
    with st.spinner("Pulling from Azure DevOps..."):
        try:
            items, data_mode = load_items(force_pull=True)
            st.sidebar.success(f"Pulled {len(items)} items from Azure (live).")
        except Exception as exc:
            st.sidebar.error(f"Pull failed: {exc}")
if not items:
    # Auto-pull on first load when a secret exists but no local workbook does
    # (typical on a cloud host): otherwise the app would show "no data".
    auto = bool(_pat()) and not os.path.exists(WORKBOOK)
    items, data_mode = load_items(force_pull=bool(refresh and _pat()) or auto)

dev = [i for i in items if i["type"] in DEV_TYPES]

if not dev:
    st.sidebar.warning("No data loaded.")
    st.error("No dev work items found.")
    missing_pat = not _pat()
    if missing_pat:
        st.info("`AZDO_PAT` secret is not set. Set it in the hosting platform's secrets "
                "(Streamlit Cloud → Settings → Secrets) or as the GitHub Actions secret, "
                "then press **Refresh from Azure DevOps**.")
    # Show the underlying pull failure so it isn't a silent "nothing on screen"
    if st.session_state.get("last_pull_error"):
        st.warning(f"Last Azure pull failed: {st.session_state['last_pull_error']}")
    st.info("If you are self-hosting without a workbook, the app needs live Azure access "
            "via AZDO_PAT to load any data.")
    st.stop()

st.sidebar.metric("Data source", data_mode)
st.sidebar.metric("Dev scope items", len(dev))
st.sidebar.metric("All items", len(items))

# Precompute shared analysis once (executive-only metrics used by sidebar).
all_m = item_metrics(dev)
scope = scope_metrics([i for i in dev if i["sprint"] != PB])
verdict, color = ribbon(scope["scope_pct"], scope["task_pct"], all_m["unassigned"], all_m["stale"])
prog = type_progress(dev)

# ---- Sidebar navigation: one section per tab, mirroring the Excel workbook
PAGES = [
    "Executive Dashboard",
    "Sprint Summary",
    "Sprint Board",
    "Tag Analysis",
    "Team Analysis",
    "Area Analysis",
    "Active Now",
    "Risks & Aging",
    "Data Quality",
    "Releases",
    "Raw Data",
]
page = st.sidebar.radio("📊 Sections", PAGES)

st.caption(f"Refresh pulls directly from {ORG}/{PROJECT}." if data_mode == "live"
           else "Showing workbook cache. Set AZDO_PAT + Refresh for live data.")
st.divider()


# ============================================================ EXECUTIVE
def render_executive():
    st.header("🚀 Executive Dashboard")
    st.markdown(
        f"<div style='background:{color};color:white;padding:14px 20px;border-radius:10px;"
        f"font-size:20px;font-weight:700'>{verdict} — {delivery_action(dev, all_m['unassigned'])}</div>",
        unsafe_allow_html=True,
    )

    if not dev:
        st.warning("No work items to chart yet.")
        return

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Story Scope Done", f"{scope['scope_pct'] or 0:.0%}")
    c2.metric("Task Completion", f"{scope['task_pct'] or 0:.0%}")
    c3.metric("Active Now", all_m["active"])
    c4.metric("Unassigned", all_m["unassigned"])
    c5.metric("Product Backlog", sum(1 for i in dev if i["sprint"] == PB))
    c6.metric("Stale (≥14d)", all_m["stale"])

    st.subheader("Completion by work type")
    prog_df = pd.DataFrame([
        {"Work Type": t, "Total": m["total"], "Done": m["done"], "Completion %": m["pct"] or 0}
        for t, m in [("Epic", prog["Epic"]), ("Feature", prog["Feature"]),
                     ("User Story", prog["User Story"]), ("Task", prog["Task"])]
    ])
    st.dataframe(prog_df, use_container_width=True, hide_index=True)
    hier_txt = "child→parent roll-up active ✅" if prog["hierarchy_used"] else "own-state (add Parent ID for roll-up)"
    st.caption(f"Hierarchy: {hier_txt}")

    st.subheader("Work by state")
    state_df = pd.DataFrame([
        {"State": s, "Items": n} for s, n in Counter(i["state"] for i in dev).most_common()
    ])
    col_l, col_r = st.columns([1, 1])
    with col_l:
        st.bar_chart(state_df.set_index("State"))
    with col_r:
        st.dataframe(state_df, use_container_width=True, hide_index=True)


# ============================================================ SPRINT SUMMARY
def sprint_summary_df():
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
            "Scope Done %": scg["scope_pct"] or 0,
            "Tasks": scg["tasks"],
            "Tasks Done": scg["tasks_done"],
            "Task Done %": scg["task_pct"] or 0,
            "Active": im["active"],
            "Unassigned": im["unassigned"],
            f"Open ≥{STALE_DAYS}d": im["stale"],
            "Iteration Meaning": "No sprint assigned" if sprint == PB else "Committed iteration",
        })
    return pd.DataFrame(rows)


def render_sprint_summary():
    st.header("📅 Sprint Summary")
    st.caption("One row per real Azure iteration; Product Backlog shown separately.")
    st.dataframe(sprint_summary_df(), use_container_width=True, hide_index=True)


# ============================================================ SPRINT BOARD
def render_sprint_board():
    st.header("📋 Sprint Board")
    st.caption("Every dev work item grouped by iteration and assignee, with Azure links.")
    df = pd.DataFrame([{
        "Iteration": i["sprint"], "ID": i["id"], "Title": i["title"], "Type": i["type"],
        "State": i["state"], "Assignee": i["assignee"], "Area": i["area"],
        "Tags": "; ".join(i["tags"]) or "Untagged", "SP": i["sp"],
        "Priority": i["priority"],
        "Created": i["created"], "Changed": i["changed"],
        "Age (d)": (dt.date.today() - i["created"]).days if i["created"] else None,
        "Parent ID": i["parent"], "Azure Link": i["url"],
    } for i in dev])
    st.dataframe(df, use_container_width=True, hide_index=True, height=500)


# ============================================================ TAG ANALYSIS
def render_tag_analysis():
    st.header("🏷️ Tag Analysis")
    st.caption("Multi-tag items counted once per tag; Untagged shown explicitly.")
    tag_map = defaultdict(list)
    for i in dev:
        for t in (i["tags"] or ["Untagged"]):
            tag_map[t].append(i)
    rows = []
    for tag, members in sorted(tag_map.items(), key=lambda x: -len(x[1])):
        sc = scope_metrics(members)
        im = item_metrics(members)
        rows.append({
            "Tag": tag, "Items": len(members),
            "Stories": sc["stories"], "Stories Done": sc["stories_done"],
            "Scope %": sc["scope_pct"] or 0,
            "Tasks": sc["tasks"], "Tasks Done": sc["tasks_done"],
            "Task %": sc["task_pct"] or 0,
            "Active": im["active"], "Unassigned": im["unassigned"],
            f"Open ≥{STALE_DAYS}d": im["stale"],
            "Areas": ", ".join(sorted({i["area"] for i in members})),
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


# ============================================================ TEAM ANALYSIS
def team_df():
    assignee_of_story = defaultdict(set)
    story_by_id = {i["id"]: i for i in dev if i["type"] == "User Story"}
    for i in dev:
        if i["type"] == "Task" and i["parent"] in story_by_id:
            assignee_of_story[i["parent"]].add(i["assignee"])
    groups = defaultdict(list)
    for i in dev:
        groups[i["assignee"]].append(i)
    rows = []
    for assignee, members in sorted(groups.items(), key=lambda x: -sum(1 for i in x[1] if i["type"] == "Task")):
        tasks = [i for i in members if i["type"] == "Task"]
        done_t = sum(is_done(t) for t in tasks)
        involved = {i["id"] for i in members if i["type"] == "User Story"}
        for sid, asg in assignee_of_story.items():
            if assignee in asg:
                involved.add(sid)
        full = {sid for sid in involved if story_by_id.get(sid) and is_done(story_by_id[sid])}
        rows.append({
            "Assignee": assignee,
            "Tasks": len(tasks), "Tasks Done": done_t,
            "Task %": done_t / len(tasks) if tasks else None,
            "Active": sum(i["state"] in ACTIVE for i in members),
            "Open": sum(not is_done(i) for i in members),
            f"Open ≥{STALE_DAYS}d": item_metrics(members)["stale"],
            "Stories Involved": len(involved), "Stories Fully Done": len(full),
            "Areas": ", ".join(sorted({i["area"] for i in members})),
        })
    return pd.DataFrame(rows)


def render_team_analysis():
    st.header("👥 Team Delivery (task-centric)")
    st.caption("A story is rarely owned by one person; members are credited through Tasks they completed.")
    st.dataframe(team_df(), use_container_width=True, hide_index=True)


# ============================================================ AREA ANALYSIS
def area_df():
    rows = []
    for area in sorted({i["area"] for i in dev}, key=lambda a: -sum(1 for i in dev if i["area"] == a)):
        members = [i for i in dev if i["area"] == area]
        sc = scope_metrics(members)
        im = item_metrics(members)
        rows.append({
            "Area": area, "Total": len(members),
            "Stories": sc["stories"], "Stories Done": sc["stories_done"],
            "Scope %": sc["scope_pct"] or 0,
            "Tasks": sc["tasks"], "Tasks Done": sc["tasks_done"],
            "Task %": sc["task_pct"] or 0,
            "SP": sc["total_sp"], "Done SP": sc["done_sp"],
            "Active": im["active"], "Unassigned": im["unassigned"],
            f"Open ≥{STALE_DAYS}d": im["stale"],
        })
    return pd.DataFrame(rows)


def render_area_analysis():
    st.header("🗂️ Area Analysis")
    st.caption("Scope & execution split across Azure Area Paths.")
    st.dataframe(area_df(), use_container_width=True, hide_index=True)


# ============================================================ ACTIVE NOW
def render_active_now():
    st.header("⚡ Active & Open Work — Touch This Now")
    st.caption("Everything open, ordered by risk (unassigned > active > aging).")
    open_items = [i for i in dev if not is_done(i)]
    def priority(item):
        if item["assignee"] == "Unassigned":
            return "Critical"
        if item["state"] in ACTIVE:
            return "Doing"
        if item["created"] and (dt.date.today() - item["created"]).days >= STALE_DAYS:
            return "Aging"
        if item["type"] == "User Story":
            return "Scope"
        return "High"
    rows = []
    for i in sorted(open_items, key=lambda x: priority(x)):
        rows.append({
            "Priority": priority(i), "ID": i["id"], "Title": i["title"], "Type": i["type"],
            "State": i["state"], "Assignee": i["assignee"], "Sprint": i["sprint"],
            "Area": i["area"], "Tags": "; ".join(i["tags"]) or "Untagged",
            "Age (d)": (dt.date.today() - i["created"]).days if i["created"] else None,
            "Azure Link": i["url"],
        })
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True, height=500)
    else:
        st.success("No open work — all done!")


# ============================================================ RISKS & AGING
def render_risks():
    st.header("⚠️ Risks & Aging")
    st.caption("Open work ranked by age; age = days since Created Date.")
    open_items = [i for i in dev if not is_done(i)]
    ordered = sorted(open_items, key=lambda i: (i["assignee"] != "Unassigned",
                                                -(i["created"] and (dt.date.today() - i["created"]).days or -1),
                                                i["id"]))
    rows = []
    for i in ordered:
        risk = []
        if i["assignee"] == "Unassigned":
            risk.append("Unassigned")
        if i["sprint"] == PB:
            risk.append("No sprint")
        if i["created"] and (dt.date.today() - i["created"]).days >= STALE_DAYS:
            risk.append(f"Age ≥{STALE_DAYS}d")
        if i["type"] == "User Story" and i["sp"] is None:
            risk.append("No SP")
        age = (dt.date.today() - i["created"]).days if i["created"] else None
        rows.append({
            "Risk": ", ".join(risk) or "Monitor", "Age": age, "ID": i["id"], "Title": i["title"],
            "Type": i["type"], "State": i["state"], "Assignee": i["assignee"],
            "Sprint": i["sprint"], "Area": i["area"], "Tags": "; ".join(i["tags"]) or "Untagged",
            "Azure Link": i["url"],
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True, height=500)


# ============================================================ DATA QUALITY
def render_data_quality():
    st.header("🔍 Data Quality & Trust")
    rows = [
        ("All Azure work items imported", len(items), "Exact"),
        ("Dev scope (Epic+Feature+Story+Task)", len(dev), "Exact"),
        ("Test artifacts retained in Raw Data", len(items) - len(dev), "Excluded from delivery scope"),
        ("Items in real sprint paths", sum(1 for i in dev if i["sprint"] != PB), "Exact"),
        ("Product Backlog (no sprint)", sum(1 for i in dev if i["sprint"] == PB), "Exact"),
        ("Items without assignee", all_m["unassigned"], "Exact"),
        ("Items without tags", sum(1 for i in dev if not i["tags"]), "Exact"),
        ("User Stories without Story Points", sum(1 for i in dev if i["type"] == "User Story" and i["sp"] is None), "Exact"),
        ("Items with Parent ID", sum(1 for i in dev if i["parent"] is not None), "Enables hierarchy roll-up"),
    ]
    st.dataframe(pd.DataFrame(rows, columns=["Check", "Count", "Interpretation"]),
                 use_container_width=True, hide_index=True)


# ============================================================ RELEASES
def render_releases():
    st.header("🚦 Releases")
    # Release plans / target dates are not part of the Azure work-item pull.
    # This mirrors the workbook's "Releases" tab (release intelligence / manual input).
    release_rows = [{
        "Version": "No release-plan source in current Azure pull",
        "Platform": "", "Target Date": None, "Actual Date": None,
        "Status": "", "Owner": "", "Release Notes": "Connect Azure Pipelines/Delivery Plans or a Target-Date field to populate.",
    }]
    st.dataframe(pd.DataFrame(release_rows), use_container_width=True, hide_index=True)
    st.info("Release dates are not present in the work-item API pull. "
            "Add a dedicated Azure field (Target Date) or connect Pipelines to auto-populate this tab.")


# ============================================================ RAW DATA
def render_raw_data():
    st.header("📦 Raw Data — all Azure work items")
    st.caption("All 546 imported items (incl. test artifacts), exactly as pulled from Azure DevOps.")
    all_items = items  # already loaded by the app
    df = pd.DataFrame([{
        "Work Item ID": i["id"], "Title": i["title"], "Work Item Type": i["type"],
        "State": i["state"], "Assigned To": i["assignee"], "Iteration Path": i["sprint"],
        "Area Path": i["area"], "Story Points": i["sp"], "Priority": i["priority"],
        "Created Date": i["created"], "Changed Date": i["changed"],
        "Tags": "; ".join(i["tags"]) or "Untagged", "Parent ID": i["parent"], "Azure Link": i["url"],
    } for i in all_items])
    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True, height=520)
    else:
        st.info("No raw data loaded. Press Refresh (requires AZDO_PAT) or supply the workbook.")


# ---- dispatch
if page == "Executive Dashboard":
    render_executive()
elif page == "Sprint Summary":
    render_sprint_summary()
elif page == "Sprint Board":
    render_sprint_board()
elif page == "Tag Analysis":
    render_tag_analysis()
elif page == "Team Analysis":
    render_team_analysis()
elif page == "Area Analysis":
    render_area_analysis()
elif page == "Active Now":
    render_active_now()
elif page == "Risks & Aging":
    render_risks()
elif page == "Data Quality":
    render_data_quality()
elif page == "Releases":
    render_releases()
elif page == "Raw Data":
    render_raw_data()