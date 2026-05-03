"""Tests for log-linear trend fitting."""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

from model.trend_fitting import fit_log_linear


def test_recovers_known_slope(synthetic_log_linear_df: pd.DataFrame) -> None:
    fit = fit_log_linear(
        synthetic_log_linear_df,
        "y",
        trend_name="synthetic",
        frontier_rule="all",
        year_col="release_year_fractional",
    )
    assert fit is not None
    assert math.isclose(fit.slope_log10_per_year, math.log10(6.0), abs_tol=1e-3)
    assert math.isclose(fit.annual_growth_multiplier, 6.0, rel_tol=1e-3)
    assert fit.r_squared > 0.999  # nearly noise-free
    assert fit.n_models == len(synthetic_log_linear_df)


def test_handles_insufficient_data() -> None:
    df = pd.DataFrame({"release_year_fractional": [2024.0], "y": [1e25]})
    fit = fit_log_linear(
        df,
        "y",
        trend_name="too_small",
        frontier_rule="all",
        year_col="release_year_fractional",
    )
    assert fit is None
