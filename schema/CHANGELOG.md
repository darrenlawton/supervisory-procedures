# Schema Changelog

## v1.1 (2026-02-23)

### Added
- `workflow` block (required) — the ordered sequence of steps the agent must follow. Each step maps 1:1 to an entry in `scope.approved_activities` and may reference a `veto_trigger`, `checkpoint`, or `uses_skill` by ID.
- `helper_skills` block (optional) — declares centrally-maintained helper skills from `registry/shared/` that this skill delegates to in its workflow.
- `metadata.type` field (optional) — enum `standard | shared`. Set to `shared` for centrally-maintained helper skills in `registry/shared/`.
- `schema_version` enum extended to include `"1.1"`.

### Notes
- `workflow.steps[].activity` must match an entry in `scope.approved_activities` exactly (validated at runtime by the registry; not enforced by JSON Schema due to cross-field reference limits).
- `workflow.steps[].veto_trigger` and `workflow.steps[].checkpoint` must match IDs in `hard_veto_triggers` and `oversight_checkpoints` respectively.
- `helper_skills[].id` and `workflow.steps[].uses_skill` must use the `shared/<slug>` pattern — only skills in `registry/shared/` may be referenced.
- Helper skills in `registry/shared/` should only be created where genuine reuse exists across two or more business area skills.

---

## v1.0 (2024-01-01)

Initial release of the Agent Skill schema.

### Structure
- `metadata` — identity, versioning, supervisor ownership, authorised agents
- `context` — business description, rationale, regulations, risk classification
- `scope` — approved activities (exhaustive allowlist)
- `constraints` — procedural requirements and unacceptable actions
- `hard_veto_triggers` — conditions that halt agent execution immediately
- `oversight_checkpoints` — workflow checkpoints and condition-triggered checkpoints

### Notes
- `schema_version` enum is hub-controlled; spoke teams cannot add values
- `authorised_agents: ["*"]` is permitted but triggers a CI warning
- All dates use ISO 8601 format (YYYY-MM-DD)
- Agent IDs should follow the convention `<function>-agent-<environment>`
