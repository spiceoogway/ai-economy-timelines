"""Page 6: Effective-Compute Handoff.

The cleanest read of the slow / base / fast envelope, designed for
the next modeling layer. Hard-codes the three envelope scenarios per
the upstream scope.
"""
from __future__ import annotations

import streamlit as st

from app.charts import bucket_handoff_chart, envelope_chart
from app.data_loader import load_phase4_handoff
from app.formatting import format_flop

st.set_page_config(page_title="Effective-Compute Handoff", layout="wide")
st.title("Effective-Compute Handoff")
st.caption("Slow / base / fast largest-frontier-run envelope, plus base-case "
           "bucket totals. This is the canonical input table for the next "
           "(effective-compute) layer.")

df = load_phase4_handoff()

# --- Quick-glance milestone cards ---------------------------------------

st.subheader("Milestone year envelope")
for year_label, year in [("2024", 2024), ("2030", 2030), ("2040", 2040)]:
    if year not in df["year"].values:
        continue
    row = df[df["year"] == year].iloc[0]
    st.markdown(f"###### {year_label}")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            "Slow",
            format_flop(row.get("slow_largest_frontier_run_flop")),
        )
        st.caption("chip_bottleneck × inference_heavy")
    with col2:
        st.metric(
            "Base",
            format_flop(row.get("base_largest_frontier_run_flop")),
        )
        st.caption("base × base")
    with col3:
        st.metric(
            "Fast",
            format_flop(row.get("fast_largest_frontier_run_flop")),
        )
        st.caption("capex_rich × training_race")

# --- Charts -------------------------------------------------------------

st.divider()
st.subheader("Envelope over time")
st.plotly_chart(envelope_chart(df), use_container_width=True)

st.subheader("Base-case bucket totals over time")
st.plotly_chart(bucket_handoff_chart(df), use_container_width=True)

# --- Table --------------------------------------------------------------

st.divider()
st.subheader("Handoff table")
st.caption("Wide format. Slow / base / fast `largest_frontier_run_flop` "
           "side-by-side; base-case bucket totals on the right.")

st.dataframe(
    df, hide_index=True, use_container_width=True,
    column_config={
        "year": st.column_config.NumberColumn("Year", format="%d"),
        **{
            col: st.column_config.NumberColumn(format="%.2e")
            for col in df.columns
            if col != "year"
        },
    },
)

# --- Downloads ----------------------------------------------------------

st.divider()
col1, col2 = st.columns(2)
with col1:
    st.download_button(
        "Download Effective-Compute Handoff CSV",
        df.to_csv(index=False).encode(),
        file_name="effective_compute_handoff.csv",
        type="primary",
    )
with col2:
    from app.data_loader import load_largest_frontier_run
    full = load_largest_frontier_run()
    st.download_button(
        "Download full scenario CSV (all 16)",
        full.to_csv(index=False).encode(),
        file_name="allocation_largest_frontier_run.csv",
    )
