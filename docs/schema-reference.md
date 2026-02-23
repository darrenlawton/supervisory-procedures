# Schema Reference — Agent Skill v1.0

Full field-by-field reference for the `skill.schema.json` v1.0 format.

---

## `metadata`

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | ✓ | `<business_area>/<kebab-name>`, e.g. `retail_banking/loan-application-processing` |
| `name` | string | ✓ | Human-readable display name |
| `version` | string | ✓ | Semantic version: `MAJOR.MINOR.PATCH` |
| `schema_version` | `"1.0"` | ✓ | Hub-controlled. Do not change. |
| `business_area` | string | ✓ | Slug matching your registry directory |
| `supervisor` | object | ✓ | See sub-fields below |
| `supervisor.name` | string | ✓ | Supervisor full name |
| `supervisor.email` | string (email) | ✓ | Supervisor email — must be monitored |
| `supervisor.role` | string | ✓ | Job title / role |
| `status` | `draft`/`approved`/`deprecated` | ✓ | Set to `draft` when authoring |
| `created_at` | date (ISO 8601) | ✓ | e.g. `2024-01-15` |
| `approved_at` | date or `null` | ✓ | Set by hub on approval; `null` for drafts |
| `approved_by` | string or `null` | ✓ | Set by hub on approval; `null` for drafts |
| `authorised_agents` | array[string] | ✓ | Agent IDs allowed to load this skill (min 1) |

---

## `context`

| Field | Type | Required | Description |
|---|---|---|---|
| `description` | string | ✓ | What business activity this skill governs |
| `business_rationale` | string | ✓ | Why AI assistance is appropriate here |
| `applicable_regulations` | array[string] | ✓ | Regulatory references (can be empty list) |
| `risk_classification` | `low`/`medium`/`high`/`critical` | ✓ | Risk level of AI involvement |

---

## `scope`

| Field | Type | Required | Description |
|---|---|---|---|
| `approved_activities` | array[string] | ✓ | Exhaustive list of what the agent MAY do (min 1) |

---

## `constraints`

| Field | Type | Required | Description |
|---|---|---|---|
| `procedural_requirements` | array[string] | ✓ | Steps the agent MUST follow (min 1) |
| `unacceptable_actions` | array[string] | ✓ | Absolute prohibitions — must NEVER do (min 1) |

---

## `hard_veto_triggers`

Array of objects (min 1). Each object:

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string (slug) | ✓ | Short identifier, e.g. `sanctions-hit` |
| `description` | string | ✓ | Plain English condition description |
| `condition_hint` | string | | Optional technical hint for developers |
| `action` | `halt_and_escalate`/`halt_and_notify`/`halt_and_refuse` | ✓ | What happens when triggered |
| `escalation_contact` | string | | Who to notify on escalation |

### Actions explained

- **`halt_and_escalate`** — Stop and immediately escalate to a senior contact (e.g. sanctions hit → Financial Crime team)
- **`halt_and_notify`** — Stop and send a notification to the relevant team
- **`halt_and_refuse`** — Stop and decline the request (e.g. a protected characteristic is detected)

---

## `oversight_checkpoints`

Two sub-arrays:

### `workflow_checkpoints`

Named stages in the normal workflow. Each object:

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string (slug) | ✓ | Short identifier |
| `name` | string | ✓ | Display name |
| `description` | string | ✓ | What this checkpoint does |
| `checkpoint_type` | `review`/`approve`/`notify`/`halt` | ✓ | Type of human involvement |
| `required` | boolean | ✓ | `true` = always triggered; `false` = conditional |
| `who_reviews` | string | ✓ | Who reviews at this checkpoint |
| `sla_hours` | integer | | Optional SLA in hours |

### `condition_triggered_checkpoints`

Triggered by deviations or anomalies. Each object:

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string (slug) | ✓ | Short identifier |
| `name` | string | ✓ | Display name |
| `trigger_condition` | string | ✓ | Plain English: what triggers this checkpoint |
| `description` | string | ✓ | What happens at this checkpoint |
| `checkpoint_type` | `review`/`approve`/`notify`/`halt` | ✓ | Type of human involvement |
| `who_reviews` | string | ✓ | Who reviews at this checkpoint |
| `sla_hours` | integer | | Optional SLA in hours |

### Checkpoint types explained

- **`review`** — A human reviews the agent's output but the process can continue
- **`approve`** — A human must explicitly approve before the process continues
- **`notify`** — Inform a stakeholder; no approval required
- **`halt`** — Stop the process and wait for human intervention
