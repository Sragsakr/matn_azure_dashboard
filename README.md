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

## Deploy on Hugging Face Spaces (recommended free web hosting)
Hugging Face Spaces hosts Streamlit apps free and keeps them running (does not sleep),
so your **Refresh-from-Azure button works live**. Sync this repo into a Space:

1. Create a **read-only** Azure DevOps PAT (Work Items → Read).
2. Go to [huggingface.co/spaces](https://huggingface.co/spaces) → **Create new Space**.
3. SDK: **Streamlit**. (Optionally link your GitHub repo, or upload these files.)
4. Before running, the Space needs the secret: in the Space **Settings → Variables and secrets**,
   add key `AZDO_PAT` = your PAT.
5. The app auto-loads `dashboard_app.py` and the in-app **"Refresh from Azure DevOps"**
   button pulls live data on demand.

> The PAT is stored only as a Space secret — never in the repo.
> No GitHub Pages is used; this is a live server-backed Streamlit app.

## Deploy on Render (alternative web hosting)
Render also runs the Streamlit app as a live public web service from this repo —
no GitHub Pages involved. It picks up the included `render.yaml` automatically.

1. Create a **read-only** Azure DevOps PAT (Work Items → Read).
2. On [render.com](https://render.com) sign up with GitHub, then **New + → Web Service**.
3. Pick the `matn_azure_dashboard` repo. Render auto-detects `render.yaml`.
4. In **Environment**, add key `AZDO_PAT` = your PAT (a secret, never committed).
5. Click **Create Web Service** — it builds and serves the dashboard publicly.
6. The in-app **"Refresh from Azure DevOps"** button pulls live data on demand.

> Note: `render.yaml` keeps the PAT as a Render secret (`sync: false`); it is
> never stored in the repository.

## Security notes
- The PAT is **never** stored in any file; it is read from the `AZDO_PAT` env var only.
- `.gitignore` excludes secret/token patterns and the venv.
- Rotate the PAT in Azure DevOps if it has ever leaked (e.g. shared in a chat or shell history).

## Files
- `pull_from_azure_devops.py` — Azure pull (writes `Raw Data`, then triggers build).
- `build_dashboard.py` — computes and styles all analytical sheets.
- `Delivery_Manager_Dashboard.xlsx` — the output workbook.