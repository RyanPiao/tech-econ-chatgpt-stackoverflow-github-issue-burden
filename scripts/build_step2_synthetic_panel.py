from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"
SEED = 20260312
POST_START = pd.Timestamp("2022-12-01")

ECOSYSTEMS = [
    {
        "ecosystem": "python",
        "stack_overflow_tag_anchor": "python",
        "github_repo_group": "psf/requests | pandas-dev/pandas | pallets/flask",
        "representative_repo_count": 3,
        "so_dependence_pre": 0.82,
        "baseline_active_repos": 138,
    },
    {
        "ecosystem": "javascript",
        "stack_overflow_tag_anchor": "javascript",
        "github_repo_group": "nodejs/node | expressjs/express | webpack/webpack",
        "representative_repo_count": 3,
        "so_dependence_pre": 0.76,
        "baseline_active_repos": 154,
    },
    {
        "ecosystem": "reactjs",
        "stack_overflow_tag_anchor": "reactjs",
        "github_repo_group": "facebook/react | reduxjs/redux | vercel/next.js",
        "representative_repo_count": 3,
        "so_dependence_pre": 0.73,
        "baseline_active_repos": 116,
    },
    {
        "ecosystem": "django",
        "stack_overflow_tag_anchor": "django",
        "github_repo_group": "django/django | encode/django-rest-framework",
        "representative_repo_count": 2,
        "so_dependence_pre": 0.69,
        "baseline_active_repos": 92,
    },
    {
        "ecosystem": "tensorflow",
        "stack_overflow_tag_anchor": "tensorflow",
        "github_repo_group": "tensorflow/tensorflow | keras-team/keras",
        "representative_repo_count": 2,
        "so_dependence_pre": 0.62,
        "baseline_active_repos": 97,
    },
    {
        "ecosystem": "pytorch",
        "stack_overflow_tag_anchor": "pytorch",
        "github_repo_group": "pytorch/pytorch | lightning-ai/pytorch-lightning",
        "representative_repo_count": 2,
        "so_dependence_pre": 0.48,
        "baseline_active_repos": 88,
    },
    {
        "ecosystem": "kubernetes",
        "stack_overflow_tag_anchor": "kubernetes",
        "github_repo_group": "kubernetes/kubernetes | helm/helm",
        "representative_repo_count": 2,
        "so_dependence_pre": 0.41,
        "baseline_active_repos": 110,
    },
    {
        "ecosystem": "rust",
        "stack_overflow_tag_anchor": "rust",
        "github_repo_group": "rust-lang/rust | tokio-rs/tokio",
        "representative_repo_count": 2,
        "so_dependence_pre": 0.34,
        "baseline_active_repos": 84,
    },
]

VARIABLE_DICTIONARY = [
    {
        "variable": "month",
        "dtype": "date",
        "definition": "Calendar month for the ecosystem-month panel row.",
        "role": "index",
    },
    {
        "variable": "ecosystem",
        "dtype": "string",
        "definition": "Technology ecosystem grouped from Stack Overflow tags and representative GitHub repositories.",
        "role": "index",
    },
    {
        "variable": "stack_overflow_tag_anchor",
        "dtype": "string",
        "definition": "Main Stack Overflow tag used to define the ecosystem in Step 2.",
        "role": "mapping",
    },
    {
        "variable": "github_repo_group",
        "dtype": "string",
        "definition": "Representative public GitHub repositories associated with the ecosystem.",
        "role": "mapping",
    },
    {
        "variable": "representative_repo_count",
        "dtype": "integer",
        "definition": "Count of representative repositories in the GitHub group mapping.",
        "role": "descriptor",
    },
    {
        "variable": "month_index",
        "dtype": "integer",
        "definition": "Zero-based sequential month index in the sample window.",
        "role": "time",
    },
    {
        "variable": "post_chatgpt",
        "dtype": "integer",
        "definition": "Indicator equal to 1 for months beginning in 2022-12 and later, 0 otherwise.",
        "role": "treatment_timing",
    },
    {
        "variable": "so_dependence_pre",
        "dtype": "float",
        "definition": "Pre-period Stack Overflow dependence score fixed before the intervention. In the synthetic demonstration this is assigned transparently, not estimated from real public data.",
        "role": "treatment_intensity",
    },
    {
        "variable": "treatment_intensity",
        "dtype": "float",
        "definition": "Interaction of post_chatgpt and so_dependence_pre.",
        "role": "treatment_intensity",
    },
    {
        "variable": "active_repos_observed",
        "dtype": "integer",
        "definition": "Synthetic count of active repositories observed in the ecosystem-month.",
        "role": "descriptor",
    },
    {
        "variable": "stackoverflow_questions_month",
        "dtype": "integer",
        "definition": "Synthetic monthly Stack Overflow question count aligned to the ecosystem anchor tag.",
        "role": "input_proxy",
    },
    {
        "variable": "issues_opened",
        "dtype": "integer",
        "definition": "Synthetic count of GitHub issues opened in the ecosystem-month.",
        "role": "primary_outcome",
    },
    {
        "variable": "median_close_days",
        "dtype": "float",
        "definition": "Synthetic median issue close duration in days for issues closed in the month.",
        "role": "primary_outcome",
    },
    {
        "variable": "avg_first_response_hours",
        "dtype": "float",
        "definition": "Synthetic average hours from issue open to first maintainer response.",
        "role": "secondary_outcome",
    },
    {
        "variable": "backlog_open_end_month",
        "dtype": "integer",
        "definition": "Synthetic count of still-open issues at month end.",
        "role": "primary_outcome",
    },
    {
        "variable": "is_synthetic",
        "dtype": "integer",
        "definition": "Indicator equal to 1 for all rows in this Step 2 demonstration panel.",
        "role": "provenance",
    },
]


def build_panel() -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    months = pd.date_range("2021-01-01", "2024-12-01", freq="MS")
    rows = []

    for eco_idx, eco in enumerate(ECOSYSTEMS):
        eco_noise = rng.normal(0, 0.02, size=len(months))
        season = np.sin(np.linspace(0, 4 * np.pi, len(months)) + eco_idx / 3)

        for month_index, month in enumerate(months):
            post = int(month >= POST_START)
            trend = month_index / 12
            seasonal_component = season[month_index]
            intensity = eco["so_dependence_pre"] * post

            active_repos = int(
                round(
                    eco["baseline_active_repos"]
                    + 1.4 * trend
                    + 4.5 * seasonal_component
                    + rng.normal(0, 2.5)
                )
            )
            active_repos = max(active_repos, eco["representative_repo_count"])

            so_questions = int(
                round(
                    140
                    + 360 * eco["so_dependence_pre"]
                    + 11 * seasonal_component
                    - 7 * trend
                    - 32 * post * eco["so_dependence_pre"]
                    + rng.normal(0, 10)
                )
            )
            so_questions = max(so_questions, 10)

            issues_opened = int(
                round(
                    26
                    + 0.18 * active_repos
                    + 9 * eco["so_dependence_pre"]
                    + 2.8 * trend
                    + 1.8 * seasonal_component
                    + 7.0 * intensity
                    + rng.normal(0, 2.0)
                )
            )
            issues_opened = max(issues_opened, 1)

            median_close_days = round(
                8.5
                + 1.5 * eco["so_dependence_pre"]
                + 0.12 * trend
                + 1.1 * intensity
                + 0.45 * eco_noise[month_index]
                + rng.normal(0, 0.55),
                2,
            )
            median_close_days = max(median_close_days, 0.25)

            avg_first_response_hours = round(
                11.0
                + 4.0 * eco["so_dependence_pre"]
                + 0.18 * trend
                + 2.1 * intensity
                + rng.normal(0, 0.8),
                2,
            )
            avg_first_response_hours = max(avg_first_response_hours, 0.1)

            backlog_open_end_month = int(
                round(
                    110
                    + 0.55 * issues_opened
                    + 12 * eco["so_dependence_pre"]
                    + 2.5 * trend
                    + 6.0 * intensity
                    + rng.normal(0, 5.0)
                )
            )
            backlog_open_end_month = max(backlog_open_end_month, 0)

            rows.append(
                {
                    "month": month,
                    "ecosystem": eco["ecosystem"],
                    "stack_overflow_tag_anchor": eco["stack_overflow_tag_anchor"],
                    "github_repo_group": eco["github_repo_group"],
                    "representative_repo_count": eco["representative_repo_count"],
                    "month_index": month_index,
                    "post_chatgpt": post,
                    "so_dependence_pre": eco["so_dependence_pre"],
                    "treatment_intensity": round(intensity, 4),
                    "active_repos_observed": active_repos,
                    "stackoverflow_questions_month": so_questions,
                    "issues_opened": issues_opened,
                    "median_close_days": median_close_days,
                    "avg_first_response_hours": avg_first_response_hours,
                    "backlog_open_end_month": backlog_open_end_month,
                    "is_synthetic": 1,
                }
            )

    panel = pd.DataFrame(rows).sort_values(["ecosystem", "month"]).reset_index(drop=True)
    panel["month"] = pd.to_datetime(panel["month"]).dt.strftime("%Y-%m-%d")
    return panel


def build_manifest(panel: pd.DataFrame) -> dict:
    return {
        "artifact": "Step 2 synthetic demonstration panel",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "seed": SEED,
        "sample_start": panel["month"].min(),
        "sample_end": panel["month"].max(),
        "n_rows": int(len(panel)),
        "n_ecosystems": int(panel["ecosystem"].nunique()),
        "panel_frequency": "monthly",
        "unit_of_analysis": "ecosystem-month",
        "intervention_timing": "2022-11-30 public launch; post indicator begins at 2022-12 monthly observations",
        "provenance": "synthetic demonstration only",
        "synthetic_note": (
            "This file is a transparent synthetic demonstration used to validate Step 2 schema, merging logic, "
            "and preanalysis scaffolding without claiming empirical findings from real public-source extraction."
        ),
    }


def main() -> None:
    OUTPUTS.mkdir(parents=True, exist_ok=True)

    panel = build_panel()
    panel_path = OUTPUTS / "step2_synthetic_panel.csv"
    panel.to_csv(panel_path, index=False)

    dictionary = pd.DataFrame(VARIABLE_DICTIONARY)
    dictionary_path = OUTPUTS / "step2_variable_dictionary.csv"
    dictionary.to_csv(dictionary_path, index=False)

    manifest = build_manifest(panel)
    manifest_path = OUTPUTS / "step2_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(f"Wrote {panel_path}")
    print(f"Wrote {dictionary_path}")
    print(f"Wrote {manifest_path}")


if __name__ == "__main__":
    main()
