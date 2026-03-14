from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"
EXPECTED_PANEL_COLUMNS = [
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
    "exposure_bucket",
    "months_since_chatgpt",
    "post_period_label",
    "high_exposure",
    "issues_per_active_repo",
    "backlog_per_active_repo",
    "questions_per_active_repo",
    "avg_first_response_days",
    "log_issues_opened",
    "log_backlog_open_end_month",
    "issue_burden_index",
]
EXPECTED_DIAGNOSTIC_OUTCOMES = {
    "issues_opened",
    "median_close_days",
    "avg_first_response_hours",
    "backlog_open_end_month",
    "issue_burden_index",
    "issues_per_active_repo",
}
EXPECTED_CHANGE_OUTCOMES = {
    "issues_opened",
    "median_close_days",
    "avg_first_response_hours",
    "backlog_open_end_month",
    "issues_per_active_repo",
    "backlog_per_active_repo",
    "issue_burden_index",
}


def validate() -> dict:
    errors = []
    warnings = []

    panel = pd.read_csv(OUTPUTS / "step3_identification_ready_panel.csv")
    ecosystem_summary = pd.read_csv(OUTPUTS / "step3_ecosystem_pre_post_summary.csv")
    event_summary = pd.read_csv(OUTPUTS / "step3_event_time_exposure_summary.csv")
    diagnostics = pd.read_csv(OUTPUTS / "step3_parallel_trend_diagnostics.csv")
    exposure_change = pd.read_csv(OUTPUTS / "step3_exposure_change_summary.csv")
    manifest = json.loads((OUTPUTS / "step3_manifest.json").read_text(encoding="utf-8"))

    if list(panel.columns) != EXPECTED_PANEL_COLUMNS:
        errors.append(
            {
                "check": "panel_schema",
                "message": "Step 3 identification-ready panel columns do not match the expected schema.",
            }
        )

    if panel.isna().any().any():
        errors.append(
            {
                "check": "panel_missing_values",
                "message": "Step 3 panel contains missing values.",
                "details": panel.isna().sum()[panel.isna().sum() > 0].to_dict(),
            }
        )

    if sorted(panel["exposure_bucket"].dropna().unique().tolist()) != ["high", "low", "mid"]:
        errors.append(
            {
                "check": "exposure_bucket_support",
                "message": "Exposure buckets must contain high, mid, and low.",
            }
        )

    if set(panel["post_period_label"].unique()) != {"pre", "post"}:
        errors.append(
            {
                "check": "post_period_labels",
                "message": "post_period_label must contain pre and post.",
            }
        )

    if panel["months_since_chatgpt"].min() != -23 or panel["months_since_chatgpt"].max() != 24:
        errors.append(
            {
                "check": "event_time_range",
                "message": "Unexpected months_since_chatgpt range.",
                "details": {
                    "min": int(panel["months_since_chatgpt"].min()),
                    "max": int(panel["months_since_chatgpt"].max()),
                },
            }
        )

    if (panel["is_synthetic"] != 1).any():
        errors.append(
            {
                "check": "synthetic_flag",
                "message": "All Step 3 rows must remain synthetic.",
            }
        )

    balanced_counts = panel.groupby("ecosystem")["month"].nunique()
    if not (balanced_counts == 48).all():
        errors.append(
            {
                "check": "balanced_panel",
                "message": "Each ecosystem should retain 48 monthly observations in Step 3.",
                "details": balanced_counts[balanced_counts != 48].to_dict(),
            }
        )

    if set(diagnostics["outcome"]) != EXPECTED_DIAGNOSTIC_OUTCOMES:
        errors.append(
            {
                "check": "diagnostic_outcomes",
                "message": "Parallel-trend diagnostics do not cover the expected outcomes.",
            }
        )

    if set(exposure_change["outcome"]) != EXPECTED_CHANGE_OUTCOMES:
        errors.append(
            {
                "check": "exposure_change_outcomes",
                "message": "Exposure-change summary does not cover the expected outcomes.",
            }
        )

    if ecosystem_summary["ecosystem"].nunique() != 8:
        errors.append(
            {
                "check": "ecosystem_summary_count",
                "message": "Ecosystem summary should contain one row per ecosystem.",
            }
        )

    if event_summary["ecosystems"].min() <= 0:
        errors.append(
            {
                "check": "event_summary_counts",
                "message": "Event-time summary must have positive ecosystem counts.",
            }
        )

    if len(manifest.get("outputs", [])) != 6:
        warnings.append(
            {
                "check": "manifest_outputs",
                "message": "Manifest outputs list length differs from the expected Step 3 package size.",
            }
        )

    summary = {
        "n_rows": int(len(panel)),
        "n_ecosystems": int(panel["ecosystem"].nunique()),
        "issue_burden_index_range": [
            float(panel["issue_burden_index"].min()),
            float(panel["issue_burden_index"].max()),
        ],
        "event_time_rows": int(len(event_summary)),
        "diagnostic_rows": int(len(diagnostics)),
        "change_rows": int(len(exposure_change)),
    }

    return {
        "status": "ok" if not errors else "error",
        "errors": errors,
        "warnings": warnings,
        "summary": summary,
    }


def main() -> None:
    report = validate()
    report_path = OUTPUTS / "step3_validation_report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {report_path}")
    if report["status"] != "ok":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
