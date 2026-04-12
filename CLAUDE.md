# CLAUDE.md

This file provides guidance for AI assistants (Claude Code and similar tools) working in this repository.

## Repository Overview

**Status:** Newly initialized — no application code has been added yet.

- **Remote:** `takooo66/a1` on GitHub
- **Default branch:** `main`
- **Initialized:** 2026-03-27

The repository currently contains only a `.gitkeep` file. When a project is scaffolded into this repo, update this document to reflect the actual tech stack, conventions, and workflows.

---

## Git Workflow

### Branch Naming

Feature and task branches follow the pattern:

```
<actor>/<short-description>-<id>
```

Examples:
- `claude/add-claude-documentation-3HEI0`
- `feature/user-auth`
- `fix/login-redirect`

### Development Branch

When working on assigned tasks, develop on the designated branch (provided per session). Never push directly to `main` without explicit permission.

### Commit Messages

Write concise, imperative commit messages:

```
Add user authentication flow
Fix null pointer in profile loader
Refactor database connection pooling
```

Avoid vague messages like "fix stuff" or "wip".

### Push Procedure

```bash
git push -u origin <branch-name>
```

If the push fails due to a network error, retry up to 4 times with exponential backoff (2s, 4s, 8s, 16s).

### Pull Requests

Do **not** create a pull request unless the user explicitly requests one.

---

## Working in This Repository

### Before Making Changes

1. Read the relevant files before editing them.
2. Understand existing code before suggesting or applying modifications.
3. Prefer editing existing files over creating new ones.

### Code Quality

- Do not add features, refactors, or "improvements" beyond what was asked.
- Do not add comments or docstrings to code you didn't change.
- Do not introduce error handling for scenarios that cannot happen.
- Do not add backwards-compatibility shims for removed code.

### Security

Never introduce:
- Command injection vulnerabilities
- SQL injection
- XSS
- Hardcoded secrets or credentials in source files

Validate input only at system boundaries (user input, external APIs). Trust internal framework guarantees.

### Reversibility

Before taking destructive or hard-to-reverse actions (deleting files, force-pushing, resetting history, modifying shared infrastructure), confirm with the user first.

---

## Placeholder: Tech Stack

> **Update this section once a tech stack is chosen.**

When the project is set up, document here:

- **Language(s):** e.g., TypeScript, Python, Go
- **Framework(s):** e.g., Next.js, FastAPI, Gin
- **Package manager:** e.g., npm, pnpm, uv, go mod
- **Test runner:** e.g., Vitest, pytest, go test
- **Linter / formatter:** e.g., ESLint + Prettier, Ruff, gofmt

---

## Placeholder: Development Commands

> **Update this section once a build system is configured.**

Common commands to document here:

```bash
# Install dependencies
<install command>

# Run development server
<dev command>

# Run tests
<test command>

# Lint / format
<lint command>

# Build for production
<build command>
```

---

## Placeholder: Environment Variables

> **Update this section once environment configuration is established.**

Document required environment variables and provide a reference to `.env.example` if one exists.

---

## Updating This File

Whenever significant changes are made to the project (new tech stack, new CI pipeline, updated conventions, etc.), update this CLAUDE.md to keep it accurate. Stale documentation is worse than no documentation.
