# BRD-lite Brief: Dashboard Visual Excellence
## Executive Summary
Transform the Streamlit delivery dashboard from functional tables into a premium, animated, dual-theme (dark/light) analytics product while keeping every Azure data source intact.

## Business Objective
BRD-OBJ-VIS-1: Make the dashboard the daily decision screen for leadership. Adoption depends on visual trust: charts over tables, glanceable KPIs, and a polished dark/light experience.

## SMART Success Metric
100% of primary sections present at least one chart; dark/light themes fully consistent (zero unreadable elements); page-level load under 3s with cached data (assumed).

## Target Users
PM/Scrum Master and engineering leadership reviewing Hoteliana delivery.

## Problem / AS-IS to TO-BE
AS-IS: plain white cards, sparse bar charts, dense unstyled tables, single light theme.
TO-BE: themed design system with dark/light toggle, gradient KPI cards, rich Altair charts (donut, area, stacked bars), styled dataframes with color-coded status columns, animated micro-interactions.

## Recommended Approach
Deep Streamlit theming + Altair chart system + dataframe styling. No separate React frontend — same data, dramatically better visuals, deployable immediately.
Alternatives rejected: full React rebuild (slow, duplicates backend), cosmetic-only CSS (tables/charts stay ugly).

## Constraints
Streamlit 1.62, Altair 6.2 only (no plotly). All current Azure data, filters, bilingual AR/EN support preserved.

## Non-Goals
No new data sources, no auth changes, no workbook changes.

## Outcome Report
feature_status: requirements_ready
requirement_trace: BRD-OBJ-VIS-1 -> candidate REQ-VIS-* (theme system, charts, tables, polish)
recommended_next_workflow: plan-feature
