---
name: audit-logging
description: >
  Writes timestamped, immutable audit log entries for any supervisory skill.
  Use when an agent needs to record a data access, decision step, or workflow
  event to the persistent audit trail. Provides append-only logging with
  session correlation and JSON-structured output.
user-invocable: false
---

# Audit Logging

Shared enforcement script for supervisory skill audit trails. Call this at every
data access, decision point, and workflow transition.

## Usage

```bash
python registry/shared/audit-logging/scripts/audit_log.py \
  --skill <skill-id> \
  --session ${CLAUDE_SESSION_ID} \
  --action <action-slug> \
  [--detail "<free-text detail>"] \
  [--outcome success|failure|escalated]
```

The script appends one JSON line to `audit_trail.jsonl` in the current working
directory. Only the confirmation message enters the context window.

## Required arguments

- `--skill`: the skill ID (e.g. `retail_banking/loan-application-processing`)
- `--session`: session identifier for correlation across log entries
- `--action`: short slug describing the action (e.g. `sanctions_screening_complete`)

## Optional arguments

- `--detail`: human-readable description of what happened
- `--outcome`: `success`, `failure`, or `escalated` (default: `success`)
- `--log-file`: path to log file (default: `audit_trail.jsonl`)

## Output

On success the script prints `OK: logged <action>` and exits 0.
On failure it prints an error message to stderr and exits 1.

## Example

```bash
python registry/shared/audit-logging/scripts/audit_log.py \
  --skill retail_banking/loan-application-processing \
  --session ${CLAUDE_SESSION_ID} \
  --action sanctions_screening_complete \
  --detail "Applicant ID 12345: NO_MATCH returned by OFAC feed" \
  --outcome success
```
