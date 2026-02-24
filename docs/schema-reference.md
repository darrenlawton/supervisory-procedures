# Schema Reference — Agent Skill v2.0

Full field-by-field reference for the `skill.schema.json` v2.0 format.

---

## `metadata`

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | ✓ | `<business_area>/<kebab-name>`, e.g. `retail_banking/loan-application-processing` |
| `name` | string | ✓ | Human-readable display name |
| `version` | string | ✓ | Semantic version: `MAJOR.MINOR.PATCH` |
| `schema_version` | `"2.0"` | ✓ | Hub-controlled. Do not change. |
| `business_area` | string | ✓ | Slug matching your registry directory name |
| `type` | `standard`/`shared` | | `standard` for business area skills; `shared` for registry-wide helper skills |
| `supervisor` | object | ✓ | See sub-fields below |
| `supervisor.name` | string | ✓ | Supervisor full name |
| `supervisor.email` | string (email) | ✓ | Supervisor email — must be actively monitored |
| `supervisor.role` | string | ✓ | Job title / role |
| `status` | `draft`/`approved`/`deprecated` | ✓ | Set to `draft` when authoring; hub sets `approved` on merge |
| `created_at` | date (ISO 8601) | ✓ | e.g. `2024-01-15` |
| `approved_at` | date or `null` | ✓ | Set by hub on approval; `null` for drafts |
| `approved_by` | string or `null` | ✓ | Set by hub on approval; `null` for drafts |
| `authorised_agents` | array[string] | ✓ | Agent IDs allowed to load this skill (min 1) |

---

## `context`

| Field | Type | Required | Description |
|---|---|---|---|
| `description` | string | ✓ | What business activity this skill governs. Also used to generate the agent-facing skill description in `SKILL.md`. |
| `business_rationale` | string | ✓ | Why AI assistance is appropriate here |
| `applicable_regulations` | array[string] | ✓ | Regulatory references (can be empty list) |
| `risk_classification` | `low`/`medium`/`high`/`critical` | ✓ | Risk level of AI involvement in this activity |

---

## `scope`

| Field | Type | Required | Description |
|---|---|---|---|
| `approved_activities` | array[string] | ✓ | Exhaustive allowlist of what the agent MAY do (min 1). Every `workflow.steps[].activity` must exactly match an entry here. |

---

## `constraints`

| Field | Type | Required | Description |
|---|---|---|---|
| `procedural_requirements` | array[string] | ✓ | Steps the agent MUST follow (min 1) |
| `unacceptable_actions` | array[string] | ✓ | Absolute prohibitions — the agent must NEVER do these (min 1) |

---

## `control_points`

Array of control point objects (min 1). The unified oversight model: every point where human involvement applies — from unconditional halt to automatic pass-through — is expressed as a control point with a `classification`.

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string (slug) | ✓ | Short kebab-case identifier, e.g. `sanctions-match` |
| `name` | string | ✓ | Display name |
| `description` | string | ✓ | Plain English description of what this control point represents |
| `classification` | see below | ✓ | The level of human involvement required |
| `trigger_condition` | string | | Plain English condition that causes this control point to fire automatically. Omit for control points attached to specific workflow steps. |
| `condition_hint` | string | | Optional technical hint for developers implementing trigger detection |
| `who_reviews` | string | | Role or person responsible for review/approval (required for `review`, `needs_approval`, `notify`) |
| `escalation_contact` | string | | Email or contact for escalation (required for `vetoed`) |
| `sla_hours` | integer | | Response SLA in hours |

### Classifications

| Value | Meaning |
|---|---|
| `vetoed` | Agent halts **unconditionally and immediately**. No human can override. Exit code 2 from `checkpoint_gate.py`. Use for your highest-risk conditions. |
| `needs_approval` | Agent halts and waits for **explicit sign-off** before continuing. Agent resumes only on receipt of approval. |
| `review` | Agent halts and waits for a **human reviewer** to clear the output before continuing. |
| `notify` | Human is informed but the agent is **not blocked**. Audit record is written. |
| `auto` | Agent proceeds **without human involvement**. Used to record a successful pass-through gate in the audit trail. |

---

## `workflow`

Defines the ordered sequence of steps the agent must follow.

### `workflow.steps`

Array of step objects (min 1). Steps are executed in array order — the agent must not skip, reorder, or add steps.

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string (slug) | ✓ | Step identifier, e.g. `sanctions-screening`. Used by `validate_activity.py` to verify the step is in scope. |
| `activity` | string | ✓ | Must exactly match an entry in `scope.approved_activities` |
| `control_point` | string | | ID of a control point (without `trigger_condition`) to invoke after this step completes |
| `uses_skill` | string | | Reference to a shared helper skill, e.g. `shared/audit-logging` |

---

## `helper_skills`

Optional array of shared helper skills used in the workflow. Each object:

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | ✓ | Must be in `shared/<skill-name>` format |
| `purpose` | string | ✓ | Why this helper skill is needed |
| `required` | boolean | ✓ | `true` if the workflow cannot proceed without it |

### Standard helper skills

| ID | Purpose |
|---|---|
| `shared/audit-logging` | Writes timestamped audit trail entries at every workflow step |
| `shared/checkpoint-gate` | Enforces control points at runtime; exits 0 (proceed) or 2 (vetoed) |
| `shared/validate-activity` | Verifies each workflow step is in scope before execution |

---

## Generated files

These files are produced by `supv render` and must never be edited by hand:

| File | Description |
|---|---|
| `SKILL.md` | Claude Agent Skills compatible instruction document. Contains the supervisor's procedure formatted as agent-readable instructions with embedded bash commands for all helper skill invocations. |

The CI pipeline validates that `SKILL.md` matches the current `skill.yml` on every PR. If `skill.yml` is updated without re-running `supv render`, validation fails.
