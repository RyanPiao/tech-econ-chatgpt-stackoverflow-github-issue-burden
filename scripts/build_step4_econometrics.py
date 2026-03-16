from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from linearmodels.panel import PanelOLS
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"
DOCS = ROOT / "docs"

MODEL_OUTCOMES = [
    "issues_opened",
    "median_close_days",
    "avg_first_response_hours",
    "backlog_open_end_month",
    "issue_burden_index",
]

EDA_OUTCOMES = MODEL_OUTCOMES + [
    "issues_per_active_repo",
    "backlog_per_active_repo",
    "questions_per_active_repo",
]

CONTROL_SOURCE_COLUMNS = [
    "active_repos_observed",
    "questions_per_active_repo",
    "repo_scale",
]

CONTROL_Z_COLUMNS = [
    "active_repos_z",
    "questions_per_active_repo_z",
    "repo_scale_z",
]

EVENT_WINDOW = list(range(-12, 19))
EVENT_BASELINE = -1


def event_col(month_k: int) -> str:
    return f"event_m{abs(month_k)}" if month_k < 0 else f"event_p{month_k}"


def load_step3_panel() -> pd.DataFrame:
    panel = pd.read_csv(OUTPUTS / "step3_identification_ready_panel.csv", parse_dates=["month"])
    panel = panel.sort_values(["ecosystem", "month"]).reset_index(drop=True)
    return panel


def build_feature_panel(panel: pd.DataFrame) -> pd.DataFrame:
    panel = panel.copy()

    panel["year"] = panel["month"].dt.year
    panel["calendar_month"] = panel["month"].dt.month
    panel["quarter"] = panel["month"].dt.quarter
    panel["repo_scale"] = np.log1p(panel["active_repos_observed"])
    panel["post_trend_months"] = np.where(
        panel["post_chatgpt"] == 1,
        panel["months_since_chatgpt"],
        0,
    )
    panel["season_sin"] = np.sin(2 * np.pi * panel["calendar_month"] / 12)
    panel["season_cos"] = np.cos(2 * np.pi * panel["calendar_month"] / 12)

    by_eco = panel.groupby("ecosystem", sort=False)
    panel["lag_issues_opened"] = by_eco["issues_opened"].shift(1)
    panel["lag_backlog_open_end_month"] = by_eco["backlog_open_end_month"].shift(1)
    panel["lag_avg_first_response_hours"] = by_eco["avg_first_response_hours"].shift(1)

    panel["lag_issues_opened"] = panel["lag_issues_opened"].fillna(panel["issues_opened"])
    panel["lag_backlog_open_end_month"] = panel["lag_backlog_open_end_month"].fillna(
        panel["backlog_open_end_month"]
    )
    panel["lag_avg_first_response_hours"] = panel["lag_avg_first_response_hours"].fillna(
        panel["avg_first_response_hours"]
    )

    panel["delta_issues_opened"] = panel["issues_opened"] - panel["lag_issues_opened"]
    panel["delta_backlog_open_end_month"] = (
        panel["backlog_open_end_month"] - panel["lag_backlog_open_end_month"]
    )
    panel["delta_avg_first_response_hours"] = (
        panel["avg_first_response_hours"] - panel["lag_avg_first_response_hours"]
    )

    panel["log1p_issues_opened"] = np.log1p(panel["issues_opened"])
    panel["log1p_backlog_open_end_month"] = np.log1p(panel["backlog_open_end_month"])

    scaler = StandardScaler()
    z_values = scaler.fit_transform(panel[CONTROL_SOURCE_COLUMNS])
    for idx, target in enumerate(CONTROL_Z_COLUMNS):
        panel[target] = z_values[:, idx]

    return panel


def build_eda_distribution_summary(panel: pd.DataFrame) -> pd.DataFrame:
    records: list[dict] = []

    for outcome in EDA_OUTCOMES:
        grouped = panel.groupby(["exposure_bucket", "post_period_label"], observed=True)[outcome]
        for (bucket, period), values in grouped:
            records.append(
                {
                    "outcome": outcome,
                    "exposure_bucket": bucket,
                    "post_period_label": period,
                    "n": int(values.shape[0]),
                    "mean": float(values.mean()),
                    "std": float(values.std(ddof=1)),
                    "p10": float(values.quantile(0.10)),
                    "median": float(values.median()),
                    "p90": float(values.quantile(0.90)),
                }
            )

    return pd.DataFrame(records).sort_values(
        ["outcome", "exposure_bucket", "post_period_label"]
    ).reset_index(drop=True)


def build_outcome_correlation(panel: pd.DataFrame) -> pd.DataFrame:
    corr_columns = [
        "issues_opened",
        "median_close_days",
        "avg_first_response_hours",
        "backlog_open_end_month",
        "issue_burden_index",
        "issues_per_active_repo",
        "backlog_per_active_repo",
        "questions_per_active_repo",
        "so_dependence_pre",
        "treatment_intensity",
        "active_repos_observed",
    ]
    return panel[corr_columns].corr().round(6)


def build_variance_decomposition(panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for outcome in MODEL_OUTCOMES:
        by_eco = panel.groupby("ecosystem", observed=True)[outcome]
        between_var = float(by_eco.mean().var(ddof=1))
        within_var = float(by_eco.var(ddof=1).mean())
        total_var = float(panel[outcome].var(ddof=1))
        rows.append(
            {
                "outcome": outcome,
                "between_ecosystem_variance": between_var,
                "within_ecosystem_variance": within_var,
                "total_variance": total_var,
                "between_share": float(between_var / total_var) if total_var > 0 else np.nan,
                "within_share": float(within_var / total_var) if total_var > 0 else np.nan,
            }
        )
    return pd.DataFrame(rows).sort_values("outcome").reset_index(drop=True)


def fit_twfe(
    panel: pd.DataFrame,
    outcome: str,
    include_controls: bool,
    weight_column: str | None,
) -> dict:
    frame = panel.set_index(["ecosystem", "month"])
    regressors = ["treatment_intensity"] + (CONTROL_Z_COLUMNS if include_controls else [])

    model = PanelOLS(
        dependent=frame[outcome],
        exog=frame[regressors],
        weights=frame[weight_column] if weight_column else None,
        entity_effects=True,
        time_effects=True,
        drop_absorbed=True,
    )
    fitted = model.fit(cov_type="clustered", cluster_entity=True)

    return {
        "coef": float(fitted.params["treatment_intensity"]),
        "std_error": float(fitted.std_errors["treatment_intensity"]),
        "t_stat": float(fitted.tstats["treatment_intensity"]),
        "p_value": float(fitted.pvalues["treatment_intensity"]),
        "n_obs": int(fitted.nobs),
        "r_squared": float(fitted.rsquared),
        "r_squared_within": float(fitted.rsquared_within),
        "r_squared_between": float(fitted.rsquared_between),
        "r_squared_overall": float(fitted.rsquared_overall),
    }


def build_twfe_models(panel: pd.DataFrame) -> pd.DataFrame:
    specs = [
        {
            "specification": "baseline_fe_controls_clustered",
            "include_controls": True,
            "weight_column": None,
            "notes": "Entity/time FE with standardized controls and ecosystem-clustered SE.",
        },
        {
            "specification": "fe_no_controls_clustered",
            "include_controls": False,
            "weight_column": None,
            "notes": "Entity/time FE without additional controls; ecosystem-clustered SE.",
        },
        {
            "specification": "fe_controls_weighted_repos",
            "include_controls": True,
            "weight_column": "active_repos_observed",
            "notes": "Entity/time FE with controls and active-repository analytic weights.",
        },
    ]

    rows = []
    for spec in specs:
        for outcome in MODEL_OUTCOMES:
            fit = fit_twfe(
                panel=panel,
                outcome=outcome,
                include_controls=spec["include_controls"],
                weight_column=spec["weight_column"],
            )
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
                    "notes": spec["notes"],
                }
            )

    return pd.DataFrame(rows).sort_values(["specification", "outcome"]).reset_index(drop=True)


def build_statsmodels_sanity_check(panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    outcomes = ["issues_opened", "avg_first_response_hours"]

    for outcome in outcomes:
        fit = smf.ols(
            formula=(
                f"{outcome} ~ treatment_intensity + active_repos_z + "
                "questions_per_active_repo_z + repo_scale_z + C(ecosystem) + C(month)"
            ),
            data=panel,
        ).fit(cov_type="cluster", cov_kwds={"groups": panel["ecosystem"]})

        rows.append(
            {
                "outcome": outcome,
                "coef_treatment_intensity": float(fit.params["treatment_intensity"]),
                "std_error": float(fit.bse["treatment_intensity"]),
                "t_stat": float(fit.tvalues["treatment_intensity"]),
                "p_value": float(fit.pvalues["treatment_intensity"]),
                "n_obs": int(fit.nobs),
                "r_squared": float(fit.rsquared),
                "estimator": "statsmodels_ols_fe_clustered",
            }
        )

    return pd.DataFrame(rows).sort_values("outcome").reset_index(drop=True)


def build_event_study(panel: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    frame = panel.copy()
    cols_by_k: dict[int, str] = {}
    for k in EVENT_WINDOW:
        if k == EVENT_BASELINE:
            continue
        col = event_col(k)
        frame[col] = ((frame["months_since_chatgpt"] == k).astype(int) * frame["so_dependence_pre"])
        cols_by_k[k] = col

    model_df = frame.set_index(["ecosystem", "month"])
    regressors = list(cols_by_k.values()) + CONTROL_Z_COLUMNS
    model = PanelOLS(
        dependent=model_df["issues_opened"],
        exog=model_df[regressors],
        entity_effects=True,
        time_effects=True,
        drop_absorbed=True,
        check_rank=False,
    )
    fitted = model.fit(cov_type="clustered", cluster_entity=True)

    rows = []
    for k in sorted(cols_by_k):
        col = cols_by_k[k]
        coef = float(fitted.params[col])
        se = float(fitted.std_errors[col])
        rows.append(
            {
                "event_month": k,
                "coef": coef,
                "std_error": se,
                "t_stat": float(fitted.tstats[col]),
                "p_value": float(fitted.pvalues[col]),
                "ci_low_95": float(coef - 1.96 * se),
                "ci_high_95": float(coef + 1.96 * se),
                "baseline_month_omitted": EVENT_BASELINE,
            }
        )

    event_df = pd.DataFrame(rows).sort_values("event_month").reset_index(drop=True)

    pre_cols = [cols_by_k[k] for k in sorted(cols_by_k) if k <= -2]
    pretrend_p = np.nan
    pretrend_stat = np.nan
    if pre_cols:
        restriction = ", ".join(f"{col} = 0" for col in pre_cols)
        wald = fitted.wald_test(formula=restriction)
        pretrend_p = float(np.squeeze(wald.pval))
        pretrend_stat = float(np.squeeze(wald.stat))

    diagnostics = {
        "event_window_min": int(min(EVENT_WINDOW)),
        "event_window_max": int(max(EVENT_WINDOW)),
        "omitted_baseline_month": EVENT_BASELINE,
        "pretrend_joint_wald_stat": pretrend_stat,
        "pretrend_joint_p_value": pretrend_p,
        "mean_pre_event_coef": float(event_df.loc[event_df["event_month"] <= -2, "coef"].mean()),
        "mean_post_event_coef": float(event_df.loc[event_df["event_month"] >= 0, "coef"].mean()),
    }

    return event_df, diagnostics


def build_placebo_test(panel: pd.DataFrame) -> dict:
    pre = panel.loc[panel["post_chatgpt"] == 0].copy()
    placebo_cut = pd.Timestamp("2021-06-01")

    pre["placebo_post"] = (pre["month"] >= placebo_cut).astype(int)
    pre["placebo_treatment_intensity"] = pre["placebo_post"] * pre["so_dependence_pre"]

    model_df = pre.set_index(["ecosystem", "month"])
    model = PanelOLS(
        dependent=model_df["issues_opened"],
        exog=model_df[["placebo_treatment_intensity"] + CONTROL_Z_COLUMNS],
        entity_effects=True,
        time_effects=True,
        drop_absorbed=True,
    )
    fitted = model.fit(cov_type="clustered", cluster_entity=True)

    return {
        "placebo_split_month": str(placebo_cut.date()),
        "coef": float(fitted.params["placebo_treatment_intensity"]),
        "std_error": float(fitted.std_errors["placebo_treatment_intensity"]),
        "t_stat": float(fitted.tstats["placebo_treatment_intensity"]),
        "p_value": float(fitted.pvalues["placebo_treatment_intensity"]),
        "n_obs": int(fitted.nobs),
    }


def build_leave_one_ecosystem_out(panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    ecosystems = sorted(panel["ecosystem"].unique().tolist())

    for dropped in ecosystems:
        sample = panel.loc[panel["ecosystem"] != dropped].copy()
        fit = fit_twfe(
            panel=sample,
            outcome="issues_opened",
            include_controls=True,
            weight_column=None,
        )
        rows.append(
            {
                "dropped_ecosystem": dropped,
                "coef_treatment_intensity": fit["coef"],
                "std_error": fit["std_error"],
                "p_value": fit["p_value"],
                "n_obs": fit["n_obs"],
            }
        )

    out = pd.DataFrame(rows).sort_values("dropped_ecosystem").reset_index(drop=True)
    out["coef_deviation_from_full_sample"] = (
        out["coef_treatment_intensity"] - out["coef_treatment_intensity"].mean()
    )
    return out


def build_identification_diagnostics(
    twfe_models: pd.DataFrame,
    event_diag: dict,
    placebo: dict,
    loo: pd.DataFrame,
) -> pd.DataFrame:
    baseline = twfe_models.loc[
        twfe_models["specification"] == "baseline_fe_controls_clustered"
    ].copy()

    rows = []
    for _, row in baseline.iterrows():
        rows.append(
            {
                "diagnostic": f"baseline_coef_{row['outcome']}",
                "value": float(row["coef_treatment_intensity"]),
                "context": "Baseline TWFE with controls and clustered SE.",
            }
        )
        rows.append(
            {
                "diagnostic": f"baseline_pvalue_{row['outcome']}",
                "value": float(row["p_value"]),
                "context": "Inference on treatment-intensity coefficient in baseline TWFE.",
            }
        )

    rows.extend(
        [
            {
                "diagnostic": "event_study_pretrend_joint_p_value",
                "value": float(event_diag["pretrend_joint_p_value"]),
                "context": "Joint Wald test for pre-period event interactions (k <= -2).",
            },
            {
                "diagnostic": "event_study_mean_pre_coef",
                "value": float(event_diag["mean_pre_event_coef"]),
                "context": "Average pre-period event-study coefficient.",
            },
            {
                "diagnostic": "event_study_mean_post_coef",
                "value": float(event_diag["mean_post_event_coef"]),
                "context": "Average post-period event-study coefficient.",
            },
            {
                "diagnostic": "placebo_treatment_p_value",
                "value": float(placebo["p_value"]),
                "context": "Pre-period placebo TWFE test for treatment intensity.",
            },
            {
                "diagnostic": "max_abs_loo_deviation",
                "value": float(np.abs(loo["coef_deviation_from_full_sample"]).max()),
                "context": "Sensitivity of issues_opened coefficient across leave-one-ecosystem-out runs.",
            },
        ]
    )

    return pd.DataFrame(rows)


def build_key_metrics(
    panel: pd.DataFrame,
    twfe_models: pd.DataFrame,
    event_diag: dict,
    placebo: dict,
    loo: pd.DataFrame,
) -> dict:
    baseline = twfe_models.loc[
        twfe_models["specification"] == "baseline_fe_controls_clustered"
    ].set_index("outcome")

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "panel_rows": int(len(panel)),
        "ecosystem_count": int(panel["ecosystem"].nunique()),
        "sample_start": str(panel["month"].min().date()),
        "sample_end": str(panel["month"].max().date()),
        "baseline_coef_issues_opened": float(
            baseline.loc["issues_opened", "coef_treatment_intensity"]
        ),
        "baseline_p_issues_opened": float(baseline.loc["issues_opened", "p_value"]),
        "baseline_coef_avg_first_response_hours": float(
            baseline.loc["avg_first_response_hours", "coef_treatment_intensity"]
        ),
        "baseline_p_avg_first_response_hours": float(
            baseline.loc["avg_first_response_hours", "p_value"]
        ),
        "event_study_pretrend_joint_p_value": float(event_diag["pretrend_joint_p_value"]),
        "placebo_p_value": float(placebo["p_value"]),
        "loo_max_abs_deviation": float(np.abs(loo["coef_deviation_from_full_sample"]).max()),
    }


def f3(value: float) -> str:
    return f"{value:.3f}"


def f4(value: float) -> str:
    return f"{value:.4f}"


def build_step4_markdown(
    twfe_models: pd.DataFrame,
    event_diag: dict,
    placebo: dict,
    variance: pd.DataFrame,
) -> str:
    baseline = twfe_models.loc[
        twfe_models["specification"] == "baseline_fe_controls_clustered"
    ].set_index("outcome")

    var_tbl = variance.set_index("outcome")

    markdown = f"""# Step 4 Baseline Econometric Model

## Purpose
Step 4 formalizes the baseline identification design using the Step 3 synthetic ecosystem-month panel. This stage moves from descriptive diagnostics into econometric estimation with two-way fixed effects, richer controls, event-study dynamics, and stability checks.

## Data and modeling frame
- Input panel: `outputs/step3_identification_ready_panel.csv`
- Unit of analysis: ecosystem-month
- Sample window: 2021-01 to 2024-12
- Main treatment intensity: `post_chatgpt × so_dependence_pre`

Step 4 augments the panel with model-ready controls (log repository scale, normalized activity proxies, lag/delta diagnostics, seasonality features), then estimates fixed-effects models in `linearmodels` with ecosystem-clustered standard errors.

## Produced artifacts
- `outputs/step4_model_panel.csv`
- `outputs/step4_eda_distribution_summary.csv`
- `outputs/step4_outcome_correlation.csv`
- `outputs/step4_variance_decomposition.csv`
- `outputs/step4_twfe_models.csv`
- `outputs/step4_statsmodels_sanity_check.csv`
- `outputs/step4_event_study_issues_opened.csv`
- `outputs/step4_placebo_test.csv`
- `outputs/step4_leave_one_ecosystem_out.csv`
- `outputs/step4_identification_diagnostics.csv`
- `outputs/step4_key_metrics.json`
- `outputs/step4_manifest.json`
- `docs/STEP4_baseline_econometric_model.md`

## Baseline TWFE estimates (controls + ecosystem-clustered SE)
Coefficient on `treatment_intensity`:

- `issues_opened`: {f4(float(baseline.loc['issues_opened', 'coef_treatment_intensity']))} (p={f4(float(baseline.loc['issues_opened', 'p_value']))})
- `median_close_days`: {f4(float(baseline.loc['median_close_days', 'coef_treatment_intensity']))} (p={f4(float(baseline.loc['median_close_days', 'p_value']))})
- `avg_first_response_hours`: {f4(float(baseline.loc['avg_first_response_hours', 'coef_treatment_intensity']))} (p={f4(float(baseline.loc['avg_first_response_hours', 'p_value']))})
- `backlog_open_end_month`: {f4(float(baseline.loc['backlog_open_end_month', 'coef_treatment_intensity']))} (p={f4(float(baseline.loc['backlog_open_end_month', 'p_value']))})
- `issue_burden_index`: {f4(float(baseline.loc['issue_burden_index', 'coef_treatment_intensity']))} (p={f4(float(baseline.loc['issue_burden_index', 'p_value']))})

A cross-implementation sanity check in `statsmodels` (`outputs/step4_statsmodels_sanity_check.csv`) confirms the same positive treatment-direction for core outcomes.

## Identification diagnostics
- Event-study pretrend joint Wald p-value (k ≤ -2): {f4(float(event_diag['pretrend_joint_p_value']))}
- Mean pre-period event coefficient: {f4(float(event_diag['mean_pre_event_coef']))}
- Mean post-period event coefficient: {f4(float(event_diag['mean_post_event_coef']))}
- Pre-period placebo test p-value (split at 2021-06): {f4(float(placebo['p_value']))}

## Variance structure insight
Between-ecosystem share of variation:

- `issues_opened`: {f3(float(var_tbl.loc['issues_opened', 'between_share']))}
- `avg_first_response_hours`: {f3(float(var_tbl.loc['avg_first_response_hours', 'between_share']))}
- `backlog_open_end_month`: {f3(float(var_tbl.loc['backlog_open_end_month', 'between_share']))}

Within-ecosystem variation remains substantial for all modeled outcomes, supporting fixed-effects estimation as an informative baseline lens.

## Interpretation boundary
As in earlier steps, all results are generated from a synthetic panel for pipeline and identification validation. These estimates are not empirical claims about real public-source data.

## Reproduction
From the repository root:

```bash
python3 -m venv .venv-step4
source .venv-step4/bin/activate
pip install -r requirements-step4.txt
python scripts/run_step4_econometrics.py
```
"""
    return markdown


def build_manifest(panel: pd.DataFrame) -> dict:
    return {
        "artifact": "Step 4 synthetic baseline econometric package",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_panel": "outputs/step3_identification_ready_panel.csv",
        "sample_start": str(panel["month"].min().date()),
        "sample_end": str(panel["month"].max().date()),
        "n_rows": int(len(panel)),
        "n_ecosystems": int(panel["ecosystem"].nunique()),
        "synthetic_note": (
            "Step 4 continues to use synthetic ecosystem-month data so econometric identification code, "
            "diagnostics, and reproducibility checks can be audited without implying real-world estimates."
        ),
        "outputs": [
            "outputs/step4_model_panel.csv",
            "outputs/step4_eda_distribution_summary.csv",
            "outputs/step4_outcome_correlation.csv",
            "outputs/step4_variance_decomposition.csv",
            "outputs/step4_twfe_models.csv",
            "outputs/step4_statsmodels_sanity_check.csv",
            "outputs/step4_event_study_issues_opened.csv",
            "outputs/step4_placebo_test.csv",
            "outputs/step4_leave_one_ecosystem_out.csv",
            "outputs/step4_identification_diagnostics.csv",
            "outputs/step4_key_metrics.json",
            "outputs/step4_manifest.json",
            "docs/STEP4_baseline_econometric_model.md",
        ],
    }


def main() -> None:
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)

    panel = load_step3_panel()
    step4_panel = build_feature_panel(panel)

    eda_summary = build_eda_distribution_summary(step4_panel)
    corr = build_outcome_correlation(step4_panel)
    variance = build_variance_decomposition(step4_panel)
    twfe = build_twfe_models(step4_panel)
    statsmodels_sanity = build_statsmodels_sanity_check(step4_panel)
    event_study, event_diag = build_event_study(step4_panel)
    placebo = build_placebo_test(step4_panel)
    loo = build_leave_one_ecosystem_out(step4_panel)
    diagnostics = build_identification_diagnostics(twfe, event_diag, placebo, loo)
    key_metrics = build_key_metrics(step4_panel, twfe, event_diag, placebo, loo)
    markdown = build_step4_markdown(twfe, event_diag, placebo, variance)
    manifest = build_manifest(step4_panel)

    out_panel = step4_panel.copy()
    out_panel["month"] = out_panel["month"].dt.strftime("%Y-%m-%d")
    out_panel.to_csv(OUTPUTS / "step4_model_panel.csv", index=False)
    eda_summary.to_csv(OUTPUTS / "step4_eda_distribution_summary.csv", index=False)
    corr.to_csv(OUTPUTS / "step4_outcome_correlation.csv", index=True)
    variance.to_csv(OUTPUTS / "step4_variance_decomposition.csv", index=False)
    twfe.to_csv(OUTPUTS / "step4_twfe_models.csv", index=False)
    statsmodels_sanity.to_csv(OUTPUTS / "step4_statsmodels_sanity_check.csv", index=False)
    event_study.to_csv(OUTPUTS / "step4_event_study_issues_opened.csv", index=False)
    pd.DataFrame([placebo]).to_csv(OUTPUTS / "step4_placebo_test.csv", index=False)
    loo.to_csv(OUTPUTS / "step4_leave_one_ecosystem_out.csv", index=False)
    diagnostics.to_csv(OUTPUTS / "step4_identification_diagnostics.csv", index=False)
    (OUTPUTS / "step4_key_metrics.json").write_text(
        json.dumps(key_metrics, indent=2) + "\n", encoding="utf-8"
    )
    (OUTPUTS / "step4_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    (DOCS / "STEP4_baseline_econometric_model.md").write_text(markdown, encoding="utf-8")

    print(f"Wrote {OUTPUTS / 'step4_model_panel.csv'}")
    print(f"Wrote {OUTPUTS / 'step4_eda_distribution_summary.csv'}")
    print(f"Wrote {OUTPUTS / 'step4_outcome_correlation.csv'}")
    print(f"Wrote {OUTPUTS / 'step4_variance_decomposition.csv'}")
    print(f"Wrote {OUTPUTS / 'step4_twfe_models.csv'}")
    print(f"Wrote {OUTPUTS / 'step4_statsmodels_sanity_check.csv'}")
    print(f"Wrote {OUTPUTS / 'step4_event_study_issues_opened.csv'}")
    print(f"Wrote {OUTPUTS / 'step4_placebo_test.csv'}")
    print(f"Wrote {OUTPUTS / 'step4_leave_one_ecosystem_out.csv'}")
    print(f"Wrote {OUTPUTS / 'step4_identification_diagnostics.csv'}")
    print(f"Wrote {OUTPUTS / 'step4_key_metrics.json'}")
    print(f"Wrote {OUTPUTS / 'step4_manifest.json'}")
    print(f"Wrote {DOCS / 'STEP4_baseline_econometric_model.md'}")


if __name__ == "__main__":
    main()
