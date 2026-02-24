# Schema Changelog

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
- `SKILL.md` generation — `supv render` generates a Claude Agent Skills compatible instruction document from `skill.yml`. CI validates that `SKILL.md` matches the current `skill.yml` in strict mode.

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
