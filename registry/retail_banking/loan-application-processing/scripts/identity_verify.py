#!/usr/bin/env python3
"""Identity verification stub for loan application processing.

In production this calls the bank's identity verification service (e.g. Experian,
Onfido) to confirm the applicant's identity against two independent sources.

Exit codes:
  0 — VERIFIED (both sources confirmed)
  1 — PARTIAL (only one source confirmed — halt and notify)
  2 — FAILED (no sources confirmed — hard veto)
"""
from __future__ import annotations

import argparse
import json
import sys


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify applicant identity")
    parser.add_argument("--applicant-id", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--dob", required=True)
    parser.add_argument("--sources", type=int, default=2, help="Required number of sources")
    args = parser.parse_args()

    # -----------------------------------------------------------------
    # TODO: replace with real identity verification API calls.
    # The stub always returns VERIFIED for demonstration purposes.
    # -----------------------------------------------------------------
    result = {
        "applicant_id": args.applicant_id,
        "status": "VERIFIED",
        "sources_confirmed": 2,
        "sources_required": args.sources,
        "note": "Stub implementation — replace with live API call in production",
    }

    status = result["status"]
    print(json.dumps(result))

    if status == "VERIFIED":
        sys.exit(0)
    elif status == "PARTIAL":
        sys.exit(1)
    else:  # FAILED
        sys.exit(2)


if __name__ == "__main__":
    main()
