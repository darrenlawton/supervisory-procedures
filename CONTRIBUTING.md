# Contributing

## For Business Supervisors — Adding or Updating Skills

1. **Read the [Authoring Guide](docs/authoring-guide.md)** first
2. Use the wizard: `supv new`
3. Validate locally: `supv validate registry/<area>/<skill>.yml`
4. Open a PR using the provided template
5. Complete the supervisor sign-off checklist

If you are adding a skill to a **new business area**, contact the central innovation team first — they need to set up the CODEOWNERS entry and governance structure.

---

## For Hub Team — Tooling and Schema Changes

### Setup

```bash
git clone <repo-url>
cd supervisory-procedures
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
pytest --cov=supervisory_procedures --cov-report=term-missing
```

### Linting

```bash
ruff check .
ruff format .
```

### Type Checking

```bash
mypy supervisory_procedures/
```

### Schema Changes

Any change to `schema/skill.schema.json` must:
1. Be backwards-compatible (additive) for the current schema version, OR
2. Introduce a new `schema_version` enum value with a migration guide
3. Update `schema/CHANGELOG.md`
4. Pass all existing tests

---

## Branch and PR Guidelines

- Branch from `main`: `git checkout -b feat/your-change`
- Keep PRs focused — one skill or one change at a time
- CI must pass before merge
- Hub team does final merge to `main`
