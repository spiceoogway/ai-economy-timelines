# Component Contracts

For each model component (built or future), the inputs it consumes, the
transformation it performs, the outputs it produces, what it does *not*
include, the main uncertainty, and the planned downstream consumer.

The two `built` components have firm contracts (the engine code defines
them). The five `future` components have *proposed* contracts that
should be revisited when each is actually built.

---

## Historical Baseline

**Status:** ✓ built

**Inputs:**
- `data/raw/epoch_notable_ai_models_raw.csv` (Epoch's "Notable AI Models" dataset; 1,011 model rows, 47 raw columns)

**Transformation:**
- Normalize column names and organization labels
- Parse publication dates; derive `release_year_fractional`
- Compute frontier-rule flags (Rule A: top-10 by compute in trailing window; Rule B: top per-org-per-year; Rule C: ≥1e23 FLOP)
- Fit log-linear trends (`log10(y) = a + b·year`) for compute, three cost variants, and cost-per-FLOP, across 9 frontier-rule × time-window combinations

**Outputs:**
- `data/processed/historical_models.{csv,parquet}` — cleaned 1,011-row dataset
- `outputs/tables/historical_trend_estimates.csv` — 45 fitted-trend rows
- `outputs/tables/historical_hardware_summary.csv` — hardware-type by year
- 8 charts under `outputs/charts/historical_*.png`

**Does not include:**
- Capability metrics (no benchmark scores, no task horizons)
- Forward projections (the trend fits are descriptive, not predictive)
- Total-compute or fleet-size estimates (per-run only)
- Geographic split

**Main uncertainty:** the cost-variant divergence (headline 2023-USD vs
upfront-hardware vs cloud-rental costs grow at 2.5× / 4.9× / 3.4× per
year respectively under Rule A 2018+). This is bigger than the rule-
choice divergence and is the single most important caveat the
historical baseline carries forward.

**Downstream consumer:** the supply-capacity model reads
`historical_trend_estimates.csv` to overlay the historical trend on
`outputs/charts/supply_vs_historical_compute_trend.png`. The allocation
layer will use it as a calibration target.

---

## Supply Capacity Model

**Status:** ✓ built

**Inputs:**
- `data/assumptions/supply_input_assumptions.yaml` (15 parameters × 4 scenarios at milestone years)
- `scenarios/supply_*.yaml` (4 scenario configs: base / capex_rich / chip_bottleneck / power_datacenter_bottleneck)
- `outputs/tables/historical_trend_estimates.csv` (read by `pipelines/supply.py` for the comparison overlay)

**Transformation:**
- Linearly interpolate parameters between milestone years
- Project annual H100-equivalent shipments through 2040
- Apply linear retirement (lifetime in years) → installed chip-limited stock
- Compute four constraint-limited stocks independently: chip / power / DC / capex
- Take `min` across the four → `available_stock_h100e`; record `argmin` → `binding_constraint`
- Multiply by peak FLOP × seconds/year × utilization → `usable_compute_flop_year`

**Outputs:**
- `data/processed/supply_fundamental_inputs.csv`
- `outputs/tables/supply_fundamental_inputs_by_year.csv` (4 scenarios × 17 years)
- `outputs/tables/supply_scenario_summary.csv`, `supply_binding_constraints.csv`, `supply_capex_requirements.csv`, `supply_sensitivity_analysis.csv`
- 9 charts under `outputs/charts/supply_*.png`

**Does not include:**
- Training vs inference allocation
- Single-frontier-run compute (the model gives total annual usable compute, not per-run)
- Capability forecasting
- Effective compute (no algorithmic-efficiency adjustment)
- Revenue / reinvestment feedback
- Geographic split
- Quarterly grain (annual only)

**Main uncertainty:** 2030 H100-equivalent stock (Epoch's published
range is 20M–400M, a 20× spread; the base case anchors to the median
100M). The hyperscaler-AI-share assumption (we treat ~75% of
hyperscaler capex as AI infrastructure post-2025) is a close second.

**Downstream consumer:** the allocation layer will consume
`supply_fundamental_inputs_by_year.csv` directly to produce
`largest_frontier_run_flop_by_year`.

---

## Compute Allocation Layer

**Status:** ✗ next

**Inputs (proposed):**
- `outputs/tables/supply_fundamental_inputs_by_year.csv` (annual usable compute by scenario)
- `outputs/tables/historical_trend_estimates.csv` (calibration target)
- `data/assumptions/allocation_input_assumptions.yaml` (new; allocation shares + largest-run concentration)
- `scenarios/allocation_*.yaml` (new; allocation scenarios)

**Transformation (proposed):**
- Split annual `usable_compute_flop_year` into training / inference / AI R&D experiments / post-training / reserves shares
- Within the training slice, model the largest-run concentration (fraction of training compute that goes to the single largest run)
- Combine: `largest_frontier_run_flop = usable_compute × training_share × largest_run_concentration`
- Calibrate against historical Rule A 2018+ trend (the model should reproduce the historical 5.97×/yr in the 2018–2024 backcast)

**Outputs (proposed):**
- `outputs/tables/allocation_by_year.csv` — training / inference / R&D / post-training / reserves shares per scenario per year
- `outputs/tables/largest_frontier_run_flop_by_year.csv` — **the headline output**, single-frontier-run FLOP per scenario per year, comparable directly with the historical-baseline trend
- Charts under `outputs/charts/allocation_*.png`

**Does not include (proposed):**
- Effective compute (algorithmic adjustment)
- Capability forecasting
- Per-organization or per-lab allocation

**Main uncertainty (anticipated):** the largest-run concentration
parameter. Historical estimates put it at 5–15% of frontier-lab
compute, but the absolute fraction of *global* compute is harder to
pin down. Sensitivity to this parameter is roughly linear in the
output.

**Downstream consumer:** the effective-compute layer.

---

## Effective Compute Layer

**Status:** ✗ future

**Inputs (proposed):**
- `outputs/tables/largest_frontier_run_flop_by_year.csv` (from the allocation layer)
- Algorithmic-efficiency assumptions: how much more capability per FLOP do new architectures + training recipes deliver each year?

**Transformation (proposed):**
- Adjust raw frontier-run FLOP upward by an annual algorithmic-efficiency multiplier
- Output `effective_compute_flop_by_year` (gross — i.e., what 2024 architectures *would have* needed)

**Outputs (proposed):**
- `outputs/tables/effective_compute_by_year.csv`
- Charts comparing raw vs effective compute trajectories

**Does not include (proposed):**
- Capability metrics directly (just the FLOP-equivalent quantity)
- Per-task efficiency (treats efficiency as one global multiplier)

**Main uncertainty (anticipated):** the algorithmic-efficiency
multiplier itself. Epoch's published estimate is ~3× per year for
language-model training; ranges from ~1.5× to ~10× depending on
which subfield and which definition of "efficiency."

**Downstream consumer:** capability-mapping layer.

---

## Capability Mapping Layer

**Status:** ✗ future

**Inputs (proposed):**
- `outputs/tables/effective_compute_by_year.csv`
- Capability-vs-effective-compute scaling laws (e.g. METR's task-horizon doubling time, GPQA / MMLU scaling, autonomous-coding benchmarks)

**Transformation (proposed):**
- Map effective compute to one or more capability metrics: task horizons, benchmark scores, automation levels

**Outputs (proposed):**
- `outputs/tables/capability_by_year.csv`
- Charts of capability trajectories per scenario

**Does not include (proposed):**
- Probabilistic confidence bands (deferred to projection-engine layer)
- Economic value of capabilities (deferred to economy-feedback layer)

**Main uncertainty (anticipated):** the FLOP-to-capability mapping
itself. Different benchmarks scale at very different rates with
compute, and within-benchmark scaling laws have been revised
multiple times.

**Downstream consumer:** projection engine.

---

## Projection Engine

**Status:** ✗ future

**Inputs (proposed):**
- All upstream layers' outputs
- Probability distributions over input parameters (replacing scenario point estimates)

**Transformation (proposed):**
- Monte Carlo over the joint input distribution
- Produce confidence bands on each downstream output

**Outputs (proposed):**
- Probabilistic versions of every prior layer's outputs (with confidence intervals)

**Does not include (proposed):**
- Causal feedback (one-shot Monte Carlo, not dynamic)

**Main uncertainty (anticipated):** the *correlations* between input
parameters. Treating shipments and capex as independent over-states
sensitivity; treating them as perfectly correlated under-states it.

**Downstream consumer:** economy-feedback layer.

---

## Economy Feedback Layer

**Status:** ✗ future

**Inputs (proposed):**
- All upstream layers' outputs
- Revenue / valuation models per capability level
- Reinvestment elasticities (how much of AI revenue flows back into AI capex)

**Transformation (proposed):**
- Close the macro loop: revenue from capabilities → reinvestment → capex on the supply side → next-period output
- Iterate to fixed point or trajectory equilibrium

**Outputs (proposed):**
- Self-consistent forward projections including macro feedback
- Counterfactuals (e.g. what happens if reinvestment elasticity drops)

**Does not include (proposed):**
- Policy shocks (treated exogenously if at all)

**Main uncertainty (anticipated):** the AI-revenue-to-capex elasticity.
Currently ~80–90% for the largest hyperscalers; whether this
persists at scale is genuinely uncertain.

**Downstream consumer:** none — this is the bottom of the model
stack.

---

## Cross-component invariants

Some properties must hold across the full stack once it's built:

- **Backcast calibration.** When the allocation layer is built, applying
  it to 2018–2024 should approximately reproduce the historical Rule A
  2018+ trend. If it doesn't, either the supply model is mis-anchored,
  the allocation parameters are wrong, or the historical baseline
  itself is flawed.
- **Total-compute conservation.** Across all allocation slices in a
  given year, the sum should equal `usable_compute_flop_year` for
  that scenario.
- **Effective-compute monotonicity.** Effective compute per
  frontier-run FLOP should be non-decreasing year-over-year (you
  can't *unlearn* algorithmic efficiency).

These will become integration tests once the corresponding layers
exist.
