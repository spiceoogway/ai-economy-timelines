# Phase 2 Findings — Fundamental Input Compute-Capacity Model

**Author:** automated analysis pipeline
**Date:** 2026-05-03
**Status:** Phase 2 complete (sprint 1 skeleton + sprint 2 sourced inputs).
Phase 3 handoff parameters at the bottom.

---

## 1. Summary

Under sourced base-case assumptions, **global usable AI compute capacity
grows ~46%/yr from 2024 through 2040**, hitting ~1.7e+31 FLOP/year by
2040 — about three orders of magnitude above 2024. The binding
constraint is capex through 2036, then chips for the remainder. None of
the four scenarios reproduces the Phase 1 historical Rule A 2018+ rate
of 5.97×/yr (~497% CAGR); the gap remains roughly 10 orders of
magnitude by 2040.

Three honest readings of the Phase 1 vs Phase 2 gap:

1. **Phase 1's compute trend is single-frontier-run growth, not aggregate
   supply growth.** The two diverge if (and only if) frontier runs use a
   growing share of total compute — which they almost certainly did
   2018–2024. Phase 3 (allocation) is where this is quantified.
2. **The historical 6×/yr rate is unsustainable on Phase 2 fundamentals,
   regardless of share dynamics.** Even capex-rich (50%/yr) is one full
   OOM slower per year than Phase 1.
3. **Sourced inputs increased Phase 2 output growth by ~8 percentage
   points** vs sprint 1's placeholders (38% → 46% base case CAGR), but
   did not close the gap. The conclusion holds.

| Scenario | 2024 (FLOP/yr) | 2040 (FLOP/yr) | CAGR | Binding 2030 |
|---|---|---|---|---|
| Baseline continuation | 3.97e+28 | 1.65e+31 | **45.7%/yr** | capex |
| Capex-rich | 4.37e+28 | 2.89e+31 | 50.1%/yr | capex |
| Chip-constrained | 3.83e+28 | 6.54e+30 | 37.9%/yr | chip |
| Power/DC-constrained | 3.50e+28 | 6.64e+30 | 38.8%/yr | **datacenter** |

---

## 2. Data sources (sprint 2)

Source codes used in `data/assumptions/phase2_input_assumptions.csv`:

| Code | Source | Date |
|---|---|---|
| `epoch_2024_scaling` | Epoch AI, "Can AI scaling continue through 2030?" | 2024-08-20 |
| `iea_energy_ai` | IEA, "Energy and AI" report | 2025-04-10 |
| `nvidia_h100_spec` | NVIDIA H100 datasheet | — |
| `nvidia_ir` | NVIDIA Investor Relations / 10-K filings | various |
| `hyperscaler_10k` | Microsoft / Alphabet / Meta / Amazon 10-K capex disclosures | various |
| `stargate_announce` | OpenAI / MSFT / Oracle / SoftBank Stargate announcement | 2025 |
| `industry_typical` | Conservative industry-typical figures (PUE, server overhead, MFU) | — |
| `author_synthesis` | Multi-source synthesis with cited anchors | 2026-05 |

Confidence flags per row:

- `high` — directly cited from named source
- `medium` — derived/synthesized, anchored to cited figures
- `low` — round-number placeholder retained from sprint 1 (≈18% of rows, mostly long-horizon 2040 values)

Most-anchored anchors:
- 2024 global DC electricity: **415 TWh** (IEA, ~1.5% of world total)
- 2030 base-case DC electricity: **945 TWh** (IEA)
- 2024 NVIDIA H100/H200 shipments: **1.5–2M units** (Epoch median)
- 2030 H100-eq stock for training: **20M–400M units**, median 100M (Epoch)
- US AI-DC 2023: **~3 GW**, total US DC 2030: **~90 GW** (Epoch)
- Power efficiency 2024→2030: **24×** vs Llama 3.1 405B (Epoch)

## 3. Inclusion criteria (assumption table)

- Long-format CSV: `(parameter, scenario, year, value, unit, source, confidence, notes)`.
- 173 rows covering **15 parameters** × 4 scenarios at milestone years (2024, 2025, 2026, 2030, 2040), linearly interpolated between milestones.
- Constants stored as a single milestone (held constant across years).
- Values supplied to 2 significant figures except where the source uses 3.
- Comments (lines starting `#`) used liberally in the CSV for source notes.

## 4. Model architecture

```
shipments_t (H100-eq)
    ↓ + linear retirement (5–6y depending on scenario)
installed_stock_h100e_chip_limited_t
    ┐         ┐         ┐
power_lim   dc_lim   capex_lim_t          (each computed independently)
    └─┬─┘─┬─┴─┬─┘
      min: available_stock_h100e_t
            ↓ × peak_flops × seconds/year
      available_compute_flop_year_pre_util
            ↓ × cluster_utilization
      usable_compute_flop_year_t
```

Power vs DC differentiation (new in sprint 2):

```
power_limited_h100e = (ai_dc_mw × ai_share × 1000) / (chip_kw × server_oh × pue)
dc_limited_h100e    = (ai_dc_mw × dc_packing_efficiency × 1000) / (chip_kw × server_oh × pue)
```

`dc_packing_efficiency ∈ [0, 1]` captures cooling, slot, transformer,
and permitting drag — the fraction of nominal AI-DC MW that can actually
host frontier accelerators. `1.0` in base/capex_rich/chip_bottleneck;
falls to `0.65` by 2040 in `power_dc_bottleneck`.

## 5. Headline results by scenario

### Baseline continuation
- **CAGR 2024→2040: 45.7%/yr.** Reaches 1.65e+31 FLOP/yr by 2040.
- Binding constraint: **capex** through 2036, then **chips** 2037+.
- Stock: 3.18M H100e (2024) → 959M H100e (2040), ~300× growth.
- Capex required ramps from $0.2T/yr (2024) to ~$3T/yr (2040); coverage stays > 70% throughout (capex shortfall, not surplus).

### Capex-rich acceleration
- **CAGR 2024→2040: 50.1%/yr.** Reaches 2.89e+31 FLOP/yr by 2040.
- Binding mostly **chips** (2024–2027) then **capex** (2028–2034) then **chips** again (2035+). The brief mid-period capex bind reflects cumulative capex falling behind cumulative chip-stock value.
- Stock: 3.5M (2024) → 1.68B (2040). Roughly 2× the base case by 2040.

### Chip-constrained
- **CAGR 2024→2040: 37.9%/yr.** Reaches 6.54e+30 FLOP/yr by 2040 (~25% of base).
- Binding **capex** 2024–2026, **chip** 2027–2040.
- Stock: 2.73M → 349M.
- Driven entirely by Epoch's 20M-H100e lower-bound 2030 stock and a 6-year (vs 5-year) refresh cycle.

### Power / data-center constrained
- **CAGR 2024→2040: 38.8%/yr.** Reaches 6.64e+30 FLOP/yr by 2040.
- Binding **capex** 2024–2026, **datacenter** 2027+ (sprint-2 differentiation activated — the new `dc_packing_efficiency` parameter does the work).
- Stock: 2.8M → 387M.
- Power capacity itself never binds in any scenario under our 24× efficiency improvement — the binding is on physical buildout density, not raw MW.

## 6. Cost variant trajectories (Phase 1 carryover)

Per Phase 1's most important finding (cost-variant divergence is bigger
than rule-choice divergence), Phase 2 carries three cost-per-H100e-year
variants forward.

Base scenario, 2024 → 2040:

| Variant | 2024 USD/H100e/yr | 2040 USD/H100e/yr | Ratio |
|---|---|---|---|
| Upfront-amortized (chip × cluster_mult / lifetime) | 13,200 | 4,550 | 0.34× |
| Cloud-rental | 15,000 | 5,000 | 0.33× |
| Blended 50/50 | 14,100 | 4,775 | 0.34× |

Persistent ~10% gap between cloud and upfront, narrowing toward 2040.
Under chip-bottleneck the cloud rate runs ~50–80% higher than under
base case, peaking at the supply-tightest moments. Chart:
`outputs/charts/phase2_cost_per_h100e_by_variant.png`.

## 7. Sensitivity (one-parameter perturbations of base case)

`outputs/charts/phase2_sensitivity_bands.png` and
`outputs/tables/phase2_sensitivity_analysis.csv`. Each parameter scaled
by {0.5, 0.75, 1.0, 1.5, 2.0} for all years, holding everything else
at base.

| Perturbation | 2040 usable compute multiplier vs base |
|---|---|
| Shipments × 0.5 | ~0.55× (chip becomes binding earlier) |
| Shipments × 2.0 | ~1.5× (capex binds harder, less than 2×) |
| AI-DC MW × 0.5 | ~0.85× (power doesn't bind in base; only matters if it does) |
| AI-DC MW × 2.0 | ~1.0× (no effect; power was slack) |
| Capex × 0.5 | ~0.55× (capex was already binding) |
| Capex × 2.0 | ~1.4× (chip starts binding earlier) |

**Implication for Phase 3:** capex and shipments are the two highest-leverage parameters for the base case. AI-DC MW is slack under base assumptions and only matters when something else moves it in.

## 8. Key uncertainties

1. **Single-run vs aggregate compute confusion (most important).** Phase 1
   measures single training-run FLOP for a frontier model. Phase 2
   measures total annual usable global AI compute. Comparing them
   directly is not apples-to-apples. Phase 3 must explicitly model the
   share of total annual compute consumed by the largest single run.
2. **Hyperscaler capex AI-share bias.** We treat ~75% of hyperscaler
   capex as AI infrastructure for 2025+. The actual share is debated;
   if it is 60% the base CAGR drops by ~3 percentage points.
3. **H100-equivalent unit definition.** We've used FP16/BF16 dense
   peak FLOP/s as the conversion. For training-relevant workloads the
   memory-bandwidth-corrected H100-eq is ~10–15% lower per chip; for
   MoE inference it is higher. We use the dense definition throughout.
4. **2030 stock estimate width.** Epoch's 2030 H100-eq for training
   range is **20M–400M (20× spread)**. We use a midpoint and the
   model is approximately linear in this input.
5. **AI-DC MW coverage gap.** IEA gives total DC TWh; Epoch gives US
   AI-DC GW. Implied global AI-DC for 2024 is ~10–15 GW with wide
   uncertainty bands. We anchor at 12 GW.
6. **Lifetime is scenario-dependent.** A swing from 5 to 6 years
   reduces required shipments to maintain the same stock by ~17%; we
   keep this scenario-keyed.
7. **No geographic split.** Global aggregate only; US, China, EU, RoW
   are intermixed. Power and capex are highly geographically
   concentrated and a regional split would tighten constraint
   identification materially.
8. **No quarterly grain.** 2024 and 2025 are now fully observed and a
   quarterly calibration would tighten the modern-window levels.

## 9. Recommended Phase 3 handoff parameters

These are the explicit handoff parameters for Phase 3 (allocation
across training, inference, AI R&D, post-training, reserves).

```
=== Annual usable compute capacity envelope (FLOP / year) ===

Year   Base         Capex-rich   Chip-bot     Power/DC-bot
2024   3.97e+28     4.37e+28     3.83e+28     3.50e+28
2025   1.05e+29     1.18e+29     8.86e+28     8.92e+28
2026   2.08e+29     2.69e+29     1.67e+29     1.79e+29
2027   3.55e+29     5.04e+29     2.78e+29     3.04e+29
2030   1.35e+30     2.46e+30     7.05e+29     1.04e+30
2035   4.93e+30     8.69e+30     2.15e+30     2.39e+30
2040   1.65e+31     2.89e+31     6.54e+30     6.64e+30

Read full CSV: outputs/tables/phase2_fundamental_inputs_by_year.csv

=== Recommended Phase 3 base-case envelope ===
Use base_input_case as the central case.
Use chip_bottleneck as the slow / pessimistic floor.
Use capex_rich as the fast / optimistic ceiling.
Use power_datacenter_bottleneck as the alternative-bottleneck stress.

=== Available H100-eq stock by year (units, base case) ===
2024:   3.18e+06
2025:   8.62e+06
2026:   1.81e+07
2027:   3.07e+07
2030:   1.18e+08  ← anchored to Epoch median 100M ± 5x
2035:   4.30e+08
2040:   9.59e+08

=== Capex required by year (USD/yr, base case) ===
2024:   2.10e+11
2025:   3.50e+11
2026:   5.00e+11
2030:   1.50e+12
2040:   3.00e+12
Cumulative 2024-2040: ~$22T

=== Power capacity by year (MW, AI-dedicated, base case) ===
2024:   12,000
2025:   22,000
2026:   38,000
2030:   80,000   ← anchored to IEA + Epoch
2040:   300,000

=== Binding constraint by year (base case) ===
2024-2036: capex
2037-2040: chip

=== Cost per H100-eq accelerator-year (base, 2024 / 2040) ===
upfront-amortized: $13,200 → $4,550
cloud-rental:      $15,000 → $5,000
blended:           $14,100 → $4,775

(All three trajectories should be carried forward into Phase 3 — the
divergence is a real economic signal per Phase 1 findings.)
```

### Known weaknesses (carry forward to Phase 3 documentation)

- Single-frontier-run share of total compute is the largest unmodeled quantity. Phase 3 must address this.
- 2030 H100-eq stock estimate has 20× spread between Epoch lower and upper bounds.
- ~18% of assumption rows are still `confidence=low` — mostly the 2040 long-horizon values, which are extrapolations.
- No geographic structure.
- Cumulative-capex limit treatment is simplified (we sum annual flows; depreciation / write-downs / refinancing are not modeled).

## 10. Open questions for Phase 3

1. **What share of usable compute goes to a single largest training
   run by year?** 2018: probably ~15% of frontier-lab compute. 2024:
   probably 5–10% globally. Phase 3 should make this explicit and
   variable.
2. **Training vs inference allocation.** Phase 3 needs a split, ideally
   parameterized — base case probably ~35% training, ~55% inference,
   ~10% reserves/post-training as of 2024, with the inference share
   growing.
3. **AI R&D experiments share.** This is the wedge that grows fastest
   if recursive self-improvement is real; Phase 3 should isolate it.
4. **Reserved capacity and cluster fragmentation.** Not all H100-eq
   stock is fungible — reserved capacity, geographic fragmentation,
   and lab-specific pools all shrink the effectively-allocatable pool
   below the headline figure.
5. **Allocation under a binding constraint.** When chips bind, who
   gets them? Hyperscalers, sovereign programs, frontier labs, and
   inference cloud customers all compete for the same pool. This is a
   Phase 3 question.

---

## Appendix: deliverable checklist

| Spec deliverable | File | Status |
|---|---|---|
| Input assumptions file | `data/assumptions/phase2_input_assumptions.csv` | ✓ (173 rows, sourced) |
| Fundamental input model | `model/fundamental_inputs.py` | ✓ |
| Scenario configs (4) | `scenarios/phase2_*.yaml` | ✓ |
| Notebook / driver | `notebooks/run_phase2_sprint2.py` | ✓ |
| Accelerator stock chart | `outputs/charts/phase2_accelerator_stock_h100e.png` | ✓ |
| Theoretical compute chart | `outputs/charts/phase2_theoretical_compute_capacity.png` | ✓ |
| Usable compute chart | `outputs/charts/phase2_usable_compute_capacity.png` | ✓ |
| Power capacity constraint chart | `outputs/charts/phase2_power_capacity_constraint.png` | ✓ (with DC differentiation) |
| Capex required chart | `outputs/charts/phase2_capex_required.png` | ✓ |
| Binding-constraint heatmap | `outputs/charts/phase2_binding_constraint_by_year.png` | ✓ |
| Phase 2 vs Phase 1 chart | `outputs/charts/phase2_vs_phase1_compute_trend.png` | ✓ |
| Cost-per-H100e by variant | `outputs/charts/phase2_cost_per_h100e_by_variant.png` | ✓ (bonus) |
| Sensitivity bands | `outputs/charts/phase2_sensitivity_bands.png` | ✓ (bonus) |
| Year-by-year fundamentals | `outputs/tables/phase2_fundamental_inputs_by_year.csv` | ✓ |
| Scenario summary | `outputs/tables/phase2_scenario_summary.csv` | ✓ |
| Binding constraints | `outputs/tables/phase2_binding_constraints.csv` | ✓ |
| Capex requirements | `outputs/tables/phase2_capex_requirements.csv` | ✓ |
| Sensitivity analysis | `outputs/tables/phase2_sensitivity_analysis.csv` | ✓ (bonus) |
| Phase 2 scope | `docs/phase2_scope.md` | ✓ |
| Phase 2 initial notes | `docs/phase2_initial_notes.md` | ✓ (sprint 1) |
| Phase 2 findings memo | `docs/phase2_findings.md` | ✓ (this file) |
