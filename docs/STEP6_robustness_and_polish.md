# Step 6 Robustness and Polish

## QA changelog (what was run)
- Re-estimated the Step 4 treatment-intensity model with **ecosystem-specific linear trends** to finalize the baseline specification for Step 6.
- Refit all core outcomes under the finalized specification and exported one consolidated model table.
- Ran targeted alternative-explanation checks for the main finding (`issues_opened`):
  1. active-repo weighting,
  2. lagged outcome control,
  3. Stack Overflow activity controls,
  4. symmetric ±12 month window,
  5. 6-month lead placebo,
  6. intensive-margin ratio outcome.
- Ran a shifted intervention cutoff sweep (five candidate cutoff months) to test whether the effect is concentrated around the intended intervention timing.

## Finalized model decision
Finalized Step 6 model: **TWFE with standardized controls + ecosystem-specific linear trends**, ecosystem-clustered SE.

For `issues_opened`:
- Step 4 reference coefficient: 5.9985 (p=0.0001)
- Step 6 finalized coefficient: 10.8180 (p=0.0000)
- Standardized finalized effect: 1.279 SD

For `avg_first_response_hours` under the finalized model:
- Coefficient: 3.8092 (p=0.0000)

## Alternative-explanation robustness summary (main finding: `issues_opened`)
- Lagged-outcome control: 9.7179 (p=0.0000)
- Symmetric ±12 month window: 7.2464 (p=0.0030)
- SO-activity controls: 12.1226 (p=0.1442)
- 6-month lead placebo term: -1.0172 (p=0.3777)
- Intensive-margin (`issues_per_active_repo`) outcome: 0.0566 (p=0.0041)

Interpretation for QA: most checks preserve a positive treatment-intensity direction, while adding direct SO-activity controls attenuates precision, consistent with potential channel overlap/mediation rather than a pure contradiction.

## Cutoff sweep diagnostic
Shifted-cutoff estimates (trend-adjusted model) are reported in `outputs/step6_cutoff_sweep.csv`.

- Coefficient at intended cutoff (2022-12-01): 10.8180 (rank=1 among tested cutoffs)
- Highest coefficient among tested cutoffs: 2022-12-01 with 10.8180

## Produced artifacts
- `outputs/step6_finalized_model_results.csv`
- `outputs/step6_alternative_explanations.csv`
- `outputs/step6_cutoff_sweep.csv`
- `outputs/step6_key_metrics.json`
- `outputs/step6_manifest.json`
- `outputs/step6_validation_report.json`
- `docs/STEP6_robustness_and_polish.md`

## Interpretation boundary
All results remain synthetic and are intended for pipeline QA, specification stress-testing, and reproducibility checks. They are not empirical claims from live public-source data.

## Reproduction
From the repository root:

```bash
python3 -m venv .venv-step6
source .venv-step6/bin/activate
pip install -r requirements-step6.txt
python scripts/run_step6_finalize.py
```
