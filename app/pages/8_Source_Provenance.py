"""Page 8: Source Provenance (optional).

External-reviewer-friendly view of where every input comes from.
"""
from __future__ import annotations

import streamlit as st

from app.data_loader import load_assumptions_long

st.set_page_config(page_title="Source Provenance", layout="wide")
st.title("Source Provenance")
st.caption("Where every input comes from. For a deeper narrative, see "
           "`docs/input_provenance.md`.")

audit = load_assumptions_long()

# Aggregate counts by (component, source_type, confidence)
st.subheader("Source / confidence overview")

col1, col2 = st.columns(2)
with col1:
    by_component = audit.groupby(
        ["component", "confidence"]
    ).size().reset_index(name="count")
    st.markdown("##### Rows by component × confidence")
    st.dataframe(by_component, hide_index=True, use_container_width=True)
with col2:
    by_source = audit.groupby(
        ["source"]
    ).size().reset_index(name="count").sort_values("count", ascending=False)
    st.markdown("##### Rows by source")
    st.dataframe(by_source, hide_index=True, use_container_width=True)

st.divider()
st.subheader("Full provenance")

# Sortable / filterable
st.dataframe(
    audit, hide_index=True, use_container_width=True,
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

st.download_button(
    "Download provenance CSV",
    audit.to_csv(index=False).encode(),
    file_name="source_provenance.csv",
)
