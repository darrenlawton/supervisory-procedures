# Shared — Centrally-Maintained Helper Skills

This directory contains Agent Skills maintained by the central innovation team for reuse across business areas.

## Governance

Shared skills are owned exclusively by `@org/central-innovation-team`. No business area team may add or modify skills here directly — changes require a pull request reviewed by the hub.

## When to create a shared skill

A skill belongs here only when **genuine reuse exists across two or more business area skills**. Do not create a shared skill speculatively or for a capability used by a single team. If reuse emerges later, a skill can be promoted from a business area registry to shared at that point.

## How to use a shared skill

Reference a shared skill in your business area skill's `helper_skills` block and `workflow.steps[].uses_skill` field:

```yaml
helper_skills:
  - id: shared/your-helper-skill
    purpose: "Why this skill is used in this workflow."
    required: true

workflow:
  steps:
    - id: your-step
      activity: "The approved activity this step performs"
      uses_skill: shared/your-helper-skill
```

The `uses_skill` value must match the `metadata.id` of a skill in this directory.

## Skills

| Skill ID | Name | Status | Reused by |
|---|---|---|---|
| *(none yet)* | | | |

## Adding a new shared skill

1. Confirm that ≥2 existing business area skills need the same capability
2. Open a PR adding the skill YAML to this directory
3. Update the table above
4. The central team will review and merge
