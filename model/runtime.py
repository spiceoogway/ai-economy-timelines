"""Cross-cutting constants: paths, colors, and source attributions.

Single source of truth for things that would otherwise get duplicated
across `model/*.py`, the test suite, and the `pipelines/*.py` drivers.

When adding a new scenario YAML, update SCENARIO_COLORS here. When
adding a new constraint to supply_engine.CONSTRAINTS, update
CONSTRAINT_COLORS. Both are checked by tests/test_runtime.py.
"""
from __future__ import annotations

from pathlib import Path

# --- paths ---------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
ASSUMPTIONS_DIR = DATA_DIR / "assumptions"
SCENARIOS_DIR = REPO_ROOT / "scenarios"
OUTPUTS_DIR = REPO_ROOT / "outputs"
CHARTS_DIR = OUTPUTS_DIR / "charts"
TABLES_DIR = OUTPUTS_DIR / "tables"

ASSUMPTIONS_YAML = ASSUMPTIONS_DIR / "supply_input_assumptions.yaml"
RAW_NOTABLE_AI_MODELS = RAW_DIR / "epoch_notable_ai_models_raw.csv"
HISTORICAL_TREND_TABLE = TABLES_DIR / "historical_trend_estimates.csv"

# --- colors --------------------------------------------------------------

# Frontier rules used by the historical baseline (a/b/c).
RULE_COLORS = {
    "frontier_rule_a": "tab:blue",
    "frontier_rule_b": "tab:orange",
    "frontier_rule_c": "tab:green",
}

# Supply scenarios. Keys must match the `name:` field in scenarios/*.yaml.
SCENARIO_COLORS = {
    "base_input_case": "tab:blue",
    "capex_rich": "tab:green",
    "chip_bottleneck": "tab:red",
    "power_datacenter_bottleneck": "tab:orange",
}

# Distinct markers per scenario so overlapping series remain readable when
# scenarios share a parameter trajectory (e.g. base and chip_bottleneck
# share `ai_datacenter_capacity_mw`; base / chip_bottleneck /
# power_datacenter_bottleneck share `ai_infrastructure_capex_usd`).
SCENARIO_MARKERS = {
    "base_input_case": "o",
    "capex_rich": "s",
    "chip_bottleneck": "^",
    "power_datacenter_bottleneck": "D",
}

# Allocation scenarios. Keys must match the `name:` field in
# scenarios/allocation_*.yaml. Distinct from SCENARIO_COLORS so
# scenario-grid charts (which combine supply × allocation) can colour
# the two axes independently.
ALLOCATION_SCENARIO_COLORS = {
    "allocation_base": "tab:blue",
    "allocation_inference_heavy": "tab:purple",
    "allocation_training_race": "tab:red",
    "allocation_rnd_acceleration": "tab:olive",
}

ALLOCATION_SCENARIO_MARKERS = {
    "allocation_base": "o",
    "allocation_inference_heavy": "s",
    "allocation_training_race": "^",
    "allocation_rnd_acceleration": "D",
}

# Allocation buckets — matches model.allocation_engine.BUCKET_SHARES.
BUCKET_COLORS = {
    "inference": "tab:blue",
    "training": "tab:red",
    "ai_rnd_experiment": "tab:green",
    "post_training": "tab:orange",
    "safety_eval": "tab:purple",
    "reserved_idle_fragmented": "#888888",
}

# Supply binding-constraint categories. Keys must match the entries in
# supply_engine.CONSTRAINTS.
CONSTRAINT_COLORS = {
    "chip": "#d62728",
    "power": "#ff7f0e",
    "datacenter": "#9467bd",
    "capex": "#2ca02c",
}

# --- attribution lines (for chart titles) --------------------------------

EPOCH_SOURCE_LINE = "Source: Epoch AI Notable AI Models (retrieved 2026-05-02)"
