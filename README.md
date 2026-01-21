# Agentic Dev Loop 🤖

> **Autonomous development:** Jira ticket → Claude Code → GitHub PR → Jules review → Merge

An autonomous development system where AI implements Jira tickets in a persistent loop until tests pass, then creates PRs for AI-powered code review.

[![CI](https://img.shields.io/badge/CI-GitHub%20Actions-blue)](/.github/workflows/ci.yml)
[![Jules](https://img.shields.io/badge/Review-Jules%20AI-green)](/.github/workflows/jules-review.yml)
[![Self-Healing](https://img.shields.io/badge/Self--Healing-Enabled-orange)](/.github/workflows/self-healing.yml)

---

## How It Works

```
┌─────────┐     ┌─────────────────┐     ┌──────────────┐     ┌───────┐
│  Jira   │────▶│  Claude Code    │────▶│ GitHub Actions│────▶│ Merge │
│ Ticket  │     │  (Ralph Loop)   │     │  + Jules AI   │     │       │
└─────────┘     └─────────────────┘     └──────────────┘     └───────┘
     │                  │                      │
     │                  ▼                      │
     │         CURRENT_TASK.md                 │
     │        (Persistent Memory)              │
     │                                         │
     └─────────────────────────────────────────┘
                    Self-Healing
```

1. **Create** a Jira ticket with acceptance criteria
2. **Run** `/start-task PROJ-123` in Claude Code
3. **Watch** as the agent implements using TDD
4. **Review** the auto-generated PR (with Jules AI assist)
5. **Merge** when satisfied

---

## Quick Start

```bash
# 1. Configure credentials
cp .env.example .env
# Edit .env with your Jira details

# 2. Install git hooks
./scripts/setup-hooks.sh

# 3. Start Claude and begin
claude
# Then: /start-task PROJ-123
```

📖 **Full guide:** [docs/QUICKSTART.md](docs/QUICKSTART.md)

---

## Features

### ✅ All Phases Complete

| Phase | Component | Status |
|-------|-----------|--------|
| **1. Infrastructure** | CODEOWNERS, git hooks, PR validation | ✅ |
| **2. MCP Integration** | Jira tools (get, search, transition, comment) | ✅ |
| **3. Ralph Loop** | Stop-hook, exit policy, persistent memory | ✅ |
| **4. Jules Review** | AI code review on PRs | ✅ |
| **5. Self-Healing** | Auto-fix on CI failures (max 3 retries) | ✅ |
| **6. Security** | PreToolUse validation, prompt injection protection | ✅ |
| **7. Init Flow** | /start-task, TDD workflow, GUIDELINES.md | ✅ |

### 🔒 Security

- **CODEOWNERS** protects `.github/` and `.claude/hooks/`
- **PreToolUse hook** validates package installs against allowlist
- **Dangerous commands blocked:** `curl | bash`, `eval`, `sudo`, etc.
- **Prompt injection protection** for external data (Jira descriptions)
- **Container isolation** available via Docker

### 🔄 Ralph Loop Exit Criteria

The agent **cannot exit** until:
- ✅ All tests pass
- ✅ No linting errors
- ✅ Completion promise found
- ⏱️ Or max 25 iterations reached

### 📊 Traceability

Every git operation references Jira:
- **Branch:** `feature/PROJ-123-description`
- **Commit:** `PROJ-123: Implements feature X`
- **PR Title:** `[PROJ-123] Add feature X`

---

## File Structure

```
.
├── .claude/
│   ├── hooks/           # Stop-hook + PreToolUse security
│   ├── plugins/         # Jira MCP configuration
│   ├── skills/          # /start-task, /finish-task
│   └── settings.json    # Claude Code config
├── .github/
│   ├── CODEOWNERS       # Protected file rules
│   └── workflows/       # CI, Jules, Self-healing
├── docs/
│   ├── CURRENT_TASK.md  # Agent persistent memory
│   ├── GUIDELINES.md    # Agent behavior reference
│   └── QUICKSTART.md    # This guide
└── scripts/             # Helper scripts
```

---

## Configuration

### Environment Variables

| Variable | Description |
|----------|-------------|
| `JIRA_URL` | `https://company.atlassian.net` |
| `JIRA_USERNAME` | Your Jira email |
| `JIRA_API_TOKEN` | API token from Atlassian |

### Package Allowlist

Edit `.claude/package-allowlist.json` to allow project-specific packages:

```json
{
  "npm": ["react", "next", "tailwindcss"],
  "pip": ["django", "celery", "redis"]
}
```

### Ralph Loop Config

Edit `.claude/ralph-config.json`:

```json
{
  "exit_policy": {
    "max_iterations": 25,
    "completion_promise": "<promise>DONE</promise>"
  }
}
```

---

## GitHub Actions

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `pr-validation.yml` | PR opened | Validate title, commits, branch |
| `ci.yml` | Push/PR | Lint, test, build |
| `jules-review.yml` | PR opened | AI code review |
| `self-healing.yml` | CI failure | Auto-fix attempts |

---

## Docker (Optional)

Run the agent in an isolated container:

```bash
docker compose up -d
docker compose exec agent bash
# Now run claude inside container
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Agent won't exit | Check tests pass, check `.claude/ralph-state.json` |
| Jira connection fails | Verify `.env` credentials |
| Git hooks not working | Run `./scripts/setup-hooks.sh` |
| Package install blocked | Add to `.claude/package-allowlist.json` |

---

## Contributing

1. Create branch: `feature/PROJ-123-description`
2. Make changes
3. Commit: `PROJ-123: Description`
4. Create PR

**Note:** Changes to `.github/` or `.claude/hooks/` require human review.

---

## License

MIT

---

**Built with Claude Code** 🤖
