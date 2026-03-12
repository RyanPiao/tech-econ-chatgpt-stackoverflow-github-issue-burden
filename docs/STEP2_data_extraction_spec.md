# Step 2 — Data Extraction Specification

## Purpose
This Step 2 document fixes the data structure, source plan, variable definitions, and reproducible handoff for the project **"ChatGPT and the shift from Stack Overflow to GitHub issue burden."**

The goal at this stage is not to claim empirical findings. The goal is to make the eventual data build auditable and reproducible.

## Step 2 source mode used here
The empirical design still targets **public-source data** from Stack Overflow / Stack Exchange and GitHub public issue histories.

For this week's Step 2 handoff, the repository ships a **synthetic demonstration panel** instead of a live public-data extract.

That choice is deliberate and transparent:
- high-volume public extraction and tag-to-repository mapping are feasible in principle, but not yet packaged here in a way that is lightweight and reproducible for any public reader;
- a synthetic panel lets reviewers inspect the schema, merge logic, treatment construction, and validation checks without mistaking a quick partial scrape for real evidence;
- no synthetic file in this repository should be interpreted as an empirical result.

## Unit of analysis
The locked Step 2 unit is:
- **ecosystem-month**

An ecosystem-month row combines:
1. a Stack Overflow tag anchor representing support demand in that ecosystem; and
2. a mapped public GitHub repository group representing issue-tracker burden for the same ecosystem.

## Sample window
The Step 2 demonstration panel uses:
- **2021-01 through 2024-12**, monthly frequency

This window gives a clean pre-period and post-period around ChatGPT's public launch on **2022-11-30**.

## Intervention timing
The post indicator is defined as:
- `post_chatgpt = 1` for months beginning **2022-12-01** and later
- `post_chatgpt = 0` otherwise

## Candidate ecosystem mapping frame
The current mapping frame is intentionally compact so that Step 3+ work can remain interpretable.

| ecosystem | Stack Overflow tag anchor | Representative GitHub repositories | Why included |
|---|---|---|---|
| python | `python` | `psf/requests`, `pandas-dev/pandas`, `pallets/flask` | Large public support footprint and broad issue activity |
| javascript | `javascript` | `nodejs/node`, `expressjs/express`, `webpack/webpack` | High public Q&A volume and mature open-source ecosystem |
| reactjs | `reactjs` | `facebook/react`, `reduxjs/redux`, `vercel/next.js` | Front-end ecosystem with strong forum and repository activity |
| django | `django` | `django/django`, `encode/django-rest-framework` | Clear tag identity and established issue processes |
| tensorflow | `tensorflow` | `tensorflow/tensorflow`, `keras-team/keras` | AI/ML ecosystem with substantial public troubleshooting |
| pytorch | `pytorch` | `pytorch/pytorch`, `lightning-ai/pytorch-lightning` | AI/ML comparison ecosystem with active maintainer workflows |
| kubernetes | `kubernetes` | `kubernetes/kubernetes`, `helm/helm` | Infrastructure ecosystem with heavy issue usage |
| rust | `rust` | `rust-lang/rust`, `tokio-rs/tokio` | Strong open-source identity and public support channels |

This table is a Step 2 mapping frame, not a final claim that these are the only valid ecosystems.

## Intended public-source inputs for later real extraction

### 1) Stack Overflow / Stack Exchange side
Target fields for real extraction:
- monthly question counts by anchor tag
- unanswered or low-answer share when available
- question volume in the pre-period used to construct dependence intensity

Potential public routes:
- Stack Exchange Data Explorer exports
- Stack Exchange public data dump
- BigQuery or equivalent public mirrors where available

Step 2 lock for treatment construction:
- the dependence measure must be formed from **pre-period information only**;
- no post-period Stack Overflow activity may be used to redefine treatment intensity.

### 2) GitHub side
Target fields for real extraction:
- issue-open counts by month
- closure timing and time-to-close summaries
- first-response timing when recoverable from public issue and comment histories
- month-end open backlog counts

Potential public routes:
- GitHub public API extraction for selected repositories
- GH Archive issue event histories plus repository metadata where feasible

Step 2 lock for outcome construction:
- outcomes are repository-group summaries rolled up to the ecosystem-month level;
- issue and pull request records must remain separated;
- outcome construction must be identical across ecosystems.

## Locked Step 2 variables
The canonical Step 2 panel contains these fields:

| variable | role | definition |
|---|---|---|
| `month` | index | Calendar month |
| `ecosystem` | index | Ecosystem identifier |
| `stack_overflow_tag_anchor` | mapping | Main Stack Overflow tag used for the ecosystem |
| `github_repo_group` | mapping | Representative GitHub repositories for the ecosystem |
| `representative_repo_count` | descriptor | Number of mapped repositories |
| `month_index` | time | Sequential month counter |
| `post_chatgpt` | timing | Monthly post indicator beginning in 2022-12 |
| `so_dependence_pre` | treatment intensity | Pre-period Stack Overflow dependence score |
| `treatment_intensity` | treatment intensity | `post_chatgpt × so_dependence_pre` |
| `active_repos_observed` | descriptor | Number of active repositories observed that month |
| `stackoverflow_questions_month` | input proxy | Monthly Stack Overflow question count |
| `issues_opened` | primary outcome | Number of GitHub issues opened in the month |
| `median_close_days` | primary outcome | Median days to close for issues closed in the month |
| `avg_first_response_hours` | secondary outcome | Average hours to first maintainer response |
| `backlog_open_end_month` | primary outcome | Open-issue backlog at month end |
| `is_synthetic` | provenance | Equals 1 for the demonstration panel in this repo |

## File-level Step 2 outputs in this repository
The reproducible Step 2 handoff currently writes:
- `outputs/step2_synthetic_panel.csv`
- `outputs/step2_variable_dictionary.csv`
- `outputs/step2_manifest.json`
- `outputs/step2_validation_report.json`

These are created by:
- `scripts/build_step2_synthetic_panel.py`
- `scripts/validate_step2_outputs.py`

## Reproduction commands
From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-step2.txt
python scripts/build_step2_synthetic_panel.py
python scripts/validate_step2_outputs.py
```

## Quality checks locked in Step 2
The validation script checks that:
1. the panel matches the expected schema;
2. the variable dictionary covers every panel variable;
3. the synthetic demonstration panel is balanced by ecosystem and month;
4. missing values are absent;
5. nonnegative fields remain nonnegative; and
6. all rows are correctly marked as synthetic.

## What Step 2 does not do
This repository does **not** yet claim:
- a causal estimate;
- evidence of substitution magnitude;
- a welfare interpretation for maintainers; or
- any descriptive trend from real public data.

Those tasks belong to later steps after the public-source extraction path is fully implemented and reviewed.
