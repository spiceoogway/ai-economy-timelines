# ai-economy-timelines

A scenario-based model of frontier AI compute. Three components shipped, effective compute is next.

- **Historical baseline** — empirical compute & spend baseline for frontier models, derived from the [Epoch AI](https://epoch.ai) "Notable AI Models" dataset. Log-linear fits, frontier-rule sensitivity, residual diagnostics.
- **Supply capacity model** — forward compute-capacity projection 2024–2040: H100-equivalent shipments, installed stock with retirement, power / data-center / capex constraints, utilization derating, binding-constraint identification across four scenarios.
- **Allocation layer** — splits total usable compute into 6 buckets (inference, training, AI R&D, post-training, safety/eval, reserved), decomposes the training pool into the largest single frontier run, and produces `largest_frontier_run_flop_by_year` across the 4 × 4 = 16 supply × allocation combined-scenario cross-product.

## How to read this repo

New readers should start with the orientation docs in `docs/`:

1. [`docs/executive_summary.md`](docs/executive_summary.md) — plain-English summary, headline numbers, what's built, what's next.
2. [`docs/model_map.md`](docs/model_map.md) — full model architecture and data flow with diagrams.
3. [`docs/model_state.md`](docs/model_state.md) — what's built vs not built, run commands, output table.
4. [`docs/output_guide.md`](docs/output_guide.md) — what each output file means and how to interpret it.
5. [`docs/input_provenance.md`](docs/input_provenance.md) — where every input comes from, with confidence flags.
6. [`docs/glossary.md`](docs/glossary.md) — definitions of core terms (frontier training run vs total usable compute, etc.).
7. [`docs/component_contracts.md`](docs/component_contracts.md) — per-component inputs, outputs, and downstream consumers.
8. [`docs/model_walkthrough.md`](docs/model_walkthrough.md) — guided tour through the actual outputs.
9. [`docs/review_workbook_guide.md`](docs/review_workbook_guide.md) — how to use the DuckDB review database and Excel workbook.

Then:

9. [`docs/historical_findings.md`](docs/historical_findings.md) — historical-baseline final memo.
10. [`docs/supply_findings.md`](docs/supply_findings.md) — supply-capacity final memo + allocation-layer handoff.
11. [`docs/scope.md`](docs/scope.md) — merged scope for both components.

## Most important caution

> The supply-capacity model estimates **total annual usable AI compute**.
> It does **not** estimate the **largest frontier training run** yet.
> That is the purpose of the next layer (compute allocation).

Treating the historical 5.97×/yr frontier-run trend as a forecast of total compute, or treating the supply-capacity 45.7%/yr CAGR as a forecast of single-run scaling, is the most common reading mistake. See the executive summary for the full framing.

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
uv run validate-outputs    # confirm every artifact is present + non-empty
uv run pytest              # run the test suite (32 tests)
```

The first three pipelines produce `outputs/charts/`, `outputs/tables/`,
and `data/processed/` artifacts. `uv run database` and `uv run workbook`
are the institutional review layer — they consume those artifacts to
produce a single DuckDB file (`outputs/database/ai_economy.duckdb`)
and an 11-sheet Excel workbook (`outputs/workbooks/ai_economy_model_review.xlsx`).
See [`docs/review_workbook_guide.md`](docs/review_workbook_guide.md)
for how to use them.

## Structure

```
data/
  raw/                 Raw Epoch CSVs (immutable)
  processed/           Cleaned datasets; outputs of historical/supply pipelines
  assumptions/
    supply_input_assumptions.yaml    Single source of truth for supply-capacity inputs
docs/
  executive_summary.md      Plain-English summary
  model_map.md              Architecture + data flow
  model_state.md            What's built / not built
  output_guide.md           Output-file interpretation
  input_provenance.md       Where inputs come from
  glossary.md               Core terms
  component_contracts.md    Per-component inputs/outputs
  model_walkthrough.md      Guided walkthrough of actual outputs
  scope.md                  Merged scope for both components
  historical_findings.md    Historical-baseline final memo
  historical_initial_notes.md
  supply_findings.md        Supply-capacity final memo
  supply_initial_notes.md
  data_dictionary.md
  assets/
    model_architecture.png  Polished architecture diagram
model/
  runtime.py                Shared paths, color maps, source-line strings
  data_cleaning.py          Historical raw-data normalization
  frontier_filters.py       Historical frontier-model rules (A/B/C)
  trend_fitting.py          Historical log-linear fits
  historical_charts.py      Historical chart helpers
  supply_engine.py          Supply-side compute-capacity engine
  allocation_engine.py      Allocation engine (buckets + training-pool decomp)
pipelines/
  historical.py             `uv run historical` entry point
  supply.py                 `uv run supply` entry point
  supply_charts.py          Supply chart helpers
  allocation.py             `uv run allocation` entry point
  allocation_charts.py      Allocation chart helpers
model/
  workbook_export.py        11-sheet Excel review workbook builder
  review_database.py        DuckDB review-database builder (14 tables, 6 views)
pipelines/
  build_review_database.py  `uv run database` entry point
  export_workbook.py        `uv run workbook` entry point
  validate_repo_outputs.py  `uv run validate-outputs` entry point
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

Full memo: `docs/historical_findings.md`.

## Supply-capacity headline (sourced base case)

| Scenario | 2024 (FLOP/yr) | 2040 (FLOP/yr) | CAGR | Binding 2030 |
|---|---|---|---|---|
| Baseline continuation | 3.97e+28 | 1.65e+31 | **45.7%/yr** | capex |
| Capex-rich | 4.37e+28 | 2.89e+31 | 50.1%/yr | capex |
| Chip-constrained | 3.83e+28 | 6.54e+30 | 37.9%/yr | chip |
| Power/DC-constrained | 3.50e+28 | 6.64e+30 | 38.8%/yr | datacenter |

Full memo + allocation-layer handoff: `docs/supply_findings.md`.

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

Full memo + effective-compute handoff: `docs/allocation_findings.md`.
