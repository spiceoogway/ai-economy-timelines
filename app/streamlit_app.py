"""Landing page for the AI Economy Timelines scenario explorer.

Streamlit auto-discovers the pages under `app/pages/` and renders them
in the sidebar. This file is the welcome / entry page.

Run with:
    uv run demo
"""
from __future__ import annotations

import streamlit as st

from app.data_loader import database_exists, database_manifest, run_manifest

st.set_page_config(
    page_title="AI Economy Timelines",
    page_icon="📊",
    layout="wide",
)

st.title("AI Economy Timelines — Scenario Explorer")
st.markdown(
    "A read-only interactive view of the historical baseline, supply "
    "capacity model, and allocation layer. Source of truth remains the "
    "YAMLs, Python pipelines, CSV outputs, and Markdown findings — this "
    "app reads from the generated DuckDB review database (with CSV fallback)."
)

st.markdown("### How to read this demo")
st.markdown(
    """
1. **Model Overview** — what's built, what's next, headline numbers.
2. **Scenario Matrix** — all 16 combined scenarios sorted by 2040 largest run.
3. **Supply Capacity** — usable compute, capex, and binding constraints by supply scenario.
4. **Allocation Layer** — bucket allocation + training-pool decomposition.
5. **Largest Frontier Run** — the headline output, comparable with the historical trend.
6. **Effective-Compute Handoff** — slow / base / fast envelope for the next layer.
7. **Assumptions** — supply + allocation assumptions with source/confidence flags.
8. **Source Provenance** *(optional)* — flattened audit trail.
9. **Run Manifest** *(optional)* — when each artifact was last regenerated.
"""
)

# Surface the data-source status
st.divider()
st.subheader("Data source")

dbm = database_manifest()
rm = run_manifest()

col1, col2 = st.columns(2)
with col1:
    if database_exists():
        st.success("✅ Reading from DuckDB review database")
        if dbm:
            st.caption(
                f"Schema v{dbm.get('schema_version', '?')} · "
                f"git {dbm.get('git_commit', '?')} · "
                f"{len(dbm.get('tables_created', []))} tables · "
                f"{len(dbm.get('views_created', []))} views"
            )
            st.caption(f"Built: {dbm.get('created_at', 'unknown')}")
    else:
        st.warning(
            "⚠️ DuckDB not found at `outputs/database/ai_economy.duckdb` — "
            "falling back to CSV files under `outputs/tables/`. "
            "Run `uv run database` to build it."
        )

with col2:
    if rm:
        st.info(
            f"**Latest validation run:** {rm.get('run_timestamp', 'unknown')[:19]}\n\n"
            f"git: {rm.get('git_commit', '?')} · "
            f"tests: {'passed ✅' if rm.get('tests_passed') else 'failed ⚠️'} · "
            f"checks: {rm.get('passes', '?')} pass / "
            f"{rm.get('failures', '?')} fail"
        )
    else:
        st.info(
            "No run manifest found at `outputs/runs/latest_run_manifest.json`. "
            "Run `uv run validate-outputs` to produce one."
        )

st.divider()

st.subheader("Most important caution")
st.warning(
    """
**Total annual usable AI compute is not the same as the largest frontier training run.**

The historical baseline measures one training run's compute. The supply
capacity model measures all global usable AI compute per year. Treating
them as comparable forecasts is the most common reading mistake.

The allocation layer (Page 5) bridges them by modeling the share of
total usable compute that goes to the single largest training run.
"""
)

st.divider()

st.subheader("Open the app")
st.markdown(
    """
Navigate through the pages in the sidebar (left). Each page is
independently runnable — you can deep-link into the most relevant page
for your review.

Recommended starting points:
- **Page 5: Largest Frontier Run** — the headline forward output.
- **Page 6: Effective-Compute Handoff** — the slow / base / fast envelope
  for downstream consumers.
- **Page 2: Scenario Matrix** — for at-a-glance comparison across all 16
  combined scenarios.
"""
)
