# Agentic DevOps Voice — Architecture Overview

## What It Is

A desktop voice app that turns spoken descriptions into Jira tickets. You speak, it transcribes, extracts intent, and creates a structured ticket — end-to-end.

```
┌─────────────────────────────┐         ┌─────────────────────────────┐
│   coffeedev (Mac)           │         │   ai-server2 (Ubuntu)       │
│                             │         │                             │
│   Tauri Desktop App         │  HTTP   │   FastAPI Backend           │
│   ┌───────────────────┐     │ ──────> │   ┌───────────────────┐     │
│   │ React UI (Vite)   │     │  POST   │   │ Whisper (small)   │     │
│   │ Rust audio capture│     │ /api/   │   │ Ollama (qwen2.5)  │     │
│   │ cpal microphone   │     │ transcr │   │ Jira REST API     │     │
│   └───────────────────┘     │         │   └───────────────────┘     │
│                             │ <────── │                             │
│                             │   WS    │   WebSocket /ws/status      │
│                             │ status  │   (real-time pipeline       │
│                             │ updates │    status updates)          │
└─────────────────────────────┘         └─────────────────────────────┘
```

## Two Machines, One Pipeline

### coffeedev — Mac (Frontend + Audio)

| | |
|---|---|
| **Machine** | Apple M4, 16 GB RAM, macOS 26.3 |
| **Role** | Desktop app: mic capture, UI, user interaction |
| **Stack** | Tauri 2, React 18, TypeScript, Zustand, Rust (cpal) |
| **Toolchain** | Node v25.6.1, Rust 1.93.1 |
| **Code path** | `~/Projects/agentic-devops-pipeline-v2/sejfa-voice/voice-app/` |
| **Run** | `npm run tauri dev` |

**What runs here:**
- The Tauri window (native macOS app)
- Vite dev server on `:5173` (React frontend)
- Rust binary captures microphone audio via `cpal` at 16kHz mono
- Emits `mic-level` events (RMS) for live waveform visualization
- Sends captured audio samples to backend via Tauri command → HTTP

### ai-server2 — Ubuntu (Backend + AI)

| | |
|---|---|
| **Machine** | 6 cores, 15 GB RAM, Ubuntu 24.04, NVIDIA RTX 2060 (6 GB VRAM) |
| **Role** | AI pipeline: transcription, intent extraction, ticket creation |
| **Stack** | Python 3.12, FastAPI, Whisper, Ollama, Jira REST API |
| **GPU** | CUDA 12.2, Driver 535 |
| **Code path** | `/home/ai-server2/04-voice-mode-4-loop/voice-app/` (frontend source) |
| | `/home/ai-server2/04-voice-mode-4-loop/agentic-devops-loop/` (backend) |
| **Run backend** | `source venv/bin/activate && uvicorn src.voice_pipeline.main:app --host 0.0.0.0 --port 8000 --reload` |
| **IP** | `192.168.86.36:8000` |

**What runs here:**
- FastAPI server on `:8000`
- Whisper `small` model (GPU) — speech-to-text
- Ollama `qwen2.5-coder-helpful:3b` (GPU) — intent extraction
- Jira ticket creation via REST API
- WebSocket server pushing real-time status to the desktop app
- Also where Claude Code edits the source code (synced to Mac via rsync)

## Data Flow

```
1. User presses Space (or taps button)
   └─ React → Tauri invoke("start_mic")
      └─ Rust: cpal opens mic, captures i16 samples at 16kHz
         └─ Every ~50ms: calculates RMS, emits "mic-level" event
            └─ React: drives waveform bar heights

2. User presses Space again (stop)
   └─ React → Tauri invoke("stop_mic") → returns Vec<i16>
      └─ Shows AudioPreview (SVG waveform, play button)

3. User clicks "Send"
   └─ React → Tauri invoke("send_audio", { samples, serverUrl })
      └─ Rust: encodes WAV, POST multipart to ai-server2:8000/api/transcribe
         └─ Backend: Whisper transcribes → text returned

4. Backend pipeline continues (async, via WebSocket)
   └─ ai-server2: Ollama extracts intent from transcription
      ├─ If ambiguous → WS: "clarification_needed" → ClarificationDialog
      └─ If clear → Jira ticket created → WS: "completed"
         └─ React: SuccessCard with clickable ticket link
```

## Key Files

### Frontend (voice-app/)

| File | Purpose |
|------|---------|
| `src/App.tsx` | Main orchestrator — wires all components, handles toggle/send/clarify |
| `src/stores/pipelineStore.ts` | Zustand store — all app state (status, toasts, ticket result, etc.) |
| `src/lib/ws.ts` | WebSocket client — connects to backend, maps status → processingStep |
| `src/components/RecordButton.tsx` | Record button with timer, waveform, processing spinner |
| `src/components/AudioPreview.tsx` | Post-recording preview with waveform + play/send/discard |
| `src/components/Toast.tsx` | Toast notification overlay (success/error/info) |
| `src/components/SuccessCard.tsx` | Ticket created card with Jira link |
| `src/components/ClarificationDialog.tsx` | Multi-round clarification with numbered questions |
| `src/hooks/useKeyboardShortcuts.ts` | Space=record, Escape=dismiss |
| `src/hooks/useMicLevel.ts` | Listens to Tauri `mic-level` events, rolling buffer |

### Rust (voice-app/src-tauri/)

| File | Purpose |
|------|---------|
| `src/mic.rs` | Microphone capture (cpal), RMS calculation, event emission |
| `src/api.rs` | WAV encoding (hound), HTTP POST to backend (reqwest) |
| `src/lib.rs` | Tauri builder — registers commands, passes AppHandle to MicState |

### Backend (agentic-devops-loop/src/voice_pipeline/)

| File | Purpose |
|------|---------|
| `main.py` | FastAPI app, routes, WebSocket endpoint |
| `transcriber/` | Whisper speech-to-text |
| `intent/` | Ollama intent extraction |
| `jira/` | Jira ticket creation |
| `pipeline/` | Pipeline orchestration + clarification loop |

## Development Workflow

Source code lives on **ai-server2**. Changes are synced to the Mac for Tauri compilation.

```bash
# 1. Edit code on ai-server2 (via Claude Code or SSH)
cd /home/ai-server2/04-voice-mode-4-loop/voice-app

# 2. Verify TypeScript + build
npx tsc --noEmit && npm run build

# 3. Sync to Mac
rsync -avz --exclude node_modules --exclude dist --exclude target --exclude .vite \
  /home/ai-server2/04-voice-mode-4-loop/voice-app/ \
  coffeedev:~/Projects/agentic-devops-pipeline-v2/sejfa-voice/voice-app/

# 4. On Mac: run Tauri dev (npm install if dependencies changed)
ssh coffeedev "cd ~/Projects/.../voice-app && npm run tauri dev"

# 5. Backend (should already be running on ai-server2)
curl -s http://localhost:8000/health
```

## Network

| Connection | From | To | Protocol |
|-----------|------|-----|----------|
| Audio upload | Mac (Tauri) | ai-server2:8000 | HTTP POST multipart |
| Pipeline status | ai-server2:8000 | Mac (React) | WebSocket |
| Clarification | Mac (React) | ai-server2:8000 | HTTP POST JSON |
| Jira | ai-server2 | Atlassian Cloud | HTTPS REST |
| Code sync | ai-server2 | Mac | rsync over SSH |

## Git

- **Repo:** `github.com/itsimonfredlingjack/agentic-devops-loop`
- **Branch:** `feature/voice-app-glassmorphism`
- **Monorepo:** `voice-app/` (frontend) + `agentic-devops-loop/` (backend) share the same repo
