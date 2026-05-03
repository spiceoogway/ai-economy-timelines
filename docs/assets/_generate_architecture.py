"""Generate docs/assets/model_architecture.png.

Standalone matplotlib script. Run with:

    uv run python docs/assets/_generate_architecture.py

Produces a polished architecture diagram showing the 7-component model
stack (2 built, 1 next, 4 future), the major input categories on the
side, and the calibration arrow from the historical baseline.
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


def _box(ax, x, y, w, h, label, color, status_label, status_color, fontsize=11):
    """Rounded rectangle with a coloured status pill."""
    box = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.02,rounding_size=0.08",
        linewidth=1.4,
        edgecolor="#222",
        facecolor=color,
        zorder=2,
    )
    ax.add_patch(box)
    ax.text(x + w / 2, y + h * 0.62, label,
            ha="center", va="center", fontsize=fontsize, fontweight="bold")
    # status pill
    pill_w, pill_h = 0.55, 0.18
    pill_x, pill_y = x + w / 2 - pill_w / 2, y + h * 0.18
    pill = FancyBboxPatch(
        (pill_x, pill_y), pill_w, pill_h,
        boxstyle="round,pad=0.0,rounding_size=0.06",
        linewidth=0,
        facecolor=status_color,
        zorder=3,
    )
    ax.add_patch(pill)
    ax.text(pill_x + pill_w / 2, pill_y + pill_h / 2, status_label,
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


def _input_panel(ax, x, y, w, h, title, items, bg):
    """A side panel listing input categories for one component."""
    panel = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.02,rounding_size=0.06",
        linewidth=1.0,
        edgecolor="#999",
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


def main() -> None:
    fig, ax = plt.subplots(figsize=(12, 10))
    ax.set_xlim(0, 12)
    ax.set_ylim(-0.2, 10.6)
    ax.set_aspect("equal")
    ax.axis("off")

    # ---- Component column (center) ----
    comp_x, comp_w, comp_h = 4.0, 4.0, 0.85
    spacings = [
        ("Historical Baseline",         8.6, BUILT,  "BUILT",  "#2ca02c"),
        ("Supply Capacity Model",       7.2, BUILT,  "BUILT",  "#2ca02c"),
        ("Compute Allocation",          5.8, NEXT,   "NEXT",   "#ff7f0e"),
        ("Effective Compute",           4.4, FUTURE, "FUTURE", "#7d8499"),
        ("Capability Mapping",          3.2, FUTURE, "FUTURE", "#7d8499"),
        ("Projection Engine",           2.0, FUTURE, "FUTURE", "#7d8499"),
        ("Economy Feedback",            0.8, FUTURE, "FUTURE", "#7d8499"),
    ]

    for label, y, color, status_label, status_color in spacings:
        _box(ax, comp_x, y, comp_w, comp_h, label, color, status_label, status_color)

    # Vertical down-arrows between consecutive components (skip historical → supply; that's a side arrow)
    arrow_pairs = [
        (7.2, 5.8),  # supply → allocation
        (5.8, 4.4),  # allocation → effective
        (4.4, 3.2),  # effective → capability
        (3.2, 2.0),  # capability → projection
        (2.0, 0.8),  # projection → economy
    ]
    cx = comp_x + comp_w / 2
    for y_top, y_bot in arrow_pairs:
        _arrow(ax, (cx, y_top), (cx, y_bot + comp_h))

    # Historical baseline → comparison/calibration → allocation (curved arrow)
    _arrow(
        ax,
        (comp_x + comp_w, 8.6 + comp_h / 2),  # right edge of historical
        (comp_x + comp_w, 5.8 + comp_h / 2),   # right edge of allocation
        label="comparison /\ncalibration",
        curve="arc3,rad=-0.5",
        color="#666",
    )

    # Economy feedback → supply capacity (loop-back)
    _arrow(
        ax,
        (comp_x, 0.8 + comp_h / 2),                 # left edge of economy
        (comp_x, 7.2 + comp_h / 2),                 # left edge of supply
        label="reinvestment\nfeedback",
        curve="arc3,rad=0.7",
        color="#1f77b4",
        linewidth=1.2,
    )

    # ---- Input panels on the right side ----
    panel_x, panel_w = 9.2, 2.6
    _input_panel(ax, panel_x, 6.6, panel_w, 1.6,
                 "Supply inputs",
                 ["chips (H100-eq shipments)",
                  "power & data centers (MW)",
                  "capex ($/yr)",
                  "utilization (MFU)"],
                 SUPPLY_INPUT_BG)
    _input_panel(ax, panel_x, 5.0, panel_w, 1.4,
                 "Allocation inputs",
                 ["training / inference / R&D shares",
                  "post-training share",
                  "largest-run concentration"],
                 ALLOC_INPUT_BG)
    _input_panel(ax, panel_x, 3.4, panel_w, 1.4,
                 "Capability inputs",
                 ["algorithmic efficiency",
                  "data quality",
                  "post-training efficiency"],
                 CAP_INPUT_BG)

    # Connector lines from input panels to their components
    _arrow(ax, (panel_x, 7.4),
           (comp_x + comp_w, 7.2 + comp_h / 2),
           color="#888", linewidth=1.0)
    _arrow(ax, (panel_x, 5.7),
           (comp_x + comp_w, 5.8 + comp_h / 2),
           color="#888", linewidth=1.0)
    _arrow(ax, (panel_x, 4.1),
           (comp_x + comp_w, 3.2 + comp_h / 2),
           color="#888", linewidth=1.0)

    # ---- Historical baseline input panel (left side) ----
    _input_panel(ax, 0.4, 8.0, panel_w, 1.4,
                 "Historical inputs",
                 ["Epoch \"Notable AI Models\"",
                  "1,011 models, 1950–2026"],
                 HIST_BG)
    _arrow(ax, (0.4 + panel_w, 8.5),
           (comp_x, 8.6 + comp_h / 2),
           color="#888", linewidth=1.0)

    # ---- Title and footer ----
    ax.text(6.0, 10.30, "Model architecture",
            ha="center", va="center", fontsize=15, fontweight="bold")
    ax.text(6.0, 9.95,
            "Two components built • one next • four future",
            ha="center", va="center", fontsize=10, color="#444")
    ax.text(6.0, 0.05,
            "Generated by docs/assets/_generate_architecture.py · "
            "see docs/model_map.md for the data-flow diagram",
            ha="center", va="center", fontsize=8, color="#777", style="italic")

    fig.tight_layout()
    fig.savefig(OUT, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
