from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"

EXPECTED_BASE_OUTCOMES = {
    "issues_opened",
    "median_close_days",
    "avg_first_response_hours",
    "backlog_open_end_month",
    "issue_burden_index",
}

EXPECTED_HETERO_OUTCOMES = {
    "issues_opened",
    "avg_first_response_hours",
    "backlog_open_end_month",
    "issue_burden_index",
}

EXPECTED_DYNAMIC_EVENT_MONTHS = {k for k in range(-12, 19) if k != -1}
EXPECTED_HETERO_DIMS = {
    "pre_period_active_repo_scale",
    "pre_period_backlog_per_repo",
    "pre_period_issue_burden_index",
}
EXPECTED_HETERO_MODEL_TYPES = {"interaction", "split_sample"}
EXPECTED_SENSITIVITY_SPECS = {
    "baseline_clustered_entity",
    "clustered_entity_time",
    "robust_white",
    "kernel_bartlett_bw4",
    "weighted_clustered_entity",
    "winsorized_p01_p99_clustered_entity",
    "log1p_outcome_clustered_entity",
    "asinh_outcome_clustered_entity",
    "permutation_inference_300",
}


def validate() -> dict:
    errors = []
    warnings = []

    sensitivity = pd.read_csv(OUTPUTS / "step5_sensitivity_checks.csv")
    dynamic = pd.read_csv(OUTPUTS / "step5_dynamic_analysis.csv")
    heterogeneity = pd.read_csv(OUTPUTS / "step5_heterogeneity_analysis.csv")
    key_metrics = json.loads((OUTPUTS / "step5_key_metrics.json").read_text(encoding="utf-8"))
    manifest = json.loads((OUTPUTS / "step5_manifest.json").read_text(encoding="utf-8"))

    step4_twfe = pd.read_csv(OUTPUTS / "step4_twfe_models.csv")

    if not EXPECTED_SENSITIVITY_SPECS.issubset(set(sensitivity["specification"].unique())):
        errors.append(
            {
                "check": "sensitivity_specs",
                "message": "Sensitivity table is missing required specifications.",
                "details": sorted(
                    EXPECTED_SENSITIVITY_SPECS - set(sensitivity["specification"].unique())
                ),
            }
        )

    baseline_rows = sensitivity.loc[
        sensitivity["specification"] == "baseline_clustered_entity"
    ]
    if set(baseline_rows["outcome"].unique()) != EXPECTED_BASE_OUTCOMES:
        errors.append(
            {
                "check": "baseline_sensitivity_outcomes",
                "message": "Baseline sensitivity specification should cover all core outcomes.",
            }
        )

    for outcome in EXPECTED_BASE_OUTCOMES:
        dyn_outcome = dynamic.loc[dynamic["outcome"] == outcome]
        if set(dyn_outcome["event_month"].tolist()) != EXPECTED_DYNAMIC_EVENT_MONTHS:
            errors.append(
                {
                    "check": f"dynamic_event_support_{outcome}",
                    "message": "Dynamic analysis event support does not match expected lead/lag window.",
                }
            )

    dynamic_outcomes = set(dynamic["outcome"].unique())
    if dynamic_outcomes != EXPECTED_BASE_OUTCOMES:
        errors.append(
            {
                "check": "dynamic_outcomes",
                "message": "Dynamic analysis does not cover the expected outcomes.",
            }
        )

    hetero_dims = set(heterogeneity["heterogeneity_dimension"].unique())
    if hetero_dims != EXPECTED_HETERO_DIMS:
        errors.append(
            {
                "check": "heterogeneity_dimensions",
                "message": "Heterogeneity output does not cover expected dimensions.",
                "details": {
                    "missing": sorted(EXPECTED_HETERO_DIMS - hetero_dims),
                    "extra": sorted(hetero_dims - EXPECTED_HETERO_DIMS),
                },
            }
        )

    hetero_model_types = set(heterogeneity["model_type"].unique())
    if hetero_model_types != EXPECTED_HETERO_MODEL_TYPES:
        errors.append(
            {
                "check": "heterogeneity_model_types",
                "message": "Heterogeneity output must include interaction and split_sample models.",
            }
        )

    hetero_outcomes = set(heterogeneity["outcome"].unique())
    if hetero_outcomes != EXPECTED_HETERO_OUTCOMES:
        errors.append(
            {
                "check": "heterogeneity_outcomes",
                "message": "Heterogeneity output does not cover expected outcomes.",
            }
        )

    # split-sample must have high + low subgroup rows for each dimension/outcome
    split_rows = heterogeneity.loc[heterogeneity["model_type"] == "split_sample"]
    for dim in EXPECTED_HETERO_DIMS:
        for outcome in EXPECTED_HETERO_OUTCOMES:
            sample = split_rows.loc[
                (split_rows["heterogeneity_dimension"] == dim)
                & (split_rows["outcome"] == outcome)
            ]
            if set(sample["subgroup"].tolist()) != {"high", "low"}:
                errors.append(
                    {
                        "check": f"split_support_{dim}_{outcome}",
                        "message": "Split-sample rows must contain both high and low groups.",
                    }
                )

    interaction_rows = heterogeneity.loc[heterogeneity["model_type"] == "interaction"]
    if interaction_rows["coef_interaction"].isna().any():
        errors.append(
            {
                "check": "interaction_nan_coef",
                "message": "Interaction rows must include interaction coefficients.",
            }
        )

    perm_rows = sensitivity.loc[sensitivity["specification"] == "permutation_inference_300"]
    if perm_rows.empty:
        errors.append(
            {
                "check": "permutation_rows",
                "message": "Permutation sensitivity rows are missing.",
            }
        )
    else:
        if (perm_rows["permutation_draws"] != 300).any():
            errors.append(
                {
                    "check": "permutation_draws",
                    "message": "Permutation rows must report 300 draws.",
                }
            )
        if ((perm_rows["permutation_empirical_p_value"] < 0) | (perm_rows["permutation_empirical_p_value"] > 1)).any():
            errors.append(
                {
                    "check": "permutation_p_bounds",
                    "message": "Permutation empirical p-values must be in [0, 1].",
                }
            )

    # check baseline issues coefficient aligns with Step 4 baseline for reproducibility
    step4_baseline_issues = step4_twfe.loc[
        (step4_twfe["outcome"] == "issues_opened")
        & (step4_twfe["specification"] == "baseline_fe_controls_clustered"),
        "coef_treatment_intensity",
    ].iloc[0]

    step5_baseline_issues = sensitivity.loc[
        (sensitivity["outcome"] == "issues_opened")
        & (sensitivity["specification"] == "baseline_clustered_entity"),
        "coef_treatment_intensity",
    ].iloc[0]

    if not np.isclose(step4_baseline_issues, step5_baseline_issues, atol=1e-10):
        errors.append(
            {
                "check": "step4_step5_baseline_match",
                "message": "Step 5 baseline should exactly reproduce Step 4 baseline for issues_opened.",
                "details": {
                    "step4": float(step4_baseline_issues),
                    "step5": float(step5_baseline_issues),
                },
            }
        )

    if key_metrics.get("panel_rows") != 384 or key_metrics.get("ecosystem_count") != 8:
        errors.append(
            {
                "check": "key_metrics_dimensions",
                "message": "Step 5 key metrics dimensions are inconsistent with panel dimensions.",
            }
        )

    required_manifest_outputs = {
        "outputs/step5_sensitivity_checks.csv",
        "outputs/step5_dynamic_analysis.csv",
        "outputs/step5_heterogeneity_analysis.csv",
        "outputs/step5_key_metrics.json",
        "outputs/step5_manifest.json",
        "outputs/step5_validation_report.json",
        "docs/STEP5_robustness_checks.md",
    }
    manifest_outputs = set(manifest.get("outputs", []))
    if not required_manifest_outputs.issubset(manifest_outputs):
        errors.append(
            {
                "check": "manifest_outputs",
                "message": "Step 5 manifest is missing required outputs.",
                "details": sorted(required_manifest_outputs - manifest_outputs),
            }
        )

    if len(sensitivity) < 30:
        warnings.append(
            {
                "check": "sensitivity_rows",
                "message": "Sensitivity output is smaller than expected; verify full spec coverage.",
            }
        )

    summary = {
        "sensitivity_rows": int(len(sensitivity)),
        "dynamic_rows": int(len(dynamic)),
        "heterogeneity_rows": int(len(heterogeneity)),
        "dynamic_outcomes": sorted(dynamic_outcomes),
        "heterogeneity_dimensions": sorted(hetero_dims),
        "permutation_rows": int(len(perm_rows)),
    }

    return {
        "status": "ok" if not errors else "error",
        "errors": errors,
        "warnings": warnings,
        "summary": summary,
    }


def main() -> None:
    report = validate()
    report_path = OUTPUTS / "step5_validation_report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {report_path}")
    if report["status"] != "ok":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
