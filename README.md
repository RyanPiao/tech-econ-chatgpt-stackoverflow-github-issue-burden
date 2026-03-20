# ChatGPT and the Shift from Stack Overflow to GitHub Issue Burden

Canonical project repo for the approved topic:
`tech-econ-chatgpt-stackoverflow-github-issue-burden`

## Status
- ✅ Step 1: problem framing
- ✅ Step 2: data extraction specification and preanalysis lock
- ✅ Step 3: exploratory analysis and identification-ready scaffolding
- ✅ Step 4: baseline econometric model + identification diagnostics
- ✅ Step 5: robustness checks (sensitivity, dynamics, heterogeneity)
- ✅ Step 6: finalized model + alternative-explanation robustness package
- ⏳ Step 7: final synthesis package

## Research question
After ChatGPT's public launch, did software ecosystems that relied more heavily on Stack Overflow experience a larger increase in GitHub issue burden?

## Current repository scope
This repository now includes:
- a locked ecosystem-month panel design;
- a synthetic demonstration dataset used to validate structure and pipeline logic;
- Step 3 exploratory summaries and identification-ready transformations;
- Step 4 model-ready pipeline outputs with advanced EDA artifacts and baseline FE estimates;
- Step 5 robustness outputs covering covariance sensitivity, transformation checks, permutation inference, event-study dynamics, and subgroup heterogeneity;
- Step 6 finalized model outputs with trend-adjusted TWFE and alternative-explanation diagnostics; and
- reproducible validation reports for each implemented step.

## Why the current data are synthetic
The intended long-run design uses public-source data. The current repository ships a synthetic demonstration panel instead of a live public scrape.

That choice is deliberate. A quick partial scrape would be easy to over-interpret, while a transparent synthetic panel lets readers inspect the data structure, variable definitions, merge logic, exploratory summaries, and model code without mistaking the present outputs for real-world evidence. The synthetic files in this repository are for **workflow validation and method development only**.

## Core variables
- **Primary outcome family:** GitHub issue burden, measured with issue-open counts, median close duration, and month-end open backlog
- **Secondary outcome:** average hours to first maintainer response
- **Treatment variable:** post-ChatGPT exposure interacted with a pre-period Stack Overflow dependence measure
- **Unit of analysis:** ecosystem-month

## Repository structure
```text
.
├── README.md
├── requirements-step2.txt
├── requirements-step3.txt
├── requirements-step4.txt
├── requirements-step5.txt
├── requirements-step6.txt
├── docs/
│   ├── STEP1_problem_framing.md
│   ├── STEP2_data_extraction_spec.md
│   ├── STEP2_preanalysis_lock.md
│   ├── STEP3_exploratory_analysis.md
│   ├── STEP4_baseline_econometric_model.md
│   ├── STEP5_robustness_checks.md
│   └── STEP6_robustness_and_polish.md
├── notebooks/
│   ├── STEP2_synthetic_panel_walkthrough.ipynb
│   ├── STEP3_exploratory_analysis.ipynb
│   ├── STEP4_baseline_econometric_model.ipynb
│   └── STEP6_robustness_and_polish.ipynb
├── outputs/
│   ├── step2_*.csv/json
│   ├── step3_*.csv/json
│   ├── step4_*.csv/json
│   ├── step5_*.csv/json
│   └── step6_*.csv/json
└── scripts/
    ├── build_step2_synthetic_panel.py
    ├── build_step3_analysis.py
    ├── build_step4_econometrics.py
    ├── build_step5_robustness.py
    ├── build_step6_final_model.py
    ├── run_step3_eda.py
    ├── run_step3_pipeline.py
    ├── run_step4_econometrics.py
    ├── run_step4_pipeline.py
    ├── run_step5_robustness.py
    ├── run_step5_pipeline.py
    ├── run_step6_finalize.py
    ├── run_step6_pipeline.py
    ├── validate_step2_outputs.py
    ├── validate_step3_outputs.py
    ├── validate_step4_outputs.py
    ├── validate_step5_outputs.py
    └── validate_step6_outputs.py
```

## Step artifacts

### Step 1
- `docs/STEP1_problem_framing.md`

### Step 2
- `docs/STEP2_data_extraction_spec.md`
- `docs/STEP2_preanalysis_lock.md`
- `requirements-step2.txt`
- `scripts/build_step2_synthetic_panel.py`
- `scripts/validate_step2_outputs.py`
- `notebooks/STEP2_synthetic_panel_walkthrough.ipynb`
- `outputs/step2_synthetic_panel.csv`
- `outputs/step2_variable_dictionary.csv`
- `outputs/step2_manifest.json`
- `outputs/step2_validation_report.json`

### Step 3
- `docs/STEP3_exploratory_analysis.md`
- `requirements-step3.txt`
- `scripts/build_step3_analysis.py`
- `scripts/validate_step3_outputs.py`
- `scripts/run_step3_eda.py`
- `scripts/run_step3_pipeline.py`
- `notebooks/STEP3_exploratory_analysis.ipynb`
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
- `outputs/step3_validation_report.json`

### Step 4
- `docs/STEP4_baseline_econometric_model.md`
- `requirements-step4.txt`
- `scripts/build_step4_econometrics.py`
- `scripts/validate_step4_outputs.py`
- `scripts/run_step4_econometrics.py`
- `scripts/run_step4_pipeline.py`
- `notebooks/STEP4_baseline_econometric_model.ipynb`
- `outputs/step4_model_panel.csv`
- `outputs/step4_eda_distribution_summary.csv`
- `outputs/step4_outcome_correlation.csv`
- `outputs/step4_variance_decomposition.csv`
- `outputs/step4_twfe_models.csv`
- `outputs/step4_event_study_issues_opened.csv`
- `outputs/step4_placebo_test.csv`
- `outputs/step4_leave_one_ecosystem_out.csv`
- `outputs/step4_identification_diagnostics.csv`
- `outputs/step4_key_metrics.json`
- `outputs/step4_manifest.json`
- `outputs/step4_validation_report.json`

### Step 5
- `docs/STEP5_robustness_checks.md`
- `requirements-step5.txt`
- `scripts/build_step5_robustness.py`
- `scripts/validate_step5_outputs.py`
- `scripts/run_step5_robustness.py`
- `scripts/run_step5_pipeline.py`
- `outputs/step5_sensitivity_checks.csv`
- `outputs/step5_dynamic_analysis.csv`
- `outputs/step5_heterogeneity_analysis.csv`
- `outputs/step5_key_metrics.json`
- `outputs/step5_manifest.json`
- `outputs/step5_validation_report.json`

### Step 6
- `docs/STEP6_robustness_and_polish.md`
- `requirements-step6.txt`
- `scripts/build_step6_final_model.py`
- `scripts/validate_step6_outputs.py`
- `scripts/run_step6_finalize.py`
- `scripts/run_step6_pipeline.py`
- `notebooks/STEP6_robustness_and_polish.ipynb`
- `outputs/step6_finalized_model_results.csv`
- `outputs/step6_alternative_explanations.csv`
- `outputs/step6_cutoff_sweep.csv`
- `outputs/step6_key_metrics.json`
- `outputs/step6_manifest.json`
- `outputs/step6_validation_report.json`

## Reproduce Step 6 outputs
From the repository root:

```bash
python3 -m venv .venv-step6
source .venv-step6/bin/activate
pip install -r requirements-step6.txt
python scripts/run_step6_pipeline.py
```

If Step 2–Step 5 artifacts already exist and you only want the Step 6 layer:

```bash
source .venv-step6/bin/activate
python scripts/run_step6_finalize.py
```

## Step 6 summary takeaway
In the synthetic panel, the finalized trend-adjusted TWFE model keeps a positive treatment-intensity effect for issue inflow and first-response burden. Alternative-explanation checks (weighting, lag control, symmetric windows, lead placebo, ratio outcomes) remain directionally aligned in most cases, while adding direct Stack Overflow activity controls attenuates precision, suggesting channel overlap rather than a clean contradiction.

## Current interpretation boundary
This repository still does **not** claim empirical estimates from live public data. Step 6 remains a synthetic robustness-validation stage designed to finalize specification choices and stress-test alternative explanations before real-data implementation.
