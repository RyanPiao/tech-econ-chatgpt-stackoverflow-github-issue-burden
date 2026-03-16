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
DOCS = ROOT / "docs"
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


def build_ecosystem_summary(panel: pd.DataFrame) -> pd.DataFrame:
    summary = (
        panel.groupby("ecosystem", as_index=False)
        .agg(
            so_dependence_pre=("so_dependence_pre", "first"),
            exposure_bucket=("exposure_bucket", "first"),
            avg_issues_opened=("issues_opened", "mean"),
            avg_close_days=("median_close_days", "mean"),
            avg_response_hours=("avg_first_response_hours", "mean"),
            avg_backlog=("backlog_open_end_month", "mean"),
            avg_issues_per_active_repo=("issues_per_active_repo", "mean"),
            avg_backlog_per_active_repo=("backlog_per_active_repo", "mean"),
            avg_issue_burden_index=("issue_burden_index", "mean"),
        )
        .sort_values("so_dependence_pre", ascending=False)
        .reset_index(drop=True)
    )
    return summary


def build_binary_prepost_summary(panel: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        panel.groupby(["high_exposure", "post_period_label"], as_index=False)
        .agg(
            mean_issues_opened=("issues_opened", "mean"),
            mean_close_days=("median_close_days", "mean"),
            mean_response_hours=("avg_first_response_hours", "mean"),
            mean_backlog=("backlog_open_end_month", "mean"),
            mean_issues_per_active_repo=("issues_per_active_repo", "mean"),
            mean_backlog_per_active_repo=("backlog_per_active_repo", "mean"),
            mean_issue_burden_index=("issue_burden_index", "mean"),
        )
    )
    grouped["dependence_group"] = grouped["high_exposure"].map(
        {1: "High pre-period Stack Overflow dependence", 0: "Low/mid pre-period Stack Overflow dependence"}
    )
    grouped = grouped.drop(columns=["high_exposure"])
    return grouped[
        [
            "dependence_group",
            "post_period_label",
            "mean_issues_opened",
            "mean_close_days",
            "mean_response_hours",
            "mean_backlog",
            "mean_issues_per_active_repo",
            "mean_backlog_per_active_repo",
            "mean_issue_burden_index",
        ]
    ].sort_values(["dependence_group", "post_period_label"]).reset_index(drop=True)


def build_twfe_preview(panel: pd.DataFrame) -> pd.DataFrame:
    results = []
    for outcome in PRIMARY_OUTCOMES:
        fit = smf.ols(
            f"{outcome} ~ treatment_intensity + C(ecosystem) + C(month)",
            data=panel,
        ).fit(cov_type="HC1")
        results.append(
            {
                "outcome": outcome,
                "coef_treatment_intensity": float(fit.params["treatment_intensity"]),
                "se_hc1": float(fit.bse["treatment_intensity"]),
                "t_stat": float(fit.tvalues["treatment_intensity"]),
                "p_value": float(fit.pvalues["treatment_intensity"]),
                "n_obs": int(fit.nobs),
                "r_squared": float(fit.rsquared),
            }
        )
    return pd.DataFrame(results).sort_values("outcome").reset_index(drop=True)


def build_key_metrics(panel: pd.DataFrame) -> dict:
    high = panel.loc[panel["high_exposure"] == 1]
    low_mid = panel.loc[panel["high_exposure"] == 0]

    def prepost_change(frame: pd.DataFrame, column: str) -> float:
        pre = frame.loc[frame["post_chatgpt"] == 0, column].mean()
        post = frame.loc[frame["post_chatgpt"] == 1, column].mean()
        return float(post - pre)

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "panel_rows": int(len(panel)),
        "ecosystem_count": int(panel["ecosystem"].nunique()),
        "sample_start": str(pd.to_datetime(panel["month"]).min().date()),
        "sample_end": str(pd.to_datetime(panel["month"]).max().date()),
        "high_exposure_prepost_change_issues": prepost_change(high, "issues_opened"),
        "low_mid_exposure_prepost_change_issues": prepost_change(low_mid, "issues_opened"),
        "high_exposure_prepost_change_backlog": prepost_change(high, "backlog_open_end_month"),
        "low_mid_exposure_prepost_change_backlog": prepost_change(low_mid, "backlog_open_end_month"),
        "high_exposure_prepost_change_close_days": prepost_change(high, "median_close_days"),
        "low_mid_exposure_prepost_change_close_days": prepost_change(low_mid, "median_close_days"),
    }




def format_float(value: float, digits: int = 3) -> str:
    return f"{value:.{digits}f}"


def build_step3_markdown(
    ecosystem_pre_post: pd.DataFrame,
    twfe_preview: pd.DataFrame,
) -> str:
    high = ecosystem_pre_post.loc[ecosystem_pre_post["exposure_bucket"] == "high"]
    low = ecosystem_pre_post.loc[ecosystem_pre_post["exposure_bucket"].isin(["low", "mid"])]

    def mean_delta(frame: pd.DataFrame, col: str) -> float:
        return float(frame[col].mean())

    high_issue = mean_delta(high, "delta_issues_opened")
    low_issue = mean_delta(low, "delta_issues_opened")
    high_backlog = mean_delta(high, "delta_backlog_open_end_month")
    low_backlog = mean_delta(low, "delta_backlog_open_end_month")
    high_close = mean_delta(high, "delta_median_close_days")
    low_close = mean_delta(low, "delta_median_close_days")

    coef_map = twfe_preview.set_index("outcome").to_dict("index")

    markdown = f"""# Step 3 Exploratory Analysis

## Purpose
Step 3 moves the project from schema validation into first-pass empirical exploration using the synthetic ecosystem-month panel defined in Step 2. The goal here is not to claim final causal results, but to check whether the panel behaves in a way that is consistent with the proposed identification strategy and whether a fixed-effects specification can recover interpretable directional patterns.

## Data used
This step uses the synthetic panel in `outputs/step2_synthetic_panel.csv`, covering 8 technology ecosystems observed monthly from 2021-01 through 2024-12.

The panel remains synthetic on purpose. That keeps the workflow honest: readers can inspect the design logic, variable construction, and model code without mistaking the current outputs for real-world evidence.

## What was produced
Step 3 adds these exploratory artifacts:

- `outputs/step3_identification_ready_panel.csv`
- `outputs/step3_ecosystem_pre_post_summary.csv`
- `outputs/step3_event_time_exposure_summary.csv`
- `outputs/step3_parallel_trend_diagnostics.csv`
- `outputs/step3_exposure_change_summary.csv`
- `outputs/step3_ecosystem_summary.csv`
- `outputs/step3_prepost_summary.csv`
- `outputs/step3_twfe_preview.csv`
- `outputs/step3_key_metrics.json`
- `outputs/step3_manifest.json`
- `docs/STEP3_exploratory_analysis.md`

It also uses the reproducible runner:

- `scripts/run_step3_eda.py`

## Descriptive patterns
Using the exposure buckets derived from pre-period Stack Overflow dependence:

- High-dependence ecosystems show a larger post-period increase in issues opened (`+{format_float(high_issue)}`) than low/mid-dependence ecosystems (`+{format_float(low_issue)}`).
- High-dependence ecosystems also show a somewhat larger increase in month-end issue backlog (`+{format_float(high_backlog)}`) than low/mid-dependence ecosystems (`+{format_float(low_backlog)}`).
- Median issue close duration rises more in the high-dependence group (`+{format_float(high_close)}` days) than in the low/mid-dependence group (`+{format_float(low_close)}` days).

These differences are modest, but they move in the hypothesized direction: ecosystems that relied more heavily on Stack Overflow before the ChatGPT shock experience somewhat greater pressure on GitHub issue management afterward.

## Fixed-effects preview
A first-pass two-way fixed-effects preview estimates:

`outcome ~ treatment_intensity + ecosystem fixed effects + month fixed effects`

where `treatment_intensity = post_chatgpt × so_dependence_pre`.

Preview coefficients:

- `issues_opened`: `{format_float(coef_map['issues_opened']['coef_treatment_intensity'], 4)}` (HC1 s.e. `{format_float(coef_map['issues_opened']['se_hc1'], 4)}`, p=`{format_float(coef_map['issues_opened']['p_value'], 6)}`)
- `median_close_days`: `{format_float(coef_map['median_close_days']['coef_treatment_intensity'], 4)}` (HC1 s.e. `{format_float(coef_map['median_close_days']['se_hc1'], 4)}`, p=`{format_float(coef_map['median_close_days']['p_value'], 6)}`)
- `avg_first_response_hours`: `{format_float(coef_map['avg_first_response_hours']['coef_treatment_intensity'], 4)}` (HC1 s.e. `{format_float(coef_map['avg_first_response_hours']['se_hc1'], 4)}`, p=`{format_float(coef_map['avg_first_response_hours']['p_value'], 6)}`)
- `backlog_open_end_month`: `{format_float(coef_map['backlog_open_end_month']['coef_treatment_intensity'], 4)}` (HC1 s.e. `{format_float(coef_map['backlog_open_end_month']['se_hc1'], 4)}`, p=`{format_float(coef_map['backlog_open_end_month']['p_value'], 6)}`)

## Interpretation boundary
The preview suggests that, in the synthetic panel, greater pre-period Stack Overflow dependence is associated with larger post-ChatGPT increases in issue inflow and first-response delay. The backlog result is weaker at this stage, which is useful information: it suggests the eventual real-data exercise should distinguish between immediate flow pressure and slower-moving stock accumulation.

This is still exploratory work. The specification does not yet include the robustness, heterogeneity, or alternative functional-form checks that belong in later steps.

## Risks carried forward to Step 4
1. The synthetic panel may make treatment-response patterns cleaner than real data will be.
2. Backlog dynamics appear noisier than issue inflow and response-time measures, so that outcome may require alternative scaling or lag structure.
3. The next step should formalize the baseline econometric specification and document the remaining assumptions more explicitly.

## Reproduction
From the repository root:

```bash
python3 -m venv .venv-step3
source .venv-step3/bin/activate
pip install -r requirements-step3.txt
python scripts/run_step3_eda.py
```
"""
    return markdown


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
            "outputs/step3_ecosystem_summary.csv",
            "outputs/step3_prepost_summary.csv",
            "outputs/step3_twfe_preview.csv",
            "outputs/step3_key_metrics.json",
            "outputs/step3_manifest.json",
            "docs/STEP3_exploratory_analysis.md",
        ],
    }


def main() -> None:
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)

    panel = load_step2_panel()
    ecosystem_pre_post = build_ecosystem_pre_post_summary(panel)
    event_summary = build_event_time_summary(panel)
    diagnostics = build_parallel_trend_diagnostics(panel)
    exposure_change = build_exposure_change_summary(ecosystem_pre_post)
    ecosystem_summary = build_ecosystem_summary(panel)
    prepost_summary = build_binary_prepost_summary(panel)
    twfe_preview = build_twfe_preview(panel)
    key_metrics = build_key_metrics(panel)
    markdown = build_step3_markdown(ecosystem_pre_post, twfe_preview)
    manifest = build_manifest(panel)

    panel.to_csv(OUTPUTS / "step3_identification_ready_panel.csv", index=False)
    ecosystem_pre_post.to_csv(OUTPUTS / "step3_ecosystem_pre_post_summary.csv", index=False)
    event_summary.to_csv(OUTPUTS / "step3_event_time_exposure_summary.csv", index=False)
    diagnostics.to_csv(OUTPUTS / "step3_parallel_trend_diagnostics.csv", index=False)
    exposure_change.to_csv(OUTPUTS / "step3_exposure_change_summary.csv", index=False)
    ecosystem_summary.to_csv(OUTPUTS / "step3_ecosystem_summary.csv", index=False)
    prepost_summary.to_csv(OUTPUTS / "step3_prepost_summary.csv", index=False)
    twfe_preview.to_csv(OUTPUTS / "step3_twfe_preview.csv", index=False)
    (OUTPUTS / "step3_key_metrics.json").write_text(
        json.dumps(key_metrics, indent=2) + "\n", encoding="utf-8"
    )
    (OUTPUTS / "step3_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    (DOCS / "STEP3_exploratory_analysis.md").write_text(markdown, encoding="utf-8")

    print(f"Wrote {OUTPUTS / 'step3_identification_ready_panel.csv'}")
    print(f"Wrote {OUTPUTS / 'step3_ecosystem_pre_post_summary.csv'}")
    print(f"Wrote {OUTPUTS / 'step3_event_time_exposure_summary.csv'}")
    print(f"Wrote {OUTPUTS / 'step3_parallel_trend_diagnostics.csv'}")
    print(f"Wrote {OUTPUTS / 'step3_exposure_change_summary.csv'}")
    print(f"Wrote {OUTPUTS / 'step3_ecosystem_summary.csv'}")
    print(f"Wrote {OUTPUTS / 'step3_prepost_summary.csv'}")
    print(f"Wrote {OUTPUTS / 'step3_twfe_preview.csv'}")
    print(f"Wrote {OUTPUTS / 'step3_key_metrics.json'}")
    print(f"Wrote {OUTPUTS / 'step3_manifest.json'}")
    print(f"Wrote {DOCS / 'STEP3_exploratory_analysis.md'}")


if __name__ == "__main__":
    main()
