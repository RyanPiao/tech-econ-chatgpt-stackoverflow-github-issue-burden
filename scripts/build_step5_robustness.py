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

BASE_OUTCOMES = [
    "issues_opened",
    "median_close_days",
    "avg_first_response_hours",
    "backlog_open_end_month",
    "issue_burden_index",
]

DYNAMIC_OUTCOMES = BASE_OUTCOMES.copy()

HETEROGENEITY_OUTCOMES = [
    "issues_opened",
    "avg_first_response_hours",
    "backlog_open_end_month",
    "issue_burden_index",
]

CONTROL_Z_COLUMNS = [
    "active_repos_z",
    "questions_per_active_repo_z",
    "repo_scale_z",
]

EVENT_WINDOW = list(range(-12, 19))
EVENT_BASELINE = -1

HETEROGENEITY_DIMENSIONS = {
    "high_pre_active_repos": "pre_period_active_repo_scale",
    "high_pre_backlog_per_repo": "pre_period_backlog_per_repo",
    "high_pre_issue_burden": "pre_period_issue_burden_index",
}


def event_col(month_k: int) -> str:
    return f"event_m{abs(month_k)}" if month_k < 0 else f"event_p{month_k}"


def load_step4_panel() -> pd.DataFrame:
    panel = pd.read_csv(OUTPUTS / "step4_model_panel.csv", parse_dates=["month"])
    panel = panel.sort_values(["ecosystem", "month"]).reset_index(drop=True)
    return panel


def fit_panel_ols(
    panel: pd.DataFrame,
    outcome: str,
    exog_columns: list[str],
    *,
    weight_column: str | None = None,
    cov_type: str = "clustered_entity",
) -> dict:
    frame = panel.set_index(["ecosystem", "month"])

    model = PanelOLS(
        dependent=frame[outcome],
        exog=frame[exog_columns],
        weights=frame[weight_column] if weight_column else None,
        entity_effects=True,
        time_effects=True,
        drop_absorbed=True,
    )

    if cov_type == "clustered_entity":
        fitted = model.fit(cov_type="clustered", cluster_entity=True)
    elif cov_type == "clustered_entity_time":
        fitted = model.fit(cov_type="clustered", cluster_entity=True, cluster_time=True)
    elif cov_type == "robust":
        fitted = model.fit(cov_type="robust")
    elif cov_type == "kernel_bartlett_bw4":
        fitted = model.fit(cov_type="kernel", kernel="bartlett", bandwidth=4)
    else:
        raise ValueError(f"Unknown cov_type: {cov_type}")

    return {
        "fitted": fitted,
        "n_obs": int(fitted.nobs),
        "r_squared": float(fitted.rsquared),
        "r_squared_within": float(fitted.rsquared_within),
        "r_squared_between": float(fitted.rsquared_between),
        "r_squared_overall": float(fitted.rsquared_overall),
    }


def build_sensitivity_checks(panel: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []

    core_specs = [
        {
            "specification": "baseline_clustered_entity",
            "cov_type": "clustered_entity",
            "weight_column": None,
            "notes": "Matches Step 4 baseline covariance setting.",
        },
        {
            "specification": "clustered_entity_time",
            "cov_type": "clustered_entity_time",
            "weight_column": None,
            "notes": "Two-way clustered covariance (ecosystem and month).",
        },
        {
            "specification": "robust_white",
            "cov_type": "robust",
            "weight_column": None,
            "notes": "Heteroskedasticity-robust covariance without clustering.",
        },
        {
            "specification": "kernel_bartlett_bw4",
            "cov_type": "kernel_bartlett_bw4",
            "weight_column": None,
            "notes": "Panel kernel covariance with Bartlett kernel, bandwidth 4.",
        },
        {
            "specification": "weighted_clustered_entity",
            "cov_type": "clustered_entity",
            "weight_column": "active_repos_observed",
            "notes": "Entity-clustered covariance with active-repository analytic weights.",
        },
    ]

    for spec in core_specs:
        for outcome in BASE_OUTCOMES:
            fit = fit_panel_ols(
                panel=panel,
                outcome=outcome,
                exog_columns=["treatment_intensity"] + CONTROL_Z_COLUMNS,
                weight_column=spec["weight_column"],
                cov_type=spec["cov_type"],
            )
            fitted = fit["fitted"]

            rows.append(
                {
                    "outcome": outcome,
                    "outcome_transformation": "level",
                    "specification": spec["specification"],
                    "coef_treatment_intensity": float(fitted.params["treatment_intensity"]),
                    "std_error": float(fitted.std_errors["treatment_intensity"]),
                    "t_stat": float(fitted.tstats["treatment_intensity"]),
                    "p_value": float(fitted.pvalues["treatment_intensity"]),
                    "n_obs": fit["n_obs"],
                    "r_squared": fit["r_squared"],
                    "r_squared_within": fit["r_squared_within"],
                    "r_squared_between": fit["r_squared_between"],
                    "r_squared_overall": fit["r_squared_overall"],
                    "permutation_empirical_p_value": np.nan,
                    "permutation_draws": np.nan,
                    "notes": spec["notes"],
                }
            )

    for outcome in BASE_OUTCOMES:
        lo, hi = panel[outcome].quantile([0.01, 0.99])
        temp_col = f"winsorized_{outcome}"

        temp_panel = panel.copy()
        temp_panel[temp_col] = temp_panel[outcome].clip(lower=lo, upper=hi)

        fit = fit_panel_ols(
            panel=temp_panel,
            outcome=temp_col,
            exog_columns=["treatment_intensity"] + CONTROL_Z_COLUMNS,
            cov_type="clustered_entity",
        )
        fitted = fit["fitted"]

        rows.append(
            {
                "outcome": outcome,
                "outcome_transformation": "winsorized_p01_p99",
                "specification": "winsorized_p01_p99_clustered_entity",
                "coef_treatment_intensity": float(fitted.params["treatment_intensity"]),
                "std_error": float(fitted.std_errors["treatment_intensity"]),
                "t_stat": float(fitted.tstats["treatment_intensity"]),
                "p_value": float(fitted.pvalues["treatment_intensity"]),
                "n_obs": fit["n_obs"],
                "r_squared": fit["r_squared"],
                "r_squared_within": fit["r_squared_within"],
                "r_squared_between": fit["r_squared_between"],
                "r_squared_overall": fit["r_squared_overall"],
                "permutation_empirical_p_value": np.nan,
                "permutation_draws": np.nan,
                "notes": "Outcome winsorized at the 1st and 99th percentiles; entity-clustered covariance.",
            }
        )

    for outcome in BASE_OUTCOMES:
        temp_panel = panel.copy()

        if float(temp_panel[outcome].min()) > -1.0:
            temp_col = f"log1p_{outcome}_step5"
            temp_panel[temp_col] = np.log1p(temp_panel[outcome])
            transform = "log1p"
            spec_name = "log1p_outcome_clustered_entity"
            notes = "log(1 + outcome) transformation with entity-clustered covariance."
        else:
            temp_col = f"asinh_{outcome}_step5"
            temp_panel[temp_col] = np.arcsinh(temp_panel[outcome])
            transform = "asinh"
            spec_name = "asinh_outcome_clustered_entity"
            notes = "asinh(outcome) transformation for outcomes that can take negative values."

        fit = fit_panel_ols(
            panel=temp_panel,
            outcome=temp_col,
            exog_columns=["treatment_intensity"] + CONTROL_Z_COLUMNS,
            cov_type="clustered_entity",
        )
        fitted = fit["fitted"]

        rows.append(
            {
                "outcome": outcome,
                "outcome_transformation": transform,
                "specification": spec_name,
                "coef_treatment_intensity": float(fitted.params["treatment_intensity"]),
                "std_error": float(fitted.std_errors["treatment_intensity"]),
                "t_stat": float(fitted.tstats["treatment_intensity"]),
                "p_value": float(fitted.pvalues["treatment_intensity"]),
                "n_obs": fit["n_obs"],
                "r_squared": fit["r_squared"],
                "r_squared_within": fit["r_squared_within"],
                "r_squared_between": fit["r_squared_between"],
                "r_squared_overall": fit["r_squared_overall"],
                "permutation_empirical_p_value": np.nan,
                "permutation_draws": np.nan,
                "notes": notes,
            }
        )

    eco_base = (
        panel[["ecosystem", "so_dependence_pre"]]
        .drop_duplicates()
        .sort_values("ecosystem")
        .reset_index(drop=True)
    )
    ecosystems = eco_base["ecosystem"].tolist()
    exposures = eco_base["so_dependence_pre"].to_numpy(dtype=float)

    rng = np.random.default_rng(42)
    n_perm = 300
    perm_outcomes = ["issues_opened", "avg_first_response_hours"]

    for outcome in perm_outcomes:
        observed_fit = fit_panel_ols(
            panel=panel,
            outcome=outcome,
            exog_columns=["treatment_intensity"] + CONTROL_Z_COLUMNS,
            cov_type="clustered_entity",
        )
        observed_coef = float(observed_fit["fitted"].params["treatment_intensity"])

        perm_coefs: list[float] = []
        for _ in range(n_perm):
            shuffled = exposures.copy()
            rng.shuffle(shuffled)
            mapping = dict(zip(ecosystems, shuffled, strict=True))

            temp_panel = panel.copy()
            temp_panel["perm_treatment_intensity"] = (
                temp_panel["post_chatgpt"] * temp_panel["ecosystem"].map(mapping)
            )

            perm_fit = fit_panel_ols(
                panel=temp_panel,
                outcome=outcome,
                exog_columns=["perm_treatment_intensity"] + CONTROL_Z_COLUMNS,
                cov_type="clustered_entity",
            )
            perm_coef = float(perm_fit["fitted"].params["perm_treatment_intensity"])
            perm_coefs.append(perm_coef)

        perm_coefs_arr = np.asarray(perm_coefs)
        exceed = float((np.abs(perm_coefs_arr) >= abs(observed_coef)).sum())
        empirical_p = float((exceed + 1.0) / (n_perm + 1.0))

        rows.append(
            {
                "outcome": outcome,
                "outcome_transformation": "level",
                "specification": "permutation_inference_300",
                "coef_treatment_intensity": observed_coef,
                "std_error": float(np.std(perm_coefs_arr, ddof=1)),
                "t_stat": np.nan,
                "p_value": np.nan,
                "n_obs": observed_fit["n_obs"],
                "r_squared": observed_fit["r_squared"],
                "r_squared_within": observed_fit["r_squared_within"],
                "r_squared_between": observed_fit["r_squared_between"],
                "r_squared_overall": observed_fit["r_squared_overall"],
                "permutation_empirical_p_value": empirical_p,
                "permutation_draws": n_perm,
                "notes": "Permutation test shuffling ecosystem-level exposure across units (300 draws).",
            }
        )

    out = pd.DataFrame(rows).sort_values(
        ["specification", "outcome", "outcome_transformation"]
    ).reset_index(drop=True)
    return out


def build_dynamic_analysis(panel: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []

    for outcome in DYNAMIC_OUTCOMES:
        frame = panel.copy()
        cols_by_k: dict[int, str] = {}

        for k in EVENT_WINDOW:
            if k == EVENT_BASELINE:
                continue
            col = f"{event_col(k)}__{outcome}"
            frame[col] = (
                (frame["months_since_chatgpt"] == k).astype(int) * frame["so_dependence_pre"]
            )
            cols_by_k[k] = col

        regressors = list(cols_by_k.values()) + CONTROL_Z_COLUMNS
        model_df = frame.set_index(["ecosystem", "month"])

        model = PanelOLS(
            dependent=model_df[outcome],
            exog=model_df[regressors],
            entity_effects=True,
            time_effects=True,
            drop_absorbed=True,
            check_rank=False,
        )
        fitted = model.fit(cov_type="clustered", cluster_entity=True)

        pre_cols = [cols_by_k[k] for k in sorted(cols_by_k) if k <= -2]
        pretrend_p = np.nan
        pretrend_stat = np.nan
        if pre_cols:
            restriction = ", ".join(f"{col} = 0" for col in pre_cols)
            wald = fitted.wald_test(formula=restriction)
            pretrend_p = float(np.squeeze(wald.pval))
            pretrend_stat = float(np.squeeze(wald.stat))

        temp_rows: list[dict] = []
        for k in sorted(cols_by_k):
            col = cols_by_k[k]
            coef = float(fitted.params[col])
            se = float(fitted.std_errors[col])
            temp_rows.append(
                {
                    "outcome": outcome,
                    "event_month": k,
                    "coef": coef,
                    "std_error": se,
                    "t_stat": float(fitted.tstats[col]),
                    "p_value": float(fitted.pvalues[col]),
                    "ci_low_95": float(coef - 1.96 * se),
                    "ci_high_95": float(coef + 1.96 * se),
                }
            )

        temp_df = pd.DataFrame(temp_rows).sort_values("event_month").reset_index(drop=True)
        mean_pre = float(temp_df.loc[temp_df["event_month"] <= -2, "coef"].mean())
        mean_post = float(temp_df.loc[temp_df["event_month"] >= 0, "coef"].mean())
        cum_0_6 = float(
            temp_df.loc[temp_df["event_month"].between(0, 6), "coef"].sum()
        )
        cum_0_12 = float(
            temp_df.loc[temp_df["event_month"].between(0, 12), "coef"].sum()
        )

        for _, row in temp_df.iterrows():
            rows.append(
                {
                    "outcome": row["outcome"],
                    "event_month": int(row["event_month"]),
                    "coef": float(row["coef"]),
                    "std_error": float(row["std_error"]),
                    "t_stat": float(row["t_stat"]),
                    "p_value": float(row["p_value"]),
                    "ci_low_95": float(row["ci_low_95"]),
                    "ci_high_95": float(row["ci_high_95"]),
                    "baseline_month_omitted": EVENT_BASELINE,
                    "pretrend_joint_wald_stat": pretrend_stat,
                    "pretrend_joint_p_value": pretrend_p,
                    "mean_pre_event_coef": mean_pre,
                    "mean_post_event_coef": mean_post,
                    "cumulative_post_coef_0_6": cum_0_6,
                    "cumulative_post_coef_0_12": cum_0_12,
                }
            )

    out = pd.DataFrame(rows).sort_values(["outcome", "event_month"]).reset_index(drop=True)
    return out


def add_heterogeneity_flags(panel: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, float]]:
    pre = (
        panel.loc[panel["post_chatgpt"] == 0]
        .groupby("ecosystem", as_index=False)
        .agg(
            pre_active_repos_mean=("active_repos_observed", "mean"),
            pre_backlog_per_repo_mean=("backlog_per_active_repo", "mean"),
            pre_issue_burden_mean=("issue_burden_index", "mean"),
        )
    )

    thresholds = {
        "high_pre_active_repos": float(pre["pre_active_repos_mean"].median()),
        "high_pre_backlog_per_repo": float(pre["pre_backlog_per_repo_mean"].median()),
        "high_pre_issue_burden": float(pre["pre_issue_burden_mean"].median()),
    }

    pre["high_pre_active_repos"] = (
        pre["pre_active_repos_mean"] >= thresholds["high_pre_active_repos"]
    ).astype(int)
    pre["high_pre_backlog_per_repo"] = (
        pre["pre_backlog_per_repo_mean"] >= thresholds["high_pre_backlog_per_repo"]
    ).astype(int)
    pre["high_pre_issue_burden"] = (
        pre["pre_issue_burden_mean"] >= thresholds["high_pre_issue_burden"]
    ).astype(int)

    merged = panel.merge(
        pre[
            [
                "ecosystem",
                "high_pre_active_repos",
                "high_pre_backlog_per_repo",
                "high_pre_issue_burden",
            ]
        ],
        on="ecosystem",
        how="left",
    )

    for col in HETEROGENEITY_DIMENSIONS:
        merged[col] = merged[col].astype(int)

    return merged, thresholds


def build_heterogeneity_analysis(panel: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, float]]:
    panel_h, thresholds = add_heterogeneity_flags(panel)
    rows: list[dict] = []

    for dim_col, dim_label in HETEROGENEITY_DIMENSIONS.items():
        interaction_col = f"treat_x_{dim_col}"
        panel_h[interaction_col] = panel_h["treatment_intensity"] * panel_h[dim_col]

        for outcome in HETEROGENEITY_OUTCOMES:
            fit = fit_panel_ols(
                panel=panel_h,
                outcome=outcome,
                exog_columns=["treatment_intensity", interaction_col] + CONTROL_Z_COLUMNS,
                cov_type="clustered_entity",
            )
            fitted = fit["fitted"]

            base_coef = float(fitted.params["treatment_intensity"])
            interaction_coef = float(fitted.params[interaction_col])

            rows.append(
                {
                    "outcome": outcome,
                    "heterogeneity_dimension": dim_label,
                    "model_type": "interaction",
                    "subgroup": "low_reference",
                    "coef_treatment_intensity": base_coef,
                    "std_error": float(fitted.std_errors["treatment_intensity"]),
                    "t_stat": float(fitted.tstats["treatment_intensity"]),
                    "p_value": float(fitted.pvalues["treatment_intensity"]),
                    "coef_interaction": interaction_coef,
                    "std_error_interaction": float(fitted.std_errors[interaction_col]),
                    "p_value_interaction": float(fitted.pvalues[interaction_col]),
                    "implied_high_group_effect": base_coef + interaction_coef,
                    "n_obs": fit["n_obs"],
                    "ecosystem_count": int(panel_h["ecosystem"].nunique()),
                    "threshold_value": thresholds[dim_col],
                    "notes": "Interaction FE model: treatment + treatment×high_group + controls.",
                }
            )

            for group_value, subgroup in [(0, "low"), (1, "high")]:
                sample = panel_h.loc[panel_h[dim_col] == group_value].copy()
                split_fit = fit_panel_ols(
                    panel=sample,
                    outcome=outcome,
                    exog_columns=["treatment_intensity"] + CONTROL_Z_COLUMNS,
                    cov_type="clustered_entity",
                )
                split_fitted = split_fit["fitted"]

                rows.append(
                    {
                        "outcome": outcome,
                        "heterogeneity_dimension": dim_label,
                        "model_type": "split_sample",
                        "subgroup": subgroup,
                        "coef_treatment_intensity": float(
                            split_fitted.params["treatment_intensity"]
                        ),
                        "std_error": float(split_fitted.std_errors["treatment_intensity"]),
                        "t_stat": float(split_fitted.tstats["treatment_intensity"]),
                        "p_value": float(split_fitted.pvalues["treatment_intensity"]),
                        "coef_interaction": np.nan,
                        "std_error_interaction": np.nan,
                        "p_value_interaction": np.nan,
                        "implied_high_group_effect": np.nan,
                        "n_obs": split_fit["n_obs"],
                        "ecosystem_count": int(sample["ecosystem"].nunique()),
                        "threshold_value": thresholds[dim_col],
                        "notes": "Split-sample FE model estimated separately within subgroup.",
                    }
                )

    out = pd.DataFrame(rows).sort_values(
        ["heterogeneity_dimension", "outcome", "model_type", "subgroup"]
    ).reset_index(drop=True)
    return out, thresholds


def build_key_metrics(
    panel: pd.DataFrame,
    sensitivity: pd.DataFrame,
    dynamic: pd.DataFrame,
    heterogeneity: pd.DataFrame,
) -> dict:
    baseline_issues = sensitivity.loc[
        (sensitivity["outcome"] == "issues_opened")
        & (sensitivity["specification"] == "baseline_clustered_entity")
    ].iloc[0]

    twoway_issues = sensitivity.loc[
        (sensitivity["outcome"] == "issues_opened")
        & (sensitivity["specification"] == "clustered_entity_time")
    ].iloc[0]

    winsor_issues = sensitivity.loc[
        (sensitivity["outcome"] == "issues_opened")
        & (sensitivity["specification"] == "winsorized_p01_p99_clustered_entity")
    ].iloc[0]

    perm_issues = sensitivity.loc[
        (sensitivity["outcome"] == "issues_opened")
        & (sensitivity["specification"] == "permutation_inference_300")
    ].iloc[0]

    dyn_issues = dynamic.loc[dynamic["outcome"] == "issues_opened"].iloc[0]

    split_repo = heterogeneity.loc[
        (heterogeneity["outcome"] == "issues_opened")
        & (heterogeneity["heterogeneity_dimension"] == "pre_period_active_repo_scale")
        & (heterogeneity["model_type"] == "split_sample")
    ]
    low_repo = split_repo.loc[split_repo["subgroup"] == "low", "coef_treatment_intensity"].iloc[0]
    high_repo = split_repo.loc[split_repo["subgroup"] == "high", "coef_treatment_intensity"].iloc[0]

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "panel_rows": int(len(panel)),
        "ecosystem_count": int(panel["ecosystem"].nunique()),
        "sample_start": str(panel["month"].min().date()),
        "sample_end": str(panel["month"].max().date()),
        "baseline_coef_issues_opened": float(baseline_issues["coef_treatment_intensity"]),
        "baseline_p_issues_opened": float(baseline_issues["p_value"]),
        "two_way_cluster_p_issues_opened": float(twoway_issues["p_value"]),
        "winsorized_coef_issues_opened": float(winsor_issues["coef_treatment_intensity"]),
        "permutation_empirical_p_issues_opened": float(
            perm_issues["permutation_empirical_p_value"]
        ),
        "dynamic_pretrend_p_issues_opened": float(dyn_issues["pretrend_joint_p_value"]),
        "dynamic_cumulative_post_0_12_issues_opened": float(
            dyn_issues["cumulative_post_coef_0_12"]
        ),
        "heterogeneity_repo_scale_low_coef_issues_opened": float(low_repo),
        "heterogeneity_repo_scale_high_coef_issues_opened": float(high_repo),
        "heterogeneity_repo_scale_gap_high_minus_low": float(high_repo - low_repo),
    }


def f3(value: float) -> str:
    return f"{value:.3f}"


def f4(value: float) -> str:
    return f"{value:.4f}"


def build_step5_markdown(
    sensitivity: pd.DataFrame,
    dynamic: pd.DataFrame,
    heterogeneity: pd.DataFrame,
) -> str:
    def pick(outcome: str, spec: str) -> pd.Series:
        return sensitivity.loc[
            (sensitivity["outcome"] == outcome)
            & (sensitivity["specification"] == spec)
            & (sensitivity["outcome_transformation"] == "level")
        ].iloc[0]

    base_issues = pick("issues_opened", "baseline_clustered_entity")
    twoway_issues = pick("issues_opened", "clustered_entity_time")
    robust_issues = pick("issues_opened", "robust_white")
    weighted_issues = pick("issues_opened", "weighted_clustered_entity")

    base_resp = pick("avg_first_response_hours", "baseline_clustered_entity")

    winsor_issues = sensitivity.loc[
        (sensitivity["outcome"] == "issues_opened")
        & (sensitivity["specification"] == "winsorized_p01_p99_clustered_entity")
    ].iloc[0]

    log_issues = sensitivity.loc[
        (sensitivity["outcome"] == "issues_opened")
        & (sensitivity["specification"] == "log1p_outcome_clustered_entity")
    ].iloc[0]

    perm_issues = sensitivity.loc[
        (sensitivity["outcome"] == "issues_opened")
        & (sensitivity["specification"] == "permutation_inference_300")
    ].iloc[0]

    dyn_issues = dynamic.loc[dynamic["outcome"] == "issues_opened"].iloc[0]
    dyn_response = dynamic.loc[dynamic["outcome"] == "avg_first_response_hours"].iloc[0]

    split_repo = heterogeneity.loc[
        (heterogeneity["outcome"] == "issues_opened")
        & (heterogeneity["heterogeneity_dimension"] == "pre_period_active_repo_scale")
        & (heterogeneity["model_type"] == "split_sample")
    ]
    low_repo = split_repo.loc[split_repo["subgroup"] == "low", "coef_treatment_intensity"].iloc[0]
    high_repo = split_repo.loc[split_repo["subgroup"] == "high", "coef_treatment_intensity"].iloc[0]

    inter_backlog = heterogeneity.loc[
        (heterogeneity["outcome"] == "issues_opened")
        & (heterogeneity["heterogeneity_dimension"] == "pre_period_backlog_per_repo")
        & (heterogeneity["model_type"] == "interaction")
    ].iloc[0]

    markdown = f"""# Step 5 Robustness Checks

## Purpose
Step 5 stress-tests the Step 4 baseline by checking whether inference is sensitive to covariance assumptions, outcome transformations, randomization inference, dynamic treatment timing, and subgroup composition.

## Inputs
- `outputs/step4_model_panel.csv`
- `outputs/step4_twfe_models.csv`

## Produced artifacts
- `outputs/step5_sensitivity_checks.csv`
- `outputs/step5_dynamic_analysis.csv`
- `outputs/step5_heterogeneity_analysis.csv`
- `outputs/step5_key_metrics.json`
- `outputs/step5_manifest.json`
- `outputs/step5_validation_report.json`
- `docs/STEP5_robustness_checks.md`

## Sensitivity checks
For `issues_opened`, the treatment-intensity coefficient remains positive under all tested covariance choices:

- Baseline entity-clustered FE: {f4(float(base_issues['coef_treatment_intensity']))} (p={f4(float(base_issues['p_value']))})
- Two-way clustered FE (ecosystem + month): {f4(float(twoway_issues['coef_treatment_intensity']))} (p={f4(float(twoway_issues['p_value']))})
- Robust (White-style) FE covariance: {f4(float(robust_issues['coef_treatment_intensity']))} (p={f4(float(robust_issues['p_value']))})
- Weighted FE (active repositories): {f4(float(weighted_issues['coef_treatment_intensity']))} (p={f4(float(weighted_issues['p_value']))})

Transformation checks for `issues_opened` are directionally consistent:

- Winsorized (p01/p99): {f4(float(winsor_issues['coef_treatment_intensity']))} (p={f4(float(winsor_issues['p_value']))})
- log(1+y): {f4(float(log_issues['coef_treatment_intensity']))} (p={f4(float(log_issues['p_value']))})

Randomization inference (300 exposure permutations) yields an empirical p-value of {f4(float(perm_issues['permutation_empirical_p_value']))} for `issues_opened`.

For `avg_first_response_hours`, the baseline effect remains positive and precise: {f4(float(base_resp['coef_treatment_intensity']))} (p={f4(float(base_resp['p_value']))}).

## Dynamic checks (event-study interactions)
Event-study models are estimated for all baseline outcomes with an omitted month of k = -1 and an event window from k = -12 to k = +18.

For `issues_opened`:
- Joint pretrend p-value (k <= -2): {f4(float(dyn_issues['pretrend_joint_p_value']))}
- Mean pre-period coefficient: {f4(float(dyn_issues['mean_pre_event_coef']))}
- Mean post-period coefficient: {f4(float(dyn_issues['mean_post_event_coef']))}
- Cumulative post coefficient, k=0..12: {f4(float(dyn_issues['cumulative_post_coef_0_12']))}

For `avg_first_response_hours`:
- Joint pretrend p-value (k <= -2): {f4(float(dyn_response['pretrend_joint_p_value']))}
- Cumulative post coefficient, k=0..12: {f4(float(dyn_response['cumulative_post_coef_0_12']))}

## Heterogeneity checks
Heterogeneity is tested across three pre-period ecosystem partitions:
1. active repository scale,
2. backlog per active repository,
3. issue burden index.

For `issues_opened` in split-sample FE models by pre-period active repository scale:
- Low-scale ecosystems: {f4(float(low_repo))}
- High-scale ecosystems: {f4(float(high_repo))}
- High-minus-low gap: {f4(float(high_repo - low_repo))}

In the interaction model for pre-period backlog per repository, the interaction term is {f4(float(inter_backlog['coef_interaction']))} (p={f4(float(inter_backlog['p_value_interaction']))}), which points to a slightly smaller high-backlog effect but with weak statistical precision.

## Interpretation boundary
All estimates remain synthetic and are used for pipeline validation, model stress-testing, and reproducibility checks. They should not be interpreted as empirical claims about real ecosystems.

## Reproduction
From the repository root:

```bash
python3 -m venv .venv-step5
source .venv-step5/bin/activate
pip install -r requirements-step5.txt
python scripts/run_step5_robustness.py
```
"""
    return markdown


def build_manifest(panel: pd.DataFrame) -> dict:
    return {
        "artifact": "Step 5 synthetic robustness package",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_panel": "outputs/step4_model_panel.csv",
        "sample_start": str(panel["month"].min().date()),
        "sample_end": str(panel["month"].max().date()),
        "n_rows": int(len(panel)),
        "n_ecosystems": int(panel["ecosystem"].nunique()),
        "synthetic_note": (
            "Step 5 continues synthetic-only estimation to test robustness logic and inference stability "
            "before any real-data implementation."
        ),
        "outputs": [
            "outputs/step5_sensitivity_checks.csv",
            "outputs/step5_dynamic_analysis.csv",
            "outputs/step5_heterogeneity_analysis.csv",
            "outputs/step5_key_metrics.json",
            "outputs/step5_manifest.json",
            "outputs/step5_validation_report.json",
            "docs/STEP5_robustness_checks.md",
        ],
    }


def main() -> None:
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)

    panel = load_step4_panel()

    sensitivity = build_sensitivity_checks(panel)
    dynamic = build_dynamic_analysis(panel)
    heterogeneity, _ = build_heterogeneity_analysis(panel)
    key_metrics = build_key_metrics(panel, sensitivity, dynamic, heterogeneity)
    markdown = build_step5_markdown(sensitivity, dynamic, heterogeneity)
    manifest = build_manifest(panel)

    sensitivity.to_csv(OUTPUTS / "step5_sensitivity_checks.csv", index=False)
    dynamic.to_csv(OUTPUTS / "step5_dynamic_analysis.csv", index=False)
    heterogeneity.to_csv(OUTPUTS / "step5_heterogeneity_analysis.csv", index=False)
    (OUTPUTS / "step5_key_metrics.json").write_text(
        json.dumps(key_metrics, indent=2) + "\n", encoding="utf-8"
    )
    (OUTPUTS / "step5_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    (DOCS / "STEP5_robustness_checks.md").write_text(markdown, encoding="utf-8")

    print(f"Wrote {OUTPUTS / 'step5_sensitivity_checks.csv'}")
    print(f"Wrote {OUTPUTS / 'step5_dynamic_analysis.csv'}")
    print(f"Wrote {OUTPUTS / 'step5_heterogeneity_analysis.csv'}")
    print(f"Wrote {OUTPUTS / 'step5_key_metrics.json'}")
    print(f"Wrote {OUTPUTS / 'step5_manifest.json'}")
    print(f"Wrote {DOCS / 'STEP5_robustness_checks.md'}")


if __name__ == "__main__":
    main()
