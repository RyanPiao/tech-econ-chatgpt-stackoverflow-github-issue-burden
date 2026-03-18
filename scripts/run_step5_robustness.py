from __future__ import annotations

from build_step5_robustness import main as build_step5
from validate_step5_outputs import main as validate_step5


if __name__ == "__main__":
    build_step5()
    validate_step5()
    print("Step 5 robustness outputs refreshed successfully.")
