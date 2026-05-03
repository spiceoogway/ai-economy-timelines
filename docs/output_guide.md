# Output Guide

Per-file documentation for every major artifact in `outputs/tables/` and
`data/processed/`. For each file: what it is, main columns, how to use it,
what *not* to infer, and the planned downstream consumer.

## outputs/tables/historical_trend_estimates.csv

**What it is:** all log-linear trend fits produced by the historical
baseline. 45 rows covering training compute, training cost (3 cost
variants), and cost-per-FLOP, each across 9 frontier rules / time
windows.

**Main columns:**
- `trend_name` — `training_compute`, `training_cost_2023usd`, `training_cost_cloud`, `training_cost_upfront`, `cost_per_flop_2023usd`
- `frontier_rule` — e.g. `frontier_rule_a_2018+`, `epoch_frontier_flag_full`, `all_models_full`
- `start_year`, `end_year`, `n_models`
- `slope_log10_per_year` — fitted slope of log10(y) vs year
- `annual_growth_multiplier` — equivalent annual ×, i.e. 10^slope
- `doubling_time_years` — log(2) / log(annual_multiplier)
- `r_squared`, `standard_error`
- `notes` — free-text fit context

**How to use it:** as the source-of-truth for any historical-trend statement
("frontier compute grew at X×/yr"). Pick the (trend_name, frontier_rule)
row matching the claim. Rule A 2018+ is the project's preferred frontier
definition for the modern era.

**What *not* to infer:** these are *historical* fits, not forecasts. The
preferred Rule A 2018+ slope of ~5.97×/yr cannot be extrapolated to 2030+
without a supply-capacity check. The historical trend is a single-frontier-
run quantity, not a total-compute quantity.

**Downstream consumer:** the supply-capacity pipeline reads this file via
`get_historical_rule_a_2018_fit()` to overlay the historical fit on
`outputs/charts/supply_vs_historical_compute_trend.png`. The allocation
layer will use it as its calibration target.

---

## outputs/tables/supply_fundamental_inputs_by_year.csv

**What it is:** the supply-capacity model's primary output. One row per
(scenario, year) covering 2024–2040 across four scenarios = 68 rows
× ~24 columns.

**Main columns:**
- `year`, `scenario`
- `accelerator_shipments_h100e` — annual H100-eq shipments (input)
- `installed_stock_h100e_chip_limited` — chip-only stock (with retirement)
- `power_limited_stock_h100e`, `datacenter_limited_stock_h100e`, `capex_limited_stock_h100e`
- `available_stock_h100e` — `min` of the four above (the binding limit)
- `binding_constraint` — `chip` / `power` / `datacenter` / `capex`
- `theoretical_compute_flop_year` — chip stock × peak FLOP × seconds/year
- `usable_compute_flop_year` — after constraints + utilization derating; **the headline**
- `cost_per_h100e_year_{upfront,cloud,blended}` — three cost variants per Phase 1 finding

**How to use it:** as the input to the (yet-to-be-built) allocation layer.
For any forward-compute statement, pull the (scenario, year, column) cell.
The base scenario (`base_input_case`) is the recommended central case.

**What *not* to infer:** **`usable_compute_flop_year` is total annual
global usable AI compute**, not the size of any single training run.
Treating it as a single-run quantity (and comparing it against the
historical 5.97×/yr trend on its own) is the most common reading mistake.
The allocation layer will translate this into single-frontier-run FLOP.

**Downstream consumer:** the allocation layer will consume this file
directly to produce `largest_frontier_run_flop_by_year`.

---

## outputs/tables/supply_scenario_summary.csv

**What it is:** a pivot-table summary at milestone years (2024, 2025,
2026, 2027, 2030, 2035, 2040) across the four supply scenarios. Smaller
than the full annual table; useful for quick comparisons.

**Main columns:** same as `supply_fundamental_inputs_by_year.csv` but
filtered to milestone years and aggregated where applicable.

**How to use it:** quoting numbers in memos, presentations, or
informal discussion. Faster to skim than the full annual file.

**What *not* to infer:** the milestone-year subset is a representative
sample, not a complete picture; growth is non-linear between
milestones in some scenarios.

**Downstream consumer:** memo authoring; not consumed by other
pipelines.

---

## outputs/tables/supply_binding_constraints.csv

**What it is:** for each scenario, a count of how many years (within
2024–2040) each constraint binds.

**Main columns:** `scenario`, `binding_constraint`, `years_binding`.

**How to use it:** quick sanity check on which constraints actually
matter in each scenario. Under base, capex binds 13 years and chip
binds 4. Under power_datacenter_bottleneck, datacenter binds most
of the horizon.

**What *not* to infer:** "years binding" is a coarse summary. The
year-by-year sequence of binding constraints (in
`supply_fundamental_inputs_by_year.csv`) tells the actual story —
e.g. *when* the binding switches from capex to chip matters more
than the total count.

**Downstream consumer:** the allocation layer will need to know
which constraint is binding because chip-binding vs capex-binding
implies very different supply elasticities (and therefore different
allocation trade-offs).

---

## outputs/tables/supply_capex_requirements.csv

**What it is:** capex required (to grow chip-limited stock by Δ at
this year's cluster cost) vs capex assumed-available, per scenario
per year.

**Main columns:** `scenario`, `year`, `capex_required_usd`,
`capex_available_usd`, `capex_coverage_ratio` (= required ÷ available).

**How to use it:** to understand whether the supply scenarios are
internally consistent — i.e. whether the chip stock the model
*assumes* shipped is consistent with the capex the model *assumes*
available. Coverage ratio < 1 means assumed capex is more than
sufficient; > 1 means the chip-stock assumption requires more capex
than the model says exists, which is exactly what makes capex bind
in those years.

**What *not* to infer:** the capex-required figure assumes 100% of
that capex flows to chips + clusters; in reality, software, data
centers, R&D salaries, and inference operations also draw on the
same capex pool. The model's `cluster_capex_multiplier` already
accounts for some of this.

**Downstream consumer:** internal supply-model consistency check;
not consumed by other pipelines.

---

## outputs/tables/supply_sensitivity_analysis.csv

**What it is:** results of one-parameter perturbations of the base
scenario across three high-leverage inputs (shipments, AI-DC MW,
capex) at multipliers {0.5×, 0.75×, 1.0×, 1.5×, 2.0×}. 15 ×
17 years × full row width = ~255 rows.

**Main columns:** all `supply_fundamental_inputs_by_year.csv` columns
plus `sensitivity_parameter` and `sensitivity_multiplier`.

**How to use it:** to see how much each input matters. Roughly:
shipments and capex are tightly coupled in the base case (capex was
already binding); AI-DC capacity is *slack* in the base case so
perturbing it has minimal effect.

**What *not* to infer:** these are *single-parameter* perturbations
holding everything else fixed. Real input uncertainty is correlated
across parameters (e.g. a chip shortage usually coincides with
higher chip prices), and the joint sensitivity is not captured here.

**Downstream consumer:** sensitivity-band charts; informs which
inputs the allocation layer should treat as wider-uncertainty
priors.

---

## outputs/tables/historical_hardware_summary.csv

**What it is:** for each frontier-flagged historical model, a count
of (release_year, hardware_type) combinations. Descriptive only.

**Main columns:** `release_year`, `hardware_type`, `n`.

**How to use it:** to track the historical evolution from V100 →
A100 → H100 → B200 in the frontier-model corpus.

**What *not* to infer:** Epoch's `hardware_type` field is sparse and
sometimes inconsistent (e.g. "TPU v4 Pods" vs "TPU v4"); don't read
fine-grained per-chip distinctions into this.

**Downstream consumer:** the supply model's H100-equivalent
performance-index calibration (informational).

---

## data/processed/historical_models.{csv,parquet}

**What it is:** the cleaned, frontier-flagged version of Epoch's
"Notable AI Models" dataset. 1,011 rows × 35 columns, covering
1950–2026.

**Main columns:** see [`data_dictionary.md`](data_dictionary.md) for the
full schema. Headlines: `model_name`, `organization`, `release_year`,
`training_compute_flop`, `estimated_training_cost_usd`,
`epoch_frontier_flag`, `frontier_rule_{a,b,c}`, `frontier_any`.

**How to use it:** the source-of-truth for any per-model historical
question. The trend tables are derived from this file.

**What *not* to infer:** the dataset is *Epoch's* — confidence flags
are theirs, not ours. Some entries are confident measurements; many
are reverse-engineered estimates. The `compute_estimate_quality`
column tracks the original Epoch confidence (Confident / Likely /
Speculative / Unknown).

**Downstream consumer:** internal to the historical pipeline
(`pipelines/historical.py`). Not directly consumed by the supply or
allocation layers.

---

## outputs/tables/allocation_compute_by_bucket.csv

**What it is:** the allocation pipeline's primary output — annual
compute allocation across the 6 buckets, with training-pool
decomposition, for every (supply, allocation) combination. 16
combined scenarios × 17 years = 272 rows × ~24 columns.

**Main columns:**
- `year`, `supply_scenario`, `allocation_scenario`, `combined_scenario`
- `usable_compute_flop_year` (carried from supply)
- 6 bucket shares (sum to 1) and 6 corresponding `*_compute_flop_year` values
- `frontier_lab_training_share`, `largest_run_concentration`, `cluster_contiguity_factor`
- `frontier_lab_training_compute_flop_year`
- **`largest_frontier_run_flop`** — the headline quantity
- `frontier_run_share_of_total_compute`
- `binding_constraint` (carried from supply)

**How to use it:** as the input to the (yet-to-be-built) effective-
compute layer. For any allocation-derived statement, pull the
appropriate (combined_scenario, year) row.

**What *not* to infer:** these are *raw* FLOP numbers. They have
not been adjusted for algorithmic efficiency, data quality, or
architectural improvements. Treating two FLOP numbers from
different years as equivalent capability is wrong; that's what
the effective-compute layer exists to fix.

**Downstream consumer:** the effective-compute layer.

---

## outputs/tables/allocation_largest_frontier_run.csv

**What it is:** a slimmer view of the allocation output focused on
the headline quantity. 272 rows.

**Main columns:** `year`, `supply_scenario`, `allocation_scenario`,
`combined_scenario`, `largest_frontier_run_flop`,
`frontier_run_share_of_total_compute`,
`training_compute_flop_year`,
`frontier_lab_training_compute_flop_year`.

**How to use it:** the cleanest single source for forward
single-frontier-run-FLOP statements. Comparable apples-to-apples
with the historical Rule A 2018+ trend (after rebasing the
historical intercept to 1e25 FLOP at 2024).

**What *not* to infer:** the same caveat as `allocation_compute_by_bucket.csv`
applies — raw FLOP, not effective FLOP.

**Downstream consumer:** historical-comparison chart; the
effective-compute layer.

---

## outputs/tables/allocation_scenario_summary.csv

**What it is:** per-combined-scenario milestone summary at 2024 /
2030 / 2040, plus 16-year CAGRs. 16 rows.

**Main columns:** `combined_scenario`, `supply_scenario`,
`allocation_scenario`, `usable_compute_{2024,2030,2040}`,
`largest_run_{2024,2030,2040}`, `largest_run_cagr_2024_2040`,
`frontier_run_share_{2024,2030,2040}`.

**How to use it:** quick-comparison table for memos and
presentations. Sorted by 2040 largest_run gives a clear
"which combination produces the biggest single run" ranking.

**What *not* to infer:** the milestone subset hides non-monotonic
behavior. Use `allocation_compute_by_bucket.csv` for the
year-by-year detail.

**Downstream consumer:** memo authoring; not consumed by other
pipelines.

---

## outputs/tables/allocation_vs_historical_trend.csv

**What it is:** year-by-year gap between allocation-derived
single-frontier-run projections and the historical Rule A 2018+
extrapolation. 272 rows (one per combined_scenario × year).

**Main columns:** `year`, `scenario` (the combined name),
`supply_scenario`, `allocation_scenario`,
`historical_trend_frontier_run_flop` (extrapolation rebased to 1e25
at 2024), `projected_largest_frontier_run_flop`, `gap_ratio`,
`log10_gap`.

**How to use it:** to quantify the gap between the historical-trend
extrapolation and the allocation-derived forward projection. By 2040
the historical extrapolation reaches ~1e+37 vs realistic
projections ~1e+28-29, giving log10_gap of ~8-9 OOM.

**What *not* to infer:** **the historical extrapolation is not a
forecast.** It's a descriptive fit on 2018–2024 data. The "gap" is
the joint effect of (a) the historical trend already slowing,
(b) allocation parameters possibly being conservative, and
(c) supply fundamentals genuinely capping single-run growth.

**Downstream consumer:** the effective-compute layer (calibration
target — does adjusting for algorithmic efficiency close the gap?).

---

## outputs/tables/allocation_share_assumptions_by_year.csv

**What it is:** the linearly-interpolated allocation parameters by
year. Audit trail showing what shares the model used between
milestones. 4 scenarios × 17 years = 68 rows.

**Main columns:** `allocation_scenario`, `year`, plus all 9
allocation parameters.

**How to use it:** to verify what the model assumed in any given
year, especially between milestones. Bucket shares should sum to
1.0 within tolerance for every row (enforced by tests).

**What *not* to infer:** these are *interpolated* values; the
underlying milestones are at 2024 / 2030 / 2040 only, with linear
interpolation between. A non-linear trajectory between milestones
would require additional milestones.

**Downstream consumer:** internal validation; not consumed by
other pipelines.

---

## outputs/database/ai_economy.duckdb

**What it is:** a single DuckDB file aggregating every output table
plus a flattened sources_and_confidence table from the assumption
YAMLs (14 tables, 6 SQL views).

**Tables:** the 13 from above (historical_models /
historical_trend_estimates / historical_hardware_summary /
supply_fundamental_inputs_by_year / supply_scenario_summary /
supply_binding_constraints / supply_capex_requirements /
supply_sensitivity_analysis / allocation_compute_by_bucket /
allocation_largest_frontier_run / allocation_scenario_summary /
allocation_vs_historical_trend / allocation_share_assumptions_by_year)
plus `sources_and_confidence` built from YAML.

**Views:** `v_largest_run_2040_ranked`, `v_phase4_handoff`,
`v_scenario_matrix`, `v_base_case_timeseries`,
`v_slow_base_fast_envelope`, `v_sources_and_confidence`.

**How to use it:** for ad-hoc SQL queries across multiple model
components without writing pandas. Open in any DuckDB-compatible
client (DBeaver, the DuckDB CLI, etc.) or query inline:

```python
import duckdb
con = duckdb.connect("outputs/database/ai_economy.duckdb", read_only=True)
con.execute("SELECT * FROM v_phase4_handoff WHERE year IN (2024, 2030, 2040)").fetchdf()
```

**What *not* to infer:** the database is a generated artifact.
It can become stale if you edit a CSV without rerunning
`uv run database`. Source of truth remains the upstream CSVs.

**Downstream consumer:** the Excel workbook (which reads the
underlying CSVs directly, not the DuckDB), and any ad-hoc analysis.

---

## outputs/workbooks/ai_economy_model_review.xlsx

**What it is:** an 11-sheet Excel workbook generated from the
output CSVs and assumption YAMLs. The institutional review
artifact.

**Sheets:** README, Model Flow, Scenario Matrix, Historical
Baseline, Supply Capacity, Allocation Buckets, Largest Frontier
Run, Phase 4 Handoff, Assumptions, Sources & Confidence, Output
Inventory. See [`review_workbook_guide.md`](review_workbook_guide.md)
for sheet-by-sheet documentation.

**How to use it:** open in Excel / Numbers / LibreOffice. Sort
and filter the tabular sheets; the Phase 4 Handoff sheet
specifically formats slow / base / fast envelopes side-by-side
for the effective-compute layer.

**What *not* to infer:** **don't edit the workbook by hand**.
Edits are wiped on the next regen. Edit the upstream YAMLs and
rerun the pipelines instead.

**Downstream consumer:** human reviewers; the effective-compute
layer (Phase 4 Handoff sheet).

---

## outputs/runs/latest_run_manifest.json

**What it is:** a small JSON file capturing the most recent
`uv run validate-outputs` run. Contains run_timestamp, git_commit,
python_version, pipelines_run list, output table list, output
chart list, database path, workbook path, tests_passed bool, and
total pass/fail counts.

**How to use it:** as an audit trail. Captures what state the
repo was in at the time of the last full validation pass.

**What *not* to infer:** the manifest is overwritten on each
`uv run validate-outputs`. For run history, see git log.

**Downstream consumer:** none directly; useful for debugging
"when did this artifact last regenerate cleanly?".

---

## data/processed/supply_fundamental_inputs.csv

**What it is:** identical content to
`outputs/tables/supply_fundamental_inputs_by_year.csv`. Lives under
`data/processed/` because in the canonical Phase-2 spec layout it's
treated as a "processed dataset" rather than an analytical output.

**How to use it:** prefer the `outputs/tables/` copy for downstream
consumption; this copy exists for spec compliance.

**Downstream consumer:** none distinct from the
`outputs/tables/` copy.
