"""Plotly chart helpers for the Streamlit demo.

Plotly for time-series and bar charts (interactive hover/zoom).
Streamlit native `st.dataframe` for tables (faster, sortable,
downloadable).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Color palettes — match the static charts where they overlap
SUPPLY_COLORS = {
    "base_input_case": "#1f77b4",
    "capex_rich": "#2ca02c",
    "chip_bottleneck": "#d62728",
    "power_datacenter_bottleneck": "#ff7f0e",
}
ALLOCATION_COLORS = {
    "allocation_base": "#1f77b4",
    "allocation_inference_heavy": "#9467bd",
    "allocation_training_race": "#d62728",
    "allocation_rnd_acceleration": "#bcbd22",
}
ENVELOPE_COLORS = {
    "slow": "#d62728",
    "base": "#ff7f0e",
    "fast": "#2ca02c",
}
BUCKET_COLORS = {
    "inference": "#1f77b4",
    "training": "#d62728",
    "ai_rnd_experiment": "#2ca02c",
    "post_training": "#ff7f0e",
    "safety_eval": "#9467bd",
    "reserved_idle_fragmented": "#888888",
}


def _log_y(fig: go.Figure, title: str | None = None) -> go.Figure:
    fig.update_yaxes(type="log")
    if title:
        fig.update_layout(title=title)
    fig.update_layout(legend_title_text="", margin=dict(l=20, r=20, t=50, b=40))
    return fig


# --- supply charts ------------------------------------------------------


def supply_usable_compute_over_time(df: pd.DataFrame) -> go.Figure:
    fig = px.line(
        df, x="year", y="usable_compute_flop_year",
        color="scenario", markers=True,
        color_discrete_map=SUPPLY_COLORS,
        labels={"usable_compute_flop_year": "Usable compute (FLOP/year)",
                "year": "Year"},
    )
    return _log_y(fig, "Usable AI compute capacity by supply scenario")


def supply_stock_over_time(df: pd.DataFrame) -> go.Figure:
    fig = px.line(
        df, x="year", y="available_stock_h100e",
        color="scenario", markers=True,
        color_discrete_map=SUPPLY_COLORS,
        labels={"available_stock_h100e": "Installed stock (H100-eq)",
                "year": "Year"},
    )
    return _log_y(fig, "Installed H100-equivalent stock by supply scenario")


def supply_capex_required(capex_df: pd.DataFrame) -> go.Figure:
    fig = px.line(
        capex_df, x="year", y="capex_required_usd",
        color="scenario", markers=True,
        color_discrete_map=SUPPLY_COLORS,
        labels={"capex_required_usd": "Capex required (USD/year)",
                "year": "Year"},
    )
    return _log_y(fig, "Capex required by supply scenario")


def supply_binding_constraint_heatmap(df: pd.DataFrame) -> go.Figure:
    """Pivot binding_constraint by (scenario, year) → categorical heatmap."""
    constraint_to_int = {"chip": 0, "power": 1, "datacenter": 2, "capex": 3}
    pivot = df.pivot(index="scenario", columns="year", values="binding_constraint")
    z = pivot.replace(constraint_to_int).values
    fig = go.Figure(
        data=go.Heatmap(
            z=z,
            x=pivot.columns,
            y=pivot.index,
            colorscale=[
                [0.0, "#d62728"],   # chip
                [0.33, "#ff7f0e"],  # power
                [0.67, "#9467bd"],  # datacenter
                [1.0, "#2ca02c"],   # capex
            ],
            showscale=False,
        )
    )
    fig.update_layout(
        title="Binding constraint by year and supply scenario",
        margin=dict(l=20, r=20, t=50, b=40),
    )
    return fig


# --- allocation charts --------------------------------------------------


def bucket_stacked_area(df: pd.DataFrame, supply_scen: str, alloc_scen: str) -> go.Figure:
    """Stacked area chart of compute by bucket for one (supply, alloc) combo."""
    sub = df[
        (df["supply_scenario"] == supply_scen)
        & (df["allocation_scenario"] == alloc_scen)
    ].sort_values("year")
    fig = go.Figure()
    bucket_keys = [
        ("inference", "inference_compute_flop_year"),
        ("training", "training_compute_flop_year"),
        ("ai_rnd_experiment", "ai_rnd_experiment_compute_flop_year"),
        ("post_training", "post_training_compute_flop_year"),
        ("safety_eval", "safety_eval_compute_flop_year"),
        ("reserved_idle_fragmented", "reserved_idle_fragmented_compute_flop_year"),
    ]
    for name, col in bucket_keys:
        fig.add_trace(go.Scatter(
            x=sub["year"], y=sub[col],
            mode="lines",
            line=dict(width=0.5, color=BUCKET_COLORS[name]),
            stackgroup="one",
            name=name.replace("_", " ").title(),
        ))
    fig.update_yaxes(type="log")
    fig.update_layout(
        title=f"Allocation buckets — {supply_scen} × {alloc_scen}",
        margin=dict(l=20, r=20, t=50, b=40),
        legend_title_text="",
    )
    return fig


def share_over_time(df: pd.DataFrame, share_col: str, title: str) -> go.Figure:
    """One line per allocation scenario, share on linear axis 0–1."""
    sub = df.drop_duplicates(subset=["allocation_scenario", "year"]).sort_values(
        ["allocation_scenario", "year"]
    )
    fig = px.line(
        sub, x="year", y=share_col,
        color="allocation_scenario", markers=True,
        color_discrete_map=ALLOCATION_COLORS,
        labels={share_col: "Share", "year": "Year"},
    )
    fig.update_yaxes(range=[0, 1], tickformat=".0%")
    fig.update_layout(
        title=title,
        margin=dict(l=20, r=20, t=50, b=40),
        legend_title_text="",
    )
    return fig


# --- largest-frontier-run charts ----------------------------------------


def largest_run_over_time(
    df: pd.DataFrame,
    selected_combined: list[str] | None = None,
    historical_fit: tuple[float, float, float] | None = None,
) -> go.Figure:
    """One line per combined scenario; optional historical extrapolation."""
    if selected_combined is None:
        plot = df
    else:
        plot = df[df["combined_scenario"].isin(selected_combined)]
    fig = px.line(
        plot.sort_values("year"),
        x="year", y="largest_frontier_run_flop",
        color="combined_scenario", markers=True,
        labels={"largest_frontier_run_flop": "Largest frontier run (FLOP)",
                "year": "Year"},
    )
    if historical_fit is not None:
        slope, intercept, mult = historical_fit
        years = np.linspace(2018, 2040, 200)
        flop = 10 ** (intercept + slope * years)
        fig.add_trace(go.Scatter(
            x=years, y=flop,
            mode="lines",
            line=dict(color="black", width=2, dash="dash"),
            name=f"Historical Rule A 2018+ ({mult:.2f}×/yr)",
        ))
    return _log_y(fig, "Largest frontier training run over time")


def bar_2040_largest_run(df: pd.DataFrame) -> go.Figure:
    """Bar chart of 2040 largest_run by combined scenario."""
    sub = df[df["year"] == 2040].sort_values(
        "largest_frontier_run_flop", ascending=True
    )
    fig = px.bar(
        sub, x="largest_frontier_run_flop", y="combined_scenario",
        orientation="h",
        labels={"largest_frontier_run_flop": "2040 largest run (FLOP)",
                "combined_scenario": ""},
    )
    fig.update_xaxes(type="log")
    fig.update_layout(
        title="2040 largest frontier run by combined scenario",
        margin=dict(l=20, r=20, t=50, b=40),
    )
    return fig


def frontier_run_share_chart(df: pd.DataFrame) -> go.Figure:
    fig = px.line(
        df.sort_values("year"),
        x="year", y="frontier_run_share_of_total_compute",
        color="combined_scenario", markers=True,
        labels={"frontier_run_share_of_total_compute":
                "Largest run / total usable compute",
                "year": "Year"},
    )
    fig.update_yaxes(type="log", tickformat=".1%")
    fig.update_layout(
        title="Largest frontier run as share of total usable compute",
        margin=dict(l=20, r=20, t=50, b=40),
        legend_title_text="",
    )
    return fig


# --- handoff envelope chart ---------------------------------------------


def envelope_chart(handoff_df: pd.DataFrame) -> go.Figure:
    """Slow / base / fast envelope as three lines over time."""
    fig = go.Figure()
    for envelope in ("slow", "base", "fast"):
        col = f"{envelope}_largest_frontier_run_flop"
        if col not in handoff_df.columns:
            continue
        fig.add_trace(go.Scatter(
            x=handoff_df["year"],
            y=handoff_df[col],
            mode="lines+markers",
            line=dict(color=ENVELOPE_COLORS[envelope], width=2.5),
            name=envelope.capitalize(),
        ))
    fig.update_yaxes(type="log")
    fig.update_layout(
        title="Slow / base / fast largest-frontier-run envelope",
        xaxis_title="Year",
        yaxis_title="Largest frontier run (FLOP)",
        margin=dict(l=20, r=20, t=50, b=40),
        legend_title_text="",
    )
    return fig


def bucket_handoff_chart(handoff_df: pd.DataFrame) -> go.Figure:
    """Base-case bucket totals as a stacked area."""
    fig = go.Figure()
    bucket_cols = [
        ("Inference", "base_inference_compute_flop_year"),
        ("Training", "base_training_compute_flop_year"),
        ("AI R&D experiment", "base_ai_rnd_experiment_compute_flop_year"),
        ("Post-training", "base_post_training_compute_flop_year"),
    ]
    for name, col in bucket_cols:
        if col not in handoff_df.columns:
            continue
        fig.add_trace(go.Scatter(
            x=handoff_df["year"], y=handoff_df[col],
            mode="lines",
            stackgroup="one",
            line=dict(width=0.5),
            name=name,
        ))
    fig.update_yaxes(type="log")
    fig.update_layout(
        title="Base-case bucket totals (training / inference / R&D / post-training)",
        xaxis_title="Year",
        yaxis_title="Compute (FLOP/year)",
        margin=dict(l=20, r=20, t=50, b=40),
        legend_title_text="",
    )
    return fig
