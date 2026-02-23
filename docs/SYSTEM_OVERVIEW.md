# Agentic DevOps Pipeline — Full System Overview

## The Big Picture

An autonomous development system where you **speak a feature request**, and AI handles the rest — from Jira ticket to merged pull request.

```
  You speak          AI transcribes        AI extracts intent       AI creates ticket
     🎙️          ──→    Whisper          ──→     Ollama           ──→     Jira
   (Mac)              (ai-server2)           (ai-server2)             (Atlassian)
                                                                          │
     ◄──────────────────────────────────────────────────────────────────────
     You see SuccessCard                                                  │
     with ticket link                                                     ▼
                                                                    Ralph Loop
                                                                  (Claude Code
                                                                    on Mac)
                                                                      │  ▲
                                                                      │  │  TDD loop
                                                                      ▼  │  until done
                                                                   GitHub Actions
                                                                      │
                                                                      ▼
                                                                  Jules AI Review
                                                                      │
                                                                      ▼
                                                                    Merge ✓
```

## Two Machines, One Repo

Code syncs via `git pull` from GitHub — no rsync, no SSH mounts.

```
┌─────────────────────────────────┐      ┌─────────────────────────────────┐
│    coffeedev (Mac M4, 16 GB)    │      │  ai-server2 (Ubuntu, RTX 2060)  │
│                                 │      │                                 │
│  ┌───────────────────────────┐  │ HTTP │  ┌───────────────────────────┐  │
│  │  Agentic DevOps Voice     │──│─────→│  │  Voice Pipeline Backend   │  │
│  │  (Tauri + React + Rust)   │  │      │  │  (FastAPI + Whisper +     │  │
│  │  Desktop app              │  │  WS  │  │   Ollama + Jira API)      │  │
│  │                           │←─│──────│  │  Port: 8000               │  │
│  └───────────────────────────┘  │      │  └───────────────────────────┘  │
│                                 │      │                                 │
│  ┌───────────────────────────┐  │      │  ┌───────────────────────────┐  │
│  │  Claude Code / Ralph Loop │  │      │  │  Demo Apps                │  │
│  │  (hooks, skills, Jira)    │  │      │  │  BookIt :8001, EventIt,   │  │
│  │  Dev env, tests, git      │  │      │  │  StoreIt, TrackIt         │  │
│  └───────────────────────────┘  │      │  └───────────────────────────┘  │
└─────────────────────────────────┘      └─────────────────────────────────┘
              │                                        │
              │     ┌──────────────────────┐           │
              └────→│  GitHub (git only)   │←──────────┘
                    │  Single source of    │
                    │  truth — no rsync    │
                    └──────────┬───────────┘
                    ┌──────────┴───────────┐
                    ▼                      ▼
               Jira Cloud          GitHub Actions
              (Atlassian)          (CI/CD + Jules)
```

## The Products

### 1. Agentic DevOps Voice (Desktop App)

**What:** Tauri 2 desktop app — press Space, speak, get a Jira ticket.

| | |
|---|---|
| **Runs on** | coffeedev (Mac M4) |
| **Stack** | Tauri 2, React 18, TypeScript, Zustand, Rust (cpal) |
| **Code** | `voice-app/` |
| **Talks to** | Voice Pipeline Backend on ai-server2:8000 (configurable in Settings) |

**Flow:** Mic capture (Rust) → Audio preview → Send WAV → Get transcription → See processing steps via WebSocket → SuccessCard with ticket link.

**Key features:** Live mic waveform (RMS), recording timer, audio preview with playback, toast notifications, keyboard shortcuts (Space/Escape), clarification dialog for ambiguous requests.

### 2. Voice Pipeline Backend

**What:** FastAPI server that turns audio into Jira tickets using AI.

| | |
|---|---|
| **Runs on** | ai-server2 (Ubuntu, RTX 2060 6 GB) |
| **Stack** | Python 3.12, FastAPI, Whisper, Ollama, Jira REST API |
| **Code** | `src/voice_pipeline/` |
| **Port** | 8000 |
| **GPU** | Whisper small + Ollama qwen2.5-coder-helpful:3b |

**Pipeline stages:**
1. `POST /api/pipeline/run/audio` — Upload audio → Whisper speech-to-text
2. Ollama intent extraction (project, type, priority, description)
3. If ambiguous → WebSocket `clarification_needed` → user answers → retry
4. If clear → Jira REST API → ticket created with `VOICE_INITIATED` label
5. WebSocket `completed` with ticket info
6. Auto-queue for Ralph Loop (if `AUTO_DISPATCH_LOOP=true`)

**Endpoints:** `/health`, `/api/transcribe`, `/api/extract`, `/api/pipeline/run`, `/api/pipeline/run/audio`, `/api/pipeline/clarify`, `/api/loop/queue`, `/ws/status`

### 3. Ralph Loop (Autonomous Dev Agent)

**What:** Infrastructure that makes Claude Code work autonomously on Jira tickets.

| | |
|---|---|
| **Runs on** | coffeedev (Mac) via Claude Code CLI |
| **Stack** | Claude Code hooks (Python), GitHub Actions, Jules AI |
| **Code** | `.claude/` |

**How it works:**
1. `/start-task DEV-123` — fetches Jira ticket, creates branch, populates `CURRENT_TASK.md`
2. Claude Code enters TDD loop: RED → GREEN → REFACTOR
3. `stop-hook.py` blocks exit until tests pass + lint clean + all criteria met
4. `/finish-task` — commit, push, create PR
5. GitHub Actions runs CI (lint, test, coverage)
6. Jules AI reviews the PR
7. If CI fails → self-healing pipeline retries (max 3x)
8. If everything passes → merge

**Key files:**
- `.claude/hooks/stop-hook.py` — quality gate
- `.claude/hooks/pre-tool-use.py` — security (package allowlist, protected paths)
- `.claude/ralph-config.json` — exit policy, max 25 iterations, 80% coverage
- `docs/CURRENT_TASK.md` — persistent agent memory

### 4. Demo Apps (built BY the pipeline)

| App | Domain | Purpose |
|-----|--------|---------|
| BookIt | Appointment booking | Proves: Stripe, email, multi-tenant |
| EventIt | Event ticketing | Proves: QR codes, SQLAlchemy, Alembic |
| StoreIt | E-commerce | Proves: PostgreSQL concurrency, webhooks |
| TrackIt | Time tracking | Proves: invoicing, Swedish VAT, integer arithmetic |

These run on ai-server2. They are NOT products — they exist to prove the pipeline works.

## Hardware

### coffeedev (Mac)
| | |
|---|---|
| **CPU** | Apple M4 |
| **RAM** | 16 GB |
| **OS** | macOS 26.3 |
| **Role** | Voice app, Claude Code / Ralph Loop, dev environment, tests |
| **Toolchain** | Node v22.22.0 (NVM), Python 3.14.3 (pyenv), Rust |

### ai-server2 (Ubuntu)
| | |
|---|---|
| **CPU** | 6 cores |
| **RAM** | 15 GB |
| **GPU** | NVIDIA RTX 2060 (6 GB VRAM), CUDA 12.2 |
| **OS** | Ubuntu 24.04 LTS |
| **Role** | AI inference (Whisper + Ollama), pipeline backend, demo apps |
| **Toolchain** | Python 3.12, Node v24.13.0, Docker v29.2.0 |
| **Ollama** | v0.13.5 on localhost:11434 |

## Network Map

| Connection | From | To | Protocol | Port |
|-----------|------|-----|----------|------|
| Audio upload | Mac (Tauri) | ai-server2 | HTTP POST multipart | 8000 |
| Pipeline status | ai-server2 | Mac (React) | WebSocket | 8000 |
| Clarification | Mac (React) | ai-server2 | HTTP POST JSON | 8000 |
| Whisper inference | FastAPI | local GPU | — | — |
| Ollama inference | FastAPI | localhost | HTTP | 11434 |
| Jira | Mac + ai-server2 | Atlassian Cloud | HTTPS REST | 443 |
| GitHub | Mac + ai-server2 | github.com | HTTPS (git + API) | 443 |
| Code sync | Both machines | GitHub | git pull/push | 443 |

**Tailscale:** Both machines connected via Tailscale VPN (ai-server2: `100.101.182.67`).

## Repository Structure

Everything lives in one monorepo: `github.com/itsimonfredlingjack/agentic-devops-loop`

Both machines clone the same repo. `git pull` to sync.

```
agentic-devops-loop/
│
├── voice-app/                  ← Tauri desktop app (React + Rust)
│   ├── src/                      React components, hooks, stores
│   ├── src-tauri/                Rust: mic capture, WAV encoding, API calls
│   └── ARCHITECTURE.md           Detailed architecture doc
│
├── src/voice_pipeline/         ← FastAPI voice-to-Jira pipeline
│   ├── main.py                   FastAPI app entry point
│   ├── config.py                 Pydantic Settings (.env)
│   ├── transcriber/              Whisper speech-to-text
│   ├── intent/                   Ollama intent extraction
│   ├── jira/                     Jira ticket creation
│   └── pipeline/                 Orchestration + status
│
├── .claude/                    ← Ralph Loop infrastructure
│   ├── hooks/                    stop-hook, pre-tool-use, prevent-push
│   ├── skills/                   start-task, finish-task
│   └── ralph-config.json         Exit policy
│
├── .github/workflows/          ← CI/CD pipelines
│
├── bookit/                     ← Demo: appointment booking
├── eventit/                    ← Demo: event ticketing
├── storeit/                    ← Demo: e-commerce
├── trackit/                    ← Demo: time tracking
│
├── tests/                      ← pytest test suite (64+ tests)
├── infra/                      ← Docker, Caddy, Hetzner setup
├── scripts/                    ← Helper scripts
└── docs/                       ← Documentation
```

## GitHub Actions (CI/CD)

| Workflow | Trigger | What it does |
|----------|---------|--------------|
| `ci.yml` | Push to main | Full matrix: lint, test, coverage (Python 3.11-3.13) |
| `ci_branch.yml` | Push to feature branches | Fast feedback: single Python version |
| `pr-validation.yml` | PR opened/edited | Validate title format, branch naming |
| `jules-review.yml` | PR opened | AI code review via Jules |
| `self-healing.yml` | CI failure | Auto-fix and retry (max 3x) |
| `cleanup-branches.yml` | Manual dispatch | Remove stale branches |
| `deploy-apps.yml` | Push to main | Deploy demo apps via Docker |

## Security Layers

| Layer | What | Where |
|-------|------|-------|
| **pre-tool-use hook** | Blocks unauthorized packages, dangerous commands, protected paths | `.claude/hooks/pre-tool-use.py` |
| **stop-hook** | Prevents agent exit without passing tests/lint | `.claude/hooks/stop-hook.py` |
| **prevent-push** | Blocks direct push to main | `.claude/hooks/prevent-push.py` |
| **CODEOWNERS** | Requires human review for `.github/`, hooks, Docker, .env | `.github/CODEOWNERS` |
| **package-allowlist** | Only pre-approved packages can be installed | `.claude/package-allowlist.json` |
| **prompt injection guard** | Jira data wrapped in XML tags, treated as data not instructions | `.claude/utils/sanitize.py` |
| **git hooks** | Validates commit message format + branch naming locally | `.githooks/` |

## How to Run Everything

```bash
# ── Voice Pipeline Backend (ai-server2) ──
cd /home/ai-server2/agentic-devops-loop
source venv/bin/activate
uvicorn src.voice_pipeline.main:app --host 0.0.0.0 --port 8000 --reload

# ── Voice Desktop App (Mac) ──
cd ~/Projects/agentic-devops-pipeline-v2/agentic-devops-loop/voice-app
npm run tauri dev

# ── Sync code (both machines) ──
git pull                                 # That's it. No rsync.

# ── Health Checks (from Mac) ──
curl -s http://100.101.182.67:8000/health   # Voice pipeline on ai-server2
curl -s http://100.101.182.67:11434/api/tags # Ollama models (if exposed)

# ── Tests (Mac) ──
cd ~/Projects/agentic-devops-pipeline-v2/agentic-devops-loop
source venv/bin/activate && pytest tests/ -xvs
source venv/bin/activate && ruff check .
```

## Design Language

Both the voice app and BookIt share a **glassmorphism** design system:

- Dark gradient background (`#1a1a2e` → `#16213e`)
- Frosted glass cards (`backdrop-filter: blur(12px)`, `rgba(255,255,255,0.06)`)
- Accent colors: coral `#e94560`, blue `#4a9eff`, green `#4ade80`
- Inter font family
- Animated background blobs
- CSS Modules for scoped styles
- Shared `tokens.css` design tokens

## What's Next

- **Auto-trigger Ralph Loop** — when voice app creates a `VOICE_INITIATED` ticket, automatically start Claude Code on it
- **Production deployment** — Docker compose for backend services, Tauri build for Mac app distribution
