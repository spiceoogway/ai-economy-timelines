"""Tests for the supply-side compute-capacity engine."""
from __future__ import annotations

from pathlib import Path

import pytest

from model.supply_engine import (
    CONSTRAINTS,
    ScenarioConfig,
    load_assumptions,
    project_scenario,
)


def _tiny_scenario() -> ScenarioConfig:
    return ScenarioConfig(
        name="tiny",
        display_name="Tiny test scenario",
        description="Synthetic single-scenario fixture",
        assumption_scenario="tiny",
        start_year=2024,
        end_year=2030,
    )


def test_project_scenario_shape(tmp_assumptions_yaml: Path) -> None:
    a = load_assumptions(tmp_assumptions_yaml)
    df = project_scenario(_tiny_scenario(), a)
    assert len(df) == 7  # 2024..2030 inclusive
    expected_cols = {
        "year",
        "scenario",
        "available_stock_h100e",
        "binding_constraint",
        "usable_compute_flop_year",
    }
    assert expected_cols <= set(df.columns)
    assert df["binding_constraint"].isin(CONSTRAINTS).all()


def test_binding_constraint_is_argmin_of_limits(tmp_assumptions_yaml: Path) -> None:
    a = load_assumptions(tmp_assumptions_yaml)
    df = project_scenario(_tiny_scenario(), a).set_index("year")
    limit_cols = {
        "chip": "installed_stock_h100e_chip_limited",
        "power": "power_limited_stock_h100e",
        "datacenter": "datacenter_limited_stock_h100e",
        "capex": "capex_limited_stock_h100e",
    }
    for y, row in df.iterrows():
        limits = {c: row[col] for c, col in limit_cols.items()}
        true_argmin = min(limits, key=limits.get)
        assert row["binding_constraint"] == true_argmin, (
            f"year {y}: binding={row['binding_constraint']} but argmin={true_argmin} "
            f"(values: {limits})"
        )


def test_available_stock_equals_min_of_limits(tmp_assumptions_yaml: Path) -> None:
    a = load_assumptions(tmp_assumptions_yaml)
    df = project_scenario(_tiny_scenario(), a)
    limit_cols = [
        "installed_stock_h100e_chip_limited",
        "power_limited_stock_h100e",
        "datacenter_limited_stock_h100e",
        "capex_limited_stock_h100e",
    ]
    expected_min = df[limit_cols].min(axis=1)
    # Floating-point match within 1e-6 relative
    assert ((df["available_stock_h100e"] - expected_min).abs() < 1e-6).all()
