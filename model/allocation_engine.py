"""Allocation-layer engine.

Pipeline (per docs/scope.md §3):

    usable_compute_flop_year_t  (from supply_engine)
        ↓ × bucket_share_t
    {inference, training, ai_rnd, post_training, safety_eval, reserved}_compute_flop_year_t
        ↓ × frontier_lab_training_share_t
    frontier_lab_training_compute_t
        ↓ × largest_run_concentration_t × cluster_contiguity_factor_t
    largest_frontier_run_flop_t                 ← headline output

The 6 bucket shares sum to 1 at every year. The 3 training-decomposition
parameters (frontier_lab_training_share, largest_run_concentration,
cluster_contiguity_factor) are independent of the bucket shares.

Allocation scenarios are independent of supply scenarios; the allocation
pipeline computes the 4 × 4 = 16 cross-product of combined scenarios.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
import yaml

from model.runtime import (
    ASSUMPTIONS_DIR,
    PROCESSED_DIR,
    SCENARIOS_DIR,
    TABLES_DIR,
)

# --- constants -----------------------------------------------------------

ALLOCATION_ASSUMPTIONS_YAML = ASSUMPTIONS_DIR / "allocation_input_assumptions.yaml"
SUPPLY_OUTPUTS_TABLE = TABLES_DIR / "supply_fundamental_inputs_by_year.csv"

BUCKET_SHARES = (
    "inference_share",
    "training_share",
    "ai_rnd_experiment_share",
    "post_training_share",
    "safety_eval_share",
    "reserved_idle_fragmented_share",
)

BUCKET_COMPUTE_COLUMNS = tuple(
    s.replace("_share", "_compute_flop_year") for s in BUCKET_SHARES
)

TRAINING_DECOMPOSITION_PARAMS = (
    "frontier_lab_training_share",
    "largest_run_concentration",
    "cluster_contiguity_factor",
)

ALL_ALLOCATION_PARAMS = tuple(BUCKET_SHARES) + TRAINING_DECOMPOSITION_PARAMS

REQUIRED_SUPPLY_COLUMNS = (
    "year",
    "scenario",
    "usable_compute_flop_year",
    "binding_constraint",
)

SHARE_TOLERANCE = 1e-6


@dataclass(frozen=True)
class AllocationScenario:
    """Allocation-side scenario config (parallel to supply's ScenarioConfig)."""
    name: str
    display_name: str
    description: str
    assumption_scenario: str
    start_year: int
    end_year: int

    @classmethod
    def from_yaml(cls, path: Path) -> "AllocationScenario":
        d = yaml.safe_load(path.read_text())
        return cls(
            name=d["name"],
            display_name=d.get("display_name", d["name"]),
            description=d.get("description", "").strip(),
            assumption_scenario=d["assumption_scenario"],
            start_year=int(d["start_year"]),
            end_year=int(d["end_year"]),
        )


# --- loaders ------------------------------------------------------------


def load_allocation_assumptions(
    path: Path = ALLOCATION_ASSUMPTIONS_YAML,
) -> dict:
    """Load the nested allocation assumptions YAML.

    Schema (validated by load):
        scenarios:
            <scenario_name>:
                description: ...
                milestones:
                    <year>:
                        <param_name>: <value>
                        ...
    """
    raw = yaml.safe_load(path.read_text())
    if not isinstance(raw, dict) or "scenarios" not in raw:
        raise ValueError(f"{path}: top-level must contain a 'scenarios' key")
    scenarios = raw["scenarios"]
    if not isinstance(scenarios, dict) or not scenarios:
        raise ValueError(f"{path}: 'scenarios' must be a non-empty mapping")
    for name, block in scenarios.items():
        if "milestones" not in block or not block["milestones"]:
            raise ValueError(f"{path}: scenario {name!r} has no milestones")
        for year, params in block["milestones"].items():
            missing = [p for p in ALL_ALLOCATION_PARAMS if p not in params]
            if missing:
                raise ValueError(
                    f"{path}: scenario {name!r} milestone {year} missing "
                    f"parameters: {missing}"
                )
    return raw


def load_all_allocation_scenarios() -> list[AllocationScenario]:
    """Load every scenarios/allocation_*.yaml registration file."""
    paths = sorted(SCENARIOS_DIR.glob("allocation_*.yaml"))
    return [AllocationScenario.from_yaml(p) for p in paths]


def load_supply_capacity_outputs(
    path: Path = SUPPLY_OUTPUTS_TABLE,
) -> pd.DataFrame:
    """Read the supply pipeline's annual output table.

    Raises a clear error if the supply pipeline hasn't been run yet —
    `uv run supply` must have produced this file before allocation
    can run.
    """
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Run `uv run supply` first to produce "
            "the supply-capacity outputs that allocation consumes."
        )
    df = pd.read_csv(path)
    assert_required_supply_columns(df)
    return df


# --- interpolation ------------------------------------------------------


def _interp_param(milestones: dict, years: Iterable[int], param: str) -> np.ndarray:
    """Linear interpolation of one parameter across milestone years."""
    sorted_years = sorted(int(y) for y in milestones.keys())
    xs = np.array(sorted_years, dtype=float)
    ys = np.array([milestones[y][param] for y in sorted_years], dtype=float)
    target = np.array(list(years), dtype=float)
    if len(xs) == 1:
        return np.repeat(ys[0], len(target))
    return np.interp(target, xs, ys, left=ys[0], right=ys[-1])


def interpolate_allocation_assumptions(
    assumptions: dict, years: Iterable[int]
) -> pd.DataFrame:
    """Project the milestone assumptions to a yearly table.

    Returns a long-format DataFrame indexed by (allocation_scenario,
    year) with one column per allocation parameter.
    """
    years_list = list(years)
    rows = []
    for name, block in assumptions["scenarios"].items():
        ms = block["milestones"]
        scen_data: dict = {"allocation_scenario": [name] * len(years_list),
                           "year": years_list}
        for param in ALL_ALLOCATION_PARAMS:
            scen_data[param] = _interp_param(ms, years_list, param)
        rows.append(pd.DataFrame(scen_data))
    return pd.concat(rows, ignore_index=True)


# --- validation ---------------------------------------------------------


def assert_required_supply_columns(df: pd.DataFrame) -> None:
    missing = [c for c in REQUIRED_SUPPLY_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(
            f"Supply outputs missing required columns: {missing}. "
            f"Got columns: {list(df.columns)}"
        )


def assert_bucket_shares_sum_to_one(
    df: pd.DataFrame, tolerance: float = SHARE_TOLERANCE
) -> None:
    sums = df[list(BUCKET_SHARES)].sum(axis=1)
    deviation = (sums - 1.0).abs()
    if (deviation > tolerance).any():
        bad = df[deviation > tolerance][["allocation_scenario", "year"]].head(5)
        raise ValueError(
            f"Bucket shares sum to ≠ 1.0 (tolerance {tolerance}). "
            f"First offending rows:\n{bad.to_string(index=False)}"
        )


def assert_values_between_zero_and_one(
    df: pd.DataFrame, columns: Iterable[str]
) -> None:
    for col in columns:
        if col not in df.columns:
            continue
        out_of_range = ~df[col].between(0.0, 1.0)
        if out_of_range.any():
            bad = df[out_of_range].head(3)
            raise ValueError(
                f"Column {col!r} has values outside [0, 1]:\n{bad.to_string(index=False)}"
            )


def assert_no_negative_compute(df: pd.DataFrame) -> None:
    compute_cols = [c for c in df.columns if c.endswith("_compute_flop_year") or c == "largest_frontier_run_flop"]
    for col in compute_cols:
        if (df[col] < 0).any():
            raise ValueError(f"Negative values found in {col!r}")


def validate_allocation_shares(df: pd.DataFrame) -> None:
    """Run all allocation invariants on a DataFrame."""
    assert_bucket_shares_sum_to_one(df)
    assert_values_between_zero_and_one(df, ALL_ALLOCATION_PARAMS)


# --- core math ----------------------------------------------------------


def build_combined_scenarios(
    supply_df: pd.DataFrame, allocation_df: pd.DataFrame
) -> pd.DataFrame:
    """Cartesian product of supply scenarios × allocation scenarios per year.

    Returns one row per (supply_scenario, allocation_scenario, year).
    """
    supply = supply_df.rename(columns={"scenario": "supply_scenario"})
    merged = supply.merge(allocation_df, on="year", how="inner")
    merged["combined_scenario"] = (
        merged["supply_scenario"] + " × " + merged["allocation_scenario"]
    )
    return merged


def allocate_compute_by_bucket(df: pd.DataFrame) -> pd.DataFrame:
    """Multiply usable_compute by each bucket share."""
    out = df.copy()
    for share, target in zip(BUCKET_SHARES, BUCKET_COMPUTE_COLUMNS):
        out[target] = out["usable_compute_flop_year"] * out[share]
    return out


def estimate_frontier_lab_training_compute(df: pd.DataFrame) -> pd.DataFrame:
    """Apply the frontier-lab share to total training compute."""
    out = df.copy()
    out["frontier_lab_training_compute_flop_year"] = (
        out["training_compute_flop_year"] * out["frontier_lab_training_share"]
    )
    return out


def estimate_largest_frontier_run(df: pd.DataFrame) -> pd.DataFrame:
    """Headline output: largest_frontier_run_flop and its share of total compute."""
    out = df.copy()
    out["largest_frontier_run_flop"] = (
        out["frontier_lab_training_compute_flop_year"]
        * out["largest_run_concentration"]
        * out["cluster_contiguity_factor"]
    )
    out["frontier_run_share_of_total_compute"] = (
        out["largest_frontier_run_flop"] / out["usable_compute_flop_year"]
    )
    return out


def compare_to_historical_frontier_trend(
    allocation_df: pd.DataFrame,
    historical_trend: tuple[float, float, float],
) -> pd.DataFrame:
    """Compute historical-extrapolated frontier-run FLOP and gap_ratio.

    `historical_trend` is (slope_log10_per_year, intercept_log10,
    annual_multiplier) — the same tuple used for the supply-vs-historical
    chart. The intercept is rebased so 2024 ≈ 1e25 FLOP per single
    frontier run; we extrapolate that line forward and compare against
    the allocation-derived `largest_frontier_run_flop`.
    """
    slope, intercept, _mult = historical_trend
    out = allocation_df.copy()
    out["historical_trend_frontier_run_flop"] = 10 ** (
        intercept + slope * out["year"].astype(float)
    )
    out["projected_largest_frontier_run_flop"] = out["largest_frontier_run_flop"]
    out["gap_ratio"] = (
        out["projected_largest_frontier_run_flop"]
        / out["historical_trend_frontier_run_flop"]
    )
    out["log10_gap"] = np.log10(out["gap_ratio"].replace({0: np.nan}))
    return out


# --- top-level orchestrator ---------------------------------------------


def run_allocation_model(
    supply_df: pd.DataFrame | None = None,
    assumptions: dict | None = None,
    years: Iterable[int] | None = None,
) -> pd.DataFrame:
    """Full allocation projection: combined-scenario annual table with all
    derived quantities. Validates invariants before returning.

    If `years` is omitted, derives from supply_df's year column.
    """
    if supply_df is None:
        supply_df = load_supply_capacity_outputs()
    if assumptions is None:
        assumptions = load_allocation_assumptions()
    if years is None:
        years = sorted(int(y) for y in supply_df["year"].unique())

    allocation_df = interpolate_allocation_assumptions(assumptions, years)
    validate_allocation_shares(allocation_df)

    combined = build_combined_scenarios(supply_df, allocation_df)
    combined = allocate_compute_by_bucket(combined)
    combined = estimate_frontier_lab_training_compute(combined)
    combined = estimate_largest_frontier_run(combined)

    # Final post-condition checks
    assert_no_negative_compute(combined)
    assert (combined["largest_frontier_run_flop"]
            <= combined["training_compute_flop_year"] + 1e-3).all(), (
        "largest_frontier_run_flop > training_compute_flop_year — invariant violated"
    )

    return combined
