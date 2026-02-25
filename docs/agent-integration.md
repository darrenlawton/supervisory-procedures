# Agent Integration Guide

How to consume Supervisory Procedures skills in your AI agent code.

---

## Installation

```bash
pip install supervisory-procedures
# or in your requirements.txt / pyproject.toml dependencies
```

---

## Basic Usage

```python
from pathlib import Path
from supervisory_procedures.core.registry import SkillRegistry
from supervisory_procedures.core.access_control import (
    AgentNotAuthorisedError,
    SkillNotApprovedError,
    SkillNotFoundError,
)

# Load the registry (scans and validates all skills on first call)
registry = SkillRegistry()

# Fetch a skill — enforces all three access-control layers
try:
    skill = registry.get_skill(
        "retail_banking/loan-application-processing",
        agent_id="loan-processor-agent-prod",
    )
except SkillNotFoundError:
    ...  # skill does not exist or failed schema validation
except SkillNotApprovedError as exc:
    ...  # skill.status is 'draft' or 'deprecated'
except AgentNotAuthorisedError:
    ...  # agent_id not in authorised_agents

# Read the generated SKILL.md as the agent's system prompt
skill_md = Path(skill["_skill_dir"]) / "SKILL.md"
instructions = skill_md.read_text()
```

---

## Three-Layer Access Control

Every call to `get_skill(skill_id, agent_id=...)` enforces:

| Layer | Check | Error raised |
|---|---|---|
| 1 | Skill `status` must be `approved` | `SkillNotApprovedError` |
| 2 | `agent_id` must be in `authorised_agents` | `AgentNotAuthorisedError` |
| 3 | Skill must pass schema validation | Excluded from registry at load time — raises `SkillNotFoundError` |

Layer 3 means invalid skills are silently excluded from the cache at load time. From the agent's perspective, they do not exist.

---

## Reading the Agent Instructions (SKILL.md)

`skill["_skill_dir"]` is the path to the skill's directory. `SKILL.md` inside that directory is the Agent Skills compatible instruction document generated from `skill.yml`.

It contains the supervisor's approved activities, ordered workflow, control points, and unacceptable actions, formatted as concrete agent instructions with embedded bash commands for all runtime enforcement scripts.

Pass it as the agent's system prompt:

```python
from pathlib import Path
import anthropic

skill_dir = Path(skill["_skill_dir"])
instructions = (skill_dir / "SKILL.md").read_text()

client = anthropic.Anthropic()
response = client.messages.create(
    model="claude-opus-4-6",
    max_tokens=4096,
    system=instructions,
    messages=[{"role": "user", "content": task}],
)
```

See `examples/load_skill_in_agent.py` for a complete working example.

---

## Checking Permissions Without Fetching

Use `is_permitted()` to check access without raising an exception:

```python
from supervisory_procedures.core.access_control import is_permitted

if is_permitted(skill_data, "my-agent-prod"):
    # safe to proceed
    ...
```

Or use `check_access()` to raise on failure:

```python
from supervisory_procedures.core.access_control import check_access

check_access(skill_data, "my-agent-prod")  # raises PermissionError if not permitted
```

---

## Using a Custom Registry Path

For testing, CI, or non-standard deployments:

```python
registry = SkillRegistry(registry_path="/path/to/your/registry")
```

---

## Exporting to JSON

```python
import json

skill = registry.get_skill("retail_banking/loan-application-processing")
skill_id = skill.get("metadata", {}).get("id", "unknown")

envelope = {
    "export_format": "supervisory-skill-v1",
    "skill_id": skill_id,
    "skill": skill,
}
json_str = json.dumps(envelope, indent=2, ensure_ascii=False, default=str)
```

Or via the CLI:

```bash
supv export retail_banking/loan-application-processing
```

---

## Listing Available Skills

```python
# All skills
skills = registry.list_skills()

# Filter by business area
retail_skills = registry.list_skills(business_area="retail_banking")

# Filter by status
approved = registry.list_skills(status="approved")

# Each result is a metadata dict with risk_classification merged in
for s in skills:
    print(s["id"], s["status"], s["risk_classification"])
```

---

## Error Reference

| Exception | When raised | Inherits from |
|---|---|---|
| `SkillNotFoundError` | Skill ID not in registry (not found or invalid schema) | `Exception` |
| `SkillNotApprovedError` | Skill is `draft` or `deprecated` | `PermissionError` |
| `AgentNotAuthorisedError` | `agent_id` not in `authorised_agents` | `PermissionError` |

All three are importable from `supervisory_procedures.core.access_control`.
