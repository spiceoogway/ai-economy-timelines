# ai-economy-timelines

Phase 1: Historical compute & spend baseline for frontier AI models.

This repo reconstructs historical frontier-model training compute and estimated
training cost from the [Epoch AI](https://epoch.ai) "Notable AI Models"
database, fits log-linear growth curves, and produces diagnostic charts.

The goal of Phase 1 is **not** forecasting capabilities, AGI timelines, or
the AI economy. It is a defensible empirical baseline that later phases can
build on. See `docs/phase1_scope.md`.

## Structure

```
data/
  raw/                  Raw Epoch CSV exports (immutable)
  processed/            Cleaned, frontier-flagged dataset
docs/
  phase1_scope.md       Phase 1 goals and acceptance criteria
  data_dictionary.md    Field definitions and source-to-schema mapping
  phase1_initial_notes.md   Sprint-1 working notes
  phase1_findings.md    Final memo (end of Phase 1)
notebooks/              Sequential analysis notebooks (01-05)
model/                  Reusable Python modules
  data_cleaning.py
  frontier_filters.py
  trend_fitting.py
outputs/
  charts/               Final PNGs
  tables/               Fitted-trend CSVs
```

## Setup

```bash
uv sync
uv run jupyter lab
```

## Data source

Epoch AI "Notable AI Models" database — public CSV download.
Retrieval date and column-mapping notes live in `docs/data_dictionary.md`.

## Phase 1 headline (Rule A, 2018+)

| Metric | Annual × | Doubling | R² | n |
|---|---|---|---|---|
| Training compute (FLOP) | 5.97× | 4.7 mo | 0.84 | 113 |
| Training cost (2023 USD) | 4.89× | 5.2 mo | 0.72 | 74 |
| Cost per FLOP | 0.76× (~24%/yr decline) | — | 0.21 | 74 |

Full memo with rule sensitivity, cost-variant sensitivity, and Phase 2
handoff parameters: `docs/phase1_findings.md`.

## Phase

Phase 1 only. Out of scope: capability forecasting, automation modeling,
revenue forecasting, chip supply, regulatory scenarios. Those come later.
