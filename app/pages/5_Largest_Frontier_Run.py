"""Page 5: Largest Frontier Run.

The headline forward output. 16 lines (one per combined scenario)
with optional historical comparison overlay; 2040 ranking; share
of total compute.
"""
from __future__ import annotations

import streamlit as st

from app.charts import (
    bar_2040_largest_run,
    frontier_run_share_chart,
    largest_run_over_time,
)
from app.data_loader import (
    historical_rule_a_fit,
    load_largest_frontier_run,
)

st.set_page_config(page_title="Largest Frontier Run", layout="wide")
st.title("Largest Frontier Training Run")
st.caption("The headline forward quantity: how big could the single largest "
           "training run get under different supply × allocation choices?")

df = load_largest_frontier_run()

# Sidebar
st.sidebar.header("Display")
show_historical = st.sidebar.checkbox(
    "Overlay historical Rule A 2018+ trend", value=True
)

PRESETS = {
    "Slow / base / fast envelope": [
        "chip_bottleneck × allocation_inference_heavy",
        "base_input_case × allocation_base",
        "capex_rich × allocation_training_race",
    ],
    "All 16 scenarios": list(df["combined_scenario"].unique()),
    "Base supply × all allocations": [
        c for c in df["combined_scenario"].unique() if c.startswith("base_input_case")
    ],
    "All supplies × base allocation": [
        c for c in df["combined_scenario"].unique() if c.endswith("allocation_base")
    ],
}
preset_name = st.sidebar.selectbox("Scenario preset", list(PRESETS.keys()))
selected = st.sidebar.multiselect(
    "Combined scenarios",
    sorted(df["combined_scenario"].unique()),
    default=PRESETS[preset_name],
)

# --- Main chart: largest_run over time, optional historical overlay -----

historical_fit = historical_rule_a_fit() if show_historical else None
fig = largest_run_over_time(df, selected_combined=selected,
                            historical_fit=historical_fit)
st.plotly_chart(fig, use_container_width=True)

# --- 2040 ranking + share chart -----------------------------------------

st.divider()
col1, col2 = st.columns(2)
with col1:
    st.subheader("2040 ranking")
    st.plotly_chart(bar_2040_largest_run(df), use_container_width=True)
with col2:
    st.subheader("Frontier-run share of total compute")
    st.plotly_chart(
        frontier_run_share_chart(df[df["combined_scenario"].isin(selected)]),
        use_container_width=True,
    )

# --- Detail table -------------------------------------------------------

st.divider()
st.subheader("Detail (selected scenarios)")
view = df[df["combined_scenario"].isin(selected)].copy()
view["frontier_run_share_pct"] = view["frontier_run_share_of_total_compute"] * 100
view = view[[
    "year", "combined_scenario", "combined_scenario_id",
    "supply_scenario", "allocation_scenario",
    "largest_frontier_run_flop", "frontier_run_share_pct",
    "training_compute_flop_year", "frontier_lab_training_compute_flop_year",
]]

st.dataframe(
    view, hide_index=True, use_container_width=True,
    column_config={
        "year": st.column_config.NumberColumn("Year", format="%d"),
        "combined_scenario": st.column_config.TextColumn("Combined scenario"),
        "combined_scenario_id": st.column_config.TextColumn("Combined ID"),
        "supply_scenario": st.column_config.TextColumn("Supply"),
        "allocation_scenario": st.column_config.TextColumn("Allocation"),
        "largest_frontier_run_flop": st.column_config.NumberColumn(
            "Largest run (FLOP)", format="%.2e"
        ),
        "frontier_run_share_pct": st.column_config.NumberColumn(
            "% of total", format="%.2f%%"
        ),
        "training_compute_flop_year": st.column_config.NumberColumn(
            "Training pool", format="%.2e"
        ),
        "frontier_lab_training_compute_flop_year": st.column_config.NumberColumn(
            "Frontier-lab training", format="%.2e"
        ),
    },
)

st.download_button(
    "Download largest_frontier_run CSV (full table)",
    df.to_csv(index=False).encode(),
    file_name="allocation_largest_frontier_run.csv",
)
