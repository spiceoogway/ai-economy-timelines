"""Page 4: Allocation Layer.

Show how total usable compute is split into the 6 buckets, with
allocation-scenario sliders for the share trajectories.
"""
from __future__ import annotations

import streamlit as st

from app.charts import bucket_stacked_area, share_over_time
from app.data_loader import load_allocation_buckets

st.set_page_config(page_title="Allocation Layer", layout="wide")
st.title("Allocation Layer")
st.caption("Total usable compute split into 6 buckets, with training-pool "
           "decomposition into the largest single frontier run.")

df = load_allocation_buckets()

# Sidebar: scenario pickers
st.sidebar.header("Scenario")
supply_scens = sorted(df["supply_scenario"].unique())
alloc_scens = sorted(df["allocation_scenario"].unique())

supply_choice = st.sidebar.selectbox(
    "Supply scenario", supply_scens,
    index=supply_scens.index("base_input_case") if "base_input_case" in supply_scens else 0,
)
alloc_choice = st.sidebar.selectbox(
    "Allocation scenario", alloc_scens,
    index=alloc_scens.index("allocation_base") if "allocation_base" in alloc_scens else 0,
)
year_range = st.sidebar.slider(
    "Year range",
    int(df["year"].min()), int(df["year"].max()),
    (int(df["year"].min()), int(df["year"].max())),
)

df_view = df[
    (df["year"] >= year_range[0]) & (df["year"] <= year_range[1])
]

# --- Charts -------------------------------------------------------------

st.subheader(f"Buckets — {supply_choice} × {alloc_choice}")
fig = bucket_stacked_area(df_view, supply_choice, alloc_choice)
st.plotly_chart(fig, use_container_width=True)

st.divider()
st.subheader("Share trajectories")
col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(
        share_over_time(df_view, "training_share", "Training share over time"),
        use_container_width=True,
    )
with col2:
    st.plotly_chart(
        share_over_time(df_view, "inference_share", "Inference share over time"),
        use_container_width=True,
    )

col3, col4 = st.columns(2)
with col3:
    st.plotly_chart(
        share_over_time(
            df_view, "ai_rnd_experiment_share", "AI R&D experiment share"
        ),
        use_container_width=True,
    )
with col4:
    st.plotly_chart(
        share_over_time(
            df_view, "frontier_run_share_of_total_compute",
            "Largest-run share of total compute (log-scale below for detail)",
        ),
        use_container_width=True,
    )

# --- Tables -------------------------------------------------------------

st.divider()
st.subheader(f"Bucket detail — {supply_choice} × {alloc_choice}")

sub = df_view[
    (df_view["supply_scenario"] == supply_choice)
    & (df_view["allocation_scenario"] == alloc_choice)
].copy()

st.dataframe(
    sub, hide_index=True, use_container_width=True,
    column_config={
        col: st.column_config.NumberColumn(format="%.2e")
        for col in sub.columns
        if col.endswith("_compute_flop_year") or col.endswith("_flop")
    } | {
        col: st.column_config.NumberColumn(format="%.1f%%")
        for col in sub.columns
        if col.endswith("_share") or col in (
            "frontier_lab_training_share",
            "largest_run_concentration",
            "cluster_contiguity_factor",
            "frontier_run_share_of_total_compute",
        )
    },
)

# Note: NumberColumn percentage formats need values in [0, 1] for the %
# format to render correctly. Streamlit uses raw values; format="%.1f%%"
# treats values literally so 0.30 displays as "0.3%", which is wrong.
# Working around by pre-multiplying:
sub_display = sub.copy()
for c in sub_display.columns:
    if c.endswith("_share") or c in (
        "frontier_lab_training_share",
        "largest_run_concentration",
        "cluster_contiguity_factor",
        "frontier_run_share_of_total_compute",
    ):
        sub_display[c] = sub_display[c] * 100

# CSV download
st.download_button(
    "Download allocation buckets CSV (full table)",
    df.to_csv(index=False).encode(),
    file_name="allocation_compute_by_bucket.csv",
)
