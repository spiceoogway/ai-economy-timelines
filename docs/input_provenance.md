# Input Provenance

Every input the model reads, where it came from, and how confident we are
in it.

## Confidence rubric

- **high** — directly sourced from a named public source (e.g. NVIDIA
  H100 datasheet, IEA published TWh figure, the Epoch CSV itself).
- **medium** — derived or synthesized from named public sources (e.g.
  global H100-eq shipments inferred from NVIDIA's reported datacenter
  revenue + AMD MI300 production guidance + TPU pod estimates).
- **low** — round-number placeholder or long-horizon extrapolation. Most
  remaining `low` rows are 2040 values that extrapolate from the 2030
  anchor.

The full source/confidence metadata lives in the assumptions YAML
itself; see `data/assumptions/supply_input_assumptions.yaml` for
per-row provenance.

## Inputs by component

| Input | Component | File | Source | Source type | Confidence | Used for | Notes |
|---|---|---|---|---|---|---|---|
| Epoch "Notable AI Models" dataset | Historical baseline | `data/raw/epoch_notable_ai_models_raw.csv` | [Epoch AI](https://epoch.ai/data/notable_ai_models.csv) | public dataset | high | historical training compute, cost, parameters, hardware, frontier flag | raw immutable source; retrieved 2026-05-02 |
| Epoch "Frontier" subset | Historical baseline (cross-check) | `data/raw/epoch_frontier_ai_models_raw.csv` | Epoch AI | public dataset | high | sanity-check our own frontier rules against Epoch's curated subset | not used directly in fits |
| Epoch "Large-Scale" subset | Historical baseline (cross-check) | `data/raw/epoch_large_scale_ai_models_raw.csv` | Epoch AI | public dataset | high | reference only | not used directly in fits |
| H100/H200/B200 shipments + AMD/TPU/Trainium | Supply capacity | `supply_input_assumptions.yaml` `h100_equivalent_shipments` | Epoch "Can AI scaling continue through 2030?" (Aug 2024) + author synthesis | public estimate + synthesis | medium | accelerator stock projection, chip-limited stock | NVIDIA reported H100/H200 ~1.5–2M for 2024 (Epoch); AMD MI300, TPU, Trainium, China-domestic added by synthesis |
| Accelerator lifetime (years) | Supply capacity | `supply_input_assumptions.yaml` `accelerator_lifetime_years` | hyperscaler 10-K depreciation schedules + author synthesis | public financial disclosures + synthesis | medium | retirement curve in stock projection | base 5y; capex-rich 4y; chip/power-DC bottleneck 6y (forced longer holds) |
| H100 peak FLOP/s | Supply capacity | `supply_input_assumptions.yaml` `peak_flops_per_h100e` | NVIDIA H100 datasheet | public spec | high | theoretical compute calculation | 989 TFLOP/s FP16 dense; constant by H100-eq definition |
| H100 power draw (kW) | Supply capacity | `supply_input_assumptions.yaml` `power_kw_per_h100e` | NVIDIA H100 datasheet (2024); Epoch 24× efficiency improvement (2030) | public spec + public estimate | high (2024) / medium (2030) | per-chip effective power for the power constraint | H100 SXM 700W chip TDP; 0.25 kW by 2030 implied by Epoch's 24× perf-per-watt improvement |
| Server / cluster power overhead | Supply capacity | `supply_input_assumptions.yaml` `server_power_overhead` | industry-typical | conservative industry figure | medium | converts chip TDP → server-level power | 1.5× multiplier (CPUs, NICs, storage, power-delivery losses) |
| PUE | Supply capacity | `supply_input_assumptions.yaml` `pue` | industry-typical | published hyperscale-DC ranges | high (2024) / medium (2030+) | converts server power → datacenter total | Modern hyperscale AI DC ~1.15–1.25 (2024), trends toward 1.10 with liquid cooling |
| AI data-center capacity (MW, global) | Supply capacity | `supply_input_assumptions.yaml` `ai_datacenter_capacity_mw` | IEA "Energy and AI" report (April 2025) + Epoch + author synthesis | public report + public estimate + synthesis | medium | power and DC constraints | IEA: 415 TWh global DC 2024 → 945 TWh 2030; AI share derived; 12 GW (2024) → 80 GW (2030) base case |
| AI share of DC power | Supply capacity | `supply_input_assumptions.yaml` `ai_share_of_dc_power` | industry-typical | conservative figure | medium | fraction of AI-dedicated DC power that's actually AI workloads | 0.85 base; 0.80 power-DC bottleneck; 0.90 capex-rich |
| DC packing efficiency | Supply capacity | `supply_input_assumptions.yaml` `dc_packing_efficiency` | author synthesis | synthesis | medium (2024) / low (2040) | DC slot/cooling/transformer slack — separate from raw grid power | 1.0 most scenarios; falls to 0.65 by 2040 in power_datacenter_bottleneck |
| Cluster utilization (MFU) | Supply capacity | `supply_input_assumptions.yaml` `cluster_utilization` | industry-typical | published MFU benchmarks (Llama-3, GPT-4 estimates) | medium | converts theoretical → usable compute | 0.40 (2024) → 0.55 (2040) base; transformer training MFU ~35–50% |
| Accelerator unit cost (USD per H100-eq) | Supply capacity | `supply_input_assumptions.yaml` `accelerator_unit_cost_usd` | NVIDIA Investor Relations (H100 ASP) + author synthesis | public IR + synthesis | high (2024) / medium (2030+) | capex constraint | $30K (2024) → $15K (2030); H100 list ~$25–40K |
| Cluster capex multiplier | Supply capacity | `supply_input_assumptions.yaml` `cluster_capex_multiplier` | author synthesis from Epoch's "power infra ~40% of GPU cost by 2030" | public estimate + synthesis | medium | converts chip cost → installed-cluster cost (servers + networking + DC + power infra) | 2.2× (2024) → 2.5× (2030); scenario-keyed |
| Hyperscaler AI infrastructure capex | Supply capacity | `supply_input_assumptions.yaml` `ai_infrastructure_capex_usd` | Microsoft/Alphabet/Meta/Amazon 10-K filings + Stargate announcement + author synthesis | public financial disclosures + synthesis | medium | capex constraint | $210B (2024) → $1.5T (2030) base; AI share of total hyperscaler capex assumed ~75% |
| Cloud rental rate per H100-eq per year | Supply capacity | `supply_input_assumptions.yaml` `cloud_rental_usd_per_h100e_year` | industry-typical (~$2/hr × 8760 × 80% util) + author synthesis | published cloud-rental rates + synthesis | medium | cost-per-H100e-year (cloud variant), preserves Phase 1 cost-variant insight | $15K/yr (2024) → $5K/yr (2040) base |

## Source-quality breakdown

Per the YAML's per-row confidence flags, sourced supply assumptions are
distributed roughly:

| Confidence | Approximate row count | Notes |
|---|---|---|
| **high** | ~25% | NVIDIA H100 spec, IEA TWh figures, NVIDIA IR ASP |
| **medium** | ~55% | Synthesis from cited public sources |
| **low** | ~20% | Mostly 2040 long-horizon extrapolations |

The single highest-leverage `medium`-flagged input is **2030 H100-equivalent
shipments** (and therefore stock). Epoch's published range is 20M–400M
H100-eq for "training stock by 2030" — a 20× spread. The base case anchors
to Epoch's median of 100M; the chip_bottleneck scenario anchors to the 20M
floor. This single input dominates the supply-capacity output ranges.

## Per-component external dependencies

- **Historical baseline:** depends only on Epoch's "Notable AI Models" CSV. Refresh by re-downloading the CSV (it's updated periodically) and re-running `uv run historical`.
- **Supply capacity model:** depends on the assumptions YAML; upstream sources cited in the YAML's per-row `source` field are not directly read. To incorporate updated Epoch AI scaling estimates, IEA reports, or hyperscaler 10-K disclosures, edit the YAML and re-run `uv run supply`.

## Future component inputs (not yet sourced)

When the allocation layer is built, it will need:

- **Training-vs-inference split.** Currently estimated at ~35/55/10 (training/inference/reserves) for 2024 — to be sourced from public hyperscaler / lab disclosures and academic estimates.
- **Largest-run concentration.** Fraction of total training compute that goes to the single largest run. Currently unmodeled. Probably 5–15% historically, with wide bands.
- **AI R&D experiment share.** ~10–30% of frontier-lab compute budgets historically — to be refined when allocation lands.
