"""
pages/11_releases.py
----------------------
Releases page. Rendering logic moved verbatim from dashboard_app.py's
render_releases() (Phase 2 multipage restructure — structural move only,
no behavior/styling changes).
"""

import pandas as pd
import streamlit as st

from app import tr, localized_frame

st.header(tr("Releases", "الإصدارات"))
# Release plans / target dates are not part of the Azure work-item pull.
# This mirrors the workbook's "Releases" tab (release intelligence / manual input).
release_rows = [{
    "Version": "No release-plan source in current Azure pull",
    "Platform": "", "Target Date": None, "Actual Date": None,
    "Status": "", "Owner": "", "Release Notes": "Connect Azure Pipelines/Delivery Plans or a Target-Date field to populate.",
}]
st.dataframe(localized_frame(pd.DataFrame(release_rows)), width="stretch", hide_index=True)
st.info(tr(
    "Release dates are not present in the work-item pull. Add a Target Date field or connect Azure Pipelines.",
    "تواريخ الإصدارات غير موجودة في سحب عناصر العمل. أضف حقل Target Date أو اربط Azure Pipelines.",
))
