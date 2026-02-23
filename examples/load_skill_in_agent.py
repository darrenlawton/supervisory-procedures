"""Minimal example: load and use a skill in an agent.

Run from the project root after installing the package:
    pip install -e .
    python examples/load_skill_in_agent.py
"""

from supervisory_procedures.core.registry import SkillRegistry
from supervisory_procedures.core.access_control import (
    AgentNotAuthorisedError,
    SkillNotApprovedError,
    SkillNotFoundError,
)


def main():
    # Initialise the registry (defaults to the /registry directory)
    registry = SkillRegistry()

    agent_id = "loan-processor-agent-prod"
    skill_id = "retail_banking/loan-application-processing"

    print(f"Loading skill '{skill_id}' for agent '{agent_id}'...")

    try:
        skill = registry.get_skill(skill_id, agent_id=agent_id)
    except SkillNotFoundError:
        print(f"  ERROR: Skill '{skill_id}' not found in registry.")
        return
    except SkillNotApprovedError as exc:
        print(f"  BLOCKED: Skill is not approved (status: {exc.status}).")
        return
    except AgentNotAuthorisedError:
        print(f"  BLOCKED: Agent '{agent_id}' is not authorised for this skill.")
        return

    meta = skill["metadata"]
    ctx = skill["context"]
    scope = skill["scope"]

    print(f"\n  Skill loaded: {meta['name']} v{meta['version']}")
    print(f"  Risk:         {ctx['risk_classification']}")
    print(f"  Approved by:  {meta.get('approved_by', 'n/a')} on {meta.get('approved_at', 'n/a')}")

    print("\n  Approved activities:")
    for activity in scope["approved_activities"]:
        print(f"    ✓ {activity}")

    veto_triggers = skill["hard_veto_triggers"]
    print(f"\n  Hard veto triggers ({len(veto_triggers)}):")
    for veto in veto_triggers:
        print(f"    ⚠  [{veto['action']}] {veto['id']}: {veto['description'][:60]}...")

    print("\n  Agent is ready to operate within the defined constraints.")


if __name__ == "__main__":
    main()
