#!/usr/bin/env python3
"""Confidence score gate for sanctions/PEP alert review.

Checks whether the agent's recommendation confidence meets the minimum threshold.
If confidence is below threshold, triggers the confidence-below-threshold veto.

Exit codes:
  0 — confidence meets threshold, proceed
  2 — confidence below threshold, halt_and_escalate
"""
from __future__ import annotations

import argparse
import json
import sys

MINIMUM_CONFIDENCE = 0.70


def main() -> None:
    parser = argparse.ArgumentParser(description="Check recommendation confidence score")
    parser.add_argument("--score", type=float, required=True, help="Confidence score (0.0–1.0)")
    parser.add_argument(
        "--threshold",
        type=float,
        default=MINIMUM_CONFIDENCE,
        help=f"Minimum acceptable confidence (default: {MINIMUM_CONFIDENCE})",
    )
    args = parser.parse_args()

    result = {
        "score": args.score,
        "threshold": args.threshold,
        "passed": args.score >= args.threshold,
    }
    print(json.dumps(result))

    if result["passed"]:
        sys.exit(0)
    else:
        sys.exit(2)


if __name__ == "__main__":
    main()
