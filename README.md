# ChatGPT and the Shift from Stack Overflow to GitHub Issue Burden

Canonical project repo for the approved topic:
`tech-econ-chatgpt-stackoverflow-github-issue-burden`

## Status
- ✅ Step 1: problem framing
- ✅ Step 2: data extraction specification and preanalysis lock
- ✅ Step 3: exploratory analysis and identification-ready scaffolding
- ✅ Step 4: baseline econometric model + identification diagnostics
- ⏳ Step 5: robustness checks
- ⏳ Step 6: dynamic and heterogeneity checks
- ⏳ Step 7: final synthesis package

## Research question
After ChatGPT's public launch, did software ecosystems that relied more heavily on Stack Overflow experience a larger increase in GitHub issue burden?

## Current repository scope
This repository now includes:
- a locked ecosystem-month panel design;
- a synthetic demonstration dataset used to validate structure and pipeline logic;
- Step 3 exploratory summaries and identification-ready transformations;
- Step 4 model-ready pipeline outputs with advanced EDA artifacts;
- baseline two-way fixed-effects estimates (linearmodels PanelOLS);
- event-study, placebo, and leave-one-ecosystem-out diagnostics; and
- reproducible validation reports for each step.

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
├── docs/
│   ├── STEP1_problem_framing.md
│   ├── STEP2_data_extraction_spec.md
│   ├── STEP2_preanalysis_lock.md
│   ├── STEP3_exploratory_analysis.md
│   └── STEP4_baseline_econometric_model.md
├── notebooks/
│   ├── STEP2_synthetic_panel_walkthrough.ipynb
│   ├── STEP3_exploratory_analysis.ipynb
│   └── STEP4_baseline_econometric_model.ipynb
├── outputs/
│   ├── step2_*.csv/json
│   ├── step3_*.csv/json
│   └── step4_*.csv/json
└── scripts/
    ├── build_step2_synthetic_panel.py
    ├── build_step3_analysis.py
    ├── build_step4_econometrics.py
    ├── run_step3_eda.py
    ├── run_step3_pipeline.py
    ├── run_step4_econometrics.py
    ├── run_step4_pipeline.py
    ├── validate_step2_outputs.py
    ├── validate_step3_outputs.py
    └── validate_step4_outputs.py
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

## Reproduce Step 4 outputs
From the repository root:

```bash
python3 -m venv .venv-step4
source .venv-step4/bin/activate
pip install -r requirements-step4.txt
python scripts/run_step4_pipeline.py
```

If Step 2 and Step 3 artifacts already exist and you only want the Step 4 layer:

```bash
source .venv-step4/bin/activate
python scripts/run_step4_econometrics.py
```

## Step 4 summary takeaway
In the synthetic panel, the baseline fixed-effects model with controls preserves the directional pattern from Step 3: higher pre-period Stack Overflow dependence is associated with larger post-launch increases in issue inflow and response-time burden. Step 4 adds richer diagnostics (event-study, placebo split, and leave-one-ecosystem-out sensitivity) so that Step 5 can focus on robustness and alternative specifications.

## Current interpretation boundary
This repository still does **not** claim empirical estimates from live public data. Step 4 is a reproducible synthetic econometric validation stage that stress-tests identification logic before real-data implementation.
