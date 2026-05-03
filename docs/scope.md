# Project Scope

This is the merged scope for the project: a **historical baseline** of
frontier AI training compute and cost (from Epoch's Notable AI Models
dataset) and a **supply-side compute-capacity model** projecting
2024–2040 under multiple scenarios. Future components (allocation,
effective compute, capability) will be added in their own sections
when they land.

The historical baseline is the empirical input layer for the supply
capacity model — together they answer:

> What did frontier AI training compute and cost look like historically,
> and what physical / financial / infrastructure inputs determine how
> much AI compute can exist going forward?

---

# Section 1 — Historical Baseline

## Objective

Build a clean historical baseline for frontier AI model training compute and
estimated training cost.

The goal of the historical baseline is **not** to forecast AGI, capabilities, automation, or
the AI economy. The goal is to answer:

> Can we accurately reconstruct historical frontier-model compute and spending
> trends before using them as the foundation for forecasts?

The historical baseline should produce a reliable dataset, fitted historical curves, and
diagnostic charts that later phases can build on.

## Core research questions

1. How fast has frontier training compute grown historically?
2. How fast has estimated frontier training cost grown historically?
3. How much variation exists between labs, model types, and time periods?
4. What historical growth curve best fits frontier training compute?
5. What historical growth curve best fits frontier training spend?
6. How sensitive are these estimates to frontier-model selection rules?
7. What baseline assumptions should be carried into the supply capacity model?

## In scope

- Epoch "Notable AI Models" data, 2012–2026 (broad) and 2018–2026 (narrow).
- Three frontier filters (A: top-10 by compute at release; B: top-per-org-per-year;
  C: above 1e23 FLOP).
- Log-linear trend fits for training compute, training cost, and cost per FLOP.
- Hardware/cluster descriptive statistics.
- Quality flags per row (compute / cost / date / inclusion).

## Out of scope

Capability forecasting · task-horizon modeling · AI R&D automation ·
recursive improvement · revenue forecasting · inference-demand modeling ·
macro productivity · labor-market automation · regulatory scenarios ·
chip export-control modeling · power-grid bottlenecks · valuation modeling.

## Deliverables

1. `data/processed/historical_models.{parquet,csv}`
2. `docs/data_dictionary.md`
3. Charts in `outputs/charts/` (compute, cost, cost/FLOP, by-org, residuals)
4. `outputs/tables/historical_trend_estimates.csv`
5. `docs/historical_findings.md` memo

## Acceptance criteria

The historical baseline is complete when:

1. Clean model-level dataset with documented sources.
2. At least three explicit frontier-model filters.
3. Historical trend estimates for training compute, training cost, cost/FLOP.
4. Diagnostic charts showing fit quality and outliers.
5. Memo explaining assumptions, uncertainties, and supply-capacity handoff parameters.

---

# Section 2 — Supply-Side Compute Capacity Model

## Objective

Build the first structural projection layer beneath frontier compute.

The historical baseline asked:

> What happened historically to frontier training compute and training cost?

The supply capacity model asks:

> What physical, financial, and infrastructure inputs determine how much AI compute can exist in the future?

The goal is to stop treating frontier compute growth as a pure trend and instead derive available compute from fundamentals:

```text
chips
power
data centers
capex
hardware performance
hardware cost
utilization
cloud / ownership economics
```

The supply capacity model does **not** yet forecast capabilities. It should produce a defensible input-side compute capacity model that the allocation layer can allocate across training, inference, and AI R&D.

---

# 1. Core Research Questions

The supply capacity model should answer:

```text
1. How much AI accelerator compute capacity exists by year?
2. How fast can accelerator stock grow?
3. What share of accelerator stock is plausibly available for frontier AI labs?
4. How do chip performance, chip cost, power draw, and utilization evolve?
5. How much power and data-center capacity constrain usable compute?
6. How much capex is required to sustain different compute-growth paths?
7. Do the historical compute trends remain physically/economically plausible?
8. What input assumptions should be handed to the allocation layer?
```

The key output is a **supply-side compute capacity model**, not a capability forecast.

---

# 2. In Scope

## A. Accelerator Supply Model

Model annual AI accelerator supply and installed stock.

Required variables:

```text
year
accelerator_type
vendor
annual_shipments_units
installed_stock_units
retired_stock_units
average_lifetime_years
frontier_relevant_stock_units
```

Initial accelerator categories:

```text
NVIDIA H100 / H200 class
NVIDIA B100 / B200 / GB200 class
Google TPU class
AMD MI300 / MI350 class
AWS Trainium / Inferentia class
Other frontier-relevant accelerators
```

For the supply capacity model, you do **not** need perfect chip-by-chip precision. You need a common unit.

Recommended common unit:

```text
H100-equivalent accelerator-years
```

Optional second unit:

```text
FP16/BF16 dense FLOP/s-equivalent
```

The supply capacity model should produce:

```text
installed_accelerator_stock_t
h100_equivalent_stock_t
annual_accelerator_growth_t
```

---

## B. Hardware Performance Model

Convert accelerator stock into theoretical compute.

Required variables:

```text
peak_flops_per_chip
memory_bandwidth
memory_capacity
interconnect_bandwidth
power_draw_watts
release_year
performance_relative_to_h100
```

Initial conversion:

```text
theoretical_compute_per_year =
    chip_count
  × peak_flops_per_chip
  × seconds_per_year
```

Then apply utilization later.

Recommended simplification:

```text
hardware_performance_index_t
```

Where:

```text
H100 = 1.0
H200 = estimated multiplier
B200 / GB200 = estimated multiplier
TPU generation = estimated multiplier
MI300 / MI350 = estimated multiplier
```

Outputs:

```text
theoretical_compute_capacity_flop_per_year
h100_equivalent_compute_capacity
hardware_performance_growth_rate
```

---

## C. Power Constraint Model

Compute is constrained by electricity, not just chips.

Required variables:

```text
chip_power_draw_kw
server_power_overhead
networking_power_overhead
cooling_overhead
PUE
data_center_power_capacity_mw
usable_ai_power_capacity_mw
power_availability_constraint
```

Basic equation:

```text
usable_ai_power_mw =
    data_center_power_capacity_mw
  × ai_share_of_datacenter_power
```

Then:

```text
max_accelerators_power_supported =
    usable_ai_power_mw
  / effective_power_per_accelerator_mw
```

Where:

```text
effective_power_per_accelerator =
    chip_power
  × server_overhead
  × PUE
```

Deliverables:

```text
power_limited_accelerator_stock_t
power_limited_compute_capacity_t
binding_constraint_flag_t
```

The key question:

```text
Are chips the bottleneck, power the bottleneck, or capex the bottleneck?
```

---

## D. Data-Center Buildout Model

Model how quickly AI compute capacity can actually be housed.

Required variables:

```text
data_center_capacity_mw
new_capacity_added_mw_per_year
construction_lag_years
ai_dedicated_capacity_share
retrofit_capacity_mw
greenfield_capacity_mw
regional_capacity_constraints
```

Simple first equation:

```text
available_datacenter_capacity_t =
    existing_capacity_t
  + new_capacity_online_t
  + retrofit_capacity_t
```

Outputs:

```text
ai_datacenter_capacity_mw_by_year
buildout_lag_assumptions
capacity_addition_scenarios
```

This module should be linked to the power model but kept separate because permitting, interconnection, transformers, cooling, and land can bind before aggregate electricity supply does.

---

## E. Capex and Financing Model

Model how much money is required to buy and deploy the compute stack.

Required variables:

```text
accelerator_capex
server_capex
networking_capex
storage_capex
datacenter_capex
power_infrastructure_capex
total_ai_infrastructure_capex
frontier_lab_capex
hyperscaler_capex
government_capex
financing_constraint_flag
```

Simple total cost structure:

```text
total_deployed_compute_capex =
    accelerator_cost
  + server_cost
  + networking_cost
  + storage_cost
  + datacenter_cost
  + power_infrastructure_cost
```

The supply capacity model should explicitly distinguish:

```text
chip-only capex
cluster capex
full-stack data-center capex
```

This matters because the historical baseline training-cost estimates are not the same as full infrastructure investment. the historical baseline found that cost variants diverge meaningfully and should be carried forward separately.

Outputs:

```text
capex_required_by_scenario
capex_per_h100e_year
compute_capacity_per_dollar
capex_limited_compute_capacity_t
```

---

## F. Utilization and Derating Model

Theoretical FLOP are not usable FLOP.

Required variables:

```text
cluster_utilization_rate
training_utilization_rate
inference_utilization_rate
networking_efficiency
memory_constraint_factor
failure_rate
scheduling_loss
reserved_capacity_share
```

Basic equation:

```text
usable_compute_capacity_t =
    theoretical_compute_capacity_t
  × utilization_t
  × cluster_efficiency_t
```

Recommended first-pass values should be scenario-based, not overfit:

```text
low_utilization
base_utilization
high_utilization
```

Outputs:

```text
usable_compute_flop_per_year
usable_compute_derating_factor
utilization_sensitivity_table
```

---

## G. Ownership and Cloud Economics

The supply capacity model should preserve the historical baseline cost-variant insight.

Track three cost perspectives:

```text
1. Upfront hardware cost
2. Cloud-rental equivalent cost
3. Blended / headline 2023-USD cost
```

Required outputs:

```text
cost_per_flop_upfront
cost_per_flop_cloud
cost_per_flop_blended
cost_per_h100e_year_upfront
cost_per_h100e_year_cloud
cost_per_h100e_year_blended
```

---

# 3. Out of Scope

Do **not** include these in the supply capacity model:

```text
Capability forecasting
Task-horizon modeling
AI R&D automation
Recursive improvement
Training vs inference allocation
Revenue forecasting
Labor automation
Macroeconomic productivity
Policy response modeling
Military / geopolitical scenario modeling
Full chip supply-chain model
Company valuation modeling
```

Important boundary:

```text
the supply capacity model estimates available compute capacity.
the allocation layer decides how that compute is allocated.
the effective-compute layer converts raw compute into effective compute.
the capability layer maps effective compute to capabilities.
```

---

# 4. Core Model Architecture

The supply capacity model should produce yearly values from 2024–2040.

Recommended annual model flow:

```text
accelerator_shipments_t
        ↓
installed_accelerator_stock_t
        ↓
h100_equivalent_stock_t
        ↓
theoretical_compute_capacity_t
        ↓
power_limited_compute_capacity_t
        ↓
datacenter_limited_compute_capacity_t
        ↓
capex_limited_compute_capacity_t
        ↓
usable_compute_capacity_t
```

Final supply capacity model output:

```text
available_ai_compute_capacity_t =
    min(
        chip_limited_compute_t,
        power_limited_compute_t,
        datacenter_limited_compute_t,
        capex_limited_compute_t
    )
    × utilization_t
```

Also output the binding constraint:

```text
binding_constraint_t =
    argmin(
        chip_limited_compute_t,
        power_limited_compute_t,
        datacenter_limited_compute_t,
        capex_limited_compute_t
    )
```

---

# 5. Data Schema

## Input Assumptions Table

File:

```text
data/assumptions/supply_input_assumptions.yaml
```

Columns:

```text
parameter
scenario
year
value
unit
source
confidence
notes
```

Examples:

```text
h100_equivalent_shipments
ai_datacenter_capacity_mw
average_accelerator_power_kw
pue
cluster_utilization_rate
accelerator_cost_usd
datacenter_capex_per_mw
hardware_performance_index
```

---

## Processed Annual Input Table

File:

```text
data/processed/supply_fundamental_inputs.csv
```

Columns:

```text
year
scenario
accelerator_shipments_h100e
installed_stock_h100e
retired_stock_h100e
hardware_performance_index
theoretical_compute_flop_year
ai_power_capacity_mw
power_limited_stock_h100e
datacenter_capacity_mw
datacenter_limited_stock_h100e
capex_available_usd
capex_required_usd
capex_limited_stock_h100e
utilization_rate
usable_compute_flop_year
binding_constraint
```

---

# 6. Scenarios

The supply capacity model should include at least four scenarios.

## Scenario 1: Baseline Continuation

```text
Name: base_input_case
Purpose: central case using the historical baseline handoff assumptions
```

Use the historical baseline as an output check, not a direct driver.

Historical-baseline handoff parameters:

```text
base compute growth: 6.0×/yr
fast compute growth: 6.4×/yr
slow compute growth: 2.0×/yr
base cost-per-FLOP decline: 0.75×/yr
```

These should be used to compare whether the input model can plausibly reproduce historical-like compute growth.

## Scenario 2: Chip-Constrained

```text
Name: chip_bottleneck
Assumption: demand and capex exist, but accelerator supply grows slowly
```

## Scenario 3: Power / Data-Center Constrained

```text
Name: power_datacenter_bottleneck
Assumption: chips and capital exist, but grid interconnection and data-center buildout limit deployment
```

## Scenario 4: Capex-Rich Acceleration

```text
Name: capex_rich
Assumption: hyperscalers, governments, and AI labs massively increase AI infrastructure investment
```

Optional later:

```text
regulated_slowdown
hardware_breakthrough
supply_chain_shock
sovereign_ai_buildout
```

---

# 7. Supply Capacity Model Deliverables

## Deliverable 1: Input Assumptions File

```text
data/assumptions/supply_input_assumptions.yaml
```

Purpose:

```text
Single auditable source of scenario assumptions.
```

---

## Deliverable 2: Fundamental Input Model Module

```text
model/supply_engine.py
```

Responsibilities:

```text
load_assumptions()
project_accelerator_stock()
convert_to_h100_equivalent()
estimate_power_limited_capacity()
estimate_datacenter_limited_capacity()
estimate_capex_limited_capacity()
estimate_usable_compute()
identify_binding_constraint()
```

---

## Deliverable 3: Scenario Config Files

```text
scenarios/supply_base_input_case.yaml
scenarios/supply_chip_bottleneck.yaml
scenarios/supply_power_datacenter_bottleneck.yaml
scenarios/supply_capex_rich.yaml
```

---

## Deliverable 4: the supply capacity model Notebook

```text
pipelines/supply.py
```

Required sections:

```text
1. Load Historical-baseline handoff parameters
2. Load the supply capacity model assumptions
3. Project accelerator stock
4. Convert to theoretical compute capacity
5. Apply power constraints
6. Apply data-center constraints
7. Apply capex constraints
8. Apply utilization derating
9. Compare implied compute growth vs the historical baseline historical trend
10. Export processed the supply capacity model dataset
```

---

## Deliverable 5: Charts

```text
outputs/charts/supply_accelerator_stock_h100e.png
outputs/charts/supply_theoretical_compute_capacity.png
outputs/charts/supply_usable_compute_capacity.png
outputs/charts/supply_power_capacity_constraint.png
outputs/charts/supply_capex_required.png
outputs/charts/supply_binding_constraint_by_year.png
outputs/charts/supply_vs_historical_compute_trend.png
```

---

## Deliverable 6: Tables

```text
outputs/tables/supply_fundamental_inputs_by_year.csv
outputs/tables/supply_scenario_summary.csv
outputs/tables/supply_binding_constraints.csv
outputs/tables/supply_capex_requirements.csv
```

---

## Deliverable 7: the supply capacity model Memo

```text
docs/scope.md
docs/supply_findings.md
```

`supply_findings.md` should end with handoff parameters for the allocation layer:

```text
usable_compute_capacity_by_year
theoretical_compute_capacity_by_year
available_h100e_stock_by_year
capex_required_by_year
power_capacity_by_year
binding_constraint_by_year
recommended compute allocation envelope
known weaknesses
```

---

# 8. Acceptance Criteria

The supply capacity model is complete when the repo can:

```text
1. Project accelerator stock by year under multiple scenarios.
2. Convert accelerator stock into theoretical annual compute capacity.
3. Apply power, data-center, capex, and utilization constraints.
4. Identify the binding constraint by year and scenario.
5. Produce usable AI compute capacity through 2040.
6. Compare input-derived compute capacity against the historical compute trends.
7. Export a clean annual dataset for the allocation layer.
8. Document assumptions and uncertainties in a memo.
```

A strong the supply capacity model should be able to defend statements like:

```text
“In the base input case, available AI compute grows X×/yr through 2030, below/above the historical baseline historical frontier trend of ~6×/yr.”

“In the power/data-center bottleneck case, chips are available but deployment capacity binds beginning in year Y.”

“In the capex-rich case, the limiting factor shifts from capital to power by year Z.”

“Under these assumptions, sustaining historical-baseline-style compute growth would require approximately $X of cumulative AI infrastructure capex by year Y.”
```

---

# 9. First Implementation Sprint

## Sprint Length

```text
1–2 weeks
```

## Sprint Goal

Create a working the supply capacity model skeleton that projects H100-equivalent stock and usable compute capacity under three scenarios.

## Sprint Tasks

```text
1. Add data/assumptions/supply_input_assumptions.yaml.
2. Add scenarios/supply_base_input_case.yaml.
3. Add scenarios/supply_chip_bottleneck.yaml.
4. Add scenarios/supply_power_datacenter_bottleneck.yaml.
5. Implement model/supply_engine.py.
6. Project accelerator stock from shipments and retirement assumptions.
7. Convert stock to theoretical annual compute.
8. Apply a simple utilization derating.
9. Add rough power and capex constraints.
10. Generate first comparison chart against the historical baseline Rule A historical trend.
```

## Sprint Output

```text
pipelines/supply.py
outputs/charts/supply_usable_compute_capacity.png
outputs/charts/supply_vs_historical_compute_trend.png
outputs/tables/supply_scenario_summary.csv
docs/supply_initial_notes.md
```

---

# 10. Recommended Repo Additions

As implemented, the supply-capacity component lives at:

```text
data/
  assumptions/
    supply_input_assumptions.yaml

scenarios/
  supply_base_input_case.yaml
  supply_chip_bottleneck.yaml
  supply_power_datacenter_bottleneck.yaml
  supply_capex_rich.yaml

model/
  supply_engine.py

pipelines/
  supply.py
  supply_charts.py

docs/
  scope.md           (this file; merged historical + supply scope)
  supply_initial_notes.md
  supply_findings.md
```

---

# Final Supply Capacity Model Decision

```text
Primary task:
Model the fundamental input stack that determines available AI compute capacity.

Primary inputs:
Accelerator supply, hardware performance, power, data-center capacity, capex, and utilization.

Primary output:
Annual usable AI compute capacity by scenario through 2040.

Primary handoff to the allocation layer:
A scenario-indexed compute capacity envelope that can be allocated across training, inference, AI R&D experiments, post-training, and reserves.
```
