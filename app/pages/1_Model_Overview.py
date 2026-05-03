"""Page 1: Model Overview.

The "what am I looking at?" entry page. Shows status of each
component, headline numbers, the central caution, and the architecture
diagram.
"""
from __future__ import annotations

from pathlib import Path

import streamlit as st

from app.formatting import format_flop, format_pct

st.set_page_config(page_title="Model Overview", layout="wide")
st.title("Model Overview")

st.markdown(
    "AI Economy Timelines is a scenario-based model of frontier AI compute. "
    "Four components are built; one is next; three are deferred."
)

# --- Component status ----------------------------------------------------

st.subheader("Components")

cols = st.columns(4)
component_rows = [
    ("Historical baseline", "BUILT", "uv run historical",
     "Empirical fits on Epoch's 'Notable AI Models' dataset."),
    ("Supply capacity model", "BUILT", "uv run supply",
     "Forward projection 2024–2040: chips, power, capex, utilization."),
    ("Allocation layer", "BUILT", "uv run allocation",
     "Splits compute into 6 buckets; produces largest_frontier_run_flop."),
    ("Review layer", "BUILT", "uv run database / workbook",
     "Generated DuckDB + 11-sheet Excel workbook."),
]
for col, (name, status, cmd, desc) in zip(cols, component_rows):
    with col:
        st.markdown(f"##### {name}")
        st.success(f"✅ {status}")
        st.caption(f"`{cmd}`")
        st.caption(desc)

cols = st.columns(4)
future_rows = [
    ("Effective compute", "NEXT", "—",
     "Adjust raw FLOP for algorithmic-efficiency gains."),
    ("Capability mapping", "FUTURE", "—",
     "Effective FLOP → task horizons / benchmark scores."),
    ("Projection engine", "FUTURE", "—",
     "Probabilistic projections combining all upstream layers."),
    ("Economy feedback", "FUTURE", "—",
     "Revenue → reinvestment → supply-side capex."),
]
for col, (name, status, cmd, desc) in zip(cols, future_rows):
    with col:
        st.markdown(f"##### {name}")
        if status == "NEXT":
            st.warning(f"⏭️ {status}")
        else:
            st.info(f"🔮 {status}")
        st.caption(desc)

# --- Headline numbers ----------------------------------------------------

st.divider()
st.subheader("Headline numbers")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Historical Rule A 2018+ compute growth", "5.97×/yr",
              "doubling every ~4.7 months", delta_color="off")
    st.caption("Phase 1 baseline; descriptive fit, n=113")
with col2:
    st.metric("Base supply CAGR (2024→2040)", "45.7%/yr",
              "1.65e+31 FLOP/yr by 2040", delta_color="off")
    st.caption("Capex binds 2024–2036, then chip")
with col3:
    st.metric("Base allocation largest-run CAGR", "27.6%/yr",
              "6.93e+28 FLOP by 2040", delta_color="off")
    st.caption("Frontier-run share of total falls 3.5% → 0.4%")

st.markdown("##### Slow / base / fast 2040 largest frontier run envelope")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Slow", format_flop(7.84e+27))
    st.caption("chip_bottleneck × inference_heavy")
with col2:
    st.metric("Base", format_flop(6.93e+28))
    st.caption("base × base")
with col3:
    st.metric("Fast", format_flop(9.38e+29))
    st.caption("capex_rich × training_race")

# --- Most important caution ---------------------------------------------

st.divider()
st.subheader("Most important caution")
st.warning(
    "**Total annual usable AI compute is not the same as the largest "
    "frontier training run.** The historical baseline measures one "
    "training run's compute; the supply capacity model measures all "
    "global usable AI compute per year. The allocation layer (Page 5) "
    "bridges them."
)

# --- Architecture diagram -----------------------------------------------

st.divider()
st.subheader("Architecture")

diagram_path = (
    Path(__file__).resolve().parents[2] / "docs" / "assets" / "model_architecture.png"
)
if diagram_path.exists():
    st.image(str(diagram_path), caption="Model architecture (regenerable via "
                                        "`uv run python docs/assets/_generate_architecture.py`)")
else:
    st.info(f"Architecture diagram not found at {diagram_path}")

# --- Where to next? -----------------------------------------------------

st.divider()
st.markdown(
    """
##### Where to next?

- **Page 2: Scenario Matrix** — at-a-glance comparison across all 16 combined scenarios.
- **Page 5: Largest Frontier Run** — the headline forward output.
- **Page 6: Effective-Compute Handoff** — slow / base / fast envelope for the next layer.
"""
)
