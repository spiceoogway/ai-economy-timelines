"""Tests for the allocation engine.

Covers the 8 invariants required by the allocation scope §13:

- shares sum to 1 (within tolerance)
- shares ∈ [0, 1]
- training decomposition is valid (subshares ∈ [0, 1])
- no negative compute outputs
- largest_run_flop ≤ training_compute_flop_year
- combined-scenario count equals supply-scenarios × allocation-scenarios
- required output columns are present
- the full pipeline runs without raising
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest
import yaml

from model.allocation_engine import (
    ALL_ALLOCATION_PARAMS,
    BUCKET_COMPUTE_COLUMNS,
    BUCKET_SHARES,
    allocate_compute_by_bucket,
    assert_bucket_shares_sum_to_one,
    assert_no_negative_compute,
    build_combined_scenarios,
    estimate_frontier_lab_training_compute,
    estimate_largest_frontier_run,
    interpolate_allocation_assumptions,
    load_allocation_assumptions,
    run_allocation_model,
    validate_allocation_shares,
)


@pytest.fixture()
def synthetic_supply_df() -> pd.DataFrame:
    """Two-supply-scenario × 5-year synthetic supply output."""
    rows = []
    for scen, base in (("supply_a", 1e28), ("supply_b", 5e28)):
        for i, y in enumerate(range(2024, 2029)):
            rows.append({
                "year": y,
                "scenario": scen,
                "usable_compute_flop_year": base * (1.5 ** i),
                "binding_constraint": "capex",
            })
    return pd.DataFrame(rows)


@pytest.fixture()
def synthetic_assumptions() -> dict:
    """Two allocation scenarios; minimum required parameters."""
    common = {
        "inference_share": 0.50,
        "training_share": 0.30,
        "ai_rnd_experiment_share": 0.10,
        "post_training_share": 0.05,
        "safety_eval_share": 0.03,
        "reserved_idle_fragmented_share": 0.02,
        "frontier_lab_training_share": 0.60,
        "largest_run_concentration": 0.20,
        "cluster_contiguity_factor": 0.90,
    }
    return {
        "scenarios": {
            "alloc_x": {"description": "X", "milestones": {2024: common, 2028: common}},
            "alloc_y": {"description": "Y", "milestones": {2024: common, 2028: common}},
        }
    }


# --- 1: shares sum to 1 -------------------------------------------------

def test_allocation_shares_sum_to_one() -> None:
    """The committed allocation YAML must have shares summing to 1.0
    at every milestone."""
    asm = load_allocation_assumptions()
    for name, block in asm["scenarios"].items():
        for year, params in block["milestones"].items():
            total = sum(params[s] for s in BUCKET_SHARES)
            assert math.isclose(total, 1.0, abs_tol=1e-6), (
                f"{name}/{year}: bucket shares sum to {total:.6f}, not 1.0"
            )


# --- 2: shares between 0 and 1 ------------------------------------------

def test_allocation_shares_between_zero_and_one() -> None:
    asm = load_allocation_assumptions()
    for name, block in asm["scenarios"].items():
        for year, params in block["milestones"].items():
            for p in ALL_ALLOCATION_PARAMS:
                v = params[p]
                assert 0.0 <= v <= 1.0, (
                    f"{name}/{year}/{p}: value {v} outside [0, 1]"
                )


# --- 3: training decomposition is valid ---------------------------------

def test_training_decomposition_valid() -> None:
    """Each of the three training-decomposition multipliers should be
    in [0, 1] across all milestones."""
    asm = load_allocation_assumptions()
    for block in asm["scenarios"].values():
        for params in block["milestones"].values():
            for p in (
                "frontier_lab_training_share",
                "largest_run_concentration",
                "cluster_contiguity_factor",
            ):
                assert 0.0 <= params[p] <= 1.0


# --- 4: no negative compute outputs -------------------------------------

def test_no_negative_compute_outputs(synthetic_supply_df, synthetic_assumptions) -> None:
    df = run_allocation_model(synthetic_supply_df, synthetic_assumptions,
                              years=range(2024, 2029))
    assert_no_negative_compute(df)
    for col in BUCKET_COMPUTE_COLUMNS + ("largest_frontier_run_flop",
                                         "frontier_lab_training_compute_flop_year"):
        assert (df[col] >= 0).all(), f"{col} has negative values"


# --- 5: largest_run ≤ training pool -------------------------------------

def test_largest_run_less_than_training_pool(
    synthetic_supply_df, synthetic_assumptions
) -> None:
    df = run_allocation_model(synthetic_supply_df, synthetic_assumptions,
                              years=range(2024, 2029))
    assert (df["largest_frontier_run_flop"]
            <= df["training_compute_flop_year"] + 1e-9).all()


# --- 6: combined-scenario count -----------------------------------------

def test_combined_scenarios_count(synthetic_supply_df, synthetic_assumptions) -> None:
    """Cross product: supply scenarios × allocation scenarios = combined count."""
    n_supply = synthetic_supply_df["scenario"].nunique()
    n_alloc = len(synthetic_assumptions["scenarios"])
    df = run_allocation_model(synthetic_supply_df, synthetic_assumptions,
                              years=range(2024, 2029))
    assert df["combined_scenario"].nunique() == n_supply * n_alloc


# --- 7: required output columns present ---------------------------------

def test_required_columns_present(synthetic_supply_df, synthetic_assumptions) -> None:
    df = run_allocation_model(synthetic_supply_df, synthetic_assumptions,
                              years=range(2024, 2029))
    required = {
        "year", "supply_scenario", "allocation_scenario", "combined_scenario",
        "usable_compute_flop_year",
        "training_compute_flop_year", "inference_compute_flop_year",
        "ai_rnd_experiment_compute_flop_year", "post_training_compute_flop_year",
        "safety_eval_compute_flop_year", "reserved_idle_fragmented_compute_flop_year",
        "frontier_lab_training_compute_flop_year",
        "largest_frontier_run_flop", "frontier_run_share_of_total_compute",
    }
    assert required <= set(df.columns), (
        f"Missing columns: {required - set(df.columns)}"
    )


# --- 8: pipeline runs end-to-end ----------------------------------------

def test_allocation_pipeline_runs(synthetic_supply_df, synthetic_assumptions) -> None:
    """Smoke test that run_allocation_model() doesn't raise on synthetic
    inputs and the bucket-share invariant is enforced post-hoc."""
    df = run_allocation_model(synthetic_supply_df, synthetic_assumptions,
                              years=range(2024, 2029))
    n_supply = synthetic_supply_df["scenario"].nunique()
    n_alloc = len(synthetic_assumptions["scenarios"])
    n_years = 5
    assert len(df) == n_supply * n_alloc * n_years
    # Allocation-side invariants survive merge:
    assert_bucket_shares_sum_to_one(df)


# --- additional: validate_allocation_shares catches bad sums ------------

def test_validate_allocation_shares_rejects_bad_sum() -> None:
    df = pd.DataFrame({
        "allocation_scenario": ["bad"],
        "year": [2024],
        "inference_share": [0.50],
        "training_share": [0.30],
        "ai_rnd_experiment_share": [0.10],
        "post_training_share": [0.05],
        "safety_eval_share": [0.03],
        "reserved_idle_fragmented_share": [0.10],  # makes sum 1.08
        "frontier_lab_training_share": [0.60],
        "largest_run_concentration": [0.20],
        "cluster_contiguity_factor": [0.90],
    })
    with pytest.raises(ValueError, match="sum to ≠ 1.0"):
        validate_allocation_shares(df)
