from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"
INPUT_PANEL = OUTPUTS / "step2_synthetic_panel.csv"


def load_panel() -> pd.DataFrame:
    df = pd.read_csv(INPUT_PANEL, parse_dates=["month"])
    df = df.sort_values(["ecosystem", "month"]).reset_index(drop=True)
    df["post_label"] = np.where(df["post_chatgpt"] == 1, "Post-ChatGPT", "Pre-ChatGPT")
    df["issues_per_repo"] = df["issues_opened"] / df["active_repos_observed"]
    df["backlog_per_repo"] = df["backlog_open_end_month"] / df["active_repos_observed"]
    df["high_so_dependence"] = (df["so_dependence_pre"] >= df["so_dependence_pre"].median()).astype(int)
    return df


def build_ecosystem_summary(df: pd.DataFrame) -> pd.DataFrame:
    summary = (
        df.groupby("ecosystem", as_index=False)
        .agg(
            so_dependence_pre=("so_dependence_pre", "first"),
            avg_issues_opened=("issues_opened", "mean"),
            avg_close_days=("median_close_days", "mean"),
            avg_response_hours=("avg_first_response_hours", "mean"),
            avg_backlog=("backlog_open_end_month", "mean"),
            avg_issues_per_repo=("issues_per_repo", "mean"),
        )
        .sort_values("so_dependence_pre", ascending=False)
    )
    return summary.round(3)


def build_prepost_summary(df: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        df.groupby(["high_so_dependence", "post_label"], as_index=False)
        .agg(
            mean_issues_opened=("issues_opened", "mean"),
            mean_close_days=("median_close_days", "mean"),
            mean_response_hours=("avg_first_response_hours", "mean"),
            mean_backlog=("backlog_open_end_month", "mean"),
            mean_issues_per_repo=("issues_per_repo", "mean"),
        )
    )
    grouped["dependence_group"] = grouped["high_so_dependence"].map({1: "High pre-period Stack Overflow dependence", 0: "Low pre-period Stack Overflow dependence"})
    grouped = grouped.drop(columns=["high_so_dependence"])
    return grouped.round(3)


def run_twfe_preview(df: pd.DataFrame) -> pd.DataFrame:
    outcomes = [
        "issues_opened",
        "median_close_days",
        "avg_first_response_hours",
        "backlog_open_end_month",
    ]
    results = []
    for outcome in outcomes:
        model = smf.ols(
            f"{outcome} ~ treatment_intensity + C(ecosystem) + C(month)",
            data=df,
        ).fit(cov_type="HC1")
        coef = model.params["treatment_intensity"]
        se = model.bse["treatment_intensity"]
        results.append(
            {
                "outcome": outcome,
                "coef_treatment_intensity": round(float(coef), 4),
                "se_hc1": round(float(se), 4),
                "t_stat": round(float(model.tvalues["treatment_intensity"]), 4),
                "p_value": round(float(model.pvalues["treatment_intensity"]), 6),
                "n_obs": int(model.nobs),
                "r_squared": round(float(model.rsquared), 4),
            }
        )
    return pd.DataFrame(results)


def build_key_metrics(df: pd.DataFrame) -> dict:
    high = df[df["high_so_dependence"] == 1]
    low = df[df["high_so_dependence"] == 0]

    def prepost_change(frame: pd.DataFrame, column: str) -> float:
        pre = frame.loc[frame["post_chatgpt"] == 0, column].mean()
        post = frame.loc[frame["post_chatgpt"] == 1, column].mean()
        return round(float(post - pre), 3)

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "panel_rows": int(len(df)),
        "ecosystem_count": int(df["ecosystem"].nunique()),
        "sample_start": str(df["month"].min().date()),
        "sample_end": str(df["month"].max().date()),
        "high_dependence_prepost_change_issues": prepost_change(high, "issues_opened"),
        "low_dependence_prepost_change_issues": prepost_change(low, "issues_opened"),
        "high_dependence_prepost_change_backlog": prepost_change(high, "backlog_open_end_month"),
        "low_dependence_prepost_change_backlog": prepost_change(low, "backlog_open_end_month"),
        "high_dependence_prepost_change_close_days": prepost_change(high, "median_close_days"),
        "low_dependence_prepost_change_close_days": prepost_change(low, "median_close_days"),
    }


def main() -> None:
    OUTPUTS.mkdir(exist_ok=True)
    df = load_panel()

    ecosystem_summary = build_ecosystem_summary(df)
    prepost_summary = build_prepost_summary(df)
    twfe_preview = run_twfe_preview(df)
    key_metrics = build_key_metrics(df)

    ecosystem_summary.to_csv(OUTPUTS / "step3_ecosystem_summary.csv", index=False)
    prepost_summary.to_csv(OUTPUTS / "step3_prepost_summary.csv", index=False)
    twfe_preview.to_csv(OUTPUTS / "step3_twfe_preview.csv", index=False)
    (OUTPUTS / "step3_key_metrics.json").write_text(json.dumps(key_metrics, indent=2) + "\n")

    manifest = {
        "step": 3,
        "description": "Exploratory analysis and fixed-effects preview on the synthetic ecosystem-month panel.",
        "source_panel": str(INPUT_PANEL.relative_to(ROOT)),
        "artifacts": [
            "outputs/step3_ecosystem_summary.csv",
            "outputs/step3_prepost_summary.csv",
            "outputs/step3_twfe_preview.csv",
            "outputs/step3_key_metrics.json",
        ],
        "reproduce": [
            "python3 -m venv .venv-step3",
            "source .venv-step3/bin/activate",
            "pip install -r requirements-step3.txt",
            "python scripts/run_step3_eda.py",
        ],
    }
    (OUTPUTS / "step3_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
