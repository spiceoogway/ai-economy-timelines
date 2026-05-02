"""Three explicit frontier-model filters.

Phase 1 deliberately uses multiple filters — the choice of "frontier" is not
neutral, and trend estimates can shift materially under different rules.
"""
from __future__ import annotations

import pandas as pd

# Rule C threshold. 1e23 FLOP is the cutoff used in some compute-governance
# frameworks and is a reasonable round number for the post-GPT-3 era. Pre-2020
# models will almost never cross it; that is the point.
RULE_C_FLOP_THRESHOLD = 1e23


def rule_a_top_n_by_compute_at_release(
    df: pd.DataFrame,
    n: int = 10,
    window_years: int = 1,
) -> pd.Series:
    """Frontier Rule A: top N models by training compute within a rolling
    release-time window. The window approximates "at time of release" without
    requiring an exact daily ranking — for each model we ask whether it was
    among the top N highest-compute systems released in the trailing
    `window_years` years.
    """
    flag = pd.Series(False, index=df.index)
    eligible = df.dropna(subset=["training_compute_flop", "release_year_fractional"])
    if eligible.empty:
        return flag
    for idx, row in eligible.iterrows():
        t = row["release_year_fractional"]
        window = eligible[
            (eligible["release_year_fractional"] <= t)
            & (eligible["release_year_fractional"] > t - window_years)
        ]
        top = window.nlargest(n, "training_compute_flop")
        if idx in top.index:
            flag.loc[idx] = True
    return flag


def rule_b_top_per_org_per_year(df: pd.DataFrame) -> pd.Series:
    """Frontier Rule B: the highest-compute model per organization per
    calendar year (only among rows with known compute and known org)."""
    flag = pd.Series(False, index=df.index)
    eligible = df.dropna(
        subset=["training_compute_flop", "organization", "release_year"]
    )
    if eligible.empty:
        return flag
    idx = (
        eligible.groupby(["organization", "release_year"])["training_compute_flop"]
        .idxmax()
        .dropna()
        .astype(int)
        .tolist()
    )
    flag.loc[idx] = True
    return flag


def rule_c_above_threshold(
    df: pd.DataFrame, threshold: float = RULE_C_FLOP_THRESHOLD
) -> pd.Series:
    """Frontier Rule C: models above a fixed compute threshold."""
    return df["training_compute_flop"].fillna(0) >= threshold


def add_frontier_flags(df: pd.DataFrame) -> pd.DataFrame:
    """Add boolean columns frontier_rule_a / _b / _c (and an `any` union).
    Mutates a copy and returns it."""
    out = df.copy()
    out["frontier_rule_a"] = rule_a_top_n_by_compute_at_release(out, n=10)
    out["frontier_rule_b"] = rule_b_top_per_org_per_year(out)
    out["frontier_rule_c"] = rule_c_above_threshold(out)
    out["frontier_any"] = (
        out["frontier_rule_a"] | out["frontier_rule_b"] | out["frontier_rule_c"]
    )
    return out
