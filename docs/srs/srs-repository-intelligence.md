# SRS/FRS: Repository Intelligence

## Trace
BRD-OBJ-REPO-1 -> REQ-REPO-1..6 -> AC-REPO-1..7 -> SRS-REPO-1..6.

## Architecture
- New pure module `azure_repo_activity.py` owns Azure Git REST pagination, normalization, aggregation, and failure records.
- `app.py` and `pages/10_repository_intelligence.py` own Streamlit state, bilingual presentation, filters, and progress/error states.
- Dependency direction: UI -> repo activity module -> `requests.Session` -> Azure REST API.
- No storage migration. Results are held in Streamlit session state only.

## Contracts
### SRS-REPO-1 Authentication
Input: organization, project, PAT. Header uses Basic `:<PAT>`. PAT is never logged or returned.

### SRS-REPO-2 Pagination
Azure Git collection calls use the documented `$top=100`/`$skip` parameters; commit-change calls use `top=100`/`skip`. Paging stops only on the final short page. Timeout: 30 seconds/request.

### SRS-REPO-3 Collections
- `git/repositories`
- Per repo: `commits`, `pushes`, `pullrequests?searchCriteria.status=all`
- Per commit: `commits/{commitId}/changes`
Output dataset keys: `repositories`, `commits`, `pushes`, `pull_requests`, `changes`, `failures`.

### SRS-REPO-4 Normalized rows
Rows contain repository identifiers/names, identity display name/email where supplied, UTC date strings, IDs, messages/descriptions, branch names, reviewers/votes, and Azure web links. Missing optional Azure fields become empty strings/None, not invented values.

### SRS-REPO-5 UI
Repository Intelligence page renders KPI cards, repository inventory, contributor summary, commits, pushes, PRs, and changed files. Repository/contributor/status filters apply to tables. Arabic mode localizes UI labels only; Azure content remains exact.

### SRS-REPO-6 Failure behavior
A repository endpoint failure is recorded in `failures` and remaining repositories continue. Authentication/repository-list failure is fatal and displayed without affecting work-item pages.

## NFRs
- Read-only and secret-safe.
- Pagination completeness over arbitrary page count.
- No duplicate rows by `(repo_id, commit_id)`, `(repo_id, push_id)`, `(repo_id, pull_request_id)`, `(repo_id, commit_id, change_index)`.
- Session cache prevents refetch on ordinary Streamlit reruns; explicit refresh invalidates it.
- UI shows progress because all-history file expansion may take minutes.

## Verification matrix
- AC-1/2/5: unit tests with multi-page fake responses and continuation headers.
- AC-3: aggregation unit tests.
- AC-4: change normalization tests.
- AC-6: browser test Arabic + English.
- AC-7: missing PAT and endpoint failure tests/manual UI verification.
- Regression: `py_compile`, workbook build, Streamlit health, all existing navigation pages.

## ADR
Use direct Azure REST reads rather than cloning repositories. This preserves read-only behavior, avoids disk growth/source-content exposure, and provides authoritative PR/push metadata. All-history is fetched on demand and cached per Streamlit session.
