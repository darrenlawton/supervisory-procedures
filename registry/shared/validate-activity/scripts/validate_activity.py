#!/usr/bin/env python3
"""Activity allowlist enforcer for supervisory skill scope boundaries.

Reads a JSON allowlist file and checks whether the requested activity is
permitted. Prints a JSON result to stdout. Exit 0 = permitted, exit 1 = denied.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Check activity against approved allowlist")
    parser.add_argument("--activity", required=True, help="Activity slug to check")
    parser.add_argument(
        "--allowlist",
        required=True,
        help="Path to JSON file containing array of approved activity slugs",
    )
    args = parser.parse_args()

    allowlist_path = Path(args.allowlist)
    try:
        allowlist: list[str] = json.loads(allowlist_path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        print(
            json.dumps({
                "allowed": False,
                "activity": args.activity,
                "reason": f"Could not read allowlist: {exc}",
            }),
            file=sys.stderr,
        )
        sys.exit(1)

    if args.activity in allowlist:
        print(json.dumps({"allowed": True, "activity": args.activity}))
        sys.exit(0)

    print(json.dumps({
        "allowed": False,
        "activity": args.activity,
        "reason": f"'{args.activity}' is not in the approved_activities allowlist",
    }))
    sys.exit(1)


if __name__ == "__main__":
    main()
