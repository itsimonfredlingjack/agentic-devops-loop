# Repository Guidelines

## Project Structure & Module Organization
- `.claude/` agent config (hooks, plugins, skills, settings).
- `.github/` CI workflows and CODEOWNERS.
- `docs/` operator docs like `CURRENT_TASK.md`, `GUIDELINES.md`, `QUICKSTART.md`, and `SPEC.md`.
- `scripts/` helper scripts for hooks, branching, and PR creation.
- `Dockerfile` and `docker-compose.yml` for containerized runs.

## Build, Test, and Development Commands
- `npm install` installs JS tooling dependencies.
- `npm run lint` runs ESLint across the repo.
- `npm test` runs Jest tests.
- `./scripts/setup-hooks.sh` installs local git hooks.
- `claude` then `/start-task PROJ-123` starts the agent loop.
- `docker compose up -d` and `docker compose exec agent bash` runs in Docker.

## Coding Style & Naming Conventions
- Use ESLint as the source of truth; keep diffs focused and avoid drive-by formatting.
- Branches: `feature/PROJ-123-description`.
- Commits: `PROJ-123: Short description`.
- PR titles: `[PROJ-123] Short description`.

## Testing Guidelines
- Framework: Jest.
- Add tests alongside new logic where possible (e.g., `foo.test.js`).
- Ensure `npm test` passes before opening a PR.

## Commit & Pull Request Guidelines
- Link the Jira ticket and include a short summary plus test results in the PR description.
- CI runs lint/test/build in GitHub Actions; green checks required.
- Changes to `.github/` or `.claude/hooks/` require human review (per CODEOWNERS).

## Security & Configuration Tips
- Copy `.env.example` to `.env` and set `JIRA_URL`, `JIRA_USERNAME`, `JIRA_API_TOKEN`.
- Update `.claude/package-allowlist.json` before adding new npm/pip packages.
