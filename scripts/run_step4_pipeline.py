from __future__ import annotations

from build_step2_synthetic_panel import main as build_step2
from build_step3_analysis import main as build_step3
from build_step4_econometrics import main as build_step4
from validate_step2_outputs import main as validate_step2
from validate_step3_outputs import main as validate_step3
from validate_step4_outputs import main as validate_step4


if __name__ == "__main__":
    build_step2()
    validate_step2()
    build_step3()
    validate_step3()
    build_step4()
    validate_step4()
    print("Step 4 full pipeline completed successfully.")
