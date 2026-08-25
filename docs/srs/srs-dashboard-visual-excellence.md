# SRS/FRS: Dashboard Visual Excellence

Trace: BRD-OBJ-VIS-1 -> REQ-VIS-1..5 -> AC-VIS-1..5 -> SRS-VIS-1..5.

## SRS-VIS-1 Theme architecture
`apply_theme(mode, arabic)` injects CSS variables on `:root[data-theme]`: bg, surface, surface-2, line, ink, muted, brand, accents. Mode from `st.session_state["theme"]`. All component CSS uses `var(--*)` only — no hardcoded hex outside the palette block. Charts read a matching Altair theme dict (`chart_theme()`).

Palette:
- Dark: bg #0B1220, surface #111A2C, surface-2 #17233A, line #263349, ink #F1F5F9, muted #94A3B8.
- Light: bg #F4F7FB, surface #FFFFFF, surface-2 #F8FAFC, line #E5EAF2, ink #0F172A, muted #64748B.
Accents shared: blue #3B82F6, green #10B981, purple #8B5CF6, amber #F59E0B, red #EF4444, teal #14B8A6, pink #EC4899, gold #CA8A04.

## SRS-VIS-2 Chart factory
`theme_chart(chart)` applies: transparent background, domain/grid line colors from theme, label/title colors, font stack, tooltip style. Factory helpers: `donut_chart(frame, field, value)`, `hbar_chart(frame, x, y, sort_desc=True)`, `stacked_hbar_chart(frame, x, y, color)`, `area_trend_chart(frame, x, y1, y2)`. All charts get localized titles/tooltips at call sites.

## SRS-VIS-3 Table styling contract
Shared builders: `progress_column(label)` (% as bar), `state_column(labels_to_colors)`, `date_columns(*labels)`, plus per-table column order. Dataframe CSS themed via `st.DataFrame` config + global CSS for gridlines/headers.

## SRS-VIS-4 Component specs
KPI card: gradient top border (accent), icon chip, big value, delta slot optional; CSS keyframe fade-slide-in. Section headers: emoji/icon chip + title + caption. Health ribbon keeps semantic colors in both themes.

## SRS-VIS-5 Failure modes
Charts render empty-state captions when frames are empty. Theme toggle triggers natural Streamlit rerun only; no data refetch (session cache untouched).

## Verification matrix
- Unit: existing 4 tests still pass (no data changes).
- Static: py_compile all modules; grep no raw hex outside palette/theme functions (allowance: accent constants module-level).
- Browser: AR+EN × dark+light on Executive, Sprint Board, Repository Intelligence; screenshots; zero unreadable elements; charts visible.
