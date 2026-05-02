"""Phase 1 chart helpers.

Each function takes the processed dataframe (and optionally a list of
TrendFit objects to overlay) and writes a single PNG. Consistent styling
across charts: log y-axis where appropriate, frontier rules colored,
non-frontier as light grey background.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from model.trend_fitting import TrendFit

RULE_COLORS = {
    "frontier_rule_a": "tab:blue",
    "frontier_rule_b": "tab:orange",
    "frontier_rule_c": "tab:green",
}

EPOCH_SOURCE_LINE = "Source: Epoch AI Notable AI Models (retrieved 2026-05-02)"


def _scatter_with_rules(
    ax,
    df: pd.DataFrame,
    y_col: str,
    *,
    title: str,
    ylabel: str,
):
    has_y = df.dropna(subset=[y_col, "release_year_fractional"])
    bg = has_y[~has_y["frontier_any"]]
    ax.scatter(
        bg["release_year_fractional"],
        bg[y_col],
        s=12,
        alpha=0.25,
        color="grey",
        label=f"non-frontier (n={len(bg)})",
    )
    for rule, color in RULE_COLORS.items():
        sub = has_y[has_y[rule]]
        ax.scatter(
            sub["release_year_fractional"],
            sub[y_col],
            s=28,
            alpha=0.7,
            color=color,
            label=f"{rule} (n={len(sub)})",
            edgecolor="white",
            linewidth=0.4,
        )
    ax.set_yscale("log")
    ax.set_xlabel("Publication year")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(True, which="both", alpha=0.25)


def _overlay_fit(ax, fit: TrendFit, x_min: float, x_max: float, *, color, label):
    xs = np.linspace(x_min, x_max, 200)
    ys = 10 ** (fit.intercept_log10 + fit.slope_log10_per_year * xs)
    ax.plot(xs, ys, color=color, linestyle="--", linewidth=1.5, label=label)


def chart_compute_over_time(
    df: pd.DataFrame, fit: TrendFit | None, out: Path
) -> None:
    fig, ax = plt.subplots(figsize=(11, 7))
    _scatter_with_rules(
        ax,
        df,
        "training_compute_flop",
        title=f"Frontier model training compute over time\n{EPOCH_SOURCE_LINE}",
        ylabel="Training compute (FLOP, log scale)",
    )
    if fit is not None:
        _overlay_fit(
            ax,
            fit,
            x_min=fit.start_year,
            x_max=df["release_year_fractional"].max(),
            color="tab:blue",
            label=(
                f"Rule A fit ({fit.start_year}+): "
                f"{fit.annual_growth_multiplier:.2f}×/yr, "
                f"doubling {fit.doubling_time_years:.2f} yr, R²={fit.r_squared:.2f}"
            ),
        )
    ax.legend(loc="lower right", fontsize=9, framealpha=0.9)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


def chart_cost_over_time(
    df: pd.DataFrame, fit: TrendFit | None, out: Path
) -> None:
    fig, ax = plt.subplots(figsize=(11, 7))
    _scatter_with_rules(
        ax,
        df,
        "estimated_training_cost_usd",
        title=f"Frontier model training cost over time (2023 USD)\n{EPOCH_SOURCE_LINE}",
        ylabel="Estimated training cost (2023 USD, log scale)",
    )
    if fit is not None:
        _overlay_fit(
            ax,
            fit,
            x_min=fit.start_year,
            x_max=df["release_year_fractional"].max(),
            color="tab:blue",
            label=(
                f"Rule A fit ({fit.start_year}+): "
                f"{fit.annual_growth_multiplier:.2f}×/yr, "
                f"doubling {fit.doubling_time_years:.2f} yr, R²={fit.r_squared:.2f}"
            ),
        )
    ax.legend(loc="lower right", fontsize=9, framealpha=0.9)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


def chart_cost_per_flop_over_time(
    df: pd.DataFrame, fit: TrendFit | None, out: Path
) -> None:
    fig, ax = plt.subplots(figsize=(11, 7))
    _scatter_with_rules(
        ax,
        df,
        "cost_per_flop",
        title=f"Cost per training FLOP over time (2023 USD / FLOP)\n{EPOCH_SOURCE_LINE}",
        ylabel="Cost per FLOP (2023 USD, log scale)",
    )
    if fit is not None:
        _overlay_fit(
            ax,
            fit,
            x_min=fit.start_year,
            x_max=df["release_year_fractional"].max(),
            color="tab:blue",
            label=(
                f"Rule A fit ({fit.start_year}+): "
                f"{fit.annual_growth_multiplier:.3f}×/yr "
                f"({(1 - fit.annual_growth_multiplier)*100:.1f}%/yr decline), "
                f"R²={fit.r_squared:.2f}"
            ),
        )
    ax.legend(loc="upper right", fontsize=9, framealpha=0.9)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


def chart_compute_by_organization(
    df: pd.DataFrame, *, top_n_orgs: int, out: Path
) -> None:
    has = df.dropna(
        subset=["training_compute_flop", "release_year_fractional", "organization"]
    )
    has = has[has["frontier_rule_a"] | has["frontier_rule_b"] | has["frontier_rule_c"]]
    counts = has.groupby("organization").size().sort_values(ascending=False)
    keep = counts.head(top_n_orgs).index.tolist()
    fig, ax = plt.subplots(figsize=(11, 7))
    palette = plt.cm.tab20(np.linspace(0, 1, len(keep)))
    for color, org in zip(palette, keep):
        sub = has[has["organization"] == org]
        ax.scatter(
            sub["release_year_fractional"],
            sub["training_compute_flop"],
            s=36,
            alpha=0.75,
            color=color,
            edgecolor="white",
            linewidth=0.4,
            label=f"{org} (n={len(sub)})",
        )
    rest = has[~has["organization"].isin(keep)]
    ax.scatter(
        rest["release_year_fractional"],
        rest["training_compute_flop"],
        s=12,
        alpha=0.25,
        color="grey",
        label=f"other orgs (n={len(rest)})",
    )
    ax.set_yscale("log")
    ax.set_xlabel("Publication year")
    ax.set_ylabel("Training compute (FLOP, log scale)")
    ax.set_title(
        f"Frontier training compute by organization (top {top_n_orgs})\n{EPOCH_SOURCE_LINE}"
    )
    ax.grid(True, which="both", alpha=0.25)
    ax.legend(loc="lower right", fontsize=8, framealpha=0.9, ncol=2)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


def chart_cost_by_organization(
    df: pd.DataFrame, *, top_n_orgs: int, out: Path
) -> None:
    has = df.dropna(
        subset=["estimated_training_cost_usd", "release_year_fractional", "organization"]
    )
    has = has[has["frontier_rule_a"] | has["frontier_rule_b"] | has["frontier_rule_c"]]
    counts = has.groupby("organization").size().sort_values(ascending=False)
    keep = counts.head(top_n_orgs).index.tolist()
    fig, ax = plt.subplots(figsize=(11, 7))
    palette = plt.cm.tab20(np.linspace(0, 1, len(keep)))
    for color, org in zip(palette, keep):
        sub = has[has["organization"] == org]
        ax.scatter(
            sub["release_year_fractional"],
            sub["estimated_training_cost_usd"],
            s=36,
            alpha=0.75,
            color=color,
            edgecolor="white",
            linewidth=0.4,
            label=f"{org} (n={len(sub)})",
        )
    rest = has[~has["organization"].isin(keep)]
    ax.scatter(
        rest["release_year_fractional"],
        rest["estimated_training_cost_usd"],
        s=12,
        alpha=0.25,
        color="grey",
        label=f"other orgs (n={len(rest)})",
    )
    ax.set_yscale("log")
    ax.set_xlabel("Publication year")
    ax.set_ylabel("Estimated training cost (2023 USD, log scale)")
    ax.set_title(
        f"Frontier training cost by organization (top {top_n_orgs})\n{EPOCH_SOURCE_LINE}"
    )
    ax.grid(True, which="both", alpha=0.25)
    ax.legend(loc="lower right", fontsize=8, framealpha=0.9, ncol=2)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


def _residuals(df: pd.DataFrame, y_col: str, fit: TrendFit) -> pd.DataFrame:
    sub = df.dropna(
        subset=[y_col, "release_year_fractional", "organization"]
    ).copy()
    sub["log10_y"] = np.log10(sub[y_col])
    sub["fitted"] = fit.intercept_log10 + fit.slope_log10_per_year * sub["release_year_fractional"]
    sub["residual"] = sub["log10_y"] - sub["fitted"]
    return sub


def chart_residuals_by_year_and_org(
    df: pd.DataFrame,
    fit: TrendFit,
    *,
    y_col: str,
    top_n_orgs: int,
    out: Path,
    title: str,
) -> None:
    res = _residuals(df, y_col, fit)
    fig, axes = plt.subplots(1, 2, figsize=(14, 6), sharey=True)

    # By year — boxplot
    ax = axes[0]
    res["release_year_int"] = res["release_year_fractional"].astype(int)
    years = sorted(res["release_year_int"].unique())
    data = [res.loc[res["release_year_int"] == y, "residual"].values for y in years]
    ax.boxplot(data, tick_labels=[str(y) for y in years], showfliers=True)
    ax.axhline(0, color="black", linestyle="--", linewidth=0.8)
    ax.set_xlabel("Publication year")
    ax.set_ylabel("Residual (log10 scale)")
    ax.set_title(f"Residuals by year — {title}")
    ax.grid(True, axis="y", alpha=0.25)
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", fontsize=8)

    # By organization — boxplot, top N
    ax = axes[1]
    counts = res.groupby("organization").size().sort_values(ascending=False)
    keep = counts.head(top_n_orgs).index.tolist()
    sub = res[res["organization"].isin(keep)].copy()
    sub["organization"] = pd.Categorical(sub["organization"], categories=keep, ordered=True)
    org_data = [sub.loc[sub["organization"] == o, "residual"].values for o in keep]
    ax.boxplot(org_data, tick_labels=keep, showfliers=True)
    ax.axhline(0, color="black", linestyle="--", linewidth=0.8)
    ax.set_xlabel("Organization")
    ax.set_title(f"Residuals by organization (top {top_n_orgs}) — {title}")
    ax.grid(True, axis="y", alpha=0.25)
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", fontsize=8)

    fig.suptitle(
        f"OLS residuals from {fit.frontier_rule} fit "
        f"(slope={fit.slope_log10_per_year:.3f}/yr, R²={fit.r_squared:.2f})",
        fontsize=11,
    )
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


def chart_hardware_timeline(df: pd.DataFrame, out: Path) -> None:
    has = df.dropna(subset=["hardware_quantity", "release_year_fractional"])
    has = has[has["frontier_any"]]
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Hardware quantity over time
    ax = axes[0]
    ax.scatter(
        has["release_year_fractional"],
        has["hardware_quantity"],
        s=24,
        alpha=0.7,
        color="tab:purple",
        edgecolor="white",
        linewidth=0.4,
    )
    ax.set_yscale("log")
    ax.set_xlabel("Publication year")
    ax.set_ylabel("Accelerator count (log scale)")
    ax.set_title(f"Frontier-model accelerator counts (n={len(has)})")
    ax.grid(True, which="both", alpha=0.25)

    # Training duration over time
    ax = axes[1]
    has2 = df.dropna(subset=["training_duration_days", "release_year_fractional"])
    has2 = has2[has2["frontier_any"]]
    ax.scatter(
        has2["release_year_fractional"],
        has2["training_duration_days"],
        s=24,
        alpha=0.7,
        color="tab:red",
        edgecolor="white",
        linewidth=0.4,
    )
    ax.set_yscale("log")
    ax.set_xlabel("Publication year")
    ax.set_ylabel("Training duration (days, log scale)")
    ax.set_title(f"Frontier-model training duration (n={len(has2)})")
    ax.grid(True, which="both", alpha=0.25)

    fig.suptitle(f"Hardware / cluster descriptive timeline\n{EPOCH_SOURCE_LINE}", fontsize=11)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)
