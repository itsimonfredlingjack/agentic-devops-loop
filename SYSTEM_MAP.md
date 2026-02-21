# SYSTEM_MAP.md — SEJFA Project Inventory

> **Single source of truth.** Read this before touching anything.
> Last updated: 2026-02-21

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
                                            │  - Booking + Stripe + email      │
                                            │                                  │
                                            │  TrackIt (FastAPI :8002)         │
                                            │  - Time tracking + invoicing     │
                                            │  - 25% moms, integer-matte      │
                                            │                                  │
                                            │  StoreIt (FastAPI :8004)         │
                                            │  - E-commerce + PostgreSQL       │
                                            │  - SELECT FOR UPDATE locking     │
                                            │  - Stripe Checkout + webhooks    │
                                            │                                  │
                                            │  PostgreSQL 16 (Docker :5433)    │
                                            │  - StoreIt database (256MB)      │
                                            │                                  │
                                            │  Ollama (:11434)                 │
                                            │  - qwen2.5-coder-helpful:3b      │
                                            └──────────────────────────────────┘
                                                         │
                                                         ▼
                                                   Jira Cloud
                                                   GitHub Actions
```

## Port map

| Port | Service | Status |
|------|---------|--------|
| 8000 | Voice Pipeline (FastAPI) | systemd: sejfa-voice-pipeline |
| 8001 | BookIt backend | systemd: sejfa-bookit |
| 8002 | TrackIt backend | running |
| 8003 | (reserved) | in use |
| 8004 | StoreIt backend | manual start |
| 5433 | PostgreSQL 16 (Docker) | storeit-postgres container |
| 11434 | Ollama | running |
| 5173 | voice-app Vite dev | manual start |

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
| **State** | All code exists, 322 tests pass. Running as systemd service. |
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

### 5. trackit/ — Time Tracking & Invoicing

| | |
|---|---|
| **Stack** | FastAPI + aiosqlite + Pydantic v2 |
| **Location** | `trackit/backend/` |
| **Port** | :8002 |
| **State** | Complete — 41 tests passing, ruff clean |
| **Database** | SQLite (`trackit.db`) |
| **PR** | #59 |

**Multi-tenant:** tenants → projects → time entries → invoices.

**Invoice service:** 25% Swedish VAT (moms), integer arithmetic in cents/ore. Finalize flow marks entries as invoiced (idempotent, single-transaction).

**Endpoints:**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check |
| `/api/tenants` | POST | Create tenant |
| `/api/tenants/{slug}` | GET | Get tenant by slug |
| `/api/tenants/{slug}/projects` | POST/GET | Create/list projects |
| `/api/tenants/{slug}/projects/{id}/time` | POST | Log time entry |
| `/api/tenants/{slug}/invoice` | GET | Generate invoice for month |
| `/api/tenants/{slug}/invoice/finalize` | POST | Lock entries as invoiced |

**Run:** `source trackit/backend/venv/bin/activate && uvicorn trackit.main:app --host 0.0.0.0 --port 8002`

### 6. storeit/ — E-Commerce Backend (PostgreSQL)

| | |
|---|---|
| **Stack** | FastAPI + SQLAlchemy 2.0 + asyncpg + PostgreSQL 16 + Stripe |
| **Location** | `storeit/backend/` |
| **Port** | :8004 (API), :5433 (PostgreSQL via Docker) |
| **State** | Complete — 63 tests passing (incl. 4 race condition tests), ruff clean |
| **Database** | PostgreSQL 16 Alpine (Docker container `storeit-postgres`) |
| **Migrations** | Alembic (async) — `alembic/versions/1918cc1d3287_initial_schema.py` |
| **PR** | #59 |

**Key differentiator:** `SELECT FOR UPDATE` pessimistic locking prevents overselling under concurrent load. Proven by race condition tests with `asyncio.Barrier` + `asyncio.gather` (10 buyers, 1 stock → exactly 1 wins).

**Domain models (9 tables):**
- `categories`, `products`, `product_variants` — product catalog
- `inventory`, `inventory_reservations` — stock with soft reservation + TTL
- `carts`, `cart_items` — session-based shopping cart
- `orders`, `order_items` — order lifecycle with state machine

**Order state machine:**
```
pending → paid → processing → shipped → delivered
  ↓        ↓        ↓
cancelled cancelled cancelled     delivered → refunded
```

**Concurrency safety:**
- All lock functions use consistent ordering: InventoryRecord FIRST, then InventoryReservation
- Multi-variant carts sort by variant_id before locking (prevents ABBA deadlocks)
- Background task expires stale reservations every 60s (prevents stock lockup)

**Stripe integration:**
- `POST /api/payments/checkout` — creates Stripe Checkout Session
- `POST /api/payments/webhook` — signature verify → order paid → fulfill reservations
- Idempotent: duplicate webhooks are safely ignored

**Endpoints:**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check |
| `/api/categories` | POST/GET | Category CRUD |
| `/api/products` | POST/GET | Product CRUD |
| `/api/products/{id}` | GET | Product with variants |
| `/api/products/{id}/variants` | POST | Add variant |
| `/api/inventory/{variant_id}` | GET/PUT | Stock management |
| `/api/cart/{session_id}` | GET | Get cart |
| `/api/cart/{session_id}/items` | POST | Add item to cart |
| `/api/cart/{session_id}/items/{id}` | PATCH/DELETE | Update/remove item |
| `/api/orders` | POST/GET | Create order / list orders |
| `/api/orders/{id}` | GET | Get order |
| `/api/orders/{id}/status` | PATCH | Transition order status |
| `/api/payments/checkout` | POST | Create Stripe Checkout Session |
| `/api/payments/webhook` | POST | Stripe webhook handler |

**Run:**
```bash
# Start PostgreSQL
docker compose -f storeit/backend/docker-compose.yml up -d

# Apply migrations
source storeit/backend/venv/bin/activate && cd storeit/backend && alembic upgrade head

# Start server
uvicorn storeit.main:app --host 0.0.0.0 --port 8004
```

### 7. voice-pipeline/ — Standalone Copy (LEGACY)

| | |
|---|---|
| **Location** | `voice-pipeline/` |
| **State** | Older fork, 64 tests. Missing LoopQueue, different imports. |
| **Action** | Do NOT develop here. Use root `src/voice_pipeline/` instead. |

### 8. grupp-ett-github/ — Separate Project

| | |
|---|---|
| **Location** | `grupp-ett-github/` |
| **State** | Flask app, not part of SEJFA. Has own pyproject.toml. |

### 9. Mobilapp — On Mac

| | |
|---|---|
| **Repo** | `agentic-devops-pipeline-v2` on coffeedev (Mac) |
| **Location** | Not on ai-server2 |

---

## Systemd services

| Service | Status | What |
|---------|--------|------|
| `sejfa-voice-pipeline` | active | Voice pipeline on :8000 |
| `sejfa-bookit` | active | BookIt on :8001 |
| `sejfa-loop-runner` | active | Polls queue every 10s |

TrackIt and StoreIt are not yet systemd services (manual start).

---

## Test suite summary

| Project | Tests | Time | DB |
|---------|-------|------|-------|
| Voice pipeline | 322 | ~5s | mocked |
| Voice-app | 110 | ~2s | N/A (Vitest) |
| BookIt | 30+ | ~1s | in-memory SQLite |
| TrackIt | 41 | 0.14s | in-memory SQLite |
| StoreIt | 63 | 3.3s | in-memory SQLite + PostgreSQL (race tests) |
| **Total** | **566+** | | |

---

## What works vs what doesn't

| Thing | Works? | Blocker |
|-------|--------|---------|
| Voice-app UI + mic capture | Yes | Built on Mac only |
| Voice-app → backend audio upload | Partially | Calls wrong endpoint |
| Whisper transcription | Yes (code) | Needs GPU + server running |
| Ollama intent extraction | Yes (code) | Needs Ollama running on :11434 |
| Jira ticket creation | Yes (code) | Needs `.env` with credentials |
| WebSocket status updates | Yes (code) | Needs server running |
| LoopQueue (in-memory) | Yes | Lost on restart |
| PersistentLoopQueue (SQLite) | Yes (agentic-devops-loop only) | Not wired to root main.py |
| loop-runner.sh | Yes | Running as systemd service |
| Ralph Loop hooks | Yes | Active when Claude Code runs |
| GitHub Actions CI | Yes | Running on push/PR |
| BookIt | Yes | Running as systemd service |
| TrackIt | Yes | 41 tests, not yet systemd |
| StoreIt | Yes | 63 tests, PostgreSQL via Docker, not yet systemd |
| StoreIt race condition tests | Yes | SELECT FOR UPDATE proven with 10 concurrent buyers |
| StoreIt Stripe integration | Yes (mocked) | Needs real Stripe keys for production |

---

## Known gaps (in priority order)

### GAP 1: Wrong endpoint in voice-app
**File:** `voice-app/src-tauri/src/api.rs`
**Bug:** Posts to `/api/transcribe` (returns text only) instead of `/api/pipeline/run/audio` (runs full pipeline)
**Impact:** Desktop app transcribes audio but never creates Jira tickets
**Fix:** Change URL in `send_audio` function. One line on Mac.

### GAP 2: PersistentLoopQueue not in root
**Exists in:** `agentic-devops-loop/src/voice_pipeline/persistent_loop_queue.py`
**Missing from:** Root `src/voice_pipeline/`
**Impact:** Server restart loses pending tickets (in-memory only)

### GAP 3: StoreIt missing auth
**Impact:** All endpoints are unauthenticated. Admin operations (set stock, transition orders) are open.
**Fix:** Add JWT auth middleware (Phase 4).

### GAP 4: StoreIt missing pagination
**Impact:** List endpoints (`GET /api/orders`, `/api/products`) return all rows. Will OOM under load.
**Fix:** Add cursor or offset pagination.

### GAP 5: No structured logging
**Impact:** Hard to debug in production. No request IDs or correlation.

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

### TrackIt
```bash
source /home/ai-server2/04-voice-mode-4-loop/trackit/backend/venv/bin/activate
uvicorn trackit.main:app --host 0.0.0.0 --port 8002
```

### StoreIt
```bash
# Start PostgreSQL (first time or after reboot)
docker compose -f /home/ai-server2/04-voice-mode-4-loop/storeit/backend/docker-compose.yml up -d

# Apply migrations (first time only)
source /home/ai-server2/04-voice-mode-4-loop/storeit/backend/venv/bin/activate
cd /home/ai-server2/04-voice-mode-4-loop/storeit/backend && alembic upgrade head

# Start server
uvicorn storeit.main:app --host 0.0.0.0 --port 8004
```

### Voice-app (dev, on this machine)
```bash
cd /home/ai-server2/04-voice-mode-4-loop/voice-app
npm run dev  # Vite on :5173
```

### Tests
```bash
# Voice pipeline (322 tests)
source agentic-devops-loop/venv/bin/activate && pytest tests/ -xvs

# Voice-app (110 tests)
cd voice-app && npm test

# BookIt
cd bookit/backend && source venv/bin/activate && pytest tests/ -xvs

# TrackIt (41 tests)
source trackit/backend/venv/bin/activate && pytest trackit/backend/tests/ -xvs

# StoreIt (63 tests — includes PostgreSQL race tests if Docker running)
source storeit/backend/venv/bin/activate && pytest storeit/backend/tests/ -xvs
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
| BookIt backend | `bookit/backend/src/bookit/` |
| BookIt frontend | `bookit/frontend/src/` |
| **TrackIt backend** | `trackit/backend/src/trackit/` |
| **TrackIt tests** | `trackit/backend/tests/` |
| **StoreIt backend** | `storeit/backend/src/storeit/` |
| **StoreIt tests** | `storeit/backend/tests/` |
| **StoreIt migrations** | `storeit/backend/alembic/versions/` |
| **StoreIt docker-compose** | `storeit/backend/docker-compose.yml` |
| systemd services | `/etc/systemd/system/sejfa-*.service` |
