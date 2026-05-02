"""Log-linear trend fitting for frontier compute / cost curves.

Fits log10(y) = a + b * year and returns slope, annual-multiplier, doubling-
time, R^2, standard error, n, and the year range used.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import log

import numpy as np
import pandas as pd
import statsmodels.api as sm


@dataclass
class TrendFit:
    trend_name: str
    frontier_rule: str
    n_models: int
    start_year: int | None
    end_year: int | None
    slope_log10_per_year: float
    intercept_log10: float
    annual_growth_multiplier: float
    doubling_time_years: float
    r_squared: float
    standard_error: float
    notes: str = ""

    def to_row(self) -> dict:
        return {
            "trend_name": self.trend_name,
            "frontier_rule": self.frontier_rule,
            "start_year": self.start_year,
            "end_year": self.end_year,
            "n_models": self.n_models,
            "slope_log10_per_year": self.slope_log10_per_year,
            "annual_growth_multiplier": self.annual_growth_multiplier,
            "doubling_time_years": self.doubling_time_years,
            "r_squared": self.r_squared,
            "standard_error": self.standard_error,
            "notes": self.notes,
        }


def fit_log_linear(
    df: pd.DataFrame,
    y_col: str,
    *,
    trend_name: str,
    frontier_rule: str,
    year_col: str = "release_year_fractional",
    log_already: bool = False,
    notes: str = "",
) -> TrendFit | None:
    """Fit log10(y) ~ year on the rows where both columns are present and
    finite. Returns None if fewer than 3 usable rows."""
    sub = df[[year_col, y_col]].copy()
    if not log_already:
        sub[y_col] = np.log10(sub[y_col].replace({0: np.nan}))
    sub = sub.replace([np.inf, -np.inf], np.nan).dropna()
    if len(sub) < 3:
        return None
    X = sm.add_constant(sub[year_col].values)
    y = sub[y_col].values
    res = sm.OLS(y, X).fit()
    slope = float(res.params[1])
    intercept = float(res.params[0])
    se = float(res.bse[1])
    multiplier = 10**slope
    doubling = log(2) / log(multiplier) if multiplier > 1 else float("nan")
    return TrendFit(
        trend_name=trend_name,
        frontier_rule=frontier_rule,
        n_models=int(len(sub)),
        start_year=int(np.floor(sub[year_col].min())),
        end_year=int(np.floor(sub[year_col].max())),
        slope_log10_per_year=slope,
        intercept_log10=intercept,
        annual_growth_multiplier=multiplier,
        doubling_time_years=doubling,
        r_squared=float(res.rsquared),
        standard_error=se,
        notes=notes,
    )


def fits_to_frame(fits: list[TrendFit]) -> pd.DataFrame:
    return pd.DataFrame([f.to_row() for f in fits if f is not None])
