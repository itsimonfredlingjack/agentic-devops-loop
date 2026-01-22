# Promise Flag File Format

## Overview

The promise flag file is a deterministic way to signal task completion to the stop-hook. It provides an alternative to transcript-based promise detection.

## Location

```
.claude/.promise_done
```

## Format

The file contains a single line with the exact completion promise:

```
<promise>DONE</promise>
```

## When to Use

The flag file is useful when:
- Long sessions make transcript searching unreliable
- Promise appears early but gets lost in verbose output
- You want guaranteed promise detection without searching entire transcript

## How It Works

1. **Agent writes promise to flag file** at task completion
2. **stop-hook checks for flag file** in Check 3
3. **If file exists and contains correct promise**, exit is allowed

## Example

```bash
# When task is complete, write flag file
echo "<promise>DONE</promise>" > .claude/.promise_done

# stop-hook will detect this and allow exit
```

## Technical Details

- File must be in `.claude/` directory
- Content is read as-is (stripped of whitespace)
- Must match completion_promise exactly (usually `<promise>DONE</promise>`)
- File is checked AFTER transcript search, so transcript promise takes precedence

## Cleanup

The flag file is NOT automatically deleted. Consider cleaning up after task completion:

```bash
# After successful task exit
rm .claude/.promise_done
```

Or keep it for logging purposes (file persists across sessions).
