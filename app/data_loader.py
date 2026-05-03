"""Data loader for the Streamlit scenario explorer.

Prefers the DuckDB review database
(`outputs/database/ai_economy.duckdb`); falls back to the per-output
CSVs under `outputs/tables/` when the database is missing.

Every loader is wrapped in `@st.cache_data` so DuckDB / CSV reads
happen once per Streamlit session, not on every widget interaction.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import duckdb
import pandas as pd
import streamlit as st

from model.runtime import OUTPUTS_DIR, TABLES_DIR

DATABASE_PATH = OUTPUTS_DIR / "database" / "ai_economy.duckdb"
DATABASE_MANIFEST_PATH = OUTPUTS_DIR / "database" / "database_manifest.json"
RUN_MANIFEST_PATH = OUTPUTS_DIR / "runs" / "latest_run_manifest.json"

# Snake-case ID derivation, mirrored from model.review_database.
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

ENVELOPE_LABELS = {
    "chip_bottleneck__inference_heavy": "slow",
    "base__base": "base",
    "capex_rich__training_race": "fast",
}


# --- existence checks ---------------------------------------------------


def database_exists() -> bool:
    return DATABASE_PATH.exists() and DATABASE_PATH.stat().st_size > 0


@st.cache_data
def database_manifest() -> dict | None:
    """Return the database build manifest, or None if missing."""
    if not DATABASE_MANIFEST_PATH.exists():
        return None
    return json.loads(DATABASE_MANIFEST_PATH.read_text())


@st.cache_data
def run_manifest() -> dict | None:
    """Return the latest pipeline-run manifest from
    `outputs/runs/latest_run_manifest.json`."""
    if not RUN_MANIFEST_PATH.exists():
        return None
    return json.loads(RUN_MANIFEST_PATH.read_text())


# --- low-level loader ---------------------------------------------------


def _add_combined_scenario_id(df: pd.DataFrame) -> pd.DataFrame:
    """Add snake-case `combined_scenario_id` if the dataframe has the
    supply_scenario + allocation_scenario columns."""
    if "supply_scenario" in df.columns and "allocation_scenario" in df.columns:
        df = df.copy()
        df["combined_scenario_id"] = (
            df["supply_scenario"].map(SUPPLY_SCENARIO_ID).fillna(df["supply_scenario"])
            + "__"
            + df["allocation_scenario"].map(ALLOCATION_SCENARIO_ID).fillna(df["allocation_scenario"])
        )
    return df


@st.cache_data
def load_table(name: str) -> pd.DataFrame:
    """Load a named table from DuckDB if available, else from
    `outputs/tables/<name>.csv`. Adds `combined_scenario_id` where
    applicable.
    """
    if database_exists():
        try:
            with duckdb.connect(str(DATABASE_PATH), read_only=True) as con:
                df = con.execute(f"SELECT * FROM {name}").fetchdf()
            return df
        except Exception:
            # Fall through to CSV
            pass
    csv_path = TABLES_DIR / f"{name}.csv"
    if not csv_path.exists():
        raise FileNotFoundError(
            f"Table {name!r} not found in DuckDB or CSV. Did you run "
            "`uv run historical && uv run supply && uv run allocation`?"
        )
    df = pd.read_csv(csv_path)
    return _add_combined_scenario_id(df)


@st.cache_data
def load_view(view_name: str) -> pd.DataFrame:
    """Load a SQL view from DuckDB. Falls back to a CSV reconstruction
    where possible."""
    if database_exists():
        try:
            with duckdb.connect(str(DATABASE_PATH), read_only=True) as con:
                return con.execute(f"SELECT * FROM {view_name}").fetchdf()
        except Exception:
            pass
    # CSV fallback for the views we can reconstruct in pandas
    if view_name == "v_phase4_handoff":
        return _csv_phase4_handoff()
    if view_name == "v_largest_run_2040_ranked":
        return _csv_largest_run_2040_ranked()
    if view_name == "v_slow_base_fast_envelope":
        return _csv_slow_base_fast()
    if view_name == "v_scenario_matrix":
        return load_table("allocation_scenario_summary").sort_values(
            "largest_run_2040", ascending=False
        )
    raise FileNotFoundError(
        f"View {view_name!r} not available; database missing and no CSV fallback."
    )


# --- specific loaders the pages ask for --------------------------------


@st.cache_data
def load_scenario_matrix() -> pd.DataFrame:
    """16 combined scenarios × milestone metrics, with combined_scenario_id."""
    df = load_table("allocation_scenario_summary")
    return df.sort_values("largest_run_2040", ascending=False).reset_index(drop=True)


@st.cache_data
def load_phase4_handoff() -> pd.DataFrame:
    """Slow / base / fast envelope rows, wide format with the four
    base-case bucket totals."""
    return _csv_phase4_handoff()


def _csv_phase4_handoff() -> pd.DataFrame:
    df = load_table("allocation_compute_by_bucket")
    sub = df[df["combined_scenario_id"].isin(ENVELOPE_LABELS.keys())].copy()
    sub["envelope"] = sub["combined_scenario_id"].map(ENVELOPE_LABELS)
    largest = (
        sub.pivot(index="year", columns="envelope", values="largest_frontier_run_flop")
        [["slow", "base", "fast"]]
        .rename(columns={
            "slow": "slow_largest_frontier_run_flop",
            "base": "base_largest_frontier_run_flop",
            "fast": "fast_largest_frontier_run_flop",
        })
    )
    base_buckets = sub[sub["envelope"] == "base"].set_index("year")[[
        "training_compute_flop_year",
        "ai_rnd_experiment_compute_flop_year",
        "post_training_compute_flop_year",
        "inference_compute_flop_year",
    ]].rename(columns={
        "training_compute_flop_year": "base_training_compute_flop_year",
        "ai_rnd_experiment_compute_flop_year": "base_ai_rnd_experiment_compute_flop_year",
        "post_training_compute_flop_year": "base_post_training_compute_flop_year",
        "inference_compute_flop_year": "base_inference_compute_flop_year",
    })
    return largest.join(base_buckets).reset_index()


def _csv_largest_run_2040_ranked() -> pd.DataFrame:
    df = load_table("allocation_largest_frontier_run")
    return df[df["year"] == 2040].sort_values(
        "largest_frontier_run_flop", ascending=False
    ).reset_index(drop=True)


def _csv_slow_base_fast() -> pd.DataFrame:
    df = load_table("allocation_compute_by_bucket")
    sub = df[df["combined_scenario_id"].isin(ENVELOPE_LABELS.keys())].copy()
    sub["envelope"] = sub["combined_scenario_id"].map(ENVELOPE_LABELS)
    return sub[[
        "year", "envelope", "combined_scenario_id",
        "largest_frontier_run_flop", "training_compute_flop_year",
        "inference_compute_flop_year", "ai_rnd_experiment_compute_flop_year",
        "post_training_compute_flop_year",
        "frontier_run_share_of_total_compute",
    ]].sort_values(["year", "envelope"]).reset_index(drop=True)


@st.cache_data
def load_largest_frontier_run() -> pd.DataFrame:
    """All 16 combined scenarios × 17 years."""
    return load_table("allocation_largest_frontier_run")


@st.cache_data
def load_allocation_buckets() -> pd.DataFrame:
    """Full bucket-level allocation table."""
    return load_table("allocation_compute_by_bucket")


@st.cache_data
def load_supply_annual() -> pd.DataFrame:
    return load_table("supply_fundamental_inputs_by_year")


@st.cache_data
def load_supply_summary() -> pd.DataFrame:
    return load_table("supply_scenario_summary")


@st.cache_data
def load_historical_trends() -> pd.DataFrame:
    return load_table("historical_trend_estimates")


@st.cache_data
def load_assumptions_long() -> pd.DataFrame:
    """Flattened source/confidence audit. Loaded from DuckDB if available,
    otherwise reconstructed from the YAMLs."""
    if database_exists():
        try:
            with duckdb.connect(str(DATABASE_PATH), read_only=True) as con:
                return con.execute("SELECT * FROM sources_and_confidence").fetchdf()
        except Exception:
            pass
    # Reconstruct from YAMLs
    from model.review_database import (
        _flatten_allocation_assumptions,
        _flatten_supply_assumptions,
    )
    from model.runtime import ASSUMPTIONS_DIR
    rows = _flatten_supply_assumptions(
        ASSUMPTIONS_DIR / "supply_input_assumptions.yaml"
    )
    rows.extend(_flatten_allocation_assumptions(
        ASSUMPTIONS_DIR / "allocation_input_assumptions.yaml"
    ))
    return pd.DataFrame(rows)


@st.cache_data
def load_allocation_share_assumptions() -> pd.DataFrame:
    return load_table("allocation_share_assumptions_by_year")


@st.cache_data
def load_vs_historical() -> pd.DataFrame:
    return load_table("allocation_vs_historical_trend")


# --- historical fit constants -------------------------------------------


@st.cache_data
def historical_rule_a_fit() -> tuple[float, float, float]:
    """(slope_log10_per_year, intercept_log10, annual_multiplier),
    rebased so 2024 corresponds to 1e25 FLOP per single frontier run."""
    df = load_historical_trends()
    row = df[
        (df["trend_name"] == "training_compute")
        & (df["frontier_rule"] == "frontier_rule_a_2018+")
    ].iloc[0]
    slope = float(row["slope_log10_per_year"])
    mult = float(row["annual_growth_multiplier"])
    intercept = 25.0 - slope * 2024.0
    return slope, intercept, mult
