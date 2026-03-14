# Step 3 Exploratory Analysis

## Purpose
Step 3 moves the project from schema validation into first-pass empirical exploration using the synthetic ecosystem-month panel defined in Step 2. The goal here is not to claim final causal results, but to check whether the panel behaves in a way that is consistent with the proposed identification strategy and whether a fixed-effects specification can recover interpretable directional patterns.

## Data used
This step uses the synthetic panel in `outputs/step2_synthetic_panel.csv`, covering 8 technology ecosystems observed monthly from 2021-01 through 2024-12.

The panel remains synthetic on purpose. That keeps the workflow honest: readers can inspect the design logic, variable construction, and model code without mistaking the current outputs for real-world evidence.

## What was produced
Step 3 adds four exploratory artifacts:

- `outputs/step3_ecosystem_summary.csv`
- `outputs/step3_prepost_summary.csv`
- `outputs/step3_twfe_preview.csv`
- `outputs/step3_key_metrics.json`

It also adds the reproducible runner:

- `scripts/run_step3_eda.py`

## Descriptive patterns
Using the median split of pre-period Stack Overflow dependence:

- High-dependence ecosystems show a larger post-period increase in issues opened (`+11.272`) than low-dependence ecosystems (`+10.011`).
- High-dependence ecosystems also show a somewhat larger increase in month-end issue backlog (`+15.353`) than low-dependence ecosystems (`+14.524`).
- Median issue close duration rises more in the high-dependence group (`+1.054` days) than in the low-dependence group (`+0.808` days).

These differences are modest, but they move in the hypothesized direction: ecosystems that relied more heavily on Stack Overflow before the ChatGPT shock experience somewhat greater pressure on GitHub issue management afterward.

## Fixed-effects preview
A first-pass two-way fixed-effects preview estimates:

`outcome ~ treatment_intensity + ecosystem fixed effects + month fixed effects`

where `treatment_intensity = post_chatgpt × so_dependence_pre`.

Preview coefficients:

- `issues_opened`: `5.1086` (HC1 s.e. `1.7899`, p=`0.004316`)
- `median_close_days`: `0.5402` (HC1 s.e. `0.3120`, p=`0.083373`)
- `avg_first_response_hours`: `2.4262` (HC1 s.e. `0.4503`, p `< 0.001`)
- `backlog_open_end_month`: `2.3938` (HC1 s.e. `3.4354`, p=`0.485921`)

## Interpretation boundary
The preview suggests that, in the synthetic panel, greater pre-period Stack Overflow dependence is associated with larger post-ChatGPT increases in issue inflow and first-response delay. The backlog result is weaker at this stage, which is useful information: it suggests the eventual real-data exercise should distinguish between immediate flow pressure and slower-moving stock accumulation.

This is still exploratory work. The specification does not yet include the robustness, heterogeneity, or alternative functional-form checks that belong in later steps.

## Risks carried forward to Step 4
1. The synthetic panel may make treatment-response patterns cleaner than real data will be.
2. Backlog dynamics appear noisier than issue inflow and response-time measures, so that outcome may require alternative scaling or lag structure.
3. The next step should formalize the baseline econometric specification and document the remaining assumptions more explicitly.

## Reproduction
From the repository root:

```bash
python3 -m venv .venv-step3
source .venv-step3/bin/activate
pip install -r requirements-step3.txt
python scripts/run_step3_eda.py
```
