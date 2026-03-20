from __future__ import annotations

from build_step6_final_model import main as build_step6
from validate_step6_outputs import main as validate_step6


if __name__ == "__main__":
    build_step6()
    validate_step6()
    print("Step 6 finalized model and robustness outputs refreshed successfully.")
