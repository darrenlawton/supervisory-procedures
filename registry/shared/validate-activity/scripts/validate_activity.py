#!/usr/bin/env python3
"""Activity scope enforcer — validates a workflow step against skill.yml.

Reads the skill.yml file and checks whether the requested step ID is a valid
workflow step. Prints a JSON result to stdout.

Exit codes:
  0 — step is permitted (found in workflow.steps)
  1 — step is not permitted or skill.yml could not be read
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate a workflow step against skill.yml")
    parser.add_argument("--skill", required=True, help="Path to the skill's skill.yml file")
    parser.add_argument("--step", required=True, help="Workflow step ID to validate")
    args = parser.parse_args()

    skill_path = Path(args.skill)
    try:
        skill = yaml.safe_load(skill_path.read_text())
    except (OSError, yaml.YAMLError) as exc:
        print(json.dumps({
            "allowed": False,
            "step": args.step,
            "reason": f"Could not read skill.yml: {exc}",
        }))
        sys.exit(1)

    valid_step_ids = {s["id"] for s in skill.get("workflow", {}).get("steps", [])}

    if args.step in valid_step_ids:
        print(json.dumps({"allowed": True, "step": args.step}))
        sys.exit(0)

    print(json.dumps({
        "allowed": False,
        "step": args.step,
        "reason": f"'{args.step}' is not a valid workflow step in this skill",
    }))
    sys.exit(1)


if __name__ == "__main__":
    main()
