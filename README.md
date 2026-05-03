# ai-economy-timelines

A scenario-based model of frontier AI compute. Five components shipped, effective compute is next.

- **Historical baseline** — empirical compute & spend baseline for frontier models, derived from the [Epoch AI](https://epoch.ai) "Notable AI Models" dataset. Log-linear fits, frontier-rule sensitivity, residual diagnostics.
- **Supply capacity model** — forward compute-capacity projection 2024–2040: H100-equivalent shipments, installed stock with retirement, power / data-center / capex constraints, utilization derating, binding-constraint identification across four scenarios.
- **Allocation layer** — splits total usable compute into 6 buckets (inference, training, AI R&D, post-training, safety/eval, reserved), decomposes the training pool into the largest single frontier run, and produces `largest_frontier_run_flop_by_year` across the 4 × 4 = 16 supply × allocation combined-scenario cross-product.
- **Review layer** — generated DuckDB review database (14 tables, 6 views) and 11-sheet Excel review workbook for SQL queries and at-a-glance review.
- **Scenario explorer** — read-only Streamlit app on top of the DuckDB; 9 pages covering overview, scenario matrix, supply, allocation, largest run, effective-compute handoff, assumptions, provenance, and run manifest.

## How to read this repo

The docs are organized into four named groups. Read in order if you're new to the project; jump directly if you're looking for something specific.

### A. Start here

1. [`docs/executive_summary.md`](docs/executive_summary.md) — plain-English summary, headline numbers, what's built, what's next.
2. [`docs/model_map.md`](docs/model_map.md) — full model architecture and data flow with diagrams.
3. [`docs/model_state.md`](docs/model_state.md) — what's built vs not built, run commands, output table.
4. [`docs/glossary.md`](docs/glossary.md) — definitions of core terms (frontier training run vs total usable compute, etc.).

### B. Reading the outputs

5. [`docs/output_guide.md`](docs/output_guide.md) — what each output file means and how to interpret it.
6. [`docs/model_walkthrough.md`](docs/model_walkthrough.md) — guided tour through the actual outputs.
7. [`docs/review_workbook_guide.md`](docs/review_workbook_guide.md) — how to use the DuckDB review database and Excel workbook.
8. [`docs/streamlit_demo_guide.md`](docs/streamlit_demo_guide.md) — how to launch and use the interactive scenario explorer.

### C. Per-component memos

9. [`docs/historical_findings.md`](docs/historical_findings.md) — historical-baseline final memo.
10. [`docs/supply_findings.md`](docs/supply_findings.md) — supply-capacity final memo + allocation-layer handoff.
11. [`docs/allocation_findings.md`](docs/allocation_findings.md) — allocation-layer final memo + effective-compute handoff.
12. [`docs/historical_initial_notes.md`](docs/historical_initial_notes.md) — sprint-1 working notes for the historical baseline.
13. [`docs/supply_initial_notes.md`](docs/supply_initial_notes.md) — sprint-1 working notes for the supply capacity model.
14. [`docs/allocation_initial_notes.md`](docs/allocation_initial_notes.md) — sprint-1 working notes for the allocation layer.

### D. Reference

15. [`docs/scope.md`](docs/scope.md) — merged scope for the historical, supply, and allocation components.
16. [`docs/component_contracts.md`](docs/component_contracts.md) — per-component inputs, outputs, and downstream consumers.
17. [`docs/input_provenance.md`](docs/input_provenance.md) — where every input comes from, with confidence flags.
18. [`docs/data_dictionary.md`](docs/data_dictionary.md) — historical-baseline column-level schema and source-to-column mappings.

## Most important caution

> The supply-capacity model estimates **total annual usable AI compute**.
> The allocation layer maps that to **largest frontier training run**.
> Treating the historical 5.97×/yr frontier-run trend as a forecast of total compute, or treating supply / allocation projections as forecasts of single-run scaling without the bridging share parameters, is the most common reading mistake.

See the executive summary for the full framing.

## Setup

```bash
uv sync
```

## Run

```bash
uv run historical          # rebuild historical-baseline deliverables
uv run supply              # rebuild supply-capacity deliverables
uv run allocation          # rebuild allocation deliverables (requires supply)
uv run database            # build the DuckDB review database
uv run workbook            # build the Excel review workbook
uv run demo                # launch the Streamlit scenario explorer
uv run validate-outputs    # confirm every artifact is present + non-empty
uv run pytest              # run the test suite (32 tests)
```

The first three pipelines produce `outputs/charts/`, `outputs/tables/`,
and `data/processed/` artifacts. `uv run database` and `uv run workbook`
are the institutional review layer — they consume those artifacts to
produce a single DuckDB file (`outputs/database/ai_economy.duckdb`)
and an 11-sheet Excel workbook (`outputs/workbooks/ai_economy_model_review.xlsx`).
`uv run demo` launches a read-only Streamlit scenario explorer on top
of the DuckDB. See [`docs/review_workbook_guide.md`](docs/review_workbook_guide.md)
and [`docs/streamlit_demo_guide.md`](docs/streamlit_demo_guide.md) for
how to use them.

## Structure

```
data/
  raw/                      Raw Epoch CSVs (immutable)
  processed/                Cleaned datasets; outputs of the upstream pipelines
  assumptions/
    supply_input_assumptions.yaml      Single source of truth for supply-capacity inputs
    allocation_input_assumptions.yaml  Single source of truth for allocation inputs
docs/                       Markdown documentation (see "How to read" above)
  assets/
    model_architecture.png  Regenerable architecture diagram
model/
  runtime.py                Shared paths, color maps, source-line strings
  data_cleaning.py          Historical raw-data normalization
  frontier_filters.py       Historical frontier-model rules (A/B/C)
  trend_fitting.py          Historical log-linear fits
  historical_charts.py      Historical chart helpers
  supply_engine.py          Supply-side compute-capacity engine
  allocation_engine.py      Allocation engine (buckets + training-pool decomp)
  review_database.py        DuckDB review-database builder (14 tables, 6 views)
  workbook_export.py        11-sheet Excel review workbook builder
pipelines/
  historical.py             `uv run historical` entry point
  supply.py                 `uv run supply` entry point
  supply_charts.py          Supply chart helpers
  allocation.py             `uv run allocation` entry point
  allocation_charts.py      Allocation chart helpers
  build_review_database.py  `uv run database` entry point
  export_workbook.py        `uv run workbook` entry point
  validate_repo_outputs.py  `uv run validate-outputs` entry point
app/
  streamlit_app.py          Streamlit landing page (`uv run demo`)
  data_loader.py            DuckDB-first / CSV-fallback accessors (cached)
  formatting.py             Number-formatter helpers (FLOP, %, USD)
  charts.py                 Plotly chart helpers
  launcher.py               `uv run demo` entry point
  pages/                    9 sidebar-navigable pages
scenarios/
  supply_*.yaml             Four supply-side scenarios
  allocation_*.yaml         Four allocation scenarios
tests/                      pytest suite (32 tests including output inventory)
outputs/
  charts/                   Final PNGs (historical_*, supply_*, allocation_*)
  tables/                   Fitted-trend / capacity / allocation CSVs
  database/                 ai_economy.duckdb + database_manifest.json
  workbooks/                ai_economy_model_review.xlsx
  runs/                     latest_run_manifest.json
```

## Historical-baseline headline (Rule A, 2018+)

| Metric | Annual × | Doubling | R² | n |
|---|---|---|---|---|
| Training compute (FLOP) | 5.97× | 4.7 mo | 0.84 | 113 |
| Training cost (2023 USD) | 4.89× | 5.2 mo | 0.72 | 74 |
| Cost per FLOP | 0.76× (~24%/yr decline) | — | 0.21 | 74 |

Full memo: [`docs/historical_findings.md`](docs/historical_findings.md).

## Supply-capacity headline (sourced base case)

| Scenario | 2024 (FLOP/yr) | 2040 (FLOP/yr) | CAGR | Binding 2030 |
|---|---|---|---|---|
| Baseline continuation | 3.97e+28 | 1.65e+31 | **45.7%/yr** | capex |
| Capex-rich | 4.37e+28 | 2.89e+31 | 50.1%/yr | capex |
| Chip-constrained | 3.83e+28 | 6.54e+30 | 37.9%/yr | chip |
| Power/DC-constrained | 3.50e+28 | 6.64e+30 | 38.8%/yr | datacenter |

Full memo + allocation-layer handoff: [`docs/supply_findings.md`](docs/supply_findings.md).

## Allocation headline (largest frontier training run)

Combined supply × allocation scenarios (4 × 4 = 16). Top and bottom of the
range:

| Combined scenario | 2024 | 2040 | CAGR |
|---|---|---|---|
| capex_rich × training_race (fast) | 1.74e+27 | 9.38e+29 | **48.1%/yr** |
| **base × base (headline)** | **1.39e+27** | **6.93e+28** | **27.6%/yr** |
| chip_bottleneck × inference_heavy (slow) | 9.52e+26 | 7.84e+27 | 14.1%/yr |

Frontier-run share of total compute *falls* in every scenario (3.5% in
2024 → <1% in most by 2040). The historical Rule A 2018+ extrapolation
of 5.97×/yr passes through the allocation envelope around 2027–2028
and reaches ~1e+37 FLOP by 2040 — a ~7 OOM gap that the
effective-compute layer will partly address.

Full memo + effective-compute handoff: [`docs/allocation_findings.md`](docs/allocation_findings.md).
