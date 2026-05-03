# Historical Baseline — Findings

**Author:** automated analysis pipeline
**Date:** 2026-05-02
**Status:** Historical baseline complete. Supply-capacity handoff parameters at the bottom.

---

## 1. Summary

Under the recommended **Frontier Rule A (top-10 by training compute at
release), 2018+ window**, the historical record from Epoch AI says:

| Metric | Annual multiplier | Doubling | R² | n |
|---|---|---|---|---|
| Training compute (FLOP) | **5.97×** | **4.7 mo** | 0.84 | 113 |
| Training cost (2023 USD) | **4.89×** | **5.2 mo** | 0.72 | 74 |
| Cost per FLOP (2023 USD/FLOP) | **0.76×** | n/a (decline) | 0.21 | 74 |

In plain English: from 2018 through early 2026, frontier training runs grew
by roughly **6× per year in raw compute** and **5× per year in inflation-
adjusted dollars**, while the **price per training FLOP fell ~24%/yr**.

The single most important historical-baseline caveat is that these numbers are
**moderately sensitive to frontier definition and very sensitive to cost
variant.** Sections 6–8 quantify both.

---

## 2. Data sources

- **Primary:** Epoch AI "Notable AI Models" CSV
  (<https://epoch.ai/data/notable_ai_models.csv>), retrieved **2026-05-02**.
  1,011 model rows, 1950–2026.
- **Cross-checks:** Epoch's `frontier_ai_models.csv` and
  `large_scale_ai_models.csv` (downloaded but not used in headline fits;
  Epoch's own frontier subset is replicated in our `epoch_frontier_flag`
  column).
- **Local snapshot:** `data/raw/epoch_*.csv` (immutable).
- **Processed dataset:** `data/processed/historical_models.{csv,parquet}` (1,011 rows × 35 cols).

Mappings from Epoch column names to historical-baseline schema names: `docs/data_dictionary.md`.

---

## 3. Inclusion criteria

- **All 1,011 notable models retained** in the processed dataset (full row preservation).
- For **trend fits**, rows are dropped only when the relevant `y` column is missing.
- **Compute coverage:** 521 / 1,011 models have a known `training_compute_flop`. Coverage is strong post-2018 (≥30/year through 2025).
- **Cost coverage** is sparser: 179 models with the headline 2023-USD cost figure, 33 with explicit upfront cost, 25 with explicit cloud-rental cost.
- **Date quality:** 1,007 / 1,011 rows have a parseable publication date.
- **Confidence flags:** Epoch's `Confidence` field is mapped to `compute_estimate_quality` (high / medium / low).

---

## 4. Frontier definitions

We use **three independent rules plus Epoch's own flag** as a sanity check.
There is no neutral definition of "frontier" and treating any single rule as
authoritative is precisely the kind of unforced error this project is trying
to avoid.

| Rule | Definition | n flagged (full) | n flagged (2018+) |
|---|---|---|---|
| **A** | Top 10 by training compute within the 1-year window ending at release | 245 | 113 |
| **B** | Highest-compute model per organization per calendar year | 378 | 264 |
| **C** | `training_compute_flop ≥ 1e23` | 137 | 137 |
| (Epoch) | Epoch's curated `Frontier model` boolean | 123 | — |

Rule C is the most restrictive but also the most fragile — by truncating
the lower tail it removes most within-year variation, which collapses both
its slope estimate and its R².

---

## 5. Historical compute trend

Full table: `outputs/tables/historical_trend_estimates.csv`. Compute rows below.

| Window | Rule | n | ×/yr | Doubling (mo) | R² |
|---|---|---|---|---|---|
| 2018+ | all models | 370 | 6.30 | 4.5 | 0.50 |
| 2018+ | A (top-10) | 113 | **5.97** | **4.7** | **0.84** |
| 2018+ | B (top/org/yr) | 264 | 6.38 | 4.5 | 0.46 |
| 2018+ | C (≥1e23) | 137 | 2.00 | 12.0 | 0.30 |
| Full | all models | 521 | 2.12 | 11.1 | 0.76 |
| Full | A | 245 | 2.14 | 10.9 | 0.83 |
| Full | B | 378 | 2.02 | 11.9 | 0.75 |
| Full | Epoch flag | 113 | 2.05 | 11.6 | **0.89** |

**Headline reading:** the modern (2018+) frontier-compute trend is **~6×
per year** under Rule A or B and converges with the all-models trend. The
long-run trend (1950–2026) is **~2× per year**. The two regimes are real and
visible in the chart `outputs/charts/historical_compute_over_time.png`.

Rule C's 2× answer for 2018+ is a **selection artifact** rather than a
disagreement — once you require ≥1e23 FLOP, the bottom of the post-2018
distribution disappears and you are left fitting a shorter dynamic range.
Treat it as an upper-bound floor, not a "slow" estimate.

---

## 6. Historical cost trend

| Window | Rule | n | ×/yr | Doubling (mo) | R² |
|---|---|---|---|---|---|
| 2018+ | all models | 155 | 3.13 | 7.3 | 0.27 |
| 2018+ | A | 74 | **4.89** | **5.2** | **0.72** |
| 2018+ | B | 121 | 3.02 | 7.5 | 0.23 |
| 2018+ | C | 51 | 3.03 | 7.5 | 0.50 |
| Full | A | 98 | 3.16 | 7.2 | 0.73 |
| Full | Epoch flag | 56 | 3.28 | 7.0 | **0.91** |

**Headline cost reading:** under Rule A 2018+, frontier training costs grew
**~5× per year**, doubling about every 5 months. Under Epoch's own flag the
fit is even cleaner (R² = 0.91) at **~3.3× per year**, doubling ~7 months.

Note the spread: 3× to 5×. We'll treat ~4× as the central estimate.

Chart: `outputs/charts/historical_cost_over_time.png`.

### Cost variant sensitivity (historical-baseline critical finding)

Epoch publishes three cost columns. Under **Rule A 2018+**, the same
trend looks very different depending on which one you fit:

| Cost variant | ×/yr | Doubling (mo) | R² | n |
|---|---|---|---|---|
| Headline (2023 USD) | **4.89** | **5.2** | 0.72 | 74 |
| Cloud-rental | 3.41 | 6.8 | 0.85 | 22 |
| Upfront-hardware | 2.49 | 9.1 | 0.84 | 27 |

**The headline figure grows almost twice as fast as the upfront-hardware
figure.** This is not noise — it is a real divergence:

- **Upfront cost** captures the price of the chips actually installed.
  Hardware prices (especially per-FLOP) have fallen, so total upfront
  cost grows more slowly than total compute.
- **Cloud-rental cost** is what you'd pay a hyperscaler at posted rates;
  it is closer to opportunity cost.
- **Headline 2023 USD** is Epoch's blended figure, closest to cloud-rental
  but with broader coverage.

For the supply capacity model we recommend carrying **all three** cost variants forward, with
the headline 2023-USD figure as the base case and explicit fast/slow bounds
that reflect cost-variant disagreement.

---

## 7. Cost per FLOP trend

| Window | Rule | n | ×/yr | Annual decline | R² |
|---|---|---|---|---|---|
| 2018+ | A | 74 | 0.76 | **24.2%** | 0.21 |
| 2018+ | C | 51 | 0.88 | 11.7% | 0.10 |
| Full | A | 98 | 0.69 | 31.1% | 0.46 |
| Full | Epoch flag | 56 | 0.72 | 27.8% | **0.68** |

Cost per FLOP **declines roughly 25–30% per year** across most reasonable
cuts of the data. R² is materially lower than for compute or cost in
isolation — unsurprising, because cost-per-FLOP combines the noise of two
already-uncertain estimates and the dataset thins to ~50–100 rows.

The historical base estimate is **~25%/yr decline (0.75×/yr)** for the modern
window, with bounds at ~12% and ~30% reflecting the rule sensitivity.

Chart: `outputs/charts/historical_cost_per_flop_over_time.png`.

---

## 8. Key uncertainties

1. **Cost variant divergence (largest single uncertainty).** Same models,
   same window, same regression — but the implied annual cost-growth
   multiplier ranges 2.5× → 4.9× depending on which cost column you use.
   the supply capacity model must not silently average these.
2. **Cost coverage is thin.** 74 frontier-rule-A rows have headline cost,
   only 22–27 have the more hardware-grounded variants. Late 2025 / 2026
   are particularly sparse.
3. **2026 partial year.** Only 2 models with known compute disclosed so
   far. Strong negative residuals for 2026 in `residuals_compute_trend.png`
   probably reflect right-truncation, not a deceleration.
4. **OLS, no error model.** Epoch's `Confidence` field is collected but
   not yet used in fitting. A WLS variant using inverse-confidence weights
   would tighten standard errors but would not change central estimates
   materially given how concentrated `Confident` ratings are post-2020.
5. **Selection artifacts in Rule C.** Already discussed.
6. **Organization-level structure.** The residual-by-org chart shows
   OpenAI, Google, Meta, DeepMind, NVIDIA, and xAI sit consistently above
   the trend line under Rule A 2018+; Alibaba, Anthropic, Google Brain
   sit below. the supply capacity model should not assume one global rate fits all labs.
7. **Long-tail pre-1990 data.** Including pre-deep-learning systems pulls
   the long-run slope down. The two-regime (slow until ~2010, fast after)
   structure is visible in every chart and is one of the cleaner findings
   in this dataset.
8. **Hardware quality / cluster scale data is too sparse for a model.**
   199 frontier rows with accelerator counts and 204 with training duration
   give a credible *descriptive* timeline (`outputs/charts/historical_hardware_timeline.png`)
   but not enough for a reliable multivariate fit yet.

---

## 9. Recommended assumptions for the supply capacity model

These are the explicit handoff parameters. Each is a recommendation, not
a forecast — the corresponding fast/slow bounds are intentionally wide
enough to bracket the rule-sensitivity and variant-sensitivity exposed in
Sections 5–7.

```
Base compute growth assumption:           6.0×/yr        (Rule A, 2018+)
Fast compute growth assumption:           6.4×/yr        (Rule B, 2018+)
Slow compute growth assumption:           2.0×/yr        (long-run, 1950+)

Base training-cost growth assumption:     4.0×/yr        (mid of Rule A 2018+ vs Epoch-flag full)
Fast training-cost growth assumption:     4.9×/yr        (Rule A 2018+, headline 2023 USD)
Slow training-cost growth assumption:     2.5×/yr        (Rule A 2018+, upfront-hardware variant)

Base cost-per-FLOP decline assumption:    0.75×/yr  (~25% / yr decline)
Fast cost-per-FLOP decline assumption:    0.69×/yr  (~31% / yr decline)
Slow cost-per-FLOP decline assumption:    0.88×/yr  (~12% / yr decline)

Recommended historical window:            2018-01-01 → most recent full quarter
Recommended frontier definition:          Rule A (top-10 at release)
                                          with Rule B + Epoch flag as cross-checks
```

### Known weaknesses

- Cost-variant divergence (2.5× ↔ 4.9×) is wider than rule-choice divergence
  and is **not** captured by quoting a single 2023-USD figure with a CI.
  the supply capacity model must explicitly track at least the cloud and upfront variants in
  parallel.
- The cost-per-FLOP fit is the noisiest of the three trends (R² = 0.21
  under the headline rule). Treat its central estimate as ±10 percentage
  points on the annual decline rate, not ±2.
- Right-truncation: late-2025 and 2026 disclosures will continue to arrive
  for months. Re-fitting in Q3 2026 should tighten the modern-window
  slopes and may revise the headline numbers slightly upward (reporting
  bias historically favors high-compute systems).
- Organization-level residual structure is **not** modeled. the supply capacity model may
  need lab-level effects rather than a single global rate.

---

## 10. Open questions

1. Should Rule A use a top-N **percentile** (e.g. top 10%) rather than a
   fixed top-10? The current rule under-counts the modern era when many
   more frontier-grade models are released per year.
2. Should the fits be **WLS** with `Confidence` as inverse variance? Likely
   small effect, but worth confirming.
3. Should we collect **non-Epoch** cost figures (lab disclosures, hardware
   purchase reports, public cloud pricing) as a follow-up cross-check on
   the cost-variant divergence?
4. Do we need a **separate "training compute including post-training"**
   trend? RLHF/RLAIF and inference-time scaling are now non-negligible and
   Epoch's `Finetune compute` column is sparse but populated for some
   recent models.
5. Should the next phase formalize the **two-regime** finding (slow pre-2010,
   fast post-2010) with a piecewise fit and a structural break test rather
   than assuming a single 2018+ window?

---

## Appendix: deliverable checklist

| Spec deliverable | File | Status |
|---|---|---|
| Clean dataset (parquet) | `data/processed/historical_models.parquet` | ✓ |
| Clean dataset (CSV) | `data/processed/historical_models.csv` | ✓ |
| Data dictionary | `docs/data_dictionary.md` | ✓ |
| Compute over time | `outputs/charts/historical_compute_over_time.png` | ✓ |
| Cost over time | `outputs/charts/historical_cost_over_time.png` | ✓ |
| Cost per FLOP | `outputs/charts/historical_cost_per_flop_over_time.png` | ✓ |
| Compute by organization | `outputs/charts/historical_compute_by_organization.png` | ✓ |
| Cost by organization | `outputs/charts/historical_cost_by_organization.png` | ✓ |
| Residuals (compute) | `outputs/charts/historical_residuals_compute.png` | ✓ |
| Residuals (cost) | `outputs/charts/historical_residuals_cost.png` | ✓ |
| Hardware timeline | `outputs/charts/historical_hardware_timeline.png` | ✓ (bonus) |
| Trend estimates table | `outputs/tables/historical_trend_estimates.csv` | ✓ (45 rows) |
| Hardware summary | `outputs/tables/historical_hardware_summary.csv` | ✓ (bonus) |
| historical-baseline memo | `docs/historical_findings.md` | ✓ (this file) |
