"""Smoke tests for cross-cutting constants.

Locks in the contract: every scenario YAML must have a SCENARIO_COLORS
entry, and every CONSTRAINTS value must have a CONSTRAINT_COLORS entry.
"""
from __future__ import annotations

import yaml

from model.runtime import CONSTRAINT_COLORS, SCENARIO_COLORS
from model.supply_engine import CONSTRAINTS, SCENARIOS_DIR


def test_every_scenario_has_a_color() -> None:
    scenario_yamls = sorted(SCENARIOS_DIR.glob("supply_*.yaml"))
    assert scenario_yamls, "no scenario YAMLs found"
    for path in scenario_yamls:
        d = yaml.safe_load(path.read_text())
        name = d["name"]
        assert name in SCENARIO_COLORS, (
            f"scenario {name!r} (from {path.name}) has no entry in SCENARIO_COLORS"
        )


def test_every_constraint_has_a_color() -> None:
    for c in CONSTRAINTS:
        assert c in CONSTRAINT_COLORS, (
            f"constraint {c!r} (from CONSTRAINTS tuple) has no entry in CONSTRAINT_COLORS"
        )
