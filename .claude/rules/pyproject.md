---
paths:
  - "pyproject.toml"
---

- Runtime dependencies go under `[project] dependencies`
- Dev dependencies go under `[dependency-groups] dev`; docs under `[dependency-groups] docs`
- Before adding a dependency: verify active maintenance, compatible license (MIT/BSD/Apache), and minimal transitive dependencies
- Use version ranges (`>=X.Y`) for runtime dependencies -- never pin exact versions in a library
- NEVER remove existing ruff rules without explicit user approval
- NEVER lower the coverage threshold (currently 80%)
- GUI/platform-specific modules that require a macOS run loop may be omitted from coverage via `[tool.coverage.run] omit`
- Every coverage omission MUST have a comment explaining why the code cannot be tested
- Omitted modules MUST delegate business logic to testable modules — the omitted file should only contain framework glue
- NEVER omit a module just because testing is inconvenient; only omit when testing is genuinely impossible in the test environment
- After modifying dependencies, run `uv sync --all-groups`
- The `uv.lock` file MUST be committed alongside dependency changes
