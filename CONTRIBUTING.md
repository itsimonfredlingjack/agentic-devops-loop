# Contributing to SEJFA

## Code Structure

This repository follows a modular structure to separate core logic, integrations, and agent utilities.

### `src/sejfa/core/`
Place business logic, data models, and core services here.
Examples: Authentication, Subscriber management, Database models.

### `src/sejfa/integrations/`
Place external API clients and integration logic here.
Examples: Jira client, Slack client, GitHub integration.

### `src/sejfa/utils/`
Place general utility functions and helpers here.
Examples: Security sanitization, string formatting.

### `agent/`
Place agent-specific files here.
- `plans/`: Memory of completed tasks/plans.
- `ralph-prompts.md`: Instructions for the autonomous agent.

## Testing

Mirror the source structure in `tests/`.
- `tests/core/`: Tests for `src/sejfa/core/`
- `tests/integrations/`: Tests for `src/sejfa/integrations/`
- `tests/utils/`: Tests for `src/sejfa/utils/`
- `tests/agent/`: Tests for agent scripts and hooks.

## Guidelines

- Keep the root directory clean. Only `app.py`, `CURRENT_TASK.md` (agent memory), and config files should be here.
- Do not modify `.claude/` unless necessary for agent configuration.
