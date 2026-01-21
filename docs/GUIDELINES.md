# Agent Development Guidelines

> **READ THIS WHEN STUCK OR UNSURE**
> This document provides guidance for the autonomous development loop.

## Core Principles

### 1. Test-Driven Development (TDD)

```
RED    → Write a failing test first
GREEN  → Write minimal code to pass
REFACTOR → Clean up without breaking tests
```

**Never skip the red phase.** If you can't write a failing test, you don't understand the requirement.

### 2. Small, Incremental Changes

- One logical change per commit
- Run tests after every change
- Commit working code frequently

### 3. Read Before Write

- Always read existing code before modifying
- Understand the patterns already in use
- Follow existing conventions

## Ralph Loop Workflow

### Each Iteration

1. **Read** `docs/CURRENT_TASK.md` (your memory)
2. **Check** acceptance criteria progress
3. **Plan** the next small step
4. **Execute** (write test → implement → verify)
5. **Update** CURRENT_TASK.md with progress
6. **Repeat** until all criteria met

### Exit Conditions

You may ONLY output `<promise>DONE</promise>` when:

- [ ] ALL acceptance criteria are checked off
- [ ] ALL tests pass (`pytest` or `npm test`)
- [ ] NO linting errors (`ruff check .` or `npm run lint`)
- [ ] Changes are committed with proper format
- [ ] Branch is pushed to remote

**If ANY condition is false, keep working.**

## Common Patterns

### Running Tests

```bash
# Python
pytest -xvs                    # Stop on first failure, verbose
pytest --cov=src               # With coverage
pytest path/to/test_file.py    # Single file

# Node
npm test                       # Run all tests
npm test -- --watch           # Watch mode
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
npx prettier --write .        # Format
```

### Git Operations

```bash
# Check status
git status
git diff

# Commit (always include Jira ID)
git add -A
git commit -m "PROJ-123: Implement feature X"

# Push
git push -u origin feature/PROJ-123-description
```

## Troubleshooting

### Tests Won't Pass

1. Read the error message carefully
2. Check if it's a test bug vs implementation bug
3. Run single test in isolation
4. Add debug output if needed
5. Check for missing dependencies

### Linting Failures

1. Run with `--fix` flag first
2. For remaining issues, read the rule documentation
3. Don't disable rules without good reason

### Stuck in Loop

If iteration count is high (>15) and no progress:

1. Re-read acceptance criteria
2. Check if requirement is ambiguous
3. Simplify the approach
4. Consider breaking into smaller tasks

### Context Lost

If you feel confused about the task:

1. Read `docs/CURRENT_TASK.md` completely
2. Check git log for recent changes
3. Review the acceptance criteria
4. Start fresh from a known good state

## Security Rules

### Never Do

- Modify `.github/` or `.claude/hooks/`
- Install packages not in allowlist
- Use `sudo`, `eval`, or pipe to shell
- Write to `/etc/` or system directories
- Push with `--force`
- Reset with `--hard`

### Always Do

- Validate input before using
- Use parameterized queries
- Escape output appropriately
- Follow least-privilege principle

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

## Communication

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

*Remember: The goal is working software that meets requirements, not perfection.*
