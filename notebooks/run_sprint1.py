"""Sprint-1 driver: load → clean → flag → fit → plot → save.

Run with: `uv run python notebooks/run_sprint1.py`

Produces:
  data/processed/frontier_models_historical.csv
  data/processed/frontier_models_historical.parquet
  outputs/charts/frontier_training_compute_over_time.png
  outputs/tables/initial_compute_growth_estimates.csv

Sprint-1 scope: training compute only. Cost / cost-per-FLOP trends and
residual diagnostics are deferred to subsequent sprints.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from model.data_cleaning import load_raw, select_processed
from model.frontier_filters import add_frontier_flags
from model.trend_fitting import fit_log_linear, fits_to_frame

PROCESSED_DIR = REPO_ROOT / "data" / "processed"
CHARTS_DIR = REPO_ROOT / "outputs" / "charts"
TABLES_DIR = REPO_ROOT / "outputs" / "tables"

# Phase 1 narrow window — better data, more relevant for current frontier.
NARROW_START_YEAR = 2018


def main() -> None:
    print("[1/5] Loading raw Epoch CSV...")
    df = load_raw()
    print(f"      raw rows: {len(df):,}")

    print("[2/5] Adding frontier flags...")
    df = add_frontier_flags(df)
    flagged = df[["frontier_rule_a", "frontier_rule_b", "frontier_rule_c", "epoch_frontier_flag"]].sum()
    print(f"      flag counts:\n{flagged.to_string()}")

    print("[3/5] Selecting processed schema and writing processed dataset...")
    processed_cols = list(select_processed(df).columns) + [
        "frontier_rule_a",
        "frontier_rule_b",
        "frontier_rule_c",
        "frontier_any",
    ]
    out = df[processed_cols].copy()
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out.to_csv(PROCESSED_DIR / "frontier_models_historical.csv", index=False)
    out.to_parquet(PROCESSED_DIR / "frontier_models_historical.parquet", index=False)
    print(f"      wrote {len(out):,} rows × {len(out.columns)} cols")

    # ----------- trend fits -----------
    print("[4/5] Fitting compute trends (log10(FLOP) ~ year)...")
    has_compute = out.dropna(subset=["training_compute_flop", "release_year_fractional"])
    narrow = has_compute[has_compute["release_year"] >= NARROW_START_YEAR]

    fits = []
    fits.append(
        fit_log_linear(
            has_compute,
            "training_compute_flop",
            trend_name="training_compute",
            frontier_rule="all_models_full",
            notes="all models with known compute, full historical window",
        )
    )
    fits.append(
        fit_log_linear(
            narrow,
            "training_compute_flop",
            trend_name="training_compute",
            frontier_rule="all_models_2018+",
            notes="all models with known compute, 2018+",
        )
    )
    for rule in ["frontier_rule_a", "frontier_rule_b", "frontier_rule_c"]:
        fits.append(
            fit_log_linear(
                narrow[narrow[rule]],
                "training_compute_flop",
                trend_name="training_compute",
                frontier_rule=f"{rule}_2018+",
                notes=f"{rule} == True, 2018+",
            )
        )
        fits.append(
            fit_log_linear(
                has_compute[has_compute[rule]],
                "training_compute_flop",
                trend_name="training_compute",
                frontier_rule=f"{rule}_full",
                notes=f"{rule} == True, full historical window",
            )
        )
    fits.append(
        fit_log_linear(
            has_compute[has_compute["epoch_frontier_flag"]],
            "training_compute_flop",
            trend_name="training_compute",
            frontier_rule="epoch_frontier_flag_full",
            notes="Epoch's own 'Frontier model' flag",
        )
    )

    fits_df = fits_to_frame(fits)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    fits_df.to_csv(TABLES_DIR / "initial_compute_growth_estimates.csv", index=False)
    print(fits_df.to_string(index=False))

    # ----------- chart -----------
    print("[5/5] Generating frontier_training_compute_over_time.png...")
    fig, ax = plt.subplots(figsize=(11, 7))
    bg = has_compute[~has_compute["frontier_any"]]
    ax.scatter(
        bg["release_year_fractional"],
        bg["training_compute_flop"],
        s=12,
        alpha=0.25,
        color="grey",
        label=f"non-frontier (n={len(bg)})",
    )
    color_map = {
        "frontier_rule_a": "tab:blue",
        "frontier_rule_b": "tab:orange",
        "frontier_rule_c": "tab:green",
    }
    for rule, color in color_map.items():
        sub = has_compute[has_compute[rule]]
        ax.scatter(
            sub["release_year_fractional"],
            sub["training_compute_flop"],
            s=28,
            alpha=0.7,
            color=color,
            label=f"{rule} (n={len(sub)})",
            edgecolor="white",
            linewidth=0.4,
        )

    # Overlay the rule-A 2018+ regression line.
    a_fit = next(
        f for f in fits if f and f.frontier_rule == "frontier_rule_a_2018+"
    )
    xs = np.linspace(NARROW_START_YEAR, has_compute["release_year_fractional"].max(), 200)
    ys = 10 ** (a_fit.intercept_log10 + a_fit.slope_log10_per_year * xs)
    ax.plot(
        xs,
        ys,
        color="tab:blue",
        linestyle="--",
        linewidth=1.5,
        label=(
            f"Rule A fit (2018+): {a_fit.annual_growth_multiplier:.2f}×/yr, "
            f"doubling {a_fit.doubling_time_years:.2f} yr, R²={a_fit.r_squared:.2f}"
        ),
    )

    ax.set_yscale("log")
    ax.set_xlabel("Publication year")
    ax.set_ylabel("Training compute (FLOP, log scale)")
    ax.set_title(
        "Frontier model training compute over time\n"
        "Source: Epoch AI Notable AI Models (retrieved 2026-05-02)"
    )
    ax.grid(True, which="both", alpha=0.25)
    ax.legend(loc="lower right", fontsize=9, framealpha=0.9)
    fig.tight_layout()

    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(CHARTS_DIR / "frontier_training_compute_over_time.png", dpi=150)
    plt.close(fig)
    print(f"      wrote {CHARTS_DIR / 'frontier_training_compute_over_time.png'}")
    print("\nDone.")


if __name__ == "__main__":
    main()
