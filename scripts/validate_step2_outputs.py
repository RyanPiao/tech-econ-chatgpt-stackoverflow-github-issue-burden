from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"
EXPECTED_COLUMNS = [
    "month",
    "ecosystem",
    "stack_overflow_tag_anchor",
    "github_repo_group",
    "representative_repo_count",
    "month_index",
    "post_chatgpt",
    "so_dependence_pre",
    "treatment_intensity",
    "active_repos_observed",
    "stackoverflow_questions_month",
    "issues_opened",
    "median_close_days",
    "avg_first_response_hours",
    "backlog_open_end_month",
    "is_synthetic",
]


def validate() -> dict:
    panel = pd.read_csv(OUTPUTS / "step2_synthetic_panel.csv", parse_dates=["month"])
    dictionary = pd.read_csv(OUTPUTS / "step2_variable_dictionary.csv")

    errors = []
    warnings = []

    if list(panel.columns) != EXPECTED_COLUMNS:
        errors.append(
            {
                "check": "column_order_and_names",
                "message": "Panel columns do not match the Step 2 expected schema.",
            }
        )

    dictionary_variables = dictionary["variable"].tolist()
    missing_in_dictionary = [col for col in EXPECTED_COLUMNS if col not in dictionary_variables]
    if missing_in_dictionary:
        errors.append(
            {
                "check": "dictionary_coverage",
                "message": f"Variable dictionary missing: {missing_in_dictionary}",
            }
        )

    if panel.isna().any().any():
        null_counts = panel.isna().sum()
        errors.append(
            {
                "check": "missing_values",
                "message": "Panel contains missing values.",
                "details": null_counts[null_counts > 0].to_dict(),
            }
        )

    counts_per_ecosystem = panel.groupby("ecosystem")["month"].nunique().to_dict()
    bad_counts = {k: int(v) for k, v in counts_per_ecosystem.items() if v != 48}
    if bad_counts:
        errors.append(
            {
                "check": "balanced_panel",
                "message": "Each ecosystem should have 48 monthly observations.",
                "details": bad_counts,
            }
        )

    if set(panel["post_chatgpt"].unique()) != {0, 1}:
        errors.append(
            {
                "check": "post_indicator_support",
                "message": "post_chatgpt must contain both 0 and 1 values.",
            }
        )

    if (panel["is_synthetic"] != 1).any():
        errors.append(
            {
                "check": "synthetic_flag",
                "message": "All rows must be flagged as synthetic in Step 2 demonstration outputs.",
            }
        )

    nonnegative_cols = [
        "representative_repo_count",
        "month_index",
        "so_dependence_pre",
        "treatment_intensity",
        "active_repos_observed",
        "stackoverflow_questions_month",
        "issues_opened",
        "median_close_days",
        "avg_first_response_hours",
        "backlog_open_end_month",
    ]
    negatives = {
        col: int((panel[col] < 0).sum()) for col in nonnegative_cols if (panel[col] < 0).any()
    }
    if negatives:
        errors.append(
            {
                "check": "nonnegative_fields",
                "message": "Nonnegative fields contain negative values.",
                "details": negatives,
            }
        )

    if not panel["month"].is_monotonic_increasing:
        warnings.append(
            {
                "check": "global_month_sort",
                "message": "Global month ordering is not monotonic because the panel is sorted by ecosystem then month. This is acceptable.",
            }
        )

    summary = {
        "n_rows": int(len(panel)),
        "n_ecosystems": int(panel["ecosystem"].nunique()),
        "sample_start": panel["month"].min().strftime("%Y-%m-%d"),
        "sample_end": panel["month"].max().strftime("%Y-%m-%d"),
        "issues_opened_range": [int(panel["issues_opened"].min()), int(panel["issues_opened"].max())],
        "median_close_days_range": [
            float(panel["median_close_days"].min()),
            float(panel["median_close_days"].max()),
        ],
    }

    return {
        "status": "ok" if not errors else "error",
        "errors": errors,
        "warnings": warnings,
        "summary": summary,
    }


def main() -> None:
    report = validate()
    report_path = OUTPUTS / "step2_validation_report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {report_path}")
    if report["status"] != "ok":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
