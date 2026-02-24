---
name: loan-application-processing
description: >
  Processes retail banking personal loan applications end-to-end: document
  retrieval and parsing, identity verification, sanctions screening, credit
  assessment, underwriter recommendation, and applicant communication.
  STATUS: approved. AUTHORISED-AGENTS: loan-processor-agent-prod,
  loan-processor-agent-staging.
status: approved
authorised_agents:
  - loan-processor-agent-prod
  - loan-processor-agent-staging
supervisor: "Sarah Johnson <sarah.johnson@bank.example.com>"
risk: high
schema_version: "2.0"
---

# Loan Application Processing

**Supervisor:** Sarah Johnson, Head of Consumer Credit Operations
**Risk:** High | **Regulations:** FCA CONC 5.2, ICO UK GDPR Art. 22, Equality Act 2010

> For full regulatory detail see [resources/regulations.md](resources/regulations.md).
> For escalation contacts see [resources/escalation_contacts.md](resources/escalation_contacts.md).

---

## Initialisation (run before any other action)

```bash
python registry/shared/audit-logging/scripts/audit_log.py \
  --skill retail_banking/loan-application-processing \
  --session ${CLAUDE_SESSION_ID} \
  --action skill_invoked
```

---

## Approved activities

You may ONLY perform activities in this list. Before any action, validate it:

```bash
python registry/shared/validate-activity/scripts/validate_activity.py \
  --activity <activity-slug> \
  --allowlist scripts/approved_activities.json
```

If `"allowed": false` is returned, **halt immediately**. Do not perform the
activity. Log the attempt with `--outcome failure`.

| Slug | Description |
|---|---|
| `retrieve_application_documents` | Retrieve and parse proof of income, ID documents |
| `query_credit_score` | Query internal credit scoring system |
| `run_sanctions_screening` | Cross-reference applicant against sanctions databases |
| `calculate_debt_to_income` | Calculate DTI ratio from verified income figures |
| `generate_underwriter_recommendation` | Generate structured recommendation report |
| `send_applicant_communication` | Send templated emails to applicant |
| `write_audit_log_entry` | Write entry to audit trail |

---

## Workflow (execute steps in this exact order)

### Step 1 — Retrieve application documents
**Activity:** `retrieve_application_documents`

```bash
# Validate activity
python registry/shared/validate-activity/scripts/validate_activity.py \
  --activity retrieve_application_documents \
  --allowlist scripts/approved_activities.json

# Verify identity against two independent sources
python scripts/identity_verify.py \
  --applicant-id $APPLICANT_ID --name "$APPLICANT_NAME" --dob $APPLICANT_DOB
```

**If exit code 2 (FAILED) — identity-verification-failure (vetoed), halt immediately:**
```bash
python registry/shared/checkpoint-gate/scripts/checkpoint_gate.py \
  --skill retail_banking/loan-application-processing \
  --session ${CLAUDE_SESSION_ID} \
  --control-point identity-verification-failure \
  --classification vetoed \
  --contact underwriting-team@bank.example.com \
  --detail "Identity verification failed for applicant $APPLICANT_ID"
# Exit code 2 — halt all processing now.
```

**On success (exit code 0) — identity-verified (auto, agent proceeds):**
```bash
python registry/shared/checkpoint-gate/scripts/checkpoint_gate.py \
  --skill retail_banking/loan-application-processing \
  --session ${CLAUDE_SESSION_ID} \
  --control-point identity-verified \
  --classification auto

python registry/shared/audit-logging/scripts/audit_log.py \
  --skill retail_banking/loan-application-processing \
  --session ${CLAUDE_SESSION_ID} \
  --action retrieve_application_documents \
  --detail "Documents retrieved and identity verified for applicant $APPLICANT_ID"
```

### Step 2 — Sanctions screening
**Activity:** `run_sanctions_screening`
**MUST run before any credit check.**

```bash
python registry/shared/validate-activity/scripts/validate_activity.py \
  --activity run_sanctions_screening \
  --allowlist scripts/approved_activities.json

python scripts/sanctions_check.py \
  --applicant-id $APPLICANT_ID --name "$APPLICANT_NAME" --dob $APPLICANT_DOB
```

**If exit code 2 (MATCH) — sanctions-match (vetoed), halt immediately:**
```bash
python registry/shared/checkpoint-gate/scripts/checkpoint_gate.py \
  --skill retail_banking/loan-application-processing \
  --session ${CLAUDE_SESSION_ID} \
  --control-point sanctions-match \
  --classification vetoed \
  --contact financial-crime-team@bank.example.com \
  --detail "Sanctions MATCH returned for applicant $APPLICANT_ID"
# Exit code 2 — halt all processing now.
```

```bash
python registry/shared/audit-logging/scripts/audit_log.py \
  --skill retail_banking/loan-application-processing \
  --session ${CLAUDE_SESSION_ID} \
  --action run_sanctions_screening \
  --detail "Sanctions screening complete: NO_MATCH for applicant $APPLICANT_ID"
```

### Step 3 — Credit score query
**Activity:** `query_credit_score`

```bash
python registry/shared/validate-activity/scripts/validate_activity.py \
  --activity query_credit_score --allowlist scripts/approved_activities.json

# If data source flags protected characteristics → vetoed, halt immediately:
python registry/shared/checkpoint-gate/scripts/checkpoint_gate.py \
  --skill retail_banking/loan-application-processing \
  --session ${CLAUDE_SESSION_ID} \
  --control-point protected-characteristic-detected \
  --classification vetoed \
  --contact ethics-and-compliance@bank.example.com

python registry/shared/audit-logging/scripts/audit_log.py \
  --skill retail_banking/loan-application-processing \
  --session ${CLAUDE_SESSION_ID} \
  --action query_credit_score
```

### Step 4 — Calculate debt-to-income ratio
**Activity:** `calculate_debt_to_income`

```bash
python registry/shared/validate-activity/scripts/validate_activity.py \
  --activity calculate_debt_to_income --allowlist scripts/approved_activities.json

python registry/shared/audit-logging/scripts/audit_log.py \
  --skill retail_banking/loan-application-processing \
  --session ${CLAUDE_SESSION_ID} \
  --action calculate_debt_to_income
```

### Step 5 — Send progress notification to applicant
**Activity:** `send_applicant_communication`

```bash
python registry/shared/validate-activity/scripts/validate_activity.py \
  --activity send_applicant_communication --allowlist scripts/approved_activities.json

python registry/shared/audit-logging/scripts/audit_log.py \
  --skill retail_banking/loan-application-processing \
  --session ${CLAUDE_SESSION_ID} \
  --action send_applicant_communication --detail "Progress notification sent"
```

### Step 6 — Generate underwriter recommendation
**Activity:** `generate_underwriter_recommendation`

```bash
python registry/shared/validate-activity/scripts/validate_activity.py \
  --activity generate_underwriter_recommendation --allowlist scripts/approved_activities.json
```

After generating the report, invoke the creditworthiness review checkpoint.
**The agent must halt here and await human underwriter clearance:**

```bash
python registry/shared/checkpoint-gate/scripts/checkpoint_gate.py \
  --skill retail_banking/loan-application-processing \
  --session ${CLAUDE_SESSION_ID} \
  --control-point creditworthiness-assessment-review \
  --classification needs_approval \
  --reviewer "Qualified underwriter (minimum Grade 3 accreditation)" \
  --sla-hours 24
# PENDING — halt here. Do not proceed until clearance is received.

python registry/shared/audit-logging/scripts/audit_log.py \
  --skill retail_banking/loan-application-processing \
  --session ${CLAUDE_SESSION_ID} \
  --action generate_underwriter_recommendation \
  --detail "Recommendation report generated and submitted for underwriter review"
```

### Step 7 — Communicate lending decision (post-clearance only)
**Activity:** `send_applicant_communication`
**Only execute after underwriter clearance has been received for step 6.**

```bash
python registry/shared/checkpoint-gate/scripts/checkpoint_gate.py \
  --skill retail_banking/loan-application-processing \
  --session ${CLAUDE_SESSION_ID} \
  --control-point decision-communication \
  --classification notify \
  --reviewer "Underwriter (approved the decision)"

python registry/shared/audit-logging/scripts/audit_log.py \
  --skill retail_banking/loan-application-processing \
  --session ${CLAUDE_SESSION_ID} \
  --action send_applicant_communication \
  --detail "Lending decision communicated to applicant"
```

---

## What you must never do

- Issue a lending decision to the applicant without underwriter approval
- Bypass or override a `MATCH` result from sanctions screening
- Access applicant data beyond what is required for this application
- Use demographic characteristics (age, ethnicity, religion, gender, disability) in scoring
- Share application data with third parties not in the data processing agreement
- Retain applicant personal data beyond the 7-year regulatory retention period

---

## Condition-triggered control points

These apply when specific conditions arise during processing. Invoke the
checkpoint gate with the appropriate `--control-point` ID before proceeding.

| Condition | Control point | Classification | Reviewer | SLA |
|---|---|---|---|---|
| Credit score 580–640 | `borderline-credit-score` | `review` | Senior underwriter (Grade 5+) | 48h |
| Loan amount > £50,000 | `high-value-application` | `needs_approval` | Underwriter + Head of Consumer Credit | 48h |
| 2+ fraud indicator flags | `suspected-fraud-indicators` | `needs_approval` | Financial Crime Investigation Team | 4h |

```bash
# Example: borderline credit score
python registry/shared/checkpoint-gate/scripts/checkpoint_gate.py \
  --skill retail_banking/loan-application-processing \
  --session ${CLAUDE_SESSION_ID} \
  --control-point borderline-credit-score \
  --classification review \
  --reviewer "Senior underwriter (Grade 5+)" \
  --sla-hours 48
```
