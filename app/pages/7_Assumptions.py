"""Page 7: Assumptions.

Inspect supply + allocation assumptions without opening YAML.
Filter by component, scenario, confidence.
"""
from __future__ import annotations

import streamlit as st

from app.data_loader import (
    load_allocation_share_assumptions,
    load_assumptions_long,
)

st.set_page_config(page_title="Assumptions", layout="wide")
st.title("Assumptions")
st.caption("Supply + allocation assumptions, source-flagged and "
           "confidence-flagged. Source of truth remains "
           "`data/assumptions/*.yaml`; this page is a read-only view.")

# --- Sources & confidence audit ----------------------------------------

st.subheader("Source / confidence audit")

audit = load_assumptions_long()

# Sidebar filters
st.sidebar.header("Filter")
components = sorted(audit["component"].unique())
component_choice = st.sidebar.multiselect(
    "Component", components, default=components
)
confidences = sorted(c for c in audit["confidence"].dropna().unique())
confidence_choice = st.sidebar.multiselect(
    "Confidence", confidences, default=confidences
)

filtered = audit[
    audit["component"].isin(component_choice)
    & audit["confidence"].isin(confidence_choice)
]

# Render
st.dataframe(
    filtered, hide_index=True, use_container_width=True,
    column_config={
        "input": st.column_config.TextColumn("Parameter"),
        "component": st.column_config.TextColumn("Component"),
        "scenario": st.column_config.TextColumn("Scenario"),
        "source": st.column_config.TextColumn("Source"),
        "source_type": st.column_config.TextColumn("Source type"),
        "confidence": st.column_config.TextColumn("Confidence"),
        "unit": st.column_config.TextColumn("Unit"),
        "used_for": st.column_config.TextColumn("Used for"),
        "notes": st.column_config.TextColumn("Notes"),
    },
)

# --- Allocation share assumptions by year ------------------------------

st.divider()
st.subheader("Allocation shares by year (interpolated)")
st.caption("All 9 allocation parameters per scenario, projected to every "
           "year between milestone anchors via linear interpolation.")

shares = load_allocation_share_assumptions()
share_cols = [c for c in shares.columns if c not in ("allocation_scenario", "year")]
shares_display = shares.copy()
for col in share_cols:
    shares_display[col] = shares_display[col] * 100

st.dataframe(
    shares_display, hide_index=True, use_container_width=True,
    column_config={
        "allocation_scenario": st.column_config.TextColumn("Scenario"),
        "year": st.column_config.NumberColumn("Year", format="%d"),
        **{
            col: st.column_config.NumberColumn(format="%.1f%%")
            for col in share_cols
        },
    },
)

st.download_button(
    "Download share assumptions CSV",
    shares.to_csv(index=False).encode(),
    file_name="allocation_share_assumptions_by_year.csv",
)
