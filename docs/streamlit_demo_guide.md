# Streamlit Demo Guide

How to launch and use the **scenario explorer** — a read-only
Streamlit app sitting on top of the generated outputs.

The app is for **exploration and review**, not editing. Every number
you see is reproducible from the upstream YAMLs and Python pipelines;
the app reads from the DuckDB review database (with CSV fallback).

## Launch

```bash
uv run demo
```

This wraps `streamlit run app/streamlit_app.py`. Opens a browser tab
at `http://localhost:8501` automatically.

## Prerequisites

The app reads from `outputs/database/ai_economy.duckdb`, which is built
from the upstream pipeline outputs. For a clean state, run:

```bash
uv run historical    # produces historical_*.csv outputs
uv run supply        # produces supply_*.csv outputs
uv run allocation    # produces allocation_*.csv outputs
uv run database      # builds the DuckDB review database
uv run demo          # launches the Streamlit app
```

If the database is missing, the app falls back to the per-file CSVs
under `outputs/tables/` — slightly slower but functionally equivalent.
The Model Overview page surfaces a status banner indicating which
data source is in use.

## Pages

The sidebar shows nine pages, numbered for the recommended reading
order. Each page is independently runnable; deep-link to the most
relevant page for your review.

### 1. Model Overview
Component status cards (BUILT / NEXT / FUTURE), the six headline
numbers, the architecture diagram, and the central caution. Read
this first if you've never seen the model before.

### 2. Scenario Matrix
All 16 combined scenarios sorted by 2040 largest_frontier_run_flop.
Slow / base / fast envelope rows tagged. Sortable, filterable, CSV
download. Bar chart of 2040 largest_run by combined scenario.

### 3. Supply Capacity
Four side-by-side charts (usable compute, H100-eq stock, capex
required, binding-constraint heatmap) with a year-range slider in
the sidebar. Summary table + expandable annual + capex tables. Three
CSV downloads.

### 4. Allocation Layer
Pick one (supply, allocation) combo via the sidebar. See the bucket
stacked-area chart for that pair plus four share-over-time charts
(training / inference / AI R&D / frontier-run share of total).
Bucket-detail table + CSV download.

### 5. Largest Frontier Run
The headline forward output. Sidebar offers presets (slow / base /
fast envelope, all 16, base supply × all allocations, etc.) and a
multi-select for custom combinations. Optional historical Rule A
2018+ overlay shows the gap. 2040 ranking + share charts side by
side; detail table.

### 6. Effective-Compute Handoff
**The page designed for downstream consumers.** Milestone-year
envelope cards (slow / base / fast at 2024, 2030, 2040), envelope
chart, base-case bucket-totals chart, wide-format handoff table
(year + slow/base/fast largest_run + base-case bucket totals), and
two CSV download buttons.

### 7. Assumptions
Source / confidence audit table with sidebar filters (component,
confidence). Allocation share assumptions interpolated by year.
Both downloadable.

### 8. Source Provenance *(optional)*
Aggregate counts by component × confidence and by source, plus
full provenance table. For external-reviewer-style audits.

### 9. Run Manifest *(optional)*
Latest validation-run metadata: timestamp, git commit, test
pass/fail, total checks. Database build manifest with table/view
counts.

## What the demo is NOT for

- **Don't edit assumptions in the app.** It's read-only by design.
  Edit the upstream YAMLs (`data/assumptions/*.yaml`) and rerun the
  pipelines.
- **Don't trust app numbers if upstream artifacts are stale.** If
  you've changed a YAML or pipeline since the last DuckDB build,
  rebuild it: `uv run database`.
- **Don't treat this as a forecast.** Same caveat as the workbook:
  raw FLOP isn't effective FLOP; allocation parameters are
  `confidence: medium` from scope defaults; the historical trend
  is descriptive, not predictive.

## Source-of-truth hierarchy (reminder)

```
1. Raw data and public sources
2. YAML assumptions and scenario files       ← edit here
3. Python model logic
4. Processed CSV / Parquet outputs           ← regenerate via uv run *
5. DuckDB review database                    ← rebuild via uv run database
6. Excel review workbook                     ← rebuild via uv run workbook
7. Streamlit demo                            ← rebuild = it picks up automatically
8. Markdown findings and charts              ← per-component
```

Lower tiers are *generated* from higher tiers. If they disagree,
trust higher.

## Customizing further (out of scope for the first demo)

The first demo is intentionally read-only. Future versions could
add:

- Interactive sliders for allocation parameters (training_share,
  largest_run_concentration, etc.) — recomputing
  `largest_frontier_run_flop` on the fly.
- A custom-scenario builder.
- Effective-compute layer overlays (once that layer is built).
- Cloud deployment with password protection.

These belong in a v2 after the next modeling layer (effective
compute) ships.

## Troubleshooting

- **"DuckDB not found":** run `uv run database` first. If you've never
  run any pipeline, do the full sequence:
  `uv run historical && uv run supply && uv run allocation && uv run database`.
- **"Table {name} not found":** the upstream pipeline that produces
  that table hasn't been run. Check `docs/output_guide.md` for the
  table → pipeline mapping.
- **Stale numbers:** the app caches per-session via `@st.cache_data`.
  Restart the app (Ctrl-C, `uv run demo` again) to invalidate.
- **Port already in use:** Streamlit picks the next free port; check
  the terminal output for the URL.
