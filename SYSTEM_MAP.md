# SYSTEM_MAP.md — SEJFA Project Inventory

> **Single source of truth.** Read this before touching anything.
> Last updated: 2026-02-20

## Architecture

```
coffeedev (Mac M-series)                    ai-server2 (Ubuntu, RTX 2060)
┌─────────────────────────┐                 ┌──────────────────────────────────┐
│                         │                 │                                  │
│  voice-app (Tauri)      │   audio/HTTP    │  Voice Pipeline (FastAPI :8000)  │
│  - React + Rust         │────────────────>│  - Whisper (GPU)                 │
│  - Mic capture (cpal)   │                 │  - Ollama intent extraction      │
│  - Glassmorphism UI     │<────────────────│  - Jira ticket creation          │
│                         │   WS updates    │  - LoopQueue                     │
│                         │                 │                                  │
│  Mobilapp               │                 │  loop-runner.sh (polling :8000)  │
│  (agentic-devops-       │                 │  - Picks up pending tickets      │
│   pipeline-v2 repo)     │                 │  - Runs: claude /start-task      │
│                         │                 │                                  │
└─────────────────────────┘                 │  BookIt (FastAPI :8001)          │
                                            │  - React + SQLite + Stripe       │
                                            │                                  │
                                            │  Ollama (:11434)                 │
                                            │  - mistral:7b-instruct-q4_0      │
                                            └──────────────────────────────────┘
                                                         │
                                                         ▼
                                                   Jira Cloud
                                                   GitHub Actions
```

## Full pipeline (when everything runs)

```
Voice (Mac) → Whisper (GPU) → Ollama (intent) → Jira ticket
                                                     │
                                          VOICE_INITIATED label
                                                     │
                                            loop-runner.sh polls
                                                     │
                                          claude /start-task DEV-XX
                                                     │
                                            TDD loop (Ralph Loop)
                                                     │
                                          git push → PR → CI
                                                     │
                                          Jules AI review → merge
```

---

## Components

### 1. voice-app/ — Tauri Desktop App

| | |
|---|---|
| **Stack** | Tauri 2 + React 18 + TypeScript + Zustand |
| **Location** | `voice-app/` (source here, built on Mac) |
| **Port** | Vite dev :5173, talks to backend :8000 |
| **State** | UI complete, glassmorphism, 110 Vitest tests, ESLint clean |
| **Bundle** | Configured in `src-tauri/tauri.conf.json`, built via `npm run tauri build` on Mac |

**13 React components**, 3 custom hooks, Zustand store with full pipeline state.

**Rust backend** (`src-tauri/src/`): mic capture via cpal, WAV encoding, HTTP upload.

**BUG:** `api.rs:send_audio` posts to `/api/transcribe` instead of `/api/pipeline/run/audio`. Transcription works but the full pipeline (Ollama + Jira) never triggers.

### 2. src/voice_pipeline/ — Voice Pipeline Backend

| | |
|---|---|
| **Stack** | FastAPI + Whisper + Ollama + Jira REST |
| **Location** | `src/voice_pipeline/` (root level) |
| **Port** | :8000 |
| **State** | All code exists, 322 tests pass. NOT running as service. |
| **Config** | `src/voice_pipeline/config.py`, reads `.env` |

**Endpoints:**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check |
| `/api/transcribe` | POST | Whisper only (returns text) |
| `/api/extract` | POST | Ollama intent only |
| `/api/pipeline/run` | POST | Full pipeline from text |
| `/api/pipeline/run/audio` | POST | Full pipeline from audio |
| `/api/pipeline/clarify` | POST | Clarification round |
| `/api/webhook/jira` | POST | Jira webhook receiver |
| `/api/loop/queue` | GET | Pending tickets for Ralph Loop |
| `/api/loop/started` | POST | Mark ticket as started |
| `/api/loop/completed` | POST | Mark ticket as completed |
| `/ws/status` | WS | Real-time status broadcast |

**Run:** `source agentic-devops-loop/venv/bin/activate && uvicorn src.voice_pipeline.main:app --host 0.0.0.0 --port 8000`

### 3. agentic-devops-loop/ — Ralph Loop Infrastructure

| | |
|---|---|
| **Location** | `agentic-devops-loop/` |
| **Purpose** | Claude Code hooks, skills, loop config, scripts |
| **Has own git** | Yes (nested `.git/`) |

**Key files:**
- `.claude/hooks/stop-hook.py` — quality gate (blocks exit until tests+lint pass)
- `.claude/hooks/pre-tool-use.py` — security (package allowlist, protected paths)
- `.claude/hooks/prevent-push.py` — blocks direct push to main
- `.claude/ralph-config.json` — max 25 iterations, 80% coverage
- `scripts/loop-runner.sh` — polls queue, triggers `claude /start-task`
- `src/voice_pipeline/persistent_loop_queue.py` — SQLite-backed queue (not yet in root)

**Tests:** 332 (includes 10 PersistentLoopQueue tests not in root)

### 4. bookit/ — Booking System

| | |
|---|---|
| **Stack** | FastAPI + aiosqlite + React + Stripe |
| **Location** | `bookit/` |
| **Ports** | Backend :8001, Frontend :5173 |
| **State** | Complete app — multi-tenant, payments, email, recurring bookings, stats dashboard |
| **Database** | SQLite (`bookit/backend/bookit.db`) |

Separate from SEJFA voice pipeline. Runs entirely on ai-server2.

### 5. voice-pipeline/ — Standalone Copy (LEGACY)

| | |
|---|---|
| **Location** | `voice-pipeline/` |
| **State** | Older fork, 64 tests. Missing LoopQueue, different imports. |
| **Action** | Do NOT develop here. Use root `src/voice_pipeline/` instead. |

### 6. grupp-ett-github/ — Separate Project

| | |
|---|---|
| **Location** | `grupp-ett-github/` |
| **State** | Flask app, not part of SEJFA. Has own pyproject.toml. |

### 7. Mobilapp — On Mac

| | |
|---|---|
| **Repo** | `agentic-devops-pipeline-v2` on coffeedev (Mac) |
| **Location** | Not on ai-server2 |

---

## What works vs what doesn't

| Thing | Works? | Blocker |
|-------|--------|---------|
| Voice-app UI + mic capture | Yes | Built on Mac only |
| Voice-app → backend audio upload | Partially | Calls wrong endpoint (`/api/transcribe` not `/api/pipeline/run/audio`) |
| Whisper transcription | Yes (code) | Needs GPU + server running |
| Ollama intent extraction | Yes (code) | Needs Ollama running on :11434 |
| Jira ticket creation | Yes (code) | Needs `.env` with credentials |
| WebSocket status updates | Yes (code) | Needs server running |
| LoopQueue (in-memory) | Yes | Lost on restart |
| PersistentLoopQueue (SQLite) | Yes (agentic-devops-loop only) | Not wired to root main.py |
| loop-runner.sh | Yes (code) | Not running as service |
| Ralph Loop hooks | Yes | Active when Claude Code runs |
| GitHub Actions CI | Yes | Running on push/PR |
| BookIt | Yes | Independent, working |

---

## Known gaps (in priority order)

### GAP 1: Wrong endpoint in voice-app
**File:** `voice-app/src-tauri/src/api.rs`
**Bug:** Posts to `/api/transcribe` (returns text only) instead of `/api/pipeline/run/audio` (runs full pipeline)
**Impact:** Desktop app transcribes audio but never creates Jira tickets
**Fix:** Change URL in `send_audio` function. One line on Mac.

### GAP 2: No .env file
**Template:** `agentic-devops-loop/.env.example`
**Needs:** `JIRA_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`, `JIRA_PROJECT_KEY`
**Impact:** Nothing talks to Jira without credentials

### GAP 3: Services not running
**Backend:** `uvicorn src.voice_pipeline.main:app` not started
**Loop runner:** `scripts/loop-runner.sh` not started
**Fix:** systemd services (see `scripts/systemd/`)

### GAP 4: PersistentLoopQueue not in root
**Exists in:** `agentic-devops-loop/src/voice_pipeline/persistent_loop_queue.py`
**Missing from:** Root `src/voice_pipeline/`
**Impact:** Server restart loses pending tickets (in-memory only)

---

## How to run everything

### Backend (voice pipeline)
```bash
cd /home/ai-server2/04-voice-mode-4-loop
source agentic-devops-loop/venv/bin/activate
cp agentic-devops-loop/.env.example .env  # Then fill in real credentials
uvicorn src.voice_pipeline.main:app --host 0.0.0.0 --port 8000
```

### Loop runner (auto-triggers Ralph Loop)
```bash
cd /home/ai-server2/04-voice-mode-4-loop/agentic-devops-loop
LOOP_RUNNER_BACKEND_URL=http://localhost:8000 \
LOOP_RUNNER_REPO_DIR=/home/ai-server2/04-voice-mode-4-loop/agentic-devops-loop \
bash scripts/loop-runner.sh
```

### BookIt
```bash
cd /home/ai-server2/04-voice-mode-4-loop/bookit/backend
source venv/bin/activate
uvicorn src.main:app --host 0.0.0.0 --port 8001
```

### Voice-app (dev, on this machine)
```bash
cd /home/ai-server2/04-voice-mode-4-loop/voice-app
npm run dev  # Vite on :5173
```

### Voice-app (Tauri build, on Mac)
```bash
ssh coffeedev
cd voice-app
npm run tauri build  # Creates .app bundle
```

### Tests
```bash
# Python (322 tests)
source agentic-devops-loop/venv/bin/activate && pytest tests/ -xvs

# Voice-app (110 tests)
cd voice-app && npm test

# BookIt
cd bookit/backend && source venv/bin/activate && pytest tests/ -xvs
```

---

## File locations cheat sheet

| What | Where |
|------|-------|
| Voice pipeline code | `src/voice_pipeline/` |
| Voice pipeline tests | `tests/voice_pipeline/` |
| Pipeline config | `src/voice_pipeline/config.py` |
| .env template | `agentic-devops-loop/.env.example` |
| Ralph Loop hooks | `agentic-devops-loop/.claude/hooks/` |
| Loop runner script | `agentic-devops-loop/scripts/loop-runner.sh` |
| PersistentLoopQueue | `agentic-devops-loop/src/voice_pipeline/persistent_loop_queue.py` |
| CI workflows | `.github/workflows/` |
| Tauri config | `voice-app/src-tauri/tauri.conf.json` |
| Rust audio code | `voice-app/src-tauri/src/api.rs` |
| BookIt backend | `bookit/backend/src/` |
| BookIt frontend | `bookit/frontend/src/` |
| systemd services | `scripts/systemd/` |
