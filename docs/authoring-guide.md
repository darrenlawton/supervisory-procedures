# Authoring Guide — Agent Skill Definitions

_Written for business supervisors. No programming knowledge required._

---

## What is an Agent Skill?

An **Agent Skill** is a structured document that tells an AI agent what it is allowed to do, what it must never do, and when it must pause and wait for human review. Think of it as the written authorisation and operating procedure for an AI assistant in your area.

Skills are stored as YAML files in the Git registry and go through a controlled approval process before an AI agent can use them. Once approved, a `SKILL.md` is generated from your definition and becomes the agent's runtime instruction document — ensuring the agent always operates according to your procedure.

---

## How to Create a Skill

### Option 1 — Use the Wizard (Recommended)

The fastest way is the guided command-line wizard. Open a terminal and run:

```bash
supv new
```

The wizard walks through every section of the skill definition in plain English — no YAML knowledge required. It covers 9 steps: business area, name and version, supervisor details, context, approved activities, constraints, control points, workflow, and authorised agents.

When complete, the wizard saves `skill.yml` to the registry. Then generate the agent instruction document:

```bash
supv render <business_area>/<skill-name>
```

### Option 2 — Copy an Example

Copy an existing skill directory that is similar to what you need:

```bash
cp -r registry/retail_banking/loan-application-processing \
      registry/<your_business_area>/<your_skill_name>
```

Edit `skill.yml` in the new directory. Use the [Schema Reference](schema-reference.md) as a guide. Run `supv render` to regenerate `SKILL.md` after every change.

---

## Skill Structure Overview

A skill has seven sections:

| Section | Purpose |
|---|---|
| `metadata` | Who owns this skill, what version it is, who is approved to use it |
| `context` | What business activity this covers and why AI is appropriate |
| `scope` | The **complete list** of activities the agent is allowed to perform |
| `constraints` | Steps the agent must follow, and things it must never do |
| `control_points` | Every point where human oversight applies — from unconditional halt to automatic pass-through |
| `workflow` | The ordered sequence of steps the agent must follow, each mapped to an approved activity |
| `helper_skills` | Shared infrastructure skills used in the workflow (audit logging, checkpoint enforcement, scope validation) |

---

## Control Points

Control points are the mechanism through which you define human oversight. Every situation requiring human involvement — whether a hard stop, a sign-off, a review, or a notification — is a control point. Each has a `classification`:

| Classification | What it means |
|---|---|
| `vetoed` | Agent halts **unconditionally and immediately**. No human can override. Use for your highest-risk conditions (sanctions match, MNPI detection, identity failure). |
| `needs_approval` | Agent halts and waits for **explicit sign-off** before continuing. Use where a named human must authorise before the next step. |
| `review` | Agent halts and waits for a **human reviewer** to clear the output before continuing. |
| `notify` | Human is informed but the agent is **not blocked**. Use for awareness without requiring action. |
| `auto` | Agent proceeds **without human involvement**. Used to record a successful gate in the audit trail. |

Control points with a `trigger_condition` fire automatically when that condition is detected — at any point during the workflow. Control points without a `trigger_condition` are attached to specific workflow steps.

---

## Key Authoring Principles

### 1. The Approved Activities List is Exhaustive

`scope.approved_activities` is an **allowlist** — not a suggestion. Anything not on the list is forbidden. Write descriptions carefully and specifically.

Good: _"Calculate debt-to-income ratio using declared and verified income figures"_
Too vague: _"Process financial data"_

### 2. Define Vetoed Control Points for Your Highest Risks

Use `classification: vetoed` for conditions where continued agent operation would be dangerous or unlawful. These cause the agent to halt immediately with no possibility of override. Think about:

- A sanctions screening match
- Detection of material non-public information (MNPI)
- A required data source being unavailable
- Any regulatory bright line that must never be crossed

### 3. Map Every Workflow Step to an Approved Activity

Each step in `workflow.steps` must reference an `activity` that appears exactly in `scope.approved_activities`. The agent validates this at each step before executing.

### 4. Name Your Authorised Agents Explicitly

`authorised_agents` controls which AI agents can load this skill. Use the agent's full ID (e.g. `loan-processor-agent-prod`). Avoid `*` (which allows any agent) except in controlled test environments.

### 5. Status Starts as `draft`

New skills start with `status: draft`. The wizard sets this automatically. A draft skill cannot be loaded by any agent. The skill is promoted to `approved` by the hub team after the pull request is reviewed.

---

## Submitting Your Skill for Approval

1. Create the skill using `supv new` or by editing a copy
2. Generate the agent instruction document: `supv render <area>/<skill-name>`
3. Validate locally: `supv validate registry/<area>/<skill-name>/skill.yml --strict`
4. Create a git branch and commit **both** `skill.yml` and the generated `SKILL.md`
5. Open a pull request — use the provided template and complete the checklist
6. Your business area's governance team reviews the content
7. The central innovation hub team does a final structural check and merges

Once merged, `approved_at` and `approved_by` are set, and the skill is live.

---

## Maintaining Skills

### Updating a Skill

Edit `skill.yml` and increase the `version` field (e.g. `1.0.0` → `1.1.0`). Re-run `supv render` to regenerate `SKILL.md`. Submit a PR with both files. The CI pipeline will block the merge if `SKILL.md` does not match the current `skill.yml`.

### Deprecating a Skill

Set `status: deprecated`. The agent can no longer load it. Submit a PR with a brief explanation of why the skill is being retired. The `SKILL.md` does not need to be updated for deprecation.

---

## Getting Help

- Run `supv --help` for CLI reference
- See [Schema Reference](schema-reference.md) for field-by-field documentation
- See [Hub-Spoke Governance](hub-spoke-governance.md) for the approval process
- Contact the central innovation team for assistance
