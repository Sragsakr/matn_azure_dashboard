# PRD: Repository Intelligence

Last updated: 2026-08-25 | Owner: Delivery Manager | Priority: High | Status: Approved

## Problem and objective
Delivery leadership cannot see Azure Repos engineering activity beside delivery work items. The dashboard must provide an all-history, auditable view of repositories, contributors, commits, pushes, changed files, and pull requests without replacing or mutating Azure data.

**BRD-OBJ-REPO-1:** Give delivery leadership one source for repository inventory and contributor activity. Success: every Azure Repo and every API-returned commit/push/PR is discoverable, filterable, and linked back to Azure.

## Personas / JTBD
- PM/Scrum Master: understand who changed what, where, and through which PR.
- Engineering lead: inspect repository, contributor, commit, push, reviewer, and file-level history.

## Requirements and acceptance criteria
### REQ-REPO-1 — Repository inventory
Show every Git repository in `matnsolutions/Hoteliana`, including name, default branch, size, remote/web URL, and disabled state.
- **AC-REPO-1:** Given valid Work/Code read credentials, when Repository Intelligence loads, then every repository returned by the paginated Azure API is shown.

### REQ-REPO-2 — Complete activity history
Show all API-returned commits and pushes across all repositories, with author/pusher, timestamp, message, commit IDs, push ID, repository, and Azure links.
- **AC-REPO-2:** Documented `$top`/`$skip` pagination continues until Azure returns the final short page.
- **AC-REPO-3:** Contributor totals reconcile to the loaded commit and push rows.

### REQ-REPO-3 — File-level commit detail
Show changed path, change type, object ID, original path when provided, repository, commit, author, date, and commit message.
- **AC-REPO-4:** Every loaded commit is queried for changes and every returned change appears in the file table.

### REQ-REPO-4 — Pull request intelligence
Show Active, Completed, and Abandoned PRs with title, description, creator, status, branches, dates, reviewers/votes, merge commit, and Azure link.
- **AC-REPO-5:** All three statuses are fetched with continuation support and no duplicate PR rows.

### REQ-REPO-5 — Bilingual enterprise UI
Add a Repository Intelligence navigation item and Arabic/English headings, captions, filters, summary KPIs, and tables consistent with the MATN Enterprise visual system.
- **AC-REPO-6:** The page renders in RTL Arabic and LTR English without changing underlying Azure values.

### REQ-REPO-6 — Security and resilience
Read PAT only from Streamlit secrets/environment. Never persist credentials. Show explicit loading, no-access, empty, partial-failure, and success states.
- **AC-REPO-7:** Missing/invalid Code read permission produces an actionable message and does not break existing dashboard pages.

## Decisions
| Decision | Choice | Reason |
|---|---|---|
| History | All project history | User requirement |
| Detail | All tables directly | User requirement |
| PR scope | Active + Completed + Abandoned | User requirement |
| Data authority | Azure DevOps REST API | Existing source of truth |
| Mutation | Read-only | Dashboard analytics only |

## Non-goals
No repository writes, PR approval/merge, source-code content display, diff rendering, or secret persistence.

## Risks / guardrails
All-history file expansion can be slow and API-heavy. Use continuation tokens, bounded HTTP timeouts, session caching, progress feedback, and partial-failure reporting. Existing work-item dashboard metrics must not regress.

## Delivery slices
1. Azure Git client + pagination + normalization (M).
2. Unit tests for pagination/normalization/aggregation (M).
3. Repository Intelligence UI, bilingual tables, filters and states (M).
4. Live Azure verification + browser regression of existing pages (S).

## RACI
Delivery Manager: A/UAT. Agent: R for architecture/backend/frontend/QA. Azure DevOps: source system. Repository admins: C for Code Read PAT permission.
