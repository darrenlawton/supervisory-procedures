#!/usr/bin/env python3
"""Sanctions screening stub for loan application processing.

In production this wraps the bank's OFAC/HM Treasury API client.
Returns a JSON result: MATCH, NO_MATCH, or INCONCLUSIVE.

Exit codes:
  0 — NO_MATCH (safe to proceed)
  1 — INCONCLUSIVE (halt and notify)
  2 — MATCH (hard veto — halt and escalate)
"""
from __future__ import annotations

import argparse
import json
import sys


def main() -> None:
    parser = argparse.ArgumentParser(description="Run sanctions screening for an applicant")
    parser.add_argument("--applicant-id", required=True, help="Applicant reference ID")
    parser.add_argument("--name", required=True, help="Applicant full name")
    parser.add_argument("--dob", required=True, help="Date of birth (YYYY-MM-DD)")
    args = parser.parse_args()

    # -----------------------------------------------------------------
    # TODO: replace with real OFAC / HM Treasury / EU list API call.
    # The stub always returns NO_MATCH for demonstration purposes.
    # -----------------------------------------------------------------
    result = {
        "applicant_id": args.applicant_id,
        "status": "NO_MATCH",
        "confidence": 0.0,
        "lists_checked": ["OFAC_SDN", "HM_TREASURY", "EU_CONSOLIDATED"],
        "note": "Stub implementation — replace with live API call in production",
    }

    status = result["status"]
    print(json.dumps(result))

    if status == "NO_MATCH":
        sys.exit(0)
    elif status == "INCONCLUSIVE":
        sys.exit(1)
    else:  # MATCH
        sys.exit(2)


if __name__ == "__main__":
    main()
