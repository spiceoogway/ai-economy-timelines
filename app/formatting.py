"""Number-formatting helpers for the Streamlit demo."""
from __future__ import annotations


def format_flop(value: float | None) -> str:
    """6.93e+28 → '6.93e+28' (scientific notation, 2 sig figs)."""
    if value is None:
        return "—"
    if value == 0:
        return "0"
    return f"{value:.2e}"


def format_pct(value: float | None) -> str:
    """0.276 → '27.6%' (one decimal)."""
    if value is None:
        return "—"
    return f"{value * 100:.1f}%"


def format_share(value: float | None) -> str:
    """Same as format_pct but shows two decimals when values are very small."""
    if value is None:
        return "—"
    if abs(value) < 0.01:
        return f"{value * 100:.2f}%"
    return f"{value * 100:.1f}%"


def format_usd(value: float | None) -> str:
    """$210B / $1.5T / $9.4e+28 — picks the most readable form."""
    if value is None or value == 0:
        return "—"
    abs_v = abs(value)
    if abs_v >= 1e12:
        return f"${value / 1e12:.1f}T"
    if abs_v >= 1e9:
        return f"${value / 1e9:.0f}B"
    if abs_v >= 1e6:
        return f"${value / 1e6:.0f}M"
    return f"${value:,.0f}"


def format_year(year: int | float | None) -> str:
    """4-digit year."""
    if year is None:
        return "—"
    return f"{int(year)}"


def format_compute_compact(value: float | None) -> str:
    """Compact FLOP for metric cards: 6.9e28 instead of 6.93e+28."""
    if value is None or value == 0:
        return "—"
    return f"{value:.1e}".replace("e+0", "e").replace("e-0", "e-")


def envelope_color(envelope: str) -> str:
    """Hex color for a slow/base/fast envelope label."""
    return {
        "slow": "#FFC7CE",
        "base": "#FFEB9C",
        "fast": "#C6EFCE",
    }.get(envelope, "#DDDDDD")
