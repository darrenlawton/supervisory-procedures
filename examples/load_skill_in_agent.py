"""Example: load a supervised skill and run an agent session with it.

This example shows the full path from supervisor-governed skill definition
to a running agent session:

  1. SkillRegistry enforces access control (status, agent allowlist, schema validity)
  2. SKILL.md — generated from skill.yml — becomes the agent's system prompt,
     embedding the supervisor's approved activities, control points, and workflow
     directly into the agent's instructions
  3. The agent operates within the constraints defined by the supervisor;
     it cannot deviate from the procedure or access anything outside scope

Run from the project root:
    pip install -e .
    python examples/load_skill_in_agent.py
"""

from __future__ import annotations

from pathlib import Path

import anthropic

from supervisory_procedures.core.registry import SkillRegistry
from supervisory_procedures.core.access_control import (
    AgentNotAuthorisedError,
    SkillNotApprovedError,
    SkillNotFoundError,
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SKILL_ID = "retail_banking/loan-application-processing"
AGENT_ID = "loan-processor-agent-prod"

# ---------------------------------------------------------------------------
# Step 1 — Load the skill with access control enforcement
# ---------------------------------------------------------------------------

def load_skill(skill_id: str, agent_id: str) -> dict:
    """Load a skill from the registry, enforcing all three access-control layers.

    Layer 1 — Status gate:   only approved skills load.
    Layer 2 — Allowlist gate: agent_id must be in authorised_agents.
    Layer 3 — Schema gate:   invalid skills are excluded at registry load time.
    """
    registry = SkillRegistry()

    try:
        return registry.get_skill(skill_id, agent_id=agent_id)
    except SkillNotFoundError:
        raise SystemExit(f"ERROR: Skill '{skill_id}' not found in registry.")
    except SkillNotApprovedError as exc:
        raise SystemExit(
            f"BLOCKED: Skill '{skill_id}' has status '{exc.status}'. "
            "Only approved skills may be loaded by agents."
        )
    except AgentNotAuthorisedError:
        raise SystemExit(
            f"BLOCKED: Agent '{agent_id}' is not on the authorised_agents list "
            f"for '{skill_id}'."
        )


# ---------------------------------------------------------------------------
# Step 2 — Read the generated SKILL.md as the agent's instruction document
# ---------------------------------------------------------------------------

def read_skill_instructions(skill_data: dict) -> str:
    """Return the contents of SKILL.md — the agent's runtime instruction document.

    SKILL.md is generated from skill.yml by `supv render` and contains the
    supervisor's approved activities, workflow, control points, and constraints
    formatted as Claude Agent Skills compatible instructions.
    """
    skill_dir = Path(skill_data["_skill_dir"])
    skill_md = skill_dir / "SKILL.md"

    if not skill_md.exists():
        skill_id = skill_data["metadata"]["id"]
        raise FileNotFoundError(
            f"SKILL.md not found at {skill_md}. "
            f"Run `supv render {skill_id}` to generate it."
        )

    return skill_md.read_text()


# ---------------------------------------------------------------------------
# Step 3 — Run an agent session with the skill loaded
# ---------------------------------------------------------------------------

def run_agent_session(skill_data: dict, task: str) -> None:
    """Start an agent session using SKILL.md as the system prompt.

    The supervisor's procedure is embedded directly in the agent's instructions.
    The agent operates within the defined scope and cannot deviate from the
    workflow, approved activities, or control point requirements.
    """
    meta = skill_data["metadata"]
    ctx = skill_data["context"]
    control_points = skill_data["control_points"]
    workflow_steps = skill_data["workflow"]["steps"]

    # Print a summary of what the agent has been cleared to do
    print(f"Skill:        {meta['name']} v{meta['version']}")
    print(f"Supervisor:   {meta['supervisor']['name']} ({meta['supervisor']['role']})")
    print(f"Risk:         {ctx['risk_classification']}")
    print(f"Approved by:  {meta.get('approved_by', 'n/a')} on {meta.get('approved_at', 'n/a')}")

    print(f"\nControl points ({len(control_points)}):")
    for cp in control_points:
        print(f"  [{cp['classification']:15s}] {cp['id']}")

    print(f"\nWorkflow ({len(workflow_steps)} steps):")
    for step in workflow_steps:
        cp_ref = f"  → {step['control_point']}" if step.get("control_point") else ""
        print(f"  {step['id']}{cp_ref}")

    # SKILL.md becomes the system prompt — the supervisor's procedure is enforced
    # from the first token of the agent's response
    instructions = read_skill_instructions(skill_data)

    print(f"\nRunning agent session for task:\n  {task}\n")
    print("-" * 60)

    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=4096,
        system=instructions,
        messages=[{"role": "user", "content": task}],
    )

    print(response.content[0].text)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print(f"Loading skill '{SKILL_ID}' for agent '{AGENT_ID}'...\n")

    skill_data = load_skill(SKILL_ID, AGENT_ID)
    run_agent_session(
        skill_data,
        task=(
            "Process loan application APP-2025-00142 for John Smith, "
            "DOB 1985-03-14. Income documents and ID have been submitted."
        ),
    )
