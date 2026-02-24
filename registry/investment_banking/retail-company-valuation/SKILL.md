---
name: retail-company-valuation
description: "AI-assisted construction of valuation models for publicly listed and private retail sector companies. The agent assembles comparable company analysis (comps), discounted cash flow (DCF) inputs, and LBO model parameters from internal and approved external data sources. Use when Retail Company Valuation Model is needed for investment banking operations. Risk: high. Authorised agents: ib-valuation-agent-prod."
---

# Retail Company Valuation Model

> **Governed Skill** — Supervisor: Your Full Name (Head of Investment Banking Coverage — Retail)
> Risk: **high** | Version: 2.0.0 | Regulations: FCA MAR — Market Abuse Regulation (insider information controls) | FCA COBS 12.2 — Research independence requirements | MiFID II — Conflicts of interest and research objectivity

*All steps, controls, and restrictions below are defined by your supervisor. Follow this procedure exactly.*

---
## Initialisation

Before any other action, record that this skill has been invoked:

```bash
python registry/shared/audit-logging/scripts/audit_log.py \
  --skill investment_banking/retail-company-valuation \
  --session ${CLAUDE_SESSION_ID} \
  --action skill_invoked
```

---
## Approved Activities

You may **only** perform activities listed below. Validate each step before executing:

```bash
python registry/shared/validate-activity/scripts/validate_activity.py \
  --skill registry/investment_banking/retail-company-valuation/skill.yml \
  --step <step-id>
```

If `"allowed": false` — halt immediately and log the attempt.

| Step ID | Activity |
|---------|----------|
| `restricted-list-check` | Check the target company against the firm's restricted and watch lists prior to any data retrieval |
| `retrieve-public-filings` | Retrieve public financial filings (10-K, 20-F, annual reports) for target and comparable companies |
| `pull-market-data` | Pull approved market data feeds for share price, EV, and trading multiples |
| `calculate-trading-multiples` | Calculate EV/EBITDA, P/E, EV/Sales, and EV/EBIT multiples for comparable companies |
| `build-dcf-inputs` | Build DCF model inputs using normalised historical financials and published consensus forecasts |
| `construct-lbo-skeleton` | Construct LBO model skeleton with standard leverage assumptions |
| `flag-data-anomalies` | Flag data gaps or anomalies in source financials for analyst follow-up |
| `generate-valuation-report` | Generate a structured valuation summary report for senior banker review |
| `deliver-model` | Package and deliver the approved valuation model to authorised recipients |
| `log-list-check` | Log all data sources, versions, and assumptions to the audit trail |

---
## What You Must Never Do

- Use non-public (inside) information as a model input
- Publish or share the valuation with any external party without Coverage MD approval
- Override or suppress a flagged data anomaly without analyst acknowledgement
- Generate a final investment recommendation — the agent produces analysis only
- Access deal team data rooms for companies outside the approved coverage list

---
## Vetoed Conditions — Halt Immediately

If any of these conditions arise, invoke the checkpoint immediately and halt. No human override is possible.

### inside-information-detected — Inside Information Detected

An input data source is flagged as potentially containing material non-public information (MNPI) about the target company. Processing must halt immediately and be escalated to the MNPI Compliance desk.

**Trigger:** An input data source is flagged as potentially containing material non-public information (MNPI) about the target company, or originates from a deal room.
**Condition hint:** `data_source.mnpi_flag == true OR data_source.origin == "deal_room"`

```bash
python registry/shared/checkpoint-gate/scripts/checkpoint_gate.py \
  --skill investment_banking/retail-company-valuation \
  --session ${CLAUDE_SESSION_ID} \
  --control-point inside-information-detected \
  --classification vetoed \
  --contact compliance-mnpi-desk@bank.example.com
# Exit code 2 — halt all processing immediately.
```

### target-on-restricted-list — Target on Restricted or Watch List

The target company appears on the firm's restricted or watch list, indicating an active deal or conflict of interest. Processing must halt immediately and be escalated to the Conflicts Office.

**Trigger:** The target company matches an entry on the firm's restricted or watch list.
**Condition hint:** `restricted_list_check.match == true`

```bash
python registry/shared/checkpoint-gate/scripts/checkpoint_gate.py \
  --skill investment_banking/retail-company-valuation \
  --session ${CLAUDE_SESSION_ID} \
  --control-point target-on-restricted-list \
  --classification vetoed \
  --contact conflicts-office@bank.example.com
# Exit code 2 — halt all processing immediately.
```

### data-source-not-approved — Unapproved Data Source

The agent has attempted to retrieve data from a vendor or source not on the approved data vendor list. Processing must halt and the IB Data Governance team must be notified.

**Trigger:** Agent attempts to retrieve data from a vendor or source not present on the approved data vendor list.

```bash
python registry/shared/checkpoint-gate/scripts/checkpoint_gate.py \
  --skill investment_banking/retail-company-valuation \
  --session ${CLAUDE_SESSION_ID} \
  --control-point data-source-not-approved \
  --classification vetoed \
  --contact ib-data-governance@bank.example.com
# Exit code 2 — halt all processing immediately.
```

---
## Oversight Checkpoints

These checkpoints are invoked at specific workflow steps (see Workflow section).

### restricted-list-cleared — Restricted List Check Complete

Classification: **needs_approval** | Reviewer: Compliance — Conflicts Office | SLA: 2h

Compliance confirms the target company is not on the restricted or watch list before any data retrieval or modelling begins.

```bash
python registry/shared/checkpoint-gate/scripts/checkpoint_gate.py \
  --skill investment_banking/retail-company-valuation \
  --session ${CLAUDE_SESSION_ID} \
  --control-point restricted-list-cleared \
  --classification needs_approval \
  --reviewer "Compliance — Conflicts Office" \
  --sla-hours 2
# PENDING — halt here and await explicit approval before continuing.
```

### valuation-senior-review — Senior Banker Valuation Review

Classification: **needs_approval** | Reviewer: VP or MD — Investment Banking Coverage | SLA: 24h

Senior banker reviews the agent's draft valuation output, including methodology, comparable selection, and DCF assumptions, and provides explicit sign-off before any client use.

```bash
python registry/shared/checkpoint-gate/scripts/checkpoint_gate.py \
  --skill investment_banking/retail-company-valuation \
  --session ${CLAUDE_SESSION_ID} \
  --control-point valuation-senior-review \
  --classification needs_approval \
  --reviewer "VP or MD — Investment Banking Coverage" \
  --sla-hours 24
# PENDING — halt here and await explicit approval before continuing.
```

### external-sharing-approval — External Distribution Sign-off

Classification: **needs_approval** | Reviewer: Coverage Managing Director | SLA: 4h

Coverage MD explicitly approves sharing the valuation model or summary with any external party.

```bash
python registry/shared/checkpoint-gate/scripts/checkpoint_gate.py \
  --skill investment_banking/retail-company-valuation \
  --session ${CLAUDE_SESSION_ID} \
  --control-point external-sharing-approval \
  --classification needs_approval \
  --reviewer "Coverage Managing Director" \
  --sla-hours 4
# PENDING — halt here and await explicit approval before continuing.
```

---
## Condition-Triggered Controls

These activate when their trigger condition is met during any workflow step.

### private-company-target — Private Company — Enhanced Data Governance Review

Classification: **needs_approval** | Reviewer: Legal Counsel + Compliance | SLA: 48h

**Trigger:** Target company is not publicly listed.

Private company valuations rely on non-public financial data subject to NDA. Legal and compliance must confirm data usage is permissible before modelling proceeds.

```bash
python registry/shared/checkpoint-gate/scripts/checkpoint_gate.py \
  --skill investment_banking/retail-company-valuation \
  --session ${CLAUDE_SESSION_ID} \
  --control-point private-company-target \
  --classification needs_approval \
  --reviewer "Legal Counsel + Compliance" \
  --sla-hours 48
# PENDING — halt here and await explicit approval before continuing.
```

### data-anomaly-flagged — Financial Data Anomaly Review

Classification: **review** | Reviewer: Analyst or Associate — Investment Banking Coverage | SLA: 4h

**Trigger:** Agent flags a material inconsistency or anomaly in source financials (e.g. restatement, non-recurring items exceeding 10% of EBITDA).

Analyst must acknowledge and document the anomaly before the model proceeds. Agent output must note the anomaly in the final report.

```bash
python registry/shared/checkpoint-gate/scripts/checkpoint_gate.py \
  --skill investment_banking/retail-company-valuation \
  --session ${CLAUDE_SESSION_ID} \
  --control-point data-anomaly-flagged \
  --classification review \
  --reviewer "Analyst or Associate — Investment Banking Coverage" \
  --sla-hours 4
# PENDING — halt here and await reviewer clearance before continuing.
```

---
## Workflow

Execute steps in this exact order. Do not skip, reorder, or add steps.

### Step 1 — restricted-list-check

**Activity:** Check the target company against the firm's restricted and watch lists prior to any data retrieval

```bash
python registry/shared/validate-activity/scripts/validate_activity.py \
  --skill registry/investment_banking/retail-company-valuation/skill.yml \
  --step restricted-list-check

python registry/shared/audit-logging/scripts/audit_log.py \
  --skill investment_banking/retail-company-valuation \
  --session ${CLAUDE_SESSION_ID} \
  --action restricted-list-check
```

Control point **restricted-list-cleared** (halt and await approval):

```bash
python registry/shared/checkpoint-gate/scripts/checkpoint_gate.py \
  --skill investment_banking/retail-company-valuation \
  --session ${CLAUDE_SESSION_ID} \
  --control-point restricted-list-cleared \
  --classification needs_approval \
  --reviewer "Compliance — Conflicts Office" \
  --sla-hours 2
# PENDING — halt here and await explicit approval before continuing.
```

### Step 2 — log-list-check

**Activity:** Log all data sources, versions, and assumptions to the audit trail

```bash
python registry/shared/validate-activity/scripts/validate_activity.py \
  --skill registry/investment_banking/retail-company-valuation/skill.yml \
  --step log-list-check

python registry/shared/audit-logging/scripts/audit_log.py \
  --skill investment_banking/retail-company-valuation \
  --session ${CLAUDE_SESSION_ID} \
  --action log-list-check
```

### Step 3 — retrieve-public-filings

**Activity:** Retrieve public financial filings (10-K, 20-F, annual reports) for target and comparable companies

```bash
python registry/shared/validate-activity/scripts/validate_activity.py \
  --skill registry/investment_banking/retail-company-valuation/skill.yml \
  --step retrieve-public-filings

python registry/shared/audit-logging/scripts/audit_log.py \
  --skill investment_banking/retail-company-valuation \
  --session ${CLAUDE_SESSION_ID} \
  --action retrieve-public-filings
```

### Step 4 — log-filings-retrieved

**Activity:** Log all data sources, versions, and assumptions to the audit trail

```bash
python registry/shared/validate-activity/scripts/validate_activity.py \
  --skill registry/investment_banking/retail-company-valuation/skill.yml \
  --step log-filings-retrieved

python registry/shared/audit-logging/scripts/audit_log.py \
  --skill investment_banking/retail-company-valuation \
  --session ${CLAUDE_SESSION_ID} \
  --action log-filings-retrieved
```

### Step 5 — pull-market-data

**Activity:** Pull approved market data feeds for share price, EV, and trading multiples

```bash
python registry/shared/validate-activity/scripts/validate_activity.py \
  --skill registry/investment_banking/retail-company-valuation/skill.yml \
  --step pull-market-data

python registry/shared/audit-logging/scripts/audit_log.py \
  --skill investment_banking/retail-company-valuation \
  --session ${CLAUDE_SESSION_ID} \
  --action pull-market-data
```

### Step 6 — log-market-data-retrieved

**Activity:** Log all data sources, versions, and assumptions to the audit trail

```bash
python registry/shared/validate-activity/scripts/validate_activity.py \
  --skill registry/investment_banking/retail-company-valuation/skill.yml \
  --step log-market-data-retrieved

python registry/shared/audit-logging/scripts/audit_log.py \
  --skill investment_banking/retail-company-valuation \
  --session ${CLAUDE_SESSION_ID} \
  --action log-market-data-retrieved
```

### Step 7 — calculate-trading-multiples

**Activity:** Calculate EV/EBITDA, P/E, EV/Sales, and EV/EBIT multiples for comparable companies

```bash
python registry/shared/validate-activity/scripts/validate_activity.py \
  --skill registry/investment_banking/retail-company-valuation/skill.yml \
  --step calculate-trading-multiples

python registry/shared/audit-logging/scripts/audit_log.py \
  --skill investment_banking/retail-company-valuation \
  --session ${CLAUDE_SESSION_ID} \
  --action calculate-trading-multiples
```

### Step 8 — log-multiples-calculated

**Activity:** Log all data sources, versions, and assumptions to the audit trail

```bash
python registry/shared/validate-activity/scripts/validate_activity.py \
  --skill registry/investment_banking/retail-company-valuation/skill.yml \
  --step log-multiples-calculated

python registry/shared/audit-logging/scripts/audit_log.py \
  --skill investment_banking/retail-company-valuation \
  --session ${CLAUDE_SESSION_ID} \
  --action log-multiples-calculated
```

### Step 9 — build-dcf-inputs

**Activity:** Build DCF model inputs using normalised historical financials and published consensus forecasts

```bash
python registry/shared/validate-activity/scripts/validate_activity.py \
  --skill registry/investment_banking/retail-company-valuation/skill.yml \
  --step build-dcf-inputs

python registry/shared/audit-logging/scripts/audit_log.py \
  --skill investment_banking/retail-company-valuation \
  --session ${CLAUDE_SESSION_ID} \
  --action build-dcf-inputs
```

### Step 10 — log-dcf-built

**Activity:** Log all data sources, versions, and assumptions to the audit trail

```bash
python registry/shared/validate-activity/scripts/validate_activity.py \
  --skill registry/investment_banking/retail-company-valuation/skill.yml \
  --step log-dcf-built

python registry/shared/audit-logging/scripts/audit_log.py \
  --skill investment_banking/retail-company-valuation \
  --session ${CLAUDE_SESSION_ID} \
  --action log-dcf-built
```

### Step 11 — construct-lbo-skeleton

**Activity:** Construct LBO model skeleton with standard leverage assumptions

```bash
python registry/shared/validate-activity/scripts/validate_activity.py \
  --skill registry/investment_banking/retail-company-valuation/skill.yml \
  --step construct-lbo-skeleton

python registry/shared/audit-logging/scripts/audit_log.py \
  --skill investment_banking/retail-company-valuation \
  --session ${CLAUDE_SESSION_ID} \
  --action construct-lbo-skeleton
```

### Step 12 — log-lbo-constructed

**Activity:** Log all data sources, versions, and assumptions to the audit trail

```bash
python registry/shared/validate-activity/scripts/validate_activity.py \
  --skill registry/investment_banking/retail-company-valuation/skill.yml \
  --step log-lbo-constructed

python registry/shared/audit-logging/scripts/audit_log.py \
  --skill investment_banking/retail-company-valuation \
  --session ${CLAUDE_SESSION_ID} \
  --action log-lbo-constructed
```

### Step 13 — flag-data-anomalies

**Activity:** Flag data gaps or anomalies in source financials for analyst follow-up

```bash
python registry/shared/validate-activity/scripts/validate_activity.py \
  --skill registry/investment_banking/retail-company-valuation/skill.yml \
  --step flag-data-anomalies

python registry/shared/audit-logging/scripts/audit_log.py \
  --skill investment_banking/retail-company-valuation \
  --session ${CLAUDE_SESSION_ID} \
  --action flag-data-anomalies
```

### Step 14 — generate-valuation-report

**Activity:** Generate a structured valuation summary report for senior banker review

```bash
python registry/shared/validate-activity/scripts/validate_activity.py \
  --skill registry/investment_banking/retail-company-valuation/skill.yml \
  --step generate-valuation-report

python registry/shared/audit-logging/scripts/audit_log.py \
  --skill investment_banking/retail-company-valuation \
  --session ${CLAUDE_SESSION_ID} \
  --action generate-valuation-report
```

Control point **valuation-senior-review** (halt and await approval):

```bash
python registry/shared/checkpoint-gate/scripts/checkpoint_gate.py \
  --skill investment_banking/retail-company-valuation \
  --session ${CLAUDE_SESSION_ID} \
  --control-point valuation-senior-review \
  --classification needs_approval \
  --reviewer "VP or MD — Investment Banking Coverage" \
  --sla-hours 24
# PENDING — halt here and await explicit approval before continuing.
```

### Step 15 — log-report-generated

**Activity:** Log all data sources, versions, and assumptions to the audit trail

```bash
python registry/shared/validate-activity/scripts/validate_activity.py \
  --skill registry/investment_banking/retail-company-valuation/skill.yml \
  --step log-report-generated

python registry/shared/audit-logging/scripts/audit_log.py \
  --skill investment_banking/retail-company-valuation \
  --session ${CLAUDE_SESSION_ID} \
  --action log-report-generated
```

### Step 16 — deliver-model

**Activity:** Package and deliver the approved valuation model to authorised recipients

```bash
python registry/shared/validate-activity/scripts/validate_activity.py \
  --skill registry/investment_banking/retail-company-valuation/skill.yml \
  --step deliver-model

python registry/shared/audit-logging/scripts/audit_log.py \
  --skill investment_banking/retail-company-valuation \
  --session ${CLAUDE_SESSION_ID} \
  --action deliver-model
```

Control point **external-sharing-approval** (halt and await approval):

```bash
python registry/shared/checkpoint-gate/scripts/checkpoint_gate.py \
  --skill investment_banking/retail-company-valuation \
  --session ${CLAUDE_SESSION_ID} \
  --control-point external-sharing-approval \
  --classification needs_approval \
  --reviewer "Coverage Managing Director" \
  --sla-hours 4
# PENDING — halt here and await explicit approval before continuing.
```

### Step 17 — log-delivery

**Activity:** Log all data sources, versions, and assumptions to the audit trail

```bash
python registry/shared/validate-activity/scripts/validate_activity.py \
  --skill registry/investment_banking/retail-company-valuation/skill.yml \
  --step log-delivery

python registry/shared/audit-logging/scripts/audit_log.py \
  --skill investment_banking/retail-company-valuation \
  --session ${CLAUDE_SESSION_ID} \
  --action log-delivery
```
