"""Page 2: Scenario Matrix.

All 16 combined scenarios sorted by 2040 largest-run, with milestone
metrics. Sortable / filterable; bar chart of 2040 largest_run; CSV
download button.
"""
from __future__ import annotations

import streamlit as st

from app.charts import bar_2040_largest_run
from app.data_loader import (
    ENVELOPE_LABELS,
    load_largest_frontier_run,
    load_scenario_matrix,
)

st.set_page_config(page_title="Scenario Matrix", layout="wide")
st.title("Scenario Matrix")
st.caption("16 combined scenarios = 4 supply × 4 allocation. "
           "Sortable. Filterable. Slow / base / fast highlighted.")

df = load_scenario_matrix()

# Add envelope tag
df = df.copy()
df["envelope"] = df["combined_scenario_id"].map({
    "chip_bottleneck__inference_heavy": "🔴 slow",
    "base__base": "🟡 base",
    "capex_rich__training_race": "🟢 fast",
}).fillna("")

# Sidebar: filter to slow/base/fast
st.sidebar.header("Filter")
show_envelopes_only = st.sidebar.checkbox(
    "Show only slow / base / fast envelope rows", value=False
)

if show_envelopes_only:
    df_view = df[df["envelope"] != ""]
else:
    df_view = df

# Preferred column order
ordered_cols = [
    "envelope", "combined_scenario_id", "supply_scenario", "allocation_scenario",
    "usable_compute_2030", "usable_compute_2040",
    "largest_run_2030", "largest_run_2040", "largest_run_cagr_2024_2040",
    "frontier_run_share_2030", "frontier_run_share_2040",
]
ordered_cols = [c for c in ordered_cols if c in df_view.columns]
df_view = df_view[ordered_cols]

# Render with column-config formatting
column_config = {
    "envelope": st.column_config.TextColumn("Envelope", width="small"),
    "combined_scenario_id": st.column_config.TextColumn("Combined ID"),
    "supply_scenario": st.column_config.TextColumn("Supply scenario"),
    "allocation_scenario": st.column_config.TextColumn("Allocation scenario"),
    "usable_compute_2030": st.column_config.NumberColumn(
        "Usable 2030", format="%.2e"
    ),
    "usable_compute_2040": st.column_config.NumberColumn(
        "Usable 2040", format="%.2e"
    ),
    "largest_run_2030": st.column_config.NumberColumn(
        "Largest run 2030", format="%.2e"
    ),
    "largest_run_2040": st.column_config.NumberColumn(
        "Largest run 2040", format="%.2e"
    ),
    "largest_run_cagr_2024_2040": st.column_config.NumberColumn(
        "Largest-run CAGR", format="%.1f%%",
    ),
    "frontier_run_share_2030": st.column_config.NumberColumn(
        "Run share 2030", format="%.2f%%",
    ),
    "frontier_run_share_2040": st.column_config.NumberColumn(
        "Run share 2040", format="%.2f%%",
    ),
}

# Streamlit's NumberColumn doesn't auto-multiply by 100 for %, scale them up
df_display = df_view.copy()
for c in ["largest_run_cagr_2024_2040",
          "frontier_run_share_2030", "frontier_run_share_2040"]:
    if c in df_display.columns:
        df_display[c] = df_display[c] * 100

st.dataframe(df_display, hide_index=True, use_container_width=True,
             column_config=column_config)

# CSV download
csv_bytes = df_view.to_csv(index=False).encode()
st.download_button(
    "Download Scenario Matrix CSV",
    csv_bytes,
    file_name="scenario_matrix.csv",
    mime="text/csv",
)

st.divider()

# Bar chart of 2040 largest run by combined scenario
st.subheader("2040 largest frontier run by combined scenario")
runs = load_largest_frontier_run()
fig = bar_2040_largest_run(runs)
st.plotly_chart(fig, use_container_width=True)
