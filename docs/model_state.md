# Model State

**Last updated:** 2026-05-03

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

## Current run commands

```bash
uv sync              # one-time setup (installs deps, registers entry points)
uv run historical    # rebuild historical-baseline deliverables
uv run supply        # rebuild supply-capacity deliverables
uv run pytest        # run the test suite (11 tests)
```

Both `uv run historical` and `uv run supply` are idempotent — re-running
them overwrites the existing artifacts in `outputs/charts/` and
`outputs/tables/`.

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

Charts (in `outputs/charts/`):

- 8 `historical_*.png` (compute / cost / cost-per-FLOP / by-org / residuals / hardware-timeline)
- 9 `supply_*.png` (accelerator stock / theoretical / usable compute / power constraint / capex required / binding-constraint heatmap / cost variants / sensitivity bands / supply-vs-historical)

For per-file interpretation see [`output_guide.md`](output_guide.md).

## Not yet built

### Compute allocation

- **Purpose:** split total usable AI compute into inference, training, AI R&D, post-training, reserves.
- **Main missing output:** `largest_frontier_run_flop_by_year`.
- **Reason this is next:** without it, the supply-capacity model's total-compute trajectory cannot be compared to the historical-baseline's single-frontier-run trend. This is the central conceptual bridge in the project.

### Effective compute

- **Purpose:** convert raw frontier training-run FLOP into algorithmically-adjusted *effective* compute, accounting for architectural and post-training efficiency gains.
- **Depends on:** allocation layer's `largest_frontier_run_flop_by_year` output.

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

**The allocation layer.** Keep the same scenario-keyed structure (`scenarios/allocation_*.yaml`), follow the same layout as the supply-capacity component (`pipelines/allocation.py`, `model/allocation_engine.py`, `data/assumptions/allocation_input_assumptions.yaml`), and emit `largest_frontier_run_flop_by_year` as the headline output.

The orientation docs (`docs/executive_summary.md`, this file, `docs/model_map.md`) explicitly forward-reference allocation as the bridging layer. Building it next closes the most important conceptual gap in the model.
