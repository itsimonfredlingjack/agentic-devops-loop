# Agentic Dev Loop - Technical Specification

> A complete autonomous development system powered by Claude Code, GitHub Actions, and Jira integration.

---

## Table of Contents

1. [Ralph Wiggum Technique](#ralph-wiggum-technique)
2. [MCP Servers](#mcp-servers)
3. [Claude Code Hooks](#claude-code-hooks)
4. [Skills & Commands](#skills--commands)
5. [Security & Permissions](#security--permissions)
6. [GitHub Actions Workflows](#github-actions-workflows)
7. [Git Hooks](#git-hooks)
8. [Configuration Files](#configuration-files)
9. [Docker Setup](#docker-setup)
10. [Directory Structure](#directory-structure)

---

## Ralph Wiggum Technique

The **Ralph Loop** (named after Ralph Wiggum's "I'm helping!" energy) is an autonomous iteration system that allows Claude Code to work independently through complex tasks.

### Core Concept

```
┌─────────────────────────────────────────────────────────────┐
│                    RALPH LOOP CYCLE                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   /start-task PROJ-123                                      │
│         │                                                   │
│         ▼                                                   │
│   ┌─────────────────┐                                       │
│   │  Read Context   │◄─────────────────────┐                │
│   │  CURRENT_TASK   │                      │                │
│   └────────┬────────┘                      │                │
│            │                               │                │
│            ▼                               │                │
│   ┌─────────────────┐                      │                │
│   │  Do Work        │                      │                │
│   │  (TDD cycle)    │                      │                │
│   └────────┬────────┘                      │                │
│            │                               │                │
│            ▼                               │                │
│   ┌─────────────────┐     NO              │                │
│   │  Exit Check     │──────────────────────┘                │
│   │  (Stop Hook)    │                                       │
│   └────────┬────────┘                                       │
│            │ YES                                            │
│            ▼                                                │
│   ┌─────────────────┐                                       │
│   │  <promise>DONE  │                                       │
│   │  </promise>     │                                       │
│   └─────────────────┘                                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Exit Criteria

The loop only exits when **ALL** conditions are met:

| Criterion | Description |
|-----------|-------------|
| `<promise>DONE</promise>` | Completion marker in output |
| Tests pass | All tests green (if `tests_must_pass: true`) |
| Lint passes | No linting errors |
| Max iterations | Hard limit (default: 25) |

### Configuration

**File:** `.claude/ralph-config.json`

```json
{
  "active_profile": "template_repo",
  "profiles": {
    "template_repo": {
      "exit_policy": {
        "completion_promise": "<promise>DONE</promise>",
        "max_iterations": 25,
        "requirements": {
          "tests_must_pass": false,
          "lint_must_pass": true
        }
      }
    },
    "code_repo": {
      "exit_policy": {
        "requirements": {
          "tests_must_pass": true,
          "coverage_threshold": 80
        }
      }
    }
  },
  "task_memory": {
    "file": "docs/CURRENT_TASK.md",
    "read_on_start": true,
    "update_on_iteration": true
  },
  "self_healing": {
    "enabled": true,
    "max_retries": 3,
    "retry_on": ["test_failure", "lint_failure", "ci_failure"]
  }
}
```

### Persistent Memory

**File:** `docs/CURRENT_TASK.md`

This file persists context across iterations:
- Active Jira ticket ID
- Branch name
- Acceptance criteria checklist
- Implementation progress
- Blockers and decisions
- Files modified

---

## MCP Servers

Model Context Protocol (MCP) servers extend Claude Code's capabilities.

### Project-Specific MCPs

| Server | Purpose | Config Location |
|--------|---------|-----------------|
| **Jira MCP** | Jira ticket CRUD, transitions, comments | `~/.claude.json` (project scope) |

#### Jira MCP

**Package:** `@anthropic/jira-mcp`

**Tools:**
- `jira_get_issue` - Fetch ticket details
- `jira_search` - JQL search
- `jira_transition_issue` - Change ticket status
- `jira_add_comment` - Add comments to tickets

**Configuration:**
```json
{
  "jira-mcp": {
    "type": "stdio",
    "command": "npx",
    "args": ["-y", "@anthropic/jira-mcp"],
    "env": {
      "JIRA_URL": "https://your-domain.atlassian.net",
      "JIRA_EMAIL": "your-email@example.com",
      "JIRA_API_TOKEN": "<from .env>"
    }
  }
}
```

### Global MCPs (Available in Session)

These are configured at user/system level, not project-specific:

| Server | Purpose |
|--------|---------|
| **Serena** | Semantic code analysis, symbol navigation, refactoring |
| **Playwright** | Browser automation, screenshots, testing |
| **Context7** | Documentation lookup for libraries |
| **Supermemory** | Persistent memory across sessions |

### Plugin System

**Location:** `.claude/plugins/`

Custom MCP definitions via `manifest.json`:

```json
{
  "name": "agentic-loop",
  "version": "1.0.0",
  "mcpServers": {
    "jira": {
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-server-atlassian", "jira"],
      "env": ["JIRA_URL", "JIRA_USERNAME", "JIRA_API_TOKEN"]
    }
  }
}
```

---

## Claude Code Hooks

Hooks intercept tool calls for validation and control.

### PreToolUse Hook

**File:** `.claude/hooks/pre-tool-use.py`

**Triggers on:** `Bash`, `Write`, `Edit`

**Validates:**
- Package installations against allowlist
- File paths (blocks protected paths)
- Shell commands (blocks dangerous patterns)

**Blocked Patterns:**
```python
DANGEROUS_PATTERNS = [
    r'curl.*\|.*bash',      # Remote code execution
    r'wget.*\|.*bash',
    r'eval\s*\(',           # Arbitrary code execution
    r'rm\s+-rf\s+/',        # Destructive deletion
    r':\(\)\{.*\}',         # Fork bombs
    r'>\s*/dev/sd',         # Direct disk writes
    r'mkfs\.',              # Filesystem formatting
]
```

**Protected Paths:**
- `.github/` - Workflow tampering
- `.claude/hooks/` - Security bypass
- `.env` - Credential exposure
- `Dockerfile`, `docker-compose.yml`
- Lock files (`package-lock.json`, etc.)

### Stop Hook

**File:** `.claude/hooks/stop-hook.py`

**Triggers on:** Every tool call completion (`*` matcher)

**Purpose:** Enforces Ralph Loop exit criteria

**Logic:**
1. Check for `.claude/.ralph_loop_active` flag
2. If active, scan last N characters for `<promise>DONE</promise>`
3. If found, allow exit
4. If not found, increment iteration counter
5. If max iterations reached, force exit with warning

**State Files:**
- `.claude/ralph-state.json` - Iteration counter
- `.claude/.ralph_loop_active` - Loop activation flag
- `.claude/.promise_done` - Completion flag

---

## Skills & Commands

### Skills (AI-Invoked Workflows)

**Location:** `.claude/skills/`

| Skill | File | Description |
|-------|------|-------------|
| `/start-task` | `start-task.md` | Initialize task from Jira |
| `/finish-task` | `finish-task.md` | Complete and close task |

#### /start-task JIRA_ID

1. Fetch Jira ticket details
2. Create feature branch (`{type}/{JIRA_ID}-{slug}`)
3. Initialize `docs/CURRENT_TASK.md`
4. Transition Jira to "In Progress"
5. Reset Ralph Loop state
6. Add "Work started" comment to Jira

#### /finish-task

1. Validate all acceptance criteria met
2. Run final test/lint pass
3. Commit remaining changes
4. Push to remote
5. Create/update PR
6. Transition Jira to "Review"
7. Add PR link to Jira comment

### Commands (User-Invoked)

**Location:** `.claude/commands/`

| Command | File | Description |
|---------|------|-------------|
| `/start-task` | `start-task.md` | Same as skill |
| `/finish-task` | `finish-task.md` | Same as skill |
| `/preflight` | `preflight.md` | Validate environment setup |

#### /preflight

Validates:
- `.env` file exists with required vars
- Git configured correctly
- Jira connectivity
- Python/Node available
- Hooks installed

---

## Security & Permissions

### Permission Model

**File:** `.claude/settings.json`

```json
{
  "permissions": {
    "allow": [
      "Bash(pytest*)",
      "Bash(npm test*)",
      "Bash(ruff*)",
      "Bash(eslint*)",
      "Bash(git status*)",
      "Bash(git diff*)",
      "Bash(git log*)",
      "Bash(git add*)",
      "Bash(git commit*)",
      "Bash(git checkout*)",
      "Bash(git push*)",
      "Bash(gh pr*)"
    ],
    "deny": [
      "Bash(rm -rf /)",
      "Bash(git push --force*)",
      "Bash(git reset --hard*)",
      "Bash(*| bash*)",
      "Bash(*eval*)",
      "Bash(sudo *)",
      "Edit(.claude/hooks/*)",
      "Edit(.github/*)",
      "Write(.claude/hooks/*)",
      "Write(.github/*)"
    ]
  }
}
```

### Package Allowlist

**File:** `.claude/package-allowlist.json`

Only these packages can be installed by the agent. Versions must be pinned when `policy.require_pinned_versions` is enabled; use `"*"` to allow any pinned version.

**npm:**
- `jest` (pinned), `eslint` (pinned)
- `vitest`, `@playwright/test`, `prettier`, `typescript`
- `@types/*` (wildcard for DefinitelyTyped)

**pip:**
- `pytest`, `pytest-cov`
- `ruff`, `mypy`
- `httpx`

Example:

```json
{
  "policy": { "require_pinned_versions": true },
  "npm": { "jest": ["30.2.0"], "@types/*": ["*"] },
  "pip": { "pytest": ["*"] }
}
```

### CODEOWNERS Protection

**File:** `.github/CODEOWNERS`

```
# Security-critical files require manual review
/.github/         @security-team
/.claude/hooks/   @security-team
/.env*            @security-team
Dockerfile        @security-team
docker-compose*   @security-team
```

---

## GitHub Actions Workflows

**Location:** `.github/workflows/`

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `ci.yml` | Push, PR | Lint → Type Check → Test → Build |
| `pr-validation.yml` | PR | Title, commit, branch format validation |
| `jules-review.yml` | PR | AI code review via Jules |
| `self-healing.yml` | CI failure | Auto-fix and retry (max 3x) |
| `pages.yml` | Push to main | Deploy docs to GitHub Pages |

### CI Pipeline

```yaml
jobs:
  lint:
    - ruff check . (Python)
    - eslint . (JS/TS)
  
  type-check:
    - mypy . (Python)
    - tsc --noEmit (TS)
  
  test:
    - pytest --cov
    - npm test
  
  build:
    - python -m build
    - npm run build
```

### Self-Healing

On CI failure:
1. Dispatch new Claude Code session
2. Analyze failure logs
3. Attempt auto-fix
4. Commit fix and retry CI
5. Max 3 attempts, then alert human

---

## Git Hooks

**Location:** `.githooks/`

**Installation:** `./scripts/setup-hooks.sh`

| Hook | File | Validates |
|------|------|-----------|
| `pre-push` | `pre-push` | Branch naming: `{type}/{JIRA_ID}-{slug}` |
| `commit-msg` | `commit-msg` | Commit format: `{JIRA_ID}: {description}` |

### Branch Naming

**Pattern:** `{type}/{JIRA_ID}-{slug}`

**Allowed types:**
- `feature/` - New functionality
- `bugfix/` - Bug fixes
- `hotfix/` - Production fixes
- `refactor/` - Code improvements
- `docs/` - Documentation only

**Examples:**
- `feature/PROJ-123-add-csv-export`
- `bugfix/PROJ-456-fix-login-error`

### Commit Message Format

**Pattern:** `{JIRA_ID}: {description}`

**Examples:**
- `PROJ-123: Add CSV export to dashboard`
- `PROJ-123: Fix test for edge case`

---

## Configuration Files

| File | Purpose |
|------|---------|
| `.claude/settings.json` | Hooks, permissions |
| `.claude/ralph-config.json` | Ralph Loop exit policy |
| `.claude/package-allowlist.json` | Allowed packages |
| `.claude/ralph-state.json` | Iteration counter (runtime) |
| `.env` | Credentials (git-ignored) |
| `.env.example` | Credential template |

---

## Docker Setup

### Multi-Stage Build

**File:** `Dockerfile`

```dockerfile
# Base stage - runtime dependencies
FROM python:3.12-slim AS base

# Development stage - dev tools + Claude CLI
FROM base AS development
RUN pip install pytest ruff mypy
# ... install Claude CLI

# Production stage - minimal runtime
FROM base AS production
COPY --from=development /app /app
```

### Compose Services

**File:** `docker-compose.yml`

```yaml
services:
  agent:
    build:
      target: development
    volumes:
      - .:/workspace
      - ~/.claude.json:/root/.claude.json:ro
    environment:
      - GIT_AUTHOR_NAME
      - GIT_AUTHOR_EMAIL
```

---

## Directory Structure

```
agentic-dev-loop/
├── .claude/
│   ├── hooks/
│   │   ├── pre-tool-use.py      # Security validation
│   │   └── stop-hook.py         # Ralph Loop control
│   ├── skills/
│   │   ├── start-task.md        # Task initialization
│   │   └── finish-task.md       # Task completion
│   ├── commands/
│   │   ├── start-task.md
│   │   ├── finish-task.md
│   │   └── preflight.md
│   ├── plugins/
│   │   └── agentic-loop/
│   │       └── manifest.json    # MCP plugin definition
│   ├── settings.json            # Hooks & permissions
│   ├── ralph-config.json        # Exit policy
│   ├── package-allowlist.json   # Allowed packages
│   └── ralph-state.json         # Runtime state
│
├── .github/
│   ├── workflows/
│   │   ├── ci.yml
│   │   ├── pr-validation.yml
│   │   ├── jules-review.yml
│   │   ├── self-healing.yml
│   │   └── pages.yml
│   ├── CODEOWNERS
│   └── PULL_REQUEST_TEMPLATE.md
│
├── .githooks/
│   ├── pre-push
│   └── commit-msg
│
├── docs/
│   ├── CURRENT_TASK.md          # Persistent task memory
│   ├── GUIDELINES.md            # Agent behavior guide
│   ├── QUICKSTART.md            # Setup instructions
│   ├── SPEC.md                  # This file
│   ├── guide/                   # Web guide
│   └── monitor/                 # Visual monitor
│
├── scripts/
│   ├── setup-hooks.sh
│   ├── create-branch.sh
│   └── create-pr.sh
│
├── .env.example                 # Credential template
├── .gitignore
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## Quick Reference

### Start Working

```bash
# 1. Setup credentials
cp .env.example .env
# Edit .env with your Jira credentials

# 2. Install hooks
./scripts/setup-hooks.sh

# 3. Verify setup
/preflight

# 4. Start a task
/start-task PROJ-123

# 5. Work autonomously (Ralph Loop)
# ... Claude works ...

# 6. Complete task
/finish-task
```

### Environment Variables

| Variable | Description |
|----------|-------------|
| `JIRA_URL` | Jira instance URL |
| `JIRA_EMAIL` | Jira account email |
| `JIRA_API_TOKEN` | Jira API token |

### Runtime Files

| File | Purpose | Git-tracked |
|------|---------|-------------|
| `.claude/ralph-state.json` | Iteration counter | No |
| `.claude/.ralph_loop_active` | Loop flag | No |
| `.claude/.promise_done` | Completion flag | No |
| `.claude/ralph-loop.log` | Loop log | No |
| `docs/CURRENT_TASK.md` | Task memory | Yes |

---

*Last updated: 2025-01-23*
