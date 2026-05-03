# Executive Summary

## The model in one sentence

A scenario-based model of frontier AI compute that combines an empirical historical baseline (what single frontier training runs *did* historically) with a forward supply-capacity projection (how much total AI compute *could exist* per year through 2040), with downstream allocation, capability, and economic-feedback layers planned next.

## What has been built

| Component | Purpose | Status |
|---|---|---|
| **Historical baseline** | Reconstruct historical frontier-model training compute and estimated training cost from Epoch's "Notable AI Models" dataset; fit log-linear curves with rule and cost-variant sensitivity | ✓ complete |
| **Supply capacity model** | Project annual usable global AI compute capacity 2024–2040 from chips, power, data centers, capex, and utilization, under four scenarios | ✓ complete |
| **Allocation layer** | Split usable compute into training, inference, AI R&D, post-training, reserves; estimate the largest single frontier training run | ✗ next |
| **Effective compute** | Convert raw frontier-run FLOP into algorithmically-adjusted effective compute | ✗ future |
| **Capability mapping** | Map effective compute to task horizons / benchmark performance / automation levels | ✗ future |
| **Projection engine** | Probabilistic projections combining all above | ✗ future |
| **Economy feedback** | Revenue / reinvestment loops back into supply-side capex | ✗ future |

## What the model currently projects

- **Historical training-compute and training-cost growth rates** under three frontier-model definitions and full / 2018+ time windows (`outputs/tables/historical_trend_estimates.csv`).
- **Annual usable AI compute capacity** by scenario, 2024–2040, with per-year breakdowns of installed H100-equivalent stock, power-limited stock, DC-limited stock, capex-limited stock, and the binding constraint (`outputs/tables/supply_fundamental_inputs_by_year.csv`).
- **Capex required vs available** per scenario per year.
- **Sensitivity bands** on the three highest-leverage supply inputs (shipments, AI-DC capacity, capex).

## What the model does not yet project

- The size of the **largest single frontier training run** in any future year. The supply-capacity model gives total annual usable compute; converting that into "the largest training run" requires an allocation layer that is **not yet built**. This is the single most important gap.
- Algorithmically-adjusted **effective** compute (after architectural / data-quality / post-training improvements).
- AI **capabilities** (task horizons, benchmark scores, automation levels).
- AI-economy feedback loops (revenue → reinvestment → more supply).
- Geography splits — currently all global aggregate.

## Main findings so far

- **Historical (Rule A 2018+):** frontier training compute grew **~5.97× per year** (R²=0.84, n=113), doubling every ~4.7 months. Frontier training cost grew **~4.89× per year** (R²=0.72, n=74). Cost per FLOP fell **~24% per year**.
- **Supply (sourced base case):** total usable AI compute grows **~45.7% per year** 2024→2040 (CAGR), reaching **~1.65e+31 FLOP/year** by 2040. **Capex** is the binding constraint 2024–2036; **chips** become binding 2037–2040.
- **Headline gap:** the historical 5.97×/yr rate is **roughly 10 OOM faster** than even the most aggressive supply scenario (capex-rich, ~50%/yr) by 2040. The historical trend measures one frontier training run; the supply model measures all global AI compute. Reconciling them is the allocation layer's job.

## Main conceptual caution

> **The historical baseline measures one training run. The supply-capacity model measures all global AI compute. They are not the same quantity, and treating them as comparable trends is the most common reading mistake.**

The historical 5.97×/yr is the growth rate of the largest single training run released in each window; the supply 45.7%/yr is the growth rate of total annual usable compute across every chip on earth. Frontier runs use a *share* of total compute, and that share has likely been growing — which is why one trend can outpace the other for a while. Fixing this dependency is exactly what the allocation layer exists to do.

## What comes next

**The allocation layer.** Split total usable compute into training / inference / AI R&D / post-training / reserves, estimate the **largest-frontier-run share** by year, and emit `largest_frontier_run_flop_by_year` as the bridge between this project's supply estimates and the historical-baseline frontier-run trend.

For details on each of these points: `docs/model_map.md` (architecture), `docs/model_state.md` (build status), `docs/output_guide.md` (output interpretation), `docs/historical_findings.md` and `docs/supply_findings.md` (component memos).
