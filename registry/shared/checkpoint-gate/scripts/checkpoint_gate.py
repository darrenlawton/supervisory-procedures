#!/usr/bin/env python3
"""Control point enforcer for supervisory skill workflows (schema v2.0).

Maps to the unified control_points classification model:

  auto          — agent proceeds without human involvement; logs and exits 0.
  notify        — human is informed but not blocked; logs, prints NOTIFIED, exits 0.
  review        — human actively reviews before agent continues; logs, prints PENDING, exits 0.
  needs_approval — explicit human sign-off required; logs, prints PENDING, exits 0.
  vetoed        — agent halts unconditionally; logs, prints VETOED, exits 2.

Exit codes:
  0 — proceed (auto / notify / review / needs_approval written to log)
  2 — halt immediately (vetoed)
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

CLASSIFICATIONS = ("auto", "notify", "review", "needs_approval", "vetoed")


def main() -> None:
    parser = argparse.ArgumentParser(description="Enforce a supervisory control point")
    parser.add_argument("--skill", required=True, help="Skill ID")
    parser.add_argument("--session", required=True, help="Session ID for correlation")
    parser.add_argument("--control-point", required=True, help="Control point ID from skill definition")
    parser.add_argument(
        "--classification",
        required=True,
        choices=CLASSIFICATIONS,
        help="Classification from the control_points definition",
    )
    parser.add_argument("--reviewer", default="", help="who_reviews value (for notify/review/needs_approval)")
    parser.add_argument("--contact", default="", help="escalation_contact (for vetoed)")
    parser.add_argument("--sla-hours", type=int, default=None)
    parser.add_argument("--detail", default="")
    parser.add_argument("--log-file", default="control_points.jsonl")
    args = parser.parse_args()

    if args.classification == "vetoed" and not args.contact:
        print("ERROR: --contact is required for vetoed classification", file=sys.stderr)
        sys.exit(1)

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "skill": args.skill,
        "session": args.session,
        "control_point": args.control_point,
        "classification": args.classification,
        "reviewer": args.reviewer,
        "contact": args.contact,
        "sla_hours": args.sla_hours,
        "detail": args.detail,
        "status": args.classification,
    }

    log_path = Path(args.log_file)
    try:
        with log_path.open("a") as f:
            f.write(json.dumps(record) + "\n")
    except OSError as exc:
        print(f"ERROR: could not write control point log: {exc}", file=sys.stderr)
        sys.exit(1)

    cp = args.control_point

    if args.classification == "auto":
        print(f"PASSED: {cp} (auto — no human action required)")
        sys.exit(0)

    if args.classification == "notify":
        print(f"NOTIFIED: {cp} → {args.reviewer}")
        sys.exit(0)

    if args.classification == "review":
        sla = f", SLA: {args.sla_hours}h" if args.sla_hours else ""
        print(f"PENDING: {cp} — review required by {args.reviewer}{sla}")
        sys.exit(0)

    if args.classification == "needs_approval":
        sla = f", SLA: {args.sla_hours}h" if args.sla_hours else ""
        print(f"PENDING: {cp} — approval required from {args.reviewer}{sla}")
        sys.exit(0)

    # vetoed
    print(f"VETOED: {cp} — halt immediately → escalate to {args.contact}")
    sys.exit(2)


if __name__ == "__main__":
    main()
