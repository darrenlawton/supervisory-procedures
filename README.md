# Supervisory Procedures — Skill-as-Code Platform

**The people accountable for AI agents rarely control them. This tool changes that.**

AI agents are being deployed into production workflows across financial services, operations, and compliance. The people accountable for those workflows — business supervisors — have no direct way to control what agents are permitted to do.

Supervisory Procedures closes that gap. Business supervisors define **Agent Skills** in structured YAML: an exhaustive list of permitted actions, hard prohibitions, veto conditions that halt execution, and human oversight checkpoints. Skills are version-controlled in Git, reviewed via pull request, and loaded by agent runtimes at execution time.

The engineer builds the agent. The supervisor controls what it is allowed to do.

## Concept

An **Agent Skill** is a structured YAML document that answers four questions about an AI agent:

- What is it **approved to do?** — an exhaustive allowlist of permitted actions
- What must it **never do?** — absolute prohibitions enforced at registration
- When should it **stop immediately?** — hard veto triggers that halt execution and escalate
- Where does a **human decide?** — named checkpoints where review or approval is required before the agent continues

Skills are version-controlled in Git, approved via pull request, and loaded by agent runtimes at execution time. The organisation's central team owns the schema and tooling; each business area authors skills within that framework — without needing to write or deploy code.

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
