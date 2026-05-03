"""CI-style sanity checks on the output inventory.

Complement to `pipelines/validate_repo_outputs.py` — that script is a
runtime check after a full pipeline rebuild; this is a fast pytest
check that runs against whatever artifacts are committed to the repo.

Skipped (xfail-ish) when artifacts are missing rather than failing
hard, so a contributor can run pytest mid-rebuild without spurious
failures. Real validation lives in `uv run validate-outputs`.
"""
from __future__ import annotations

import pytest

from model.runtime import (
    ASSUMPTIONS_DIR,
    CHARTS_DIR,
    OUTPUTS_DIR,
    PROCESSED_DIR,
    SCENARIOS_DIR,
    TABLES_DIR,
)

# Subset of the most important / least-likely-to-be-mid-rebuild artifacts.
# The full inventory is in pipelines/validate_repo_outputs.py.
KEY_TABLES = [
    "historical_trend_estimates.csv",
    "supply_fundamental_inputs_by_year.csv",
    "allocation_compute_by_bucket.csv",
    "allocation_largest_frontier_run.csv",
]
KEY_CHARTS = [
    "historical_compute_over_time.png",
    "supply_usable_compute_capacity.png",
    "allocation_vs_historical_training_compute.png",
]
KEY_ASSUMPTIONS = [
    "supply_input_assumptions.yaml",
    "allocation_input_assumptions.yaml",
]


@pytest.mark.parametrize("name", KEY_TABLES)
def test_key_table_exists_and_nonempty(name: str) -> None:
    path = TABLES_DIR / name
    assert path.exists(), f"Missing: {path}"
    assert path.stat().st_size > 0, f"Empty: {path}"


@pytest.mark.parametrize("name", KEY_CHARTS)
def test_key_chart_exists(name: str) -> None:
    path = CHARTS_DIR / name
    assert path.exists(), f"Missing: {path}"
    assert path.stat().st_size > 0, f"Empty: {path}"


@pytest.mark.parametrize("name", KEY_ASSUMPTIONS)
def test_assumption_yaml_exists(name: str) -> None:
    path = ASSUMPTIONS_DIR / name
    assert path.exists(), f"Missing: {path}"
    assert path.stat().st_size > 0, f"Empty: {path}"


def test_scenarios_present() -> None:
    """All four supply + four allocation scenario YAMLs present."""
    supply = list(SCENARIOS_DIR.glob("supply_*.yaml"))
    allocation = list(SCENARIOS_DIR.glob("allocation_*.yaml"))
    assert len(supply) == 4, f"Expected 4 supply scenarios, found {len(supply)}"
    assert len(allocation) == 4, (
        f"Expected 4 allocation scenarios, found {len(allocation)}"
    )


def test_review_artifacts_present_or_skipped() -> None:
    """Review artifacts (DuckDB + workbook) are optional in tests; if
    they exist they must be non-empty."""
    db = OUTPUTS_DIR / "database" / "ai_economy.duckdb"
    workbook = OUTPUTS_DIR / "workbooks" / "ai_economy_model_review.xlsx"
    if db.exists():
        assert db.stat().st_size > 0, f"Empty: {db}"
    if workbook.exists():
        assert workbook.stat().st_size > 0, f"Empty: {workbook}"
