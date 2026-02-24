---
name: loan-application-processing
description: "AI-assisted processing of personal loan applications. The agent reviews submitted documentation, runs automated eligibility checks, prepares a recommendation for the underwriter, and communicates decisions to applicants. Use when Loan Application Processing is needed for retail banking operations. Risk: high. Authorised agents: loan-processor-agent-prod, loan-processor-agent-staging."
---

# Loan Application Processing

> **Governed Skill** — Supervisor: Sarah Johnson (Head of Consumer Credit Operations)
> Risk: **high** | Version: 2.0.0 | Regulations: FCA CONC 5.2 — Creditworthiness assessment | FCA CONC 7.3 — Arrears and default | ICO UK GDPR — Automated decision-making (Article 22) | Equality Act 2010 — Protected characteristics

*All steps, controls, and restrictions below are defined by your supervisor. Follow this procedure exactly.*

---
## Initialisation

Before any other action, record that this skill has been invoked:

```bash
python registry/shared/audit-logging/scripts/audit_log.py \
  --skill retail_banking/loan-application-processing \
  --session ${CLAUDE_SESSION_ID} \
  --action skill_invoked
```

---
## Approved Activities

You may **only** perform activities listed below. Validate each step before executing:

```bash
python registry/shared/validate-activity/scripts/validate_activity.py \
  --skill registry/retail_banking/loan-application-processing/skill.yml \
  --step <step-id>
```

If `"allowed": false` — halt immediately and log the attempt.

| Step ID | Activity |
|---------|----------|
| `retrieve-documents` | Retrieve and parse submitted application documents (proof of income, ID) |
| `credit-score` | Query the internal credit scoring system for the applicant's risk score |
| `sanctions-screening` | Cross-reference applicant details against the sanctions screening database |
| `calculate-dti` | Calculate debt-to-income ratio using declared and verified income figures |
| `generate-recommendation` | Generate a structured recommendation report for the human underwriter |
| `send-progress-notification` | Send templated acknowledgement and status-update emails to the applicant |
| `log-documents-retrieved` | Log all actions and data accesses to the audit trail |

---
## What You Must Never Do

- Issue a loan offer or rejection directly to the applicant without underwriter approval
- Access or store applicant data beyond what is required for this application
- Override or bypass a sanctions screening match
- Use demographic characteristics (age, ethnicity, religion, gender, disability) as inputs to scoring
- Share application data with third parties not listed in the data processing agreement
- Retain applicant personal data beyond the 7-year regulatory retention period

---
## Vetoed Conditions — Halt Immediately

If any of these conditions arise, invoke the checkpoint immediately and halt. No human override is possible.

### sanctions-match — Sanctions List Match

A positive match was returned when the applicant's name and date of birth were checked against the HM Treasury or OFAC consolidated sanctions lists. Processing must halt immediately and be escalated to the Financial Crime team.

**Trigger:** Positive match returned from HM Treasury or OFAC sanctions screening with match_confidence >= 0.85 or exact_match == true.
**Condition hint:** `sanctions_screening_result.match_confidence >= 0.85 OR sanctions_screening_result.exact_match == true`

```bash
python registry/shared/checkpoint-gate/scripts/checkpoint_gate.py \
  --skill retail_banking/loan-application-processing \
  --session ${CLAUDE_SESSION_ID} \
  --control-point sanctions-match \
  --classification vetoed \
  --contact financial-crime-team@bank.example.com
# Exit code 2 — halt all processing immediately.
```

### identity-verification-failure — Identity Verification Failure

The agent cannot verify the applicant's identity against two independent sources after exhausting available verification methods. Processing must halt and the underwriting team must be notified.

**Trigger:** Agent has exhausted all available identity verification methods and cannot confirm the applicant's identity against two independent sources.

```bash
python registry/shared/checkpoint-gate/scripts/checkpoint_gate.py \
  --skill retail_banking/loan-application-processing \
  --session ${CLAUDE_SESSION_ID} \
  --control-point identity-verification-failure \
  --classification vetoed \
  --contact underwriting-team@bank.example.com
# Exit code 2 — halt all processing immediately.
```

### data-quality-critical — Critical Data Quality Failure

Critical data required for a compliant creditworthiness assessment is missing or cannot be retrieved (e.g. credit bureau unavailable, income documents unreadable). Processing must halt and the underwriting team must be notified.

**Trigger:** Critical required fields are missing or external services return errors that prevent a compliant assessment from being completed.
**Condition hint:** `required_fields_missing.count > 0 OR external_service_errors.critical == true`

```bash
python registry/shared/checkpoint-gate/scripts/checkpoint_gate.py \
  --skill retail_banking/loan-application-processing \
  --session ${CLAUDE_SESSION_ID} \
  --control-point data-quality-critical \
  --classification vetoed \
  --contact underwriting-team@bank.example.com
# Exit code 2 — halt all processing immediately.
```

### protected-characteristic-detected — Protected Characteristic Detected

A data source or scoring model attempts to supply a protected characteristic (age band excepted by FCA) as a model feature. Processing must halt immediately and be escalated to Ethics and Compliance.

**Trigger:** A data source or scoring model exposes a protected characteristic (e.g. ethnicity, religion, gender, disability) as a model input feature.
**Condition hint:** `feature_flags.contains_protected_characteristic == true`

```bash
python registry/shared/checkpoint-gate/scripts/checkpoint_gate.py \
  --skill retail_banking/loan-application-processing \
  --session ${CLAUDE_SESSION_ID} \
  --control-point protected-characteristic-detected \
  --classification vetoed \
  --contact ethics-and-compliance@bank.example.com
# Exit code 2 — halt all processing immediately.
```

---
## Oversight Checkpoints

These checkpoints are invoked at specific workflow steps (see Workflow section).

### creditworthiness-assessment-review — Creditworthiness Assessment Review

Classification: **needs_approval** | Reviewer: Qualified underwriter (minimum Grade 3 accreditation) | SLA: 24h

Human underwriter reviews the agent's structured recommendation report, including credit score, debt-to-income ratio, and supporting documentation, and provides explicit sign-off before any decision is communicated.

```bash
python registry/shared/checkpoint-gate/scripts/checkpoint_gate.py \
  --skill retail_banking/loan-application-processing \
  --session ${CLAUDE_SESSION_ID} \
  --control-point creditworthiness-assessment-review \
  --classification needs_approval \
  --reviewer "Qualified underwriter (minimum Grade 3 accreditation)" \
  --sla-hours 24
# PENDING — halt here and await explicit approval before continuing.
```

### decision-communication — Lending Decision Communication

Classification: **notify** | Reviewer: Underwriter (approved the decision)

After underwriter approval, notifies the applicant of the lending decision via templated email. Declined applications include a reason code so the customer can request a manual review.

```bash
python registry/shared/checkpoint-gate/scripts/checkpoint_gate.py \
  --skill retail_banking/loan-application-processing \
  --session ${CLAUDE_SESSION_ID} \
  --control-point decision-communication \
  --classification notify \
  --reviewer "Underwriter (approved the decision)"
# NOTIFY — human is informed; agent may continue.
```

---
## Condition-Triggered Controls

These activate when their trigger condition is met during any workflow step.

### high-value-application — High-Value Loan Application Review

Classification: **needs_approval** | Reviewer: Underwriter + Head of Consumer Credit | SLA: 48h

**Trigger:** Requested loan amount exceeds £50,000.

Loan applications above the high-value threshold require dual-approval: both a qualified underwriter and the Head of Consumer Credit must sign off before a decision is communicated to the applicant.

```bash
python registry/shared/checkpoint-gate/scripts/checkpoint_gate.py \
  --skill retail_banking/loan-application-processing \
  --session ${CLAUDE_SESSION_ID} \
  --control-point high-value-application \
  --classification needs_approval \
  --reviewer "Underwriter + Head of Consumer Credit" \
  --sla-hours 48
# PENDING — halt here and await explicit approval before continuing.
```

### suspected-fraud-indicators — Fraud Indicators Detected

Classification: **needs_approval** | Reviewer: Financial Crime Investigation Team | SLA: 4h

**Trigger:** Two or more fraud indicator flags are raised during document verification (e.g. inconsistent employment records, mismatched address history, altered document metadata).

Two or more fraud indicator flags have been raised during document verification. Processing halts and the application is referred to the Financial Crime team for manual investigation before any further action.

```bash
python registry/shared/checkpoint-gate/scripts/checkpoint_gate.py \
  --skill retail_banking/loan-application-processing \
  --session ${CLAUDE_SESSION_ID} \
  --control-point suspected-fraud-indicators \
  --classification needs_approval \
  --reviewer "Financial Crime Investigation Team" \
  --sla-hours 4
# PENDING — halt here and await explicit approval before continuing.
```

### borderline-credit-score — Borderline Credit Score — Senior Review

Classification: **review** | Reviewer: Senior underwriter (Grade 5+) | SLA: 48h

**Trigger:** Applicant credit score falls within the borderline band (580–640) as defined in the current underwriting policy.

Applications with borderline credit scores require review by a senior underwriter to ensure consistent application of lending policy before the recommendation is finalised.

```bash
python registry/shared/checkpoint-gate/scripts/checkpoint_gate.py \
  --skill retail_banking/loan-application-processing \
  --session ${CLAUDE_SESSION_ID} \
  --control-point borderline-credit-score \
  --classification review \
  --reviewer "Senior underwriter (Grade 5+)" \
  --sla-hours 48
# PENDING — halt here and await reviewer clearance before continuing.
```

---
## Workflow

Execute steps in this exact order. Do not skip, reorder, or add steps.

### Step 1 — retrieve-documents

**Activity:** Retrieve and parse submitted application documents (proof of income, ID)

```bash
python registry/shared/validate-activity/scripts/validate_activity.py \
  --skill registry/retail_banking/loan-application-processing/skill.yml \
  --step retrieve-documents

python registry/shared/audit-logging/scripts/audit_log.py \
  --skill retail_banking/loan-application-processing \
  --session ${CLAUDE_SESSION_ID} \
  --action retrieve-documents
```

Control point **identity-verified** (auto — agent proceeds automatically):

```bash
python registry/shared/checkpoint-gate/scripts/checkpoint_gate.py \
  --skill retail_banking/loan-application-processing \
  --session ${CLAUDE_SESSION_ID} \
  --control-point identity-verified \
  --classification auto
```

### Step 2 — log-documents-retrieved

**Activity:** Log all actions and data accesses to the audit trail

```bash
python registry/shared/validate-activity/scripts/validate_activity.py \
  --skill registry/retail_banking/loan-application-processing/skill.yml \
  --step log-documents-retrieved

python registry/shared/audit-logging/scripts/audit_log.py \
  --skill retail_banking/loan-application-processing \
  --session ${CLAUDE_SESSION_ID} \
  --action log-documents-retrieved
```

### Step 3 — sanctions-screening

**Activity:** Cross-reference applicant details against the sanctions screening database

```bash
python registry/shared/validate-activity/scripts/validate_activity.py \
  --skill registry/retail_banking/loan-application-processing/skill.yml \
  --step sanctions-screening

python registry/shared/audit-logging/scripts/audit_log.py \
  --skill retail_banking/loan-application-processing \
  --session ${CLAUDE_SESSION_ID} \
  --action sanctions-screening
```

### Step 4 — log-sanctions-complete

**Activity:** Log all actions and data accesses to the audit trail

```bash
python registry/shared/validate-activity/scripts/validate_activity.py \
  --skill registry/retail_banking/loan-application-processing/skill.yml \
  --step log-sanctions-complete

python registry/shared/audit-logging/scripts/audit_log.py \
  --skill retail_banking/loan-application-processing \
  --session ${CLAUDE_SESSION_ID} \
  --action log-sanctions-complete
```

### Step 5 — credit-score

**Activity:** Query the internal credit scoring system for the applicant's risk score

```bash
python registry/shared/validate-activity/scripts/validate_activity.py \
  --skill registry/retail_banking/loan-application-processing/skill.yml \
  --step credit-score

python registry/shared/audit-logging/scripts/audit_log.py \
  --skill retail_banking/loan-application-processing \
  --session ${CLAUDE_SESSION_ID} \
  --action credit-score
```

### Step 6 — log-credit-retrieved

**Activity:** Log all actions and data accesses to the audit trail

```bash
python registry/shared/validate-activity/scripts/validate_activity.py \
  --skill registry/retail_banking/loan-application-processing/skill.yml \
  --step log-credit-retrieved

python registry/shared/audit-logging/scripts/audit_log.py \
  --skill retail_banking/loan-application-processing \
  --session ${CLAUDE_SESSION_ID} \
  --action log-credit-retrieved
```

### Step 7 — calculate-dti

**Activity:** Calculate debt-to-income ratio using declared and verified income figures

```bash
python registry/shared/validate-activity/scripts/validate_activity.py \
  --skill registry/retail_banking/loan-application-processing/skill.yml \
  --step calculate-dti

python registry/shared/audit-logging/scripts/audit_log.py \
  --skill retail_banking/loan-application-processing \
  --session ${CLAUDE_SESSION_ID} \
  --action calculate-dti
```

### Step 8 — log-dti-calculated

**Activity:** Log all actions and data accesses to the audit trail

```bash
python registry/shared/validate-activity/scripts/validate_activity.py \
  --skill registry/retail_banking/loan-application-processing/skill.yml \
  --step log-dti-calculated

python registry/shared/audit-logging/scripts/audit_log.py \
  --skill retail_banking/loan-application-processing \
  --session ${CLAUDE_SESSION_ID} \
  --action log-dti-calculated
```

### Step 9 — send-progress-notification

**Activity:** Send templated acknowledgement and status-update emails to the applicant

```bash
python registry/shared/validate-activity/scripts/validate_activity.py \
  --skill registry/retail_banking/loan-application-processing/skill.yml \
  --step send-progress-notification

python registry/shared/audit-logging/scripts/audit_log.py \
  --skill retail_banking/loan-application-processing \
  --session ${CLAUDE_SESSION_ID} \
  --action send-progress-notification
```

### Step 10 — generate-recommendation

**Activity:** Generate a structured recommendation report for the human underwriter

```bash
python registry/shared/validate-activity/scripts/validate_activity.py \
  --skill registry/retail_banking/loan-application-processing/skill.yml \
  --step generate-recommendation

python registry/shared/audit-logging/scripts/audit_log.py \
  --skill retail_banking/loan-application-processing \
  --session ${CLAUDE_SESSION_ID} \
  --action generate-recommendation
```

Control point **creditworthiness-assessment-review** (halt and await approval):

```bash
python registry/shared/checkpoint-gate/scripts/checkpoint_gate.py \
  --skill retail_banking/loan-application-processing \
  --session ${CLAUDE_SESSION_ID} \
  --control-point creditworthiness-assessment-review \
  --classification needs_approval \
  --reviewer "Qualified underwriter (minimum Grade 3 accreditation)" \
  --sla-hours 24
# PENDING — halt here and await explicit approval before continuing.
```

### Step 11 — log-recommendation-generated

**Activity:** Log all actions and data accesses to the audit trail

```bash
python registry/shared/validate-activity/scripts/validate_activity.py \
  --skill registry/retail_banking/loan-application-processing/skill.yml \
  --step log-recommendation-generated

python registry/shared/audit-logging/scripts/audit_log.py \
  --skill retail_banking/loan-application-processing \
  --session ${CLAUDE_SESSION_ID} \
  --action log-recommendation-generated
```

### Step 12 — notify-applicant-decision

**Activity:** Send templated acknowledgement and status-update emails to the applicant

```bash
python registry/shared/validate-activity/scripts/validate_activity.py \
  --skill registry/retail_banking/loan-application-processing/skill.yml \
  --step notify-applicant-decision

python registry/shared/audit-logging/scripts/audit_log.py \
  --skill retail_banking/loan-application-processing \
  --session ${CLAUDE_SESSION_ID} \
  --action notify-applicant-decision
```

Control point **decision-communication** (notify and continue):

```bash
python registry/shared/checkpoint-gate/scripts/checkpoint_gate.py \
  --skill retail_banking/loan-application-processing \
  --session ${CLAUDE_SESSION_ID} \
  --control-point decision-communication \
  --classification notify \
  --reviewer "Underwriter (approved the decision)"
# NOTIFY — human is informed; agent may continue.
```
