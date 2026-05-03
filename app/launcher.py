"""Entry point for `uv run demo`.

Wraps the Streamlit CLI so users don't have to remember the verbose
`streamlit run app/streamlit_app.py` form.
"""
from __future__ import annotations

import sys
from pathlib import Path

import streamlit.web.cli as stcli


def main() -> None:
    app_path = str(Path(__file__).parent / "streamlit_app.py")
    sys.argv = ["streamlit", "run", app_path]
    sys.exit(stcli.main())


if __name__ == "__main__":
    main()
