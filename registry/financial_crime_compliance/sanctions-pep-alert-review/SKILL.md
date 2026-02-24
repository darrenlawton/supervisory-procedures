---
name: sanctions-pep-alert-review
description: "AI-assisted first-pass review of sanctions screening and Politically Exposed Person (PEP) alerts generated during customer onboarding and ongoing monitoring. The agent works through the compliance team's standard operating procedure checklist, presents a structured recommendation (Accept / Decline / Partial Match), and hands off to a human compliance officer for final disposition. The agent does not make binding decisions — it prepares the evidence package and proposes a recommendation under the four-eyes principle. Use when Sanctions and PEP Alert Review is needed for financial crime compliance operations. Risk: critical. Authorised agents: sanctions-review-agent-prod, sanctions-review-agent-staging."
---

# Sanctions and PEP Alert Review

> **Governed Skill** — Supervisor: Head of Financial Crime Compliance (Head of Financial Crime Compliance)
> Risk: **critical** | Version: 2.0.0 | Regulations: BSA/AML — Bank Secrecy Act / Anti-Money Laundering | OFAC — US Office of Foreign Assets Control sanctions regulations | HM Treasury — UK Consolidated Sanctions List | EU Consolidated Sanctions List | FinCEN — Joint Statement on Innovative Efforts to Combat Money Laundering (2018) | Fed/OCC SR 11-7 — Model Risk Management framework | ECOA — Equal Credit Opportunity Act (fairness in decisioning) | FATF Recommendations — Politically Exposed Persons

*All steps, controls, and restrictions below are defined by your supervisor. Follow this procedure exactly.*

---
## Initialisation

Before any other action, record that this skill has been invoked:

```bash
python registry/shared/audit-logging/scripts/audit_log.py \
  --skill financial_crime_compliance/sanctions-pep-alert-review \
  --session ${CLAUDE_SESSION_ID} \
  --action skill_invoked
```

---
## Approved Activities

You may **only** perform activities listed below. Validate each step before executing:

```bash
python registry/shared/validate-activity/scripts/validate_activity.py \
  --skill registry/financial_crime_compliance/sanctions-pep-alert-review/skill.yml \
  --step <step-id>
```

If `"allowed": false` — halt immediately and log the attempt.

| Step ID | Activity |
|---------|----------|
| `query-sanctions-lists` | Query the OFAC Specially Designated Nationals list and HM Treasury/EU consolidated sanctions lists for name matches |
| `query-pep-database` | Query the PEP (Politically Exposed Person) database for name matches |
| `query-adverse-media` | Query adverse media sources for references to the customer's name |
| `match-attributes` | Match the customer's name, address, and date of birth as provided at onboarding against the name and attributes on each hit |
| `translate-names` | Translate customer names and document fields from non-Latin scripts or foreign languages to English for comparison |
| `check-age` | Check that the customer's age is consistent with the platform's Terms of Use requirements |
| `match-location` | Match the customer's state, city, and address fields against the location attributes of each sanctions or PEP hit |
| `osint-traversal` | Perform OSINT link traversal to corroborate or refute a hit (e.g. verify that a sanctions entry refers to a deceased individual) |
| `corroborate-evidence` | Corroborate hits with supplementary evidence including adverse media articles, LinkedIn profiles, or government publications |
| `classify-hits` | Classify each hit as: confirmed match, partial match (yellow flag), or false positive |
| `generate-evidence-package` | Generate a structured evidence package summarising the data sources consulted, the reasoning followed, and the recommended disposition |
| `present-recommendation` | Present the recommendation (Accept / Decline / Partial Match) to the human compliance officer for final approval |
| `log-audit` | Log all data accesses, sources queried, reasoning steps, and recommended actions to the immutable audit trail |

---
## What You Must Never Do

- Issue a final onboarding decision (approve or decline) without human compliance officer review and approval
- Clear a hit where the customer's name is an exact match on the OFAC SDN list or HM Treasury Consolidated List without human escalation
- Omit any checklist step from the SOP before issuing a recommendation
- Access or process customer personal data beyond what is required to review the current alert
- Share customer data or alert details with any third party not listed in the institution's data processing agreement
- Use nationality, ethnicity, religion, or other protected characteristics as a basis for flagging or clearing a hit
- Suppress, edit, or omit any step from the audit log
- Retain customer personal data beyond the regulatory retention period applicable to the jurisdiction

---
## Vetoed Conditions — Halt Immediately

If any of these conditions arise, invoke the checkpoint immediately and halt. No human override is possible.

### exact-sanctions-list-match — Exact Sanctions List Match

The customer's full name and at least one additional identifier match an entry on a major sanctions list with high confidence, and link traversal has not produced evidence sufficient to refute the match. Processing must halt immediately and be escalated to the Financial Crime team.

**Trigger:** Customer name and at least one additional identifier (date of birth, nationality, or address) match an OFAC SDN, HM Treasury, or EU Consolidated Sanctions List entry with confidence >= 0.90, exact or alias name match, and the match has not been refuted by evidence.
**Condition hint:** `sanctions_hit.confidence >= 0.90 AND (sanctions_hit.name_match == "exact" OR sanctions_hit.alias_match == "exact") AND sanctions_hit.refuted_by_evidence == false`

```bash
python registry/shared/checkpoint-gate/scripts/checkpoint_gate.py \
  --skill financial_crime_compliance/sanctions-pep-alert-review \
  --session ${CLAUDE_SESSION_ID} \
  --control-point exact-sanctions-list-match \
  --classification vetoed \
  --contact financial-crime-team@bank.example.com
# Exit code 2 — halt all processing immediately.
```

### confidence-below-threshold — Recommendation Confidence Below Threshold

The agent's overall confidence in its recommendation falls below the minimum acceptable threshold, indicating insufficient evidence to classify the alert as either a clear false positive or a confirmed match. Processing must halt and be escalated to the Financial Crime team.

**Trigger:** Agent's overall recommendation confidence score falls below the minimum acceptable threshold, indicating insufficient evidence to classify the alert.
**Condition hint:** `recommendation_confidence_score < 0.70`

```bash
python registry/shared/checkpoint-gate/scripts/checkpoint_gate.py \
  --skill financial_crime_compliance/sanctions-pep-alert-review \
  --session ${CLAUDE_SESSION_ID} \
  --control-point confidence-below-threshold \
  --classification vetoed \
  --contact financial-crime-team@bank.example.com
# Exit code 2 — halt all processing immediately.
```

### active-criminal-investigation-found — Active Criminal Investigation Detected

Adverse media or open-source evidence indicates that the customer is the subject of an active law enforcement investigation, criminal prosecution, or regulatory enforcement action. Processing must halt immediately.

**Trigger:** Adverse media or open-source results indicate an active law enforcement investigation, criminal prosecution, or regulatory enforcement action involving the customer.
**Condition hint:** `adverse_media_results.active_investigation == true OR adverse_media_results.criminal_prosecution == true`

```bash
python registry/shared/checkpoint-gate/scripts/checkpoint_gate.py \
  --skill financial_crime_compliance/sanctions-pep-alert-review \
  --session ${CLAUDE_SESSION_ID} \
  --control-point active-criminal-investigation-found \
  --classification vetoed \
  --contact financial-crime-team@bank.example.com
# Exit code 2 — halt all processing immediately.
```

### conflicting-evidence-on-high-risk-hit — Unresolvable Conflicting Evidence on High-Risk Hit

Multiple evidence sources return conflicting conclusions on a high-risk sanctions or PEP hit, and the conflict cannot be resolved by further link traversal within the agent's permitted data sources. Processing must halt.

**Trigger:** A high-risk hit has conflicting evidence across sources (e.g. one source indicates deceased, another indicates active) and link traversal has been exhausted without resolving the conflict.
**Condition hint:** `hit.risk_level == "high" AND evidence_sources.conflict_detected == true AND link_traversal_exhausted == true`

```bash
python registry/shared/checkpoint-gate/scripts/checkpoint_gate.py \
  --skill financial_crime_compliance/sanctions-pep-alert-review \
  --session ${CLAUDE_SESSION_ID} \
  --control-point conflicting-evidence-on-high-risk-hit \
  --classification vetoed \
  --contact financial-crime-team@bank.example.com
# Exit code 2 — halt all processing immediately.
```

### data-source-unavailable — Mandatory Data Source Unavailable

One or more mandatory data sources (OFAC, HM Treasury, PEP database) are unavailable or return an error, preventing the agent from completing the required SOP checklist steps. Processing must halt until data sources are restored.

**Trigger:** One or more mandatory data sources (OFAC SDN list, HM Treasury Consolidated List, or PEP database) are unavailable or returning errors.
**Condition hint:** `mandatory_data_sources.any_unavailable == true`

```bash
python registry/shared/checkpoint-gate/scripts/checkpoint_gate.py \
  --skill financial_crime_compliance/sanctions-pep-alert-review \
  --session ${CLAUDE_SESSION_ID} \
  --control-point data-source-unavailable \
  --classification vetoed \
  --contact financial-crime-team@bank.example.com
# Exit code 2 — halt all processing immediately.
```

---
## Oversight Checkpoints

These checkpoints are invoked at specific workflow steps (see Workflow section).

### evidence-package-review — Evidence Package Review

Classification: **review** | Reviewer: Qualified compliance officer (BSA/AML certified) | SLA: 1h

Before issuing a recommendation, the agent presents its complete evidence package to the human compliance officer — including all data sources queried, name and attribute match results, OSINT findings, confidence score, and the proposed disposition. The officer reviews and validates the package.

```bash
python registry/shared/checkpoint-gate/scripts/checkpoint_gate.py \
  --skill financial_crime_compliance/sanctions-pep-alert-review \
  --session ${CLAUDE_SESSION_ID} \
  --control-point evidence-package-review \
  --classification review \
  --reviewer "Qualified compliance officer (BSA/AML certified)" \
  --sla-hours 1
# PENDING — halt here and await reviewer clearance before continuing.
```

### final-disposition-approval — Final Disposition Approval

Classification: **needs_approval** | Reviewer: Qualified compliance officer (BSA/AML certified) | SLA: 1h

The human compliance officer makes the binding Accept, Decline, or Partial Match disposition. The agent's recommendation is advisory only. The officer's decision is recorded in the audit trail with their identity, timestamp, and any override rationale.

```bash
python registry/shared/checkpoint-gate/scripts/checkpoint_gate.py \
  --skill financial_crime_compliance/sanctions-pep-alert-review \
  --session ${CLAUDE_SESSION_ID} \
  --control-point final-disposition-approval \
  --classification needs_approval \
  --reviewer "Qualified compliance officer (BSA/AML certified)" \
  --sla-hours 1
# PENDING — halt here and await explicit approval before continuing.
```

---
## Condition-Triggered Controls

These activate when their trigger condition is met during any workflow step.

### partial-match-senior-review — Partial Match — Senior Compliance Review

Classification: **needs_approval** | Reviewer: Senior compliance officer (BSA/AML, Grade 5+) | SLA: 4h

**Trigger:** The agent classifies the alert as a Partial Match (yellow flag) — sufficient evidence to neither confirm nor clear the hit with high confidence.

Partial match cases require review by a senior compliance officer. The agent provides a summary of the conflicting evidence and recommends the most conservative available action pending human judgment.

```bash
python registry/shared/checkpoint-gate/scripts/checkpoint_gate.py \
  --skill financial_crime_compliance/sanctions-pep-alert-review \
  --session ${CLAUDE_SESSION_ID} \
  --control-point partial-match-senior-review \
  --classification needs_approval \
  --reviewer "Senior compliance officer (BSA/AML, Grade 5+)" \
  --sla-hours 4
# PENDING — halt here and await explicit approval before continuing.
```

### model-accuracy-deviation — Model Accuracy Deviation Alert

Classification: **notify** | Reviewer: AI Operations Team and Model Risk Committee

**Trigger:** The agent's rolling precision or recall metrics deviate beyond the acceptable threshold from the baseline established during backtesting and shadow-mode operation.

When performance degrades beyond acceptable bounds, the AI operations team is notified to investigate model drift and initiate retraining if required. Alert processing continues under enhanced human review until the deviation is resolved.

```bash
python registry/shared/checkpoint-gate/scripts/checkpoint_gate.py \
  --skill financial_crime_compliance/sanctions-pep-alert-review \
  --session ${CLAUDE_SESSION_ID} \
  --control-point model-accuracy-deviation \
  --classification notify \
  --reviewer "AI Operations Team and Model Risk Committee"
# NOTIFY — human is informed; agent may continue.
```

### novel-typology-detected — Novel Threat Typology Detected

Classification: **notify** | Reviewer: Financial Crime Intelligence Team and AI Operations Team | SLA: 24h

**Trigger:** A human compliance officer overrides the agent's recommendation and notes that the case represents a new or emerging threat pattern not covered by the current SOP or agent training data.

Novel typologies are escalated to the Financial Crime Intelligence team to assess whether the SOP and agent training data require updating. The override and rationale are logged and fed into the next evaluation cycle.

```bash
python registry/shared/checkpoint-gate/scripts/checkpoint_gate.py \
  --skill financial_crime_compliance/sanctions-pep-alert-review \
  --session ${CLAUDE_SESSION_ID} \
  --control-point novel-typology-detected \
  --classification notify \
  --reviewer "Financial Crime Intelligence Team and AI Operations Team" \
  --sla-hours 24
# NOTIFY — human is informed; agent may continue.
```

---
## Workflow

Execute steps in this exact order. Do not skip, reorder, or add steps.

### Step 1 — query-sanctions-lists

**Activity:** Query the OFAC Specially Designated Nationals list and HM Treasury/EU consolidated sanctions lists for name matches

```bash
python registry/shared/validate-activity/scripts/validate_activity.py \
  --skill registry/financial_crime_compliance/sanctions-pep-alert-review/skill.yml \
  --step query-sanctions-lists

python registry/shared/audit-logging/scripts/audit_log.py \
  --skill financial_crime_compliance/sanctions-pep-alert-review \
  --session ${CLAUDE_SESSION_ID} \
  --action query-sanctions-lists
```

### Step 2 — query-pep-database

**Activity:** Query the PEP (Politically Exposed Person) database for name matches

```bash
python registry/shared/validate-activity/scripts/validate_activity.py \
  --skill registry/financial_crime_compliance/sanctions-pep-alert-review/skill.yml \
  --step query-pep-database

python registry/shared/audit-logging/scripts/audit_log.py \
  --skill financial_crime_compliance/sanctions-pep-alert-review \
  --session ${CLAUDE_SESSION_ID} \
  --action query-pep-database
```

### Step 3 — query-adverse-media

**Activity:** Query adverse media sources for references to the customer's name

```bash
python registry/shared/validate-activity/scripts/validate_activity.py \
  --skill registry/financial_crime_compliance/sanctions-pep-alert-review/skill.yml \
  --step query-adverse-media

python registry/shared/audit-logging/scripts/audit_log.py \
  --skill financial_crime_compliance/sanctions-pep-alert-review \
  --session ${CLAUDE_SESSION_ID} \
  --action query-adverse-media
```

### Step 4 — translate-names

**Activity:** Translate customer names and document fields from non-Latin scripts or foreign languages to English for comparison

```bash
python registry/shared/validate-activity/scripts/validate_activity.py \
  --skill registry/financial_crime_compliance/sanctions-pep-alert-review/skill.yml \
  --step translate-names

python registry/shared/audit-logging/scripts/audit_log.py \
  --skill financial_crime_compliance/sanctions-pep-alert-review \
  --session ${CLAUDE_SESSION_ID} \
  --action translate-names
```

### Step 5 — check-age

**Activity:** Check that the customer's age is consistent with the platform's Terms of Use requirements

```bash
python registry/shared/validate-activity/scripts/validate_activity.py \
  --skill registry/financial_crime_compliance/sanctions-pep-alert-review/skill.yml \
  --step check-age

python registry/shared/audit-logging/scripts/audit_log.py \
  --skill financial_crime_compliance/sanctions-pep-alert-review \
  --session ${CLAUDE_SESSION_ID} \
  --action check-age
```

### Step 6 — match-attributes

**Activity:** Match the customer's name, address, and date of birth as provided at onboarding against the name and attributes on each hit

```bash
python registry/shared/validate-activity/scripts/validate_activity.py \
  --skill registry/financial_crime_compliance/sanctions-pep-alert-review/skill.yml \
  --step match-attributes

python registry/shared/audit-logging/scripts/audit_log.py \
  --skill financial_crime_compliance/sanctions-pep-alert-review \
  --session ${CLAUDE_SESSION_ID} \
  --action match-attributes
```

### Step 7 — match-location

**Activity:** Match the customer's state, city, and address fields against the location attributes of each sanctions or PEP hit

```bash
python registry/shared/validate-activity/scripts/validate_activity.py \
  --skill registry/financial_crime_compliance/sanctions-pep-alert-review/skill.yml \
  --step match-location

python registry/shared/audit-logging/scripts/audit_log.py \
  --skill financial_crime_compliance/sanctions-pep-alert-review \
  --session ${CLAUDE_SESSION_ID} \
  --action match-location
```

### Step 8 — osint-traversal

**Activity:** Perform OSINT link traversal to corroborate or refute a hit (e.g. verify that a sanctions entry refers to a deceased individual)

```bash
python registry/shared/validate-activity/scripts/validate_activity.py \
  --skill registry/financial_crime_compliance/sanctions-pep-alert-review/skill.yml \
  --step osint-traversal

python registry/shared/audit-logging/scripts/audit_log.py \
  --skill financial_crime_compliance/sanctions-pep-alert-review \
  --session ${CLAUDE_SESSION_ID} \
  --action osint-traversal
```

### Step 9 — corroborate-evidence

**Activity:** Corroborate hits with supplementary evidence including adverse media articles, LinkedIn profiles, or government publications

```bash
python registry/shared/validate-activity/scripts/validate_activity.py \
  --skill registry/financial_crime_compliance/sanctions-pep-alert-review/skill.yml \
  --step corroborate-evidence

python registry/shared/audit-logging/scripts/audit_log.py \
  --skill financial_crime_compliance/sanctions-pep-alert-review \
  --session ${CLAUDE_SESSION_ID} \
  --action corroborate-evidence
```

### Step 10 — classify-hits

**Activity:** Classify each hit as: confirmed match, partial match (yellow flag), or false positive

```bash
python registry/shared/validate-activity/scripts/validate_activity.py \
  --skill registry/financial_crime_compliance/sanctions-pep-alert-review/skill.yml \
  --step classify-hits

python registry/shared/audit-logging/scripts/audit_log.py \
  --skill financial_crime_compliance/sanctions-pep-alert-review \
  --session ${CLAUDE_SESSION_ID} \
  --action classify-hits
```

### Step 11 — generate-evidence-package

**Activity:** Generate a structured evidence package summarising the data sources consulted, the reasoning followed, and the recommended disposition

```bash
python registry/shared/validate-activity/scripts/validate_activity.py \
  --skill registry/financial_crime_compliance/sanctions-pep-alert-review/skill.yml \
  --step generate-evidence-package

python registry/shared/audit-logging/scripts/audit_log.py \
  --skill financial_crime_compliance/sanctions-pep-alert-review \
  --session ${CLAUDE_SESSION_ID} \
  --action generate-evidence-package
```

Control point **evidence-package-review** (halt and await review):

```bash
python registry/shared/checkpoint-gate/scripts/checkpoint_gate.py \
  --skill financial_crime_compliance/sanctions-pep-alert-review \
  --session ${CLAUDE_SESSION_ID} \
  --control-point evidence-package-review \
  --classification review \
  --reviewer "Qualified compliance officer (BSA/AML certified)" \
  --sla-hours 1
# PENDING — halt here and await reviewer clearance before continuing.
```

### Step 12 — present-recommendation

**Activity:** Present the recommendation (Accept / Decline / Partial Match) to the human compliance officer for final approval

```bash
python registry/shared/validate-activity/scripts/validate_activity.py \
  --skill registry/financial_crime_compliance/sanctions-pep-alert-review/skill.yml \
  --step present-recommendation

python registry/shared/audit-logging/scripts/audit_log.py \
  --skill financial_crime_compliance/sanctions-pep-alert-review \
  --session ${CLAUDE_SESSION_ID} \
  --action present-recommendation
```

Control point **final-disposition-approval** (halt and await approval):

```bash
python registry/shared/checkpoint-gate/scripts/checkpoint_gate.py \
  --skill financial_crime_compliance/sanctions-pep-alert-review \
  --session ${CLAUDE_SESSION_ID} \
  --control-point final-disposition-approval \
  --classification needs_approval \
  --reviewer "Qualified compliance officer (BSA/AML certified)" \
  --sla-hours 1
# PENDING — halt here and await explicit approval before continuing.
```

### Step 13 — log-audit

**Activity:** Log all data accesses, sources queried, reasoning steps, and recommended actions to the immutable audit trail

```bash
python registry/shared/validate-activity/scripts/validate_activity.py \
  --skill registry/financial_crime_compliance/sanctions-pep-alert-review/skill.yml \
  --step log-audit

python registry/shared/audit-logging/scripts/audit_log.py \
  --skill financial_crime_compliance/sanctions-pep-alert-review \
  --session ${CLAUDE_SESSION_ID} \
  --action log-audit
```
