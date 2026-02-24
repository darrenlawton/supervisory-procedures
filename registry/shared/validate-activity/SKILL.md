---
name: validate-activity
description: >
  Validates that a proposed agent action is within the approved_activities
  allowlist for the current skill. Use before performing any activity to
  enforce the scope boundary. Reads the allowlist from a JSON file supplied
  by the calling skill, so each skill maintains its own list.
user-invocable: false
---

# Validate Activity

Shared enforcement script for supervisory skill scope boundaries. Call this
before every agent action to verify it falls within the approved_activities
allowlist. If the script exits non-zero, do not proceed with the activity.

## Usage

```bash
python registry/shared/validate-activity/scripts/validate_activity.py \
  --activity <activity-slug> \
  --allowlist <path-to-allowlist.json>
```

Exit 0 = permitted; exit 1 = not permitted.

## Output

```json
{"allowed": true, "activity": "run_sanctions_screening"}
```
or
```json
{"allowed": false, "activity": "send_external_email", "reason": "'send_external_email' is not in the approved_activities allowlist"}
```

## Example

```bash
python registry/shared/validate-activity/scripts/validate_activity.py \
  --activity run_sanctions_screening \
  --allowlist scripts/approved_activities.json
# {"allowed": true, "activity": "run_sanctions_screening"}
```

If the result contains `"allowed": false`, halt immediately. Do not perform
the activity. Log the attempt via the audit-logging skill.
