# CLAUDE.md - AI Assistant Guide

> **For Claude Code and other AI assistants working in this repository**

This is an **autonomous development system** that implements Jira tickets using Claude Code in a persistent loop (Ralph Loop), validates with GitHub Actions, and enables AI-powered code review with self-healing capabilities.

## Project Overview

```
Jira Ticket → Claude Code (Ralph Loop) → GitHub Actions → Jules AI Review → Merge
```

**Core Purpose:** Automate the full development cycle from ticket to merged PR with AI assistance.

---

## Quick Reference

### Slash Commands

| Command | Purpose |
|---------|---------|
| `/start-task PROJ-123` | Initialize task from Jira ticket, create branch, setup memory |
| `/finish-task` | Verify completion, create PR, transition Jira |
| `/preflight` | Validate environment before starting work |

### Key Files

| File | Purpose |
|------|---------|
| `docs/CURRENT_TASK.md` | **Persistent memory** - read this first every iteration |
| `docs/GUIDELINES.md` | Agent behavior reference (TDD, patterns, troubleshooting) |
| `.claude/ralph-config.json` | Exit policy and profile configuration |
| `.claude/package-allowlist.json` | Allowed packages for installation |
| `.claude/settings.json` | Hook and permission configuration |

---

## Repository Structure

```
.
├── .claude/                          # Claude Code configuration
│   ├── hooks/                        # Security hooks (PROTECTED)
│   │   ├── pre-tool-use.py          # Package & command validation
│   │   └── stop-hook.py             # Ralph loop exit control
│   ├── commands/                     # Slash command definitions
│   │   ├── start-task.md
│   │   ├── finish-task.md
│   │   └── preflight.md
│   ├── skills/                       # Extended skill documentation
│   ├── plugins/                      # MCP server configurations
│   │   └── agentic-loop/manifest.json  # Jira MCP settings
│   ├── utils/                        # Helper utilities
│   │   ├── sanitize.py              # Prompt injection protection
│   │   └── preflight_check.py       # Environment validation
│   ├── settings.json                # Hook & permission config
│   ├── ralph-config.json            # Exit policy configuration
│   └── package-allowlist.json       # Allowed packages
│
├── .github/                          # GitHub configuration (PROTECTED)
│   ├── CODEOWNERS                   # Protected file rules
│   ├── workflows/
│   │   ├── ci.yml                   # Lint, test, build pipeline
│   │   ├── pr-validation.yml        # PR title/branch validation
│   │   ├── jules-review.yml         # AI code review
│   │   └── self-healing.yml         # Auto-fix on CI failure
│   └── PULL_REQUEST_TEMPLATE.md
│
├── .githooks/                        # Local git hooks
│   ├── commit-msg                   # Validates JIRA-ID: format
│   └── pre-push                     # Validates branch naming
│
├── docs/
│   ├── CURRENT_TASK.md              # Agent persistent memory
│   ├── GUIDELINES.md                # Detailed agent guidance
│   └── QUICKSTART.md                # Setup guide
│
├── scripts/                          # Helper scripts
│   ├── setup-hooks.sh               # Install git hooks
│   ├── create-branch.sh
│   └── create-pr.sh
│
├── Dockerfile                        # Container configuration
├── docker-compose.yml
└── README.md
```

---

## Development Workflow

### The Ralph Loop

When working on a Jira ticket, follow this iterative workflow:

1. **Read** `docs/CURRENT_TASK.md` (your persistent memory)
2. **Check** acceptance criteria progress
3. **Plan** the next small step
4. **Execute** using TDD (test → implement → verify)
5. **Update** CURRENT_TASK.md with progress
6. **Repeat** until all criteria met

### Test-Driven Development (TDD)

**Required workflow:**
```
RED    → Write a failing test first
GREEN  → Write minimal code to pass
REFACTOR → Clean up without breaking tests
```

**Never skip the red phase.** If you can't write a failing test, you don't understand the requirement.

### Exit Conditions

You may ONLY signal completion (`<promise>DONE</promise>`) when:

- [ ] ALL acceptance criteria are checked off
- [ ] ALL tests pass
- [ ] NO linting errors
- [ ] Changes are committed with proper format
- [ ] Branch is pushed to remote

**If ANY condition is false, keep working.**

---

## Git Conventions

### Branch Naming
```
{type}/{JIRA-ID}-{slug}
```
Examples:
- `feature/PROJ-123-add-user-auth`
- `bugfix/PROJ-456-fix-null-pointer`
- `hotfix/PROJ-789-security-patch`

Allowed types: `feature`, `bugfix`, `hotfix`, `refactor`, `docs`

### Commit Messages
```
JIRA-ID: Description
```
Examples:
- `PROJ-123: Implement login endpoint`
- `PROJ-123: Add unit tests for auth service`

Smart commits also supported:
- `PROJ-123 #comment Ready for review`
- `PROJ-123 #in-review`

### PR Titles
```
[JIRA-ID] Description
```
Example: `[PROJ-123] Add user authentication`

---

## Commands & Testing

### Running Tests

```bash
# Python
pytest -xvs                    # Stop on first failure, verbose
pytest --cov=src               # With coverage
pytest path/to/test_file.py    # Single file

# Node
npm test                       # Run all tests
npm test -- path/to/test.js   # Single file
```

### Linting

```bash
# Python
ruff check .                   # Check for issues
ruff check --fix .            # Auto-fix
ruff format .                  # Format code

# Node
npm run lint                   # Check
npm run lint -- --fix         # Auto-fix
```

### Git Operations

```bash
git status                     # Check state
git diff                       # See changes
git add -A                     # Stage all
git commit -m "PROJ-123: Description"
git push -u origin feature/PROJ-123-description
```

---

## Security Rules

### NEVER Do

- Modify `.github/` or `.claude/hooks/` directories
- Install packages not in `.claude/package-allowlist.json`
- Use `sudo`, `eval`, or pipe to shell (`curl | bash`)
- Write to `/etc/` or system directories
- Push with `--force`
- Reset with `--hard`
- Bypass hooks with `--no-verify`

### ALWAYS Do

- Validate input before using
- Use parameterized queries
- Escape output appropriately
- Follow least-privilege principle
- Read existing code before modifying

### Protected Files (Require Human Review)

Files in these paths require human review via CODEOWNERS:
- `/.github/` - All workflow configurations
- `/.claude/hooks/` - Security-critical hooks
- `/Dockerfile`, `docker-compose.yml`
- `/.env`, `/.env.*`, `/secrets/`
- Lock files (`package-lock.json`, `poetry.lock`, etc.)

---

## Package Installation

Only packages in `.claude/package-allowlist.json` can be installed, and versions must be pinned.

**Current Allowlist:**

```json
{
  "policy": { "require_pinned_versions": true },
  "npm": {
    "eslint": ["9.39.2"],
    "jest": ["30.2.0"],
    "vitest": ["*"],
    "@playwright/test": ["*"],
    "prettier": ["*"],
    "typescript": ["*"],
    "@types/*": ["*"]
  },
  "pip": {
    "pytest": ["*"],
    "pytest-cov": ["*"],
    "ruff": ["*"],
    "mypy": ["*"],
    "httpx": ["*"]
  }
}
```

To add packages, edit the allowlist file (requires human review).

---

## Configuration Profiles

The Ralph Loop supports different profiles in `.claude/ralph-config.json`:

### `template_repo` (Current Active)
- For documentation/template repos
- Tests not required
- Markdown lint enabled
- Structure validation enabled

### `code_repo`
- For code repos with test frameworks
- Tests must pass
- 80% coverage threshold
- Full TDD enforcement

---

## Jira Integration

The system uses MCP (Model Context Protocol) to interact with Jira.

**Available Tools:**
- `jira_get_issue` - Fetch ticket details
- `jira_search` - Search for issues
- `jira_transition_issue` - Change ticket status
- `jira_add_comment` - Post comments

**Required Environment Variables:**
```bash
JIRA_URL=https://company.atlassian.net
JIRA_USERNAME=your@email.com
JIRA_API_TOKEN=<your-api-token>
```

---

## GitHub Actions Workflows

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `ci.yml` | Push/PR to main | Lint, test, build, type-check |
| `pr-validation.yml` | PR opened/edited | Validate title, branch, commits |
| `jules-review.yml` | PR opened | AI code review |
| `self-healing.yml` | CI failure | Auto-fix (max 3 retries) |

---

## Code Style

### Python
```python
# Type hints required
def process_data(items: list[str]) -> dict[str, int]:
    """Process items and return counts.

    Args:
        items: List of strings to process

    Returns:
        Dictionary mapping items to their counts
    """
    return {item: items.count(item) for item in set(items)}
```

### TypeScript
```typescript
// Explicit return types
function processData(items: string[]): Record<string, number> {
  return items.reduce((acc, item) => {
    acc[item] = (acc[item] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);
}
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Agent won't exit | Check tests pass, verify acceptance criteria, check `.claude/ralph-state.json` |
| Jira connection fails | Verify `.env` credentials, run `/preflight` |
| Git hooks not working | Run `./scripts/setup-hooks.sh` |
| Package install blocked | Add to `.claude/package-allowlist.json` (requires review) |
| Context lost | Read `docs/CURRENT_TASK.md`, check git log, review acceptance criteria |
| Stuck in loop (>15 iterations) | Re-read criteria, simplify approach, break into smaller tasks |

---

## Key Concepts

| Term | Definition |
|------|------------|
| **Ralph Loop** | Persistent iteration loop that keeps the agent working until exit criteria are met |
| **CURRENT_TASK.md** | Dynamic file serving as agent memory across context windows |
| **Promise Format** | `<promise>DONE</promise>` - exact format required for exit detection |
| **Stop-Hook Flag** | `.claude/.ralph_loop_active` - signals task enforcement is active |
| **Self-Healing** | Automatic retry pipeline when CI fails (max 3 attempts) |
| **MCP** | Model Context Protocol - integration protocol for Jira tools |
| **Sanitization** | Wrapping external data in XML tags to prevent prompt injection |

---

## Communication Standards

### In CURRENT_TASK.md
- Be specific about what was done
- Note any blockers or decisions
- Update iteration count
- Track files modified

### In Commits
- Reference Jira ID
- Describe the "what" and "why"
- Keep under 72 characters for subject

### In PR Description
- Summarize all changes
- Link to Jira ticket
- Note any breaking changes
- Include test instructions

---

## Important Reminders

1. **Read `docs/CURRENT_TASK.md` at the start of every iteration** - it's your persistent memory
2. **Follow TDD strictly** - write failing tests before implementation
3. **Make small, incremental changes** - one logical change per commit
4. **Run tests after every change** - don't let failures accumulate
5. **Update CURRENT_TASK.md frequently** - track your progress
6. **Never modify protected files** - `.github/` and `.claude/hooks/` are off-limits

---

*The goal is working software that meets requirements, not perfection.*
