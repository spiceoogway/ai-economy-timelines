"""Phase 2 sprint-1 driver.

Run with: `uv run python notebooks/run_phase2_sprint1.py`

Produces:
  outputs/tables/phase2_fundamental_inputs_by_year.csv
  outputs/tables/phase2_scenario_summary.csv
  outputs/tables/phase2_binding_constraints.csv
  outputs/charts/phase2_usable_compute_capacity.png
  outputs/charts/phase2_binding_constraint_by_year.png
  outputs/charts/phase2_vs_phase1_compute_trend.png

NOTE: input assumptions are sprint-1 round-number placeholders. See
docs/phase2_initial_notes.md for what sprint 2 needs to replace.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from model.fundamental_inputs import (
    CONSTRAINTS,
    load_all_scenarios,
    load_assumptions,
    project_scenario,
)

CHARTS_DIR = REPO_ROOT / "outputs" / "charts"
TABLES_DIR = REPO_ROOT / "outputs" / "tables"

# Phase 1 handoff (Rule A 2018+ from outputs/tables/phase1_trend_estimates.csv).
PHASE1_RULE_A_2018_SLOPE = 0.776294  # log10 per year
PHASE1_RULE_A_2018_INTERCEPT = -1542.8516  # solved so that 10**(intercept + slope*2024)
# is consistent with the historical fit.
# We re-derive these at runtime from the Phase 1 table to stay in sync.

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
    """Return (slope_log10_per_year, intercept_log10, annual_multiplier)
    for Phase 1 Rule A 2018+ training-compute trend."""
    if not PHASE1_TREND_TABLE.exists():
        # Fallback to the cached value from sprint 1.
        return 0.776294, PHASE1_RULE_A_2018_INTERCEPT, 10**0.776294
    t = pd.read_csv(PHASE1_TREND_TABLE)
    row = t[
        (t["trend_name"] == "training_compute")
        & (t["frontier_rule"] == "frontier_rule_a_2018+")
    ]
    if row.empty:
        return 0.776294, PHASE1_RULE_A_2018_INTERCEPT, 10**0.776294
    slope = float(row["slope_log10_per_year"].iloc[0])
    mult = float(row["annual_growth_multiplier"].iloc[0])
    # Use the table's reported 2024 typical frontier compute as the
    # anchor: from Phase 1, frontier 2024 models are ~1e25-1e26 FLOP.
    # We anchor at 1e25 FLOP at year 2024, then continue with the slope.
    anchor_year = 2024.0
    anchor_log10 = 25.0  # ~1e25 FLOP per single frontier run
    intercept = anchor_log10 - slope * anchor_year
    return slope, intercept, mult


def main() -> None:
    print("[1/5] Loading scenarios + projecting...")
    assumptions = load_assumptions()
    scenarios = load_all_scenarios()
    frames = []
    for s in scenarios:
        print(f"      → {s.name}")
        frames.append(project_scenario(s, assumptions))
    df = pd.concat(frames, ignore_index=True)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(TABLES_DIR / "phase2_fundamental_inputs_by_year.csv", index=False)

    # ----- summary tables -----
    print("[2/5] Writing summary tables...")
    summary_years = [2024, 2025, 2027, 2030, 2035, 2040]
    summary = (
        df[df["year"].isin(summary_years)]
        .pivot_table(
            index=["scenario", "year"],
            values=[
                "available_stock_h100e",
                "usable_compute_flop_year",
                "ai_power_capacity_mw",
                "ai_infrastructure_capex_usd",
            ],
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

    # ----- chart 1: usable compute capacity over time -----
    print("[3/5] Chart: usable compute capacity by scenario...")
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(11, 7))
    for sc in scenarios:
        sub = df[df["scenario"] == sc.name]
        ax.plot(
            sub["year"],
            sub["usable_compute_flop_year"],
            marker="o",
            linewidth=2,
            color=SCENARIO_COLORS.get(sc.name, "grey"),
            label=f"{sc.display_name}",
        )
    ax.set_yscale("log")
    ax.set_xlabel("Year")
    ax.set_ylabel("Usable AI compute capacity (FLOP / year, log scale)")
    ax.set_title(
        "Phase 2 — usable AI compute capacity by scenario, 2024–2040\n"
        "Sprint 1 placeholder assumptions; absolute levels are illustrative"
    )
    ax.grid(True, which="both", alpha=0.25)
    ax.legend(loc="lower right", framealpha=0.9)
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "phase2_usable_compute_capacity.png", dpi=150)
    plt.close(fig)

    # ----- chart 2: binding constraint by year (heatmap-style) -----
    print("[4/5] Chart: binding constraint by year per scenario...")
    fig, ax = plt.subplots(figsize=(12, 4))
    scenario_names = [s.name for s in scenarios]
    years = sorted(df["year"].unique().tolist())
    constraint_to_int = {c: i for i, c in enumerate(CONSTRAINTS)}
    grid = np.zeros((len(scenario_names), len(years)))
    for i, name in enumerate(scenario_names):
        sub = df[df["scenario"] == name].set_index("year")
        for j, y in enumerate(years):
            grid[i, j] = constraint_to_int[sub.loc[y, "binding_constraint"]]
    cmap = plt.cm.colors.ListedColormap(
        [CONSTRAINT_COLORS[c] for c in CONSTRAINTS]
    )
    ax.imshow(grid, aspect="auto", cmap=cmap, vmin=-0.5, vmax=len(CONSTRAINTS) - 0.5)
    ax.set_yticks(range(len(scenario_names)))
    ax.set_yticklabels([s.display_name for s in scenarios])
    ax.set_xticks(range(len(years)))
    ax.set_xticklabels([str(y) for y in years], rotation=45, fontsize=8)
    ax.set_title("Binding constraint by year and scenario")
    # Legend
    from matplotlib.patches import Patch
    handles = [Patch(color=CONSTRAINT_COLORS[c], label=c) for c in CONSTRAINTS]
    ax.legend(handles=handles, loc="center left", bbox_to_anchor=(1.01, 0.5))
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "phase2_binding_constraint_by_year.png", dpi=150)
    plt.close(fig)

    # ----- chart 3: Phase 2 vs Phase 1 historical trend -----
    print("[5/5] Chart: Phase 2 vs Phase 1 trend...")
    slope, intercept, mult = get_phase1_rule_a_2018_fit()
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Left panel: absolute scales — Phase 2 in FLOP/year (total annual
    # compute), Phase 1 fit in FLOP/single-frontier-run, both on log y.
    ax = axes[0]
    for sc in scenarios:
        sub = df[df["scenario"] == sc.name]
        ax.plot(
            sub["year"],
            sub["usable_compute_flop_year"],
            marker="o",
            linewidth=2,
            color=SCENARIO_COLORS.get(sc.name, "grey"),
            label=f"P2 usable: {sc.display_name}",
        )
    p1_years = np.linspace(2018, 2040, 200)
    p1_flop = 10 ** (intercept + slope * p1_years)
    ax.plot(
        p1_years,
        p1_flop,
        linestyle="--",
        color="black",
        linewidth=1.8,
        label=f"P1 Rule A 2018+ frontier-run fit ({mult:.2f}×/yr, doubling 4.7 mo)",
    )
    ax.set_yscale("log")
    ax.set_xlabel("Year")
    ax.set_ylabel("FLOP (log scale)")
    ax.set_title(
        "Absolute levels\n"
        "Phase 2 = total annual usable compute · Phase 1 = single frontier run"
    )
    ax.grid(True, which="both", alpha=0.25)
    ax.legend(loc="lower right", fontsize=8)

    # Right panel: growth-rate comparison. Normalize each Phase 2 scenario
    # to its 2024 value and overlay an equivalent 6×/yr line.
    ax = axes[1]
    for sc in scenarios:
        sub = df[df["scenario"] == sc.name].set_index("year")
        norm = sub["usable_compute_flop_year"] / sub.loc[2024, "usable_compute_flop_year"]
        ax.plot(
            norm.index,
            norm.values,
            marker="o",
            linewidth=2,
            color=SCENARIO_COLORS.get(sc.name, "grey"),
            label=sc.display_name,
        )
    # Phase 1 6×/yr from 2024 baseline.
    p1_norm = mult ** (np.array(years) - 2024)
    ax.plot(
        years,
        p1_norm,
        linestyle="--",
        color="black",
        linewidth=1.8,
        label=f"P1 frontier trend ({mult:.2f}×/yr)",
    )
    ax.set_yscale("log")
    ax.set_xlabel("Year")
    ax.set_ylabel("Compute relative to 2024 (log scale)")
    ax.set_title(
        "Growth-rate comparison\n"
        "Phase 2 scenarios normalized to 2024 = 1"
    )
    ax.grid(True, which="both", alpha=0.25)
    ax.legend(loc="upper left", fontsize=8)

    fig.suptitle(
        "Phase 2 input-derived compute vs Phase 1 historical trend",
        fontsize=12,
    )
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "phase2_vs_phase1_compute_trend.png", dpi=150)
    plt.close(fig)

    # ----- console summary -----
    print("\n=== Phase 2 sprint-1 summary ===")
    for sc in scenarios:
        sub = df[df["scenario"] == sc.name].set_index("year")
        v24 = sub.loc[2024, "usable_compute_flop_year"]
        v40 = sub.loc[2040, "usable_compute_flop_year"]
        cagr = (v40 / v24) ** (1 / 16) - 1
        print(
            f"  {sc.name:32s} 2024={v24:.2e} → 2040={v40:.2e}  "
            f"CAGR={cagr*100:.1f}%/yr  binding(2030)={sub.loc[2030, 'binding_constraint']}"
        )
    print(
        f"\n  P1 Rule A 2018+ historical multiplier: {mult:.2f}×/yr "
        f"({(mult-1)*100:.0f}% CAGR — for comparison with above)"
    )


if __name__ == "__main__":
    main()
