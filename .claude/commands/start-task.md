---
description: Initialize a new task from Jira ticket, create branch, and setup CURRENT_TASK.md
---

# Start Task: $ARGUMENTS

Initialize the Ralph Loop for Jira ticket **$ARGUMENTS**.

## Instructions

This command delegates to the `start-task` skill which contains the full workflow.

### Quick Summary

1. **Pre-flight checks** - clean git state, on main branch
2. **Activate Ralph Loop** - create `.claude/.ralph_loop_active` flag
3. **Validate Jira connection** - ping API, fail if unavailable
4. **Fetch ticket** - get issue details from Jira (or ask user)
5. **Create branch** - `{type}/$ARGUMENTS-{slug}`
6. **Setup CURRENT_TASK.md** - persistent agent memory
7. **Update Jira** - transition to "In Progress", add comment
8. **Notify monitor** - send task_start event (non-blocking)
9. **Begin Ralph Loop** - TDD cycle until `<promise>DONE</promise>`

### Monitor Notification

After branch creation, notify the orbital monitor:

```bash
python3 -c "
import sys; sys.path.insert(0, '.claude/utils')
from monitor_client import send_task_start
send_task_start('$ARGUMENTS', title='{summary}', branch='{branch_name}', max_iterations=25)
import time; time.sleep(0.5)
"
```

If monitor is offline, ignore and continue.

### Exit Policy

Defined in `.claude/ralph-config.json`. The stop-hook enforces exit criteria.

---

*See `.claude/skills/start-task/SKILL.md` for the full detailed workflow.*
