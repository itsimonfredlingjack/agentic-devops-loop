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
                                                                   (Claude Code)
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

## Three Products, Two Machines

```
┌─────────────────────────────────┐      ┌─────────────────────────────────┐
│    coffeedev (Mac M4, 16 GB)    │      │  ai-server2 (Ubuntu, RTX 2060)  │
│                                 │      │                                 │
│  ┌───────────────────────────┐  │ HTTP │  ┌───────────────────────────┐  │
│  │  Agentic DevOps Voice     │──│─────→│  │  Voice Pipeline Backend   │  │
│  │  (Tauri + React + Rust)   │  │      │  │  (FastAPI + Whisper +     │  │
│  │  Desktop app              │  │  WS  │  │   Ollama + Jira API)      │  │
│  │  Port: —                  │←─│──────│  │  Port: 8000               │  │
│  └───────────────────────────┘  │      │  └───────────────────────────┘  │
│                                 │      │                                 │
│                                 │      │  ┌───────────────────────────┐  │
│                                 │      │  │  BookIt                   │  │
│                                 │      │  │  (FastAPI + React + SQLite)│  │
│                                 │      │  │  Multi-tenant booking     │  │
│                                 │      │  │  Port: 8001 + 5173       │  │
│                                 │      │  └───────────────────────────┘  │
│                                 │      │                                 │
│                                 │      │  ┌───────────────────────────┐  │
│                                 │      │  │  Ralph Loop               │  │
│                                 │      │  │  (Claude Code + hooks +   │  │
│                                 │      │  │   GitHub Actions + Jules) │  │
│                                 │      │  │  Autonomous dev agent     │  │
│                                 │      │  └───────────────────────────┘  │
└─────────────────────────────────┘      └─────────────────────────────────┘
                                                       │
                                              ┌────────┴────────┐
                                              ▼                 ▼
                                         Jira Cloud      GitHub (CI/CD)
                                        (Atlassian)    (Actions + Jules)
```

## The Three Products

### 1. Agentic DevOps Voice (Desktop App)

**What:** Tauri 2 desktop app — press Space, speak, get a Jira ticket.

| | |
|---|---|
| **Runs on** | coffeedev (Mac M4) |
| **Stack** | Tauri 2, React 18, TypeScript, Zustand, Rust (cpal) |
| **Code** | `voice-app/` |
| **Talks to** | Voice Pipeline Backend on ai-server2:8000 |

**Flow:** Mic capture (Rust) → Audio preview → Send WAV → Get transcription → See processing steps via WebSocket → SuccessCard with ticket link.

**Key features:** Live mic waveform (RMS), recording timer, audio preview with playback, toast notifications, keyboard shortcuts (Space/Escape), clarification dialog for ambiguous requests.

### 2. Voice Pipeline Backend

**What:** FastAPI server that turns audio into Jira tickets using AI.

| | |
|---|---|
| **Runs on** | ai-server2 (Ubuntu, RTX 2060 6 GB) |
| **Stack** | Python 3.12, FastAPI, Whisper, Ollama, Jira REST API |
| **Code** | `agentic-devops-loop/src/voice_pipeline/` (integrated) + `voice-pipeline/` (standalone copy) |
| **Port** | 8000 |
| **GPU** | Whisper small + Ollama qwen2.5-coder-helpful:3b |

**Pipeline stages:**
1. `POST /api/transcribe` — Whisper speech-to-text
2. `POST /api/extract` — Ollama intent extraction (project, type, priority, description)
3. If ambiguous → WebSocket `clarification_needed` → user answers → retry
4. If clear → Jira REST API → ticket created
5. WebSocket `completed` with ticket info

**Endpoints:** `/health`, `/api/transcribe`, `/api/extract`, `/api/pipeline/run`, `/api/pipeline/clarify`, `/ws/status`

### 3. BookIt (Booking System)

**What:** Multi-tenant booking system for businesses. Customers book via a public page.

| | |
|---|---|
| **Runs on** | ai-server2 |
| **Stack** | FastAPI + aiosqlite (backend), React 18 + Vite (frontend) |
| **Code** | `bookit/` |
| **Ports** | Backend :8001, Frontend :5173 |
| **DB** | SQLite (`bookit.db`) |

**Features:** Multi-tenant (slug-based URLs), service management, slot generation, Stripe payments, recurring bookings, email notifications, statistics dashboard.

**Demo data:** "Klipp & Trim" hair salon with Herrklippning, Damklippning, Färgning, Skäggtrimning.

### 4. Ralph Loop (Autonomous Dev Agent)

**What:** Not a product you use directly — it's the infrastructure that makes Claude Code work autonomously on Jira tickets.

| | |
|---|---|
| **Runs on** | ai-server2 (via Claude Code CLI) |
| **Stack** | Claude Code hooks (Python), GitHub Actions, Jules AI |
| **Code** | `agentic-devops-loop/.claude/` |

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

## Hardware

### coffeedev (Mac)
| | |
|---|---|
| **CPU** | Apple M4 |
| **RAM** | 16 GB |
| **OS** | macOS 26.3 |
| **Role** | Desktop app runtime, Tauri/Rust compilation |
| **Toolchain** | Node v25.6.1, Rust 1.93.1 |

### ai-server2 (Ubuntu)
| | |
|---|---|
| **CPU** | 6 cores |
| **RAM** | 15 GB |
| **GPU** | NVIDIA RTX 2060 (6 GB VRAM), CUDA 12.2 |
| **OS** | Ubuntu 24.04 LTS |
| **Role** | AI inference, backend services, Claude Code agent |
| **Toolchain** | Python 3.12, Node v24.13.0, Docker v29.2.0 |
| **Ollama** | v0.13.5 on localhost:11434 |

## Network Map

| Connection | From | To | Protocol | Port |
|-----------|------|-----|----------|------|
| Audio upload | Mac (Tauri) | ai-server2 | HTTP POST multipart | 8000 |
| Pipeline status | ai-server2 | Mac (React) | WebSocket | 8000 |
| Clarification | Mac (React) | ai-server2 | HTTP POST JSON | 8000 |
| BookIt API | Browser | ai-server2 | HTTP REST | 8001 |
| BookIt frontend | Browser | ai-server2 | HTTP (Vite) | 5173 |
| Whisper inference | FastAPI | local GPU | — | — |
| Ollama inference | FastAPI | localhost | HTTP | 11434 |
| Jira | ai-server2 | Atlassian Cloud | HTTPS REST | 443 |
| Stripe | ai-server2 | Stripe API | HTTPS | 443 |
| GitHub | ai-server2 | github.com | HTTPS (git + API) | 443 |
| Code sync | ai-server2 | Mac | rsync over SSH | 22 |

## Repository Structure

Everything lives in one monorepo: `github.com/itsimonfredlingjack/agentic-devops-loop`

```
04-voice-mode-4-loop/
│
├── voice-app/                  ← Tauri desktop app (React + Rust)
│   ├── src/                      React components, hooks, stores
│   ├── src-tauri/                Rust: mic capture, WAV encoding, API calls
│   ├── ARCHITECTURE.md           Detailed architecture doc
│   └── package.json              Node dependencies
│
├── bookit/                     ← Multi-tenant booking system
│   ├── backend/                  FastAPI + SQLite
│   │   ├── src/bookit/           Routers, services, schemas
│   │   ├── tests/                8 test modules
│   │   └── scripts/seed.py       Demo data generator
│   ├── frontend/                 React + Vite + Zustand
│   │   └── src/                  Pages, components, store, API client
│   └── ARCHITECTURE.md           Detailed architecture doc
│
├── agentic-devops-loop/        ← Ralph Loop infrastructure
│   ├── .claude/                  Hooks, skills, config, security
│   │   ├── hooks/                stop-hook, pre-tool-use, prevent-push
│   │   ├── skills/               start-task, finish-task
│   │   └── ralph-config.json     Exit policy
│   ├── .github/workflows/        11 CI/CD workflows
│   ├── src/voice_pipeline/       Voice pipeline (integrated copy)
│   ├── src/sejfa/                Shared utils (Jira client, monitor)
│   └── tests/                    64+ tests
│
├── voice-pipeline/             ← Standalone voice pipeline (separate copy)
│   └── src/                      Same as above, different import paths
│
├── grupp-ett-github/           ← Multi-agent monitor/dashboard
│
└── SYSTEM_OVERVIEW.md          ← This document
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
| `pages.yml` | Push to main | Deploy docs to GitHub Pages |

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
cd /home/ai-server2/04-voice-mode-4-loop/agentic-devops-loop
source venv/bin/activate
uvicorn src.voice_pipeline.main:app --host 0.0.0.0 --port 8000 --reload

# ── Voice Desktop App (Mac, via SSH) ──
ssh coffeedev "cd ~/Projects/agentic-devops-pipeline-v2/sejfa-voice/voice-app && \
  npm run tauri dev"

# ── BookIt Backend (ai-server2) ──
cd /home/ai-server2/04-voice-mode-4-loop/bookit/backend
source venv/bin/activate
python -m scripts.seed                    # First time: seed demo data
uvicorn src.bookit.main:app --host 0.0.0.0 --port 8001 --reload

# ── BookIt Frontend (ai-server2) ──
cd /home/ai-server2/04-voice-mode-4-loop/bookit/frontend
npm run dev                               # → http://localhost:5173

# ── Health Checks ──
curl -s http://localhost:8000/health      # Voice pipeline
curl -s http://localhost:8001/health      # BookIt
curl -s http://localhost:11434/api/tags   # Ollama models

# ── Code Sync (ai-server2 → Mac) ──
rsync -avz --exclude node_modules --exclude dist --exclude target --exclude .vite \
  /home/ai-server2/04-voice-mode-4-loop/voice-app/ \
  coffeedev:~/Projects/agentic-devops-pipeline-v2/sejfa-voice/voice-app/
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
- **BookIt voice integration** — "Book a haircut for Thursday at 2pm" via the voice app
- **Better app icon** — replace placeholder coral circle with a proper mic/waveform icon
- **Production deployment** — Docker compose for backend services, Tauri build for Mac app distribution
