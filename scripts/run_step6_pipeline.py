from __future__ import annotations

from build_step2_synthetic_panel import main as build_step2
from build_step3_analysis import main as build_step3
from build_step4_econometrics import main as build_step4
from build_step5_robustness import main as build_step5
from build_step6_final_model import main as build_step6
from validate_step2_outputs import main as validate_step2
from validate_step3_outputs import main as validate_step3
from validate_step4_outputs import main as validate_step4
from validate_step5_outputs import main as validate_step5
from validate_step6_outputs import main as validate_step6


if __name__ == "__main__":
    build_step2()
    validate_step2()
    build_step3()
    validate_step3()
    build_step4()
    validate_step4()
    build_step5()
    validate_step5()
    build_step6()
    validate_step6()
    print("Step 6 full pipeline completed successfully.")
