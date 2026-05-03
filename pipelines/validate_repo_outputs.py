"""Repo-output validation.

Run with: `uv run validate-outputs`

Walks the outputs/ tree and verifies that every artifact promised by
the docs / scope actually exists, is non-empty, and matches its
declared path. Also writes outputs/runs/latest_run_manifest.json
capturing the timestamp / git commit / pipeline state.

Exit code 0 if all checks pass; exit code 1 otherwise. Suitable for
running after a full pipeline rebuild
(`historical && supply && allocation && database && workbook`).

This script is a runtime check. The complementary CI-style check is
in tests/test_output_inventory.py.
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from model.runtime import (
    ASSUMPTIONS_DIR,
    CHARTS_DIR,
    OUTPUTS_DIR,
    PROCESSED_DIR,
    SCENARIOS_DIR,
    TABLES_DIR,
)

RUNS_DIR = OUTPUTS_DIR / "runs"
LATEST_MANIFEST = RUNS_DIR / "latest_run_manifest.json"

# --- expected artifacts -------------------------------------------------

REQUIRED_TABLES = [
    "historical_trend_estimates.csv",
    "historical_hardware_summary.csv",
    "supply_fundamental_inputs_by_year.csv",
    "supply_scenario_summary.csv",
    "supply_binding_constraints.csv",
    "supply_capex_requirements.csv",
    "supply_sensitivity_analysis.csv",
    "allocation_compute_by_bucket.csv",
    "allocation_largest_frontier_run.csv",
    "allocation_scenario_summary.csv",
    "allocation_vs_historical_trend.csv",
    "allocation_share_assumptions_by_year.csv",
]

REQUIRED_CHARTS = [
    # historical
    "historical_compute_over_time.png",
    "historical_cost_over_time.png",
    "historical_cost_per_flop_over_time.png",
    "historical_compute_by_organization.png",
    "historical_cost_by_organization.png",
    "historical_residuals_compute.png",
    "historical_residuals_cost.png",
    "historical_hardware_timeline.png",
    # supply
    "supply_accelerator_stock_h100e.png",
    "supply_theoretical_compute_capacity.png",
    "supply_usable_compute_capacity.png",
    "supply_power_capacity_constraint.png",
    "supply_capex_required.png",
    "supply_binding_constraint_by_year.png",
    "supply_vs_historical_compute_trend.png",
    "supply_cost_per_h100e_by_variant.png",
    "supply_sensitivity_bands.png",
    # allocation
    "allocation_compute_by_bucket.png",
    "allocation_largest_frontier_run.png",
    "allocation_vs_historical_training_compute.png",
    "allocation_training_vs_inference_share.png",
    "allocation_frontier_run_share_of_total.png",
    "allocation_scenario_grid.png",
]

REQUIRED_PROCESSED = [
    "historical_models.csv",
    "historical_models.parquet",
    "supply_fundamental_inputs.csv",
    "allocation_compute_by_bucket.csv",
]

REQUIRED_REVIEW_ARTIFACTS = [
    OUTPUTS_DIR / "database" / "ai_economy.duckdb",
    OUTPUTS_DIR / "database" / "database_manifest.json",
    OUTPUTS_DIR / "workbooks" / "ai_economy_model_review.xlsx",
]

REQUIRED_ASSUMPTIONS = [
    "supply_input_assumptions.yaml",
    "allocation_input_assumptions.yaml",
]

REQUIRED_SCENARIOS = [
    "supply_base_input_case.yaml",
    "supply_capex_rich.yaml",
    "supply_chip_bottleneck.yaml",
    "supply_power_datacenter_bottleneck.yaml",
    "allocation_base.yaml",
    "allocation_inference_heavy.yaml",
    "allocation_training_race.yaml",
    "allocation_rnd_acceleration.yaml",
]


# --- check helpers ------------------------------------------------------


def _check_file(path: Path, *, label: str) -> tuple[bool, str]:
    if not path.exists():
        return False, f"MISSING: {label} ({path})"
    if path.stat().st_size == 0:
        return False, f"EMPTY:   {label} ({path})"
    return True, f"OK:      {label}"


def _check_csv_nonzero(path: Path, *, label: str) -> tuple[bool, str]:
    """Stronger check for CSVs: must have ≥2 rows (header + ≥1 data row)."""
    ok, msg = _check_file(path, label=label)
    if not ok:
        return ok, msg
    n = sum(1 for _ in path.open())
    if n < 2:
        return False, f"NO ROWS: {label} (only {n} lines)"
    return True, f"OK:      {label} ({n - 1} data rows)"


def _git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
            cwd=OUTPUTS_DIR.parent,
        ).decode().strip()
    except Exception:
        return "unknown"


def _python_version() -> str:
    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"


# --- main ---------------------------------------------------------------


def main() -> None:
    failures: list[str] = []
    passes: list[str] = []

    print("=== Repo Output Validation ===")
    print()
    print("[Tables]")
    for name in REQUIRED_TABLES:
        ok, msg = _check_csv_nonzero(TABLES_DIR / name, label=name)
        (passes if ok else failures).append(msg)
        print(f"  {msg}")

    print("\n[Charts]")
    for name in REQUIRED_CHARTS:
        ok, msg = _check_file(CHARTS_DIR / name, label=name)
        (passes if ok else failures).append(msg)
        print(f"  {msg}")

    print("\n[Processed datasets]")
    for name in REQUIRED_PROCESSED:
        ok, msg = _check_file(PROCESSED_DIR / name, label=name)
        (passes if ok else failures).append(msg)
        print(f"  {msg}")

    print("\n[Review artifacts]")
    for path in REQUIRED_REVIEW_ARTIFACTS:
        ok, msg = _check_file(path, label=path.name)
        (passes if ok else failures).append(msg)
        print(f"  {msg}")

    print("\n[Assumption YAMLs]")
    for name in REQUIRED_ASSUMPTIONS:
        ok, msg = _check_file(ASSUMPTIONS_DIR / name, label=name)
        (passes if ok else failures).append(msg)
        print(f"  {msg}")

    print("\n[Scenario YAMLs]")
    for name in REQUIRED_SCENARIOS:
        ok, msg = _check_file(SCENARIOS_DIR / name, label=name)
        (passes if ok else failures).append(msg)
        print(f"  {msg}")

    # Test pass/fail
    print("\n[Tests]")
    try:
        result = subprocess.run(
            ["uv", "run", "pytest", "-q"],
            capture_output=True, text=True, cwd=OUTPUTS_DIR.parent,
        )
        tests_passed = result.returncode == 0
        last_line = result.stdout.strip().splitlines()[-1] if result.stdout.strip() else ""
        print(f"  pytest: {last_line}")
        if tests_passed:
            passes.append(f"OK:      pytest ({last_line})")
        else:
            failures.append(f"FAIL:    pytest ({last_line})")
    except FileNotFoundError:
        tests_passed = False
        failures.append("FAIL:    pytest (uv not found)")
        print("  pytest: skipped (uv not found)")

    # Write run manifest
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema_version": "1",
        "run_timestamp": datetime.now(timezone.utc).isoformat(),
        "git_commit": _git_commit(),
        "python_version": _python_version(),
        "pipelines_run": ["historical", "supply", "allocation", "database", "workbook"],
        "input_files": REQUIRED_ASSUMPTIONS + REQUIRED_SCENARIOS,
        "output_tables": REQUIRED_TABLES,
        "output_charts": REQUIRED_CHARTS,
        "database_path": "outputs/database/ai_economy.duckdb",
        "workbook_path": "outputs/workbooks/ai_economy_model_review.xlsx",
        "tests_passed": tests_passed,
        "passes": len(passes),
        "failures": len(failures),
    }
    LATEST_MANIFEST.write_text(json.dumps(manifest, indent=2))

    print(f"\nManifest → {LATEST_MANIFEST}")
    print()
    print(f"=== Summary: {len(passes)} pass / {len(failures)} fail ===")

    if failures:
        print("\nFailures:")
        for f in failures:
            print(f"  {f}")
        sys.exit(1)
    print("\nAll checks passed.")


if __name__ == "__main__":
    main()
