"""Generate docs/assets/model_architecture.png.

Standalone matplotlib script. Run with:

    uv run python docs/assets/_generate_architecture.py

Produces a polished architecture diagram showing the modeling stack
(7 components — historical through economy feedback) plus two
observability layers (review + scenario explorer) hanging off as side
branches. Status pills are kept up to date here; if you add or build a
component, edit the COMPONENTS list below and rerun.
"""
from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from pathlib import Path

OUT = Path(__file__).resolve().parent / "model_architecture.png"

# Colors
BUILT = "#2ca02c"        # green
NEXT = "#ff7f0e"         # orange
FUTURE = "#9aa0b4"       # muted blue-grey
HIST_BG = "#dfe6f5"
SUPPLY_INPUT_BG = "#f3e5d8"
ALLOC_INPUT_BG = "#fde9c8"
CAP_INPUT_BG = "#f0e0f5"
REVIEW_BG = "#e8f0fa"

STATUS_PILL_COLOR = {"BUILT": "#2ca02c", "NEXT": "#ff7f0e", "FUTURE": "#7d8499"}
STATUS_FACE = {"BUILT": BUILT, "NEXT": NEXT, "FUTURE": FUTURE}


def _box(ax, x, y, w, h, label, status, fontsize=11):
    """Rounded rectangle with a coloured status pill."""
    box = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.02,rounding_size=0.08",
        linewidth=1.4,
        edgecolor="#222",
        facecolor=STATUS_FACE[status],
        zorder=2,
    )
    ax.add_patch(box)
    ax.text(x + w / 2, y + h * 0.62, label,
            ha="center", va="center", fontsize=fontsize, fontweight="bold")
    pill_w, pill_h = 0.55, 0.18
    pill_x, pill_y = x + w / 2 - pill_w / 2, y + h * 0.18
    pill = FancyBboxPatch(
        (pill_x, pill_y), pill_w, pill_h,
        boxstyle="round,pad=0.0,rounding_size=0.06",
        linewidth=0,
        facecolor=STATUS_PILL_COLOR[status],
        zorder=3,
    )
    ax.add_patch(pill)
    ax.text(pill_x + pill_w / 2, pill_y + pill_h / 2, status,
            ha="center", va="center", fontsize=8.5, color="white", fontweight="bold")


def _arrow(ax, p1, p2, label=None, style="-|>", curve=None, color="#222", linewidth=1.6):
    arrow = FancyArrowPatch(
        p1, p2,
        arrowstyle=style,
        mutation_scale=14,
        linewidth=linewidth,
        color=color,
        connectionstyle=curve if curve else "arc3,rad=0",
        zorder=4,
    )
    ax.add_patch(arrow)
    if label:
        mx, my = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
        ax.text(mx + 0.1, my, label, fontsize=8.5, color=color, ha="left", va="center")


def _input_panel(ax, x, y, w, h, title, items, bg, *, edge="#999"):
    panel = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.02,rounding_size=0.06",
        linewidth=1.0,
        edgecolor=edge,
        facecolor=bg,
        zorder=1,
    )
    ax.add_patch(panel)
    ax.text(x + w / 2, y + h - 0.18, title,
            ha="center", va="center", fontsize=9, fontweight="bold")
    line_h = (h - 0.4) / max(len(items), 1)
    for i, item in enumerate(items):
        ax.text(x + 0.12, y + h - 0.4 - (i + 0.5) * line_h, f"• {item}",
                ha="left", va="center", fontsize=8.5)


# Modeling stack: (label, y_position, status). Edit here when status changes.
COMPONENTS = [
    ("Historical Baseline",     8.6, "BUILT"),
    ("Supply Capacity Model",   7.2, "BUILT"),
    ("Compute Allocation",      5.8, "BUILT"),
    ("Effective Compute",       4.4, "NEXT"),
    ("Capability Mapping",      3.2, "FUTURE"),
    ("Projection Engine",       2.0, "FUTURE"),
    ("Economy Feedback",        0.8, "FUTURE"),
]

# Observability side branches: (label, y_position, status).
SIDE_BRANCHES = [
    ("Review Layer\n(DuckDB + Workbook)",    5.8, "BUILT"),
    ("Scenario Explorer\n(Streamlit)",       4.4, "BUILT"),
]


def main() -> None:
    fig, ax = plt.subplots(figsize=(13, 10))
    ax.set_xlim(-0.4, 13.4)
    ax.set_ylim(-0.2, 10.6)
    ax.set_aspect("equal")
    ax.axis("off")

    comp_x, comp_w, comp_h = 4.0, 4.0, 0.85

    # --- main modeling stack -----------------------------------------
    for label, y, status in COMPONENTS:
        _box(ax, comp_x, y, comp_w, comp_h, label, status)

    # forward arrows between consecutive modeling components
    cx = comp_x + comp_w / 2
    for i in range(len(COMPONENTS) - 1):
        _, y_top, _ = COMPONENTS[i]
        _, y_bot, _ = COMPONENTS[i + 1]
        _arrow(ax, (cx, y_top), (cx, y_bot + comp_h))

    # historical → allocation calibration arrow (curved, right side)
    hist_y = COMPONENTS[0][1]
    alloc_y = COMPONENTS[2][1]
    _arrow(
        ax,
        (comp_x + comp_w, hist_y + comp_h / 2),
        (comp_x + comp_w, alloc_y + comp_h / 2),
        label="comparison /\ncalibration",
        curve="arc3,rad=-0.5",
        color="#666",
    )

    # economy feedback → supply (left side, loop-back)
    supply_y = COMPONENTS[1][1]
    econ_y = COMPONENTS[-1][1]
    _arrow(
        ax,
        (comp_x, econ_y + comp_h / 2),
        (comp_x, supply_y + comp_h / 2),
        label="reinvestment\nfeedback",
        curve="arc3,rad=0.7",
        color="#1f77b4",
        linewidth=1.2,
    )

    # --- review / observability side branches ------------------------
    side_x, side_w = -0.2, 3.4
    for label, y, status in SIDE_BRANCHES:
        _box(ax, side_x, y, side_w, comp_h, label, status, fontsize=9.5)

    # arrows from main-stack components to the side branches
    review_y = SIDE_BRANCHES[0][1]
    explorer_y = SIDE_BRANCHES[1][1]
    _arrow(
        ax,
        (comp_x, alloc_y + comp_h / 2),
        (side_x + side_w, review_y + comp_h / 2),
        color="#888", linewidth=1.1, style="->",
    )
    _arrow(
        ax,
        (side_x + side_w, review_y),
        (side_x + side_w, explorer_y + comp_h),
        color="#888", linewidth=1.0, style="->",
    )

    # --- input panels on the right side ------------------------------
    panel_x, panel_w = 10.0, 3.2
    _input_panel(ax, panel_x, 7.0, panel_w, 1.6,
                 "Supply inputs",
                 ["chips (H100-eq shipments)",
                  "power & data centers (MW)",
                  "capex ($/yr)",
                  "utilization (MFU)"],
                 SUPPLY_INPUT_BG)
    _input_panel(ax, panel_x, 5.4, panel_w, 1.4,
                 "Allocation inputs",
                 ["training / inference / R&D shares",
                  "post-training share",
                  "largest-run concentration"],
                 ALLOC_INPUT_BG)
    _input_panel(ax, panel_x, 3.8, panel_w, 1.4,
                 "Capability inputs",
                 ["algorithmic efficiency",
                  "data quality",
                  "post-training efficiency"],
                 CAP_INPUT_BG)

    _arrow(ax, (panel_x, 7.8),
           (comp_x + comp_w, supply_y + comp_h / 2),
           color="#888", linewidth=1.0)
    _arrow(ax, (panel_x, 6.1),
           (comp_x + comp_w, alloc_y + comp_h / 2),
           color="#888", linewidth=1.0)
    _arrow(ax, (panel_x, 4.5),
           (comp_x + comp_w, COMPONENTS[4][1] + comp_h / 2),
           color="#888", linewidth=1.0)

    # historical inputs panel (top left)
    _input_panel(ax, 8.0, 8.7, 1.9, 1.4,
                 "Historical inputs",
                 ["Epoch \"Notable AI Models\"",
                  "1,011 models, 1950–2026"],
                 HIST_BG)
    _arrow(ax, (8.0, 9.4),
           (comp_x + comp_w, hist_y + comp_h / 2),
           color="#888", linewidth=1.0)

    # title + footer
    n_built = sum(1 for *_, s in COMPONENTS + SIDE_BRANCHES if s == "BUILT")
    n_next = sum(1 for *_, s in COMPONENTS + SIDE_BRANCHES if s == "NEXT")
    n_future = sum(1 for *_, s in COMPONENTS + SIDE_BRANCHES if s == "FUTURE")
    ax.text(6.5, 10.30, "Model architecture",
            ha="center", va="center", fontsize=15, fontweight="bold")
    ax.text(6.5, 9.95,
            f"{n_built} built  •  {n_next} next  •  {n_future} future",
            ha="center", va="center", fontsize=10, color="#444")
    ax.text(6.5, 0.05,
            "Generated by docs/assets/_generate_architecture.py · "
            "see docs/model_map.md for the data-flow diagram",
            ha="center", va="center", fontsize=8, color="#777", style="italic")

    fig.tight_layout()
    fig.savefig(OUT, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
