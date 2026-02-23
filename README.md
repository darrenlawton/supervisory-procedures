# Supervisory Procedures — Skill-as-Code Platform

**The people accountable for AI agents rarely control them. This tool changes that.**

Organisations adopting agentic AI face a structural problem: the central team that builds and deploys AI agents is not the same team that carries accountability for what those agents do. Business areas own the risk and outcomes — and they hold the domain expertise to define what safe, compliant agent behaviour looks like in their context. But they have had no mechanism to formally express, enforce, or evidence their oversight.

Supervisory Procedures is built to solve that. It gives business supervisors a structured way to exercise their oversight accountability — defining exactly what an AI agent is permitted to do in their area, what must never happen, and where a human must stay in the loop.

The central team owns the schema and tooling. Each business area authors and governs its own skills.

## What is an Agent Skill?

An **Agent Skill** is a structured YAML document — authored by a business supervisor, version-controlled in Git, and approved via pull request. It formally answers four questions about an AI agent operating in their area:

- What is it **approved to do?** — an exhaustive allowlist of permitted actions
- What must it **never do?** — absolute prohibitions
- When should it **stop immediately?** — hard veto triggers that halt execution and escalate
- Where does a **human decide?** — oversight checkpoints where approval is required before the agent continues

Authoring a skill is the supervisory act. It is how a business area formally takes accountability for an agent's behaviour — drawing on the domain knowledge, regulatory context, and operational expertise that only they hold.

## Getting Started

### For supervisors

Create a new skill for your business area using the guided wizard:

```bash
pip install supervisory-procedures
supv new
```

The wizard walks through every section of the skill definition — no YAML knowledge required. Once complete, the skill is saved to the registry and submitted for approval via pull request.

See the [Authoring Guide](docs/authoring-guide.md) for a full walkthrough.

### For developers

Install and load a skill at agent runtime:

```bash
pip install -e .
```

```python
from supervisory_procedures.core.registry import SkillRegistry

registry = SkillRegistry()
skill = registry.get_skill(
    "retail_banking/loan-application-processing",
    agent_id="loan-processor-agent-prod",
)
approved_activities = skill["scope"]["approved_activities"]
```

Only `approved` skills load. The agent ID must be in the skill's `authorised_agents` list. See the [Agent Integration Guide](docs/agent-integration.md).

## CLI Reference

```bash
supv new                                          # guided wizard — create a new skill
supv validate registry/                           # validate all skills
supv list                                         # list all skills
supv list --business-area retail_banking          # filter by business area
supv show retail_banking/loan-application-processing
```

## How your skill is enforced

When a developer loads a skill at runtime, three layers are checked automatically:

1. **Status gate** — only `approved` skills load; drafts and deprecated skills are blocked
2. **Allowlist gate** — the agent's ID must be in the skill's `authorised_agents` list
3. **Schema validity gate** — skills that fail schema validation are excluded from the registry

The supervisor's decisions — what the agent may do, who may run it, what triggers a halt — are enforced in code. The agent cannot bypass them.

## Documentation

- [Authoring Guide](docs/authoring-guide.md) — for business supervisors creating and maintaining skills
- [Schema Reference](docs/schema-reference.md) — field-by-field reference for the skill YAML format
- [Agent Integration](docs/agent-integration.md) — for developers loading skills at runtime
- [Hub-Spoke Governance](docs/hub-spoke-governance.md) — the governance model in detail

## License

MIT
