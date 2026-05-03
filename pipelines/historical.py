"""Historical-baseline pipeline: produce all empirical-trend deliverables.

Run with: `uv run historical`

Produces:
  data/processed/historical_models.{csv,parquet}
  outputs/charts/historical_compute_over_time.png
  outputs/charts/historical_cost_over_time.png
  outputs/charts/historical_cost_per_flop_over_time.png
  outputs/charts/historical_compute_by_organization.png
  outputs/charts/historical_cost_by_organization.png
  outputs/charts/historical_residuals_compute.png
  outputs/charts/historical_residuals_cost.png
  outputs/charts/historical_hardware_timeline.png
  outputs/tables/historical_trend_estimates.csv
  outputs/tables/historical_hardware_summary.csv
"""
from __future__ import annotations

import pandas as pd

from model import historical_charts as charts
from model.data_cleaning import load_raw, select_processed
from model.frontier_filters import add_frontier_flags
from model.runtime import CHARTS_DIR, PROCESSED_DIR, TABLES_DIR
from model.trend_fitting import fit_log_linear, fits_to_frame

NARROW_START_YEAR = 2018
TOP_N_ORGS = 10

RULES = ["frontier_rule_a", "frontier_rule_b", "frontier_rule_c"]


def fit_all_for_metric(
    full: pd.DataFrame,
    narrow: pd.DataFrame,
    *,
    y_col: str,
    trend_name: str,
    extra_notes: str = "",
) -> list:
    fits = []
    fits.append(
        fit_log_linear(
            full.dropna(subset=[y_col]),
            y_col,
            trend_name=trend_name,
            frontier_rule="all_models_full",
            notes=f"all models with known {trend_name}, full historical window. {extra_notes}".strip(),
        )
    )
    fits.append(
        fit_log_linear(
            narrow.dropna(subset=[y_col]),
            y_col,
            trend_name=trend_name,
            frontier_rule="all_models_2018+",
            notes=f"all models with known {trend_name}, 2018+. {extra_notes}".strip(),
        )
    )
    for rule in RULES:
        fits.append(
            fit_log_linear(
                narrow[narrow[rule]].dropna(subset=[y_col]),
                y_col,
                trend_name=trend_name,
                frontier_rule=f"{rule}_2018+",
                notes=f"{rule} == True, 2018+. {extra_notes}".strip(),
            )
        )
        fits.append(
            fit_log_linear(
                full[full[rule]].dropna(subset=[y_col]),
                y_col,
                trend_name=trend_name,
                frontier_rule=f"{rule}_full",
                notes=f"{rule} == True, full historical window. {extra_notes}".strip(),
            )
        )
    fits.append(
        fit_log_linear(
            full[full["epoch_frontier_flag"]].dropna(subset=[y_col]),
            y_col,
            trend_name=trend_name,
            frontier_rule="epoch_frontier_flag_full",
            notes=f"Epoch's own 'Frontier model' flag. {extra_notes}".strip(),
        )
    )
    return fits


def main() -> None:
    print("[1/8] Loading raw Epoch CSV...")
    df = load_raw()
    print(f"      raw rows: {len(df):,}")

    print("[2/8] Adding frontier flags...")
    df = add_frontier_flags(df)
    flag_counts = df[RULES + ["epoch_frontier_flag"]].sum()
    print(f"      flag counts:\n{flag_counts.to_string()}")

    print("[3/8] Writing processed dataset...")
    processed_cols = list(select_processed(df).columns) + RULES + ["frontier_any"]
    out = df[processed_cols].copy()
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out.to_csv(PROCESSED_DIR / "historical_models.csv", index=False)
    out.to_parquet(PROCESSED_DIR / "historical_models.parquet", index=False)
    print(f"      wrote {len(out):,} rows × {len(out.columns)} cols")

    full = out
    narrow = out[out["release_year"] >= NARROW_START_YEAR]

    print("[4/8] Fitting trends (compute, cost, cost-per-FLOP)...")
    all_fits = []
    all_fits += fit_all_for_metric(
        full, narrow, y_col="training_compute_flop", trend_name="training_compute"
    )
    all_fits += fit_all_for_metric(
        full,
        narrow,
        y_col="estimated_training_cost_usd",
        trend_name="training_cost_2023usd",
        extra_notes="cost variant: headline 2023 USD",
    )
    all_fits += fit_all_for_metric(
        full,
        narrow,
        y_col="training_cost_cloud_usd",
        trend_name="training_cost_cloud",
        extra_notes="cost variant: cloud-rental",
    )
    all_fits += fit_all_for_metric(
        full,
        narrow,
        y_col="training_cost_upfront_usd",
        trend_name="training_cost_upfront",
        extra_notes="cost variant: upfront hardware",
    )
    all_fits += fit_all_for_metric(
        full, narrow, y_col="cost_per_flop", trend_name="cost_per_flop_2023usd"
    )

    fits_df = fits_to_frame(all_fits)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    fits_df.to_csv(TABLES_DIR / "historical_trend_estimates.csv", index=False)
    print(f"      wrote {len(fits_df)} trend rows to historical_trend_estimates.csv")

    # Pull the headline fits we'll overlay on charts.
    def _by(rule: str, trend: str):
        m = (fits_df["frontier_rule"] == rule) & (fits_df["trend_name"] == trend)
        if not m.any():
            return None
        return next(
            f for f in all_fits
            if f is not None and f.frontier_rule == rule and f.trend_name == trend
        )

    compute_fit = _by("frontier_rule_a_2018+", "training_compute")
    cost_fit = _by("frontier_rule_a_2018+", "training_cost_2023usd")
    cpf_fit = _by("frontier_rule_a_2018+", "cost_per_flop_2023usd")

    print("[5/8] Generating compute / cost / cost-per-FLOP charts...")
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    charts.chart_compute_over_time(
        out, compute_fit, CHARTS_DIR / "historical_compute_over_time.png"
    )
    charts.chart_cost_over_time(
        out, cost_fit, CHARTS_DIR / "historical_cost_over_time.png"
    )
    charts.chart_cost_per_flop_over_time(
        out, cpf_fit, CHARTS_DIR / "historical_cost_per_flop_over_time.png"
    )

    print("[6/8] Generating by-organization charts...")
    charts.chart_compute_by_organization(
        out, top_n_orgs=TOP_N_ORGS, out=CHARTS_DIR / "historical_compute_by_organization.png"
    )
    charts.chart_cost_by_organization(
        out, top_n_orgs=TOP_N_ORGS, out=CHARTS_DIR / "historical_cost_by_organization.png"
    )

    print("[7/8] Generating residual diagnostic charts...")
    if compute_fit is not None:
        charts.chart_residuals_by_year_and_org(
            narrow[narrow["frontier_rule_a"]],
            compute_fit,
            y_col="training_compute_flop",
            top_n_orgs=TOP_N_ORGS,
            out=CHARTS_DIR / "historical_residuals_compute.png",
            title="training compute, Rule A 2018+",
        )
    if cost_fit is not None:
        charts.chart_residuals_by_year_and_org(
            narrow[narrow["frontier_rule_a"]],
            cost_fit,
            y_col="estimated_training_cost_usd",
            top_n_orgs=TOP_N_ORGS,
            out=CHARTS_DIR / "historical_residuals_cost.png",
            title="training cost, Rule A 2018+",
        )

    print("[8/8] Generating hardware timeline + summary table...")
    charts.chart_hardware_timeline(out, CHARTS_DIR / "historical_hardware_timeline.png")
    hw = (
        out[out["frontier_any"]]
        .dropna(subset=["hardware_type"])
        .groupby([out["release_year"].astype("Int64"), "hardware_type"])
        .size()
        .reset_index(name="n")
        .sort_values(["release_year", "n"], ascending=[True, False])
    )
    hw.to_csv(TABLES_DIR / "historical_hardware_summary.csv", index=False)

    print("\nDone. Historical-baseline artifacts written.")
    print("\n--- Headline (Rule A 2018+) ---")
    if compute_fit:
        print(f"  compute    : {compute_fit.annual_growth_multiplier:.2f}×/yr  doubling {compute_fit.doubling_time_years*12:.1f} mo  R²={compute_fit.r_squared:.2f}  n={compute_fit.n_models}")
    if cost_fit:
        print(f"  cost (USD) : {cost_fit.annual_growth_multiplier:.2f}×/yr  doubling {cost_fit.doubling_time_years*12:.1f} mo  R²={cost_fit.r_squared:.2f}  n={cost_fit.n_models}")
    if cpf_fit:
        decline = (1 - cpf_fit.annual_growth_multiplier) * 100
        print(f"  cost/FLOP  : {cpf_fit.annual_growth_multiplier:.3f}×/yr  ({decline:.1f}%/yr decline)  R²={cpf_fit.r_squared:.2f}  n={cpf_fit.n_models}")


if __name__ == "__main__":
    main()
