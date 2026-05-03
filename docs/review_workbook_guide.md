# Review Workbook Guide

How to use the institutional review artifacts: the **DuckDB review
database** (`outputs/database/ai_economy.duckdb`) and the **Excel
review workbook** (`outputs/workbooks/ai_economy_model_review.xlsx`).

Both are **generated artifacts**. The source of truth remains the
YAMLs, Python pipelines, CSV outputs, and Markdown findings. The
workbook and database are reproducible from the repo and safe to
delete and rebuild at any time.

---

## 1. What the workbook is

An 11-sheet Excel file generated from the existing `outputs/tables/`
CSVs and the `data/assumptions/*.yaml` files. The workbook is
designed for *review*, not *editing* — open it, read it, sort and
filter, but don't paste numbers into it. Every cell is regenerable.

The DuckDB database is the same data exposed as a single SQL-queryable
file. Use it when you want to write ad-hoc queries (e.g. "top 5
combined scenarios by 2040 largest_run") without writing Python.

## 2. How to generate them

```bash
# Full rebuild (~20s end-to-end):
uv run historical
uv run supply
uv run allocation
uv run database
uv run workbook

# Verify everything was produced correctly:
uv run validate-outputs
```

The first three commands produce the upstream CSVs and PNGs. `uv run
database` reads those CSVs and assembles the DuckDB. `uv run workbook`
reads the same CSVs (and the assumption YAMLs) to produce the Excel
file. `uv run validate-outputs` walks the output tree and confirms
every promised artifact is present and non-empty.

## 3. How to read each sheet

### Sheet 1 — README
What the workbook is, when it was generated, source-of-truth hierarchy,
what NOT to infer, and links to the orientation docs. Always read first.

### Sheet 2 — Model Flow
Component status table with BUILT (green) / NEXT (yellow) / FUTURE (grey)
flags, plus inputs / transformation / outputs / downstream consumer per
component. The single best way to ground a new reader before they
look at any numbers.

### Sheet 3 — Scenario Matrix
The most-useful single sheet for fast comparison. **16 combined
scenarios sorted by 2040 largest_frontier_run_flop**, with milestone
metrics (usable_compute and largest_run at 2030 + 2040, CAGR,
frontier-run-share at 2030 + 2040, binding_constraint at 2030 + 2040).
Color-scale on largest_run_2040 (red→green) shows the scenario
ranking at a glance. Filter on `combined_scenario_id` for SQL-style
slicing.

### Sheet 4 — Historical Baseline
The full `historical_trend_estimates.csv` with 45 trend fits.
Important: **all 45 rows are descriptive fits**, not forecasts. The
preferred row is `frontier_rule == "frontier_rule_a_2018+"` and
`trend_name == "training_compute"` (the headline 5.97×/yr).

### Sheet 5 — Supply Capacity
Two sections — supply scenario summary (4 scenarios × milestone
years) and capex requirements (capex required vs assumed-available).
For full year-by-year detail, see `outputs/tables/supply_fundamental_inputs_by_year.csv`.

### Sheet 6 — Allocation Buckets
Full `allocation_compute_by_bucket.csv` (272 rows = 16 combined
scenarios × 17 years). Filter on `combined_scenario_id` to focus on
one scenario; sort by year for time-series view of the 6 buckets.

### Sheet 7 — Largest Frontier Run
The headline `largest_frontier_run_flop` for every (scenario, year).
**Slow / base / fast envelope rows are color-highlighted** (red /
yellow / green) so the handoff envelope is unmistakable.

### Sheet 8 — Phase 4 Handoff
The single most-important sheet for downstream consumers. Wide-format
pivot with slow / base / fast `largest_frontier_run_flop` columns
side-by-side, plus base-case bucket totals (training, inference,
AI R&D, post-training). Year column frozen. Column headers
color-coded (slow=red, base=yellow, fast=green).

The three envelope scenarios:

```
slow:  chip_bottleneck × inference_heavy
base:  base × base
fast:  capex_rich × training_race
```

**This sheet is what the effective-compute layer should consume as
its primary input table.**

### Sheet 9 — Assumptions
Two sections — allocation share assumptions interpolated by year
(with confidence-color coding green/yellow/red), and a supply
assumption summary listing every (parameter, scenario) row from
the supply YAML.

### Sheet 10 — Sources & Confidence
Flattened audit trail: every assumption YAML row with its `source`,
`source_type`, `confidence`, `unit`, `used_for`, and `notes`. Use
this to answer "where did this number come from?" without opening
YAML.

### Sheet 11 — Output Inventory
Every file in `outputs/tables/`, `outputs/charts/`, and
`data/processed/` with path, component (historical / supply /
allocation), type (table / chart / processed dataset), and
`generated_by` pipeline. Use this to answer "what's in the
repo?".

## 4. What the workbook should NOT be used for

- **Don't edit it by hand.** Edits are wiped on the next regen. Edit
  the upstream YAMLs and rerun the pipelines instead.
- **Don't treat workbook numbers as a separate source of truth.**
  If the workbook disagrees with a CSV, the CSV is the source of truth
  and the workbook is stale (regenerate it).
- **Don't read raw FLOP figures as effective FLOP.** The workbook
  shows raw, unadjusted training-run compute. Algorithmic-efficiency
  adjustments come from the (yet-to-be-built) effective-compute
  layer.
- **Don't read the historical trend fits as forecasts.** They are
  descriptive log-linear fits on the 2018–2026 corpus. The "gap"
  between the historical extrapolation and the allocation projections
  is real but multi-causal — see `docs/allocation_findings.md` §6.

## 5. Source-of-truth hierarchy

When numbers disagree, trust the higher row:

1. **Raw data and public sources** (Epoch CSV, IEA report, NVIDIA
   datasheet, hyperscaler 10-Ks)
2. **YAML assumptions and scenario files** (`data/assumptions/*.yaml`,
   `scenarios/*.yaml`)
3. **Python model logic** (`model/*.py`, `pipelines/*.py`)
4. **Processed CSV / Parquet outputs** (`outputs/tables/*`, `data/processed/*`)
5. **DuckDB review database** (`outputs/database/ai_economy.duckdb`)
6. **Excel review workbook** (`outputs/workbooks/ai_economy_model_review.xlsx`)
7. **Markdown findings and charts** (`docs/*_findings.md`, `outputs/charts/*`)

Rows 5–7 are *generated*. They should be reproducible from rows 1–4.
If they aren't, rerun the pipelines.

## 6. Effective-compute handoff

The Phase 4 Handoff sheet (Sheet 8) is the cleanest way to read out
the slow / base / fast envelope. Same data is also exposed via the
DuckDB view `v_phase4_handoff` and the
`outputs/tables/allocation_compute_by_bucket.csv` rows where
`combined_scenario_id` is one of `chip_bottleneck__inference_heavy`,
`base__base`, or `capex_rich__training_race`.

For year-by-year detail with the explicit envelope label
(slow/base/fast) attached to each row, query
`v_slow_base_fast_envelope`:

```sql
SELECT * FROM v_slow_base_fast_envelope WHERE year IN (2024, 2030, 2040);
```

The effective-compute layer should consume `largest_frontier_run_flop`
as its raw input and apply algorithmic-efficiency multipliers to
produce `effective_compute_flop_by_year` per scenario per year.

## 7. Database views (DuckDB)

Six views are pre-built at database-build time:

| View | What it shows |
|---|---|
| `v_largest_run_2040_ranked` | All 16 combined scenarios sorted by 2040 largest_run |
| `v_phase4_handoff` | Slow / base / fast envelope, full bucket detail per year |
| `v_scenario_matrix` | Same as Sheet 3, sorted by 2040 largest_run |
| `v_base_case_timeseries` | Just the base × base scenario, all years |
| `v_slow_base_fast_envelope` | Slow / base / fast with explicit envelope label per row |
| `v_sources_and_confidence` | Flattened audit trail from the assumption YAMLs |

Inspect via:

```bash
uv run python -c "import duckdb; con = duckdb.connect('outputs/database/ai_economy.duckdb'); \
    print(con.execute('SELECT * FROM v_largest_run_2040_ranked LIMIT 5').fetchdf())"
```

Or open the file in any DuckDB-compatible client (DBeaver, DataGrip,
the DuckDB CLI, etc.).
