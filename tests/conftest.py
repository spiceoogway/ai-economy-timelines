"""Shared pytest fixtures."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


@pytest.fixture()
def tmp_assumptions_yaml(tmp_path: Path) -> Path:
    """Minimal but complete assumptions YAML covering one scenario.

    Includes every parameter that project_scenario() pulls so that
    fundamental_inputs tests can run a real projection on synthetic data.
    """
    data = {
        "h100_equivalent_shipments": {
            "unit": "units",
            "scenarios": {
                "tiny": {
                    "source": "synthetic",
                    "confidence": "high",
                    "milestones": [
                        {"year": 2024, "value": 1_000_000},
                        {"year": 2030, "value": 10_000_000},
                    ],
                },
            },
        },
        "accelerator_lifetime_years": {
            "unit": "years",
            "scenarios": {"tiny": {"milestones": [{"year": 2024, "value": 5}]}},
        },
        "peak_flops_per_h100e": {
            "unit": "flops",
            "scenarios": {"tiny": {"milestones": [{"year": 2024, "value": 1e15}]}},
        },
        "power_kw_per_h100e": {
            "unit": "kw",
            "scenarios": {"tiny": {"milestones": [{"year": 2024, "value": 0.7}]}},
        },
        "server_power_overhead": {
            "unit": "multiplier",
            "scenarios": {"tiny": {"milestones": [{"year": 2024, "value": 1.5}]}},
        },
        "pue": {
            "unit": "multiplier",
            "scenarios": {"tiny": {"milestones": [{"year": 2024, "value": 1.2}]}},
        },
        "ai_datacenter_capacity_mw": {
            "unit": "mw",
            "scenarios": {
                "tiny": {
                    "milestones": [
                        {"year": 2024, "value": 10_000},
                        {"year": 2030, "value": 100_000},
                    ]
                }
            },
        },
        "ai_share_of_dc_power": {
            "unit": "fraction",
            "scenarios": {"tiny": {"milestones": [{"year": 2024, "value": 0.85}]}},
        },
        "dc_packing_efficiency": {
            "unit": "fraction",
            "scenarios": {"tiny": {"milestones": [{"year": 2024, "value": 1.0}]}},
        },
        "cluster_utilization": {
            "unit": "fraction",
            "scenarios": {"tiny": {"milestones": [{"year": 2024, "value": 0.4}]}},
        },
        "accelerator_unit_cost_usd": {
            "unit": "usd",
            "scenarios": {"tiny": {"milestones": [{"year": 2024, "value": 30_000}]}},
        },
        "cluster_capex_multiplier": {
            "unit": "multiplier",
            "scenarios": {"tiny": {"milestones": [{"year": 2024, "value": 2.0}]}},
        },
        "ai_infrastructure_capex_usd": {
            "unit": "usd",
            "scenarios": {
                "tiny": {
                    "milestones": [
                        {"year": 2024, "value": 1e11},
                        {"year": 2030, "value": 1e12},
                    ]
                }
            },
        },
        "cloud_rental_usd_per_h100e_year": {
            "unit": "usd",
            "scenarios": {"tiny": {"milestones": [{"year": 2024, "value": 15_000}]}},
        },
        "hardware_perf_index_relative_to_h100": {
            "unit": "multiplier",
            "scenarios": {"tiny": {"milestones": [{"year": 2024, "value": 1.0}]}},
        },
    }
    p = tmp_path / "assumptions.yaml"
    p.write_text(yaml.safe_dump(data, sort_keys=False))
    return p


@pytest.fixture()
def synthetic_log_linear_df() -> pd.DataFrame:
    """A frame the trend-fitting code can consume: log10(y) = slope * year + b
    with slope = log10(6.0) (i.e. 6× per year)."""
    rng = np.random.default_rng(42)
    years = np.arange(2018, 2026)
    slope = np.log10(6.0)
    intercept = -slope * 2024 + 25.0  # 1e25 at 2024
    log_y = slope * years + intercept + rng.normal(0, 1e-6, size=len(years))
    return pd.DataFrame(
        {
            "release_year_fractional": years.astype(float),
            "y": 10**log_y,
        }
    )
