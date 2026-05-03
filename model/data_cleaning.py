"""Load and normalize Epoch's Notable AI Models CSV into the Phase 1 schema."""
from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd

from model.runtime import RAW_NOTABLE_AI_MODELS as RAW_NOTABLE, REPO_ROOT

# Map Epoch column names → Phase 1 schema names.
COLUMN_MAP = {
    "Model": "model_name",
    "Organization": "organization",
    "Publication date": "publication_date_raw",
    "Domain": "domain",
    "Parameters": "parameters",
    "Training compute (FLOP)": "training_compute_flop",
    "Training compute notes": "training_compute_notes",
    "Training dataset size (total)": "dataset_tokens",
    "Confidence": "epoch_confidence",
    "Training time (hours)": "training_time_hours",
    "Training hardware": "hardware_type",
    "Hardware quantity": "hardware_quantity",
    "Training compute cost (2023 USD)": "estimated_training_cost_usd",
    "Compute cost notes": "cost_notes",
    "Frontier model": "epoch_frontier_flag",
    "Training compute cost (cloud)": "training_cost_cloud_usd",
    "Training compute cost (upfront)": "training_cost_upfront_usd",
    "Notability criteria": "notability_criteria",
    "Country (of organization)": "country",
    "Organization categorization": "organization_category",
    "Link": "source_url",
    "Reference": "reference",
}


def _normalize_org(name: str | float) -> str | float:
    """Light-touch organization normalization: trim whitespace, canonicalize a
    handful of well-known variants. We deliberately do NOT collapse parent/sub
    relationships (e.g. DeepMind vs Google DeepMind) because Epoch's labels
    track the organization at publication time."""
    if not isinstance(name, str):
        return name
    s = name.strip()
    fixes = {
        "Google Deepmind": "Google DeepMind",
        "OpenAi": "OpenAI",
        "Meta AI": "Meta",
        "Meta Platforms": "Meta",
    }
    return fixes.get(s, s)


def load_raw(path: Path = RAW_NOTABLE) -> pd.DataFrame:
    """Read the raw Epoch CSV, apply column rename + light normalization."""
    df = pd.read_csv(path)
    df = df.rename(columns=COLUMN_MAP)

    df["organization"] = df["organization"].map(_normalize_org)

    df["publication_date"] = pd.to_datetime(
        df["publication_date_raw"], errors="coerce"
    )
    df["release_year"] = df["publication_date"].dt.year
    df["release_year_fractional"] = (
        df["publication_date"].dt.year
        + (df["publication_date"].dt.dayofyear - 1) / 365.25
    )

    for c in [
        "training_compute_flop",
        "estimated_training_cost_usd",
        "training_cost_cloud_usd",
        "training_cost_upfront_usd",
        "parameters",
        "dataset_tokens",
        "training_time_hours",
        "hardware_quantity",
    ]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    # Epoch frontier flag: True / NaN. Convert to bool with False default.
    df["epoch_frontier_flag"] = df["epoch_frontier_flag"].fillna(False).astype(bool)

    df["training_compute_log10"] = np.log10(df["training_compute_flop"])
    df["training_cost_log10"] = np.log10(df["estimated_training_cost_usd"])
    df["cost_per_flop"] = (
        df["estimated_training_cost_usd"] / df["training_compute_flop"]
    )
    df["cost_per_flop_log10"] = np.log10(df["cost_per_flop"])

    df["training_duration_days"] = df["training_time_hours"] / 24.0

    df["model_id"] = (
        df["model_name"].astype(str).str.strip()
        + " | "
        + df["organization"].astype(str).str.strip()
        + " | "
        + df["publication_date"].dt.strftime("%Y-%m-%d").fillna("unknown")
    )

    df["compute_estimate_quality"] = df["epoch_confidence"].map(
        {
            "Confident": "high",
            "Likely": "medium",
            "Speculative": "low",
            "Unknown": "low",
        }
    )
    # If we have no compute number at all the quality flag is meaningless.
    df.loc[df["training_compute_flop"].isna(), "compute_estimate_quality"] = pd.NA

    # Cost quality: high if the upfront-USD field is filled, else medium if
    # only the cloud-equivalent figure exists, else low.
    cost_quality = pd.Series(pd.NA, index=df.index, dtype="object")
    cost_quality[df["training_cost_upfront_usd"].notna()] = "high"
    cost_quality[
        df["training_cost_upfront_usd"].isna() & df["training_cost_cloud_usd"].notna()
    ] = "medium"
    cost_quality[
        df["estimated_training_cost_usd"].notna()
        & df["training_cost_upfront_usd"].isna()
        & df["training_cost_cloud_usd"].isna()
    ] = "low"
    df["cost_estimate_quality"] = cost_quality

    df["date_quality"] = np.where(
        df["publication_date"].notna(), "publication_date", "unclear"
    )

    return df


PROCESSED_COLUMNS = [
    "model_id",
    "model_name",
    "organization",
    "release_year",
    "release_year_fractional",
    "publication_date",
    "domain",
    "training_compute_flop",
    "training_compute_log10",
    "estimated_training_cost_usd",
    "training_cost_log10",
    "training_cost_cloud_usd",
    "training_cost_upfront_usd",
    "cost_per_flop",
    "cost_per_flop_log10",
    "parameters",
    "dataset_tokens",
    "hardware_type",
    "hardware_quantity",
    "training_duration_days",
    "epoch_frontier_flag",
    "epoch_confidence",
    "compute_estimate_quality",
    "cost_estimate_quality",
    "date_quality",
    "notability_criteria",
    "organization_category",
    "country",
    "source_url",
    "training_compute_notes",
    "cost_notes",
]


def select_processed(df: pd.DataFrame) -> pd.DataFrame:
    cols = [c for c in PROCESSED_COLUMNS if c in df.columns]
    return df[cols].copy()
