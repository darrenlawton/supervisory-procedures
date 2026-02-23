# Schema Changelog

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
