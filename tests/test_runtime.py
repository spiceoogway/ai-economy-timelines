"""Smoke tests for cross-cutting constants.

The runtime module doesn't exist yet (Tier A change 3). This test
locks in the *contract*: any future scenario YAML must have a color
entry, and any constraint must have a color entry. We check the
constants wherever they currently live so this test passes today and
keeps passing after the runtime extraction.
"""
from __future__ import annotations

from pathlib import Path

import yaml

from model.fundamental_inputs import CONSTRAINTS, SCENARIOS_DIR

# Try the runtime module first (post-Tier-A.3); fall back to the
# pipelines driver (pre-Tier-A.3) so this test passes through the
# refactor.
try:
    from model.runtime import CONSTRAINT_COLORS, SCENARIO_COLORS  # type: ignore
except ImportError:
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "notebooks"))
    try:
        from run_phase2_sprint2 import CONSTRAINT_COLORS, SCENARIO_COLORS  # type: ignore
    except ImportError:
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipelines"))
        from phase2 import CONSTRAINT_COLORS, SCENARIO_COLORS  # type: ignore


def test_every_scenario_has_a_color() -> None:
    scenario_yamls = sorted(SCENARIOS_DIR.glob("phase2_*.yaml"))
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
