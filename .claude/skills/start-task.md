---
name: start-task
description: Initialize a new task from a Jira ticket, create branch, and set up CURRENT_TASK.md
args: JIRA_ID (e.g., PROJ-123)
---

# Start Task Skill

This skill initializes the Ralph Loop for a new Jira task.

## Prerequisites

- Jira MCP server must be configured with valid credentials
- Git repository must be clean (no uncommitted changes)
- Must be on main/master branch

## Workflow

### Step 1: Validate Input

The JIRA_ID argument must match the pattern `[A-Z]+-[0-9]+`.

### Step 2: Fetch Jira Ticket

Use the Jira MCP tools to fetch the ticket:

```
jira_get_issue(issue_key="{JIRA_ID}")
```

Extract from the response:
- `summary` - Ticket title
- `description` - Full description
- `issuetype.name` - Issue type (Bug, Story, Task, etc.)
- `priority.name` - Priority level
- `status.name` - Current status
- `customfield_*` - Acceptance criteria (if configured)

### Step 3: Determine Branch Type

Map Jira issue type to branch prefix:
- Bug → `bugfix/`
- Story → `feature/`
- Task → `feature/`
- Hotfix → `hotfix/`
- Default → `feature/`

### Step 4: Create Branch

Generate branch name: `{type}/{JIRA_ID}-{slug}`

Where `slug` is the summary:
- Lowercase
- Spaces replaced with hyphens
- Special characters removed
- Truncated to 50 chars

Example: `feature/PROJ-123-add-user-authentication`

```bash
git checkout main
git pull origin main
git checkout -b {branch_name}
```

### Step 5: Update CURRENT_TASK.md

Update `docs/CURRENT_TASK.md` with:

```markdown
# Current Task

> **READ THIS FILE FIRST** at the start of every iteration.
> This is your persistent memory - it survives context compaction.

## Active Task

**Jira ID:** {JIRA_ID}
**Status:** In Progress
**Branch:** {branch_name}
**Started:** {timestamp}

## Acceptance Criteria

{acceptance_criteria_from_ticket}

## Implementation Checklist

- [ ] Understand the requirements
- [ ] Write/update tests first (TDD)
- [ ] Implement the solution
- [ ] All tests pass
- [ ] Linting passes
- [ ] Code reviewed (self or peer)

## Current Progress

### Iteration Log

| # | Action | Result | Next Step |
|---|--------|--------|-----------|
| 1 | Task initialized | Branch created | Read requirements |

### Blockers

_None_

### Decisions Made

_None_

## Technical Context

### Files Modified

_None_

### Dependencies Added

_None_

### API Changes

_None_

## Exit Criteria

Before outputting `<promise>DONE</promise>`, verify:

1. [ ] All acceptance criteria are met
2. [ ] All tests pass: `pytest` or `npm test`
3. [ ] No linting errors: `ruff check .` or `npm run lint`
4. [ ] Changes committed with proper message format: `{JIRA-ID}: {description}`
5. [ ] Branch pushed to remote

## Notes

**Original Ticket Description:**
{ticket_description}

---

*Last updated: {timestamp}*
*Iteration: 1*
```

### Step 6: Transition Jira Status

Transition the Jira ticket to "In Progress":

```
jira_transition_issue(issue_key="{JIRA_ID}", transition="In Progress")
```

### Step 7: Add Jira Comment

Log that the agent has started work:

```
jira_add_comment(issue_key="{JIRA_ID}", body="🤖 Claude Code agent started work on this ticket.\n\nBranch: `{branch_name}`\nTimestamp: {timestamp}")
```

### Step 8: Reset Ralph State

Clear the iteration counter:

```bash
rm -f .claude/ralph-state.json
```

### Step 9: Confirm Ready

Output confirmation:

```
✅ Task {JIRA_ID} initialized

Branch: {branch_name}
Status: In Progress
Iteration: 1/25

Next: Read the acceptance criteria and begin implementation.
Remember to run tests frequently and output <promise>DONE</promise> when complete.
```

## Error Handling

- **Jira ticket not found:** Exit with error, do not create branch
- **Branch already exists:** Ask user whether to switch to existing branch
- **Uncommitted changes:** Abort and ask user to commit or stash
- **MCP server unavailable:** Fall back to manual mode (ask user for ticket details)

## Post-Skill Behavior

After this skill completes, the agent should:
1. Read `docs/CURRENT_TASK.md` to understand the requirements
2. Begin implementation following TDD
3. Update CURRENT_TASK.md after each significant action
4. Output `<promise>DONE</promise>` only when all exit criteria are met
