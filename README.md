# ChatGPT and the Shift from Stack Overflow to GitHub Issue Burden

Canonical project repo for the approved topic:
`tech-econ-chatgpt-stackoverflow-github-issue-burden`

## Status
- ✅ Step 1: problem framing
- ✅ Step 2: data extraction specification and preanalysis lock
- ✅ Step 3: exploratory analysis and identification-ready scaffolding
- ⏳ Step 4: baseline econometric model
- ⏳ Step 5: robustness checks
- ⏳ Step 6: dynamic and heterogeneity checks
- ⏳ Step 7: final synthesis package

## Research question
After ChatGPT's public launch, did software ecosystems that relied more heavily on Stack Overflow experience a larger increase in GitHub issue burden?

## Current repository scope
This repository now includes:
- a locked ecosystem-month panel design;
- a synthetic demonstration dataset used to validate structure and pipeline logic;
- exploratory summaries comparing higher- and lower-dependence ecosystems; and
- a first-pass fixed-effects preview that checks whether the synthetic panel moves in the hypothesized direction.

## Why the current data are synthetic
The intended long-run design uses public-source data. The current repository ships a synthetic demonstration panel instead of a live public scrape.

That choice is deliberate. A quick partial scrape would be easy to over-interpret, while a transparent synthetic panel lets readers inspect the data structure, variable definitions, merge logic, and model code without mistaking the present outputs for real-world evidence. The synthetic files in this repository are for **workflow validation and exploratory modeling only**.

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
├── docs/
│   ├── STEP1_problem_framing.md
│   ├── STEP2_data_extraction_spec.md
│   ├── STEP2_preanalysis_lock.md
│   └── STEP3_exploratory_analysis.md
├── notebooks/
│   └── STEP2_synthetic_panel_walkthrough.ipynb
├── outputs/
│   ├── step2_manifest.json
│   ├── step2_synthetic_panel.csv
│   ├── step2_validation_report.json
│   ├── step2_variable_dictionary.csv
│   ├── step3_ecosystem_summary.csv
│   ├── step3_key_metrics.json
│   ├── step3_manifest.json
│   ├── step3_prepost_summary.csv
│   └── step3_twfe_preview.csv
└── scripts/
    ├── build_step2_synthetic_panel.py
    ├── run_step3_eda.py
    └── validate_step2_outputs.py
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
- `scripts/run_step3_eda.py`
- `outputs/step3_ecosystem_summary.csv`
- `outputs/step3_prepost_summary.csv`
- `outputs/step3_twfe_preview.csv`
- `outputs/step3_key_metrics.json`
- `outputs/step3_manifest.json`

## Reproduce Step 3 outputs
From the repository root:

```bash
python3 -m venv .venv-step3
source .venv-step3/bin/activate
pip install -r requirements-step3.txt
python scripts/run_step3_eda.py
```

## Step 3 preview takeaway
In the synthetic panel, ecosystems with higher pre-period Stack Overflow dependence show somewhat larger post-ChatGPT increases in issue inflow, first-response delay, and close-duration pressure. The backlog signal is weaker, which makes it a natural target for deeper model refinement in the next step.

## Current interpretation boundary
This repository still does **not** claim empirical estimates from live public data. Step 3 is an exploratory check that the panel design, summary statistics, and fixed-effects scaffold behave coherently before the baseline econometric specification is formalized in Step 4.
