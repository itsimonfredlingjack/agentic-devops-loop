# agentic-devops-loop

> "From Jira Ticket to Production — Untouched by Human Hands."

![Agentic Loop](static/img/SEJFA-AGENTIC-DEVOPS-LOOP-MAIN-PICTURE.jpeg)

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0.0-black?style=for-the-badge&logo=flask&logoColor=white)
![Azure](https://img.shields.io/badge/Azure-Container%20Apps-0078D4?style=for-the-badge&logo=microsoftazure&logoColor=white)
![Jira](https://img.shields.io/badge/Jira-Integration-0052CC?style=for-the-badge&logo=jira&logoColor=white)

**Built by Simon Fredling Jack**
*Originally a school group project (SEJFA), now evolved into a solo autonomous DevOps experiment.*

---

## ⚡ What It Does

This isn't just a web app. It's an **autonomous software engineer**.

You create a ticket in Jira. **The Agent** wakes up.
It reads the requirements. It writes the code. It writes the tests.
It runs the tests. It fails. It fixes the code. It passes.
It opens a PR. CI runs. It merges. It deploys to Azure.

**You do nothing.**

> "The goal is to make myself obsolete."

---

## 🔄 The Ralph Loop

The core engine is the **Ralph Loop** — a strict TDD cycle enforced by the agent. It doesn't guess; it proves.

```text
START TASK
   │
   ▼
┌──────────────────┐
│  🔴 RED PHASE    │  <-- Write failing test
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  🟢 GREEN PHASE  │  <-- Write minimal code to pass
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  🔵 REFACTOR     │  <-- Clean up mess
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  🛡️ VERIFY       │  <-- Lint, Security, Type Check
└────────┬─────────┘
         │
   [ All Pass? ]──▶ NO ──┐
         │               │
         YES ────────────┘
         │
         ▼
    FINISH TASK
```

---

## 💻 Tech Stack

```bash
$ cat system_info.txt

CORE:
  Language:       Python 3.10
  Framework:      Flask (Async)
  Realtime:       Socket.IO

INFRASTRUCTURE:
  Cloud:          Azure Container Apps
  Registry:       Azure Container Registry
  CI/CD:          GitHub Actions

INTEGRATIONS:
  Project Mgmt:   Jira API
  AI Agent:       Claude Code
  Notifications:  Slack / Teams

TOOLS:
  Container:      Docker
  Linting:        Ruff
  Testing:        Pytest
```

---

## 🚀 Quick Start

Initialize the autonomous environment.

```bash
# 1. Clone the repo
git clone https://github.com/itsimonfredlingjack/agentic-devops-loop.git
cd agentic-devops-loop

# 2. Ignite the venv
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment
cp .env.example .env
# (Add your JIRA_API_TOKEN and AZURE_CREDENTIALS)

# 5. Launch the monitor
python app.py
```

---

## 🏗️ Architecture

A visualized flow of the autonomous pipeline.

```text
[ JIRA TICKET ]
      │
      │ (WebHook)
      ▼
[ AGENT WAKES UP ] ───▶ [ READS REQ ]
      │
      ▼
[ WRITES CODE ] ◀──┐
      │            │ (Fix)
      ▼            │
[ RUNS TESTS ] ────┘
      │
      │ (Pass)
      ▼
[ OPENS PR ] ──▶ [ GITHUB ACTIONS ] ──▶ [ AZURE DEPLOY ]
                                             │
                                             ▼
                                     [ LIVE ON CLOUD ]
```

<div align="center">
  <img src="static/img/SEJFA-CHAOS-VS-CLARITY.jpeg" width="600" alt="Chaos vs Clarity">
  <p><em>The Agent turns chaos into structured, deployed reality.</em></p>
</div>

---

## 📂 Project Structure

```text
.
├── .claude/                # The Brain (Agent Config & Skills)
├── src/
│   ├── sejfa/              # Core Logic (The "Employee")
│   ├── expense_tracker/    # Sample Business App
│   └── utils/              # Shared Tooling
├── scripts/                # Automation Scripts
├── tests/                  # 370+ Unit & Integration Tests
├── Dockerfile              # Container Definition
└── app.py                  # Entry Point
```

---

## 🤖 How to Use the Agent

You interact with the agent via the terminal using the `claude` CLI with custom skills.

```console
user@devbox:~$ claude -i start-task PROJ-123
> 🤖 AGENT: Ticket PROJ-123 received. "Add dark mode toggle".
> 🤖 AGENT: Branch feature/PROJ-123-dark-mode created.
> 🤖 AGENT: Starting Ralph Loop...

user@devbox:~$ claude -i finish-task
> 🤖 AGENT: Tests passed (34/34).
> 🤖 AGENT: Linter clean.
> 🤖 AGENT: PR #42 created.
> 🤖 AGENT: Jira ticket updated to "In Review".
```

<details>
<summary><strong>🔍 Deep Dive: The Philosophy</strong></summary>

> We built this to answer one question: **Can AI completely replace the junior developer loop?**
>
> The answer is yes, but only with strict guardrails. The **Ralph Loop** isn't just a methodology; it's a programmatic constraint. The agent *cannot* push code that hasn't passed the Red-Green-Refactor cycle. It's TDD enforced by code, executed by AI.

</details>

---

## 📜 License

MIT License. Hack away.
