# Phase 1 — Sprint 1 Initial Notes

**Date:** 2026-05-02
**Sprint goal:** first working historical baseline of frontier training compute.

## What's in this sprint

- Repo + Python env scaffolded (`uv`, `pandas`, `numpy`, `statsmodels`, `matplotlib`).
- Raw Epoch CSVs pulled to `data/raw/`.
- Cleaning + frontier-flagging + log-linear fitting modules in `model/`.
- Processed dataset at `data/processed/frontier_models_historical.{csv,parquet}` (1,011 rows × 35 cols).
- First chart: `outputs/charts/frontier_training_compute_over_time.png`.
- First trend table: `outputs/tables/initial_compute_growth_estimates.csv`.

## Data quality observations

- **1,011 notable models, 521 with training compute, 179 with training cost.**
  Compute coverage is strong post-2018 (≥30/yr through 2025); cost coverage
  is much sparser and will require careful handling in the cost sprint.
- **Epoch's `Frontier model` flag is set for only 123 rows.** It is more
  conservative than any of our three rules — useful as a sanity benchmark.
- **2026 partial year:** only 2 rows have known compute so far; trend fits
  that include 2026 are slightly tilted by recent disclosures and should be
  read with that caveat.
- **Long pre-2010 tail:** dozens of pre-deep-learning systems (perceptrons,
  early reinforcement learners) with very small FLOP counts. Including them
  in a single linear fit pulls the slope down — this is why the 2018+ window
  produces a much steeper slope than the full window.

## Headline numbers (sprint 1)

From `outputs/tables/initial_compute_growth_estimates.csv`:

| Window | Rule | n | Annual × | Doubling | R² |
|---|---|---|---|---|---|
| 2018+ | all models | 370 | 6.30× | 4.5 mo | 0.50 |
| 2018+ | Rule A (top-10) | 113 | 5.97× | 4.7 mo | 0.84 |
| 2018+ | Rule B (top/org/yr) | 264 | 6.38× | 4.5 mo | 0.46 |
| 2018+ | Rule C (≥1e23 FLOP) | 137 | 2.00× | 12.0 mo | 0.30 |
| Full | all models | 521 | 2.12× | 11.1 mo | 0.76 |
| Full | Rule A | 245 | 2.14× | 10.9 mo | 0.83 |
| Full | Epoch flag | 113 | 2.05× | 11.6 mo | 0.89 |

**Two early findings worth noting:**

1. **Frontier definition does change the answer.** In the 2018+ window
   the implied annual growth multiplier ranges from ~2.0× (Rule C) to ~6.4×
   (Rule B). Rule C's slow rate is a selection effect: once you condition
   on FLOP ≥ 1e23 you have already truncated the lower tail, so the
   remaining variation through time is much smaller.
2. **Rule A 2018+ has the cleanest fit (R²=0.84) and the most defensible
   reading.** Headline candidate for the Phase 2 base case: ~6× per year,
   doubling every ~5 months.

## Outliers / weird cases worth investigating

- A handful of pre-2010 entries jump several OOM above neighbors — these
  are likely AlphaGo predecessors and game-playing RL systems where the
  compute estimate aggregates self-play (lots of experience, low parameter
  count). Worth checking whether they should sit in the same trend as
  modern pretraining FLOP.
- 2024–2026 cluster around 1e25–1e26 with very tight grouping — consistent
  with reports of frontier-lab convergence on similar compute budgets.
- Rule B picks up many small-lab models with relatively low compute,
  which depresses its R². Not a bug — it's the expected behavior of the
  rule and a good demonstration of why we run three definitions.

## Follow-up sprints (deferred from sprint 1)

In rough priority order:

1. **Cost trend fits** (`04_cost_trend_analysis.ipynb`). Same regression
   structure on `estimated_training_cost_usd`, plus sensitivity across
   the headline / cloud / upfront cost variants.
2. **Cost-per-FLOP trend.** Should be strongly negative. Hardware-era
   diagnostics (V100 vs A100 vs H100/Blackwell era).
3. **Residual diagnostics by year and by organization.**
   `outputs/charts/residuals_compute_trend.png`,
   `outputs/charts/residuals_cost_trend.png`.
4. **Organization-level breakouts** —
   `outputs/charts/frontier_compute_by_organization.png` and
   `outputs/charts/frontier_cost_by_organization.png`.
5. **Hardware / cluster descriptive timeline** (no model, just charts +
   tables).
6. **Final memo** `docs/phase1_findings.md` with explicit Phase 2
   handoff parameters (base / fast / slow compute and cost growth
   assumptions, recommended historical window, recommended frontier rule).

## Open questions for Phase 1

- **Should Rule A use a top-N percentile rather than a fixed N?** Top-10
  picks up smaller frontier sets in 2010 and oversamples them in 2024
  when many more models are released per year. A fractional rule would
  be more stable.
- **What weighting (if any) for the regression?** Currently OLS. We may
  want WLS using `compute_estimate_quality` as inverse-variance.
- **Cost in 2023 USD vs nominal:** Epoch already inflation-adjusts — but
  the cost-per-FLOP trend will look different against nominal hardware
  prices, which is what cluster-builders actually paid. Decision to be
  documented in the cost-trend sprint.
- **Pre-2018 data inclusion**: keep as a separate "long-run" comparison
  fit; do not mix into the Phase 2 base case.

## Recommended (provisional) Phase 2 inputs

These are not final — final values will live in `phase1_findings.md` once
the cost and residual sprints are complete. Provisional from sprint 1:

- Recommended historical window: **2018-01-01 to last full quarter of data**.
- Recommended frontier rule: **Rule A (top-N at release)** for the base case.
- Provisional base compute growth: **~6× per year, doubling ~5 months**.
- Provisional fast / slow bounds: **4×–9× per year** (rough; tighten via
  bootstrap CIs in a later sprint).
