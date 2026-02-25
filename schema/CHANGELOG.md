# Schema Changelog

## v2.1 (2026-02-25)

Implements schema simplification recommendations from
`docs/schema-simplification-recommendations.md`.

### Breaking changes
- `scope.approved_activities` **removed**. Replaced by top-level `approved_activities` array
  (Rec 5 — flatten the `scope` wrapper, Option A).
- `trigger_condition` on control points **renamed** to `trigger` (Rec 10).
- `condition_hint` on control points **removed** — implementation detail, not a supervisory decision (Rec 6).
- `helper_skills` section **removed** — standard helpers are unconditionally included by the renderer (Rec 2).
- `schema_version` enum changed from `"2.0"` to `"2.1"`.

### Added
- `activation` field on control points (required, enum `conditional | step`) — makes the two
  activation models explicit: `conditional` fires when a trigger condition is detected at any
  workflow step; `step` fires when referenced by a specific workflow step via `control_point` (Rec 10).
- Conditional required fields on control points (Rec 11):
  - `classification: needs_approval | review | notify` → requires `who_reviews`
  - `classification: vetoed` → requires `escalation_contact`
- `activation: conditional` → requires `trigger` (Rec 10).
- Optional `artifacts` section to formalise the skill directory contract; enables artifact
  consistency validation (Rec 9).
- Artifact consistency validation pass in the validator (`_check_artifact_consistency`) (Rec 8):
  - Warns if `escalation_contact` in a control point is not found in `resources/escalation_contacts.md`
  - Warns if a regulation in `context.applicable_regulations` has no matching reference in `resources/regulations.md`
  - Errors if `workflow.steps[].uses_skill` references a shared skill that doesn't exist in `registry/`
  - Warns if `scripts/` contains unreferenced Python files
- Validator semantic check: `activation: step` control points must be referenced by at least one
  `workflow.steps[].control_point`; produces a warning if not (Rec 10).

### Changed
- `metadata.created_at`, `metadata.approved_at`, `metadata.approved_by` are now **optional**.
  They are lifecycle metadata managed by the approval pipeline, not required from authors.
  The wizard no longer emits them; the hub sets them on approval (Rec 3).
- `workflow.steps[].id` is now **optional**. When omitted, the step ID defaults to the
  activity ID. Override only needed when the same activity appears more than once (Rec 4).
- `control_points[].name` is now **optional**. When omitted, tooling derives a display name
  by converting the slug to title case (Rec 7).

### Removed
- `helper_skills` top-level section (Rec 2) — the standard helper skills
  (`shared/audit-logging`, `shared/checkpoint-gate`, `shared/validate-activity`) are now
  unconditionally included by the renderer.
- `control_points[].condition_hint` (Rec 6) — belongs in `scripts/` or code comments,
  not in the manager-authored supervisory document.

---

## v2.0 (2026-02-24)

### Breaking changes
- `hard_veto_triggers` and `oversight_checkpoints` **removed**. Replaced by a unified `control_points` array where each entry has a `classification` (`vetoed`, `needs_approval`, `review`, `notify`, `auto`).
- `scope.approved_activities` items changed from plain strings to objects with `id` (slug) and `description`.
- `workflow.steps[].activity` now references an activity `id` from `scope.approved_activities` instead of matching the full description string.
- `constraints.procedural_requirements` minimum items changed from 1 to 0. List may be empty when all constraints are expressed by workflow ordering, control points, or `unacceptable_actions`.
- `schema_version` enum changed from `"1.0"` / `"1.1"` to `"2.0"`.

### Added
- `control_points` array (required, min 1) — unified model for all human oversight, from unconditional halt (`vetoed`) to automatic pass-through (`auto`). Each control point has `id`, `name`, `description`, `classification`, and optional fields: `trigger_condition`, `condition_hint`, `who_reviews`, `escalation_contact`, `sla_hours`.
- `workflow.steps[].control_point` — references a control point `id` (without `trigger_condition`) to invoke after the step completes. Replaces the separate `veto_trigger` and `checkpoint` fields from v1.1.
- `SKILL.md` generation — `supv render` generates an Agent Skills compatible instruction document from `skill.yml`. CI validates that `SKILL.md` matches the current `skill.yml` in strict mode.

### Removed
- `hard_veto_triggers` block
- `oversight_checkpoints` block
- `workflow.steps[].veto_trigger`
- `workflow.steps[].checkpoint`

---

## v1.1 (2026-02-23)

### Added
- `workflow` block (required) — the ordered sequence of steps the agent must follow.
- `helper_skills` block (optional) — declares centrally-maintained helper skills from `registry/shared/`.
- `metadata.type` field (optional) — enum `standard | shared`.

---

## v1.0 (2024-01-01)

Initial release of the Agent Skill schema.

### Structure
- `metadata` — identity, versioning, supervisor ownership, authorised agents
- `context` — business description, rationale, regulations, risk classification
- `scope` — approved activities (exhaustive allowlist, plain string items)
- `constraints` — procedural requirements and unacceptable actions
- `hard_veto_triggers` — conditions that halt agent execution immediately
- `oversight_checkpoints` — workflow checkpoints and condition-triggered checkpoints

### Notes
- `schema_version` enum is hub-controlled; spoke teams cannot add values
- `authorised_agents: ["*"]` is permitted but triggers a CI warning
- All dates use ISO 8601 format (YYYY-MM-DD)
- Agent IDs should follow the convention `<function>-agent-<environment>`
