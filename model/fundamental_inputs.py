"""Phase 2 fundamental-input compute capacity model.

Pipeline (per docs/phase2_scope.md §4):

    accelerator_shipments_t
        ↓ (with retirement)
    installed_accelerator_stock_t  (in H100-equivalent units)
        ↓ × peak_flops × seconds/year
    theoretical_compute_capacity_t
        ↓ ∩ power constraint
    power_limited_compute_capacity_t
        ↓ ∩ data-center constraint
    datacenter_limited_compute_capacity_t
        ↓ ∩ capex constraint
    capex_limited_compute_capacity_t
        ↓ × utilization
    usable_compute_capacity_t

The four limits (chip / power / dc / capex) are computed independently in
H100-equivalent units, then we take the minimum and record the binding
constraint per year.

Sprint 1: round-number placeholder assumptions live in
data/assumptions/phase2_input_assumptions.csv (long format, scenario-keyed,
linearly interpolated between milestone years). All numbers flagged
confidence=low source=placeholder until sprint 2 replaces them with cited
figures.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
import yaml

from model.runtime import (
    ASSUMPTIONS_YAML as ASSUMPTIONS_PATH,
    REPO_ROOT,
    SCENARIOS_DIR,
)

SECONDS_PER_YEAR = 365.25 * 24 * 3600

# Constraints we identify as candidate binding constraints. Order is the
# canonical reporting order; ties are broken by this order.
CONSTRAINTS = ("chip", "power", "datacenter", "capex")


@dataclass
class ScenarioConfig:
    name: str
    display_name: str
    description: str
    assumption_scenario: str
    start_year: int
    end_year: int

    @classmethod
    def from_yaml(cls, path: Path) -> "ScenarioConfig":
        d = yaml.safe_load(path.read_text())
        return cls(
            name=d["name"],
            display_name=d.get("display_name", d["name"]),
            description=d.get("description", "").strip(),
            assumption_scenario=d["assumption_scenario"],
            start_year=int(d["start_year"]),
            end_year=int(d["end_year"]),
        )


def load_assumptions(path: Path = ASSUMPTIONS_PATH) -> pd.DataFrame:
    """Load the assumptions table as a long-format DataFrame.

    Supports both YAML (canonical, nested by parameter) and the legacy CSV
    format. Returns columns: parameter, scenario, year, value, unit,
    source, confidence, notes.
    """
    if path.suffix in (".yaml", ".yml"):
        return _load_assumptions_yaml(path)
    return _load_assumptions_csv(path)


def _load_assumptions_yaml(path: Path) -> pd.DataFrame:
    raw = yaml.safe_load(path.read_text())
    if not isinstance(raw, dict):
        raise ValueError(f"{path}: top-level must be a mapping of parameter → block")
    rows = []
    for param, pblock in raw.items():
        if not isinstance(pblock, dict) or "scenarios" not in pblock:
            raise ValueError(
                f"{path}: parameter {param!r} must be a mapping with a 'scenarios' key"
            )
        unit = pblock.get("unit")
        for scenario, sblock in pblock["scenarios"].items():
            milestones = sblock.get("milestones") or []
            if not milestones:
                raise ValueError(
                    f"{path}: {param}/{scenario} has no milestones"
                )
            default_src = sblock.get("source")
            default_conf = sblock.get("confidence")
            for m in milestones:
                if "year" not in m or "value" not in m:
                    raise ValueError(
                        f"{path}: {param}/{scenario} milestone missing year/value: {m!r}"
                    )
                rows.append(
                    {
                        "parameter": param,
                        "scenario": scenario,
                        "year": int(m["year"]),
                        "value": float(m["value"]),
                        "unit": unit,
                        "source": m.get("source", default_src),
                        "confidence": m.get("confidence", default_conf),
                        "notes": m.get("notes", ""),
                    }
                )
    return pd.DataFrame(rows)


def _load_assumptions_csv(path: Path) -> pd.DataFrame:
    """Legacy CSV reader (kept for one cycle to support migration tests)."""
    df = pd.read_csv(path, comment="#")
    df.columns = [c.strip() for c in df.columns]
    df["parameter"] = df["parameter"].str.strip()
    df["scenario"] = df["scenario"].str.strip()
    df["year"] = df["year"].astype(int)
    df["value"] = df["value"].astype(float)
    return df


def _interp_series(
    df: pd.DataFrame,
    parameter: str,
    scenario: str,
    years: Iterable[int],
    *,
    log: bool = False,
) -> pd.Series:
    """Pull the (year, value) milestones for one parameter in one scenario,
    then interpolate (optionally in log space) to a target year range.

    If only one milestone year is provided, the value is held constant
    across all years.
    """
    sub = df[(df["parameter"] == parameter) & (df["scenario"] == scenario)]
    sub = sub.sort_values("year")
    if sub.empty:
        raise KeyError(f"No assumption row for {parameter}/{scenario}")
    xs = sub["year"].to_numpy()
    ys = sub["value"].to_numpy()
    target = np.array(list(years))
    if len(xs) == 1:
        return pd.Series(np.repeat(ys[0], len(target)), index=target, name=parameter)
    if log:
        ys = np.log(ys)
    out = np.interp(target, xs, ys, left=ys[0], right=ys[-1])
    if log:
        out = np.exp(out)
    return pd.Series(out, index=target, name=parameter)


def _series_for(
    df: pd.DataFrame, scenario: str, years: list[int], parameter: str, *, log: bool
) -> pd.Series:
    return _interp_series(df, parameter, scenario, years, log=log)


def project_accelerator_stock(
    shipments: pd.Series, lifetime_years: float
) -> pd.Series:
    """Linear retirement: a chip shipped in year y is in the stock for
    `lifetime_years` years and retires linearly. For sprint 1 we use a
    sharp cutoff (chips shipped in year y are retired at end of year y+L)
    rather than a continuous decay — simpler and within placeholder noise."""
    years = shipments.index
    stock = pd.Series(0.0, index=years)
    L = int(round(lifetime_years))
    for y in years:
        # Sum shipments from years (y - L + 1) ... y, clamped to start.
        contributing = shipments.loc[max(years.min(), y - L + 1) : y]
        stock.loc[y] = contributing.sum()
    return stock


def power_limited_h100e_stock(
    ai_dc_mw: pd.Series,
    ai_share: pd.Series,
    chip_kw: pd.Series,
    server_overhead: pd.Series,
    pue: pd.Series,
) -> pd.Series:
    """How many H100-eq chips can be powered by available AI-DC MW?

        usable_ai_mw = ai_dc_mw * ai_share
        effective_kw_per_chip = chip_kw * server_overhead * pue
        n_chips = usable_ai_mw * 1000 / effective_kw_per_chip
    """
    usable_ai_kw = ai_dc_mw * ai_share * 1000.0
    eff_kw = chip_kw * server_overhead * pue
    return (usable_ai_kw / eff_kw).rename("power_limited_h100e_stock")


def datacenter_limited_h100e_stock(
    ai_dc_mw: pd.Series,
    chip_kw: pd.Series,
    server_overhead: pd.Series,
    pue: pd.Series,
    dc_packing_efficiency: pd.Series,
) -> pd.Series:
    """DC constraint on chip count from physical buildout, separate from the
    grid-power constraint. `dc_packing_efficiency` ∈ [0, 1] captures
    cooling, slot density, transformer slack, and permitting drag — i.e.
    the fraction of DC-MW that can actually be populated with frontier-
    AI accelerators. 1.0 = no constraint above grid; 0.7 = cooling and
    cabling bind 30% earlier."""
    eff_kw = chip_kw * server_overhead * pue
    return (ai_dc_mw * dc_packing_efficiency * 1000.0 / eff_kw).rename(
        "datacenter_limited_h100e_stock"
    )


def capex_limited_h100e_stock(
    capex_usd: pd.Series, chip_cost: pd.Series, cluster_multiplier: pd.Series
) -> pd.Series:
    """Cumulative capex / installed-cost-per-H100e gives the H100-eq stock
    that the cumulative capex flow can support if all of it goes to chips
    and clusters. Per-year capex flow accumulates over the projection
    window — we treat capex_usd as annual investment, summed cumulatively."""
    annual_chips_affordable = capex_usd / (chip_cost * cluster_multiplier)
    return annual_chips_affordable.cumsum().rename("capex_limited_h100e_stock")


def project_scenario(
    scenario: ScenarioConfig,
    assumptions: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Run the full Phase 2 input model for one scenario. Returns a
    dataframe indexed by year with all intermediate and final quantities."""
    if assumptions is None:
        assumptions = load_assumptions()
    s = scenario.assumption_scenario
    years = list(range(scenario.start_year, scenario.end_year + 1))

    shipments = _series_for(assumptions, s, years, "h100_equivalent_shipments", log=True)
    lifetime = _series_for(assumptions, s, years, "accelerator_lifetime_years", log=False)
    peak_flops = _series_for(assumptions, s, years, "peak_flops_per_h100e", log=False)
    chip_kw = _series_for(assumptions, s, years, "power_kw_per_h100e", log=False)
    server_oh = _series_for(assumptions, s, years, "server_power_overhead", log=False)
    pue = _series_for(assumptions, s, years, "pue", log=False)
    ai_dc_mw = _series_for(assumptions, s, years, "ai_datacenter_capacity_mw", log=True)
    ai_share = _series_for(assumptions, s, years, "ai_share_of_dc_power", log=False)
    dc_packing = _series_for(assumptions, s, years, "dc_packing_efficiency", log=False)
    util = _series_for(assumptions, s, years, "cluster_utilization", log=False)
    chip_cost = _series_for(assumptions, s, years, "accelerator_unit_cost_usd", log=True)
    cluster_mult = _series_for(assumptions, s, years, "cluster_capex_multiplier", log=False)
    capex = _series_for(assumptions, s, years, "ai_infrastructure_capex_usd", log=True)
    cloud_year = _series_for(
        assumptions, s, years, "cloud_rental_usd_per_h100e_year", log=True
    )
    perf_index = _series_for(
        assumptions, s, years, "hardware_perf_index_relative_to_h100", log=False
    )

    # Chip-limited stock comes straight from shipments + retirement.
    chip_stock = project_accelerator_stock(shipments, lifetime.iloc[0])

    # Power and DC limits: how many H100e can be installed under AI-MW.
    power_stock = power_limited_h100e_stock(ai_dc_mw, ai_share, chip_kw, server_oh, pue)
    dc_stock = datacenter_limited_h100e_stock(
        ai_dc_mw, chip_kw, server_oh, pue, dc_packing
    )

    # Capex limit: cumulative.
    capex_stock = capex_limited_h100e_stock(capex, chip_cost, cluster_mult)

    # Take the binding minimum.
    limits = pd.DataFrame(
        {
            "chip": chip_stock,
            "power": power_stock,
            "datacenter": dc_stock,
            "capex": capex_stock,
        },
        index=years,
    )
    binding_idx = limits.idxmin(axis=1)
    available_h100e = limits.min(axis=1)

    theoretical_flop_per_year = chip_stock * peak_flops * SECONDS_PER_YEAR
    available_flop_per_year_pre_util = available_h100e * peak_flops * SECONDS_PER_YEAR
    usable_flop_per_year = available_flop_per_year_pre_util * util

    out = pd.DataFrame(
        {
            "year": years,
            "scenario": scenario.name,
            "accelerator_shipments_h100e": shipments.values,
            "installed_stock_h100e_chip_limited": chip_stock.values,
            "power_limited_stock_h100e": power_stock.values,
            "datacenter_limited_stock_h100e": dc_stock.values,
            "capex_limited_stock_h100e": capex_stock.values,
            "available_stock_h100e": available_h100e.values,
            "binding_constraint": binding_idx.values,
            "peak_flops_per_h100e": peak_flops.values,
            "theoretical_compute_flop_year": theoretical_flop_per_year.values,
            "available_compute_flop_year_pre_util": available_flop_per_year_pre_util.values,
            "utilization_rate": util.values,
            "usable_compute_flop_year": usable_flop_per_year.values,
            "ai_power_capacity_mw": ai_dc_mw.values,
            "datacenter_capacity_mw": ai_dc_mw.values,
            "dc_packing_efficiency": dc_packing.values,
            "ai_infrastructure_capex_usd": capex.values,
            "accelerator_unit_cost_usd": chip_cost.values,
            "cluster_capex_multiplier": cluster_mult.values,
            "hardware_perf_index_relative_to_h100": perf_index.values,
            # Three Phase 1 cost variants — preserved per phase1_findings.md
            # because the divergence is the single largest cost uncertainty.
            "cost_per_h100e_year_upfront": (
                chip_cost * cluster_mult / lifetime
            ).values,
            "cost_per_h100e_year_cloud": cloud_year.values,
            "cost_per_h100e_year_blended": (
                0.5 * chip_cost * cluster_mult / lifetime + 0.5 * cloud_year
            ).values,
        }
    )
    return out


def sensitivity_analysis(
    base_scenario: ScenarioConfig,
    assumptions: pd.DataFrame,
    *,
    parameter: str,
    multipliers: list[float],
) -> pd.DataFrame:
    """Vary a single parameter (multiplied by each value in `multipliers`)
    while holding everything else at the base scenario, returning one
    annual frame per multiplier with a `sensitivity_multiplier` column.

    For multi-year parameters, the multiplier is applied to every year.
    """
    rows = []
    for m in multipliers:
        a = assumptions.copy()
        mask = a["parameter"] == parameter
        if not mask.any():
            raise KeyError(f"parameter {parameter!r} not in assumptions table")
        # Only modify rows for the base scenario.
        scen_mask = mask & (a["scenario"] == base_scenario.assumption_scenario)
        a.loc[scen_mask, "value"] = a.loc[scen_mask, "value"] * m
        df = project_scenario(base_scenario, a)
        df["sensitivity_parameter"] = parameter
        df["sensitivity_multiplier"] = m
        rows.append(df)
    return pd.concat(rows, ignore_index=True)


def load_all_scenarios() -> list[ScenarioConfig]:
    paths = sorted(SCENARIOS_DIR.glob("phase2_*.yaml"))
    return [ScenarioConfig.from_yaml(p) for p in paths]


def project_all_scenarios() -> pd.DataFrame:
    """Project every scenario YAML in scenarios/ and concatenate."""
    assumptions = load_assumptions()
    frames = [project_scenario(s, assumptions) for s in load_all_scenarios()]
    return pd.concat(frames, ignore_index=True)
