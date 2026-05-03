# Model State

**Last updated:** 2026-05-03 (review layer landed)

## Built

### Historical baseline

- **Status:** complete
- **Run command:** `uv run historical`
- **Main memo:** [`docs/historical_findings.md`](historical_findings.md)
- **Main output table:** `outputs/tables/historical_trend_estimates.csv`
- **Processed dataset:** `data/processed/historical_models.{csv,parquet}`
- **Headline (Rule A 2018+):** training compute 5.97×/yr (R²=0.84, n=113); training cost 4.89×/yr (R²=0.72, n=74); cost per FLOP 0.76×/yr (~24%/yr decline)
- **Charts (8):** all under `outputs/charts/historical_*.png`

### Supply capacity model

- **Status:** complete (sourced inputs, sensitivity, cost variants)
- **Run command:** `uv run supply`
- **Main memo:** [`docs/supply_findings.md`](supply_findings.md)
- **Main output table:** `outputs/tables/supply_fundamental_inputs_by_year.csv`
- **Processed dataset:** `data/processed/supply_fundamental_inputs.csv`
- **Assumptions:** `data/assumptions/supply_input_assumptions.yaml` (15 parameters × 4 scenarios)
- **Scenarios:** `scenarios/supply_*.yaml` (base / capex_rich / chip_bottleneck / power_datacenter_bottleneck)
- **Headline (base case):** 45.7%/yr CAGR 2024→2040; 1.65e+31 FLOP/yr by 2040; capex binds 2024–2036, chip binds 2037–2040
- **Charts (9):** all under `outputs/charts/supply_*.png`

### Allocation layer

- **Status:** complete
- **Run command:** `uv run allocation` (requires `uv run supply` to have produced supply outputs first)
- **Main memo:** [`docs/allocation_findings.md`](allocation_findings.md)
- **Main output table:** `outputs/tables/allocation_largest_frontier_run.csv`
- **Processed dataset:** `data/processed/allocation_compute_by_bucket.csv`
- **Assumptions:** `data/assumptions/allocation_input_assumptions.yaml` (9 parameters × 4 scenarios)
- **Scenarios:** `scenarios/allocation_*.yaml` (base / inference_heavy / training_race / rnd_acceleration)
- **Combined cross-product:** 4 supply × 4 allocation = 16 combined scenarios
- **Headline (base × base):** largest frontier run grows 27.6%/yr 2024→2040 (1.39e+27 → 6.93e+28 FLOP). Frontier-run share of total compute *falls* from 3.5% to 0.4%.
- **Range across scenarios:** 14.1%/yr (chip_bottleneck × inference_heavy) to 48.1%/yr (capex_rich × training_race) CAGR; ~50× spread in absolute 2040 FLOP.
- **Charts (6):** all under `outputs/charts/allocation_*.png`

### Review layer (DuckDB + Excel workbook)

- **Status:** complete
- **Run commands:** `uv run database` (DuckDB, ~5 MB) and `uv run workbook` (Excel, ~110 KB)
- **Main guide:** [`docs/review_workbook_guide.md`](review_workbook_guide.md)
- **Outputs:**
  - `outputs/database/ai_economy.duckdb` — 14 tables + 6 SQL views
  - `outputs/database/database_manifest.json` — schema version + git commit + row counts
  - `outputs/workbooks/ai_economy_model_review.xlsx` — 11 sheets (README, Model Flow, Scenario Matrix, Historical Baseline, Supply Capacity, Allocation Buckets, Largest Frontier Run, Phase 4 Handoff, Assumptions, Sources & Confidence, Output Inventory)
  - `outputs/runs/latest_run_manifest.json` — run metadata + pass/fail counts
- **Validation:** `uv run validate-outputs` walks the outputs tree and verifies every promised artifact exists and is non-empty (53 checks; current state 53/53 pass).

## Current run commands

```bash
uv sync                    # one-time setup (installs deps, registers entry points)
uv run historical          # rebuild historical-baseline deliverables
uv run supply              # rebuild supply-capacity deliverables
uv run allocation          # rebuild allocation deliverables (requires supply)
uv run database            # build the DuckDB review database
uv run workbook            # build the Excel review workbook
uv run validate-outputs    # confirm artifacts present + non-empty
uv run pytest              # run the test suite (32 tests)
```

All three pipelines are idempotent — re-running them overwrites the
existing artifacts in `outputs/charts/` and `outputs/tables/`. The
allocation pipeline reads `outputs/tables/supply_fundamental_inputs_by_year.csv`
and will raise a clear error if you haven't run `uv run supply` first.

## Current main outputs

Tables (in `outputs/tables/`):

| File | What it is |
|---|---|
| `historical_trend_estimates.csv` | All historical log-linear trend fits (45 rows: compute, cost, cost-per-FLOP × 4 cost variants × 9 frontier rules) |
| `historical_hardware_summary.csv` | Hardware-type usage by year for frontier-flagged historical models |
| `supply_fundamental_inputs_by_year.csv` | Annual scenario projections (4 scenarios × 17 years × ~25 columns) |
| `supply_scenario_summary.csv` | Pivot-table summary at milestone years |
| `supply_binding_constraints.csv` | Years-by-binding-constraint counts per scenario |
| `supply_capex_requirements.csv` | Capex required vs capex available, per scenario per year |
| `supply_sensitivity_analysis.csv` | One-parameter sensitivity perturbations of the base scenario |
| `allocation_compute_by_bucket.csv` | Year-by-combined-scenario allocation across the 6 buckets |
| `allocation_largest_frontier_run.csv` | The headline `largest_frontier_run_flop` per year per combined scenario |
| `allocation_scenario_summary.csv` | Per-combined-scenario milestone summary (2024 / 2030 / 2040) + 16-year CAGRs |
| `allocation_vs_historical_trend.csv` | Year-by-year gap_ratio between allocation projections and the historical Rule A 2018+ extrapolation |
| `allocation_share_assumptions_by_year.csv` | Interpolated allocation parameters by year (audit trail) |

Charts (in `outputs/charts/`):

- 8 `historical_*.png` (compute / cost / cost-per-FLOP / by-org / residuals / hardware-timeline)
- 9 `supply_*.png` (accelerator stock / theoretical / usable compute / power constraint / capex required / binding-constraint heatmap / cost variants / sensitivity bands / supply-vs-historical)
- 6 `allocation_*.png` (compute by bucket / largest frontier run / vs historical / training-vs-inference share / frontier-run share of total / 4×4 scenario grid)

For per-file interpretation see [`output_guide.md`](output_guide.md).

## Not yet built

### Effective compute

- **Purpose:** convert raw frontier training-run FLOP into algorithmically-adjusted *effective* compute, accounting for architectural and post-training efficiency gains.
- **Depends on:** allocation layer's `largest_frontier_run_flop_by_year` output (now available).
- **Reason this is next:** all upstream layers feeding it are now built; the historical-vs-projection 7-OOM gap (visible in `outputs/charts/allocation_vs_historical_training_compute.png`) is the obvious phenomenon for this layer to address by adjusting raw FLOP for algorithmic-efficiency gains.

### Capability mapping

- **Purpose:** map effective compute into task horizons / benchmark performance / automation levels.
- **Depends on:** effective-compute layer.

### Probabilistic projections

- **Purpose:** combine all upstream layers into Monte-Carlo-style projections with confidence bands rather than scenario point estimates.
- **Depends on:** capability mapping (or earlier layers, depending on what's being projected).

### Economy feedback

- **Purpose:** revenue / reinvestment loops feeding back into supply-side capex assumptions, closing the macro loop.
- **Depends on:** all of the above.

## Next recommended build

**The effective-compute layer.** Now that allocation is shipped, the
`largest_frontier_run_flop_by_year` output is available. The
effective-compute layer should consume it and adjust upward for
algorithmic-efficiency gains (Epoch's published estimate is ~3×/yr
for language-model training, with ranges 1.5×–10× depending on
sub-field). The output `effective_compute_flop_by_year` becomes the
input to the capability-mapping layer that follows.

Recommended layout, following the established conventions:

- `pipelines/effective_compute.py` (entry point: `uv run effective_compute`)
- `model/effective_compute_engine.py`
- `data/assumptions/effective_compute_input_assumptions.yaml`
- `scenarios/effective_compute_*.yaml`
