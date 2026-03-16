from __future__ import annotations

from build_step4_econometrics import main as build_step4
from validate_step4_outputs import main as validate_step4


if __name__ == "__main__":
    build_step4()
    validate_step4()
    print("Step 4 econometric outputs refreshed successfully.")
