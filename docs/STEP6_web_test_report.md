# Step 6 Web Test Report

## Scope
Full end-to-end reproducibility QA for Step 6 main finding and robustness checks, including Step 6 output validation and Step 6 manifest integrity checks.

## Execution environment
- Repository: `/Users/openclaw/.openclaw/workspace/projects/tech-econ-chatgpt-stackoverflow-github-issue-burden`
- Run timestamp (local): `2026-03-20 08:05:44 EDT`
- Python environment used: existing repo `.venv` (as requested)
- Python version: `3.14.3`

## Commands run
```bash
cd /Users/openclaw/.openclaw/workspace/projects/tech-econ-chatgpt-stackoverflow-github-issue-burden

# Use existing .venv and install Step 6 requirements
.venv/bin/python -V
.venv/bin/python -m pip install -r requirements-step6.txt

# Run full Step 6 pipeline (build + validations through Step 6)
.venv/bin/python scripts/run_step6_pipeline.py

# Re-run Step 6 validator explicitly
.venv/bin/python scripts/validate_step6_outputs.py

# Additional Step 6 QA checks for manifest integrity
.venv/bin/python - <<'PY'
import json
from pathlib import Path
import pandas as pd
root=Path('.')
manifest=json.loads((root/'outputs/step6_manifest.json').read_text())
missing=[]
size0=[]
for rel in manifest.get('outputs',[]):
    p=root/rel
    if not p.exists():
        missing.append(rel)
    elif p.stat().st_size==0:
        size0.append(rel)
panel=pd.read_csv(root/'outputs/step4_model_panel.csv')
print('missing_outputs', missing)
print('zero_byte_outputs', size0)
print('manifest_n_rows', manifest.get('n_rows'), 'actual', len(panel))
print('manifest_n_ecosystems', manifest.get('n_ecosystems'), 'actual', panel['ecosystem'].nunique())
print('manifest_sample_start', manifest.get('sample_start'), 'actual', str(pd.to_datetime(panel['month']).min().date()))
print('manifest_sample_end', manifest.get('sample_end'), 'actual', str(pd.to_datetime(panel['month']).max().date()))
PY
```

## Command outcomes
- `pip install -r requirements-step6.txt`: **PASS** (`Requirement already satisfied` for all required packages)
- `scripts/run_step6_pipeline.py`: **PASS** (completed successfully; Step 6 outputs written)
- `scripts/validate_step6_outputs.py`: **PASS** (exit code 0)
- `outputs/step6_validation_report.json`: **PASS**
  - `status: "ok"`
  - `errors: []`
  - `warnings: []`

## Step 6 main finding reproducibility
From `outputs/step6_finalized_model_results.csv` for `issues_opened`:
- Step 6 baseline reference (`baseline_step4_reference`):
  - `coef_treatment_intensity = 5.998492`
  - `p_value = 1.328893e-04`
- Step 6 finalized trend-adjusted model (`finalized_trend_adjusted`):
  - `coef_treatment_intensity = 10.818042`
  - `p_value = 2.010836e-12`

Result: **PASS** — Step 6 finalized model reproduces a positive and highly significant treatment-intensity estimate for the main outcome.

## Step 6 robustness checks reproducibility
From `outputs/step6_alternative_explanations.csv`:
- Treatment-intensity robustness checks are direction-consistent (positive) across all treatment-targeted checks.
- Placebo lead check:
  - `check_id = anticipation_lead6_placebo`
  - `target_parameter = lead6_treatment_intensity_step6`
  - `coef = -1.017187`, `p_value = 3.776985e-01` (not significant)

From `outputs/step6_cutoff_sweep.csv`:
- Tested cutoff months present: `2022-06-01`, `2022-09-01`, `2022-12-01`, `2023-03-01`, `2023-06-01`
- True cutoff flag appears exactly once at `2022-12-01`
- True cutoff coefficient: `10.818042` (rank `1` among tested cutoffs)

Result: **PASS** — Step 6 robustness artifacts and diagnostics reproduced with expected structure and values.

## Step 6 manifest integrity
From `outputs/step6_manifest.json` and filesystem checks:
- All manifest-listed Step 6 outputs exist: **PASS**
- No zero-byte files among manifest-listed outputs: **PASS**
- Manifest metadata matches panel source (`outputs/step4_model_panel.csv`): **PASS**
  - `n_rows: 384` matches actual `384`
  - `n_ecosystems: 8` matches actual `8`
  - `sample_start: 2021-01-01` matches actual
  - `sample_end: 2024-12-01` matches actual

## QA verdict
# ✅ PASS
Step 6 end-to-end reproducibility test passed, including main finding reproducibility, robustness check reproducibility, Step 6 validator status, and manifest integrity.
