# Supervisory Procedures — Skill-as-Code Platform

A governance platform for federated AI development. Business supervisors define, version-control, and govern what AI agents are authorised to do within their areas.

## Concept

Large organisations with multiple AI development teams (spokes) need a way for non-technical business supervisors to control agent behaviour without writing code. **Agent Skills** are structured YAML definitions that declare:

- What an agent is **approved to do** (an exhaustive allowlist)
- What it must **never do** (absolute prohibitions)
- **Hard veto triggers** that immediately halt execution
- **Oversight checkpoints** where a human must review or approve

Skills are version-controlled in Git, approved via pull request, and consumed by agent runtimes at execution time. The central innovation team (hub) owns the schema and tooling; business areas (spokes) author skills within that framework.

## Quick Start

```bash
pip install -e .

# Create a new skill interactively
supv new

# Validate all skills in the registry
supv validate registry/

# List skills
supv list
supv list --business-area retail_banking

# Show a specific skill
supv show retail_banking/loan-application-processing

# Export to NeMo Guardrails
supv export retail_banking/loan-application-processing --format nemo
```

## Project Structure

```
schema/              JSON Schema — the authoritative definition of a skill
registry/            Git-controlled skill registry (one dir per business area)
supervisory_procedures/   Python package (CLI, core, adapters)
tests/               Test suite
docs/                Documentation
examples/            Agent integration examples
```

## Documentation

- [Authoring Guide](docs/authoring-guide.md) — for business supervisors
- [Schema Reference](docs/schema-reference.md) — field-by-field reference
- [Agent Integration](docs/agent-integration.md) — for agent developers
- [Hub-Spoke Governance](docs/hub-spoke-governance.md) — governance model

## Access Control

Three layers enforced at runtime:

1. **Status gate** — only `approved` skills load
2. **Allowlist gate** — agent ID must be in `authorised_agents`
3. **Schema validity gate** — invalid skills are excluded from the registry cache

```python
from supervisory_procedures.core.registry import SkillRegistry

registry = SkillRegistry()
skill = registry.get_skill(
    "retail_banking/loan-application-processing",
    agent_id="loan-processor-agent-prod",
)
```

## License

MIT
