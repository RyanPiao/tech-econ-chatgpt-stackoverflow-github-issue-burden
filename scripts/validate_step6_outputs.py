from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"
DOCS = ROOT / "docs"

EXPECTED_OUTCOMES = {
    "issues_opened",
    "median_close_days",
    "avg_first_response_hours",
    "backlog_open_end_month",
    "issue_burden_index",
}

EXPECTED_FINAL_SPECS = {
    "baseline_step4_reference",
    "finalized_trend_adjusted",
}

EXPECTED_CHECK_IDS = {
    "baseline_reference",
    "eco_specific_trends",
    "repo_size_weighting",
    "lagged_outcome",
    "so_activity_controls",
    "symmetric_window",
    "anticipation_lead6_treatment",
    "anticipation_lead6_placebo",
    "intensive_margin_ratio",
}

EXPECTED_CUTOFFS = {
    "2022-06-01",
    "2022-09-01",
    "2022-12-01",
    "2023-03-01",
    "2023-06-01",
}


def validate() -> dict:
    errors: list[dict] = []
    warnings: list[dict] = []

    final_models = pd.read_csv(OUTPUTS / "step6_finalized_model_results.csv")
    alternatives = pd.read_csv(OUTPUTS / "step6_alternative_explanations.csv")
    cutoff_sweep = pd.read_csv(OUTPUTS / "step6_cutoff_sweep.csv")
    key_metrics = json.loads((OUTPUTS / "step6_key_metrics.json").read_text(encoding="utf-8"))
    manifest = json.loads((OUTPUTS / "step6_manifest.json").read_text(encoding="utf-8"))

    step4_twfe = pd.read_csv(OUTPUTS / "step4_twfe_models.csv")

    if set(final_models["specification"].unique()) != EXPECTED_FINAL_SPECS:
        errors.append(
            {
                "check": "final_specs",
                "message": "Final model table does not contain expected specifications.",
                "details": {
                    "missing": sorted(EXPECTED_FINAL_SPECS - set(final_models["specification"].unique())),
                    "extra": sorted(set(final_models["specification"].unique()) - EXPECTED_FINAL_SPECS),
                },
            }
        )

    for spec in EXPECTED_FINAL_SPECS:
        outcomes = set(final_models.loc[final_models["specification"] == spec, "outcome"].unique())
        if outcomes != EXPECTED_OUTCOMES:
            errors.append(
                {
                    "check": f"outcomes_{spec}",
                    "message": "Each final model specification must include all expected outcomes.",
                    "details": {
                        "specification": spec,
                        "missing": sorted(EXPECTED_OUTCOMES - outcomes),
                        "extra": sorted(outcomes - EXPECTED_OUTCOMES),
                    },
                }
            )

    check_ids = set(alternatives["check_id"].unique())
    if check_ids != EXPECTED_CHECK_IDS:
        errors.append(
            {
                "check": "alternative_check_ids",
                "message": "Alternative-explanation table does not contain expected checks.",
                "details": {
                    "missing": sorted(EXPECTED_CHECK_IDS - check_ids),
                    "extra": sorted(check_ids - EXPECTED_CHECK_IDS),
                },
            }
        )

    lead_row = alternatives.loc[alternatives["check_id"] == "anticipation_lead6_placebo"]
    if lead_row.empty or (lead_row["target_parameter"] != "lead6_treatment_intensity_step6").any():
        errors.append(
            {
                "check": "lead_placebo_parameter",
                "message": "Lead placebo row must target the lead6_treatment_intensity_step6 parameter.",
            }
        )

    treatment_rows = alternatives.loc[alternatives["target_parameter"] == "treatment_intensity"]
    if len(treatment_rows) < 7:
        warnings.append(
            {
                "check": "treatment_row_count",
                "message": "Fewer treatment-intensity checks than expected.",
            }
        )

    cutoff_months = set(cutoff_sweep["cutoff_month"].astype(str).unique())
    if cutoff_months != EXPECTED_CUTOFFS:
        errors.append(
            {
                "check": "cutoff_months",
                "message": "Cutoff sweep does not match expected month set.",
                "details": {
                    "missing": sorted(EXPECTED_CUTOFFS - cutoff_months),
                    "extra": sorted(cutoff_months - EXPECTED_CUTOFFS),
                },
            }
        )

    if int(cutoff_sweep["is_true_cutoff"].sum()) != 1:
        errors.append(
            {
                "check": "true_cutoff_count",
                "message": "Cutoff sweep must have exactly one true intervention cutoff row.",
            }
        )

    if not np.isfinite(cutoff_sweep["coef_treatment_intensity"]).all():
        errors.append(
            {
                "check": "cutoff_coef_finite",
                "message": "Cutoff sweep coefficients must be finite.",
            }
        )

    step4_baseline_issues = step4_twfe.loc[
        (step4_twfe["outcome"] == "issues_opened")
        & (step4_twfe["specification"] == "baseline_fe_controls_clustered"),
        "coef_treatment_intensity",
    ].iloc[0]

    step6_baseline_issues = final_models.loc[
        (final_models["outcome"] == "issues_opened")
        & (final_models["specification"] == "baseline_step4_reference"),
        "coef_treatment_intensity",
    ].iloc[0]

    if not np.isclose(step4_baseline_issues, step6_baseline_issues, atol=1e-10):
        errors.append(
            {
                "check": "step4_step6_baseline_match",
                "message": "Step 6 baseline reference should exactly reproduce Step 4 baseline for issues_opened.",
                "details": {
                    "step4": float(step4_baseline_issues),
                    "step6": float(step6_baseline_issues),
                },
            }
        )

    if key_metrics.get("panel_rows") != 384 or key_metrics.get("ecosystem_count") != 8:
        errors.append(
            {
                "check": "key_metric_dimensions",
                "message": "Step 6 key metrics dimensions are inconsistent with expected panel dimensions.",
            }
        )

    required_keys = {
        "baseline_coef_issues_opened",
        "finalized_coef_issues_opened",
        "finalized_p_issues_opened",
        "lead_placebo_p",
        "true_cutoff_coef",
        "true_cutoff_rank_desc",
        "direction_consistent_treatment_checks",
        "total_treatment_checks",
    }
    if not required_keys.issubset(set(key_metrics.keys())):
        errors.append(
            {
                "check": "key_metrics_fields",
                "message": "Step 6 key metrics JSON is missing required fields.",
                "details": sorted(required_keys - set(key_metrics.keys())),
            }
        )

    required_manifest_outputs = {
        "outputs/step6_finalized_model_results.csv",
        "outputs/step6_alternative_explanations.csv",
        "outputs/step6_cutoff_sweep.csv",
        "outputs/step6_key_metrics.json",
        "outputs/step6_manifest.json",
        "outputs/step6_validation_report.json",
        "docs/STEP6_robustness_and_polish.md",
    }
    manifest_outputs = set(manifest.get("outputs", []))
    if not required_manifest_outputs.issubset(manifest_outputs):
        errors.append(
            {
                "check": "manifest_outputs",
                "message": "Step 6 manifest is missing required outputs.",
                "details": sorted(required_manifest_outputs - manifest_outputs),
            }
        )

    if not (DOCS / "STEP6_robustness_and_polish.md").exists():
        errors.append(
            {
                "check": "step6_doc_exists",
                "message": "Step 6 markdown changelog document was not generated.",
            }
        )

    summary = {
        "final_model_rows": int(len(final_models)),
        "alternative_rows": int(len(alternatives)),
        "cutoff_rows": int(len(cutoff_sweep)),
        "outcomes": sorted(set(final_models["outcome"].unique())),
        "check_ids": sorted(check_ids),
        "true_cutoff": cutoff_sweep.loc[cutoff_sweep["is_true_cutoff"], "cutoff_month"].astype(str).tolist(),
    }

    return {
        "status": "ok" if not errors else "error",
        "errors": errors,
        "warnings": warnings,
        "summary": summary,
    }


def main() -> None:
    report = validate()
    report_path = OUTPUTS / "step6_validation_report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {report_path}")
    if report["status"] != "ok":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
