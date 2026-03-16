# Step 4 Baseline Econometric Model

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

- `issues_opened`: 5.9985 (p=0.0001)
- `median_close_days`: 0.5614 (p=0.0785)
- `avg_first_response_hours`: 2.5500 (p=0.0000)
- `backlog_open_end_month`: 3.0296 (p=0.3218)
- `issue_burden_index`: 0.7349 (p=0.0000)

A cross-implementation sanity check in `statsmodels` (`outputs/step4_statsmodels_sanity_check.csv`) confirms the same positive treatment-direction for core outcomes.

## Identification diagnostics
- Event-study pretrend joint Wald p-value (k ≤ -2): 1.0000
- Mean pre-period event coefficient: -5.9937
- Mean post-period event coefficient: 4.1305
- Pre-period placebo test p-value (split at 2021-06): 0.8628

## Variance structure insight
Between-ecosystem share of variation:

- `issues_opened`: 0.535
- `avg_first_response_hours`: 0.356
- `backlog_open_end_month`: 0.276

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
