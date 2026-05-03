"""Tests for the assumptions YAML loader."""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from model.fundamental_inputs import load_assumptions


def test_loader_returns_long_format(tmp_assumptions_yaml: Path) -> None:
    df = load_assumptions(tmp_assumptions_yaml)
    expected_cols = {
        "parameter",
        "scenario",
        "year",
        "value",
        "unit",
        "source",
        "confidence",
        "notes",
    }
    assert set(df.columns) == expected_cols
    assert df["year"].dtype.kind == "i"
    assert df["value"].dtype.kind == "f"
    # 15 params, 1 scenario each, mix of 1- or 2-milestone — > 0
    assert len(df) > 15
    assert df["scenario"].nunique() == 1
    assert df["scenario"].iloc[0] == "tiny"


def test_loader_rejects_milestone_missing_year(tmp_path: Path) -> None:
    """A milestone without `year` should raise with an informative message."""
    bad = {
        "h100_equivalent_shipments": {
            "unit": "units",
            "scenarios": {
                "broken": {
                    "milestones": [{"value": 1_000_000}],  # missing year
                },
            },
        },
    }
    p = tmp_path / "bad.yaml"
    p.write_text(yaml.safe_dump(bad))
    with pytest.raises(ValueError, match="missing year"):
        load_assumptions(p)
