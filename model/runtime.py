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
