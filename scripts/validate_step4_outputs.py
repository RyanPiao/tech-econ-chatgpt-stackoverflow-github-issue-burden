from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"

EXPECTED_PANEL_BASE_COLUMNS = {
    "month",
    "ecosystem",
    "post_chatgpt",
    "so_dependence_pre",
    "treatment_intensity",
    "issues_opened",
    "median_close_days",
    "avg_first_response_hours",
    "backlog_open_end_month",
    "issue_burden_index",
    "issues_per_active_repo",
    "backlog_per_active_repo",
    "questions_per_active_repo",
}

EXPECTED_PANEL_STEP4_COLUMNS = {
    "year",
    "calendar_month",
    "quarter",
    "repo_scale",
    "post_trend_months",
    "season_sin",
    "season_cos",
    "lag_issues_opened",
    "lag_backlog_open_end_month",
    "lag_avg_first_response_hours",
    "delta_issues_opened",
    "delta_backlog_open_end_month",
    "delta_avg_first_response_hours",
    "log1p_issues_opened",
    "log1p_backlog_open_end_month",
    "active_repos_z",
    "questions_per_active_repo_z",
    "repo_scale_z",
}

EXPECTED_MODEL_OUTCOMES = {
    "issues_opened",
    "median_close_days",
    "avg_first_response_hours",
    "backlog_open_end_month",
    "issue_burden_index",
}

EXPECTED_SPECS = {
    "baseline_fe_controls_clustered",
    "fe_no_controls_clustered",
    "fe_controls_weighted_repos",
}

EXPECTED_DIAGNOSTICS = {
    "event_study_pretrend_joint_p_value",
    "placebo_treatment_p_value",
    "max_abs_loo_deviation",
}


def validate() -> dict:
    errors = []
    warnings = []

    panel = pd.read_csv(OUTPUTS / "step4_model_panel.csv")
    eda_summary = pd.read_csv(OUTPUTS / "step4_eda_distribution_summary.csv")
    corr = pd.read_csv(OUTPUTS / "step4_outcome_correlation.csv", index_col=0)
    variance = pd.read_csv(OUTPUTS / "step4_variance_decomposition.csv")
    twfe = pd.read_csv(OUTPUTS / "step4_twfe_models.csv")
    sanity = pd.read_csv(OUTPUTS / "step4_statsmodels_sanity_check.csv")
    event = pd.read_csv(OUTPUTS / "step4_event_study_issues_opened.csv")
    placebo = pd.read_csv(OUTPUTS / "step4_placebo_test.csv")
    loo = pd.read_csv(OUTPUTS / "step4_leave_one_ecosystem_out.csv")
    diagnostics = pd.read_csv(OUTPUTS / "step4_identification_diagnostics.csv")
    key_metrics = json.loads((OUTPUTS / "step4_key_metrics.json").read_text(encoding="utf-8"))
    manifest = json.loads((OUTPUTS / "step4_manifest.json").read_text(encoding="utf-8"))

    panel_cols = set(panel.columns)
    if not EXPECTED_PANEL_BASE_COLUMNS.issubset(panel_cols):
        errors.append(
            {
                "check": "panel_base_columns",
                "message": "Step 4 model panel is missing required inherited columns.",
                "details": sorted(EXPECTED_PANEL_BASE_COLUMNS - panel_cols),
            }
        )

    if not EXPECTED_PANEL_STEP4_COLUMNS.issubset(panel_cols):
        errors.append(
            {
                "check": "panel_step4_columns",
                "message": "Step 4 model panel is missing required derived columns.",
                "details": sorted(EXPECTED_PANEL_STEP4_COLUMNS - panel_cols),
            }
        )

    if len(panel) != 384 or panel["ecosystem"].nunique() != 8:
        errors.append(
            {
                "check": "panel_dimensions",
                "message": "Step 4 panel dimensions should remain 384 rows and 8 ecosystems.",
                "details": {
                    "rows": int(len(panel)),
                    "ecosystems": int(panel["ecosystem"].nunique()),
                },
            }
        )

    if panel["month"].nunique() != 48:
        errors.append(
            {
                "check": "month_support",
                "message": "Step 4 panel should include 48 monthly periods.",
            }
        )

    core_na = panel[list(EXPECTED_PANEL_BASE_COLUMNS | EXPECTED_PANEL_STEP4_COLUMNS)].isna().sum()
    if core_na.any():
        errors.append(
            {
                "check": "panel_missing_values",
                "message": "Step 4 panel contains missing values in required columns.",
                "details": core_na[core_na > 0].to_dict(),
            }
        )

    if set(twfe["outcome"]) != EXPECTED_MODEL_OUTCOMES:
        errors.append(
            {
                "check": "twfe_outcomes",
                "message": "TWFE table does not cover all expected outcomes.",
            }
        )

    if set(twfe["specification"]) != EXPECTED_SPECS:
        errors.append(
            {
                "check": "twfe_specs",
                "message": "TWFE table does not contain all expected specifications.",
            }
        )

    expected_twfe_rows = len(EXPECTED_MODEL_OUTCOMES) * len(EXPECTED_SPECS)
    if len(twfe) != expected_twfe_rows:
        errors.append(
            {
                "check": "twfe_row_count",
                "message": "Unexpected number of rows in TWFE model table.",
                "details": {"expected": expected_twfe_rows, "actual": int(len(twfe))},
            }
        )

    if set(sanity["outcome"].tolist()) != {"issues_opened", "avg_first_response_hours"}:
        errors.append(
            {
                "check": "statsmodels_sanity_outcomes",
                "message": "Statsmodels sanity check must include issues_opened and avg_first_response_hours.",
            }
        )

    expected_event_months = {k for k in range(-12, 19) if k != -1}
    if set(event["event_month"].tolist()) != expected_event_months:
        errors.append(
            {
                "check": "event_month_support",
                "message": "Event-study table does not match expected lead/lag support.",
            }
        )

    if len(placebo) != 1:
        errors.append(
            {
                "check": "placebo_rows",
                "message": "Placebo output should contain exactly one row.",
            }
        )

    if loo["dropped_ecosystem"].nunique() != 8 or len(loo) != 8:
        errors.append(
            {
                "check": "loo_shape",
                "message": "Leave-one-ecosystem-out output must have one row per ecosystem.",
            }
        )

    diagnostic_names = set(diagnostics["diagnostic"].tolist())
    if not EXPECTED_DIAGNOSTICS.issubset(diagnostic_names):
        errors.append(
            {
                "check": "diagnostics_presence",
                "message": "Identification diagnostics are missing core checks.",
                "details": sorted(EXPECTED_DIAGNOSTICS - diagnostic_names),
            }
        )

    if corr.shape[0] != corr.shape[1]:
        errors.append(
            {
                "check": "correlation_square",
                "message": "Outcome correlation matrix must be square.",
            }
        )

    if set(variance["outcome"]) != EXPECTED_MODEL_OUTCOMES:
        errors.append(
            {
                "check": "variance_outcomes",
                "message": "Variance decomposition does not cover all modeled outcomes.",
            }
        )

    if key_metrics.get("panel_rows") != 384 or key_metrics.get("ecosystem_count") != 8:
        errors.append(
            {
                "check": "key_metrics_dimensions",
                "message": "Step 4 key metrics dimensions are inconsistent with the panel.",
            }
        )

    required_manifest_outputs = {
        "outputs/step4_model_panel.csv",
        "outputs/step4_twfe_models.csv",
        "outputs/step4_event_study_issues_opened.csv",
        "outputs/step4_key_metrics.json",
        "docs/STEP4_baseline_econometric_model.md",
    }
    manifest_outputs = set(manifest.get("outputs", []))
    if not required_manifest_outputs.issubset(manifest_outputs):
        errors.append(
            {
                "check": "manifest_outputs",
                "message": "Step 4 manifest is missing required outputs.",
                "details": sorted(required_manifest_outputs - manifest_outputs),
            }
        )

    if len(eda_summary) < 40:
        warnings.append(
            {
                "check": "eda_summary_size",
                "message": "EDA summary appears smaller than expected; verify grouping logic.",
            }
        )

    summary = {
        "panel_rows": int(len(panel)),
        "panel_columns": int(panel.shape[1]),
        "twfe_rows": int(len(twfe)),
        "event_rows": int(len(event)),
        "loo_rows": int(len(loo)),
        "diagnostic_rows": int(len(diagnostics)),
        "correlation_dim": [int(corr.shape[0]), int(corr.shape[1])],
    }

    return {
        "status": "ok" if not errors else "error",
        "errors": errors,
        "warnings": warnings,
        "summary": summary,
    }


def main() -> None:
    report = validate()
    report_path = OUTPUTS / "step4_validation_report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {report_path}")
    if report["status"] != "ok":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
