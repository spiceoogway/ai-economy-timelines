"""Allocation pipeline.

Run with: `uv run allocation`

Consumes the supply-pipeline outputs (`uv run supply` must have run
first) and produces the cross-product of supply × allocation scenarios
with bucket allocations, training-pool decomposition, and the headline
`largest_frontier_run_flop` quantity.

Outputs:
  data/processed/allocation_compute_by_bucket.csv
  outputs/tables/allocation_compute_by_bucket.csv
  outputs/tables/allocation_largest_frontier_run.csv
  outputs/tables/allocation_vs_historical_trend.csv
  outputs/tables/allocation_scenario_summary.csv
  outputs/tables/allocation_share_assumptions_by_year.csv
  outputs/charts/allocation_*.png  (next commit)
"""
from __future__ import annotations

import pandas as pd

from model.allocation_engine import (
    BUCKET_COMPUTE_COLUMNS,
    compare_to_historical_frontier_trend,
    interpolate_allocation_assumptions,
    load_all_allocation_scenarios,
    load_allocation_assumptions,
    load_supply_capacity_outputs,
    run_allocation_model,
)
from model.runtime import (
    HISTORICAL_TREND_TABLE,
    PROCESSED_DIR,
    TABLES_DIR,
)


def get_historical_rule_a_2018_fit() -> tuple[float, float, float]:
    """Mirror of pipelines/supply.py: read Rule A 2018+ historical fit and
    rebase the intercept so 2024 corresponds to 1e25 FLOP per single
    frontier run."""
    if not HISTORICAL_TREND_TABLE.exists():
        raise FileNotFoundError(
            f"{HISTORICAL_TREND_TABLE} not found. Run `uv run historical` "
            "first to produce the historical-baseline trend table."
        )
    t = pd.read_csv(HISTORICAL_TREND_TABLE)
    row = t[
        (t["trend_name"] == "training_compute")
        & (t["frontier_rule"] == "frontier_rule_a_2018+")
    ]
    slope = float(row["slope_log10_per_year"].iloc[0])
    mult = float(row["annual_growth_multiplier"].iloc[0])
    intercept = 25.0 - slope * 2024.0
    return slope, intercept, mult


def _build_scenario_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Per-combined-scenario milestone summary (2024 / 2030 / 2040)
    + 16-year CAGR on the largest-run trajectory."""
    rows = []
    for combined, sub in df.groupby("combined_scenario"):
        sub = sub.set_index("year")
        v_24 = sub.loc[2024, "largest_frontier_run_flop"]
        v_40 = sub.loc[2040, "largest_frontier_run_flop"]
        cagr = (v_40 / v_24) ** (1 / 16) - 1
        rows.append({
            "combined_scenario": combined,
            "supply_scenario": sub["supply_scenario"].iloc[0],
            "allocation_scenario": sub["allocation_scenario"].iloc[0],
            "usable_compute_2024": float(sub.loc[2024, "usable_compute_flop_year"]),
            "usable_compute_2030": float(sub.loc[2030, "usable_compute_flop_year"]),
            "usable_compute_2040": float(sub.loc[2040, "usable_compute_flop_year"]),
            "largest_run_2024": float(v_24),
            "largest_run_2030": float(sub.loc[2030, "largest_frontier_run_flop"]),
            "largest_run_2040": float(v_40),
            "largest_run_cagr_2024_2040": float(cagr),
            "frontier_run_share_2024": float(sub.loc[2024, "frontier_run_share_of_total_compute"]),
            "frontier_run_share_2030": float(sub.loc[2030, "frontier_run_share_of_total_compute"]),
            "frontier_run_share_2040": float(sub.loc[2040, "frontier_run_share_of_total_compute"]),
        })
    return pd.DataFrame(rows).sort_values("combined_scenario").reset_index(drop=True)


def main() -> None:
    print("[1/6] Loading supply outputs + allocation assumptions...")
    supply_df = load_supply_capacity_outputs()
    assumptions = load_allocation_assumptions()
    alloc_scenarios = load_all_allocation_scenarios()
    print(f"      supply: {supply_df['scenario'].nunique()} scenarios x "
          f"{supply_df['year'].nunique()} years")
    print(f"      allocation: {len(alloc_scenarios)} scenarios "
          f"({', '.join(s.name for s in alloc_scenarios)})")

    print("[2/6] Running allocation model (interpolate + cross-product + validate)...")
    df = run_allocation_model(supply_df, assumptions)
    print(f"      combined rows: {len(df):,} "
          f"({df['combined_scenario'].nunique()} combined scenarios "
          f"× {df['year'].nunique()} years)")

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)

    print("[3/6] Writing allocation_compute_by_bucket...")
    keep_cols = [
        "year", "supply_scenario", "allocation_scenario", "combined_scenario",
        "usable_compute_flop_year",
        "inference_share", "training_share", "ai_rnd_experiment_share",
        "post_training_share", "safety_eval_share", "reserved_idle_fragmented_share",
        *BUCKET_COMPUTE_COLUMNS,
        "frontier_lab_training_share", "frontier_lab_training_compute_flop_year",
        "largest_run_concentration", "cluster_contiguity_factor",
        "largest_frontier_run_flop", "frontier_run_share_of_total_compute",
        "binding_constraint",
    ]
    out = df[keep_cols].copy()
    out.to_csv(PROCESSED_DIR / "allocation_compute_by_bucket.csv", index=False)
    out.to_csv(TABLES_DIR / "allocation_compute_by_bucket.csv", index=False)

    print("[4/6] Writing largest_frontier_run + scenario_summary tables...")
    largest_cols = [
        "year", "supply_scenario", "allocation_scenario", "combined_scenario",
        "largest_frontier_run_flop", "frontier_run_share_of_total_compute",
        "training_compute_flop_year", "frontier_lab_training_compute_flop_year",
    ]
    df[largest_cols].to_csv(
        TABLES_DIR / "allocation_largest_frontier_run.csv", index=False
    )

    summary = _build_scenario_summary(df)
    summary.to_csv(TABLES_DIR / "allocation_scenario_summary.csv", index=False)

    print("[5/6] Comparing against historical baseline + writing trend table...")
    historical_fit = get_historical_rule_a_2018_fit()
    vs_hist = compare_to_historical_frontier_trend(
        df[["year", "supply_scenario", "allocation_scenario", "combined_scenario",
            "largest_frontier_run_flop"]],
        historical_fit,
    )
    vs_hist = vs_hist.rename(columns={"combined_scenario": "scenario"})
    vs_hist[[
        "year", "scenario", "supply_scenario", "allocation_scenario",
        "historical_trend_frontier_run_flop", "projected_largest_frontier_run_flop",
        "gap_ratio", "log10_gap",
    ]].to_csv(TABLES_DIR / "allocation_vs_historical_trend.csv", index=False)

    print("[6/6] Writing share_assumptions_by_year + console summary...")
    years = sorted(df["year"].unique())
    asm_long = interpolate_allocation_assumptions(assumptions, years)
    asm_long.to_csv(
        TABLES_DIR / "allocation_share_assumptions_by_year.csv", index=False
    )

    print("\n=== Allocation summary ===")
    base_combined = "base_input_case × allocation_base"
    sub = df[df["combined_scenario"] == base_combined].set_index("year")
    print(f"\n  Headline (base supply × base allocation):")
    for y in (2024, 2030, 2040):
        lr = sub.loc[y, "largest_frontier_run_flop"]
        sh = sub.loc[y, "frontier_run_share_of_total_compute"]
        print(f"    {y}: largest_run = {lr:.2e} FLOP  "
              f"(share of total = {sh*100:.2f}%)")

    cagr = (sub.loc[2040, "largest_frontier_run_flop"]
            / sub.loc[2024, "largest_frontier_run_flop"]) ** (1 / 16) - 1
    print(f"    CAGR 2024→2040: {cagr*100:.1f}%/yr")

    print(f"\n  Historical Rule A 2018+ multiplier: {historical_fit[2]:.2f}x/yr")
    print(f"\n  Combined scenarios: {df['combined_scenario'].nunique()} "
          f"({summary['supply_scenario'].nunique()} supply × "
          f"{summary['allocation_scenario'].nunique()} allocation)")


if __name__ == "__main__":
    main()
