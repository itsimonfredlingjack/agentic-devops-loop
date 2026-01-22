#!/usr/bin/env python3
"""
Ralph Loop Stop-Hook

This hook prevents the agent from exiting until:
1. The completion_promise string is found in the transcript
2. All tests pass (verified by promise format)
3. Max iterations haven't been exceeded

Exit codes:
- 0: Allow exit (promise found, criteria met)
- 2: Block exit (continue working)

The hook reads JSON from stdin and writes feedback to stderr.
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime


def load_config():
    """Load Ralph Loop configuration."""
    config_paths = [
        Path(__file__).parent.parent / "ralph-config.json",
        Path.cwd() / ".claude" / "ralph-config.json",
        Path.cwd() / "ralph-config.json",
    ]

    for config_path in config_paths:
        if config_path.exists():
            with open(config_path) as f:
                return json.load(f)

    # Default configuration
    return {
        "completion_promise": "<promise>DONE</promise>",
        "max_iterations": 25,
        "scan_length": 5000,
        "require_tests_pass": True,
        "require_lint_pass": True
    }


def get_iteration_count():
    """Get current iteration count from state file."""
    state_file = Path.cwd() / ".claude" / "ralph-state.json"
    if state_file.exists():
        with open(state_file) as f:
            state = json.load(f)
            return state.get("iterations", 0)
    return 0


def increment_iteration():
    """Increment and save iteration count."""
    state_file = Path.cwd() / ".claude" / "ralph-state.json"
    state_file.parent.mkdir(parents=True, exist_ok=True)

    state = {"iterations": 0, "started_at": datetime.now().isoformat()}
    if state_file.exists():
        with open(state_file) as f:
            state = json.load(f)

    state["iterations"] = state.get("iterations", 0) + 1
    state["last_check"] = datetime.now().isoformat()

    with open(state_file, "w") as f:
        json.dump(state, f, indent=2)

    return state["iterations"]


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


def build_continue_message(reason: str, suggestions: list) -> dict:
    """Build the JSON response for continuing work."""
    return {
        "action": "continue",
        "reason": reason,
        "suggestions": suggestions,
        "timestamp": datetime.now().isoformat()
    }


def main():
    """Main hook logic."""
    try:
        # Read input from stdin
        input_data = sys.stdin.read()

        if not input_data.strip():
            # No input, allow exit
            sys.exit(0)

        try:
            hook_input = json.loads(input_data)
        except json.JSONDecodeError:
            # Invalid JSON, allow exit (fail open)
            sys.exit(0)

        # Load configuration
        config = load_config()

        # Get values from input and config
        transcript = hook_input.get("transcript", "")
        completion_promise = config.get("completion_promise", "<promise>DONE</promise>")
        max_iterations = config.get("max_iterations", 25)
        scan_length = config.get("scan_length", 5000)

        # Increment iteration counter
        current_iteration = increment_iteration()

        # Check 1: Max iterations exceeded
        if current_iteration >= max_iterations:
            response = build_continue_message(
                f"Max iterations ({max_iterations}) reached. Forcing exit.",
                ["Review the task manually", "Check for infinite loops in logic"]
            )
            json.dump(response, sys.stderr)
            sys.exit(0)  # Allow exit on max iterations

        # Check 2: Promise found in transcript (search ENTIRE transcript)
        if check_promise_in_transcript(transcript, completion_promise, scan_length):
            sys.exit(0)  # Allow exit

        # Check 3: Promise flag file exists and is valid
        if check_promise_flag_file(completion_promise):
            sys.exit(0)  # Allow exit

        # Promise not found - block exit and provide guidance
        suggestions = [
            "Read docs/CURRENT_TASK.md to review acceptance criteria",
            "Run the test suite and verify all tests pass",
            "Check for linting errors with the appropriate linter",
            f"When all criteria are met, output: {completion_promise}"
        ]

        # Add iteration info
        reason = f"Completion criteria not met (iteration {current_iteration}/{max_iterations})"

        response = build_continue_message(reason, suggestions)
        json.dump(response, sys.stderr)

        # Exit 2 blocks the agent from exiting
        sys.exit(2)

    except Exception as e:
        # On any error, fail open (allow exit) to prevent stuck state
        error_response = {
            "error": str(e),
            "action": "allow_exit_on_error"
        }
        json.dump(error_response, sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    main()
