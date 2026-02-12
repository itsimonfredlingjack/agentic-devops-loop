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
source venv/bin/activate && python3 -c "
from dotenv import load_dotenv
load_dotenv()
from src.sejfa.integrations.jira_client import get_jira_client
client = get_jira_client()
if client.test_connection():
    print('✅ Jira connection OK')
else:
    print('❌ Jira connection FAILED')
"
```

**Pass if:** Output shows "✅ Jira connection OK"
**Fail if:** Connection error or "❌ Jira connection FAILED"

### 4. GitHub Auth (can push)

```bash
# Test GitHub SSH
ssh -T git@github.com
```

**Pass if:** "Hi {username}! You've authenticated..."
**Fail if:** Permission denied or no response

### 5. Environment Check

Verify these files exist:
- `.claude/settings.local.json`
- `CURRENT_TASK.md` (should be empty template or say "No active task")

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
     └─ Error: Connection failed
        Action: Check .env file (JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN)
[✅] GitHub auth working
[⚠️]  CURRENT_TASK.md has active task
     └─ Warning: Old task still active
        Run: /finish-task first

═════════════════════════════════════════
❌ NOT READY FOR /start-task
Blockers: 1 error, 1 warning
```

## Usage

```bash
/preflight
```

Then user sees all issues and how to fix them before attempting `/start-task`.
