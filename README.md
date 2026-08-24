# Delivery Manager Dashboard — Azure DevOps mirror

A professional, re-runnable Azure DevOps delivery analytics workbook.

## What it does
1. Pulls work items from Azure DevOps (Hoteliana project) into the `Raw Data` sheet.
2. Rebuilds analytical sheets from that data on every successful pull:
   - **Executive Dashboard** — health banner, independent % per work type (Epic/Feature/User Story/Task), state breakdown, product areas, alerts, charts.
   - **Sprint Summary** — one row per real iteration (Product Backlog separately).
   - **Sprint Board** — every dev work item explorer with Azure links.
   - **Tag Analysis**, **Area Analysis**, **Active Now**, **Risks & Aging**, **Data Quality**, **Releases**.
3. Honours the real hierarchy: a User Story only counts Done when **all** its linked Tasks are Done. Feature/Epic roll up the same way.
4. Team analysis is **task-centric** — a story is rarely owned by one person; each member is credited through the Tasks they made Done.

## Requirement
- Python 3 (virtual env recommended).
- `requests` + `openpyxl` installed (see Setup).

## Setup (one time)
```bash
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
```

Create a **read-only** Azure DevOps PAT (Work Items → Read) and set it ONLY as an environment variable — never in any file:

```bash
export AZDO_PAT="your-read-only-token"
```

## Run (pull fresh Azure data + rebuild all sheets)
```bash
./.venv/bin/python3 pull_from_azure_devops.py
```

The pull script automatically rebuilds the dashboards (`build_dashboard.py`) on success.

## Web dashboard (Streamlit)
A browser dashboard that renders the same analysis live and has a **Refresh** button
that pulls fresh data from Azure DevOps.

```bash
./.venv/bin/streamlit run dashboard_app.py
```

- Open http://localhost:8501
- Set `AZDO_PAT` (as env var, or in `.streamlit/secrets.toml`) to enable live pulls.
- Without it, the app falls back to the workbook cache so the UI still opens.

### Deploy on Streamlit Community Cloud
1. Push this repo to GitHub.
2. On [Streamlit Community Cloud](https://share.streamlit.io), create a new app pointing at `dashboard_app.py`.
3. Add `AZDO_PAT` as a **secret** in the Streamlit app settings (never in the repo).
4. The "Refresh from Azure DevOps" button will pull live data on demand.

## Security notes
- The PAT is **never** stored in any file; it is read from the `AZDO_PAT` env var only.
- `.gitignore` excludes secret/token patterns and the venv.
- Rotate the PAT in Azure DevOps if it has ever leaked (e.g. shared in a chat or shell history).

## Files
- `pull_from_azure_devops.py` — Azure pull (writes `Raw Data`, then triggers build).
- `build_dashboard.py` — computes and styles all analytical sheets.
- `Delivery_Manager_Dashboard.xlsx` — the output workbook.