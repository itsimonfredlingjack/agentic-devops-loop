---
name: preflight
description: Validate that system is ready for /start-task
args: none
---

# Preflight Command

This command checks all prerequisites for starting a new task.

## Checks Performed

### 1. Git Status

```bash
git status --porcelain
```

**Pass if:** No output (clean working tree)
**Fail if:** Files listed (uncommitted changes)

### 2. Git Branch

```bash
git branch --show-current
```

**Pass if:** Output is `main` or `master`
**Fail if:** Different branch

### 3. Jira API Available

```bash
# Test Jira connection
python3 .claude/utils/jira_api.py ping
```

**Pass if:** Returns Jira user profile
**Fail if:** Connection error or auth error

### 4. GitHub Auth (can push)

```bash
# Test GitHub SSH
ssh -T git@github.com
```

**Pass if:** "Hi {username}! You've authenticated..."
**Fail if:** Permission denied or no response

### 5. Environment Check

Verify these files exist:
- `.env` (has JIRA_URL and JIRA_TOKEN)
- `.claude/ralph-config.json`
- `docs/CURRENT_TASK.md` (should be empty or say "No active task")

## Output Format

Display checklist:

```
PREFLIGHT CHECKS
═════════════════════════════════════════

[✅] Git working tree clean
[✅] On main branch
[✅] Jira API responding
[✅] GitHub auth working
[✅] Environment configured

═════════════════════════════════════════
✅ READY FOR /start-task
```

Or if any fail:

```
PREFLIGHT CHECKS
═════════════════════════════════════════

[✅] Git working tree clean
[❌] Jira API responding
     └─ Error: Connection refused
        Action: Check JIRA_URL in .env
[✅] GitHub auth working
[⚠️]  CURRENT_TASK.md exists but not empty
     └─ Warning: Old task still active
        Run: echo "# No active task" > docs/CURRENT_TASK.md

═════════════════════════════════════════
❌ NOT READY FOR /start-task
Blockers: 1 error, 1 warning
```

## Usage

```bash
/preflight
```

Then user sees all issues and how to fix them before attempting `/start-task`.
