# Step 2 — Preanalysis Lock

## Purpose
This document locks the core Step 2 analytic choices before later descriptive or econometric work begins. It is meant to reduce specification drift once real public-source extraction is ready.

## Scope
This lock applies to the project:
- **ChatGPT and the shift from Stack Overflow to GitHub issue burden**

It governs only Step 2 choices. It does not report findings.

## Locked estimand
The primary estimand is:
- the differential post-launch change in GitHub issue burden for ecosystems with higher pre-period Stack Overflow dependence relative to ecosystems with lower pre-period Stack Overflow dependence.

In plain terms:
- after ChatGPT's public launch, do ecosystems that historically relied more on Stack Overflow show a larger increase in issue-tracker burden?

## Locked unit of analysis
- **ecosystem-month**

## Locked sample window
- Monthly observations from **2021-01** through **2024-12**

If a later real-data build expands the window, the originally locked sample should still be preserved as the baseline comparison frame.

## Locked intervention timing
- ChatGPT public launch date: **2022-11-30**
- Monthly post indicator begins: **2022-12-01**

## Locked treatment construction
Primary treatment intensity:
- `so_dependence_pre`

Definition:
- a pre-period measure of ecosystem dependence on Stack Overflow, fixed using information available before the intervention.

Locked rule:
- the treatment intensity must be computed **without using post-period information**.

Implementation in the Step 2 demonstration panel:
- `so_dependence_pre` is transparently assigned synthetic intensity values to validate the pipeline.

Planned real-data implementation:
- construct a dependence score from pre-period Stack Overflow tag activity only;
- keep the score fixed through the panel;
- interact it with the post indicator to form `treatment_intensity`.

## Locked primary outcomes
The primary outcome family is GitHub issue burden.

Primary outcomes:
1. `issues_opened`
2. `median_close_days`
3. `backlog_open_end_month`

Secondary outcome:
- `avg_first_response_hours`

Interpretation rule:
- increases in these outcomes may reflect more support burden, but they may also reflect broader repository activity or product-development changes. Later interpretation must remain cautious.

## Locked inclusion criteria for ecosystems
An ecosystem is eligible if it has all of the following:
1. a clear Stack Overflow tag anchor;
2. a public GitHub repository group that can be described transparently;
3. enough recurring issue activity to support monthly aggregation; and
4. a mapping rationale that can be documented in plain language.

## Locked exclusions
The baseline build will exclude:
- private repositories;
- pull requests treated as issues;
- ecosystems without a stable public tag mapping; and
- ad hoc post hoc ecosystem additions made only after inspecting outcome patterns.

## Locked baseline specification template for later estimation
When later model work begins, the baseline empirical template is:

```text
Outcome_(e,t) = alpha_e + gamma_t + beta * (Post_t × SO_Dependence_e) + error_(e,t)
```

Where:
- `alpha_e` = ecosystem fixed effects
- `gamma_t` = month fixed effects
- `Post_t × SO_Dependence_e` = locked treatment intensity

This template is recorded now so that later steps do not redefine the core design after seeing patterns in the data.

## Locked transformations and treatment coding rules
- `post_chatgpt` is binary and turns on in 2022-12.
- `treatment_intensity = post_chatgpt × so_dependence_pre`.
- No outcome-driven recoding of `so_dependence_pre` is allowed in the baseline design.
- Alternative binning or nonlinear treatment definitions, if later used, must be labeled as robustness checks rather than replacements for the baseline design.

## Locked missing-data rule
For the future real-data build:
- do not silently interpolate missing primary outcomes;
- if a source month is unavailable, document the source gap explicitly;
- retain a missingness log rather than imputing the baseline panel.

For the current Step 2 synthetic demonstration:
- the panel is intentionally complete so that the schema and validation logic can be tested cleanly.

## Locked outlier rule
Baseline Step 2 rule:
- no winsorization or trimming is built into the baseline panel-construction script.

If later robustness checks use alternative outlier handling, they must be documented separately and must not overwrite the baseline outputs.

## Locked documentation rule
Any change to the following must be documented explicitly in a later note:
- ecosystem mapping;
- intervention timing;
- variable definitions;
- inclusion and exclusion rules; or
- outcome construction.

## What remains outside the Step 2 lock
This document does not yet settle:
- the final real-data extraction route among public-source options;
- event-study expansion choices;
- heterogeneity splits;
- robustness families; or
- interpretation of empirical findings.

Those belong to later steps once the baseline public-source extraction is in place.
