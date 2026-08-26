"""streamlit-aggrid wrapper for rendering list-of-dicts / DataFrame data.

Reusable across any page: sortable/filterable columns by default, the
first column pinned for wide tables, built-in CSV export (st_aggrid's own
download-button toolbar), and conditional row background for stale items
(rows where an item has been open >= core.analysis.STALE_DAYS get a
subtle red tint) — reusing core.analysis's existing staleness definition
instead of reinventing it.

Nothing here calls a Streamlit widget at import time, so it is safe to
import from app.py and from any page module.
"""

import datetime as dt

import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode

from core.analysis import STALE_DAYS, is_open

# Row-level JS predicate mirroring core.analysis.item_metrics()'s "stale"
# rule: an open item whose `created` date is STALE_DAYS or more in the
# past. The grid only ever sees plain JSON cell values (dates as ISO
# strings), so the same >= STALE_DAYS comparison is re-expressed in JS
# here rather than trying to ship a Python closure into the browser.
_STALE_ROW_STYLE_JS = JsCode(
    f"""
    function(params) {{
        if (!params.data) {{ return null; }}
        var isOpen = params.data.__is_open__;
        var days = params.data.__age_days__;
        if (isOpen && days !== null && days !== undefined && days >= {STALE_DAYS}) {{
            return {{ backgroundColor: 'rgba(185, 28, 28, 0.14)' }};
        }}
        return null;
    }}
    """
)


def _with_staleness_columns(frame, items):
    """Attach hidden __is_open__ / __age_days__ helper columns to `frame`
    so the grid's row-style JS can flag stale rows, using the exact same
    is_open()/STALE_DAYS logic as core.analysis.item_metrics — not a
    reimplementation. `items` must be the same normalized work-item dicts
    (with `created`/`state_category`) the frame's rows were derived from,
    in the same row order.
    """
    if items is None or len(items) != len(frame):
        return frame
    today = dt.date.today()
    frame = frame.copy()
    frame["__is_open__"] = [bool(is_open(i)) for i in items]
    frame["__age_days__"] = [
        (today - i["created"]).days if i.get("created") else None for i in items
    ]
    return frame


def render_grid(
    data,
    items=None,
    pin_first_column=True,
    height=420,
    key=None,
    selectable=False,
    selection_mode="single",
):
    """Render `data` (a DataFrame or list-of-dicts) as an interactive,
    sortable/filterable AgGrid with CSV export.

    - `items`: optional list of normalized work-item dicts (see
      core.analysis._wi / read_workbook_items) aligned 1:1 with `data`'s
      rows. When given, rows for items stale >= STALE_DAYS get a subtle
      red-tinted background using core.analysis's own staleness rule.
    - `pin_first_column`: pins the first column so wide tables stay
      navigable (headers/IDs stay visible while scrolling horizontally).
    - `selectable`: when True, enables row selection (click a row to select
      it) and switches update_mode to SELECTION_CHANGED so the returned
      grid_response.selected_rows reflects clicks without a full rerun lag.
      Used by pages/5_team_analysis.py for Phase 4 click-to-filter (select
      a member's row -> filter the rest of the app to that assignee).
    - CSV export is built in via st_aggrid's own toolbar download button.

    Returns the underlying AgGrid return object (grid_response), in case a
    caller wants filtered/selected rows later.
    """
    frame = data if isinstance(data, pd.DataFrame) else pd.DataFrame(data)
    display_columns = list(frame.columns)
    frame = _with_staleness_columns(frame, items)

    builder = GridOptionsBuilder.from_dataframe(frame)
    builder.configure_default_column(
        sortable=True, filter=True, resizable=True, floatingFilter=False,
    )
    if display_columns:
        builder.configure_column(display_columns[0], pinned="left" if pin_first_column else None)
    # Hide the staleness helper columns from the rendered grid; they only
    # exist to drive getRowStyle.
    for helper_col in ("__is_open__", "__age_days__"):
        if helper_col in frame.columns:
            builder.configure_column(helper_col, hide=True)

    if selectable:
        builder.configure_selection(
            selection_mode=selection_mode,
            use_checkbox=False,
            suppressRowClickSelection=False,
        )

    builder.configure_grid_options(
        getRowStyle=_STALE_ROW_STYLE_JS,
        suppressColumnVirtualisation=True,
    )
    grid_options = builder.build()

    return AgGrid(
        frame,
        gridOptions=grid_options,
        height=height,
        update_mode=GridUpdateMode.SELECTION_CHANGED if selectable else GridUpdateMode.NO_UPDATE,
        allow_unsafe_jscode=True,
        show_toolbar=True,
        show_download_button=True,
        theme="streamlit",
        key=key,
    )
