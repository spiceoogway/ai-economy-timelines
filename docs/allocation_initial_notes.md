# Allocation Layer — Sprint 1 Initial Notes

**Date:** 2026-05-03
**Sprint goal:** working allocation layer producing
`largest_frontier_run_flop` from supply outputs across the 4×4 = 16
combined-scenario cross-product.

## What's in this sprint

- `data/assumptions/allocation_input_assumptions.yaml` — 4 scenarios × milestones (2024 / 2030 / 2040) × 9 parameters per milestone (6 bucket shares + 3 training-decomposition multipliers).
- `scenarios/allocation_*.yaml` — 4 registration files (display name, description, assumption_scenario reference). Same pattern as supply.
- `model/allocation_engine.py` — load / interpolate / validate, plus the projection pipeline (cross-product, allocate buckets, frontier-lab decomposition, largest-run estimate, historical comparison).
- `pipelines/allocation.py` — `uv run allocation`. Reads supply CSV + historical trend, runs engine, writes 5 tables + 6 charts.
- `pipelines/allocation_charts.py` — 6 chart helpers.
- `tests/test_allocation_engine.py` — 9 tests covering all 8 invariants from the scope plus a negative test on share validation.

## Headline numbers (base supply × base allocation)

| Year | Largest run (FLOP) | Share of total |
|---|---|---|
| 2024 | 1.39e+27 | 3.51% |
| 2030 | 2.39e+28 | 1.30% |
| 2040 | 6.93e+28 | 0.42% |

CAGR 2024→2040: **27.6% per year** for the largest single frontier run.
For comparison, the historical Rule A 2018+ extrapolation is **5.97×
per year** (497% CAGR). The historical extrapolation crosses through
the realistic allocation envelope around 2027–2028 and continues
skyward. By 2040 the historical extrapolation reaches ~1e+37 FLOP,
versus realistic allocation projections in the 1e+27 to 1e+29 range.

## Range across all 16 combined scenarios

The largest_run trajectory is dominated by allocation choice, not
supply choice. From `outputs/tables/allocation_scenario_summary.csv`:

| Combined scenario | 2024 | 2030 | 2040 | CAGR |
|---|---|---|---|---|
| capex_rich × training_race | 1.74e+27 | 1.53e+29 | 9.38e+29 | **48.1%/yr** |
| base × training_race | 1.58e+27 | 7.84e+28 | 5.34e+29 | 43.9%/yr |
| capex_rich × rnd_acceleration | 1.53e+27 | 4.40e+28 | 1.60e+29 | 33.7%/yr |
| base × rnd_acceleration | 1.39e+27 | 2.25e+28 | 9.13e+28 | 29.9%/yr |
| capex_rich × base | 1.53e+27 | 4.66e+28 | 1.22e+29 | 31.4%/yr |
| **base × base (headline)** | 1.39e+27 | 2.39e+28 | 6.93e+28 | **27.6%/yr** |
| chip_bottleneck × base | 1.34e+27 | 1.52e+28 | 2.75e+28 | 20.8%/yr |
| chip_bottleneck × inference_heavy | 9.52e+26 | 6.91e+27 | 7.84e+27 | 14.1%/yr |
| (... 8 more) | | | | |

The ratio of fastest (capex_rich × training_race, 48.1%/yr CAGR) to
slowest (chip_bottleneck × inference_heavy, 14.1%/yr CAGR) is
roughly 4× over 16 years, or ~50× by 2040 in absolute FLOP.

## Three observations worth flagging now

### 1. Allocation choice dominates supply choice for the largest-run trajectory.

In the cross-product chart (`outputs/charts/allocation_largest_frontier_run.png`),
the four allocation-scenario "color bands" stack vertically by ~0.7
OOM by 2040, while the four supply-scenario "marker variants" within
each color band only spread by ~0.3 OOM. This means: the political /
strategic question of *how* compute is allocated matters more for
frontier-run trajectories than the physical question of *how much*
compute exists in total.

### 2. The frontier-run share of total compute *falls* in every scenario.

This is the central allocation insight: even under the training-race
scenario where labs prioritize frontier runs, total usable compute
scales faster than any single training run can absorb. By 2040 the
largest run is < 4% of total compute even in the most concentrated
scenario, vs ~3.5% in 2024. The "compute is consumed by inference
serving" narrative holds across scenarios.

### 3. The historical Rule A 2018+ trend is unreproducible on supply fundamentals + reasonable allocation.

The vs-historical chart (`outputs/charts/allocation_vs_historical_training_compute.png`)
shows the historical extrapolation crosses *above* every allocation
projection by ~2027 and reaches ~1e+37 FLOP by 2040. No combination
of supply + allocation under our assumptions reproduces 5.97×/yr
single-run growth. This is what the orientation docs warned about,
now made concrete by an actual single-run forward projection. Three
honest readings:

- **The historical trend was already slowing.** Recent frontier
  models are clustered between 1e25 and 1e26 FLOP rather than
  continuing the 5.97× pace; the historical fit gives equal weight
  to the steeper 2018-2022 era.
- **Allocation parameters are conservative.** The training-race
  scenario at 35% training share + 65% frontier-lab share + 15%
  largest-run concentration is at the upper bound of plausible —
  but not implausible. If realistic concentration is closer to
  20-25%, the gap closes by ~1 OOM.
- **Supply fundamentals genuinely cap single-run growth.** Even
  capex_rich + training_race at 48.1%/yr CAGR is one full OOM/yr
  slower than the historical 5.97×/yr.

All three are probably partly true. Phase 4 (effective compute) and
Phase 5 (capability mapping) will reframe this from "single-run FLOP"
to "effective single-run training-equivalent FLOP" and may close some
of the apparent gap.

## What the next pass should do

Not in this sprint, but candidates for refinement:

1. **Source the allocation parameters.** Currently all values are
   `confidence: medium` from the upstream scope defaults. Hyperscaler
   10-Ks, lab disclosures, and academic estimates of the largest-run
   concentration parameter could move the central estimates and
   tighten the bounds.
2. **Add a fragmented-market scenario.** The scope offers
   `allocation_fragmented_market` as optional; could add as a 5th
   allocation scenario if cluster-contiguity becomes a bigger story.
3. **Time-vary the supply scenario weights.** Currently each combined
   scenario assumes the same supply scenario across all 17 years; a
   scenario where the binding constraint shifts mid-horizon would be
   more realistic.

## Open questions

1. **Should the largest-run concentration parameter be calibrated to
   2018-2024 backcast?** The historical Rule A 2018+ trend is
   observable; the allocation model should be able to reproduce
   the historical single-run trajectory in backcast. The current
   assumptions are forward-only; a backcast calibration would tighten
   the 2024 starting values.
2. **How should the cluster_contiguity_factor evolve?** Currently
   modeled as monotonically declining (geographic / cluster-size
   fragmentation grows). Could go the other way if frontier labs
   keep building larger dedicated campuses (Stargate-style).
3. **What's the inference / training split *within* a frontier lab?**
   We model frontier_lab_training_share as one number per scenario;
   in practice some labs (e.g. inference-heavy commercial) will have
   a very different split from others (e.g. capability-focused
   safety labs). A weighted-by-lab decomposition could be a future
   refinement.

## Recommended (provisional) effective-compute layer inputs

These will live in `docs/allocation_findings.md` once the memo is
finalized. Provisional from sprint 1:

- `largest_frontier_run_flop_by_year` — already emitted; the headline
  Phase 4 input.
- `training_compute_flop_year`, `ai_rnd_experiment_compute_flop_year`,
  `post_training_compute_flop_year`, `inference_compute_flop_year` —
  bucket-level totals.
- `frontier_run_share_of_total_compute` — for sensitivity testing.
- Recommended scenario envelope:
  - **Slow:** chip_bottleneck × inference_heavy (CAGR 14.1%)
  - **Base:** base × base (CAGR 27.6%)
  - **Fast:** capex_rich × training_race (CAGR 48.1%)
