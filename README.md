# Supervisory Procedures — Skill-as-Code Framework

**The people accountable for AI agents rarely control them. This tool changes that.**

Organisations adopting agentic AI face a structural problem: the central team that builds and deploys AI agents is not the same team that carries accountability for what those agents do. Business areas own the risk and outcomes — and they hold the domain expertise to define what safe, compliant agent behaviour looks like in their context. But they have had no mechanism to formally express, enforce, or evidence their oversight.

Supervisory Procedures is built to solve that. It gives business supervisors a structured way to exercise their oversight accountability — defining exactly what an AI agent is permitted to do in their area, what must never happen, and where a human must stay in the loop.

The central team owns the schema and tooling. Each business area authors and governs its own skills.

## What is an [Agent Skill](https://www.youtube.com/watch?v=CEvIs9y1uog)?

An **Agent Skill** is a structured YAML document — authored by a business supervisor, version-controlled in Git, and approved via pull request. It formally answers five questions about an AI agent operating in their area:

- What is it **approved to do?** — an exhaustive allowlist of permitted activities
- What must it **never do?** — absolute prohibitions
- How should it **execute the task?** — an ordered workflow sequence, each step mapped to a permitted activity
- Where does a **human stay in the loop?** — control points that classify the level of human involvement required: automatic, notify, review, needs approval, or unconditional halt
- Who is **authorised to run it?** — the specific agent IDs permitted to load and execute this skill

Authoring a skill is the supervisory act. It is how a business area formally takes accountability for an agent's behaviour.

## How it works

```
skill.yml  ──[supv render]──►  SKILL.md (Claude Agent Skills format)
    │                               │
    │  schema-validated              │  agent reads at runtime
    │  supervisor-governed           │  supervisor's procedure enforced as instructions
    └── single source of truth      └── never edited by hand
```

`skill.yml` is the governed definition — authored by the supervisor, schema-validated, approved via PR. `SKILL.md` is generated from it in [Claude Agent Skills](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview) format, embedding the supervisor's approved activities, control points, and workflow directly into the agent's instruction document. The agent cannot deviate from the procedure because it is structural, not advisory.

## Getting Started

### For supervisors

Create a new skill for your business area using the guided wizard:

```bash
pip install supervisory-procedures
supv new
```

The wizard walks through every section of the skill definition in plain English. Once complete, generate the agent instruction document and validate:

```bash
supv render <business_area>/<skill-name>
supv validate registry/ --strict
```

See the [Authoring Guide](docs/authoring-guide.md) for a full walkthrough.

### For developers

Install and load a skill at agent runtime:

```bash
pip install -e .
```

```python
from pathlib import Path
from supervisory_procedures.core.registry import SkillRegistry
from supervisory_procedures.core.access_control import (
    AgentNotAuthorisedError,
    SkillNotApprovedError,
    SkillNotFoundError,
)

registry = SkillRegistry()

try:
    skill = registry.get_skill(
        "retail_banking/loan-application-processing",
        agent_id="loan-processor-agent-prod",
    )
except SkillNotFoundError:
    ...  # skill does not exist or failed schema validation
except SkillNotApprovedError:
    ...  # skill is draft or deprecated
except AgentNotAuthorisedError:
    ...  # agent not on the allowlist

# Read the generated SKILL.md as the agent's system prompt
skill_md = Path(skill["_skill_dir"]) / "SKILL.md"
instructions = skill_md.read_text()
```

Only `approved` skills load. The agent ID must be in the skill's `authorised_agents` list. See the [Agent Integration Guide](docs/agent-integration.md).

## CLI Reference

```bash
supv new                                          # guided wizard — create a new skill
supv render <business_area>/<skill-name>          # generate SKILL.md from skill.yml
supv validate registry/                           # validate all skills
supv validate registry/ --strict                  # treat warnings as errors
supv list                                         # list all skills
supv list --business-area retail_banking          # filter by business area
supv show retail_banking/loan-application-processing
supv export retail_banking/loan-application-processing
```

## How your skill is enforced

**At authoring time:**
- `supv validate` checks `skill.yml` against the JSON Schema and warns if any `workflow.steps[].activity` references an ID not in `scope.approved_activities`
- `supv validate --strict` also fails if `SKILL.md` is missing or stale

**At load time**, three layers are checked automatically when an agent calls `get_skill()`:

1. **Status gate** — only `approved` skills load; drafts and deprecated skills are blocked
2. **Allowlist gate** — the agent's ID must be in the skill's `authorised_agents` list
3. **Schema validity gate** — skills that fail schema validation are excluded from the registry at load time

**At runtime**, the generated `SKILL.md` instructs the agent to:
- Validate every step against the approved workflow before executing (`validate_activity.py`)
- Invoke the appropriate control point gate at designated steps (`checkpoint_gate.py`)
- Write an audit trail entry for every action (`audit_log.py`)

The supervisor's decisions — what the agent may do, who may run it, what triggers a halt — are enforced in code. The agent cannot bypass them.

## Skill directory structure

Each skill lives in its own directory:

```
registry/
└── retail_banking/
    └── loan-application-processing/
        ├── skill.yml        ← governed definition (source of truth, never edit manually)
        ├── SKILL.md         ← generated agent instructions (never edit manually)
        ├── scripts/         ← supporting scripts
        └── resources/       ← regulations, escalation contacts
```

## Documentation

- [Authoring Guide](docs/authoring-guide.md) — for business supervisors creating and maintaining skills
- [Schema Reference](docs/schema-reference.md) — field-by-field reference for the skill YAML format
- [Agent Integration](docs/agent-integration.md) — for developers loading skills at runtime
- [Hub-Spoke Governance](docs/hub-spoke-governance.md) — the governance model in detail

## License

MIT
