"""Review database pipeline.

Run with: `uv run database`

Builds outputs/database/ai_economy.duckdb from the existing CSV outputs.
Requires that all upstream pipelines have run first (`uv run historical`,
`uv run supply`, `uv run allocation`).

The review database is a generated artifact — fully reproducible from
the repo, safe to delete and rebuild. The source of truth remains
the YAMLs, Python pipelines, CSV/Parquet outputs, and Markdown findings.
"""
from __future__ import annotations

from model.review_database import (
    DATABASE_MANIFEST,
    DATABASE_PATH,
    build_review_database,
)


def main() -> None:
    print(f"[1/3] Building DuckDB at {DATABASE_PATH}...")
    manifest = build_review_database()

    print(f"[2/3] Manifest → {DATABASE_MANIFEST}")

    print("[3/3] Summary:")
    print(f"  schema version: {manifest['schema_version']}")
    print(f"  git commit:     {manifest['git_commit']}")
    print(f"  tables:         {len(manifest['tables_created'])}")
    for table, count in manifest["row_counts"].items():
        print(f"    {table:48s} {count:>8,} rows")
    print(f"  views:          {len(manifest['views_created'])}")
    for view in manifest["views_created"]:
        print(f"    {view}")


if __name__ == "__main__":
    main()
