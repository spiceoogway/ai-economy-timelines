"""DuckDB review-database builder.

Loads existing CSV outputs into a single local DuckDB file
(`outputs/database/ai_economy.duckdb`) and creates SQL views for the
common review tasks: scenario matrix, slow / base / fast handoff,
2040 ranking, base-case timeseries, and source/confidence audit.

The review database is a **generated artifact**. The source of truth
remains the YAMLs, Python pipelines, CSV/Parquet outputs, and Markdown
findings. The database can be deleted and rebuilt at any time.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import NamedTuple

import duckdb
import pandas as pd
import yaml

from model.runtime import (
    ASSUMPTIONS_DIR,
    OUTPUTS_DIR,
    PROCESSED_DIR,
    TABLES_DIR,
)

# --- constants -----------------------------------------------------------

DATABASE_DIR = OUTPUTS_DIR / "database"
DATABASE_PATH = DATABASE_DIR / "ai_economy.duckdb"
DATABASE_MANIFEST = DATABASE_DIR / "database_manifest.json"

SCHEMA_VERSION = "1"

# Mapping of supply-scenario `name` field → short ID used in
# `combined_scenario_id`. Snake-case, no spaces, SQL-friendly.
SUPPLY_SCENARIO_ID = {
    "base_input_case": "base",
    "capex_rich": "capex_rich",
    "chip_bottleneck": "chip_bottleneck",
    "power_datacenter_bottleneck": "power_dc_bottleneck",
}
ALLOCATION_SCENARIO_ID = {
    "allocation_base": "base",
    "allocation_inference_heavy": "inference_heavy",
    "allocation_training_race": "training_race",
    "allocation_rnd_acceleration": "rnd_acceleration",
}


class TableSpec(NamedTuple):
    """One CSV → DuckDB table mapping."""
    table_name: str
    csv_path: Path
    description: str


def _table_specs() -> list[TableSpec]:
    """The 13 tables loaded into the review database."""
    return [
        # Historical
        TableSpec(
            "historical_models",
            PROCESSED_DIR / "historical_models.csv",
            "Cleaned Epoch 'Notable AI Models' dataset (1,011 rows, 1950–2026)",
        ),
        TableSpec(
            "historical_trend_estimates",
            TABLES_DIR / "historical_trend_estimates.csv",
            "All log-linear trend fits (compute / cost / cost-per-FLOP × frontier rules)",
        ),
        TableSpec(
            "historical_hardware_summary",
            TABLES_DIR / "historical_hardware_summary.csv",
            "Hardware-type usage by year for frontier-flagged historical models",
        ),
        # Supply
        TableSpec(
            "supply_fundamental_inputs_by_year",
            TABLES_DIR / "supply_fundamental_inputs_by_year.csv",
            "Annual scenario projections (4 scenarios × 17 years)",
        ),
        TableSpec(
            "supply_scenario_summary",
            TABLES_DIR / "supply_scenario_summary.csv",
            "Pivot summary at milestone years",
        ),
        TableSpec(
            "supply_binding_constraints",
            TABLES_DIR / "supply_binding_constraints.csv",
            "Years-by-binding-constraint counts per supply scenario",
        ),
        TableSpec(
            "supply_capex_requirements",
            TABLES_DIR / "supply_capex_requirements.csv",
            "Capex required vs available per scenario per year",
        ),
        TableSpec(
            "supply_sensitivity_analysis",
            TABLES_DIR / "supply_sensitivity_analysis.csv",
            "One-parameter perturbations of base scenario",
        ),
        # Allocation
        TableSpec(
            "allocation_compute_by_bucket",
            TABLES_DIR / "allocation_compute_by_bucket.csv",
            "Year × combined-scenario allocation across the 6 buckets (272 rows)",
        ),
        TableSpec(
            "allocation_largest_frontier_run",
            TABLES_DIR / "allocation_largest_frontier_run.csv",
            "Headline largest_frontier_run_flop per combined scenario per year",
        ),
        TableSpec(
            "allocation_scenario_summary",
            TABLES_DIR / "allocation_scenario_summary.csv",
            "Per-combined-scenario milestone summary + 16-year CAGRs",
        ),
        TableSpec(
            "allocation_vs_historical_trend",
            TABLES_DIR / "allocation_vs_historical_trend.csv",
            "Year-by-year gap_ratio between allocation projections and historical extrapolation",
        ),
        TableSpec(
            "allocation_share_assumptions_by_year",
            TABLES_DIR / "allocation_share_assumptions_by_year.csv",
            "Interpolated allocation parameters by year (audit trail)",
        ),
    ]


# --- combined_scenario_id derivation ------------------------------------


def _add_combined_scenario_id(df: pd.DataFrame) -> pd.DataFrame:
    """If the dataframe has supply_scenario + allocation_scenario columns,
    add a snake-case `combined_scenario_id` column for SQL queries."""
    if "supply_scenario" in df.columns and "allocation_scenario" in df.columns:
        df = df.copy()
        df["combined_scenario_id"] = (
            df["supply_scenario"].map(SUPPLY_SCENARIO_ID).fillna(df["supply_scenario"])
            + "__"
            + df["allocation_scenario"].map(ALLOCATION_SCENARIO_ID).fillna(df["allocation_scenario"])
        )
    return df


# --- table loading ------------------------------------------------------


def load_tables(con: duckdb.DuckDBPyConnection) -> list[tuple[str, int]]:
    """Load each CSV as a DuckDB table. Returns [(table_name, row_count), …]."""
    results = []
    for spec in _table_specs():
        if not spec.csv_path.exists():
            raise FileNotFoundError(
                f"{spec.csv_path} not found. Run the corresponding pipeline "
                "(`uv run historical` / `uv run supply` / `uv run allocation`) "
                "to produce the missing output."
            )
        df = pd.read_csv(spec.csv_path)
        df = _add_combined_scenario_id(df)
        con.register("_tmp_df", df)
        con.execute(f"CREATE OR REPLACE TABLE {spec.table_name} AS SELECT * FROM _tmp_df")
        con.unregister("_tmp_df")
        n = con.execute(f"SELECT COUNT(*) FROM {spec.table_name}").fetchone()[0]
        results.append((spec.table_name, int(n)))
    return results


# --- sources_and_confidence (built from YAML at load time) --------------


def _flatten_supply_assumptions(yaml_path: Path) -> list[dict]:
    """Flatten the supply YAML into one row per (parameter, scenario)."""
    raw = yaml.safe_load(yaml_path.read_text())
    rows: list[dict] = []
    if isinstance(raw, dict):
        # Supply YAML: parameter-keyed at top level
        for param, pblock in raw.items():
            if not isinstance(pblock, dict) or "scenarios" not in pblock:
                continue
            unit = pblock.get("unit")
            for scen, sblock in pblock["scenarios"].items():
                rows.append({
                    "input": param,
                    "component": "supply_capacity",
                    "scenario": scen,
                    "source": sblock.get("source"),
                    "source_type": "supply YAML",
                    "confidence": sblock.get("confidence"),
                    "unit": unit,
                    "used_for": param,
                    "notes": "",
                })
    return rows


def _flatten_allocation_assumptions(yaml_path: Path) -> list[dict]:
    """Flatten the allocation YAML — scenario-keyed structure."""
    raw = yaml.safe_load(yaml_path.read_text())
    rows: list[dict] = []
    if not isinstance(raw, dict) or "scenarios" not in raw:
        return rows
    for scen_name, sblock in raw["scenarios"].items():
        rows.append({
            "input": "allocation_shares",
            "component": "allocation",
            "scenario": scen_name,
            "source": sblock.get("source"),
            "source_type": "allocation YAML",
            "confidence": sblock.get("confidence"),
            "unit": "share",
            "used_for": "bucket_shares + training_decomposition",
            "notes": sblock.get("description", ""),
        })
    return rows


def load_sources_and_confidence(con: duckdb.DuckDBPyConnection) -> int:
    """Build a single `sources_and_confidence` table from the assumption YAMLs."""
    rows = []
    rows.extend(_flatten_supply_assumptions(
        ASSUMPTIONS_DIR / "supply_input_assumptions.yaml"
    ))
    rows.extend(_flatten_allocation_assumptions(
        ASSUMPTIONS_DIR / "allocation_input_assumptions.yaml"
    ))
    df = pd.DataFrame(rows)
    con.register("_tmp_df", df)
    con.execute(
        "CREATE OR REPLACE TABLE sources_and_confidence AS SELECT * FROM _tmp_df"
    )
    con.unregister("_tmp_df")
    return len(rows)


# --- views --------------------------------------------------------------

VIEW_DEFINITIONS = {
    "v_largest_run_2040_ranked": """
        CREATE OR REPLACE VIEW v_largest_run_2040_ranked AS
        SELECT
            combined_scenario,
            combined_scenario_id,
            supply_scenario,
            allocation_scenario,
            largest_frontier_run_flop,
            frontier_run_share_of_total_compute
        FROM allocation_largest_frontier_run
        WHERE year = 2040
        ORDER BY largest_frontier_run_flop DESC
    """,
    "v_phase4_handoff": """
        CREATE OR REPLACE VIEW v_phase4_handoff AS
        SELECT
            year,
            combined_scenario,
            combined_scenario_id,
            largest_frontier_run_flop,
            training_compute_flop_year,
            ai_rnd_experiment_compute_flop_year,
            post_training_compute_flop_year,
            inference_compute_flop_year,
            frontier_run_share_of_total_compute
        FROM allocation_compute_by_bucket
        WHERE combined_scenario_id IN (
            'chip_bottleneck__inference_heavy',
            'base__base',
            'capex_rich__training_race'
        )
        ORDER BY year, combined_scenario_id
    """,
    "v_scenario_matrix": """
        CREATE OR REPLACE VIEW v_scenario_matrix AS
        SELECT * FROM allocation_scenario_summary
        ORDER BY largest_run_2040 DESC
    """,
    "v_base_case_timeseries": """
        CREATE OR REPLACE VIEW v_base_case_timeseries AS
        SELECT * FROM allocation_compute_by_bucket
        WHERE combined_scenario_id = 'base__base'
        ORDER BY year
    """,
    "v_slow_base_fast_envelope": """
        CREATE OR REPLACE VIEW v_slow_base_fast_envelope AS
        SELECT
            year,
            CASE combined_scenario_id
                WHEN 'chip_bottleneck__inference_heavy' THEN 'slow'
                WHEN 'base__base' THEN 'base'
                WHEN 'capex_rich__training_race' THEN 'fast'
            END AS envelope,
            combined_scenario_id,
            largest_frontier_run_flop,
            training_compute_flop_year,
            inference_compute_flop_year,
            ai_rnd_experiment_compute_flop_year,
            post_training_compute_flop_year,
            frontier_run_share_of_total_compute
        FROM allocation_compute_by_bucket
        WHERE combined_scenario_id IN (
            'chip_bottleneck__inference_heavy',
            'base__base',
            'capex_rich__training_race'
        )
        ORDER BY year, envelope
    """,
    "v_sources_and_confidence": """
        CREATE OR REPLACE VIEW v_sources_and_confidence AS
        SELECT
            input,
            component,
            scenario,
            source,
            source_type,
            confidence,
            unit,
            used_for,
            notes
        FROM sources_and_confidence
        ORDER BY component, input, scenario
    """,
}


def create_views(con: duckdb.DuckDBPyConnection) -> list[str]:
    """Create the 6 review views. Returns the list of view names."""
    for name, sql in VIEW_DEFINITIONS.items():
        con.execute(sql)
    return list(VIEW_DEFINITIONS.keys())


# --- manifest -----------------------------------------------------------


def _git_commit() -> str:
    """Best-effort git short hash; returns 'unknown' if git isn't available."""
    import subprocess
    try:
        out = subprocess.check_output(
            ["git", "-C", str(DATABASE_DIR.parent.parent), "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
        ).decode().strip()
        return out
    except Exception:
        return "unknown"


def write_manifest(
    table_results: list[tuple[str, int]],
    view_names: list[str],
    sources_count: int,
    path: Path = DATABASE_MANIFEST,
) -> dict:
    """Write the database manifest JSON."""
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "git_commit": _git_commit(),
        "database_path": str(DATABASE_PATH.relative_to(DATABASE_PATH.parent.parent.parent)),
        "input_files": [str(spec.csv_path.name) for spec in _table_specs()],
        "tables_created": [name for name, _ in table_results] + ["sources_and_confidence"],
        "views_created": view_names,
        "row_counts": {name: n for name, n in table_results} | {
            "sources_and_confidence": sources_count
        },
        "note": (
            "Generated artifact. Source of truth is YAML / Python / CSV / "
            "Markdown. Rebuild with: uv run database"
        ),
    }
    path.write_text(json.dumps(manifest, indent=2))
    return manifest


# --- top-level orchestrator ---------------------------------------------


def build_review_database(
    db_path: Path = DATABASE_PATH,
    manifest_path: Path = DATABASE_MANIFEST,
) -> dict:
    """Build the full review database end-to-end. Returns the manifest dict."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()  # rebuild fresh

    con = duckdb.connect(str(db_path))
    try:
        table_results = load_tables(con)
        sources_count = load_sources_and_confidence(con)
        view_names = create_views(con)
    finally:
        con.close()

    return write_manifest(table_results, view_names, sources_count, manifest_path)
