"""Page 9: Run Manifest (optional).

Audit information about the most recent pipeline rebuild — when, what
git commit, which artifacts produced, test pass/fail.
"""
from __future__ import annotations

import json

import streamlit as st

from app.data_loader import database_manifest, run_manifest

st.set_page_config(page_title="Run Manifest", layout="wide")
st.title("Run Manifest")
st.caption("Reproducibility audit: when each artifact was last regenerated.")

# --- Latest validation run ---------------------------------------------

rm = run_manifest()
if rm is not None:
    st.subheader("Latest validation run")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("git commit", rm.get("git_commit", "—"))
        st.metric("Python version", rm.get("python_version", "—"))
    with col2:
        st.metric(
            "Tests passed",
            "✅ yes" if rm.get("tests_passed") else "⚠️ no",
        )
        st.metric("Total checks passed", rm.get("passes", "—"))
    with col3:
        st.metric("Total checks failed", rm.get("failures", "—"))
        st.metric("Run timestamp", rm.get("run_timestamp", "—")[:19])

    st.markdown("**Pipelines run:** " + ", ".join(rm.get("pipelines_run", [])))
    st.markdown(
        f"**Database path:** `{rm.get('database_path', '—')}`  •  "
        f"**Workbook path:** `{rm.get('workbook_path', '—')}`"
    )

    with st.expander("Output tables expected"):
        st.write(rm.get("output_tables", []))
    with st.expander("Output charts expected"):
        st.write(rm.get("output_charts", []))
    with st.expander("Raw manifest JSON"):
        st.json(rm)
else:
    st.info(
        "No run manifest at `outputs/runs/latest_run_manifest.json`. "
        "Run `uv run validate-outputs` to produce one."
    )

# --- Database manifest --------------------------------------------------

st.divider()
dbm = database_manifest()
if dbm is not None:
    st.subheader("Database build manifest")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Schema version", dbm.get("schema_version", "—"))
        st.metric("git commit", dbm.get("git_commit", "—"))
    with col2:
        st.metric("Tables created", len(dbm.get("tables_created", [])))
        st.metric("Views created", len(dbm.get("views_created", [])))
    st.caption(f"Created at: {dbm.get('created_at', '—')}")

    with st.expander("Tables and row counts"):
        rc = dbm.get("row_counts", {})
        st.write({k: f"{v:,} rows" for k, v in rc.items()})

    with st.expander("Raw manifest JSON"):
        st.json(dbm)
else:
    st.info(
        "No database manifest at "
        "`outputs/database/database_manifest.json`. "
        "Run `uv run database` to produce one."
    )
