"""Excel review-workbook pipeline.

Run with: `uv run workbook`

Builds outputs/workbooks/ai_economy_model_review.xlsx from the existing
CSV outputs. 11 sheets per the upstream review-layer scope.

The workbook is a generated review artifact — fully reproducible from
the repo, safe to delete and rebuild. Source of truth remains
YAML / Python / CSV / Markdown.
"""
from __future__ import annotations

from model.workbook_export import WORKBOOK_PATH, export_workbook


def main() -> None:
    print(f"[1/2] Building Excel workbook at {WORKBOOK_PATH}...")
    manifest = export_workbook()

    print("[2/2] Summary:")
    print(f"  schema version: {manifest['schema_version']}")
    print(f"  git commit:     {manifest['git_commit']}")
    print(f"  generated at:   {manifest['generated_at']}")
    print(f"  workbook:       {manifest['workbook_path']}")
    print("  sheets:")
    for n, name in enumerate([
        "README", "Model Flow", "Scenario Matrix", "Historical Baseline",
        "Supply Capacity", "Allocation Buckets", "Largest Frontier Run",
        "Phase 4 Handoff", "Assumptions", "Sources & Confidence", "Output Inventory",
    ], start=1):
        print(f"    {n:>2}. {name}")


if __name__ == "__main__":
    main()
