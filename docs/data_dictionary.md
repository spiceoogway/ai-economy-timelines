# Data Dictionary

## Source

- **Dataset**: Epoch AI "Notable AI Models" database
- **URL**: <https://epoch.ai/data/notable_ai_models.csv>
- **Retrieved**: 2026-05-02
- **Local copy**: `data/raw/epoch_notable_ai_models_raw.csv`

Two additional Epoch CSVs are pulled for cross-checks but not used directly:

- `data/raw/epoch_frontier_ai_models_raw.csv` (Epoch's own frontier subset)
- `data/raw/epoch_large_scale_ai_models_raw.csv` (large-scale subset)

The raw CSV has 1,011 model rows (47 columns) covering 1950–2026. The
processed dataset (`data/processed/frontier_models_historical.{csv,parquet}`)
preserves all 1,011 rows with the columns documented below plus the three
frontier flags.

## Field definitions

| Phase 1 column | Source column | Type | Notes |
|---|---|---|---|
| `model_id` | derived | string | `"<model_name> \| <organization> \| <date>"` |
| `model_name` | `Model` | string | unchanged |
| `organization` | `Organization` | string | normalized: `Google Deepmind`→`Google DeepMind`, `OpenAi`→`OpenAI`, `Meta AI`/`Meta Platforms`→`Meta` |
| `release_year` | derived | int | `Publication date`.year |
| `release_year_fractional` | derived | float | year + (day-of-year − 1) / 365.25 |
| `publication_date` | `Publication date` | datetime | parsed permissively; failures → NaT |
| `domain` | `Domain` | string | comma-separated tags (e.g. `Multimodal,Language,Vision`) |
| `training_compute_flop` | `Training compute (FLOP)` | float | total training FLOP |
| `training_compute_log10` | derived | float | `log10(training_compute_flop)` |
| `estimated_training_cost_usd` | `Training compute cost (2023 USD)` | float | Epoch's headline cost figure (2023 USD, inflation-adjusted) |
| `training_cost_log10` | derived | float | `log10(estimated_training_cost_usd)` |
| `training_cost_cloud_usd` | `Training compute cost (cloud)` | float | implied cloud-rental cost variant |
| `training_cost_upfront_usd` | `Training compute cost (upfront)` | float | implied upfront-hardware cost variant |
| `cost_per_flop` | derived | float | `estimated_training_cost_usd / training_compute_flop` |
| `cost_per_flop_log10` | derived | float | `log10(cost_per_flop)` |
| `parameters` | `Parameters` | float | parameter count |
| `dataset_tokens` | `Training dataset size (total)` | float | Epoch's "total" dataset size; units vary by domain (tokens, examples, hours) |
| `hardware_type` | `Training hardware` | string | e.g. `NVIDIA H100`, `TPU v4` |
| `hardware_quantity` | `Hardware quantity` | float | accelerator count |
| `training_duration_days` | derived | float | `Training time (hours) / 24` |
| `epoch_frontier_flag` | `Frontier model` | bool | Epoch's own frontier classification (NaN → False) |
| `epoch_confidence` | `Confidence` | string | `Confident`, `Likely`, `Speculative`, `Unknown` |
| `compute_estimate_quality` | derived | string | `high`/`medium`/`low` derived from `epoch_confidence`. NaN if no compute number. |
| `cost_estimate_quality` | derived | string | `high` if upfront cost present, `medium` if only cloud cost, `low` if only headline figure |
| `date_quality` | derived | string | `publication_date` if `Publication date` parsed, else `unclear` |
| `notability_criteria` | `Notability criteria` | string | Epoch's reason for inclusion |
| `organization_category` | `Organization categorization` | string | e.g. `Industry`, `Academia` |
| `country` | `Country (of organization)` | string |  |
| `source_url` | `Link` | string | upstream paper / blog / model card |
| `training_compute_notes` | `Training compute notes` | string | free text |
| `cost_notes` | `Compute cost notes` | string | free text |
| `frontier_rule_a` | derived | bool | top-10 by training compute within trailing 1-year window of release |
| `frontier_rule_b` | derived | bool | top model by compute per organization per calendar year |
| `frontier_rule_c` | derived | bool | `training_compute_flop ≥ 1e23` |
| `frontier_any` | derived | bool | `rule_a OR rule_b OR rule_c` |

## Key derived definitions

### Training compute
Total floating-point operations performed during pretraining of the model,
as estimated by Epoch (often reverse-engineered from architecture +
parameters + tokens + epochs, sometimes from disclosed run details).
Stored in absolute FLOP — typical 2024 frontier models are 1e25–1e26.

### Estimated training cost (USD)
Epoch's headline `Training compute cost (2023 USD)` field, inflation-
adjusted. This is the *implied training-run cost*, not total R&D spend.
We deliberately keep `cloud` and `upfront` variants separate because they
encode very different assumptions about hardware utilization and amortization.

### Cost per FLOP
`estimated_training_cost_usd / training_compute_flop`. Sensitive to which
of the three cost variants is used — Phase 1 uses the headline 2023-USD
figure for trend fits, with sensitivity tests against the other two
deferred to a later sprint.

### Frontier model
There is no neutral definition. Phase 1 uses **three** independent rules
plus Epoch's own flag for cross-comparison:

- **Rule A (top-10 in window)**: among the highest-compute models released
  in the 1-year window ending at this model's release. Captures
  "frontier-at-release."
- **Rule B (top per org per year)**: the highest-compute model from each
  organization in each calendar year. Captures lab-level frontiers.
- **Rule C (compute threshold)**: `training_compute_flop ≥ 1e23`. Round
  threshold matching some compute-governance frameworks.
- **Epoch flag**: Epoch's curated `Frontier model` boolean.

Trend-rate sensitivity to rule choice is one of the central diagnostics.

### Confidence flags
Epoch's `Confidence` column rates how well-substantiated the compute
estimate is. We map it as:

| Epoch | Phase 1 |
|---|---|
| Confident | high |
| Likely | medium |
| Speculative | low |
| Unknown | low |

If `training_compute_flop` is missing entirely, `compute_estimate_quality`
is `NA`.

## Transformations applied

```python
training_compute_log10 = log10(training_compute_flop)
training_cost_log10    = log10(estimated_training_cost_usd)
cost_per_flop          = estimated_training_cost_usd / training_compute_flop
cost_per_flop_log10    = log10(cost_per_flop)
training_duration_days = training_time_hours / 24
release_year_fractional = year + (day_of_year - 1) / 365.25
```

Organization normalization is intentionally minimal — we do not collapse
parent/sub relationships (e.g. DeepMind vs Google DeepMind), since
Epoch's labels track the org at publication time and merging them would
erase a real signal.
