# Allocation Layer — Findings

**Author:** automated analysis pipeline
**Date:** 2026-05-03
**Status:** Allocation layer complete. Effective-compute handoff parameters at the bottom.

---

## 1. Summary

Under sourced supply assumptions and base allocation parameters, the
**largest single frontier training run grows ~27.6% per year**
(2024→2040), reaching ~6.9e+28 FLOP by 2040. Across the 16 combined
supply × allocation scenarios, the headline trajectory ranges from
**14.1%/yr** (chip-bottleneck × inference-heavy) to **48.1%/yr**
(capex-rich × training-race) — a roughly **50× spread in absolute
2040 FLOP**.

The historical Rule A 2018+ trend (5.97×/yr per Phase 1) is
**unreproducible on supply fundamentals + reasonable allocation**.
The historical extrapolation crosses through the entire allocation
envelope around 2027–2028 and reaches ~1e+37 FLOP by 2040, vs
realistic projections in the 1e+27 to 1e+29 range.

The frontier-run share of total compute **falls in every scenario**
from ~3.5% (2024) to <4% even in the most concentrated case by 2040.
This is the central allocation insight: total usable compute scales
faster than any single training run can absorb, regardless of
allocation choice.

## 2. Why allocation was needed

The historical baseline measures *single training-run FLOP*; the
supply capacity model measures *total annual usable compute*. These
are different quantities, and comparing them directly was the
"central reading mistake" flagged throughout the orientation docs.

The allocation layer bridges them by modeling **what share of total
usable compute goes to the single largest training run**, year by
year, scenario by scenario. With this in hand, the supply trajectory
can be translated into a forward single-run trajectory and compared
apples-to-apples with the historical trend.

The headline output, `largest_frontier_run_flop`, is the first
forward-looking quantity in this project that's directly comparable
with the historical Rule A 2018+ frontier-run trend.

## 3. Allocation assumptions

Source: `data/assumptions/allocation_input_assumptions.yaml`. Four
scenarios at three milestone years, linearly interpolated.

### Bucket shares (sum to 1.0 at every milestone)

| Scenario | Year | Inference | Training | AI R&D | Post-train | Safety | Reserved |
|---|---|---|---|---|---|---|---|
| base | 2024 | 0.55 | 0.30 | 0.08 | 0.04 | 0.01 | 0.02 |
| base | 2030 | 0.60 | 0.24 | 0.10 | 0.04 | 0.01 | 0.01 |
| base | 2040 | 0.65 | 0.18 | 0.10 | 0.04 | 0.01 | 0.02 |
| inference_heavy | 2040 | 0.78 | 0.10 | 0.06 | 0.03 | 0.01 | 0.02 |
| training_race | 2040 | 0.45 | 0.35 | 0.12 | 0.04 | 0.02 | 0.02 |
| rnd_acceleration | 2040 | 0.55 | 0.18 | 0.20 | 0.04 | 0.01 | 0.02 |

### Training-pool decomposition

| Scenario | Year | frontier_lab_training_share | largest_run_concentration | cluster_contiguity_factor |
|---|---|---|---|---|
| base | 2024 | 0.65 | 0.20 | 0.90 |
| base | 2030 | 0.60 | 0.10 | 0.90 |
| base | 2040 | 0.55 | 0.05 | 0.85 |
| training_race | 2040 | 0.65 | 0.15 | 0.95 |
| inference_heavy | 2040 | 0.50 | 0.03 | 0.80 |
| rnd_acceleration | 2040 | 0.55 | 0.07 | 0.80 |

All values are flagged `confidence: medium` and source `scope_defaults`.
Refinement targets in §8.

## 4. Compute by bucket

Under base supply × base allocation, the 6 buckets at 2024 / 2030 / 2040:

| Bucket | 2024 (FLOP/yr) | 2030 (FLOP/yr) | 2040 (FLOP/yr) |
|---|---|---|---|
| Inference | 2.18e+28 | 1.10e+30 | 1.07e+31 |
| Training | 1.19e+28 | 4.42e+29 | 2.96e+30 |
| AI R&D experiment | 3.18e+27 | 1.84e+29 | 1.65e+30 |
| Post-training | 1.59e+27 | 7.37e+28 | 6.58e+29 |
| Safety / eval | 3.97e+26 | 1.84e+28 | 1.65e+29 |
| Reserved / idle / fragmented | 7.94e+26 | 1.84e+28 | 3.29e+29 |
| **Total usable** | **3.97e+28** | **1.84e+30** | **1.65e+31** |

Inference dominates throughout. Training holds at ~30% in 2024 but
shrinks in absolute share toward 2040, even though the absolute
training-compute number grows ~250× over the horizon.

Chart: `outputs/charts/allocation_compute_by_bucket.png`.

## 5. Largest frontier training-run projections

Under each combined scenario, the largest single frontier training
run by year. Sorted by 2040 value (highest first):

| Combined scenario | 2024 | 2030 | 2040 | CAGR |
|---|---|---|---|---|
| capex_rich × training_race | 1.74e+27 | 1.53e+29 | 9.38e+29 | **48.1%/yr** |
| base × training_race | 1.58e+27 | 7.84e+28 | 5.34e+29 | 43.9%/yr |
| power_dc_bot × training_race | 1.39e+27 | 4.03e+28 | 2.15e+29 | 37.0%/yr |
| chip_bot × training_race | 1.53e+27 | 4.99e+28 | 2.12e+29 | 36.1%/yr |
| capex_rich × rnd_acceleration | 1.53e+27 | 4.40e+28 | 1.60e+29 | 33.7%/yr |
| capex_rich × base | 1.53e+27 | 4.66e+28 | 1.22e+29 | 31.4%/yr |
| base × rnd_acceleration | 1.39e+27 | 2.25e+28 | 9.13e+28 | 29.9%/yr |
| **base × base** | 1.39e+27 | 2.39e+28 | 6.93e+28 | **27.6%/yr** |
| power_dc_bot × rnd_acceleration | 1.23e+27 | 1.16e+28 | 3.68e+28 | 23.7%/yr |
| chip_bot × rnd_acceleration | 1.34e+27 | 1.44e+28 | 3.62e+28 | 22.9%/yr |
| capex_rich × inference_heavy | 1.09e+27 | 2.12e+28 | 3.47e+28 | 24.2%/yr |
| power_dc_bot × base | 1.23e+27 | 1.23e+28 | 2.79e+28 | 21.6%/yr |
| chip_bot × base | 1.34e+27 | 1.52e+28 | 2.75e+28 | 20.8%/yr |
| base × inference_heavy | 9.88e+26 | 1.09e+28 | 1.98e+28 | 20.6%/yr |
| power_dc_bot × inference_heavy | 8.69e+26 | 5.58e+27 | 7.97e+27 | 14.9%/yr |
| chip_bot × inference_heavy | 9.52e+26 | 6.91e+27 | 7.84e+27 | **14.1%/yr** |

Headline: range is 14.1% → 48.1% CAGR; absolute 2040 spread is
~50×. Allocation choice (color in the chart) dominates supply choice
(marker) — the four allocation scenarios stack ~0.7 OOM apart by
2040, while supply variation within an allocation accounts for
~0.3 OOM.

Chart: `outputs/charts/allocation_largest_frontier_run.png`.

## 6. Historical comparison

The vs-historical chart
(`outputs/charts/allocation_vs_historical_training_compute.png`)
overlays the historical Rule A 2018+ extrapolation (5.97×/yr,
rebased to 1e+25 FLOP at 2024) on all 16 allocation projections.

Key observations:

- **Crossover ~2027–2028:** the historical extrapolation reaches the
  upper edge of the allocation envelope (training_race scenarios)
  around 2027–28 and rapidly leaves it behind.
- **2030 gap:** historical extrapolation ~4.5e+29 FLOP vs
  best-case allocation ~1.5e+29 FLOP (capex_rich × training_race).
  Roughly 3× gap.
- **2040 gap:** historical extrapolation ~1e+37 FLOP vs best-case
  allocation ~1e+30 FLOP. Roughly **7 OOM gap**.

The `gap_ratio` column in
`outputs/tables/allocation_vs_historical_trend.csv` quantifies this
year-by-year for every combined scenario.

> **Reading note:** the historical trend is *descriptive* — it fits
> the 2018–2024 frontier-model corpus. It is not a forecast. The
> allocation model is a *forward projection* on supply fundamentals
> and assumed allocation choices. The "gap" represents three
> things blended together: (a) the historical trend was already
> slowing; (b) our allocation parameters may be conservative; (c)
> supply fundamentals genuinely cap single-run growth. Phase 4
> (effective compute) and Phase 5 (capability mapping) will reframe
> this from raw FLOP to effective FLOP and may close some of the
> apparent gap.

## 7. Scenario sensitivity

Sensitivity by parameter, holding all else at base × base:

- **Allocation scenario** (largest effect): swapping base
  allocation for training_race raises 2040 largest_run by ~7.7×;
  swapping for inference_heavy reduces it by ~3.5×.
- **Supply scenario** (smaller effect within an allocation): swapping
  base supply for capex_rich raises 2040 largest_run by ~1.8×;
  swapping for chip_bottleneck reduces by ~2.5×.
- **Implied joint range** across all 16 scenarios: 50× in absolute
  2040 FLOP terms.

Conclusion: allocation choice dominates supply choice for
single-frontier-run projections. This is the inverse of what
intuition might suggest if you only think of the model as
"supply-constrained" — once supply is generous (any of the four
supply scenarios except chip_bottleneck have ample compute by
2030), the binding question becomes how that compute is *used*,
not how much exists.

## 8. Key uncertainties

1. **largest_run_concentration is the highest-leverage unsourced
   parameter.** A swing from 0.10 to 0.20 (within plausible range)
   changes 2040 largest_run by 2× linearly. Currently flagged
   `medium` confidence; the actual historical concentration
   parameter is debated — top-10% of frontier-lab compute? top
   single 5%? Sensitivity analysis would tighten this.
2. **frontier_lab_training_share is the second-highest leverage
   parameter.** Currently 0.55–0.70 across scenarios. The actual
   share depends on the definition of "frontier lab" (3 labs? 10?
   30?) which the model doesn't separately address.
3. **Allocation parameters are not backcast-calibrated.** The
   2024 starting values were chosen to match plausible 2024
   reality but were not formally fit against the historical
   2018–2024 frontier-model record. A backcast calibration
   could tighten the 2024 anchor.
4. **No correlation across parameters.** If allocation is
   *correlated* with supply (e.g. chip_bottleneck → forced
   higher concentration to make any training run viable),
   our scenario joint is too uniform. Sensitivity to the
   joint structure is unmodeled.
5. **No fragmentation in the cross-product.** Each combined
   scenario assumes one supply scenario across all 17 years;
   real-world supply may shift binding constraints
   mid-horizon.
6. **Historical Rule A 2018+ trend may overweight 2018-2022.**
   The Rule A trend gives equal weight to the steeper early-deep-
   learning era; recent (2023-2026) frontier models have been
   clustering between 1e25 and 1e26 FLOP rather than continuing
   the historical 5.97× pace. Re-fitting Rule A on 2022+ data
   would give a slower trend that the allocation projections
   could plausibly catch up to.

## 9. Effective-compute layer handoff parameters

These are the explicit handoff parameters for the effective-compute
layer (Phase 4 in the upstream spec; renamed to "the effective-
compute layer" in this project's docs).

```
=== Largest frontier run by year (FLOP) ===

Year   Slow envelope         Base case             Fast envelope
       (chip_bot ×           (base × base)         (capex_rich ×
        inference_heavy)                            training_race)
2024   9.52e+26              1.39e+27              1.74e+27
2025   2.55e+27              4.74e+27              5.71e+27
2026   4.14e+27              9.27e+27              1.18e+28
2027   5.19e+27              1.31e+28              1.83e+28
2030   6.91e+27              2.39e+28              1.53e+29
2035   7.31e+27              4.16e+28              4.18e+29
2040   7.84e+27              6.93e+28              9.38e+29

Read full CSV: outputs/tables/allocation_largest_frontier_run.csv

=== Recommended effective-compute layer envelope ===
Use base supply × base allocation as the central case.
Use chip_bottleneck × inference_heavy as the slow / pessimistic floor.
Use capex_rich × training_race as the fast / optimistic ceiling.
Use base × inference_heavy and capex_rich × base as alternative-stress
cases (capacity exists but allocation favors / disfavors training).

=== Bucket-level annual compute by year (base × base, FLOP/yr) ===
2024: inference 2.18e+28, training 1.19e+28, ai_rnd 3.18e+27,
      post_training 1.59e+27, safety 3.97e+26, reserved 7.94e+26
2030: inference 1.10e+30, training 4.42e+29, ai_rnd 1.84e+29,
      post_training 7.37e+28, safety 1.84e+28, reserved 1.84e+28
2040: inference 1.07e+31, training 2.96e+30, ai_rnd 1.65e+30,
      post_training 6.58e+29, safety 1.65e+29, reserved 3.29e+29

=== Frontier run share of total compute (base × base) ===
2024: 3.51%
2030: 1.30%
2040: 0.42%

The share trajectory is nearly identical across supply scenarios
(within an allocation scenario) because supply changes both
numerator and denominator proportionally. The only allocation
with materially different share is training_race, which keeps
~3-4% through 2040.
```

### Known weaknesses (carry forward)

- 7-OOM 2040 gap to historical extrapolation is real — the
  effective-compute layer needs to address whether this is
  capability-relevant or whether algorithmic / architectural
  improvements close most of it.
- All allocation parameters are `confidence: medium` from upstream
  scope defaults; sourcing pass needed.
- No backcast calibration; the 2024 anchor is plausible but
  unverified.
- 16 combined scenarios is a lot; downstream layers should pick a
  small subset (slow / base / fast) rather than carry all 16.

## 10. Open questions

1. **What's the right way to compare against the historical trend?**
   Options: (a) compare raw FLOP (current approach, shows large
   gap); (b) compare effective FLOP after Phase 4 adjustments;
   (c) re-fit the historical trend on 2022+ data only and compare
   against that. All three are defensible; the project should
   pick one as the headline.
2. **Should the cluster_contiguity_factor be supply-scenario-
   dependent?** Currently allocation-only. Under the
   power_datacenter_bottleneck supply scenario, contiguity should
   plausibly fall (more fragmentation when DC slots are scarce).
   Joint structure would tighten the projection.
3. **Is the largest-run concentration parameter the right
   handle?** An alternative: model the *number* of frontier-run-
   class training runs per year (currently implicit in
   1 / largest_run_concentration). Could be more interpretable.
4. **How should the effective-compute layer use these envelopes?**
   The handoff is 16 scenarios; the next layer probably wants 3
   (slow / base / fast). Recommended subset above; revisit when
   building the effective-compute layer.

---

## Appendix: deliverable checklist

| Spec deliverable | File | Status |
|---|---|---|
| Allocation assumptions YAML | `data/assumptions/allocation_input_assumptions.yaml` | ✓ |
| 4 scenario YAMLs | `scenarios/allocation_*.yaml` | ✓ |
| Engine module | `model/allocation_engine.py` | ✓ |
| Pipeline | `pipelines/allocation.py` | ✓ |
| Chart helpers | `pipelines/allocation_charts.py` | ✓ |
| 6 charts | `outputs/charts/allocation_*.png` | ✓ |
| 5 tables | `outputs/tables/allocation_*.csv` | ✓ |
| Tests | `tests/test_allocation_engine.py` | ✓ (9/9 passing) |
| Initial notes | `docs/allocation_initial_notes.md` | ✓ |
| Findings memo | `docs/allocation_findings.md` | ✓ (this file) |
| Scope section | `docs/scope.md` §3 | ✓ |
| README updated | `README.md` | ✓ |
| Orientation docs updated | `docs/{model_state,model_map,output_guide,component_contracts}.md` | ✓ |
