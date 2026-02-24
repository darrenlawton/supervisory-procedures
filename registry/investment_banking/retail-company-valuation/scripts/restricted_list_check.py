#!/usr/bin/env python3
"""Restricted and watch list check stub for IB retail company valuation.

In production this calls the firm's Conflicts Office API to verify that
the target company is not on the active M&A deal list, restricted list,
or watch list.

Exit codes:
  0 — NO_MATCH (safe to proceed; Compliance clearance still required)
  1 — WATCH_LIST (soft flag — refer to Compliance before proceeding)
  2 — RESTRICTED (hard veto — target-on-restricted-list control point)
"""
from __future__ import annotations

import argparse
import json
import sys


def main() -> None:
    parser = argparse.ArgumentParser(description="Check target against restricted/watch lists")
    parser.add_argument("--company-id", required=True, help="Target company identifier")
    parser.add_argument("--company-name", required=True, help="Target company name")
    args = parser.parse_args()

    # -----------------------------------------------------------------
    # TODO: replace with real Conflicts Office API call.
    # The stub always returns NO_MATCH for demonstration purposes.
    # -----------------------------------------------------------------
    result = {
        "company_id": args.company_id,
        "company_name": args.company_name,
        "status": "NO_MATCH",
        "lists_checked": ["RESTRICTED_LIST", "WATCH_LIST", "ACTIVE_MAA_DEAL_LIST"],
        "note": "Stub implementation — replace with live Conflicts Office API call in production",
    }

    status = result["status"]
    print(json.dumps(result))

    if status == "NO_MATCH":
        sys.exit(0)
    elif status == "WATCH_LIST":
        sys.exit(1)
    else:  # RESTRICTED
        sys.exit(2)


if __name__ == "__main__":
    main()
