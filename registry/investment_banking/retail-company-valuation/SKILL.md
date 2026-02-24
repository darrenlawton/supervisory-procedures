---
name: retail-company-valuation
description: >
  Constructs valuation models for publicly listed and private retail sector
  companies: restricted-list clearance, public filings retrieval, market data
  pull, comparable company multiples (EV/EBITDA, P/E, EV/Sales, EV/EBIT),
  DCF inputs, LBO skeleton, and a structured valuation summary for senior banker
  review. STATUS: draft. AUTHORISED-AGENTS: ib-valuation-agent-prod.
status: draft
authorised_agents:
  - ib-valuation-agent-prod
supervisor: "Your Full Name <your.name@bank.example.com>"
risk: high
schema_version: "2.0"
---

# Retail Company Valuation Model

**Supervisor:** Head of Investment Banking Coverage — Retail
**Risk:** High | **Regulations:** FCA MAR, FCA COBS 12.2, MiFID II

> For escalation contacts see [resources/escalation_contacts.md](resources/escalation_contacts.md).
> For regulatory detail see [resources/regulations.md](resources/regulations.md).

> **STATUS: draft** — this skill is not yet approved for production use. Do not
> share any output externally until Coverage MD approval has been obtained.

---

## Initialisation (run before any other action)

```bash
python registry/shared/audit-logging/scripts/audit_log.py \
  --skill investment_banking/retail-company-valuation \
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

If `"allowed": false` is returned, **halt immediately**. Do not perform the activity.

| Slug | Description |
|---|---|
| `check_restricted_list` | Check target against restricted and watch lists |
| `retrieve_public_filings` | Retrieve 10-K, 20-F, annual reports |
| `pull_market_data` | Pull approved market data feeds |
| `calculate_trading_multiples` | Calculate EV/EBITDA, P/E, EV/Sales, EV/EBIT |
| `build_dcf_inputs` | Build DCF model inputs from filings and consensus |
| `construct_lbo_skeleton` | Construct LBO model skeleton |
| `flag_data_anomalies` | Flag data gaps or anomalies for analyst follow-up |
| `generate_valuation_report` | Generate structured valuation summary report |
| `deliver_model` | Package and deliver approved model to authorised recipients |
| `write_audit_log_entry` | Log data sources, versions, assumptions to audit trail |

---

## Workflow (execute steps in this exact order)

### Step 1 — Restricted list check
**Activity:** `check_restricted_list`
**This is the first action. No data retrieval or modelling before clearance.**

```bash
python registry/shared/validate-activity/scripts/validate_activity.py \
  --activity check_restricted_list --allowlist scripts/approved_activities.json

python scripts/restricted_list_check.py \
  --company-id "$COMPANY_ID" --company-name "$COMPANY_NAME"
```

**If exit code 2 (MATCH) — target-on-restricted-list (vetoed), halt immediately:**
```bash
python registry/shared/checkpoint-gate/scripts/checkpoint_gate.py \
  --skill investment_banking/retail-company-valuation \
  --session ${CLAUDE_SESSION_ID} \
  --control-point target-on-restricted-list \
  --classification vetoed \
  --contact conflicts-office@bank.example.com \
  --detail "Restricted list match for $COMPANY_NAME"
# Exit code 2 — halt all processing now.
```

**On clear — invoke restricted-list-cleared (needs_approval), agent halts:**
```bash
python registry/shared/checkpoint-gate/scripts/checkpoint_gate.py \
  --skill investment_banking/retail-company-valuation \
  --session ${CLAUDE_SESSION_ID} \
  --control-point restricted-list-cleared \
  --classification needs_approval \
  --reviewer "Compliance — Conflicts Office" \
  --sla-hours 2
# PENDING — halt here. Do not retrieve any data until Compliance clears this.

python registry/shared/audit-logging/scripts/audit_log.py \
  --skill investment_banking/retail-company-valuation \
  --session ${CLAUDE_SESSION_ID} \
  --action check_restricted_list \
  --detail "Restricted list check complete: NO_MATCH for $COMPANY_NAME"
```

### Step 2 — Retrieve public filings
**Activity:** `retrieve_public_filings`

```bash
python registry/shared/validate-activity/scripts/validate_activity.py \
  --activity retrieve_public_filings --allowlist scripts/approved_activities.json

# If any data source flags MNPI or originates from a deal room → vetoed:
python registry/shared/checkpoint-gate/scripts/checkpoint_gate.py \
  --skill investment_banking/retail-company-valuation \
  --session ${CLAUDE_SESSION_ID} \
  --control-point inside-information-detected \
  --classification vetoed \
  --contact compliance-mnpi-desk@bank.example.com \
  --detail "MNPI flag detected in data source for $COMPANY_NAME"

# If data source is not on the approved vendor list → vetoed:
python registry/shared/checkpoint-gate/scripts/checkpoint_gate.py \
  --skill investment_banking/retail-company-valuation \
  --session ${CLAUDE_SESSION_ID} \
  --control-point data-source-not-approved \
  --classification vetoed \
  --contact ib-data-governance@bank.example.com

python registry/shared/audit-logging/scripts/audit_log.py \
  --skill investment_banking/retail-company-valuation \
  --session ${CLAUDE_SESSION_ID} \
  --action retrieve_public_filings \
  --detail "Filings retrieved for $COMPANY_NAME and comparables"
```

### Step 3 — Pull market data
**Activity:** `pull_market_data`

```bash
python registry/shared/validate-activity/scripts/validate_activity.py \
  --activity pull_market_data --allowlist scripts/approved_activities.json

python registry/shared/audit-logging/scripts/audit_log.py \
  --skill investment_banking/retail-company-valuation \
  --session ${CLAUDE_SESSION_ID} \
  --action pull_market_data \
  --detail "Market data pulled from approved feeds"
```

### Step 4 — Calculate trading multiples
**Activity:** `calculate_trading_multiples`

```bash
python registry/shared/validate-activity/scripts/validate_activity.py \
  --activity calculate_trading_multiples --allowlist scripts/approved_activities.json

python registry/shared/audit-logging/scripts/audit_log.py \
  --skill investment_banking/retail-company-valuation \
  --session ${CLAUDE_SESSION_ID} \
  --action calculate_trading_multiples
```

### Step 5 — Build DCF model inputs
**Activity:** `build_dcf_inputs`

```bash
python registry/shared/validate-activity/scripts/validate_activity.py \
  --activity build_dcf_inputs --allowlist scripts/approved_activities.json

python registry/shared/audit-logging/scripts/audit_log.py \
  --skill investment_banking/retail-company-valuation \
  --session ${CLAUDE_SESSION_ID} \
  --action build_dcf_inputs
```

### Step 6 — Construct LBO skeleton
**Activity:** `construct_lbo_skeleton`

```bash
python registry/shared/validate-activity/scripts/validate_activity.py \
  --activity construct_lbo_skeleton --allowlist scripts/approved_activities.json

python registry/shared/audit-logging/scripts/audit_log.py \
  --skill investment_banking/retail-company-valuation \
  --session ${CLAUDE_SESSION_ID} \
  --action construct_lbo_skeleton
```

### Step 7 — Flag data anomalies
**Activity:** `flag_data_anomalies`

If a material inconsistency or anomaly is found (e.g. restatement, non-recurring
items > 10% of EBITDA), invoke the data-anomaly-flagged review checkpoint before
proceeding:

```bash
python registry/shared/checkpoint-gate/scripts/checkpoint_gate.py \
  --skill investment_banking/retail-company-valuation \
  --session ${CLAUDE_SESSION_ID} \
  --control-point data-anomaly-flagged \
  --classification review \
  --reviewer "Analyst or Associate — Investment Banking Coverage" \
  --sla-hours 4 \
  --detail "$ANOMALY_DESCRIPTION"
# PENDING — analyst must acknowledge anomaly before proceeding.
```

### Step 8 — Generate valuation report
**Activity:** `generate_valuation_report`

```bash
python registry/shared/validate-activity/scripts/validate_activity.py \
  --activity generate_valuation_report --allowlist scripts/approved_activities.json
```

After generating the report, invoke senior banker review. **Agent must halt here:**

```bash
python registry/shared/checkpoint-gate/scripts/checkpoint_gate.py \
  --skill investment_banking/retail-company-valuation \
  --session ${CLAUDE_SESSION_ID} \
  --control-point valuation-senior-review \
  --classification needs_approval \
  --reviewer "VP or MD — Investment Banking Coverage" \
  --sla-hours 24
# PENDING — halt here. Do not deliver until senior banker signs off.

python registry/shared/audit-logging/scripts/audit_log.py \
  --skill investment_banking/retail-company-valuation \
  --session ${CLAUDE_SESSION_ID} \
  --action generate_valuation_report \
  --detail "Valuation report generated and submitted for senior banker review"
```

### Step 9 — Deliver model (post-clearance only)
**Activity:** `deliver_model`
**Only execute after senior banker sign-off has been received for step 8.**

Before any external delivery, Coverage MD must explicitly approve:

```bash
python registry/shared/checkpoint-gate/scripts/checkpoint_gate.py \
  --skill investment_banking/retail-company-valuation \
  --session ${CLAUDE_SESSION_ID} \
  --control-point external-sharing-approval \
  --classification needs_approval \
  --reviewer "Coverage Managing Director" \
  --sla-hours 4
# PENDING — halt here. No external sharing until Coverage MD approves.

python registry/shared/audit-logging/scripts/audit_log.py \
  --skill investment_banking/retail-company-valuation \
  --session ${CLAUDE_SESSION_ID} \
  --action deliver_model \
  --detail "Valuation model delivered to authorised recipients"
```

---

## What you must never do

- Use non-public (inside) information as a model input
- Retrieve data from any source not on the approved vendor list
- Share the valuation externally without Coverage MD sign-off
- Suppress or override a flagged data anomaly without analyst acknowledgement
- Generate a final investment recommendation — analysis only
- Access deal team data rooms for companies outside the approved coverage list

---

## Private company target

If the target is not publicly listed, the `private-company-target` control point
applies before any modelling proceeds:

```bash
python registry/shared/checkpoint-gate/scripts/checkpoint_gate.py \
  --skill investment_banking/retail-company-valuation \
  --session ${CLAUDE_SESSION_ID} \
  --control-point private-company-target \
  --classification needs_approval \
  --reviewer "Legal Counsel + Compliance" \
  --sla-hours 48
# PENDING — halt here until Legal and Compliance confirm data usage is permissible.
```
