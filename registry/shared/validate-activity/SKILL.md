---
name: validate-activity
description: >
  Validates that a workflow step is within the approved scope for the current
  skill. Use before performing any step to enforce the scope boundary. Reads
  the workflow definition from the skill's skill.yml file.
user-invocable: false
---

# Validate Activity

Shared enforcement script for supervisory skill scope boundaries. Call this
before every workflow step to verify it is a valid step in the skill's workflow.
If the script exits non-zero, do not proceed.

## Usage

```bash
python registry/shared/validate-activity/scripts/validate_activity.py \
  --skill <path-to-skill.yml> \
  --step <step-id>
```

Exit 0 = permitted; exit 1 = not permitted.

## Output

```json
{"allowed": true, "step": "sanctions-screening"}
```
or
```json
{"allowed": false, "step": "send-external-email", "reason": "'send-external-email' is not a valid workflow step in this skill"}
```

## Example

```bash
python registry/shared/validate-activity/scripts/validate_activity.py \
  --skill registry/retail_banking/loan-application-processing/skill.yml \
  --step sanctions-screening
# {"allowed": true, "step": "sanctions-screening"}
```

If the result contains `"allowed": false`, halt immediately. Do not perform
the step. Log the attempt via the audit-logging skill.
