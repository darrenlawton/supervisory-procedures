# Agent Skill — Pull Request

## Skill Summary

- **Skill ID**: `<business_area>/<skill-name>`
- **Business Area**:
- **Supervisor**:
- **Change type**: `[ ] New skill  [ ] Update  [ ] Deprecate`

---

## Supervisor Sign-off Checklist

_Complete before opening this PR._

- [ ] I have read the [Authoring Guide](../docs/authoring-guide.md)
- [ ] The skill has been validated locally: `supv validate registry/<path>.yml`
- [ ] All **approved activities** are explicitly listed — the list is exhaustive
- [ ] At least one **hard veto trigger** is defined
- [ ] **Authorised agents** are named explicitly (not `*`)
- [ ] The **supervisor email** is current and monitored
- [ ] **Applicable regulations** have been reviewed with the compliance team
- [ ] The **risk classification** reflects the actual risk (if `high` or `critical`, compliance approval is required)

## Regulatory / Compliance Confirmation

- [ ] Compliance team has reviewed this skill (attach sign-off if `risk_classification: high/critical`)
- [ ] Data processing implications reviewed with DPO (if personal data is involved)

## For Hub Team Review

- [ ] Schema version is `1.0` (or PR includes a schema version bump with CHANGELOG update)
- [ ] CI `validate-skills` check passes
- [ ] CODEOWNERS has been updated if a new business area directory was created

---

## Description of Changes

_Describe what the skill does and why it is being added or changed._

## Related Issues / Approvals

_Link to any compliance tickets, governance decisions, or change requests._
