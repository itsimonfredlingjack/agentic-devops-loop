# Agentic Dev Loop

An autonomous development system where Claude Code implements Jira tickets in a persistent "Ralph Wiggum" loop until tests pass, then pushes to GitHub for AI review.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Agentic Dev Loop                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   Jira ──MCP──> Claude Code (Ralph Loop) ──git──> GitHub Actions    │
│    │                      │                            │             │
│    │                      │                            ▼             │
│    │            docs/CURRENT_TASK.md              Jules Review       │
│    │            (persistent memory)                    │             │
│    │                      │                            │             │
│    └──────────────────────┼────────────────────────────┘             │
│                           │                                          │
│              Stop-Hook validates exit:                               │
│              - Tests pass? ✓                                        │
│              - Lint pass? ✓                                         │
│              - Promise found? ✓                                     │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Configure Environment

```bash
cp .env.example .env
# Edit .env with your Jira credentials
```

### 2. Setup Git Hooks

```bash
./scripts/setup-hooks.sh
```

### 3. Start a Task

```bash
claude
# Then: /start-task PROJ-123
```

### 4. Let it Run

The agent will:
1. Fetch the Jira ticket
2. Create a properly named branch
3. Implement the solution (TDD)
4. Run tests and lint repeatedly
5. Only exit when all criteria pass
6. Push and create a PR

## Components

### Phase 1: Infrastructure ✅

- `.github/CODEOWNERS` - Protects security-critical files
- `.github/workflows/pr-validation.yml` - Validates PR format and commits
- `.githooks/commit-msg` - Enforces commit message format
- `.githooks/pre-push` - Pre-push validation

### Phase 2: MCP Integration ✅

- `.claude/plugins/agentic-loop/manifest.json` - Jira MCP server config
- Environment variables for credentials

**Jira Tools Available:**
- `jira_get_issue` - Fetch ticket details
- `jira_search` - JQL queries
- `jira_transition_issue` - Move ticket status
- `jira_add_comment` - Log agent activity

### Phase 3: Ralph Loop ✅

- `.claude/hooks/stop-hook.py` - Validates exit criteria
- `.claude/ralph-config.json` - Exit policy configuration
- `docs/CURRENT_TASK.md` - Persistent memory file

**Exit Criteria:**
1. All tests pass
2. All linting passes
3. Completion promise found: `<promise>DONE</promise>`
4. Max 25 iterations (hard limit)

### Phase 4-5: GitHub Actions & Jules (TODO)

- Jules AI review on PR
- Self-healing on CI failure

## Directory Structure

```
.
├── .claude/
│   ├── hooks/
│   │   └── stop-hook.py       # Ralph Loop exit validator
│   ├── plugins/
│   │   └── agentic-loop/
│   │       └── manifest.json  # MCP server configuration
│   ├── skills/
│   │   ├── start-task.md      # Initialize task workflow
│   │   └── finish-task.md     # Complete task workflow
│   ├── ralph-config.json      # Exit policy
│   └── settings.json          # Claude Code settings
├── .github/
│   ├── CODEOWNERS             # Security-critical file protection
│   ├── workflows/
│   │   └── pr-validation.yml  # PR and commit validation
│   └── PULL_REQUEST_TEMPLATE.md
├── .githooks/
│   ├── commit-msg             # Commit message validation
│   └── pre-push               # Pre-push checks
├── docs/
│   └── CURRENT_TASK.md        # Persistent task memory
├── scripts/
│   ├── setup-hooks.sh         # Install git hooks
│   ├── create-branch.sh       # Create properly named branch
│   └── create-pr.sh           # Create PR with template
├── .env.example               # Environment template
├── .gitignore
└── README.md
```

## Traceability

All git operations reference the Jira ticket:

- **Branch:** `{type}/{JIRA-ID}-{slug}`
  - Example: `feature/PROJ-123-add-user-auth`
- **Commit:** `{JIRA-ID}: {description}`
  - Example: `PROJ-123: Implements login endpoint`
- **PR Title:** `[{JIRA-ID}] {summary}`
  - Example: `[PROJ-123] Add user authentication`

## Security

### Protected Files (via CODEOWNERS)

These files require human review:
- `.github/` - Workflows, actions
- `.claude/hooks/` - Agent safety constraints
- `Dockerfile`, `docker-compose.yml`
- `.env`, secrets
- Lock files (package-lock.json, etc.)

### Agent Restrictions

The agent CANNOT:
- Modify its own hooks or workflows
- Use `git push --force`
- Use `git reset --hard`
- Approve its own infrastructure changes

## Configuration

### ralph-config.json

```json
{
  "exit_policy": {
    "completion_promise": "<promise>DONE</promise>",
    "max_iterations": 25,
    "requirements": {
      "tests_must_pass": true,
      "lint_must_pass": true
    }
  }
}
```

### Environment Variables

| Variable | Description |
|----------|-------------|
| `JIRA_URL` | Jira Cloud URL (e.g., https://company.atlassian.net) |
| `JIRA_USERNAME` | Jira email address |
| `JIRA_API_TOKEN` | Jira API token |

## Skills

### /start-task

Initializes a new task:
1. Fetches Jira ticket
2. Creates branch
3. Populates CURRENT_TASK.md
4. Transitions Jira to "In Progress"

### /finish-task

Completes a task:
1. Verifies all criteria
2. Creates PR
3. Transitions Jira to "In Review"
4. Outputs completion promise

## Troubleshooting

### Agent Won't Exit

The stop-hook blocks exit until:
1. Tests pass
2. Lint passes
3. `<promise>DONE</promise>` appears in transcript

Check `.claude/ralph-state.json` for iteration count.

### Jira Connection Fails

1. Verify `.env` credentials
2. Check API token permissions
3. Ensure MCP server is configured

### Git Hook Errors

Run `./scripts/setup-hooks.sh` to reinstall hooks.

## Contributing

1. Create a branch following naming convention
2. Make changes
3. Ensure tests pass
4. Create PR with Jira ID

**Note:** Changes to `.github/` or `.claude/hooks/` require human review via CODEOWNERS.

## License

MIT
