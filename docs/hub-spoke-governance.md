# Hub-and-Spoke Governance Model

How the central innovation hub and business area spoke teams collaborate to govern Agent Skills.

---

## Roles

### Hub — Central Innovation Team (`@org/central-innovation-team`)

The hub team owns:
- The JSON Schema (`schema/`) — they control which schema versions are valid
- The tooling (`supervisory_procedures/`) — CLI, validators, registry, renderer
- The CI pipeline (`.github/`) — blocks merges on validation failure
- The overall governance framework

The hub team does not author skills for spoke areas. Their role is to:
1. Maintain the schema and tooling
2. Review PRs for structural correctness
3. Perform the final merge to `main`

### Spoke — Business Area Teams

Each business area has a supervisor team (e.g. `@org/retail-banking-supervisors`) that:
1. Authors skill definitions for their area
2. Reviews skill PRs from their colleagues
3. Signs off on the content as business owners

Spoke teams have write access only to their own `registry/<business_area>/` directory.

---

## CODEOWNERS Enforcement

```
# Hub owns schema, tooling, CI
/schema/                    @org/central-innovation-team
/supervisory_procedures/    @org/central-innovation-team
/.github/                   @org/central-innovation-team

# Spokes own only their registry directory
/registry/retail_banking/   @org/retail-banking-supervisors
```

Branch protection rules on `main`:
- Require at least one CODEOWNER review
- Require the `validate-skills` CI check to pass
- No direct pushes (even hub team uses PRs)

This means a spoke team can author and review a skill within their directory, but **cannot self-approve** — the hub team must do the final merge.

---

## PR Lifecycle

```
Supervisor authors skill.yml
        ↓
supv new  (or manual YAML edit)
        ↓
supv render <area>/<skill-name>   (generate SKILL.md from skill.yml)
        ↓
supv validate registry/ --strict  (local check — fails if SKILL.md is stale)
        ↓
git add registry/<area>/<skill-name>/   (commit skill.yml + SKILL.md together)
git commit + push + open PR
        ↓
CI: supv validate registry/ --strict   (automated — blocks merge on any failure)
        ↓
Spoke CODEOWNER reviews content  (business sign-off)
        ↓
Hub CODEOWNER reviews structure  (schema/tooling compliance)
        ↓
Hub merges to main
        ↓
Skill is live (agents can load it)
```

---

## The skill.yml / SKILL.md relationship

`skill.yml` is the source of truth. `SKILL.md` is generated from it by `supv render` and is what the agent reads at runtime.

**Both files must be committed together.** The CI pipeline runs `supv validate --strict`, which checks that `SKILL.md` exactly matches a fresh render of `skill.yml`. A PR that updates `skill.yml` without regenerating `SKILL.md` will fail CI.

This ensures there is never a gap between the governed definition and the agent's instructions.

---

## Adding a New Business Area

1. Create `registry/<business_area>/README.md` listing owners, governance notes, and skill index
2. Add a CODEOWNERS entry: `/registry/<business_area>/   @org/<team-name>`
3. Submit a PR — hub team reviews the governance setup
4. Once merged, the spoke team can start authoring skills

---

## Schema Version Upgrades

Schema version changes are hub-controlled. The process:
1. Hub drafts the new schema version and `schema/CHANGELOG.md` entry
2. Hub runs a migration check across all registry skills
3. Hub opens a PR with the updated `schema/skill.schema.json`
4. After merge, spoke teams update `schema_version` in their skills and re-run `supv render`
5. Both old and new schema versions may be supported during a transition period
