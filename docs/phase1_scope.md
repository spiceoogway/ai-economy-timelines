# Phase 1 Scope

## Objective

Build a clean historical baseline for frontier AI model training compute and
estimated training cost.

The goal of Phase 1 is **not** to forecast AGI, capabilities, automation, or
the AI economy. The goal is to answer:

> Can we accurately reconstruct historical frontier-model compute and spending
> trends before using them as the foundation for forecasts?

Phase 1 should produce a reliable dataset, fitted historical curves, and
diagnostic charts that later phases can build on.

## Core research questions

1. How fast has frontier training compute grown historically?
2. How fast has estimated frontier training cost grown historically?
3. How much variation exists between labs, model types, and time periods?
4. What historical growth curve best fits frontier training compute?
5. What historical growth curve best fits frontier training spend?
6. How sensitive are these estimates to frontier-model selection rules?
7. What baseline assumptions should be carried into Phase 2?

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

1. `data/processed/frontier_models_historical.{parquet,csv}`
2. `docs/data_dictionary.md`
3. Charts in `outputs/charts/` (compute, cost, cost/FLOP, by-org, residuals)
4. `outputs/tables/phase1_trend_estimates.csv`
5. `docs/phase1_findings.md` memo

## Acceptance criteria

Phase 1 is complete when:

1. Clean model-level dataset with documented sources.
2. At least three explicit frontier-model filters.
3. Historical trend estimates for training compute, training cost, cost/FLOP.
4. Diagnostic charts showing fit quality and outliers.
5. Memo explaining assumptions, uncertainties, and Phase 2 handoff parameters.
