from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from linearmodels.panel import PanelOLS

ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"
DOCS = ROOT / "docs"

FINAL_OUTCOMES = [
    "issues_opened",
    "median_close_days",
    "avg_first_response_hours",
    "backlog_open_end_month",
    "issue_burden_index",
]

CONTROL_Z_COLUMNS = [
    "active_repos_z",
    "questions_per_active_repo_z",
    "repo_scale_z",
]

TRUE_POST_START = pd.Timestamp("2022-12-01")
CUTOFF_SWEEP_DATES = [
    pd.Timestamp("2022-06-01"),
    pd.Timestamp("2022-09-01"),
    pd.Timestamp("2022-12-01"),
    pd.Timestamp("2023-03-01"),
    pd.Timestamp("2023-06-01"),
]


def load_panel() -> pd.DataFrame:
    panel = pd.read_csv(OUTPUTS / "step4_model_panel.csv", parse_dates=["month"])
    panel = panel.sort_values(["ecosystem", "month"]).reset_index(drop=True)
    return panel


def add_ecosystem_linear_trends(panel: pd.DataFrame, *, suffix: str = "step6") -> tuple[pd.DataFrame, list[str]]:
    frame = panel.copy()
    frame["month_centered"] = frame["month_index"] - frame["month_index"].mean()

    trend_cols: list[str] = []
    ecosystems = sorted(frame["ecosystem"].unique().tolist())
    reference_ecosystem = ecosystems[-1]

    for ecosystem in ecosystems:
        if ecosystem == reference_ecosystem:
            continue
        safe_name = ecosystem.replace("-", "_")
        col = f"trend_{safe_name}_{suffix}"
        frame[col] = (frame["ecosystem"] == ecosystem).astype(int) * frame["month_centered"]
        trend_cols.append(col)

    return frame, trend_cols


def fit_panel_ols(
    panel: pd.DataFrame,
    *,
    outcome: str,
    exog_columns: list[str],
    target_param: str,
    weight_column: str | None = None,
) -> dict:
    needed = ["ecosystem", "month", outcome] + exog_columns
    if weight_column:
        needed.append(weight_column)

    model_data = panel[needed].dropna().copy()
    frame = model_data.set_index(["ecosystem", "month"])

    model = PanelOLS(
        dependent=frame[outcome],
        exog=frame[exog_columns],
        weights=frame[weight_column] if weight_column else None,
        entity_effects=True,
        time_effects=True,
        drop_absorbed=True,
        check_rank=False,
    )
    fitted = model.fit(cov_type="clustered", cluster_entity=True)

    return {
        "coef": float(fitted.params[target_param]),
        "std_error": float(fitted.std_errors[target_param]),
        "t_stat": float(fitted.tstats[target_param]),
        "p_value": float(fitted.pvalues[target_param]),
        "n_obs": int(fitted.nobs),
        "r_squared": float(fitted.rsquared),
        "r_squared_within": float(fitted.rsquared_within),
        "r_squared_between": float(fitted.rsquared_between),
        "r_squared_overall": float(fitted.rsquared_overall),
    }


def build_finalized_model_results(panel: pd.DataFrame, trend_cols: list[str]) -> pd.DataFrame:
    rows: list[dict] = []

    specs = [
        {
            "specification": "baseline_step4_reference",
            "exog": ["treatment_intensity"] + CONTROL_Z_COLUMNS,
            "notes": "Step 4 reference: TWFE with standardized controls and ecosystem-clustered SE.",
        },
        {
            "specification": "finalized_trend_adjusted",
            "exog": ["treatment_intensity"] + CONTROL_Z_COLUMNS + trend_cols,
            "notes": "Finalized Step 6 model: TWFE + ecosystem-specific linear trends.",
        },
    ]

    for spec in specs:
        for outcome in FINAL_OUTCOMES:
            fit = fit_panel_ols(
                panel,
                outcome=outcome,
                exog_columns=spec["exog"],
                target_param="treatment_intensity",
            )
            outcome_std = float(panel[outcome].std(ddof=1))
            rows.append(
                {
                    "outcome": outcome,
                    "specification": spec["specification"],
                    "coef_treatment_intensity": fit["coef"],
                    "std_error": fit["std_error"],
                    "t_stat": fit["t_stat"],
                    "p_value": fit["p_value"],
                    "n_obs": fit["n_obs"],
                    "r_squared": fit["r_squared"],
                    "r_squared_within": fit["r_squared_within"],
                    "r_squared_between": fit["r_squared_between"],
                    "r_squared_overall": fit["r_squared_overall"],
                    "standardized_effect_sd": fit["coef"] / outcome_std if outcome_std > 0 else np.nan,
                    "notes": spec["notes"],
                }
            )

    out = pd.DataFrame(rows).sort_values(["specification", "outcome"]).reset_index(drop=True)
    return out


def build_alternative_explanations(panel: pd.DataFrame, trend_cols: list[str]) -> pd.DataFrame:
    rows: list[dict] = []

    def append_row(
        *,
        check_id: str,
        alternative_explanation: str,
        specification: str,
        target_parameter: str,
        fit: dict,
        notes: str,
    ) -> None:
        rows.append(
            {
                "check_id": check_id,
                "alternative_explanation": alternative_explanation,
                "specification": specification,
                "target_parameter": target_parameter,
                "coef": fit["coef"],
                "std_error": fit["std_error"],
                "t_stat": fit["t_stat"],
                "p_value": fit["p_value"],
                "n_obs": fit["n_obs"],
                "r_squared": fit["r_squared"],
                "r_squared_within": fit["r_squared_within"],
                "supports_main_direction": bool(fit["coef"] > 0),
                "notes": notes,
            }
        )

    baseline_fit = fit_panel_ols(
        panel,
        outcome="issues_opened",
        exog_columns=["treatment_intensity"] + CONTROL_Z_COLUMNS,
        target_param="treatment_intensity",
    )
    append_row(
        check_id="baseline_reference",
        alternative_explanation="Reference estimate for comparison",
        specification="step4_reference_controls",
        target_parameter="treatment_intensity",
        fit=baseline_fit,
        notes="Baseline TWFE treatment-intensity estimate from Step 4 controls-only model.",
    )

    final_fit = fit_panel_ols(
        panel,
        outcome="issues_opened",
        exog_columns=["treatment_intensity"] + CONTROL_Z_COLUMNS + trend_cols,
        target_param="treatment_intensity",
    )
    append_row(
        check_id="eco_specific_trends",
        alternative_explanation="Differential ecosystem trends drive the baseline result",
        specification="trend_adjusted_twfe",
        target_parameter="treatment_intensity",
        fit=final_fit,
        notes="Adds ecosystem-specific linear trends to absorb smooth differential drift.",
    )

    weighted_fit = fit_panel_ols(
        panel,
        outcome="issues_opened",
        exog_columns=["treatment_intensity"] + CONTROL_Z_COLUMNS + trend_cols,
        target_param="treatment_intensity",
        weight_column="active_repos_observed",
    )
    append_row(
        check_id="repo_size_weighting",
        alternative_explanation="Estimate is driven by small ecosystems only",
        specification="trend_adjusted_weighted_by_active_repos",
        target_parameter="treatment_intensity",
        fit=weighted_fit,
        notes="Uses active repository counts as analytic weights.",
    )

    lag_panel = panel.copy()
    lag_panel["lag_issues_opened_step6"] = (
        lag_panel.groupby("ecosystem", sort=False)["issues_opened"].shift(1)
    )
    lag_panel["lag_issues_opened_step6"] = lag_panel["lag_issues_opened_step6"].fillna(
        lag_panel["issues_opened"]
    )
    lag_fit = fit_panel_ols(
        lag_panel,
        outcome="issues_opened",
        exog_columns=["treatment_intensity"]
        + CONTROL_Z_COLUMNS
        + trend_cols
        + ["lag_issues_opened_step6"],
        target_param="treatment_intensity",
    )
    append_row(
        check_id="lagged_outcome",
        alternative_explanation="Persistence in issue flow, not treatment, explains the coefficient",
        specification="trend_adjusted_with_lagged_outcome",
        target_parameter="treatment_intensity",
        fit=lag_fit,
        notes="Adds lagged issues_opened to net out short-run autoregressive persistence.",
    )

    so_panel = panel.copy()
    so_panel["log1p_so_questions_step6"] = np.log1p(so_panel["stackoverflow_questions_month"])
    so_panel["post_x_log1p_so_questions_step6"] = (
        so_panel["post_chatgpt"] * so_panel["log1p_so_questions_step6"]
    )
    so_fit = fit_panel_ols(
        so_panel,
        outcome="issues_opened",
        exog_columns=["treatment_intensity"]
        + CONTROL_Z_COLUMNS
        + trend_cols
        + ["log1p_so_questions_step6", "post_x_log1p_so_questions_step6"],
        target_param="treatment_intensity",
    )
    append_row(
        check_id="so_activity_controls",
        alternative_explanation="Observed effect is fully explained by contemporaneous SO activity changes",
        specification="trend_adjusted_with_so_activity_controls",
        target_parameter="treatment_intensity",
        fit=so_fit,
        notes="Adds level and post interaction terms for Stack Overflow question volume.",
    )

    narrow_panel = panel.loc[panel["months_since_chatgpt"].between(-12, 12)].copy()
    narrow_panel, narrow_trend_cols = add_ecosystem_linear_trends(narrow_panel, suffix="narrow")
    narrow_fit = fit_panel_ols(
        narrow_panel,
        outcome="issues_opened",
        exog_columns=["treatment_intensity"] + CONTROL_Z_COLUMNS + narrow_trend_cols,
        target_param="treatment_intensity",
    )
    append_row(
        check_id="symmetric_window",
        alternative_explanation="Long-run drift outside the intervention neighborhood drives the estimate",
        specification="trend_adjusted_symmetric_window_12m",
        target_parameter="treatment_intensity",
        fit=narrow_fit,
        notes="Restricts sample to 12 months before and after intervention month.",
    )

    lead_panel = panel.copy()
    lead_panel["lead6_treatment_intensity_step6"] = (
        lead_panel.groupby("ecosystem", sort=False)["treatment_intensity"].shift(-6)
    )
    lead_panel["lead6_treatment_intensity_step6"] = lead_panel[
        "lead6_treatment_intensity_step6"
    ].fillna(0.0)

    lead_treat_fit = fit_panel_ols(
        lead_panel,
        outcome="issues_opened",
        exog_columns=["treatment_intensity", "lead6_treatment_intensity_step6"]
        + CONTROL_Z_COLUMNS
        + trend_cols,
        target_param="treatment_intensity",
    )
    append_row(
        check_id="anticipation_lead6_treatment",
        alternative_explanation="Lead contamination invalidates post-treatment attribution",
        specification="trend_adjusted_with_6m_lead",
        target_parameter="treatment_intensity",
        fit=lead_treat_fit,
        notes="Model includes 6-month lead placebo term alongside treatment intensity.",
    )

    lead_placebo_fit = fit_panel_ols(
        lead_panel,
        outcome="issues_opened",
        exog_columns=["treatment_intensity", "lead6_treatment_intensity_step6"]
        + CONTROL_Z_COLUMNS
        + trend_cols,
        target_param="lead6_treatment_intensity_step6",
    )
    append_row(
        check_id="anticipation_lead6_placebo",
        alternative_explanation="Lead contamination invalidates post-treatment attribution",
        specification="trend_adjusted_with_6m_lead",
        target_parameter="lead6_treatment_intensity_step6",
        fit=lead_placebo_fit,
        notes="Placebo lead coefficient should be near zero if no anticipatory effect.",
    )

    placebo_repo_fit = fit_panel_ols(
        panel,
        outcome="issues_per_active_repo",
        exog_columns=["treatment_intensity", "questions_per_active_repo_z", "repo_scale_z"] + trend_cols,
        target_param="treatment_intensity",
    )
    append_row(
        check_id="intensive_margin_ratio",
        alternative_explanation="Result is only from ecosystem size changes, not burden intensity",
        specification="trend_adjusted_ratio_outcome",
        target_parameter="treatment_intensity",
        fit=placebo_repo_fit,
        notes="Uses issues_per_active_repo as an intensive-margin burden outcome.",
    )

    out = pd.DataFrame(rows).sort_values(["check_id", "target_parameter"]).reset_index(drop=True)
    return out


def build_cutoff_sweep(panel: pd.DataFrame, trend_cols: list[str]) -> pd.DataFrame:
    rows: list[dict] = []

    for cutoff in CUTOFF_SWEEP_DATES:
        temp = panel.copy()
        temp["post_shift_step6"] = (temp["month"] >= cutoff).astype(int)
        temp["treatment_shift_step6"] = temp["post_shift_step6"] * temp["so_dependence_pre"]

        fit = fit_panel_ols(
            temp,
            outcome="issues_opened",
            exog_columns=["treatment_shift_step6"] + CONTROL_Z_COLUMNS + trend_cols,
            target_param="treatment_shift_step6",
        )

        rows.append(
            {
                "cutoff_month": cutoff.strftime("%Y-%m-%d"),
                "is_true_cutoff": bool(cutoff == TRUE_POST_START),
                "coef_treatment_intensity": fit["coef"],
                "std_error": fit["std_error"],
                "t_stat": fit["t_stat"],
                "p_value": fit["p_value"],
                "n_obs": fit["n_obs"],
                "r_squared_within": fit["r_squared_within"],
                "notes": "Shifted treatment-start robustness under trend-adjusted TWFE.",
            }
        )

    out = pd.DataFrame(rows).sort_values("cutoff_month").reset_index(drop=True)
    out["coef_rank_desc"] = out["coef_treatment_intensity"].rank(ascending=False, method="min").astype(int)
    return out


def build_key_metrics(
    panel: pd.DataFrame,
    final_models: pd.DataFrame,
    alternatives: pd.DataFrame,
    cutoff_sweep: pd.DataFrame,
) -> dict:
    baseline_issues = final_models.loc[
        (final_models["outcome"] == "issues_opened")
        & (final_models["specification"] == "baseline_step4_reference")
    ].iloc[0]

    final_issues = final_models.loc[
        (final_models["outcome"] == "issues_opened")
        & (final_models["specification"] == "finalized_trend_adjusted")
    ].iloc[0]

    final_response = final_models.loc[
        (final_models["outcome"] == "avg_first_response_hours")
        & (final_models["specification"] == "finalized_trend_adjusted")
    ].iloc[0]

    lag_row = alternatives.loc[alternatives["check_id"] == "lagged_outcome"].iloc[0]
    narrow_row = alternatives.loc[alternatives["check_id"] == "symmetric_window"].iloc[0]
    so_row = alternatives.loc[alternatives["check_id"] == "so_activity_controls"].iloc[0]
    lead_placebo_row = alternatives.loc[
        alternatives["check_id"] == "anticipation_lead6_placebo"
    ].iloc[0]

    strongest_cutoff = cutoff_sweep.sort_values("coef_treatment_intensity", ascending=False).iloc[0]
    true_cutoff_row = cutoff_sweep.loc[cutoff_sweep["is_true_cutoff"]].iloc[0]

    directional_rows = alternatives.loc[
        alternatives["target_parameter"] == "treatment_intensity"
    ]
    direction_consistent_count = int((directional_rows["coef"] > 0).sum())

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "panel_rows": int(len(panel)),
        "ecosystem_count": int(panel["ecosystem"].nunique()),
        "sample_start": str(panel["month"].min().date()),
        "sample_end": str(panel["month"].max().date()),
        "baseline_coef_issues_opened": float(baseline_issues["coef_treatment_intensity"]),
        "baseline_p_issues_opened": float(baseline_issues["p_value"]),
        "finalized_coef_issues_opened": float(final_issues["coef_treatment_intensity"]),
        "finalized_p_issues_opened": float(final_issues["p_value"]),
        "finalized_coef_avg_first_response_hours": float(
            final_response["coef_treatment_intensity"]
        ),
        "finalized_p_avg_first_response_hours": float(final_response["p_value"]),
        "lagged_outcome_coef_issues_opened": float(lag_row["coef"]),
        "lagged_outcome_p_issues_opened": float(lag_row["p_value"]),
        "symmetric_window_coef_issues_opened": float(narrow_row["coef"]),
        "symmetric_window_p_issues_opened": float(narrow_row["p_value"]),
        "so_activity_control_coef_issues_opened": float(so_row["coef"]),
        "so_activity_control_p_issues_opened": float(so_row["p_value"]),
        "lead_placebo_coef": float(lead_placebo_row["coef"]),
        "lead_placebo_p": float(lead_placebo_row["p_value"]),
        "cutoff_peak_month": str(strongest_cutoff["cutoff_month"]),
        "cutoff_peak_coef": float(strongest_cutoff["coef_treatment_intensity"]),
        "true_cutoff_coef": float(true_cutoff_row["coef_treatment_intensity"]),
        "true_cutoff_rank_desc": int(true_cutoff_row["coef_rank_desc"]),
        "direction_consistent_treatment_checks": direction_consistent_count,
        "total_treatment_checks": int(len(directional_rows)),
    }


def f3(value: float) -> str:
    return f"{value:.3f}"


def f4(value: float) -> str:
    return f"{value:.4f}"


def build_step6_markdown(
    final_models: pd.DataFrame,
    alternatives: pd.DataFrame,
    cutoff_sweep: pd.DataFrame,
) -> str:
    baseline_issues = final_models.loc[
        (final_models["outcome"] == "issues_opened")
        & (final_models["specification"] == "baseline_step4_reference")
    ].iloc[0]
    final_issues = final_models.loc[
        (final_models["outcome"] == "issues_opened")
        & (final_models["specification"] == "finalized_trend_adjusted")
    ].iloc[0]
    final_resp = final_models.loc[
        (final_models["outcome"] == "avg_first_response_hours")
        & (final_models["specification"] == "finalized_trend_adjusted")
    ].iloc[0]

    lag_row = alternatives.loc[alternatives["check_id"] == "lagged_outcome"].iloc[0]
    narrow_row = alternatives.loc[alternatives["check_id"] == "symmetric_window"].iloc[0]
    so_row = alternatives.loc[alternatives["check_id"] == "so_activity_controls"].iloc[0]
    lead_placebo_row = alternatives.loc[
        alternatives["check_id"] == "anticipation_lead6_placebo"
    ].iloc[0]
    ratio_row = alternatives.loc[alternatives["check_id"] == "intensive_margin_ratio"].iloc[0]

    cutoff_true = cutoff_sweep.loc[cutoff_sweep["is_true_cutoff"]].iloc[0]
    cutoff_peak = cutoff_sweep.sort_values("coef_treatment_intensity", ascending=False).iloc[0]

    markdown = f"""# Step 6 Robustness and Polish

## QA changelog (what was run)
- Re-estimated the Step 4 treatment-intensity model with **ecosystem-specific linear trends** to finalize the baseline specification for Step 6.
- Refit all core outcomes under the finalized specification and exported one consolidated model table.
- Ran targeted alternative-explanation checks for the main finding (`issues_opened`):
  1. active-repo weighting,
  2. lagged outcome control,
  3. Stack Overflow activity controls,
  4. symmetric ±12 month window,
  5. 6-month lead placebo,
  6. intensive-margin ratio outcome.
- Ran a shifted intervention cutoff sweep (five candidate cutoff months) to test whether the effect is concentrated around the intended intervention timing.

## Finalized model decision
Finalized Step 6 model: **TWFE with standardized controls + ecosystem-specific linear trends**, ecosystem-clustered SE.

For `issues_opened`:
- Step 4 reference coefficient: {f4(float(baseline_issues['coef_treatment_intensity']))} (p={f4(float(baseline_issues['p_value']))})
- Step 6 finalized coefficient: {f4(float(final_issues['coef_treatment_intensity']))} (p={f4(float(final_issues['p_value']))})
- Standardized finalized effect: {f3(float(final_issues['standardized_effect_sd']))} SD

For `avg_first_response_hours` under the finalized model:
- Coefficient: {f4(float(final_resp['coef_treatment_intensity']))} (p={f4(float(final_resp['p_value']))})

## Alternative-explanation robustness summary (main finding: `issues_opened`)
- Lagged-outcome control: {f4(float(lag_row['coef']))} (p={f4(float(lag_row['p_value']))})
- Symmetric ±12 month window: {f4(float(narrow_row['coef']))} (p={f4(float(narrow_row['p_value']))})
- SO-activity controls: {f4(float(so_row['coef']))} (p={f4(float(so_row['p_value']))})
- 6-month lead placebo term: {f4(float(lead_placebo_row['coef']))} (p={f4(float(lead_placebo_row['p_value']))})
- Intensive-margin (`issues_per_active_repo`) outcome: {f4(float(ratio_row['coef']))} (p={f4(float(ratio_row['p_value']))})

Interpretation for QA: most checks preserve a positive treatment-intensity direction, while adding direct SO-activity controls attenuates precision, consistent with potential channel overlap/mediation rather than a pure contradiction.

## Cutoff sweep diagnostic
Shifted-cutoff estimates (trend-adjusted model) are reported in `outputs/step6_cutoff_sweep.csv`.

- Coefficient at intended cutoff (2022-12-01): {f4(float(cutoff_true['coef_treatment_intensity']))} (rank={int(cutoff_true['coef_rank_desc'])} among tested cutoffs)
- Highest coefficient among tested cutoffs: {str(cutoff_peak['cutoff_month'])} with {f4(float(cutoff_peak['coef_treatment_intensity']))}

## Produced artifacts
- `outputs/step6_finalized_model_results.csv`
- `outputs/step6_alternative_explanations.csv`
- `outputs/step6_cutoff_sweep.csv`
- `outputs/step6_key_metrics.json`
- `outputs/step6_manifest.json`
- `outputs/step6_validation_report.json`
- `docs/STEP6_robustness_and_polish.md`

## Interpretation boundary
All results remain synthetic and are intended for pipeline QA, specification stress-testing, and reproducibility checks. They are not empirical claims from live public-source data.

## Reproduction
From the repository root:

```bash
python3 -m venv .venv-step6
source .venv-step6/bin/activate
pip install -r requirements-step6.txt
python scripts/run_step6_finalize.py
```
"""
    return markdown


def build_manifest(panel: pd.DataFrame) -> dict:
    return {
        "artifact": "Step 6 finalized model + alternative-explanation robustness package",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_panel": "outputs/step4_model_panel.csv",
        "sample_start": str(panel["month"].min().date()),
        "sample_end": str(panel["month"].max().date()),
        "n_rows": int(len(panel)),
        "n_ecosystems": int(panel["ecosystem"].nunique()),
        "synthetic_note": (
            "Step 6 keeps the synthetic-only boundary and focuses on specification finalization and "
            "alternative-explanation robustness diagnostics."
        ),
        "outputs": [
            "outputs/step6_finalized_model_results.csv",
            "outputs/step6_alternative_explanations.csv",
            "outputs/step6_cutoff_sweep.csv",
            "outputs/step6_key_metrics.json",
            "outputs/step6_manifest.json",
            "outputs/step6_validation_report.json",
            "docs/STEP6_robustness_and_polish.md",
        ],
    }


def main() -> None:
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)

    panel = load_panel()
    panel_with_trends, trend_cols = add_ecosystem_linear_trends(panel)

    final_models = build_finalized_model_results(panel_with_trends, trend_cols)
    alternatives = build_alternative_explanations(panel_with_trends, trend_cols)
    cutoff_sweep = build_cutoff_sweep(panel_with_trends, trend_cols)
    key_metrics = build_key_metrics(panel_with_trends, final_models, alternatives, cutoff_sweep)
    markdown = build_step6_markdown(final_models, alternatives, cutoff_sweep)
    manifest = build_manifest(panel_with_trends)

    final_models.to_csv(OUTPUTS / "step6_finalized_model_results.csv", index=False)
    alternatives.to_csv(OUTPUTS / "step6_alternative_explanations.csv", index=False)
    cutoff_sweep.to_csv(OUTPUTS / "step6_cutoff_sweep.csv", index=False)
    (OUTPUTS / "step6_key_metrics.json").write_text(
        json.dumps(key_metrics, indent=2) + "\n", encoding="utf-8"
    )
    (OUTPUTS / "step6_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    (DOCS / "STEP6_robustness_and_polish.md").write_text(markdown, encoding="utf-8")

    print(f"Wrote {OUTPUTS / 'step6_finalized_model_results.csv'}")
    print(f"Wrote {OUTPUTS / 'step6_alternative_explanations.csv'}")
    print(f"Wrote {OUTPUTS / 'step6_cutoff_sweep.csv'}")
    print(f"Wrote {OUTPUTS / 'step6_key_metrics.json'}")
    print(f"Wrote {OUTPUTS / 'step6_manifest.json'}")
    print(f"Wrote {DOCS / 'STEP6_robustness_and_polish.md'}")


if __name__ == "__main__":
    main()
