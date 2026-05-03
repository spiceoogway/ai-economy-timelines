"""Tests for Phase 1 frontier filters."""
from __future__ import annotations

import pandas as pd

from model.frontier_filters import (
    rule_a_top_n_by_compute_at_release,
    rule_b_top_per_org_per_year,
)


def _toy_models() -> pd.DataFrame:
    """Twelve synthetic models with predictable compute and release times."""
    rows = []
    for i in range(12):
        rows.append(
            {
                "model_name": f"M{i}",
                "organization": "OrgA" if i % 2 == 0 else "OrgB",
                "release_year": 2023 if i < 6 else 2024,
                "release_year_fractional": 2023.0 + 0.1 * i,
                # Compute increases with i, so largest indices are largest.
                "training_compute_flop": float(10 ** (20 + i)),
            }
        )
    return pd.DataFrame(rows)


def test_rule_a_excludes_models_dominated_in_their_window() -> None:
    """A model is flagged only if it was in the top-N of the rolling
    window ending at its own release. Models with smaller compute than
    N earlier-released competitors must NOT be flagged."""
    df = pd.DataFrame(
        {
            "model_name": list("ABCDE"),
            "organization": ["O"] * 5,
            "release_year": [2024] * 5,
            "release_year_fractional": [2024.0, 2024.2, 2024.4, 2024.6, 2024.8],
            "training_compute_flop": [10.0, 5.0, 8.0, 1.0, 3.0],
        }
    )
    flags = rule_a_top_n_by_compute_at_release(df, n=2, window_years=1.0)
    # Indices 0-2 are flagged (first two trivially; index 2 has compute=8
    # which is in top-2 of [10, 5, 8]).
    assert flags.iloc[0]
    assert flags.iloc[1]
    assert flags.iloc[2]
    # Indices 3-4 have compute < both 10 and 8, so they are dominated by
    # earlier competitors in their windows and must not be flagged.
    assert not flags.iloc[3]
    assert not flags.iloc[4]


def test_rule_b_one_per_org_per_year() -> None:
    df = _toy_models()
    flags = rule_b_top_per_org_per_year(df)
    flagged = df[flags]
    # Each (org, year) pair appears at most once among flagged models.
    counts = flagged.groupby(["organization", "release_year"]).size()
    assert (counts == 1).all()
    # And the flagged row in each group should be the highest-compute one.
    for (org, yr), group in df.groupby(["organization", "release_year"]):
        flagged_in_group = group[flags.loc[group.index]]
        assert len(flagged_in_group) == 1
        assert flagged_in_group["training_compute_flop"].iloc[0] == group["training_compute_flop"].max()
