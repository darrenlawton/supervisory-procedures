# Skill Registry

This directory is the Git-controlled registry of all authorised Agent Skills.

## Structure

```
registry/
├── <business_area>/
│   ├── README.md          # Business area owners and skill index
│   └── <skill-name>.yml   # Individual skill definitions
```

Each business area directory is owned by the corresponding spoke team (see [CODEOWNERS](../CODEOWNERS)).
No skill may be merged without:
1. Passing schema validation (`supv validate registry/ --strict`)
2. Review and approval from the business area CODEOWNER
3. Final merge by the central innovation hub team

## Adding a Business Area

1. Create a new directory: `registry/<business_area>/`
2. Add a `README.md` listing the skill owners
3. Update `CODEOWNERS` with `@org/<team-name>` for the new directory
4. Submit a PR — hub team will review the governance setup before approving
