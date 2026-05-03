"""Allocation chart helpers.

Six PNGs under outputs/charts/allocation_*. Styling constants come from
model.runtime; allocation-side colors are distinct from supply-side
colors so scenario-grid charts can colour both axes independently.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from model.allocation_engine import BUCKET_COMPUTE_COLUMNS, BUCKET_SHARES
from model.runtime import (
    ALLOCATION_SCENARIO_COLORS,
    ALLOCATION_SCENARIO_MARKERS,
    BUCKET_COLORS,
    SCENARIO_COLORS,
    SCENARIO_MARKERS,
)

_LINE_ALPHA = 0.85


def _alloc_color(name: str) -> str:
    return ALLOCATION_SCENARIO_COLORS.get(name, "grey")


def _alloc_marker(name: str) -> str:
    return ALLOCATION_SCENARIO_MARKERS.get(name, "o")


def _supply_color(name: str) -> str:
    return SCENARIO_COLORS.get(name, "grey")


def _supply_marker(name: str) -> str:
    return SCENARIO_MARKERS.get(name, "o")


def _bucket_label(col: str) -> str:
    """Pretty label for a bucket name."""
    return col.replace("_compute_flop_year", "").replace("_", " ").title()


# ---- 1. stacked area: compute by bucket (base × base) ------------------


def chart_compute_by_bucket(df: pd.DataFrame, out: Path) -> None:
    """Stacked area chart of compute by bucket under base supply + base allocation."""
    sub = df[
        (df["supply_scenario"] == "base_input_case")
        & (df["allocation_scenario"] == "allocation_base")
    ].sort_values("year")
    fig, ax = plt.subplots(figsize=(11, 7))
    bucket_keys = [
        ("inference", "inference_compute_flop_year"),
        ("training", "training_compute_flop_year"),
        ("ai_rnd_experiment", "ai_rnd_experiment_compute_flop_year"),
        ("post_training", "post_training_compute_flop_year"),
        ("safety_eval", "safety_eval_compute_flop_year"),
        ("reserved_idle_fragmented", "reserved_idle_fragmented_compute_flop_year"),
    ]
    ys = [sub[col].values for _, col in bucket_keys]
    colors = [BUCKET_COLORS[name] for name, _ in bucket_keys]
    labels = [_bucket_label(col) for _, col in bucket_keys]
    ax.stackplot(sub["year"], ys, colors=colors, labels=labels, alpha=0.85)
    ax.set_yscale("log")
    ax.set_xlabel("Year")
    ax.set_ylabel("Compute (FLOP / year, log scale)")
    ax.set_title(
        "Allocation buckets under base supply × base allocation, 2024–2040"
    )
    ax.grid(True, which="both", alpha=0.25)
    ax.legend(loc="lower right", fontsize=9, framealpha=0.9)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


# ---- 2. largest frontier run by combined scenario ----------------------


def chart_largest_frontier_run(df: pd.DataFrame, out: Path) -> None:
    """16 lines (one per combined scenario) — color by allocation, marker by supply."""
    fig, ax = plt.subplots(figsize=(13, 8))
    for combined, sub in df.groupby("combined_scenario"):
        sub = sub.sort_values("year")
        alloc = sub["allocation_scenario"].iloc[0]
        supply = sub["supply_scenario"].iloc[0]
        ax.plot(
            sub["year"], sub["largest_frontier_run_flop"],
            color=_alloc_color(alloc),
            marker=_supply_marker(supply),
            linewidth=1.5,
            alpha=_LINE_ALPHA,
            markersize=5,
            label=combined,
        )
    ax.set_yscale("log")
    ax.set_xlabel("Year")
    ax.set_ylabel("Largest frontier training run (FLOP, log scale)")
    ax.set_title(
        "Largest frontier training run by combined scenario "
        "(4 supply × 4 allocation = 16)\n"
        "Color = allocation scenario, marker = supply scenario"
    )
    ax.grid(True, which="both", alpha=0.25)
    ax.legend(loc="lower right", fontsize=6, ncol=2, framealpha=0.9)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


# ---- 3. allocation vs historical training compute -----------------------


def chart_vs_historical_training_compute(
    vs_hist_df: pd.DataFrame,
    historical_fit: tuple[float, float, float],
    out: Path,
) -> None:
    """Historical Rule A 2018+ extrapolation overlaid against allocation-
    derived single-frontier-run projections (16 scenarios)."""
    slope, intercept, mult = historical_fit
    fig, ax = plt.subplots(figsize=(13, 8))

    # Allocation projections
    for combined, sub in vs_hist_df.groupby("scenario"):
        sub = sub.sort_values("year")
        alloc = sub["allocation_scenario"].iloc[0]
        supply = sub["supply_scenario"].iloc[0]
        ax.plot(
            sub["year"], sub["projected_largest_frontier_run_flop"],
            color=_alloc_color(alloc),
            marker=_supply_marker(supply),
            linewidth=1.2,
            alpha=0.6,
            markersize=4,
            label=combined if alloc == "allocation_base" else None,
        )

    # Historical extrapolation
    years = np.linspace(2018, 2040, 200)
    hist = 10 ** (intercept + slope * years)
    ax.plot(
        years, hist,
        linestyle="--", color="black", linewidth=2.0,
        label=f"Historical Rule A 2018+ ({mult:.2f}×/yr)",
    )

    ax.set_yscale("log")
    ax.set_xlabel("Year")
    ax.set_ylabel("Frontier training-run compute (FLOP, log scale)")
    ax.set_title(
        "Historical frontier-run trend vs allocation-derived projections\n"
        "Allocation projections are color-coded by allocation scenario; "
        "marker = supply scenario"
    )
    ax.grid(True, which="both", alpha=0.25)
    ax.legend(loc="lower right", fontsize=7, ncol=2)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


# ---- 4. training vs inference share by allocation scenario --------------


def chart_training_vs_inference_share(df: pd.DataFrame, out: Path) -> None:
    """One row per allocation scenario; supply scenario doesn't change shares."""
    sub = df.drop_duplicates(subset=["allocation_scenario", "year"]).sort_values(
        ["allocation_scenario", "year"]
    )
    fig, axes = plt.subplots(1, 2, figsize=(14, 6), sharey=True)
    for alloc, group in sub.groupby("allocation_scenario"):
        c = _alloc_color(alloc)
        m = _alloc_marker(alloc)
        axes[0].plot(
            group["year"], group["training_share"],
            color=c, marker=m, linewidth=2, alpha=_LINE_ALPHA,
            label=alloc,
        )
        axes[1].plot(
            group["year"], group["inference_share"],
            color=c, marker=m, linewidth=2, alpha=_LINE_ALPHA,
            label=alloc,
        )
    for ax, title in zip(axes, ["Training share", "Inference share"]):
        ax.set_xlabel("Year")
        ax.set_ylabel("Share of total usable compute")
        ax.set_title(title)
        ax.grid(True, which="both", alpha=0.25)
        ax.set_ylim(0, 1)
        ax.legend(loc="upper right", fontsize=9)
    fig.suptitle("Training and inference shares over time by allocation scenario")
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


# ---- 5. frontier-run share of total compute -----------------------------


def chart_frontier_run_share_of_total(df: pd.DataFrame, out: Path) -> None:
    """How much of total usable compute goes to the single largest run, by
    combined scenario."""
    fig, ax = plt.subplots(figsize=(13, 7))
    for combined, sub in df.groupby("combined_scenario"):
        sub = sub.sort_values("year")
        alloc = sub["allocation_scenario"].iloc[0]
        supply = sub["supply_scenario"].iloc[0]
        ax.plot(
            sub["year"], sub["frontier_run_share_of_total_compute"] * 100,
            color=_alloc_color(alloc),
            marker=_supply_marker(supply),
            linewidth=1.4,
            alpha=_LINE_ALPHA,
            markersize=5,
            label=combined,
        )
    ax.set_yscale("log")
    ax.set_xlabel("Year")
    ax.set_ylabel("Largest frontier run as % of total usable compute (log)")
    ax.set_title(
        "Largest frontier run as a share of total usable compute\n"
        "Falls in every scenario as total compute scales faster than any single run"
    )
    ax.grid(True, which="both", alpha=0.25)
    ax.legend(loc="lower left", fontsize=6, ncol=2)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


# ---- 6. scenario grid (small multiples 4×4) -----------------------------


def chart_scenario_grid(df: pd.DataFrame, out: Path) -> None:
    """4×4 small-multiples grid: each cell shows largest_frontier_run_flop
    for one (supply, allocation) combination across years."""
    supply_order = ["base_input_case", "capex_rich",
                    "chip_bottleneck", "power_datacenter_bottleneck"]
    alloc_order = ["allocation_base", "allocation_inference_heavy",
                   "allocation_training_race", "allocation_rnd_acceleration"]
    fig, axes = plt.subplots(
        len(alloc_order), len(supply_order),
        figsize=(15, 12),
        sharex=True, sharey=True,
    )
    for i, alloc in enumerate(alloc_order):
        for j, supply in enumerate(supply_order):
            ax = axes[i, j]
            sub = df[
                (df["supply_scenario"] == supply)
                & (df["allocation_scenario"] == alloc)
            ].sort_values("year")
            ax.plot(
                sub["year"], sub["largest_frontier_run_flop"],
                color=_alloc_color(alloc), linewidth=2, alpha=_LINE_ALPHA,
                marker=_supply_marker(supply), markersize=4,
            )
            ax.set_yscale("log")
            ax.grid(True, which="both", alpha=0.2)
            if i == 0:
                ax.set_title(supply.replace("_", " "), fontsize=9)
            if j == 0:
                ax.set_ylabel(alloc.replace("allocation_", ""), fontsize=9)
            # Annotate 2024 and 2040 values
            if not sub.empty:
                v_24 = sub.iloc[0]["largest_frontier_run_flop"]
                v_40 = sub.iloc[-1]["largest_frontier_run_flop"]
                ax.annotate(f"{v_24:.1e}", (sub.iloc[0]["year"], v_24),
                            xytext=(2, 6), textcoords="offset points", fontsize=7)
                ax.annotate(f"{v_40:.1e}", (sub.iloc[-1]["year"], v_40),
                            xytext=(-30, -10), textcoords="offset points", fontsize=7)

    fig.suptitle(
        "Largest frontier training run: 4 supply × 4 allocation = 16 combined scenarios\n"
        "(rows = allocation scenario, columns = supply scenario)",
        fontsize=12,
    )
    fig.text(0.5, 0.02, "Year", ha="center")
    fig.text(0.04, 0.5, "Largest frontier run (FLOP, log)",
             va="center", rotation="vertical")
    fig.tight_layout(rect=(0.05, 0.03, 1, 0.96))
    fig.savefig(out, dpi=150)
    plt.close(fig)
