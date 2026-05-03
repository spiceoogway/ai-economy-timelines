# Glossary

Definitions of core terms used throughout this project. Where two
quantities are similar but not the same, the entries explicitly call
out the distinction.

---

## Frontier training run

A single major training run for a frontier AI model — for example, the
training run that produced GPT-4, Claude 3 Opus, or Gemini 1.5 Pro. The
historical baseline tracks one row per such run from Epoch's "Notable
AI Models" dataset.

This is **not** the same as total annual AI compute. A frontier run
consumes only a *share* of the global AI compute available in its
release year.

## Frontier training compute

The total floating-point operations performed during a single frontier
training run. Stored in absolute FLOP. Typical 2024 frontier runs are
in the **1e25–1e26 FLOP** range.

This is what the historical baseline measures via `training_compute_flop`.
It is **not** the same as `usable_compute_flop_year` (which is the
supply-side annual total).

## Total usable AI compute

The total amount of AI compute available globally in one year, after
accounting for chip stock, power, data-center capacity, capex, and
utilization. The supply-capacity model's headline output.

Measured in **FLOP per year**. The 2024 base-scenario value is roughly
**3.97e+28 FLOP/year**; the 2040 base value is **1.65e+31 FLOP/year**.

This is **not** the same as one frontier training run's FLOP. A
frontier run consumes some share (currently a small fraction) of one
year's total usable compute.

## Theoretical compute

The compute capacity implied by raw chip count × peak FLOP/s × seconds
per year, before applying constraints (power, DC, capex) or utilization
derating. The supply model emits `theoretical_compute_flop_year` as an
intermediate quantity.

## Effective compute

A future quantity (not yet implemented). Effective compute will be raw
FLOP **adjusted upward** for algorithmic-efficiency gains: each
generation of architectures, training recipes, and post-training
improvements lets a fixed FLOP budget produce a more capable model.
Without an effective-compute layer, two runs at the same FLOP count
in different years are treated as equivalent — which is wrong.

## H100-equivalent

A common unit for accelerator counts. One H100-equivalent is one
NVIDIA H100 GPU's worth of FP16/BF16 dense FLOP/s (roughly 989
TFLOP/s). Used to normalize across hardware generations and vendors:
B200 chips count as more than 1 H100-equivalent each; older A100s
count as less.

The supply model tracks `h100_equivalent_shipments` and
`installed_stock_h100e` rather than physical chip counts because the
H100-equivalent unit absorbs perf-per-chip improvements naturally.

## FLOP/year

The rate of floating-point operations per calendar year. The natural
unit for *total annual compute*, including the supply-capacity model's
`usable_compute_flop_year` and `theoretical_compute_flop_year`.

This is **not** the same as FLOP-per-training-run, which has no time
dimension. A 1e25-FLOP training run might use 1e25 FLOP total over a
multi-month training period; a 1e29-FLOP/year fleet does that much
work continuously across all running jobs.

## Training compute

Compute consumed during pretraining (and fine-tuning, in some
accountings) of a model. The historical baseline's primary measurement.
The allocation layer will need to split annual `usable_compute_flop_year`
into training vs inference vs other uses.

## Inference compute

Compute consumed serving a trained model in production. Roughly the
*opposite* allocation slice from training compute. Currently
inference-vs-training split is unmodeled; the allocation layer will
introduce it.

## AI R&D experiment compute

Compute consumed by experiments that aren't a single canonical training
run: ablations, evals, safety testing, scaling-law experiments,
post-training-recipe sweeps. Often ~10–30% of frontier-lab compute
budgets historically; the allocation layer will track this.

## Post-training compute

Compute consumed in RLHF, RLAIF, fine-tuning passes, and other
processing steps applied to a base model. Sometimes counted under
training, sometimes broken out. The allocation layer should keep
this as a separate slice.

## Capex

Capital expenditure — the dollars spent on physical AI infrastructure
(chips, servers, networking, data-center shells, power infrastructure).
The supply model treats annual `ai_infrastructure_capex_usd` as a
constraint that competes with chips and power for binding status.

The supply-model base case has 2024 capex at ~$210B and 2030 at
~$1.5T/year (global, AI-dedicated).

## Capex constraint

The capex-limited stock = cumulative capex flow ÷ installed-cost-per-H100e.
Asks: "if all available capex were spent on chips and clusters, how
many H100-equivalents could that buy?" Binds early in the supply
projection horizon (2024–2036 in the base case).

## Chip constraint

The chip-limited stock = installed H100-eq stock with linear
retirement. Asks: "ignoring all other limits, how many H100-eq exist
on earth?" Binds late in the base supply scenario (2037–2040) and
throughout the chip-bottleneck scenario.

## Power constraint

The power-limited stock = AI-dedicated MW × AI share / per-chip
effective power draw (chip × server overhead × PUE). Asks: "given the
AI-DC power capacity, how many H100-eq can it support?" Does not bind
in our base scenarios — power efficiency gains keep up with stock
growth.

## Data-center constraint

The DC-limited stock = AI-dedicated MW × `dc_packing_efficiency` /
per-chip effective power. Conceptually distinct from power because it
captures cooling, slot density, transformer/switchgear, and permitting
slack — not just raw grid-power MW. Binds throughout the
power_datacenter_bottleneck scenario.

> **Honest caveat:** in the current model, both power and DC
> constraints are derived from the same `ai_dc_mw` input scaled by
> different multipliers. They are conceptually distinct but
> mathematically coupled. A future refactor could split them into
> truly independent inputs (`grid_mw_available_for_ai` vs
> `commissioned_dc_slot_mw`); see `docs/supply_findings.md` §8.

## Binding constraint

The constraint that's actually limiting installed stock in a given year:
`argmin(chip_limit, power_limit, dc_limit, capex_limit)`. The supply
model emits `binding_constraint` as a categorical column per year per
scenario. The model's base case has capex binding 2024–2036, then chip.

## Allocation layer

The next component to be built. Splits annual `usable_compute_flop_year`
across training / inference / AI R&D / post-training / reserves, and
produces `largest_frontier_run_flop_by_year` as the bridge between
total annual compute and single-training-run compute.

## Largest-run concentration

The fraction of training compute (or of total usable compute) that
goes to the single largest training run in a year. A small but
critical parameter: changing it from 5% to 15% changes the implied
2030 frontier-run FLOP by ~3×. The allocation layer will model this
explicitly.

## Task horizon

A future quantity. The longest task duration (in human-hours) at which
an AI system performs reliably. Capability-mapping research from
METR and similar groups expresses progress as a doubling time of
the task horizon. Currently unmodeled in this project; the capability
layer will introduce it.
