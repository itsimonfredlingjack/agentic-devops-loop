# Repository Guidelines

## Project Structure & Module Organization

- `src/`: small Node/browser utilities (e.g., `src/timestamp-display.js` web component).
- `tests/`: test suite for both Node and Python:
  - Jest: `tests/**/*.test.js`
  - Pytest: `tests/test_*.py`
- `.claude/`: agent configuration, hooks, and Python utilities (`.claude/utils/*.py`) used by the autonomous dev loop.
- `.githooks/`: optional local git hooks (commit/branch validation and Jira smart-commit automation).
- `scripts/`: helper scripts for branches, PRs, and hook setup.
- `docs/`: specs and operational docs (see `docs/GUIDELINES.md` for the development loop).
- `document_upload_app/`: sample Flask app used as an example workload.

## Build, Test, and Development Commands

```bash
# Node dependencies + checks
npm ci
npm run lint          # ESLint for JS in this repo
npm test              # Jest (tests/**/*.test.js)

# Python tests (for .claude/utils + sample app helpers)
pytest -q

# Optional: reproducible dev environment
docker compose up -d
docker compose exec agent bash
```

Install the repo git hooks (recommended) after cloning:

```bash
./scripts/setup-hooks.sh
```

## Coding Style & Naming Conventions

- JavaScript: ESLint enforced (`npm run lint`): 2-space indent, single quotes, semicolons.
- Python: follow standard 4-space indentation; prefer `ruff` for lint/format when available (see `docs/GUIDELINES.md`).
- Branch naming (when hooks enabled): `{type}/{JIRA-ID}-{slug}` (e.g., `feature/PROJ-123-add-export`).

## Testing Guidelines

- Add/adjust tests alongside changes. Keep tests close to the behavior they cover:
  - JS: add `*.test.js` under `tests/`
  - Python: add `test_*.py` under `tests/`
- Run the fastest relevant tests locally before opening a PR.

## Commit & Pull Request Guidelines

- Commit messages (when hooks enabled): `{JIRA-ID}: {description}` (e.g., `PROJ-123: Add upload export endpoint`).
- Prefer small, reviewable PRs. Include:
  - a short summary, linked Jira issue (if applicable), and test results
  - screenshots for UI-visible changes (e.g., `document_upload_app/` templates)
- Use helpers where useful: `./scripts/create-branch.sh PROJ-123 feature "short description"` and `./scripts/create-pr.sh PROJ-123`.

## Security & Configuration Tips

- Do not commit secrets: copy `.env.example` to `.env` locally and keep tokens out of git history.
- Avoid changing `.claude/hooks/` or `.github/workflows/` unless the task explicitly requires it (these are safety/automation guardrails).
