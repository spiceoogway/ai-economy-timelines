"""Page 3: Supply Capacity.

Explore the supply pipeline's outputs: usable compute by scenario,
H100-eq stock, capex required, binding constraints.
"""
from __future__ import annotations

import streamlit as st

from app.charts import (
    supply_binding_constraint_heatmap,
    supply_capex_required,
    supply_stock_over_time,
    supply_usable_compute_over_time,
)
from app.data_loader import (
    load_supply_annual,
    load_supply_summary,
    load_table,
)

st.set_page_config(page_title="Supply Capacity", layout="wide")
st.title("Supply Capacity Model")
st.caption("4 supply scenarios × 17 years (2024–2040). Inputs: chips, "
           "power, data centers, capex, utilization.")

annual = load_supply_annual()
summary = load_supply_summary()
capex = load_table("supply_capex_requirements")

# Sidebar: year range slider
st.sidebar.header("Filter")
year_range = st.sidebar.slider(
    "Year range",
    int(annual["year"].min()), int(annual["year"].max()),
    (int(annual["year"].min()), int(annual["year"].max())),
)

annual_view = annual[
    (annual["year"] >= year_range[0]) & (annual["year"] <= year_range[1])
]
capex_view = capex[
    (capex["year"] >= year_range[0]) & (capex["year"] <= year_range[1])
]

# --- Headline charts ----------------------------------------------------

col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(
        supply_usable_compute_over_time(annual_view),
        use_container_width=True,
    )
with col2:
    st.plotly_chart(
        supply_stock_over_time(annual_view),
        use_container_width=True,
    )

col3, col4 = st.columns(2)
with col3:
    st.plotly_chart(
        supply_capex_required(capex_view),
        use_container_width=True,
    )
with col4:
    st.plotly_chart(
        supply_binding_constraint_heatmap(annual_view),
        use_container_width=True,
    )

# --- Tables -------------------------------------------------------------

st.divider()
st.subheader("Supply scenario summary (milestone years)")

st.dataframe(
    summary, hide_index=True, use_container_width=True,
    column_config={
        col: st.column_config.NumberColumn(format="%.2e")
        for col in summary.columns
        if col not in ("scenario", "year", "binding_constraint")
        and summary[col].dtype.kind == "f"
    },
)

with st.expander("Full annual scenario table (4 × 17 = 68 rows)"):
    st.dataframe(annual_view, hide_index=True, use_container_width=True)

with st.expander("Capex required vs available (annual)"):
    st.dataframe(capex_view, hide_index=True, use_container_width=True)

# CSV downloads
st.divider()
col_dl1, col_dl2, col_dl3 = st.columns(3)
with col_dl1:
    st.download_button(
        "Download supply summary CSV",
        summary.to_csv(index=False).encode(),
        file_name="supply_scenario_summary.csv",
    )
with col_dl2:
    st.download_button(
        "Download annual supply CSV",
        annual.to_csv(index=False).encode(),
        file_name="supply_fundamental_inputs_by_year.csv",
    )
with col_dl3:
    st.download_button(
        "Download capex CSV",
        capex.to_csv(index=False).encode(),
        file_name="supply_capex_requirements.csv",
    )
