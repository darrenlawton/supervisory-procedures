---
name: checkpoint-gate
description: >
  Enforces supervisory control points in skill workflows (schema v2.0).
  Accepts a --classification argument matching the control_points classification:
  auto, notify, review, needs_approval, or vetoed. Writes a record to the control
  point log and signals the agent whether to proceed or halt.
user-invocable: false
---

# Checkpoint Gate

Shared enforcement script for supervisory control points. Insert at every point
in the workflow where a control point is referenced. The `--classification`
argument must match the `classification` field in the skill's `control_points`
definition.

## Usage

```bash
python registry/shared/checkpoint-gate/scripts/checkpoint_gate.py \
  --skill <skill-id> \
  --session ${CLAUDE_SESSION_ID} \
  --control-point <control-point-id> \
  --classification <auto|notify|review|needs_approval|vetoed> \
  [--reviewer "<who_reviews>"] \
  [--contact <escalation_contact>] \
  [--sla-hours <n>] \
  [--detail "<context>"]
```

## Classification behaviour

| Classification | Agent behaviour | Exit code |
|---|---|---|
| `auto` | Proceeds immediately | 0 |
| `notify` | Logs notification, proceeds | 0 |
| `review` | Halts, awaits reviewer sign-off | 0 |
| `needs_approval` | Halts, awaits explicit approval | 0 |
| `vetoed` | Halts unconditionally — no override possible | 2 |

Exit code 2 means **halt immediately and do not continue under any circumstances**.

## Required arguments by classification

- `vetoed`: `--contact` is required (escalation_contact from skill definition)
- `notify`, `review`, `needs_approval`: `--reviewer` is expected (who_reviews from skill definition)
- `auto`: no additional arguments needed

## Examples

**auto** (identity verified, agent proceeds):
```bash
python registry/shared/checkpoint-gate/scripts/checkpoint_gate.py \
  --skill retail_banking/loan-application-processing \
  --session ${CLAUDE_SESSION_ID} \
  --control-point identity-verified \
  --classification auto
# PASSED: identity-verified (auto — no human action required)
```

**needs_approval** (underwriter sign-off required):
```bash
python registry/shared/checkpoint-gate/scripts/checkpoint_gate.py \
  --skill retail_banking/loan-application-processing \
  --session ${CLAUDE_SESSION_ID} \
  --control-point creditworthiness-assessment-review \
  --classification needs_approval \
  --reviewer "Qualified underwriter (minimum Grade 3 accreditation)" \
  --sla-hours 24
# PENDING: creditworthiness-assessment-review — approval required from ... (SLA: 24h)
# Agent halts here and awaits clearance.
```

**vetoed** (sanctions match — halt unconditionally):
```bash
python registry/shared/checkpoint-gate/scripts/checkpoint_gate.py \
  --skill retail_banking/loan-application-processing \
  --session ${CLAUDE_SESSION_ID} \
  --control-point sanctions-match \
  --classification vetoed \
  --contact financial-crime-team@bank.example.com \
  --detail "Exact OFAC match: John Smith DOB 1970-01-01"
# VETOED: sanctions-match — halt immediately → escalate to financial-crime-team@...
# Exit code 2. Agent must halt. No human can override a vetoed control point.
```
