# ai-economy-timelines

A scenario-based model of frontier AI compute. Two phases shipped, Phase 3 (allocation) is next.

- **Phase 1** — historical compute & spend baseline for frontier models, derived from the [Epoch AI](https://epoch.ai) "Notable AI Models" dataset. Log-linear fits, frontier-rule sensitivity, residual diagnostics.
- **Phase 2** — forward compute-capacity model 2024–2040: H100-equivalent shipments, installed stock with retirement, power / data-center / capex constraints, utilization derating, binding-constraint identification across four scenarios.

## Setup

```bash
uv sync
```

## Run

```bash
uv run phase1     # rebuild Phase 1 deliverables
uv run phase2     # rebuild Phase 2 deliverables
uv run pytest     # run the test suite
```

Both pipelines write to `outputs/charts/` and `outputs/tables/`; processed
datasets land in `data/processed/`.

## Structure

```
data/
  raw/                 Raw Epoch CSVs (immutable)
  processed/           Cleaned datasets; output of phase1/phase2
  assumptions/
    phase2_input_assumptions.yaml    Single source of truth for Phase 2 inputs
docs/
  phase1_scope.md
  phase1_findings.md   ← Phase 1 final memo
  phase2_scope.md
  phase2_initial_notes.md
  phase2_findings.md   ← Phase 2 final memo + Phase 3 handoff parameters
  data_dictionary.md
model/
  runtime.py           Shared paths, color maps, source-line strings
  data_cleaning.py     Phase 1 raw-data normalization
  frontier_filters.py  Phase 1 frontier-model rules (A/B/C)
  trend_fitting.py     Phase 1 log-linear fits
  charts.py            Phase 1 chart helpers
  fundamental_inputs.py   Phase 2 compute-capacity engine
pipelines/
  phase1.py            `uv run phase1` entry point
  phase2.py            `uv run phase2` entry point
scenarios/
  phase2_*.yaml        Four Phase 2 scenarios
tests/                 pytest suite
outputs/
  charts/              Final PNGs
  tables/              Fitted-trend / capacity / sensitivity CSVs
```

## Phase 1 headline (Rule A, 2018+)

| Metric | Annual × | Doubling | R² | n |
|---|---|---|---|---|
| Training compute (FLOP) | 5.97× | 4.7 mo | 0.84 | 113 |
| Training cost (2023 USD) | 4.89× | 5.2 mo | 0.72 | 74 |
| Cost per FLOP | 0.76× (~24%/yr decline) | — | 0.21 | 74 |

Full memo: `docs/phase1_findings.md`.

## Phase 2 headline (sourced base case)

| Scenario | 2024 (FLOP/yr) | 2040 (FLOP/yr) | CAGR | Binding 2030 |
|---|---|---|---|---|
| Baseline continuation | 3.97e+28 | 1.65e+31 | **45.7%/yr** | capex |
| Capex-rich | 4.37e+28 | 2.89e+31 | 50.1%/yr | capex |
| Chip-constrained | 3.83e+28 | 6.54e+30 | 37.9%/yr | chip |
| Power/DC-constrained | 3.50e+28 | 6.64e+30 | 38.8%/yr | datacenter |

Full memo + Phase 3 handoff parameters: `docs/phase2_findings.md`.
