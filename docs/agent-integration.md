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
from supervisory_procedures.core.registry import SkillRegistry

# Load the registry (scans and validates all skills on first call)
registry = SkillRegistry()

# Fetch a skill — enforces all three access-control layers
skill = registry.get_skill(
    "retail_banking/loan-application-processing",
    agent_id="loan-processor-agent-prod",
)

# skill is a plain dict — use it to configure your agent
approved_activities = skill["scope"]["approved_activities"]
veto_triggers = skill["hard_veto_triggers"]
```

If the agent is not authorised, `PermissionError` is raised (specifically
`AgentNotAuthorisedError` or `SkillNotApprovedError`). Handle these to fail safely.

---

## Three-Layer Access Control

Every call to `get_skill(skill_id, agent_id=...)` enforces:

| Layer | Check | Error raised |
|---|---|---|
| 1 | Skill `status` must be `approved` | `SkillNotApprovedError` |
| 2 | `agent_id` must be in `authorised_agents` | `AgentNotAuthorisedError` |
| 3 | Skill must pass schema validation | Excluded from registry at load time |

Layer 3 means invalid skills are silently excluded from the cache and raise
`SkillNotFoundError` rather than a schema error — the skill effectively doesn't exist
from the agent's perspective.

---

## Checking Permissions Without Fetching

```python
from supervisory_procedures.core.access_control import AuthorisedAgentsGuard

guard = AuthorisedAgentsGuard(skill_data)
if guard.is_permitted("my-agent-prod"):
    # safe to proceed
    ...
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
from supervisory_procedures.adapters.generic_json import GenericJsonAdapter

json_str = GenericJsonAdapter().export(skill)
# Pass json_str to any framework that can consume JSON
```

---

## Listing Available Skills

```python
# All skills
skills = registry.list_skills()

# Filter by area
retail_skills = registry.list_skills(business_area="retail_banking")

# Filter by status
approved = registry.list_skills(status="approved")
```

---

## Error Reference

| Exception | When raised |
|---|---|
| `SkillNotFoundError` | Skill ID not in registry (not found or invalid schema) |
| `SkillNotApprovedError` | Skill is `draft` or `deprecated` |
| `AgentNotAuthorisedError` | `agent_id` not in `authorised_agents` |

All three inherit from `Exception` (`SkillNotApprovedError` and `AgentNotAuthorisedError` also inherit from `PermissionError`).
