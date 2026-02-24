#!/usr/bin/env python3
"""Append-only audit log writer for supervisory skill workflows.

Writes one JSON line per call to an audit trail file.
Only the confirmation message is printed to stdout (enters agent context).
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Write an audit log entry")
    parser.add_argument("--skill", required=True, help="Skill ID")
    parser.add_argument("--session", required=True, help="Session ID for correlation")
    parser.add_argument("--action", required=True, help="Action slug being logged")
    parser.add_argument("--detail", default="", help="Human-readable detail")
    parser.add_argument(
        "--outcome",
        choices=["success", "failure", "escalated"],
        default="success",
    )
    parser.add_argument("--log-file", default="audit_trail.jsonl", help="Log file path")
    args = parser.parse_args()

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "skill": args.skill,
        "session": args.session,
        "action": args.action,
        "detail": args.detail,
        "outcome": args.outcome,
    }

    log_path = Path(args.log_file)
    try:
        with log_path.open("a") as f:
            f.write(json.dumps(entry) + "\n")
    except OSError as exc:
        print(f"ERROR: could not write audit log to {log_path}: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"OK: logged {args.action}")


if __name__ == "__main__":
    main()
