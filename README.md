# Agentic Dev Loop 🚀

> **The Infinite Loop of Autonomous Creation**
> *Where Claude builds, Jules heals, and code writes itself.*

![Build Status](https://github.com/itsimonfredlingjack/agentic-dev-loop-w-claude-code-and-github-actions/actions/workflows/ci.yml/badge.svg)
[![AI: Google Jules](https://img.shields.io/badge/AI-Google_Jules-blue.svg)](/.github/workflows/jules-review.yml)
[![Agent: Claude Code](https://img.shields.io/badge/Agent-Claude_Code-orange.svg)](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/overview)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Vibe: Immaculate](https://img.shields.io/badge/Vibe-Immaculate-purple.svg)](https://github.com/itsimonfredlingjack)

---

## 🌟 What is the Agentic Dev Loop Magic?

Welcome to the future of software engineering. This isn't just a repository; it's a **Cybernetic Development Ecosystem**.

We have fused **Claude Code (Ralph)**—the relentless builder—with **Google Jules**—the omniscient guardian—to create a self-sustaining loop of creation. You drop a Jira ticket, and the system springs to life: coding, testing, reviewing, and **fixing its own mistakes**.

It is **Self-Healing Infrastructure** meets **Autonomous Velocity**. 🦾💜⚡

---

## 🏗️ The Autonomous Flow

```mermaid
graph TD
    A([Dev Input]) --> B(Claude Code)
    B --> C(PR)
    C --> D(GitHub Actions)
    D --> E{👀 Failure?}
    E -->|Yes| F([Jules Analysis])
    F --> G(Auto-Fix)
    G --> H(Merge)
    E -->|No| H
```
## 🔄 End-to-End Pipeline - In Detail

The full journey from idea to production looks like this:

```
1. Jira ticket (GE-xxx)
        │
        ▼
2. /start-task GE-xxx
   → Claude Code fetches ticket via Jira REST API
   → Creates branch: feature/GE-xxx-slug
   → Populates docs/CURRENT_TASK.md
        │
        ▼
3. Ralph Loop (TDD)
   → Red: writes a failing test
   → Green: minimal implementation
   → Refactor
   → Updates CURRENT_TASK.md
   → Commit: "GE-xxx: description"
   → Repeats until all acceptance criteria ✓
        │
        ▼
4. /finish-task
   → Pushes branch → Creates PR
   → CI runs (lint, test on Python 3.10–3.13, security scan)
   → Jules performs AI code review
        │
        ▼
5. Merge to main
        │
        ▼
6. deploy.yml triggers automatically
   → Docker build → Push to ACR → Deploy to Azure Container Apps
        │
        ▼
7. App is live on Azure
```

### What Happens After Deploy

Every time a PR is merged to `main`:
- `deploy.yml` builds a new Docker image tagged with the commit SHA + `latest`.
- The image is pushed to **Azure Container Registry (ACR)**.
- **Azure Container Apps** automatically rolls out the new revision with zero-downtime deployment.

This means the app is continuously deployed — it is not rebuilt from scratch each time. Every merge delivers an incremental update to the same running application.

### Viewing the Live App

To find the application URL:
1. **Azure Portal** → Container Apps → your app → Overview → *Application Url*
2. Or via CLI:
   ```bash
   az containerapp show \
     --name <APP_NAME> \
     --resource-group <RESOURCE_GROUP> \
     --query properties.configuration.ingress.fqdn
   ```

---

## 🔥 Key Features

| Feature | Benefit |
|---------|---------|
| 🤖 **Self-Healing Pipelines** | **Jules** detects CI failures (linting, tests) and hot-patches the code automatically. Zero human latency. |
| ⚡ **The Infinite Loop** | A perpetual engine of productivity: Jira Ticket ➡️ Claude Dev ➡️ PR ➡️ Jules Review ➡️ Merge. |
| 🛡️ **AI Security Guardrails** | Built-in protection against prompt injection and unsafe package installs. **Jules** watches the watchmen. |
| 🧠 **Persistent Memory** | The **Ralph Loop** remembers context across sessions via `CURRENT_TASK.md`. It never forgets. |
| 🚀 **Next-Gen Velocity** | Skip the boilerplate. Focus on the architecture while the agents handle the implementation details. |

---

## 🚀 Launch the Beast

Initialize the autonomous core.

### 1. Clone the Matrix
```bash
git clone https://github.com/itsimonfredlingjack/agentic-dev-loop-w-claude-code-and-github-actions.git
cd agentic-dev-loop-w-claude-code-and-github-actions
```

### 2. Inject Credentials
```bash
cp .env.example .env
# Open .env and insert your JIRA_API_TOKEN and Agent Secrets
```

### 3. Arm the Hooks
```bash
./scripts/setup-hooks.sh
```

### 4. Ignite the Engine
```bash
claude
# Inside the session: /start-task PROJ-123
```

---

## 📁 Directory Structure

```
agentic-dev-loop/
├── .claude/               # 🧠 The Brain (Ralph Config & Memory)
│   ├── hooks/             # Security enforcement protocols
│   └── plugins/           # Integrations (MCP optional)
├── .github/workflows/     # ⚡ The Nervous System
│   ├── jules-review.yml   # AI Code Reviewer
│   └── self-healing.yml   # Auto-Remediation Logic
├── docs/                  # 📜 Knowledge Base
│   ├── CURRENT_TASK.md    # Active Working Memory
│   └── monitor/           # Real-time Status Dashboard
├── document_upload_app/   # 📦 Sample Workload
├── scripts/               # 🛠️ Utility Belts
└── src/                   # 🧬 Source Code
```

---
---

## 🤝 Join the Revolution

<div align="center">

**[⭐ Star this Repo](https://github.com/itsimonfredlingjack/agentic-dev-loop-w-claude-code-and-github-actions)**

*Architected for Dominance. Built for 2077.*

</div>

<!-- Tracking: [PROJ-123] v3 -->

---

## 🛠 Development Resources

<details>
<summary><strong>📋 Click here to copy the Flask TDD Prompt Template</strong></summary>

### How to use this template
Copy the markdown below into a new Jira ticket or Claude prompt to start a new micro-service assignment.

***

# 🚀 Uppdrag: Flask TDD - [APP_NAME]

**Mål:** Bygg en Flask-applikation enligt strikt 3-lagersarkitektur med TDD.
**Prioritet:** 1. Tester (röda -> gröna). 2. Minimal implementation.

## 🛠 Konfiguration (Fyll i detta)

| Variabel | Värde |
| :--- | :--- |
| **App Name** | `[APP_NAME]` |
| **Modell** | `[CATEGORY]` (t.ex. FINANCE) |
| **Fält** | `[LIST_OF_FIELDS]` (t.ex. id:int, title:str) |
| **Service** | `[SERVICE_NAME]` (t.ex. LibraryService) |
| **Affärsregler** | 1. `[RULE_1]`<br>2. `[RULE_2]` |
| **Routes** | `GET /`, `POST /add`, `[OTHER_ROUTE]` |

## 📋 Regler & Setup

* **Språk:** Kod/Kommentarer på **Engelska**. UI/Felmeddelanden på **Svenska**.
* **Databas:** `sqlite:///:memory:` för tester.
* **Dependency Injection:** Måste användas. Service tar repository i `__init__`.

## 🏗 Arkitektur (LÅST)

Du måste följa denna struktur exakt (Clean Architecture):

1.  **Application Factory:** `create_app(config)` i `app/__init__.py`.
2.  **Lager 1: Data (`app/data/`)**
    * Modell (Dataclass/SQLAlchemy).
    * Repository-protokoll (Abstract Base Class).
    * `InMemoryRepository` (för tester/MVP).
3.  **Lager 2: Business (`app/business/`)**
    * Ren Python-klass (Service).
    * Får **aldrig** bero på Flask eller HTTP.
    * Repository injiceras i konstruktorn.
4.  **Lager 3: Presentation (`app/presentation/`)**
    * Flask Blueprint.
    * Hanterar HTTP (request/response), Templates, Forms.
    * Service injiceras via `app.config` eller factory-mönster.

## ✅ Acceptance Criteria

### Fas 1: Core & Business Logic (Unit Tests)
- [ ] Projektstruktur skapad.
- [ ] `[MODEL_NAME]` implementerad.
- [ ] Repository-protokoll + `InMemoryRepository` skapat.
- [ ] `[SERVICE_NAME]` implementerad med DI.
- [ ] **TEST:** Unit-tester (pytest) verifierar alla affärsregler utan Flask.

### Fas 2: Integration & Web (Integration Tests)
- [ ] `create_app` konfigurerar Flask och injicerar dependencies.
- [ ] Templates (`base.html` + sidor) skapade med svensk text.
- [ ] Routes implementerade i Blueprint.
- [ ] **TEST:** Integrationstester verifierar flöden och HTTP-statuskoder.
- [ ] `pytest` körs grönt. `ruff check .` passerar.

***

</details>
