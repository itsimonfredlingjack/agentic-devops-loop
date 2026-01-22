# Agentic Loop Critical Fixes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix 7 critical issues in the agentic loop that cause task failures, promise detection failures, and missing safety guardrails.

**Architecture:** 
1. Fix stop-hook to search entire transcript (not fragile window)
2. Add deterministic promise flag file (.claude/.promise_done)
3. Add safety guards to start-task (Jira fetch fail = STOP)
4. Add git status check and CURRENT_TASK.md overwrite guarantee
5. Create exit policy profiles for template vs code repos
6. Add explicit promise format instructions
7. Create new /preflight command for pre-flight validation

**Tech Stack:** Python (hooks), Bash (commands), JSON (config), Markdown (skills)

---

## Task 1: Fix Stop-Hook to Search Entire Transcript + Flag File

### Problem
Stop-hook only scans last 5000 chars of transcript. If agent writes "DONE" early in long session, hook can't find it.

### Files
- Modify: `.claude/hooks/stop-hook.py` - Replace fragile scan_length logic
- Create: `.claude/PROMISE_FLAG_FORMAT.md` - Document flag file format

### Step 1: Read current stop-hook implementation

File: `.claude/hooks/stop-hook.py` (lines 62-69)

Current logic:
```python
def check_promise_in_transcript(transcript: str, promise: str, scan_length: int) -> bool:
    search_area = transcript[-scan_length:] if len(transcript) > scan_length else transcript
    return promise in search_area
```

**Step 2: Update check_promise_in_transcript to search entire transcript**

Replace function with:

```python
def check_promise_in_transcript(transcript: str, promise: str, scan_length: int = None) -> bool:
    """Check if completion promise exists in entire transcript.
    
    Args:
        transcript: Full session transcript
        promise: Promise string to search for
        scan_length: Ignored (for backwards compatibility)
    
    Returns:
        True if promise found anywhere in transcript
    """
    if not transcript:
        return False
    # Search ENTIRE transcript, not just tail
    return promise in transcript
```

**Step 3: Add flag file check function after check_promise_in_transcript**

Add new function:

```python
def check_promise_flag_file(promise: str) -> bool:
    """Check if promise flag file exists and contains the correct promise.
    
    Flag file location: .claude/.promise_done
    Flag file contains: exact promise string
    
    Returns:
        True if flag file exists and contains correct promise
    """
    flag_file = Path.cwd() / ".claude" / ".promise_done"
    
    if not flag_file.exists():
        return False
    
    try:
        with open(flag_file, 'r') as f:
            content = f.read().strip()
        return content == promise
    except Exception:
        return False


def write_promise_flag(promise: str) -> None:
    """Write promise flag file for stop-hook to detect."""
    flag_file = Path.cwd() / ".claude" / ".promise_done"
    flag_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(flag_file, 'w') as f:
        f.write(promise)
```

**Step 4: Update main() to check BOTH transcript AND flag file**

In `main()` function, replace the promise check (around line 92-95):

OLD:
```python
# Check 2: Promise found in transcript
if check_promise_in_transcript(transcript, completion_promise, scan_length):
    sys.exit(0)  # Allow exit
```

NEW:
```python
# Check 2: Promise found in transcript (search ENTIRE transcript)
if check_promise_in_transcript(transcript, completion_promise, scan_length):
    sys.exit(0)  # Allow exit

# Check 3: Promise flag file exists and is valid
if check_promise_flag_file(completion_promise):
    sys.exit(0)  # Allow exit
```

**Step 5: Run stop-hook tests**

Create test file to verify both transcript search and flag file work:

Run: `python -m pytest .claude/hooks/test_stop_hook.py -v`

Expected: Tests pass for both full-transcript search and flag file detection

**Step 6: Commit**

```bash
cd /tmp/agentic-repo
git add .claude/hooks/stop-hook.py
git commit -m "fix: make stop-hook search entire transcript + add promise flag file

- Remove fragile scan_length window (was only searching last 5000 chars)
- Search ENTIRE transcript for completion promise
- Add .claude/.promise_done flag file as deterministic promise indicator
- Both methods checked: transcript search OR flag file exists"
```

---

## Task 2: Add Jira Fetch Safety Guard to start-task

### Problem
If Jira MCP unavailable, agent invented what DEV-9 was about instead of stopping.

### Files
- Modify: `.claude/skills/start-task.md` - Add Jira fetch fail safety step

### Step 1: Read current start-task skill

File: `.claude/skills/start-task.md` (Step 2: Fetch Jira Ticket section)

### Step 2: Add new Step 1A: Pre-Jira Validation

Insert before Step 2:

```markdown
### Step 1A: Validate Jira Connection (SAFETY)

Before attempting to fetch, validate Jira MCP is available.

**Run this command to test:**

```bash
# Test Jira connection (will error if unavailable)
jira_search_issues(jql="project = YOUR_PROJECT LIMIT 1")
```

**If this fails with "Connection refused" or "MCP not available":**
- **STOP IMMEDIATELY**
- Output: "❌ Jira MCP is not available. Cannot fetch ticket details."
- Ask user to:
  1. Check `.env` file has `JIRA_URL` and `JIRA_TOKEN`
  2. Restart Claude Code session
  3. Or run `/preflight` to validate setup
- **DO NOT PROCEED without real Jira data**
- **DO NOT INVENT ticket details**

If Jira is unavailable, the user MUST provide ticket details manually:
1. Ask user to copy/paste ticket summary
2. Ask user to copy/paste acceptance criteria
3. Proceed with manual data (wrapped in `<jira_data>` tags)
```

### Step 3: Update Step 2 to handle fetch failures

Modify "Step 2: Fetch Jira Ticket" section:

```markdown
### Step 2: Fetch Jira Ticket

Use the Jira MCP tool to fetch the ticket:

```
jira_get_issue(issue_key="{JIRA_ID}")
```

**If this fails:**
- The Jira MCP is not properly configured
- **DO NOT GUESS or INVENT**
- Output error message and **STOP**
- Ask user to manually provide:
  - Summary (ticket title)
  - Description (full description)
  - Acceptance Criteria (if any)
  
Then wrap in `<jira_data>` tags and proceed.

Extract from the successful response:
- `summary` - Ticket title
- `description` - Full description
- `issuetype.name` - Issue type (Bug, Story, Task, etc.)
- `priority.name` - Priority level
- `status.name` - Current status
- `customfield_*` - Acceptance criteria (if configured)
```

### Step 4: Add explicit instruction about NOT inventing

Add new section after Step 3:

```markdown
### Step 3B: STRICT DATA INTEGRITY CHECK

**CRITICAL**: You have NOW received the REAL ticket data from Jira OR from user input.

**Verify:**
- [ ] You have actual summary text (not "Unknown" or placeholder)
- [ ] You have actual acceptance criteria (not "none specified")
- [ ] You have actual description (not "see summary")

**If any field is missing:**
- **ASK THE USER** for the missing information
- **DO NOT INVENT OR GUESS** requirements
- Bad requirements = bad implementation = wasted iterations

This is non-negotiable. Better to ask and wait than to implement the wrong thing.
```

### Step 5: Commit

```bash
cd /tmp/agentic-repo
git add .claude/skills/start-task.md
git commit -m "safety: add Jira fetch failure guards to start-task

- Add pre-Jira validation check before attempting fetch
- If Jira unavailable, STOP immediately (don't guess)
- Add manual fallback: user can paste ticket content
- Add strict data integrity verification
- Never proceed with invented or placeholder ticket data"
```

---

## Task 3: Guarantee CURRENT_TASK.md Overwrite on New Task

### Problem
Old "No active task" content confused agent about what to work on.

### Files
- Modify: `.claude/skills/start-task.md` - Step 6 (Update CURRENT_TASK.md)

### Step 1: Read current Step 6

File: `.claude/skills/start-task.md` (Step 6: Update CURRENT_TASK.md)

Current markdown includes a template but doesn't explicitly say to DELETE old content first.

### Step 2: Add explicit deletion/recreation step

Replace the current Step 6 header section with:

```markdown
### Step 6: Overwrite CURRENT_TASK.md (DELETE then CREATE)

**IMPORTANT**: This step ALWAYS replaces the entire file. Never append or preserve old content.

First, DELETE the old file:
```bash
rm -f docs/CURRENT_TASK.md
```

Then, CREATE the new file from scratch:
```bash
cat > docs/CURRENT_TASK.md << 'EOF'
[full template content here]
EOF
```

This guarantees:
- No stale data from previous tasks
- Clear memory state for agent
- No confusion about what task is active
```

### Step 3: Verify template is complete

Ensure the markdown template after "EOF" is complete and includes all sections.

### Step 4: Add filename to .gitignore safety check

Add a note:

```markdown
**Safety Check**: 
- Verify `.gitignore` does NOT exclude `docs/CURRENT_TASK.md`
- This file should be committed (it's persistent agent memory)
- If .gitignore has `CURRENT_TASK.md`, remove that line
```

### Step 5: Commit

```bash
cd /tmp/agentic-repo
git add .claude/skills/start-task.md
git commit -m "safety: guarantee CURRENT_TASK.md complete overwrite

- Explicitly delete old file first (rm -f)
- Then recreate from scratch (cat > with heredoc)
- Never append or preserve old content
- Prevents stale data from confusing agent"
```

---

## Task 4: Create Exit Policy Profiles in ralph-config.json

### Problem
Exit policy requires "tests_must_pass": true, but template repo has no test framework.

### Files
- Modify: `.claude/ralph-config.json` - Add profile system
- Create: `.claude/ralph-config.schema.json` - Document profile schema

### Step 1: Read current ralph-config.json

File: `.claude/ralph-config.json` (current state)

Current `requirements` section:
```json
"requirements": {
  "tests_must_pass": true,
  "lint_must_pass": true,
  "coverage_threshold": null
}
```

### Step 2: Create new config structure with profiles

Replace entire `exit_policy` section:

```json
{
  "version": "1.0.0",
  "description": "Ralph Loop exit policy configuration",
  
  "active_profile": "template_repo",
  
  "profiles": {
    "template_repo": {
      "description": "For documentation and template repos (no code tests)",
      "exit_policy": {
        "completion_promise": "<promise>DONE</promise>",
        "max_iterations": 25,
        "scan_length": 5000,
        "requirements": {
          "tests_must_pass": false,
          "lint_must_pass": true,
          "markdown_lint": true,
          "structure_validation": true
        }
      }
    },
    
    "code_repo": {
      "description": "For code repos with test frameworks",
      "exit_policy": {
        "completion_promise": "<promise>DONE</promise>",
        "max_iterations": 25,
        "scan_length": 5000,
        "requirements": {
          "tests_must_pass": true,
          "lint_must_pass": true,
          "coverage_threshold": 80
        }
      }
    }
  }
}
```

### Step 3: Update stop-hook to read active profile

Modify `.claude/hooks/stop-hook.py` function `load_config()`:

Replace:
```python
def load_config():
    # ... existing code ...
    return {
        "completion_promise": "<promise>DONE</promise>",
        "max_iterations": 25,
        "scan_length": 5000,
        "require_tests_pass": True,
        "require_lint_pass": True
    }
```

With:
```python
def load_config():
    """Load Ralph Loop configuration with profile support."""
    # ... existing config loading code ...
    
    config = json.load(f)
    active_profile = config.get("active_profile", "template_repo")
    
    # Get profile-specific exit policy
    profiles = config.get("profiles", {})
    profile = profiles.get(active_profile, {})
    exit_policy = profile.get("exit_policy", {})
    
    return exit_policy
```

### Step 4: Test both profiles

Run stop-hook with both profiles and verify:
- template_repo: tests_must_pass = false ✓
- code_repo: tests_must_pass = true ✓

### Step 5: Commit

```bash
cd /tmp/agentic-repo
git add .claude/ralph-config.json .claude/hooks/stop-hook.py
git commit -m "config: add exit policy profiles for template vs code repos

- Add 'active_profile' setting (default: template_repo)
- Profile 'template_repo': no tests required, markdown/structure validation
- Profile 'code_repo': full tests + lint + coverage required
- Stop-hook reads active profile and uses its exit policy
- Switch profiles in .claude/ralph-config.json as needed"
```

---

## Task 5: Add Explicit Promise Format Instructions to start-task

### Problem
Agent wrote "DONE" instead of "<promise>DONE</promise>".

### Files
- Modify: `.claude/skills/start-task.md` - Add exact format instructions

### Step 1: Find where exit criteria are documented

File: `.claude/skills/start-task.md` - Look for "Exit Criteria" section in CURRENT_TASK.md template

### Step 2: Add new sub-section: "Promise Format"

Insert in the Step 10 (Ralph Loop Initialization Prompt):

```markdown
### Promise Format - EXACT SPECIFICATION

When your task is complete and ALL exit criteria are met:

**Output EXACTLY this string:**

```
<promise>DONE</promise>
```

**NOT:**
- ✗ `DONE`
- ✗ `done`
- ✗ `Task complete`
- ✗ `<promise>Done</promise>` (wrong case)
- ✗ `<PROMISE>DONE</PROMISE>` (wrong case)
- ✗ Any other variation

**The EXACT string is:**
```
<promise>DONE</promise>
```

This exact format is detected by the stop-hook. Any deviation and exit will be blocked.

**Before outputting the promise, verify:**
1. [ ] All acceptance criteria met
2. [ ] All tests passing
3. [ ] All linting passing
4. [ ] Changes committed
5. [ ] Branch pushed to remote

Only then output the promise on its own line.
```

### Step 3: Add to CURRENT_TASK.md template section

In the CURRENT_TASK.md template that start-task generates, update "Exit Criteria" section:

```markdown
## Exit Criteria

Before outputting `<promise>DONE</promise>`, verify:

1. [ ] All acceptance criteria are met
2. [ ] All tests pass
3. [ ] No linting errors
4. [ ] Changes committed with proper message format
5. [ ] Branch pushed to remote

When complete, output EXACTLY:
```
<promise>DONE</promise>
```

No variations. This exact format is required for stop-hook detection.
```

### Step 4: Commit

```bash
cd /tmp/agentic-repo
git add .claude/skills/start-task.md
git commit -m "docs: add explicit promise format specification

- Document exact output format: <promise>DONE</promise>
- Show what NOT to do (DONE, done, Task complete, etc.)
- Emphasize this is detected by stop-hook
- Add before/after checklist
- Prevent promise format variations"
```

---

## Task 6: Add Git Status Check to start-task

### Problem
Uncommitted changes caused confusion when starting new task.

### Files
- Modify: `.claude/skills/start-task.md` - Add git status check as Step 1

### Step 1: Read current start-task prerequisites

File: `.claude/skills/start-task.md` (Prerequisites section)

### Step 2: Move prerequisites check to Step 0 (pre-flight)

Add new step BEFORE Step 1:

```markdown
### Step 0: Pre-Flight Checks (REQUIRED)

Before attempting to start a task, verify the working environment:

**Check 1: Git working tree is clean**

```bash
# See uncommitted changes
git status --porcelain

# Expected output: empty (no output = clean)
# If there IS output (files listed), STOP
```

**If git status shows changes:**
- **STOP immediately**
- Output: "❌ Working tree is not clean. Commit or stash changes first."
- Ask user to run: `git add . && git commit -m "WIP: stash before new task"`
- Or run: `git stash`
- **DO NOT PROCEED** with dirty working tree

**Check 2: Currently on main/master branch**

```bash
# Check current branch
git branch --show-current

# Expected: main or master
# If different, STOP
```

**If not on main:**
- Output: "❌ Not on main/master branch. Switch first."
- Run: `git checkout main`
- Then start task again

**After both checks pass:**
- Output: "✅ Pre-flight checks passed"
- Continue to Step 1
```

### Step 3: Update Step 1 (Validate Input) header

Change Step 1 heading to "Step 1: Validate Jira ID Format" (since Step 0 is now pre-flight)

Update all subsequent steps (Step 2 → Step 2, etc. remain same, but Step 1 becomes Step 1 after pre-flight)

### Step 4: Commit

```bash
cd /tmp/agentic-repo
git add .claude/skills/start-task.md
git commit -m "safety: add git pre-flight checks to start-task

- New Step 0: Check git working tree is clean
- Stop if uncommitted changes exist
- Stop if not on main/master branch
- Prevent stale state confusion
- Prevent task starting with dirty tree"
```

---

## Task 7: Create /preflight Command for Pre-Flight Validation

### Problem
MCP config documentation unclear, Jira not loading.

### Files
- Create: `.claude/commands/preflight.md` - New command

### Step 1: Create preflight command file

Create file `.claude/commands/preflight.md`:

```markdown
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

### 3. Jira MCP Available

```bash
# Test Jira connection
jira_search_issues(jql="ORDER BY created DESC LIMIT 1")
```

**Pass if:** Returns issue list
**Fail if:** Connection error or "MCP not available"

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
[✅] Jira MCP responding
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
[❌] Jira MCP responding
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
```

### Step 2: Create the preflight validation logic file

Also create `.claude/utils/preflight_check.py`:

```python
#!/usr/bin/env python3
"""
Preflight validation for starting new tasks.
"""

import subprocess
import os
import json
from pathlib import Path
from typing import Dict, List, Tuple


def check_git_status() -> Tuple[bool, str]:
    """Check if working tree is clean."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            return False, "Git command failed"
        
        if result.stdout.strip():
            return False, f"Uncommitted changes:\n{result.stdout}"
        
        return True, "Working tree clean"
    except Exception as e:
        return False, str(e)


def check_git_branch() -> Tuple[bool, str]:
    """Check if on main/master branch."""
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            return False, "Git command failed"
        
        branch = result.stdout.strip()
        if branch not in ["main", "master"]:
            return False, f"On branch '{branch}', not main/master"
        
        return True, f"On {branch} branch"
    except Exception as e:
        return False, str(e)


def check_env_file() -> Tuple[bool, str]:
    """Check if .env exists and has Jira credentials."""
    env_path = Path.cwd() / ".env"
    
    if not env_path.exists():
        return False, ".env file not found"
    
    try:
        with open(env_path) as f:
            content = f.read()
        
        has_jira_url = "JIRA_URL" in content
        has_jira_token = "JIRA_TOKEN" in content
        
        if not (has_jira_url and has_jira_token):
            missing = []
            if not has_jira_url:
                missing.append("JIRA_URL")
            if not has_jira_token:
                missing.append("JIRA_TOKEN")
            return False, f"Missing in .env: {', '.join(missing)}"
        
        return True, ".env configured with Jira credentials"
    except Exception as e:
        return False, str(e)


def check_current_task() -> Tuple[bool, str]:
    """Check CURRENT_TASK.md state."""
    task_file = Path.cwd() / "docs" / "CURRENT_TASK.md"
    
    if not task_file.exists():
        return True, "No active task (file doesn't exist)"
    
    try:
        with open(task_file) as f:
            content = f.read()
        
        if "No active task" in content or len(content.strip()) < 50:
            return True, "No active task (file empty)"
        
        return False, "Active task found - finish or clear before starting new one"
    except Exception as e:
        return False, str(e)


def check_ralph_config() -> Tuple[bool, str]:
    """Check if ralph-config.json exists and valid."""
    config_path = Path.cwd() / ".claude" / "ralph-config.json"
    
    if not config_path.exists():
        return False, ".claude/ralph-config.json not found"
    
    try:
        with open(config_path) as f:
            json.load(f)
        
        return True, "ralph-config.json valid"
    except Exception as e:
        return False, f"ralph-config.json invalid: {str(e)}"


def run_preflight() -> Dict:
    """Run all preflight checks."""
    checks = {
        "Git status": check_git_status(),
        "Git branch": check_git_branch(),
        ".env config": check_env_file(),
        "CURRENT_TASK.md": check_current_task(),
        "ralph-config": check_ralph_config(),
    }
    
    return checks


def format_output(checks: Dict) -> str:
    """Format checks for display."""
    lines = [
        "PREFLIGHT CHECKS",
        "═" * 40,
        ""
    ]
    
    all_pass = True
    for check_name, (passed, message) in checks.items():
        symbol = "✅" if passed else "❌"
        lines.append(f"[{symbol}] {check_name}")
        if not passed:
            lines.append(f"    └─ {message}")
            all_pass = False
    
    lines.append("")
    lines.append("═" * 40)
    
    if all_pass:
        lines.append("✅ READY FOR /start-task")
    else:
        lines.append("❌ NOT READY FOR /start-task")
        lines.append("Fix issues above and try again")
    
    return "\n".join(lines)


if __name__ == "__main__":
    checks = run_preflight()
    output = format_output(checks)
    print(output)
    
    # Exit with 0 if all pass, 1 if any fail
    all_pass = all(check[0] for check in checks.values())
    exit(0 if all_pass else 1)
```

### Step 3: Test preflight script

```bash
cd /tmp/agentic-repo
python .claude/utils/preflight_check.py
```

Expected output:
```
PREFLIGHT CHECKS
════════════════════════════════════════
[✅] Git status
[✅] Git branch
[✅] .env config
[✅] CURRENT_TASK.md
[✅] ralph-config
════════════════════════════════════════
✅ READY FOR /start-task
```

### Step 4: Commit

```bash
cd /tmp/agentic-repo
git add .claude/commands/preflight.md .claude/utils/preflight_check.py
git commit -m "feat: add /preflight command for pre-task validation

- Checks git status, branch, .env, current task, config
- Validates all prerequisites before /start-task
- Shows clear blockers and how to fix them
- Exit code 0 if ready, 1 if blockers found"
```

---

## Final Validation Test Sequence

After all 7 tasks are complete, verify with this sequence:

```bash
# 1. Run preflight
/preflight
# Expected: ✅ READY FOR /start-task

# 2. Start new task (use real Jira ID or DEV-9)
/start-task DEV-9
# Expected: ✓ Branch created ✓ CURRENT_TASK.md updated ✓ Ralph Loop active

# 3. Do actual work (write tests, implement, etc.)
# ... work ...

# 4. When done, verify all tests pass
npm test  # or pytest
# Expected: ALL TESTS PASS

# 5. Write exact promise format
echo "<promise>DONE</promise>"
# Expected: Stop-hook detects and allows exit

# 6. Verify stop-hook searched entire transcript
# Check .claude/ralph-loop.log for: "Promise found in entire transcript"
```

