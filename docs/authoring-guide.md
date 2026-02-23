# Authoring Guide — Agent Skill Definitions

_Written for business supervisors. No programming knowledge required._

---

## What is an Agent Skill?

An **Agent Skill** is a structured document that tells an AI agent what it is allowed to do, what it must never do, and when it must pause and wait for human review. Think of it as the written authorisation and operating procedure for an AI assistant in your area.

Skills are stored as files in the Git registry and go through a controlled approval process before an AI agent can use them.

---

## How to Create a Skill

### Option 1 — Use the Wizard (Recommended)

The fastest way is the guided command-line wizard. Open a terminal and run:

```bash
supv new
```

The wizard will ask you questions in plain English and write the YAML file for you. You do not need to know YAML syntax.

### Option 2 — Copy an Example

Copy an existing skill from the registry that is similar to what you need:

```bash
cp registry/retail_banking/loan_application_processing.yml \
   registry/<your_business_area>/<your_skill_name>.yml
```

Then edit the file. Use the [Schema Reference](schema-reference.md) as a guide.

---

## Skill Structure Overview

A skill has six sections:

| Section | Purpose |
|---|---|
| `metadata` | Who owns this skill, what version it is, who is approved to use it |
| `context` | What business activity this covers and why AI is appropriate |
| `scope` | The **complete list** of things the agent is allowed to do |
| `constraints` | Steps the agent must follow, and things it must never do |
| `hard_veto_triggers` | Conditions where the agent must immediately stop |
| `oversight_checkpoints` | Points in the workflow where a human must review or approve |

---

## Key Authoring Principles

### 1. The Approved Activities List is Exhaustive

The `scope.approved_activities` list is not a suggestion — it is an **allowlist**. Anything not on the list is forbidden. Write it carefully and be specific.

Good: _"Calculate debt-to-income ratio using declared and verified income figures"_
Too vague: _"Process financial data"_

### 2. Define Hard Veto Triggers for Your Highest Risks

Hard veto triggers cause the agent to **immediately stop** if a dangerous condition is detected. Every skill must have at least one. Think about the scenarios that would be most harmful if the AI continued:

- A sanctions screening match
- A suspected fraud indicator
- Missing data that would make a compliant decision impossible
- Any legal or regulatory "bright line" that must never be crossed

### 3. Name Your Authorised Agents Explicitly

The `authorised_agents` field controls which AI agents can load this skill. Use the agent's full ID (e.g. `loan-processor-agent-prod`). Avoid using `*` (which allows any agent) except in controlled test environments.

### 4. Status Starts as `draft`

New skills start with `status: draft`. The wizard sets this automatically. The skill is promoted to `approved` by the hub team after the pull request is reviewed. A draft skill cannot be loaded by any agent.

---

## Submitting Your Skill for Approval

1. Create the skill file using `supv new` or by editing a copy
2. Validate it locally: `supv validate registry/<area>/<skill>.yml`
3. Create a git branch and commit the file
4. Open a pull request — use the provided template and complete the checklist
5. Your business area's governance team will review the PR
6. The central innovation hub team will do a final check and merge

Once merged to `main`, the `approved_at` and `approved_by` fields are set, and the skill is live.

---

## Maintaining Skills

### Updating a Skill

Edit the YAML file and increase the `version` field (e.g. `1.0.0` → `1.1.0`). Submit a PR following the same process.

### Deprecating a Skill

Set `status: deprecated`. The agent can no longer load it. Submit a PR with a brief explanation of why the skill is being retired.

---

## Getting Help

- Run `supv --help` for CLI reference
- See [Schema Reference](schema-reference.md) for field-by-field documentation
- See [Hub-Spoke Governance](hub-spoke-governance.md) for the approval process
- Contact the central innovation team for assistance
