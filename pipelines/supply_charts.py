"""Supply-side chart helpers.

One function per output PNG. Each helper takes the projection DataFrame
(or a derivative), the list of scenarios, and an output path. Styling
constants (colors, source line) come from `model.runtime`.

Historical-baseline charts live in `model/historical_charts.py` — kept
separate because they consume the Epoch-models DataFrame on
`release_year_fractional` while supply charts consume the projection
DataFrame on `year`. Different data shapes, different x-axes,
different idioms.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch

from model.runtime import CONSTRAINT_COLORS, SCENARIO_COLORS, SCENARIO_MARKERS
from model.supply_engine import CONSTRAINTS, ScenarioConfig

# Slight transparency on supply line plots so overlapping scenarios still
# read as distinct visually.
_LINE_ALPHA = 0.85


def _scenario_color(name: str) -> str:
    return SCENARIO_COLORS.get(name, "grey")


def _scenario_marker(name: str) -> str:
    return SCENARIO_MARKERS.get(name, "o")


def _detect_overlapping_scenarios(
    df: pd.DataFrame, scenarios: list[ScenarioConfig], value_col: str
) -> list[list[str]]:
    """Return groups of scenario names that share an identical trajectory in
    `value_col`. Used to annotate charts when scenarios overplot."""
    groups: dict[tuple, list[str]] = {}
    for sc in scenarios:
        sub = df[df["scenario"] == sc.name].sort_values("year")
        traj = tuple(sub[value_col].round(6).values)
        groups.setdefault(traj, []).append(sc.display_name)
    return [g for g in groups.values() if len(g) > 1]


def _annotate_overlap(ax, overlap_groups: list[list[str]]) -> None:
    """If any scenarios share trajectories, add a small text annotation."""
    if not overlap_groups:
        return
    lines = ["Note: scenarios with identical trajectories:"]
    for grp in overlap_groups:
        lines.append("  " + " = ".join(grp))
    ax.text(
        0.02, 0.98, "\n".join(lines),
        transform=ax.transAxes,
        ha="left", va="top",
        fontsize=7.5, color="#444",
        bbox=dict(boxstyle="round,pad=0.3",
                  facecolor="white", edgecolor="#bbb", alpha=0.9),
    )


def chart_accelerator_stock(
    df: pd.DataFrame, scenarios: list[ScenarioConfig], out: Path
) -> None:
    fig, ax = plt.subplots(figsize=(11, 7))
    for sc in scenarios:
        sub = df[df["scenario"] == sc.name]
        ax.plot(
            sub["year"],
            sub["available_stock_h100e"],
            marker=_scenario_marker(sc.name),
            linewidth=2,
            alpha=_LINE_ALPHA,
            color=_scenario_color(sc.name),
            label=sc.display_name,
        )
    ax.set_yscale("log")
    ax.set_xlabel("Year")
    ax.set_ylabel("Available installed stock (H100-eq, log scale)")
    ax.set_title("Installed H100-equivalent stock by scenario, 2024–2040")
    ax.grid(True, which="both", alpha=0.25)
    ax.legend(loc="lower right", framealpha=0.9)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


def chart_theoretical_and_usable_compute(
    df: pd.DataFrame, scenarios: list[ScenarioConfig], out: Path
) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    for sc in scenarios:
        sub = df[df["scenario"] == sc.name]
        c = _scenario_color(sc.name)
        m = _scenario_marker(sc.name)
        axes[0].plot(
            sub["year"], sub["theoretical_compute_flop_year"],
            marker=m, linewidth=2, alpha=_LINE_ALPHA, color=c, label=sc.display_name,
        )
        axes[1].plot(
            sub["year"], sub["usable_compute_flop_year"],
            marker=m, linewidth=2, alpha=_LINE_ALPHA, color=c, label=sc.display_name,
        )
    titles = [
        "Theoretical (chip stock × peak FLOP × s)",
        "Usable (× utilization, after constraints)",
    ]
    for ax, title in zip(axes, titles):
        ax.set_yscale("log")
        ax.set_xlabel("Year")
        ax.set_ylabel("FLOP / year (log scale)")
        ax.set_title(title)
        ax.grid(True, which="both", alpha=0.25)
        ax.legend(loc="lower right", fontsize=9)
    fig.suptitle("Annual AI compute capacity by scenario")
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


def chart_usable_compute_capacity(
    df: pd.DataFrame, scenarios: list[ScenarioConfig], out: Path
) -> None:
    fig, ax = plt.subplots(figsize=(11, 7))
    for sc in scenarios:
        sub = df[df["scenario"] == sc.name]
        ax.plot(
            sub["year"], sub["usable_compute_flop_year"],
            marker=_scenario_marker(sc.name), linewidth=2,
            alpha=_LINE_ALPHA,
            color=_scenario_color(sc.name),
            label=sc.display_name,
        )
    ax.set_yscale("log")
    ax.set_xlabel("Year")
    ax.set_ylabel("Usable AI compute (FLOP / year, log scale)")
    ax.set_title(
        "Usable AI compute capacity by scenario, 2024–2040 (sourced inputs)"
    )
    ax.grid(True, which="both", alpha=0.25)
    ax.legend(loc="lower right", framealpha=0.9)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


def chart_power_capacity_constraint(
    df: pd.DataFrame, scenarios: list[ScenarioConfig], out: Path
) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    for sc in scenarios:
        sub = df[df["scenario"] == sc.name]
        c = _scenario_color(sc.name)
        axes[0].plot(
            sub["year"], sub["ai_power_capacity_mw"],
            marker=_scenario_marker(sc.name), linewidth=2, alpha=_LINE_ALPHA,
            color=c, label=sc.display_name,
        )
    axes[0].set_yscale("log")
    axes[0].set_xlabel("Year")
    axes[0].set_ylabel("AI data-center power capacity (MW, log scale)")
    axes[0].set_title("AI-DC installed power capacity")
    axes[0].grid(True, which="both", alpha=0.25)
    axes[0].legend(loc="lower right", fontsize=9)
    _annotate_overlap(
        axes[0], _detect_overlapping_scenarios(df, scenarios, "ai_power_capacity_mw")
    )

    for sc in scenarios:
        sub = df[df["scenario"] == sc.name]
        c = _scenario_color(sc.name)
        m = _scenario_marker(sc.name)
        axes[1].plot(
            sub["year"], sub["power_limited_stock_h100e"],
            marker=m, linewidth=2, alpha=_LINE_ALPHA, color=c,
            label=f"{sc.display_name} — power-lim",
        )
        axes[1].plot(
            sub["year"], sub["datacenter_limited_stock_h100e"],
            marker="x", linewidth=1, alpha=0.6, color=c, linestyle="--",
        )
    axes[1].set_yscale("log")
    axes[1].set_xlabel("Year")
    axes[1].set_ylabel("H100-eq stock supportable (log scale)")
    axes[1].set_title("Power-limited (solid) vs DC-packing-limited (dashed) stock")
    axes[1].grid(True, which="both", alpha=0.25)
    axes[1].legend(loc="lower right", fontsize=8)

    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


def chart_capex_required(
    capex_df: pd.DataFrame, scenarios: list[ScenarioConfig], out: Path
) -> None:
    fig, ax = plt.subplots(figsize=(11, 7))
    for sc in scenarios:
        sub = capex_df[capex_df["scenario"] == sc.name]
        c = _scenario_color(sc.name)
        m = _scenario_marker(sc.name)
        ax.plot(
            sub["year"], sub["capex_required_usd"],
            marker=m, linewidth=2, alpha=_LINE_ALPHA, color=c,
            label=f"{sc.display_name} — required",
        )
        ax.plot(
            sub["year"], sub["capex_available_usd"],
            marker=m, linewidth=1, alpha=0.55, color=c, linestyle="--",
            label=f"{sc.display_name} — available",
        )
    ax.set_yscale("log")
    ax.set_xlabel("Year")
    ax.set_ylabel("USD/year (log scale)")
    ax.set_title(
        "Capex required (solid) vs assumed-available (dashed), by scenario"
    )
    ax.grid(True, which="both", alpha=0.25)
    ax.legend(loc="lower right", fontsize=7, ncol=2)
    _annotate_overlap(
        ax, _detect_overlapping_scenarios(capex_df, scenarios, "capex_available_usd")
    )
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


def chart_binding_constraint_heatmap(
    df: pd.DataFrame,
    scenarios: list[ScenarioConfig],
    years: list[int],
    out: Path,
) -> None:
    fig, ax = plt.subplots(figsize=(12, 4))
    scenario_names = [s.name for s in scenarios]
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
    fig.savefig(out, dpi=150)
    plt.close(fig)


def chart_vs_historical_compute_trend(
    df: pd.DataFrame,
    scenarios: list[ScenarioConfig],
    historical_fit: tuple[float, float, float],
    years: list[int],
    out: Path,
) -> None:
    """historical_fit is (slope_log10_per_year, intercept_log10, annual_multiplier)."""
    slope, intercept, mult = historical_fit
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Left: absolute levels
    ax = axes[0]
    for sc in scenarios:
        sub = df[df["scenario"] == sc.name]
        ax.plot(
            sub["year"], sub["usable_compute_flop_year"],
            marker=_scenario_marker(sc.name), linewidth=2,
            alpha=_LINE_ALPHA,
            color=_scenario_color(sc.name),
            label=f"supply: {sc.display_name}",
        )
    hist_years = np.linspace(2018, 2040, 200)
    hist_flop = 10 ** (intercept + slope * hist_years)
    ax.plot(
        hist_years, hist_flop,
        linestyle="--", color="black", linewidth=1.8,
        label=f"historical Rule A 2018+ frontier-run fit ({mult:.2f}×/yr)",
    )
    ax.set_yscale("log")
    ax.set_xlabel("Year")
    ax.set_ylabel("FLOP (log scale)")
    ax.set_title(
        "Absolute levels\nsupply = total annual usable · historical = single frontier run"
    )
    ax.grid(True, which="both", alpha=0.25)
    ax.legend(loc="lower right", fontsize=8)

    # Right: growth-rate comparison (normalized to 2024 = 1)
    ax = axes[1]
    for sc in scenarios:
        sub = df[df["scenario"] == sc.name].set_index("year")
        norm = sub["usable_compute_flop_year"] / sub.loc[2024, "usable_compute_flop_year"]
        ax.plot(
            norm.index, norm.values,
            marker=_scenario_marker(sc.name), linewidth=2,
            alpha=_LINE_ALPHA,
            color=_scenario_color(sc.name),
            label=sc.display_name,
        )
    hist_norm = mult ** (np.array(years) - 2024)
    ax.plot(
        years, hist_norm,
        linestyle="--", color="black", linewidth=1.8,
        label=f"historical frontier trend ({mult:.2f}×/yr)",
    )
    ax.set_yscale("log")
    ax.set_xlabel("Year")
    ax.set_ylabel("Compute ÷ 2024 (log)")
    ax.set_title("Growth-rate comparison\nNormalized to 2024 = 1")
    ax.grid(True, which="both", alpha=0.25)
    ax.legend(loc="upper left", fontsize=8)

    fig.suptitle("Supply input-derived compute vs historical baseline trend")
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


def chart_cost_per_h100e_by_variant(df: pd.DataFrame, out: Path) -> None:
    fig, ax = plt.subplots(figsize=(11, 7))
    base_df = df[df["scenario"] == "base_input_case"]
    ax.plot(
        base_df["year"], base_df["cost_per_h100e_year_upfront"],
        marker="o", color="tab:blue", linewidth=2,
        label="Upfront-amortized (base scenario)",
    )
    ax.plot(
        base_df["year"], base_df["cost_per_h100e_year_cloud"],
        marker="s", color="tab:orange", linewidth=2,
        label="Cloud-rental (base scenario)",
    )
    ax.plot(
        base_df["year"], base_df["cost_per_h100e_year_blended"],
        marker="^", color="tab:green", linewidth=2,
        label="Blended 50/50 (base scenario)",
    )
    cb_df = df[df["scenario"] == "chip_bottleneck"]
    ax.plot(
        cb_df["year"], cb_df["cost_per_h100e_year_cloud"],
        marker="s", color="tab:red", linewidth=1, alpha=0.5, linestyle="--",
        label="Cloud-rental (chip-bottleneck)",
    )
    ax.set_yscale("log")
    ax.set_xlabel("Year")
    ax.set_ylabel("Cost per H100-eq per year (USD, log scale)")
    ax.set_title(
        "Cost per H100-eq accelerator-year by cost variant\n"
        "Preserves historical-baseline finding: cost-variant divergence is real and persistent"
    )
    ax.grid(True, which="both", alpha=0.25)
    ax.legend(loc="upper right", fontsize=9)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


def chart_sensitivity_bands(
    sens_frames: list[pd.DataFrame],
    params: list[tuple[str, str]],
    multipliers: list[float],
    out: Path,
) -> None:
    """Each entry in `sens_frames` corresponds to one entry in `params`."""
    fig, axes = plt.subplots(1, len(params), figsize=(16, 5), sharey=True)
    for ax, sens, (_, label) in zip(axes, sens_frames, params):
        for m in multipliers:
            sub = sens[sens["sensitivity_multiplier"] == m]
            ax.plot(
                sub["year"], sub["usable_compute_flop_year"],
                label=f"{m:.2f}×", linewidth=2,
            )
        ax.set_yscale("log")
        ax.set_xlabel("Year")
        ax.set_title(f"Sensitivity: {label}")
        ax.grid(True, which="both", alpha=0.25)
        ax.legend(loc="lower right", fontsize=8)
    axes[0].set_ylabel("Usable compute (FLOP/yr, log)")
    fig.suptitle(
        "Sensitivity of usable compute to one-parameter perturbations of base scenario"
    )
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)
