from __future__ import annotations

from build_step2_synthetic_panel import main as build_step2
from build_step3_analysis import main as build_step3
from validate_step2_outputs import main as validate_step2
from validate_step3_outputs import main as validate_step3


if __name__ == "__main__":
    build_step2()
    validate_step2()
    build_step3()
    validate_step3()
    print("Step 3 pipeline completed successfully.")
