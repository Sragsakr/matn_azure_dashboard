# PRD: Dashboard Visual Excellence

Last updated: 2026-08-25 | Owner: Delivery Manager | Priority: High | Status: Approved

## Objective
BRD-OBJ-VIS-1 -> REQ-VIS-1..5. Make the dashboard premium, animated, and dual-theme without touching Azure data logic.

## Requirements
### REQ-VIS-1 Theme system with dark/light toggle
Sidebar segmented control "Theme" (Dark/Light) persisted in session state. CSS custom properties drive every surface.
- AC-VIS-1: Toggle switches all surfaces (sidebar, cards, tables, charts, header) with no unreadable text in either mode.

### REQ-VIS-2 Rich chart system (Altair)
Replace st.bar_chart defaults with configured Altair charts:
- Executive: donut of work-type totals, horizontal stacked state-by-category bars, area trend of items created vs closed by week.
- Sprint Summary: grouped bar of stories done vs total per iteration.
- Tag/Area/Team: horizontal bars sorted by completion %.
- Repository Intelligence: commits-per-contributor bars, PR status donut.
- AC-VIS-2: Every primary section renders at least one interactive Altair chart with themed colors and tooltips in AR/EN.

### REQ-VIS-3 Styled dataframes
Column config for all tables: progress bars for % columns, pill-like categorical coloring for State/Status, date formatting, hidden ID noise columns where possible.
- AC-VIS-3: Percentage columns render as progress bars; state/status cells are color-coded consistently in both themes.

### REQ-VIS-4 Premium KPI cards & layout polish
Gradient-accent KPI cards, animated count-up feel via CSS, section headers with icon chips, consistent spacing, hover elevation, skeleton/spinner states already present.
- AC-VIS-4: Executive page shows gradient KPI row; hover elevates cards; both themes keep contrast ratios readable.

### REQ-VIS-5 Preserve data & bilingual behavior
No change to data fetching, filters, or Azure values. tr() localization applies to chart titles/tooltips too.
- AC-VIS-5: Existing unit tests pass; browser check passes in AR and EN, dark and light.

## Decisions
| Decision | Choice | Reason |
|---|---|---|
| Frontend | Deep Streamlit + Altair | Best value/speed balance |
| Theme toggle | Session-state segmented control | Instant, no rerun complexity |
| Charts | Altair only | Installed; themable via config |

## Non-goals
React rebuild, plotly dependency, new data sources.

## Risks
Altair default fonts/colors leak in dark mode — mitigate with charted theme function used everywhere.
