---
name: sanctions-pep-alert-review
description: >
  First-pass review of sanctions screening and Politically Exposed Person (PEP)
  alerts. Queries OFAC, HM Treasury, EU lists, and adverse media; classifies hits
  as confirmed match, partial match, or false positive; generates an evidence
  package; presents recommendation (Accept / Decline / Partial Match) to a human
  compliance officer for final disposition. Four-eyes principle — agent is advisory
  only. STATUS: approved. AUTHORISED-AGENTS: sanctions-review-agent-prod,
  sanctions-review-agent-staging.
status: approved
authorised_agents:
  - sanctions-review-agent-prod
  - sanctions-review-agent-staging
supervisor: "Head of Financial Crime Compliance <financial-crime-compliance@bank.example.com>"
risk: critical
schema_version: "2.0"
---

# Sanctions and PEP Alert Review

**Supervisor:** Head of Financial Crime Compliance
**Risk:** Critical | **Regulations:** BSA/AML, OFAC, HM Treasury, EU Consolidated Lists, FATF

> This is an advisory skill. The agent prepares evidence and proposes a recommendation.
> **All final decisions are made by a human compliance officer.**

---

## Initialisation

```bash
python registry/shared/audit-logging/scripts/audit_log.py \
  --skill financial_crime_compliance/sanctions-pep-alert-review \
  --session ${CLAUDE_SESSION_ID} \
  --action skill_invoked
```

---

## Approved activities

Validate every action before performing it:

```bash
python registry/shared/validate-activity/scripts/validate_activity.py \
  --activity <slug> \
  --allowlist scripts/approved_activities.json
```

| Slug | Description |
|---|---|
| `query_sanctions_lists` | Query OFAC SDN, HM Treasury, EU Consolidated Lists |
| `query_pep_database` | Query PEP database |
| `query_adverse_media` | Query adverse media sources |
| `translate_names` | Translate non-Latin / foreign-language names |
| `check_customer_age` | Verify age against Terms of Use |
| `match_name_and_attributes` | Match name, DOB, address against hit attributes |
| `match_location` | Match state/city/address against hit location |
| `osint_traversal` | OSINT link traversal to corroborate or refute |
| `corroborate_evidence` | Corroborate via adverse media, LinkedIn, gov publications |
| `classify_hits` | Classify as confirmed / partial / false positive |
| `generate_evidence_package` | Generate structured evidence package |
| `present_recommendation` | Present recommendation to compliance officer |
| `write_audit_log_entry` | Write to immutable audit trail |

---

## Workflow

### Step 1 — Query sanctions lists
```bash
python registry/shared/validate-activity/scripts/validate_activity.py \
  --activity query_sanctions_lists --allowlist scripts/approved_activities.json

# If data source unavailable → vetoed, halt immediately:
python registry/shared/checkpoint-gate/scripts/checkpoint_gate.py \
  --skill financial_crime_compliance/sanctions-pep-alert-review \
  --session ${CLAUDE_SESSION_ID} \
  --control-point data-source-unavailable \
  --classification vetoed \
  --contact financial-crime-team@bank.example.com

python registry/shared/audit-logging/scripts/audit_log.py \
  --skill financial_crime_compliance/sanctions-pep-alert-review \
  --session ${CLAUDE_SESSION_ID} --action query_sanctions_lists
```

### Step 2 — Query PEP database
```bash
python registry/shared/validate-activity/scripts/validate_activity.py \
  --activity query_pep_database --allowlist scripts/approved_activities.json

python registry/shared/audit-logging/scripts/audit_log.py \
  --skill financial_crime_compliance/sanctions-pep-alert-review \
  --session ${CLAUDE_SESSION_ID} --action query_pep_database
```

### Step 3 — Query adverse media
```bash
python registry/shared/validate-activity/scripts/validate_activity.py \
  --activity query_adverse_media --allowlist scripts/approved_activities.json

# If active criminal investigation detected → vetoed, halt immediately:
python registry/shared/checkpoint-gate/scripts/checkpoint_gate.py \
  --skill financial_crime_compliance/sanctions-pep-alert-review \
  --session ${CLAUDE_SESSION_ID} \
  --control-point active-criminal-investigation-found \
  --classification vetoed \
  --contact financial-crime-team@bank.example.com

python registry/shared/audit-logging/scripts/audit_log.py \
  --skill financial_crime_compliance/sanctions-pep-alert-review \
  --session ${CLAUDE_SESSION_ID} --action query_adverse_media
```

### Steps 4–9 — Translation, matching, OSINT, corroboration
Validate and audit-log each activity slug. For `osint_traversal`, if conflicting
evidence on a high-risk hit is unresolvable:

```bash
python registry/shared/checkpoint-gate/scripts/checkpoint_gate.py \
  --skill financial_crime_compliance/sanctions-pep-alert-review \
  --session ${CLAUDE_SESSION_ID} \
  --control-point conflicting-evidence-on-high-risk-hit \
  --classification vetoed \
  --contact financial-crime-team@bank.example.com
```

### Step 10 — Classify hits
```bash
python registry/shared/validate-activity/scripts/validate_activity.py \
  --activity classify_hits --allowlist scripts/approved_activities.json

# If exact sanctions list match (confidence >= 0.90) → vetoed, halt immediately:
python registry/shared/checkpoint-gate/scripts/checkpoint_gate.py \
  --skill financial_crime_compliance/sanctions-pep-alert-review \
  --session ${CLAUDE_SESSION_ID} \
  --control-point exact-sanctions-list-match \
  --classification vetoed \
  --contact financial-crime-team@bank.example.com \
  --detail "Exact match: $CUSTOMER_NAME on OFAC/HM Treasury list"

python registry/shared/audit-logging/scripts/audit_log.py \
  --skill financial_crime_compliance/sanctions-pep-alert-review \
  --session ${CLAUDE_SESSION_ID} --action classify_hits
```

### Step 11 — Generate evidence package + checkpoint
```bash
python registry/shared/validate-activity/scripts/validate_activity.py \
  --activity generate_evidence_package --allowlist scripts/approved_activities.json

# Check confidence before generating package:
python scripts/confidence_check.py --score $CONFIDENCE_SCORE
# Exit 2 → confidence-below-threshold (vetoed), halt immediately:
python registry/shared/checkpoint-gate/scripts/checkpoint_gate.py \
  --skill financial_crime_compliance/sanctions-pep-alert-review \
  --session ${CLAUDE_SESSION_ID} \
  --control-point confidence-below-threshold \
  --classification vetoed \
  --contact financial-crime-team@bank.example.com \
  --detail "Confidence score $CONFIDENCE_SCORE below threshold 0.70"

# Evidence package review checkpoint — agent halts:
python registry/shared/checkpoint-gate/scripts/checkpoint_gate.py \
  --skill financial_crime_compliance/sanctions-pep-alert-review \
  --session ${CLAUDE_SESSION_ID} \
  --control-point evidence-package-review \
  --classification review \
  --reviewer "Qualified compliance officer (BSA/AML certified)" \
  --sla-hours 1
# PENDING — halt here.

python registry/shared/audit-logging/scripts/audit_log.py \
  --skill financial_crime_compliance/sanctions-pep-alert-review \
  --session ${CLAUDE_SESSION_ID} --action generate_evidence_package
```

### Step 12 — Present recommendation (post-clearance only)
```bash
python registry/shared/checkpoint-gate/scripts/checkpoint_gate.py \
  --skill financial_crime_compliance/sanctions-pep-alert-review \
  --session ${CLAUDE_SESSION_ID} \
  --control-point final-disposition-approval \
  --classification needs_approval \
  --reviewer "Qualified compliance officer (BSA/AML certified)" \
  --sla-hours 1
# PENDING — compliance officer makes the binding decision.

python registry/shared/audit-logging/scripts/audit_log.py \
  --skill financial_crime_compliance/sanctions-pep-alert-review \
  --session ${CLAUDE_SESSION_ID} --action present_recommendation
```

---

## What you must never do

- Issue a final onboarding decision without compliance officer approval
- Clear an exact OFAC SDN / HM Treasury match without human escalation
- Omit any checklist step from the SOP
- Use nationality, ethnicity, religion, or protected characteristics in hit assessment
- Suppress, edit, or omit any step from the audit log
