"""Supply pipeline: sourced inputs + sensitivity + cost variants.

Run with: `uv run supply`

Produces all supply-side compute-capacity deliverables per docs/scope.md.

Outputs:
  data/processed/supply_fundamental_inputs.csv
  outputs/tables/supply_fundamental_inputs_by_year.csv
  outputs/tables/supply_scenario_summary.csv
  outputs/tables/supply_binding_constraints.csv
  outputs/tables/supply_capex_requirements.csv
  outputs/tables/supply_sensitivity_analysis.csv
  outputs/charts/supply_accelerator_stock_h100e.png
  outputs/charts/supply_theoretical_compute_capacity.png
  outputs/charts/supply_usable_compute_capacity.png
  outputs/charts/supply_power_capacity_constraint.png
  outputs/charts/supply_capex_required.png
  outputs/charts/supply_binding_constraint_by_year.png
  outputs/charts/supply_vs_historical_compute_trend.png
  outputs/charts/supply_cost_per_h100e_by_variant.png
  outputs/charts/supply_sensitivity_bands.png
"""
from __future__ import annotations

import pandas as pd

from model.runtime import (
    CHARTS_DIR,
    HISTORICAL_TREND_TABLE,
    PROCESSED_DIR,
    TABLES_DIR,
)
from model.supply_engine import (
    load_all_scenarios,
    load_assumptions,
    project_scenario,
    sensitivity_analysis,
)
from pipelines import supply_charts as charts


def get_historical_rule_a_2018_fit() -> tuple[float, float, float]:
    """Return (slope_log10_per_year, intercept_log10, annual_multiplier)
    for the historical Rule A 2018+ training-compute fit, with the
    intercept rebased so 2024 corresponds to 1e25 FLOP per single
    frontier run."""
    t = pd.read_csv(HISTORICAL_TREND_TABLE)
    row = t[
        (t["trend_name"] == "training_compute")
        & (t["frontier_rule"] == "frontier_rule_a_2018+")
    ]
    slope = float(row["slope_log10_per_year"].iloc[0])
    mult = float(row["annual_growth_multiplier"].iloc[0])
    intercept = 25.0 - slope * 2024.0
    return slope, intercept, mult


def _build_capex_table(df: pd.DataFrame, scenarios) -> pd.DataFrame:
    """Capex required (to grow chip-limited stock by Δ at this year's
    cluster cost) vs assumed-available capex, per scenario per year."""
    rows = []
    for sc in scenarios:
        sub = df[df["scenario"] == sc.name].set_index("year")
        delta_stock = sub["installed_stock_h100e_chip_limited"].diff().clip(lower=0)
        capex_required = (
            delta_stock
            * sub["accelerator_unit_cost_usd"]
            * sub["cluster_capex_multiplier"]
        )
        capex_available = sub["ai_infrastructure_capex_usd"]
        for y in sub.index:
            avail = float(capex_available.loc[y])
            rows.append(
                {
                    "scenario": sc.name,
                    "year": y,
                    "capex_required_usd": float(capex_required.loc[y]),
                    "capex_available_usd": avail,
                    "capex_coverage_ratio": (
                        float(capex_required.loc[y] / avail) if avail else float("nan")
                    ),
                }
            )
    return pd.DataFrame(rows)


def main() -> None:
    print("[1/8] Loading scenarios + projecting...")
    assumptions = load_assumptions()
    scenarios = load_all_scenarios()
    frames = [project_scenario(s, assumptions) for s in scenarios]
    df = pd.concat(frames, ignore_index=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(PROCESSED_DIR / "supply_fundamental_inputs.csv", index=False)
    df.to_csv(TABLES_DIR / "supply_fundamental_inputs_by_year.csv", index=False)

    print("[2/8] Summary + capex tables...")
    summary_years = [2024, 2025, 2026, 2027, 2030, 2035, 2040]
    summary = (
        df[df["year"].isin(summary_years)]
        .pivot_table(
            index=["scenario", "year"],
            values=[
                "available_stock_h100e",
                "usable_compute_flop_year",
                "ai_power_capacity_mw",
                "ai_infrastructure_capex_usd",
                "binding_constraint",
            ],
            aggfunc={
                "binding_constraint": "first",
                "available_stock_h100e": "sum",
                "usable_compute_flop_year": "sum",
                "ai_power_capacity_mw": "sum",
                "ai_infrastructure_capex_usd": "sum",
            },
        )
        .reset_index()
    )
    summary.to_csv(TABLES_DIR / "supply_scenario_summary.csv", index=False)

    binding = (
        df.groupby(["scenario", "binding_constraint"])
        .size()
        .reset_index(name="years_binding")
        .sort_values(["scenario", "years_binding"], ascending=[True, False])
    )
    binding.to_csv(TABLES_DIR / "supply_binding_constraints.csv", index=False)

    capex_df = _build_capex_table(df, scenarios)
    capex_df.to_csv(TABLES_DIR / "supply_capex_requirements.csv", index=False)

    print("[3/8] Chart: accelerator stock...")
    charts.chart_accelerator_stock(
        df, scenarios, CHARTS_DIR / "supply_accelerator_stock_h100e.png"
    )

    print("[4/8] Chart: theoretical + usable compute...")
    charts.chart_theoretical_and_usable_compute(
        df, scenarios, CHARTS_DIR / "supply_theoretical_compute_capacity.png"
    )
    charts.chart_usable_compute_capacity(
        df, scenarios, CHARTS_DIR / "supply_usable_compute_capacity.png"
    )

    print("[5/8] Chart: power capacity + capex required...")
    charts.chart_power_capacity_constraint(
        df, scenarios, CHARTS_DIR / "supply_power_capacity_constraint.png"
    )
    charts.chart_capex_required(
        capex_df, scenarios, CHARTS_DIR / "supply_capex_required.png"
    )

    print("[6/8] Chart: binding constraint heatmap...")
    years = sorted(df["year"].unique().tolist())
    charts.chart_binding_constraint_heatmap(
        df, scenarios, years, CHARTS_DIR / "supply_binding_constraint_by_year.png"
    )

    print("[7/8] Chart: vs historical baseline...")
    historical_fit = get_historical_rule_a_2018_fit()
    charts.chart_vs_historical_compute_trend(
        df, scenarios, historical_fit, years,
        CHARTS_DIR / "supply_vs_historical_compute_trend.png",
    )

    print("[8/8] Chart: cost variants + sensitivity bands...")
    charts.chart_cost_per_h100e_by_variant(
        df, CHARTS_DIR / "supply_cost_per_h100e_by_variant.png"
    )

    base_scenario = next(s for s in scenarios if s.name == "base_input_case")
    multipliers = [0.5, 0.75, 1.0, 1.5, 2.0]
    sens_params = [
        ("h100_equivalent_shipments", "Shipments"),
        ("ai_datacenter_capacity_mw", "AI-DC capacity (MW)"),
        ("ai_infrastructure_capex_usd", "Capex available"),
    ]
    sens_frames = [
        sensitivity_analysis(
            base_scenario, assumptions, parameter=param, multipliers=multipliers
        )
        for param, _ in sens_params
    ]
    charts.chart_sensitivity_bands(
        sens_frames, sens_params, multipliers,
        CHARTS_DIR / "supply_sensitivity_bands.png",
    )
    pd.concat(sens_frames, ignore_index=True).to_csv(
        TABLES_DIR / "supply_sensitivity_analysis.csv", index=False
    )

    print("\n=== Supply summary (sourced inputs) ===")
    for sc in scenarios:
        sub = df[df["scenario"] == sc.name].set_index("year")
        v24 = sub.loc[2024, "usable_compute_flop_year"]
        v40 = sub.loc[2040, "usable_compute_flop_year"]
        cagr = (v40 / v24) ** (1 / 16) - 1
        print(
            f"  {sc.name:32s} 2024={v24:.2e} → 2040={v40:.2e}  "
            f"CAGR={cagr*100:.1f}%/yr  binding(2030)={sub.loc[2030, 'binding_constraint']}"
        )
    print(f"\n  Historical Rule A 2018+ multiplier: {historical_fit[2]:.2f}×/yr")


if __name__ == "__main__":
    main()
