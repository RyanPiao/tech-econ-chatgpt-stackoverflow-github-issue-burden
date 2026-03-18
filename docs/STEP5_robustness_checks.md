# Step 5 Robustness Checks

## Purpose
Step 5 stress-tests the Step 4 baseline by checking whether inference is sensitive to covariance assumptions, outcome transformations, randomization inference, dynamic treatment timing, and subgroup composition.

## Inputs
- `outputs/step4_model_panel.csv`
- `outputs/step4_twfe_models.csv`

## Produced artifacts
- `outputs/step5_sensitivity_checks.csv`
- `outputs/step5_dynamic_analysis.csv`
- `outputs/step5_heterogeneity_analysis.csv`
- `outputs/step5_key_metrics.json`
- `outputs/step5_manifest.json`
- `outputs/step5_validation_report.json`
- `docs/STEP5_robustness_checks.md`

## Sensitivity checks
For `issues_opened`, the treatment-intensity coefficient remains positive under all tested covariance choices:

- Baseline entity-clustered FE: 5.9985 (p=0.0001)
- Two-way clustered FE (ecosystem + month): 5.9985 (p=0.0003)
- Robust (White-style) FE covariance: 5.9985 (p=0.0000)
- Weighted FE (active repositories): 5.8170 (p=0.0001)

Transformation checks for `issues_opened` are directionally consistent:

- Winsorized (p01/p99): 5.9470 (p=0.0005)
- log(1+y): 0.0247 (p=0.4328)

Randomization inference (300 exposure permutations) yields an empirical p-value of 0.0033 for `issues_opened`.

For `avg_first_response_hours`, the baseline effect remains positive and precise: 2.5500 (p=0.0000).

## Dynamic checks (event-study interactions)
Event-study models are estimated for all baseline outcomes with an omitted month of k = -1 and an event window from k = -12 to k = +18.

For `issues_opened`:
- Joint pretrend p-value (k <= -2): 1.0000
- Mean pre-period coefficient: -5.9937
- Mean post-period coefficient: 4.1305
- Cumulative post coefficient, k=0..12: 91.4623

For `avg_first_response_hours`:
- Joint pretrend p-value (k <= -2): 1.0000
- Cumulative post coefficient, k=0..12: 27.6434

## Heterogeneity checks
Heterogeneity is tested across three pre-period ecosystem partitions:
1. active repository scale,
2. backlog per active repository,
3. issue burden index.

For `issues_opened` in split-sample FE models by pre-period active repository scale:
- Low-scale ecosystems: 7.1286
- High-scale ecosystems: 4.2050
- High-minus-low gap: -2.9236

In the interaction model for pre-period backlog per repository, the interaction term is -0.4379 (p=0.4547), which points to a slightly smaller high-backlog effect but with weak statistical precision.

## Interpretation boundary
All estimates remain synthetic and are used for pipeline validation, model stress-testing, and reproducibility checks. They should not be interpreted as empirical claims about real ecosystems.

## Reproduction
From the repository root:

```bash
python3 -m venv .venv-step5
source .venv-step5/bin/activate
pip install -r requirements-step5.txt
python scripts/run_step5_robustness.py
```
