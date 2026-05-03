# Supply Capacity Model — Sprint 1 Initial Notes

**Date:** 2026-05-03
**Sprint goal:** working supply skeleton — accelerator stock, theoretical/usable compute, four scenarios, comparison chart vs the historical baseline.

## What's in this sprint

- `data/assumptions/supply_input_assumptions.yaml` — long-format
  (parameter, scenario, year, value, unit, source, confidence, notes).
  108 rows, 12 parameters × 4 scenarios at milestone years (2024 / 2025 / 2030 / 2040), linearly interpolated.
- `scenarios/supply_*.yaml` — 4 scenario configs (`base_input_case`, `chip_bottleneck`, `power_datacenter_bottleneck`, `capex_rich`).
- `model/supply_engine.py` — projection pipeline:
  shipments → installed stock (linear retirement) → theoretical compute → power-limited stock → DC-limited stock → capex-limited stock → utilization derating → binding-constraint identifier.
- `pipelines/supply.py` — driver running all 4 scenarios.
- Outputs:
  - `outputs/tables/supply_fundamental_inputs_by_year.csv`
  - `outputs/tables/supply_scenario_summary.csv`
  - `outputs/tables/supply_binding_constraints.csv`
  - `outputs/charts/supply_usable_compute_capacity.png`
  - `outputs/charts/supply_binding_constraint_by_year.png`
  - `outputs/charts/supply_vs_historical_compute_trend.png`

## ⚠ Placeholder-assumption warning

**Every numeric input in `supply_input_assumptions.yaml` is a sprint-1 placeholder.**
All rows are marked `confidence=low` and `source=placeholder_round_number`
(except for chip-spec items like H100 peak FLOP and TDP, marked
`confidence=medium`). The absolute-level numbers in the charts and tables
are **illustrative only** until sprint 2 replaces them with sourced figures.

The sprint-1 model is a working *engine*. The *answers* are not yet
defensible.

## Headline sprint-1 numbers (placeholder, illustrative)

CAGR of usable AI compute, 2024–2040:

| Scenario | 2024 (FLOP/yr) | 2040 (FLOP/yr) | CAGR | Binding 2030 |
|---|---|---|---|---|
| Base continuation | 5.85e+28 | 1.01e+31 | **38%/yr** | chip |
| Capex-rich | 7.02e+28 | 1.91e+31 | 42%/yr | chip |
| Chip-constrained | 5.02e+28 | 2.16e+30 | 27%/yr | chip |
| Power/DC-constrained | 4.88e+28 | 4.42e+30 | 33%/yr | **power** |

For comparison, historical Rule A 2018+ historical frontier-compute trend
is **5.97×/yr (~497% CAGR)** — roughly **an order of magnitude faster**
than the fastest placeholder supply scenario.

## Three observations worth flagging now

### 1. The the historical baseline 6×/yr extrapolation is unphysical under any of our placeholder scenarios.

Even under `capex_rich` (with $8T/yr AI infrastructure capex by 2040, double
base case, accelerator shipments compounding to 300M H100-eq/yr by 2040),
total usable compute grows at ~42%/yr. That is one quarter of the historical baseline
rate. By 2040 the gap between the historical extrapolation and the supply capacity model
supply is **~10 OOM**.

Three non-mutually-exclusive readings:

- **Placeholder bias**: our assumptions are conservative — true 2024 H100-eq
  shipments may already be in the tens of millions when AMD MI300, TPU v5,
  Trainium, and Chinese-domestic accelerators are converted to H100-eq.
  Sprint 2 will move the absolute floor up.
- **The historical rate is the rate of single-frontier-runs**, not total
  supply. Frontier runs almost certainly used a growing share of total
  global AI compute through 2018–2024 — the gap-filler is share, not
  shipments. the allocation layer is where this matters.
- **The historical 6× cannot continue forever** anyway. Even ignoring our
  numbers, doubling every 5 months for another 10 years implies single
  training runs at ~10⁹⁰ FLOP. The interesting question is *when* the
  fundamentals start binding — the supply capacity model's job.

### 2. Capex binds first, then chips.

Across `base`, `capex_rich`, and `chip_bottleneck` scenarios, capex is
the binding constraint in **2024–2025**, after which chips bind.
That's a structural feature of our placeholder numbers (annual capex
~$250B vs ~5M H100-eq × ~$60K cluster cost = $300B for 2024) and is
worth scrutinizing in sprint 2 — if 2024 actual capex was higher, the
crossover happens earlier or capex never binds at all.

### 3. Power binds for the entire post-2026 horizon under power_dc_bottleneck.

This is the only scenario where the binding constraint is anything other
than chips for most years — and it's the one most often cited in current
public discourse (transmission queues, transformer shortages, AI-DC
permitting). Under our placeholder numbers, with AI-DC capacity at
60 GW in 2030 and 150 GW in 2040 (vs base 150/500), power binds from
2026 onward and the 2040 capacity is **~1/4 of the base case**.

## What sprint 2 needs to do (priority-ordered)

1. **Replace shipment placeholders with sourced figures.**
   - NVIDIA disclosed datacenter-segment unit shipments (10-Ks/quarterly)
   - AMD MI300 / MI350 production guidance
   - Google TPU pod count estimates (SemiAnalysis, third-party)
   - AWS Trainium/Inferentia disclosed deployment numbers
   - Convert each to H100-eq using FP16 dense FLOP/s ratios
2. **Replace AI-DC capacity placeholders.**
   - SemiAnalysis AI Data Center Model
   - IEA "Energy and AI" report (April 2025)
   - Public hyperscaler capex announcements
3. **Replace capex placeholders.**
   - Hyperscaler 10-Ks for Microsoft / Alphabet / Meta / Amazon
   - Sovereign program announcements (UAE, Saudi, France, India)
4. **Add hardware-performance index time series.**
   Currently `peak_flops_per_h100e` is constant (because shipments are
   already in H100-eq), but we should record the *implied* hardware-perf
   improvement (H100→B200→Rubin→…) so the allocation layer can use it.
5. **Differentiate `power` and `datacenter` constraints.**
   Right now they collapse. Sprint 2 should split slot-count / cooling /
   transformer constraints from raw MW.
6. **Add sensitivity analysis.**
   The model is already scenario-keyed; trivial to add ± fits on the
   sensitive parameters (shipments, AI-DC MW, capex).
7. **Connect to historical cost-variant insight.**
   Compute and report `cost_per_h100e_year` in the three the historical baseline cost
   variants (upfront / cloud / blended) — currently we only emit a single
   amortized figure.

## Open questions for the user (Supply capacity model only)

1. **Geography**: model global aggregate, or split US / China / RoW? Phase
   1 was global; supply placeholders are global. Splitting matters more
   for sprint 2+ since power, capex, and chip access diverge sharply.
2. **Time grain**: annual is fine for capacity; should we go to quarterly
   for the 2024-2027 calibration window? the historical baseline had publication-date
   resolution which was finer.
3. **Lifetime**: 5 years linear retirement is a placeholder. Hyperscalers
   are publicly extending depreciation to 6 years. Worth making lifetime
   itself scenario-dependent.
4. **Should we calibrate sprint 2 to actual 2024 + 2025 outcomes**
   (now both fully observed)? That would tighten the absolute level and
   leave the projection slope as the modeled quantity.
