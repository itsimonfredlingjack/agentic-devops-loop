# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## UNDERSTAND THIS FIRST — Read Before Doing Anything

This project is **ONE product**: an autonomous development pipeline (Ralph Loop).
It is NOT a collection of apps. It is NOT a monorepo of services.

**The product is the process itself** — AI agents that autonomously take a Jira ticket
from backlog to merged PR, with TDD, quality gates, and AI code review at every step.

The apps in this repo (BookIt, EventIt, StoreIt, TrackIt) are **demo-targets** — proof
that the pipeline works across different domains. They are NOT products to maintain,
harden, or improve unless a Jira ticket specifically asks for it.

### Priority Hierarchy (follow this strictly)

```
P0  Pipeline infrastructure    hooks, skills, CI/CD, self-healing, Ralph Loop
P1  Voice Pipeline             input channel: voice → Whisper → Ollama → Jira ticket
P2  Jira integration           two-way sync, automatic transitions, ticket creation
P3  Monitoring & observability real-time dashboard, agent telemetry
P4  Demo apps                  ONLY when a Jira ticket targets them specifically
```

### What This Means For You (the AI agent)

- **NEVER** propose improvements to demo apps on your own initiative
- **NEVER** treat BookIt/EventIt/StoreIt/TrackIt as production services
- **NEVER** suggest auth, pagination, logging, or hardening for demo apps
- **ALWAYS** prioritize pipeline reliability over app features
- **ALWAYS** ask: "does this make the autonomous loop better?" — if not, don't do it

### The Full Pipeline (this is the product)

```
Voice → Whisper → Ollama → Jira Ticket → Claude Code (Ralph Loop) → GitHub Actions → Jules AI Review → Merge
```

## Repository Structure

### Core product (the pipeline)

| Directory | What | Stack |
|-----------|------|-------|
| `agentic-devops-loop/` | **The product.** Ralph Loop hooks, skills, CI/CD, Jira integration, voice pipeline backend | Python 3.11+, FastAPI, Claude Code hooks |
| `voice-app/` | Voice input UI — records audio, sends to pipeline, displays results | Tauri 2, React 18, TypeScript, Zustand |
| `.github/workflows/` | CI/CD: testing, self-healing, Jules AI review, branch cleanup | GitHub Actions |

### Demo targets (built BY the pipeline, not the product)

| Directory | Domain | Purpose as demo |
|-----------|--------|-----------------|
| `bookit/` | Appointment booking | Proves: Stripe integration, email, multi-tenant |
| `eventit/` | Event ticketing | Proves: QR codes, SQLAlchemy, Alembic migrations |
| `storeit/` | E-commerce | Proves: PostgreSQL concurrency, pessimistic locking, webhooks |
| `trackit/` | Time tracking | Proves: invoicing, Swedish VAT (moms), integer arithmetic |

### Legacy (do not develop here)

| Directory          | Note                                                                                          |
|--------------------|-----------------------------------------------------------------------------------------------|
| `voice-pipeline/`  | **Deprecated standalone copy.** Canonical source is `agentic-devops-loop/src/voice_pipeline/`. |

## Architecture: Ralph Loop

Ralph Loop is NOT a script you create. It is the persistent iteration mechanism built into Claude Code via hooks in `agentic-devops-loop/.claude/`:

1. `/start-task DEV-123` → fetches Jira ticket, creates branch, sets up `docs/CURRENT_TASK.md`, activates loop
2. Agent works in TDD loop (RED → GREEN → REFACTOR) until all acceptance criteria met
3. `stop-hook.py` blocks exit until: tests pass, lint clean, PR merged, `<promise>DONE</promise>` output
4. `/finish-task` runs automatically as part of the loop — commit, push, PR, merge, Jira update

Key files that control the loop:
- `.claude/hooks/stop-hook.py` — quality gate, exit enforcement
- `.claude/hooks/pre-tool-use.py` — security validation (package allowlist, protected paths, dangerous commands)
- `.claude/ralph-config.json` — exit policy, max iterations (25), coverage threshold (80%)
- `docs/CURRENT_TASK.md` — persistent agent memory across context windows
- `.claude/.ralph_loop_active` — flag file that activates enforcement

## Architecture: Voice Pipeline

```
Mac (Tauri app)                    ai-server2 (FastAPI :8000)
  |                                    |
  |--[audio via network]-------------->| POST /api/pipeline/run/audio
  |                                    |   → Whisper transcription (GPU)
  |                                    |   → Ollama intent extraction (GPU)
  |                                    |   → Jira REST API → ticket created
  |<--[WS: status updates]------------|
  |                                    |
  |--[clarification answer]----------->| POST /api/pipeline/clarify
  |<--[WS: clarification_needed]------|   (if ambiguity > threshold)
```

The gap: voice pipeline creates tickets with `VOICE_INITIATED` label, but nothing currently triggers Ralph Loop to pick them up automatically.

## Commands

### agentic-devops-loop (Python)
```bash
cd agentic-devops-loop
source venv/bin/activate && pytest tests/ -xvs          # All tests (stop on first failure)
source venv/bin/activate && pytest tests/voice_pipeline/ -xvs  # Voice pipeline tests only
source venv/bin/activate && pytest -k "test_name" -xvs   # Single test
source venv/bin/activate && ruff check .                  # Lint
source venv/bin/activate && ruff check --fix .            # Lint + auto-fix
source venv/bin/activate && ruff format .                 # Format
source venv/bin/activate && uvicorn src.voice_pipeline.main:app --host 0.0.0.0 --port 8000 --reload  # Run server
```

**venv activation is mandatory.** Without it: ImportError, wasted iteration.

### voice-pipeline (Python, standalone copy)
```bash
cd voice-pipeline
source venv/bin/activate && pytest tests/ -xvs
source venv/bin/activate && ruff check .
source venv/bin/activate && uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

Note: imports are `from src.*` here, vs `from src.voice_pipeline.*` in agentic-devops-loop.

### voice-app (Tauri/React)
```bash
cd voice-app
npm run dev              # Vite dev server :5173
npm run build            # tsc && vite build
npx tsc --noEmit         # Type check only
npm run tauri dev        # Full Tauri desktop app
```

## Git Conventions (agentic-devops-loop)

- **Branch:** `{type}/{JIRA-ID}-{slug}` (e.g., `feature/DEV-42-add-oauth`)
- **Commit:** `DEV-42: Add OAuth login endpoint`
- **PR title:** `[DEV-42] Add OAuth login`
- **Allowed types:** feature, bugfix, hotfix, refactor, docs
- **Never:** `git add -A` or `git add .` (use `git add -u` for tracked files only)

## Jira Integration

Direct REST API — NOT MCP tools:
```bash
source venv/bin/activate && python3 -c "
from dotenv import load_dotenv; load_dotenv()
from src.sejfa.integrations.jira_client import get_jira_client
client = get_jira_client()
issue = client.get_issue('DEV-42')
print(f'{issue.key}: {issue.summary}')
"
```

Methods: `get_issue()`, `search_issues()`, `add_comment()`, `transition_issue()`, `create_issue()`, `test_connection()`

## Protected Paths (Do Not Modify)

- `.github/` — CI/CD workflows, CODEOWNERS
- `.claude/hooks/` — security hooks (stop-hook, pre-tool-use, etc.)
- `Dockerfile`, `docker-compose.yml`
- `.env` files

## Ruff Configuration

Both projects share the same style:
- Line length: 100
- Target: Python 3.11
- Rules: E, F, W, I, N, UP, B, C4
- Excludes: `.claude/hooks/*`, `venv`

## Test Markers

```python
@pytest.mark.unit          # Isolated components
@pytest.mark.integration   # External dependencies
@pytest.mark.e2e           # End-to-end workflows
@pytest.mark.slow          # Long-running tests
```

Coverage threshold: 80% (local), 70% (CI).
