"""Phase 2 sprint-2 driver: sourced inputs + sensitivity + cost variants.

Run with: `uv run python notebooks/run_phase2_sprint2.py`

Supersedes the sprint-1 driver. Produces all Phase 2 deliverables per
docs/phase2_scope.md §7.

Outputs:
  data/processed/phase2_fundamental_inputs.csv
  outputs/tables/phase2_fundamental_inputs_by_year.csv  (year x scenario)
  outputs/tables/phase2_scenario_summary.csv
  outputs/tables/phase2_binding_constraints.csv
  outputs/tables/phase2_capex_requirements.csv
  outputs/charts/phase2_accelerator_stock_h100e.png
  outputs/charts/phase2_theoretical_compute_capacity.png
  outputs/charts/phase2_usable_compute_capacity.png
  outputs/charts/phase2_power_capacity_constraint.png
  outputs/charts/phase2_capex_required.png
  outputs/charts/phase2_binding_constraint_by_year.png
  outputs/charts/phase2_vs_phase1_compute_trend.png
  outputs/charts/phase2_cost_per_h100e_by_variant.png
  outputs/charts/phase2_sensitivity_bands.png
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from model.fundamental_inputs import (
    CONSTRAINTS,
    ScenarioConfig,
    load_all_scenarios,
    load_assumptions,
    project_scenario,
    sensitivity_analysis,
)

CHARTS_DIR = REPO_ROOT / "outputs" / "charts"
TABLES_DIR = REPO_ROOT / "outputs" / "tables"
PROCESSED_DIR = REPO_ROOT / "data" / "processed"
PHASE1_TREND_TABLE = REPO_ROOT / "outputs" / "tables" / "phase1_trend_estimates.csv"

SCENARIO_COLORS = {
    "base_input_case": "tab:blue",
    "capex_rich": "tab:green",
    "chip_bottleneck": "tab:red",
    "power_datacenter_bottleneck": "tab:orange",
}
CONSTRAINT_COLORS = {
    "chip": "#d62728",
    "power": "#ff7f0e",
    "datacenter": "#9467bd",
    "capex": "#2ca02c",
}


def get_phase1_rule_a_2018_fit() -> tuple[float, float, float]:
    t = pd.read_csv(PHASE1_TREND_TABLE)
    row = t[
        (t["trend_name"] == "training_compute")
        & (t["frontier_rule"] == "frontier_rule_a_2018+")
    ]
    slope = float(row["slope_log10_per_year"].iloc[0])
    mult = float(row["annual_growth_multiplier"].iloc[0])
    intercept = 25.0 - slope * 2024.0  # anchor 2024 frontier run = 1e25 FLOP
    return slope, intercept, mult


def main() -> None:
    print("[1/8] Loading scenarios + projecting...")
    assumptions = load_assumptions()
    scenarios = load_all_scenarios()
    frames = [project_scenario(s, assumptions) for s in scenarios]
    df = pd.concat(frames, ignore_index=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(PROCESSED_DIR / "phase2_fundamental_inputs.csv", index=False)
    df.to_csv(TABLES_DIR / "phase2_fundamental_inputs_by_year.csv", index=False)

    # ----- summary tables -----
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
            aggfunc={"binding_constraint": "first", "available_stock_h100e": "sum",
                     "usable_compute_flop_year": "sum",
                     "ai_power_capacity_mw": "sum",
                     "ai_infrastructure_capex_usd": "sum"},
        )
        .reset_index()
    )
    summary.to_csv(TABLES_DIR / "phase2_scenario_summary.csv", index=False)

    binding = (
        df.groupby(["scenario", "binding_constraint"])
        .size()
        .reset_index(name="years_binding")
        .sort_values(["scenario", "years_binding"], ascending=[True, False])
    )
    binding.to_csv(TABLES_DIR / "phase2_binding_constraints.csv", index=False)

    # Capex required vs available — rough check.
    capex_table = []
    for sc in scenarios:
        sub = df[df["scenario"] == sc.name].set_index("year")
        # Capex required to ADD this year's net new stock at this year's
        # cluster cost.
        delta_stock = sub["installed_stock_h100e_chip_limited"].diff().clip(lower=0)
        capex_required = (
            delta_stock
            * sub["accelerator_unit_cost_usd"]
            * sub["cluster_capex_multiplier"]
        )
        capex_available = sub["ai_infrastructure_capex_usd"]
        for y in sub.index:
            capex_table.append(
                {
                    "scenario": sc.name,
                    "year": y,
                    "capex_required_usd": float(capex_required.loc[y]),
                    "capex_available_usd": float(capex_available.loc[y]),
                    "capex_coverage_ratio": (
                        float(capex_required.loc[y] / capex_available.loc[y])
                        if capex_available.loc[y]
                        else float("nan")
                    ),
                }
            )
    pd.DataFrame(capex_table).to_csv(
        TABLES_DIR / "phase2_capex_requirements.csv", index=False
    )

    CHARTS_DIR.mkdir(parents=True, exist_ok=True)

    # ----- chart: accelerator stock -----
    print("[3/8] Chart: accelerator stock...")
    fig, ax = plt.subplots(figsize=(11, 7))
    for sc in scenarios:
        sub = df[df["scenario"] == sc.name]
        ax.plot(
            sub["year"], sub["available_stock_h100e"],
            marker="o", linewidth=2,
            color=SCENARIO_COLORS.get(sc.name, "grey"),
            label=sc.display_name,
        )
    ax.set_yscale("log")
    ax.set_xlabel("Year")
    ax.set_ylabel("Available installed stock (H100-eq, log scale)")
    ax.set_title("Phase 2 — installed H100-equivalent stock by scenario, 2024–2040")
    ax.grid(True, which="both", alpha=0.25)
    ax.legend(loc="lower right", framealpha=0.9)
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "phase2_accelerator_stock_h100e.png", dpi=150)
    plt.close(fig)

    # ----- chart: theoretical compute capacity -----
    print("[4/8] Chart: theoretical + usable compute...")
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    for sc in scenarios:
        sub = df[df["scenario"] == sc.name]
        c = SCENARIO_COLORS.get(sc.name, "grey")
        axes[0].plot(sub["year"], sub["theoretical_compute_flop_year"], marker="o", linewidth=2, color=c, label=sc.display_name)
        axes[1].plot(sub["year"], sub["usable_compute_flop_year"], marker="o", linewidth=2, color=c, label=sc.display_name)
    for ax, title in zip(axes, ["Theoretical (chip stock × peak FLOP × s)", "Usable (× utilization, after constraints)"]):
        ax.set_yscale("log")
        ax.set_xlabel("Year")
        ax.set_ylabel("FLOP / year (log scale)")
        ax.set_title(title)
        ax.grid(True, which="both", alpha=0.25)
        ax.legend(loc="lower right", fontsize=9)
    fig.suptitle("Phase 2 — annual AI compute capacity by scenario")
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "phase2_theoretical_compute_capacity.png", dpi=150)
    plt.close(fig)

    # Also save a stand-alone usable_compute chart for the spec deliverable.
    fig, ax = plt.subplots(figsize=(11, 7))
    for sc in scenarios:
        sub = df[df["scenario"] == sc.name]
        ax.plot(sub["year"], sub["usable_compute_flop_year"],
                marker="o", linewidth=2,
                color=SCENARIO_COLORS.get(sc.name, "grey"),
                label=sc.display_name)
    ax.set_yscale("log")
    ax.set_xlabel("Year")
    ax.set_ylabel("Usable AI compute (FLOP / year, log scale)")
    ax.set_title("Phase 2 — usable AI compute capacity by scenario, 2024–2040 (sourced inputs)")
    ax.grid(True, which="both", alpha=0.25)
    ax.legend(loc="lower right", framealpha=0.9)
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "phase2_usable_compute_capacity.png", dpi=150)
    plt.close(fig)

    # ----- chart: power capacity constraint -----
    print("[5/8] Chart: power capacity + capex required...")
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    for sc in scenarios:
        sub = df[df["scenario"] == sc.name]
        c = SCENARIO_COLORS.get(sc.name, "grey")
        axes[0].plot(sub["year"], sub["ai_power_capacity_mw"], marker="o", linewidth=2, color=c, label=sc.display_name)
    axes[0].set_yscale("log")
    axes[0].set_xlabel("Year")
    axes[0].set_ylabel("AI data-center power capacity (MW, log scale)")
    axes[0].set_title("AI-DC installed power capacity")
    axes[0].grid(True, which="both", alpha=0.25)
    axes[0].legend(loc="lower right", fontsize=9)

    for sc in scenarios:
        sub = df[df["scenario"] == sc.name]
        c = SCENARIO_COLORS.get(sc.name, "grey")
        axes[1].plot(sub["year"], sub["power_limited_stock_h100e"], marker="o", linewidth=2, color=c, label=f"{sc.display_name} — power-lim")
        axes[1].plot(sub["year"], sub["datacenter_limited_stock_h100e"], marker="x", linewidth=1, alpha=0.6, color=c, linestyle="--")
    axes[1].set_yscale("log")
    axes[1].set_xlabel("Year")
    axes[1].set_ylabel("H100-eq stock supportable (log scale)")
    axes[1].set_title("Power-limited (solid) vs DC-packing-limited (dashed) stock")
    axes[1].grid(True, which="both", alpha=0.25)
    axes[1].legend(loc="lower right", fontsize=8)

    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "phase2_power_capacity_constraint.png", dpi=150)
    plt.close(fig)

    # Capex required chart
    cap_df = pd.read_csv(TABLES_DIR / "phase2_capex_requirements.csv")
    fig, ax = plt.subplots(figsize=(11, 7))
    for sc in scenarios:
        sub = cap_df[cap_df["scenario"] == sc.name]
        c = SCENARIO_COLORS.get(sc.name, "grey")
        ax.plot(sub["year"], sub["capex_required_usd"], marker="o", linewidth=2, color=c, label=f"{sc.display_name} — required")
        ax.plot(sub["year"], sub["capex_available_usd"], marker="x", linewidth=1, alpha=0.5, color=c, linestyle="--")
    ax.set_yscale("log")
    ax.set_xlabel("Year")
    ax.set_ylabel("USD/year (log scale)")
    ax.set_title("Phase 2 — capex required (solid) vs assumed-available (dashed), by scenario")
    ax.grid(True, which="both", alpha=0.25)
    ax.legend(loc="lower right", fontsize=8)
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "phase2_capex_required.png", dpi=150)
    plt.close(fig)

    # ----- chart: binding constraint heatmap -----
    print("[6/8] Chart: binding constraint heatmap...")
    fig, ax = plt.subplots(figsize=(12, 4))
    scenario_names = [s.name for s in scenarios]
    years = sorted(df["year"].unique().tolist())
    constraint_to_int = {c: i for i, c in enumerate(CONSTRAINTS)}
    grid = np.zeros((len(scenario_names), len(years)))
    for i, name in enumerate(scenario_names):
        sub = df[df["scenario"] == name].set_index("year")
        for j, y in enumerate(years):
            grid[i, j] = constraint_to_int[sub.loc[y, "binding_constraint"]]
    cmap = plt.cm.colors.ListedColormap([CONSTRAINT_COLORS[c] for c in CONSTRAINTS])
    ax.imshow(grid, aspect="auto", cmap=cmap, vmin=-0.5, vmax=len(CONSTRAINTS) - 0.5)
    ax.set_yticks(range(len(scenario_names)))
    ax.set_yticklabels([s.display_name for s in scenarios])
    ax.set_xticks(range(len(years)))
    ax.set_xticklabels([str(y) for y in years], rotation=45, fontsize=8)
    ax.set_title("Binding constraint by year and scenario (sourced inputs)")
    handles = [Patch(color=CONSTRAINT_COLORS[c], label=c) for c in CONSTRAINTS]
    ax.legend(handles=handles, loc="center left", bbox_to_anchor=(1.01, 0.5))
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "phase2_binding_constraint_by_year.png", dpi=150)
    plt.close(fig)

    # ----- chart: vs Phase 1 -----
    print("[7/8] Chart: vs Phase 1...")
    slope, intercept, mult = get_phase1_rule_a_2018_fit()
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    ax = axes[0]
    for sc in scenarios:
        sub = df[df["scenario"] == sc.name]
        ax.plot(sub["year"], sub["usable_compute_flop_year"], marker="o", linewidth=2, color=SCENARIO_COLORS.get(sc.name, "grey"), label=f"P2: {sc.display_name}")
    p1_years = np.linspace(2018, 2040, 200)
    p1_flop = 10 ** (intercept + slope * p1_years)
    ax.plot(p1_years, p1_flop, linestyle="--", color="black", linewidth=1.8,
            label=f"P1 Rule A 2018+ frontier-run fit ({mult:.2f}×/yr)")
    ax.set_yscale("log"); ax.set_xlabel("Year"); ax.set_ylabel("FLOP (log scale)")
    ax.set_title("Absolute levels\nP2 = total annual usable · P1 = single frontier run")
    ax.grid(True, which="both", alpha=0.25)
    ax.legend(loc="lower right", fontsize=8)

    ax = axes[1]
    for sc in scenarios:
        sub = df[df["scenario"] == sc.name].set_index("year")
        norm = sub["usable_compute_flop_year"] / sub.loc[2024, "usable_compute_flop_year"]
        ax.plot(norm.index, norm.values, marker="o", linewidth=2,
                color=SCENARIO_COLORS.get(sc.name, "grey"), label=sc.display_name)
    p1_norm = mult ** (np.array(years) - 2024)
    ax.plot(years, p1_norm, linestyle="--", color="black", linewidth=1.8,
            label=f"P1 frontier trend ({mult:.2f}×/yr)")
    ax.set_yscale("log"); ax.set_xlabel("Year"); ax.set_ylabel("Compute ÷ 2024 (log)")
    ax.set_title("Growth-rate comparison\nNormalized to 2024 = 1")
    ax.grid(True, which="both", alpha=0.25)
    ax.legend(loc="upper left", fontsize=8)
    fig.suptitle("Phase 2 (sourced) input-derived compute vs Phase 1 historical trend")
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "phase2_vs_phase1_compute_trend.png", dpi=150)
    plt.close(fig)

    # ----- chart: cost per H100e per year, three variants -----
    print("[8/8] Chart: cost variants + sensitivity bands...")
    fig, ax = plt.subplots(figsize=(11, 7))
    base_df = df[df["scenario"] == "base_input_case"]
    ax.plot(base_df["year"], base_df["cost_per_h100e_year_upfront"],
            marker="o", color="tab:blue", linewidth=2, label="Upfront-amortized (base scenario)")
    ax.plot(base_df["year"], base_df["cost_per_h100e_year_cloud"],
            marker="s", color="tab:orange", linewidth=2, label="Cloud-rental (base scenario)")
    ax.plot(base_df["year"], base_df["cost_per_h100e_year_blended"],
            marker="^", color="tab:green", linewidth=2, label="Blended 50/50 (base scenario)")
    # Add chip_bottleneck cloud as comparison
    cb_df = df[df["scenario"] == "chip_bottleneck"]
    ax.plot(cb_df["year"], cb_df["cost_per_h100e_year_cloud"],
            marker="s", color="tab:red", linewidth=1, alpha=0.5, linestyle="--",
            label="Cloud-rental (chip-bottleneck)")
    ax.set_yscale("log")
    ax.set_xlabel("Year")
    ax.set_ylabel("Cost per H100-eq per year (USD, log scale)")
    ax.set_title(
        "Phase 2 — cost per H100-eq accelerator-year by cost variant\n"
        "Preserves Phase 1 finding: cost-variant divergence is real and persistent"
    )
    ax.grid(True, which="both", alpha=0.25)
    ax.legend(loc="upper right", fontsize=9)
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "phase2_cost_per_h100e_by_variant.png", dpi=150)
    plt.close(fig)

    # Sensitivity bands on three key inputs.
    base_scenario = next(s for s in scenarios if s.name == "base_input_case")
    multipliers = [0.5, 0.75, 1.0, 1.5, 2.0]
    fig, axes = plt.subplots(1, 3, figsize=(16, 5), sharey=True)
    sens_params = [
        ("h100_equivalent_shipments", "Shipments"),
        ("ai_datacenter_capacity_mw", "AI-DC capacity (MW)"),
        ("ai_infrastructure_capex_usd", "Capex available"),
    ]
    sens_rows = []
    for ax, (param, label) in zip(axes, sens_params):
        sens = sensitivity_analysis(
            base_scenario, assumptions, parameter=param, multipliers=multipliers
        )
        sens_rows.append(sens)
        for m in multipliers:
            sub = sens[sens["sensitivity_multiplier"] == m]
            ax.plot(sub["year"], sub["usable_compute_flop_year"],
                    label=f"{m:.2f}×", linewidth=2)
        ax.set_yscale("log")
        ax.set_xlabel("Year")
        ax.set_title(f"Sensitivity: {label}")
        ax.grid(True, which="both", alpha=0.25)
        ax.legend(loc="lower right", fontsize=8)
    axes[0].set_ylabel("Usable compute (FLOP/yr, log)")
    fig.suptitle("Phase 2 — sensitivity of usable compute to one-parameter perturbations of base scenario")
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "phase2_sensitivity_bands.png", dpi=150)
    plt.close(fig)

    # Sensitivity table
    pd.concat(sens_rows, ignore_index=True).to_csv(
        TABLES_DIR / "phase2_sensitivity_analysis.csv", index=False
    )

    # ----- console summary -----
    print("\n=== Phase 2 sprint-2 summary (sourced inputs) ===")
    for sc in scenarios:
        sub = df[df["scenario"] == sc.name].set_index("year")
        v24 = sub.loc[2024, "usable_compute_flop_year"]
        v40 = sub.loc[2040, "usable_compute_flop_year"]
        cagr = (v40 / v24) ** (1 / 16) - 1
        print(
            f"  {sc.name:32s} 2024={v24:.2e} → 2040={v40:.2e}  "
            f"CAGR={cagr*100:.1f}%/yr  binding(2030)={sub.loc[2030, 'binding_constraint']}"
        )
    print(f"\n  P1 Rule A 2018+ historical multiplier: {mult:.2f}×/yr")


if __name__ == "__main__":
    main()
