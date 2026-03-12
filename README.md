# ChatGPT and the Shift from Stack Overflow to GitHub Issue Burden

Canonical project repo for the approved topic:
`tech-econ-chatgpt-stackoverflow-github-issue-burden`

## Status
- ✅ Step 1: problem framing
- ✅ Step 2: data extraction specification and preanalysis lock
- ⏳ Step 3: exploratory analysis artifacts
- ⏳ Step 4: baseline econometric model
- ⏳ Step 5: robustness checks
- ⏳ Step 6: dynamic and heterogeneity checks
- ⏳ Step 7: final synthesis package

## Research question
After ChatGPT's public launch, did software ecosystems that relied more heavily on Stack Overflow experience a larger increase in GitHub issue burden?

## Step 2 summary
This repository now includes a reproducible Step 2 handoff built around:
- a locked ecosystem-month panel design;
- a public-source extraction specification for Stack Overflow / Stack Exchange and GitHub issue histories;
- a preanalysis lock that fixes the core treatment, timing, and outcome definitions; and
- a synthetic demonstration dataset that validates the schema and pipeline without pretending to be empirical evidence.

## Why the current Step 2 data are synthetic
The intended long-run design uses public-source data. For this Step 2 handoff, the repository ships a synthetic demonstration panel instead of a live public scrape.

That is intentional. A quick partial scrape would be easy to misread as real evidence, while a transparent synthetic panel lets readers inspect the data structure, variable definitions, merge logic, and validation checks in a reproducible way. The synthetic files in this repository are for **pipeline validation only**.

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
├── docs/
│   ├── STEP1_problem_framing.md
│   ├── STEP2_data_extraction_spec.md
│   └── STEP2_preanalysis_lock.md
├── notebooks/
│   └── STEP2_synthetic_panel_walkthrough.ipynb
├── outputs/
│   ├── step2_manifest.json
│   ├── step2_synthetic_panel.csv
│   ├── step2_validation_report.json
│   └── step2_variable_dictionary.csv
└── scripts/
    ├── build_step2_synthetic_panel.py
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

## Reproduce Step 2 outputs
From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-step2.txt
python scripts/build_step2_synthetic_panel.py
python scripts/validate_step2_outputs.py
```

## Current interpretation boundary
This repository does **not** yet report empirical findings about the magnitude or welfare implications of any shift from Stack Overflow toward GitHub issues. Step 2 only fixes the extraction plan, variable definitions, and analysis-ready panel structure needed for later work.
