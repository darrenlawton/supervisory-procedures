# Schema Simplification Recommendations — skill.yml v2.0

**Date:** 2026-02-25
**Scope:** Review of `skill.schema.json` v2.0 against the three production skill definitions, renderer, validator, wizard, CI pipeline, and supporting artifacts.

**Guiding principle:** The skill.yml is authored by a business manager (the accountable party) who may have limited technical background. Every field in the schema should either (a) express a supervisory decision the manager must make, or (b) be derivable/defaulted by tooling. The schema should make the *right* thing easy and the *wrong* thing impossible.

---

## Recommendation 1 — Eliminate explicit audit-log workflow steps; make logging automatic

### Problem

In the investment banking skill, 7 of 17 workflow steps are `audit-log` entries. In the loan processing skill, 5 of 12 steps are logging. These steps:

- Clutter the workflow, making it harder to read the actual business process
- Are not supervisory decisions — they are infrastructure requirements
- Are already handled by the renderer, which emits an `audit_log.py` bash command for *every* step in the generated SKILL.md

The manager is being asked to manually weave in something the system already does automatically.

### Recommendation

Remove the need for explicit `audit-log` activity and workflow steps. The renderer already injects audit logging at every step. Make this behaviour implicit and documented:

- Remove `audit-log` from `scope.approved_activities` (it is an infrastructure concern, not a business activity)
- Remove all `log-*` steps from `workflow.steps`
- Document in the authoring guide that every workflow step is automatically audit-logged

### Impact on the five objectives

| Objective | Effect |
|---|---|
| What is it approved to do? | Cleaner — the allowlist focuses on genuine business activities |
| What must it never do? | No change |
| How should it execute? | Clearer — the workflow shows only business-meaningful steps |
| Where does a human stay? | No change |
| Who is authorised? | No change |

### Investment banking workflow: before vs after

**Before (17 steps):**
```
restricted-list-check → log-list-check → retrieve-public-filings → log-filings-retrieved → pull-market-data → log-market-data-retrieved → calculate-trading-multiples → log-multiples-calculated → build-dcf-inputs → log-dcf-built → construct-lbo-skeleton → log-lbo-constructed → flag-data-anomalies → generate-valuation-report → log-report-generated → deliver-model → log-delivery
```

**After (10 steps):**
```
restricted-list-check → retrieve-public-filings → pull-market-data → calculate-trading-multiples → build-dcf-inputs → construct-lbo-skeleton → flag-data-anomalies → generate-valuation-report → deliver-model
```

---

## Recommendation 2 — Remove the `helper_skills` section entirely

### Problem

Every skill in the registry declares the same three helper skills with `required: true`:

- `shared/audit-logging`
- `shared/checkpoint-gate`
- `shared/validate-activity`

These are not supervisory decisions — they are system-level infrastructure that every skill must use. Asking managers to declare them is both unnecessary and risky (a manager could accidentally omit one or set `required: false`).

### Recommendation

Remove `helper_skills` from the schema. The renderer should unconditionally include the standard helper skills. If a future need arises for skill-specific helper skills, that can be added as an optional section with tighter constraints.

### Justification

The `helper_skills` section currently serves no governance function: the same three entries appear in every file, the renderer already hard-codes their script paths, and there is no validation that a declared helper skill actually exists in `registry/shared/`. Removing it eliminates boilerplate without reducing supervisory control.

---

## Recommendation 3 — Remove hub-managed lifecycle fields from required manager input

### Problem

The schema requires `approved_at`, `approved_by`, `created_at`, and `status` as required fields. The authoring guide explicitly states that `approved_at` and `approved_by` are "Set by hub on approval." Yet managers must include `approved_at: null` and `approved_by: null` in every draft. Similarly, `created_at` is always just today's date.

These are lifecycle metadata managed by the approval pipeline, not supervisory decisions.

### Recommendation

**Option A (preferred):** Make `approved_at`, `approved_by`, and `created_at` optional in the schema. The wizard and CI pipeline can populate them automatically. `status` should remain required (the manager needs to understand draft vs approved), but default to `draft` in the wizard.

**Option B:** Move lifecycle fields into a separate `lifecycle` sub-object within metadata to visually separate manager-authored fields from system-managed fields:

```yaml
metadata:
  id: retail_banking/loan-application-processing
  name: Loan Application Processing
  version: 1.0.0
  schema_version: "2.0"
  business_area: retail_banking
  supervisor: { ... }
  authorised_agents: [...]
  # --- system-managed below ---
  lifecycle:
    status: draft
    created_at: "2026-02-25"
    approved_at: null
    approved_by: null
```

### Justification

Managers should only be asked to provide information that represents their supervisory decisions. System lifecycle fields are not decisions — they are administrative bookkeeping. Including them as required fields creates confusion about what the manager owns vs what the system owns.

---

## Recommendation 4 — Eliminate the double-ID pattern on workflow steps

### Problem

Workflow steps currently require both an `id` and an `activity` reference. In practice these are almost always identical:

```yaml
- id: query-sanctions-lists
  activity: query-sanctions-lists
```

When they differ, it's only for the logging steps (e.g., `id: log-list-check`, `activity: audit-log`) which Recommendation 1 eliminates. The remaining case — multiple steps referencing the same activity — is rare and could be handled by allowing the same activity to appear multiple times in the workflow.

### Recommendation

Make `id` optional. If omitted, default to the value of `activity`. This preserves backward compatibility (existing files with both fields still validate) while reducing redundancy for new authors. The step ID only needs to differ from the activity ID when the same activity appears more than once in the workflow — and in that case the author can override.

```yaml
# Simple case (most steps):
workflow:
  steps:
    - activity: query-sanctions-lists
    - activity: query-pep-database
    - activity: classify-hits
      control_point: evidence-package-review

# Override case (same activity used twice):
    - id: send-progress-notification
      activity: send-notification
    - id: send-final-notification
      activity: send-notification
```

### Justification

The current pattern forces every author to type each activity ID twice. This adds no supervisory value and creates opportunities for typos. The validator already cross-references `activity` → `scope.approved_activities`, so the governance check is preserved.

---

## Recommendation 5 — Flatten the `scope` wrapper

### Problem

The `scope` section contains exactly one field: `approved_activities`. The extra nesting level adds no value:

```yaml
scope:
  approved_activities:
    - id: run-query
      description: ...
```

### Recommendation

Rename `scope` to `approved_activities` as a top-level array, or keep `scope` but allow direct content:

**Option A (flatten entirely):**
```yaml
approved_activities:
  - id: run-query
    description: Perform read-only queries
```

**Option B (keep scope but rename for clarity):**
```yaml
scope:
  - id: run-query
    description: Perform read-only queries
```

### Justification

Option A is the simplest. The section name `approved_activities` is self-documenting and directly answers "What is it approved to do?" without an intermediate wrapper. If additional scope-related fields are anticipated in future (e.g., `data_access_boundaries`), Option B preserves extensibility — but that should be a decision based on concrete plans, not hypothetical future needs.

**Recommended:** Option A, unless there are near-term plans to add other scope fields.

---

## Recommendation 6 — Drop `condition_hint` from the schema

### Problem

`condition_hint` contains developer-facing pseudocode:

```yaml
condition_hint: >
  sanctions_hit.confidence >= 0.90 AND
  (sanctions_hit.name_match == "exact" OR sanctions_hit.alias_match == "exact")
```

This field:

- Is not a supervisory decision — it's an implementation detail
- Requires technical knowledge to write correctly
- Has no validation (it's free-text pseudocode that may or may not match actual implementations)
- Belongs in the implementation layer (e.g., in the business-specific `scripts/` directory or as code comments)

### Recommendation

Remove `condition_hint` from the schema. If implementation teams need to document how a trigger condition maps to code, this belongs in:

- The `scripts/` directory alongside the implementation
- A separate developer-facing document
- Code comments in the actual trigger detection logic

The `trigger_condition` field (plain English) is sufficient for the manager-authored supervisory document. The implementation detail of *how* that condition is detected programmatically should live closer to the code.

### Justification

The skill.yml is a supervisory document, not an implementation specification. Including `condition_hint` blurs the boundary between "what the manager authorises" and "how the developer builds it." The existing `trigger_condition` (plain English) adequately captures the manager's intent.

---

## Recommendation 7 — Make `name` optional on control points (derive from `id`)

### Problem

Control points require both `id` and `name`:

```yaml
- id: exact-sanctions-list-match
  name: Exact Sanctions List Match
```

In every example, `name` is simply a title-cased version of `id`. This is mechanical and adds no information.

### Recommendation

Make `name` optional. When omitted, the renderer and tooling derive a display name by converting the slug to title case (`exact-sanctions-list-match` → `Exact Sanctions List Match`). Authors who want a different display name can still provide one.

### Justification

Reduces field count per control point from 4 required fields to 3. For a skill like the sanctions-pep example with 11 control points, this eliminates 11 redundant entries.

---

## Recommendation 8 — Add artifact consistency validation

### Problem (the gap you identified)

The validator cross-references `workflow.steps[].activity` against `scope.approved_activities` and checks SKILL.md freshness — but there is no validation of the supporting artifacts in the skill directory:

| Artifact | Current validation | Gap |
|---|---|---|
| `resources/escalation_contacts.md` | None | Contacts in this file may not match `escalation_contact` fields in control points |
| `resources/regulations.md` | None | Regulations covered may not match `context.applicable_regulations` |
| `scripts/*.py` | None | Scripts may exist without being referenced, or be missing |
| `shared/*` referenced by `uses_skill` | None | Referenced shared skills may not exist in `registry/shared/` |

### Recommendation

Add a new validation pass (`_check_artifact_consistency`) in the validator that:

1. **Escalation contacts:** Warn if any `escalation_contact` in a control point is not mentioned in `resources/escalation_contacts.md` (if the file exists)
2. **Regulations:** Warn if `resources/regulations.md` exists but doesn't contain headings or references matching `context.applicable_regulations` entries
3. **Shared skill existence:** Error if `workflow.steps[].uses_skill` references a shared skill ID that doesn't exist as a directory in `registry/shared/`
4. **Script inventory:** Warn if `scripts/` contains Python files that are not referenced by any workflow step or control point implementation

This should produce warnings (not errors) for items 1, 2, and 4, since the artifacts are supplementary documentation. Item 3 should be an error since a missing shared skill would break execution.

### Justification

The skill directory is a cohesive package — `skill.yml`, `SKILL.md`, `resources/`, and `scripts/` must be consistent. Currently a manager could update a control point's escalation contact in the YAML without updating `resources/escalation_contacts.md`, leaving the agent with contradictory information. Validation closes this gap without requiring structural changes to the schema itself.

---

## Recommendation 9 — Add an `artifacts` section to formalise the skill directory contract

### Problem (related to Recommendation 8)

The skill directory contains artifacts (`resources/*.md`, `scripts/*.py`) that support skill execution, but the schema has no awareness of them. The relationship between the YAML definition and these files is implicit — discoverable only by reading the authoring guide and examining existing examples.

### Recommendation

Add an optional `artifacts` section to the schema that declares the supporting files:

```yaml
artifacts:
  resources:
    - file: regulations.md
      description: Detailed regulatory obligations and agent-specific guidance
    - file: escalation_contacts.md
      description: Contact directory for all control point escalations
  scripts:
    - file: sanctions_check.py
      description: Wraps the OFAC/HM Treasury API for sanctions screening
      used_by_activity: sanctions-screening
```

This section would:

- Make the skill directory contents explicit and inspectable
- Enable the validator to check that declared files actually exist
- Enable the renderer to reference these files in SKILL.md (e.g., "See resources/regulations.md for detailed regulatory guidance")
- Document the purpose of each artifact for the next person maintaining the skill

### Justification

The current system treats the skill directory as a loose collection of files. An `artifacts` section turns it into a declared, validated package. This is particularly important given that different managers will have different levels of familiarity with the directory conventions.

**Trade-off:** This adds a new section to the YAML. It should be optional (with validation warnings if artifacts exist in the directory but aren't declared) to avoid blocking adoption.

---

## Recommendation 10 — Clarify the two control point activation models with naming

### Problem

Control points currently use the presence or absence of `trigger_condition` to determine their activation model:

- **With** `trigger_condition`: fires automatically when the condition is detected, at any point during workflow execution
- **Without** `trigger_condition`: fires only when explicitly referenced by a workflow step via `control_point`

This distinction is fundamental to understanding how oversight works, but it's implicit — determined by whether an optional field happens to be populated. The authoring guide explains it, but the schema itself doesn't make it obvious.

### Recommendation

Rename `trigger_condition` to `trigger` and add an `activation` field with two explicit values:

```yaml
control_points:
  # Fires when a condition is detected — not tied to a specific step
  - id: sanctions-match
    description: ...
    classification: vetoed
    activation: conditional
    trigger: >
      Positive match returned from HM Treasury or OFAC sanctions screening
      with match_confidence >= 0.85 or exact_match == true.
    escalation_contact: financial-crime-team@bank.example.com

  # Fires at a specific workflow step
  - id: creditworthiness-assessment-review
    description: ...
    classification: needs_approval
    activation: step
    who_reviews: Qualified underwriter
    sla_hours: 24
```

The validator would enforce:
- `activation: conditional` requires `trigger` to be present
- `activation: step` requires the control point to be referenced by at least one `workflow.steps[].control_point`

### Justification

Making the activation model explicit rather than implicit helps managers understand what they are defining. "This control point fires conditionally" vs "this control point fires at a workflow step" is a clearer mental model than "this one has a trigger_condition field and that one doesn't."

**Trade-off:** Adds one more required field per control point. Justified because the activation model is a core supervisory decision — "when does my oversight kick in?"

---

## Recommendation 11 — Enforce `who_reviews` and `escalation_contact` based on classification

### Problem

The schema describes `who_reviews` as "Expected for notify, review, and needs_approval classifications" and `escalation_contact` as "Most relevant for vetoed classification" — but neither is enforced. A manager could create a `needs_approval` control point without specifying who approves, or a `vetoed` control point without specifying who to escalate to.

### Recommendation

Add conditional required fields using JSON Schema `if/then`:

- `classification: needs_approval` or `review` → require `who_reviews`
- `classification: vetoed` → require `escalation_contact`
- `classification: notify` → require `who_reviews` (who is notified)
- `classification: auto` → neither required

### Justification

If a manager defines a control point that halts execution pending approval, the system must know who can provide that approval. This is not optional metadata — it's a core governance requirement. Making it conditionally required prevents incomplete control point definitions from passing validation.

---

## Summary — Priority and Impact

| # | Recommendation | Priority | Authoring burden | Governance impact |
|---|---|---|---|---|
| 1 | Eliminate explicit audit-log steps | High | Major reduction | Neutral (logging is automatic) |
| 2 | Remove `helper_skills` section | High | Moderate reduction | Positive (removes risk of omission) |
| 3 | Remove hub-managed lifecycle fields from required | High | Moderate reduction | Neutral (system manages them) |
| 4 | Eliminate double-ID on workflow steps | Medium | Moderate reduction | Neutral |
| 5 | Flatten `scope` wrapper | Medium | Minor reduction | Neutral |
| 6 | Drop `condition_hint` | Medium | Minor reduction | Positive (clearer ownership boundary) |
| 7 | Make control point `name` optional | Low | Minor reduction | Neutral |
| 8 | Add artifact consistency validation | High | No change (validation only) | Significant improvement |
| 9 | Add `artifacts` section to schema | Medium | Minor increase | Significant improvement |
| 10 | Explicit control point activation model | Medium | Neutral (trade-off) | Positive (clearer mental model) |
| 11 | Enforce `who_reviews`/`escalation_contact` by classification | High | No change | Significant improvement |

### Recommended implementation order

**Phase 1 — Quick wins (reduce noise, improve governance):**
- Rec 1: Remove audit-log steps
- Rec 2: Remove `helper_skills`
- Rec 3: Make lifecycle fields optional
- Rec 8: Add artifact consistency validation
- Rec 11: Enforce conditional required fields

**Phase 2 — Schema refinement:**
- Rec 4: Optional step ID
- Rec 5: Flatten `scope`
- Rec 6: Drop `condition_hint`
- Rec 7: Optional control point `name`

**Phase 3 — Structural improvements:**
- Rec 9: `artifacts` section
- Rec 10: Explicit activation model

---

## What this does NOT recommend changing

The following aspects of the current schema are well-designed and should be preserved:

1. **The five-classification control point model** (`auto`, `notify`, `review`, `needs_approval`, `vetoed`) — this is clear, exhaustive, and maps well to real oversight patterns
2. **The approved activities allowlist** — the exhaustive permit-list is the right governance approach
3. **The unacceptable actions list** — absolute prohibitions are essential and well-implemented
4. **Workflow step ordering** — sequential execution with no skip/reorder is the right default for regulated processes
5. **Schema validation in CI** — the PR-gated validation pipeline is essential
6. **The separation of skill.yml (manager-authored) and SKILL.md (system-generated)** — this cleanly separates authoring from execution
7. **The wizard** — guided authoring is essential for non-technical managers
8. **Authorised agents list** — explicit agent-level access control is a core governance requirement
