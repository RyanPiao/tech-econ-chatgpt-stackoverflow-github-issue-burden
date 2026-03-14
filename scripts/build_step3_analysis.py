from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"
POST_START = pd.Timestamp("2022-12-01")
PRIMARY_OUTCOMES = [
    "issues_opened",
    "median_close_days",
    "avg_first_response_hours",
    "backlog_open_end_month",
]
DERIVED_OUTCOMES = [
    "issues_per_active_repo",
    "backlog_per_active_repo",
    "questions_per_active_repo",
    "issue_burden_index",
]


def month_distance(month: pd.Series, reference: pd.Timestamp) -> pd.Series:
    return (month.dt.year - reference.year) * 12 + (month.dt.month - reference.month)


def load_step2_panel() -> pd.DataFrame:
    panel = pd.read_csv(OUTPUTS / "step2_synthetic_panel.csv", parse_dates=["month"])

    eco_exposure = (
        panel[["ecosystem", "so_dependence_pre"]]
        .drop_duplicates()
        .sort_values("so_dependence_pre")
        .reset_index(drop=True)
    )
    eco_exposure["exposure_bucket"] = pd.qcut(
        eco_exposure["so_dependence_pre"],
        q=3,
        labels=["low", "mid", "high"],
    )

    panel = panel.merge(eco_exposure, on=["ecosystem", "so_dependence_pre"], how="left")
    panel["months_since_chatgpt"] = month_distance(panel["month"], POST_START)
    panel["post_period_label"] = np.where(panel["post_chatgpt"] == 1, "post", "pre")
    panel["high_exposure"] = (panel["exposure_bucket"] == "high").astype(int)

    panel["issues_per_active_repo"] = panel["issues_opened"] / panel["active_repos_observed"]
    panel["backlog_per_active_repo"] = (
        panel["backlog_open_end_month"] / panel["active_repos_observed"]
    )
    panel["questions_per_active_repo"] = (
        panel["stackoverflow_questions_month"] / panel["active_repos_observed"]
    )
    panel["avg_first_response_days"] = panel["avg_first_response_hours"] / 24.0
    panel["log_issues_opened"] = np.log1p(panel["issues_opened"])
    panel["log_backlog_open_end_month"] = np.log1p(panel["backlog_open_end_month"])

    scaler = StandardScaler()
    burden_inputs = panel[
        [
            "issues_opened",
            "median_close_days",
            "avg_first_response_hours",
            "backlog_per_active_repo",
        ]
    ]
    burden_z = scaler.fit_transform(burden_inputs)
    panel["issue_burden_index"] = burden_z.mean(axis=1)
    panel["month"] = panel["month"].dt.strftime("%Y-%m-%d")
    return panel


def build_ecosystem_pre_post_summary(panel: pd.DataFrame) -> pd.DataFrame:
    metric_cols = PRIMARY_OUTCOMES + DERIVED_OUTCOMES
    static_cols = [
        "stack_overflow_tag_anchor",
        "github_repo_group",
        "representative_repo_count",
        "so_dependence_pre",
        "exposure_bucket",
    ]

    base = panel.groupby("ecosystem")[static_cols].first()
    pre = (
        panel.loc[panel["post_chatgpt"] == 0]
        .groupby("ecosystem")[metric_cols]
        .mean()
        .add_prefix("pre_")
    )
    post = (
        panel.loc[panel["post_chatgpt"] == 1]
        .groupby("ecosystem")[metric_cols]
        .mean()
        .add_prefix("post_")
    )

    summary = base.join(pre).join(post).reset_index()

    for col in metric_cols:
        summary[f"delta_{col}"] = summary[f"post_{col}"] - summary[f"pre_{col}"]

    summary["pct_change_issues_opened"] = (
        summary["delta_issues_opened"] / summary["pre_issues_opened"]
    )
    summary["pct_change_backlog_open_end_month"] = (
        summary["delta_backlog_open_end_month"] / summary["pre_backlog_open_end_month"]
    )

    return summary.sort_values("so_dependence_pre", ascending=False).reset_index(drop=True)


def build_event_time_summary(panel: pd.DataFrame) -> pd.DataFrame:
    event_summary = (
        panel.groupby(["months_since_chatgpt", "exposure_bucket"], observed=True)
        .agg(
            ecosystems=("ecosystem", "nunique"),
            mean_issues_opened=("issues_opened", "mean"),
            mean_issues_per_active_repo=("issues_per_active_repo", "mean"),
            mean_backlog_per_active_repo=("backlog_per_active_repo", "mean"),
            mean_avg_first_response_hours=("avg_first_response_hours", "mean"),
            mean_issue_burden_index=("issue_burden_index", "mean"),
        )
        .reset_index()
        .sort_values(["months_since_chatgpt", "exposure_bucket"])
        .reset_index(drop=True)
    )
    return event_summary


def build_parallel_trend_diagnostics(panel: pd.DataFrame) -> pd.DataFrame:
    pre = panel.loc[panel["post_chatgpt"] == 0].copy()
    pre["month_centered"] = pre["month_index"] - pre["month_index"].min()

    results = []
    for outcome in PRIMARY_OUTCOMES + ["issue_burden_index", "issues_per_active_repo"]:
        formula = (
            f"{outcome} ~ month_centered + so_dependence_pre + "
            "month_centered:so_dependence_pre + C(ecosystem)"
        )
        fit = smf.ols(formula, data=pre).fit(cov_type="HC1")
        key = "month_centered:so_dependence_pre"
        results.append(
            {
                "outcome": outcome,
                "coef_exposure_pretrend": float(fit.params[key]),
                "std_error": float(fit.bse[key]),
                "p_value": float(fit.pvalues[key]),
                "r_squared": float(fit.rsquared),
                "n_obs": int(fit.nobs),
            }
        )

    return pd.DataFrame(results).sort_values("outcome").reset_index(drop=True)


def build_exposure_change_summary(ecosystem_summary: pd.DataFrame) -> pd.DataFrame:
    rows = []
    outcomes = PRIMARY_OUTCOMES + ["issues_per_active_repo", "backlog_per_active_repo", "issue_burden_index"]

    for outcome in outcomes:
        change_col = f"delta_{outcome}"
        fit = smf.ols(f"Q('{change_col}') ~ so_dependence_pre", data=ecosystem_summary).fit()
        rows.append(
            {
                "outcome": outcome,
                "corr_exposure_vs_change": float(
                    ecosystem_summary["so_dependence_pre"].corr(ecosystem_summary[change_col])
                ),
                "slope_change_per_unit_exposure": float(fit.params["so_dependence_pre"]),
                "intercept": float(fit.params["Intercept"]),
                "r_squared": float(fit.rsquared),
            }
        )

    return pd.DataFrame(rows).sort_values("outcome").reset_index(drop=True)


def build_manifest(panel: pd.DataFrame) -> dict:
    return {
        "artifact": "Step 3 synthetic exploratory analysis package",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_panel": "outputs/step2_synthetic_panel.csv",
        "sample_start": panel["month"].min(),
        "sample_end": panel["month"].max(),
        "n_rows": int(len(panel)),
        "n_ecosystems": int(panel["ecosystem"].nunique()),
        "synthetic_note": (
            "Step 3 continues to use the synthetic panel so that exploratory analysis, derived features, and "
            "identification diagnostics can be inspected without presenting synthetic patterns as empirical facts."
        ),
        "outputs": [
            "outputs/step3_identification_ready_panel.csv",
            "outputs/step3_ecosystem_pre_post_summary.csv",
            "outputs/step3_event_time_exposure_summary.csv",
            "outputs/step3_parallel_trend_diagnostics.csv",
            "outputs/step3_exposure_change_summary.csv",
            "outputs/step3_manifest.json",
        ],
    }


def main() -> None:
    OUTPUTS.mkdir(parents=True, exist_ok=True)

    panel = load_step2_panel()
    ecosystem_summary = build_ecosystem_pre_post_summary(panel)
    event_summary = build_event_time_summary(panel)
    diagnostics = build_parallel_trend_diagnostics(panel)
    exposure_change = build_exposure_change_summary(ecosystem_summary)
    manifest = build_manifest(panel)

    panel.to_csv(OUTPUTS / "step3_identification_ready_panel.csv", index=False)
    ecosystem_summary.to_csv(OUTPUTS / "step3_ecosystem_pre_post_summary.csv", index=False)
    event_summary.to_csv(OUTPUTS / "step3_event_time_exposure_summary.csv", index=False)
    diagnostics.to_csv(OUTPUTS / "step3_parallel_trend_diagnostics.csv", index=False)
    exposure_change.to_csv(OUTPUTS / "step3_exposure_change_summary.csv", index=False)
    (OUTPUTS / "step3_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )

    print(f"Wrote {OUTPUTS / 'step3_identification_ready_panel.csv'}")
    print(f"Wrote {OUTPUTS / 'step3_ecosystem_pre_post_summary.csv'}")
    print(f"Wrote {OUTPUTS / 'step3_event_time_exposure_summary.csv'}")
    print(f"Wrote {OUTPUTS / 'step3_parallel_trend_diagnostics.csv'}")
    print(f"Wrote {OUTPUTS / 'step3_exposure_change_summary.csv'}")
    print(f"Wrote {OUTPUTS / 'step3_manifest.json'}")


if __name__ == "__main__":
    main()
