# Shared — Centrally-Maintained Helper Skills

This directory contains Agent Skills maintained by the central innovation team for reuse across business areas.

## Governance

Shared skills are owned exclusively by `@org/central-innovation-team`. No business area team may add or modify skills here directly — changes require a pull request reviewed by the hub.

## When to create a shared skill

A skill belongs here only when **genuine reuse exists across two or more business area skills**. Do not create a shared skill speculatively or for a capability used by a single team. If reuse emerges later, a skill can be promoted from a business area registry to shared at that point.

## Skill package structure

Each shared skill is a directory containing:

```
shared/<skill-id>/
  SKILL.md               # Agent-readable runbook (progressive disclosure, levels 1–2)
  skill.yml              # Governance definition (schema v2.0) — present for enforcement skills
  scripts/               # Executable enforcement scripts (optional)
  resources/             # Reference materials (optional)
```

Pure advisory skills (e.g. explain-code) contain only a `SKILL.md`. Enforcement skills that the agent invokes via bash (e.g. checkpoint-gate, audit-logging) also include a `skill.yml` and `scripts/`.

## How to use a shared skill

Reference a shared skill in your business area skill's `helper_skills` block:

```yaml
helper_skills:
  - id: shared/checkpoint-gate
    purpose: "Enforces supervisory control points at runtime."
    required: true
```

Then invoke the shared scripts directly in your `SKILL.md` workflow steps:

```bash
python registry/shared/checkpoint-gate/scripts/checkpoint_gate.py \
  --skill <your-skill-id> \
  --session ${CLAUDE_SESSION_ID} \
  --control-point <control-point-id> \
  --classification <auto|notify|review|needs_approval|vetoed> \
  [--reviewer "..."] [--contact ...] [--sla-hours N]
```

## Skills

### Enforcement skills (schema v2.0, with skill.yml + scripts)

| Skill ID | Purpose | Used by |
|---|---|---|
| `shared/audit-logging` | Append-only JSON-lines audit trail writer | All supervisory skills |
| `shared/checkpoint-gate` | Enforces control point classifications at runtime (auto/notify/review/needs_approval/vetoed) | All supervisory skills |
| `shared/validate-activity` | Checks proposed actions against a skill's approved_activities allowlist | All supervisory skills |

### Example / advisory skills (SKILL.md only — no skill.yml)

These skills are provided as working examples from the agent skills library.
They demonstrate the SKILL.md progressive-disclosure format and can be used directly
or adapted for your own workflows.

| Skill ID | Purpose |
|---|---|
| `shared/explain-code` | Explains a codebase section using analogies, diagrams, and step-by-step walkthrough |
| `shared/codebase-visualizer` | Generates a self-contained HTML codebase map from a directory tree |

## Adding a new shared skill

1. Confirm that ≥2 existing business area skills need the same capability
2. Create a directory at `registry/shared/<skill-id>/` with at minimum a `SKILL.md`
3. Add a `skill.yml` (schema v2.0) if the skill has governance or enforcement requirements
4. Update the tables above
5. Open a PR — the central team will review and merge
