# AGENTS.md - AI Agent Development Guidelines

**CRITICAL**: Mandatory rules for AI agents. Non-compliance will result in
rejected code.

---

## Critical Rules

## Rule 0: Use the Agent Harness Tools

Use `agent_harness` for all agent interactions

### Rule 1: File Extensions

- Use `.yaml` for ALL YAML files (NOT `.yml`)
- Use `.md` for ALL Markdown files (NOT `.MD`, `.markdown`)
- Use `.rs` for ALL Rust files

CI/CD pipelines expect `.yaml`. Using `.yml` causes build failures.

### Rule 2: Markdown File Naming

- Use `lowercase_with_underscores.md` for all documentation files
- `README.md`, `LICENSE.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`,
  `AGENTS.md`, and `CHANGELOG.md` are the ONLY exception to the lowercase rule
- Never use CamelCase, kebab-case, spaces, or uppercase

Inconsistent naming breaks documentation links.

### Rule 3: No Emojis

- No emojis in code, comments, documentation, or commit messages
- Exception: This AGENTS.md file only

Emojis cause encoding issues and break tooling.

### Rule 4: Quality Gates (ALL Must Pass)

Run in this order before claiming any task complete:

```bash
markdownlint --fix --config .markdownlint.json "${FILE}"
prettier --write --parser markdown --prose-wrap always "${FILE}"
```

Stop immediately and fix if any command fails.

### Rule 5: Documentation is Mandatory

- Never skip documentation because "code is self-documenting"

### Rule 6: Use the Agent Harness Tools

Do not write custom scripts for tasks that can be accomplished with the agent
tools.

---

## Git Conventions

Do not run git commands. The user handles all git interactions.

---

## Living Document

This file is updated as new patterns emerge.
