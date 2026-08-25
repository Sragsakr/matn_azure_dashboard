# Repository Intelligence Walkthrough

Date: 2026-08-25

## Evidence
- Unit: `python -m unittest tests/test_azure_repo_activity.py` — 4 passing scenarios (multi-page history, normalization, partial endpoint failure, contributor reconciliation).
- Static: `py_compile` for repository module and Streamlit app; `git diff --check` clean.
- Live Azure Code Read: 5 repositories, 102 commits, 127 pushes, 11 pull requests, 2,361 changed-file rows, 9 contributors, 0 collection failures.
- Live repositories: Hoteliana-Dashboard, Hoteliana, Hoteliana-Backend, Supplier-Dashboard, Agent-Dashboard.
- Browser: Arabic Repository Intelligence page rendered all six KPI counts, filters, repository/contributor/commit/push/PR/change tables with no Streamlit traceback.
- Security: PAT supplied only as process environment for verification; secret scan found no token in workspace files.

## Requirement trace
- AC-REPO-1/2 -> live counts + pagination test.
- AC-REPO-3 -> contributor reconciliation test and live contributor count.
- AC-REPO-4 -> 2,361 live changed-file rows.
- AC-REPO-5 -> all-status PR query; live project currently returns 11 completed PRs.
- AC-REPO-6 -> Arabic page browser evidence; English navigation/labels implemented through existing language control.
- AC-REPO-7 -> partial endpoint failure unit test and missing-PAT UI state.
