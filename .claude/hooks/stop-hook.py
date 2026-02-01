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
import subprocess
import sys
from pathlib import Path
from datetime import datetime

# Add utils to path for monitor_client
sys.path.insert(0, str(Path(__file__).parent.parent / "utils"))
try:
    from monitor_client import send_task_complete, send_task_fail, send_event
except ImportError:
    def send_task_complete(*a, **kw): pass
    def send_task_fail(*a, **kw): pass
    def send_event(*a, **kw): pass

# Flag file that indicates we're in an active Ralph loop
# Only /start-task creates this file, utility commands don't
LOOP_FLAG = Path.cwd() / ".claude" / ".ralph_loop_active"

# CRITICAL: If not in active Ralph loop, allow exit immediately
# This prevents utility commands (/preflight, /finish-task) from being blocked
if not LOOP_FLAG.exists():
    sys.exit(0)  # Allow exit, no enforcement


def load_config():
    """Load Ralph Loop configuration with profile support."""
    config_paths = [
        Path(__file__).parent.parent / "ralph-config.json",
        Path.cwd() / ".claude" / "ralph-config.json",
        Path.cwd() / "ralph-config.json",
    ]

    for config_path in config_paths:
        if config_path.exists():
            with open(config_path) as f:
                config = json.load(f)

            # Check if this is a profile-based config
            if "profiles" in config:
                active_profile = config.get("active_profile", "template_repo")
                profiles = config.get("profiles", {})
                profile = profiles.get(active_profile, {})
                exit_policy = profile.get("exit_policy", {})
                return exit_policy
            else:
                # Legacy format - return as-is (for backwards compatibility)
                return config.get("exit_policy", config)

    # Default configuration
    return {
        "completion_promise": "<promise>DONE</promise>",
        "max_iterations": 25,
        "requirements": {
            "tests_must_pass": False,
            "lint_must_pass": True
        }
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


def check_promise_in_transcript(transcript: str, promise: str) -> bool:
    """Check if completion promise exists in entire transcript.

    Args:
        transcript: Full session transcript
        promise: Promise string to search for

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


def get_task_id() -> str | None:
    """Extract task_id from CURRENT_TASK.md if available."""
    import re as _re
    current_task_paths = [
        Path.cwd() / "docs" / "CURRENT_TASK.md",
        Path.cwd() / "CURRENT_TASK.md",
    ]
    for task_path in current_task_paths:
        if task_path.exists():
            try:
                content = task_path.read_text()
                match = _re.search(r"([A-Z]+-\d+)", content)
                if match:
                    return match.group(1)
            except Exception:
                pass
    return None


def build_continue_message(reason: str, suggestions: list) -> dict:
    """Build the JSON response for continuing work."""
    return {
        "action": "continue",
        "reason": reason,
        "suggestions": suggestions,
        "timestamp": datetime.now().isoformat()
    }


def _tail(text: str, lines: int = 20) -> str:
    """Return the last N lines of text."""
    all_lines = text.strip().splitlines()
    return "\n".join(all_lines[-lines:])


# ---------------------------------------------------------------------------
# Verification enforcement functions
# ---------------------------------------------------------------------------

def detect_project_types(project_root: Path = None) -> set[str]:
    """Detect project types present in the repo.

    Args:
        project_root: Root directory to check. Defaults to cwd.

    Returns:
        A set containing any of: "node", "python".
    """
    root = project_root or Path.cwd()
    types: set[str] = set()

    if (root / "package.json").exists():
        types.add("node")

    # Python detection: allow tests-only repos (no pyproject) to still be verified.
    if (root / "pyproject.toml").exists() or (root / "setup.py").exists():
        types.add("python")
    else:
        tests_dir = root / "tests"
        if tests_dir.exists():
            try:
                if any(tests_dir.rglob("test_*.py")):
                    types.add("python")
            except Exception:
                pass

    return types


def run_tests(project_type: str) -> tuple[bool, str]:
    """Run the test suite for the detected project type.

    Fail-closed: if the runner is required but not found, returns False.

    Args:
        project_type: "node", "python", or "unknown".

    Returns:
        (passed, output) tuple. passed=True only if tests ran and succeeded.
    """
    if project_type == "node":
        cmd = ["npm", "test"]
    elif project_type == "python":
        cmd = ["python3", "-m", "pytest"]
    else:
        return False, "Unknown project type \u2014 no test runner configured"

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=120
        )
        output = (result.stdout + "\n" + result.stderr).strip()
        return result.returncode == 0, _tail(output)
    except FileNotFoundError:
        return False, f"Test runner not found: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return False, "Tests timed out after 120s"


def run_lint(project_type: str) -> tuple[bool, str]:
    """Run the linter for the detected project type.

    Fail-closed: if the linter is required but not found, returns False.

    Args:
        project_type: "node", "python", or "unknown".

    Returns:
        (passed, output) tuple. passed=True only if lint ran and succeeded.
    """
    if project_type == "node":
        cmd = ["npm", "run", "lint"]
    elif project_type == "python":
        cmd = ["ruff", "check", "."]
    else:
        return False, "Unknown project type \u2014 no linter configured"

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=60
        )
        output = (result.stdout + "\n" + result.stderr).strip()
        return result.returncode == 0, _tail(output)
    except FileNotFoundError:
        return False, f"Linter not found: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return False, "Lint timed out after 60s"


def run_coverage(project_type: str, threshold: int) -> tuple[bool, str]:
    """Run test coverage and check against threshold.

    Args:
        project_type: "node" or "python".
        threshold: Minimum coverage percentage required.

    Returns:
        (passed, output) tuple. passed=True only if coverage meets threshold.
    """
    if project_type == "python":
        cmd = ["python3", "-m", "pytest", "--cov", "--cov-fail-under", str(threshold), "-q"]
    elif project_type == "node":
        cmd = ["npx", "vitest", "run", "--coverage", "--coverage.thresholds.lines", str(threshold)]
    else:
        return False, f"No coverage runner for project type: {project_type}"

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=180
        )
        output = (result.stdout + "\n" + result.stderr).strip()
        return result.returncode == 0, _tail(output)
    except FileNotFoundError:
        return False, f"Coverage runner not found: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return False, "Coverage check timed out after 180s"


def verify_before_exit(requirements: dict, project_types: set[str]) -> tuple[bool, str]:
    """Run verification checks before allowing exit.

    Fail-closed: required checks that cannot run count as failures.

    Args:
        requirements: Dict with tests_must_pass, lint_must_pass, coverage_threshold flags.
        project_types: Detected project types (e.g. {"node", "python"}).

    Returns:
        (passed, detail) tuple. detail contains failure output for block message.
    """
    failures: list[str] = []

    if requirements.get("tests_must_pass", False):
        if not project_types:
            failures.append("Tests required but project type could not be detected")
        else:
            for project_type in sorted(project_types):
                passed, output = run_tests(project_type)
                if not passed:
                    failures.append(f"Tests failed ({project_type}):\n{output}")

    if requirements.get("lint_must_pass", False):
        if not project_types:
            failures.append("Lint required but project type could not be detected")
        else:
            for project_type in sorted(project_types):
                passed, output = run_lint(project_type)
                if not passed:
                    failures.append(f"Lint failed ({project_type}):\n{output}")

    coverage_threshold = requirements.get("coverage_threshold")
    if coverage_threshold and int(coverage_threshold) > 0:
        if not project_types:
            failures.append("Coverage required but project type could not be detected")
        else:
            for project_type in sorted(project_types):
                passed, output = run_coverage(project_type, int(coverage_threshold))
                if not passed:
                    failures.append(f"Coverage below {coverage_threshold}% ({project_type}):\n{output}")

    if failures:
        return False, "\n---\n".join(failures)
    return True, ""


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
        requirements = config.get("requirements", {})

        # Increment iteration counter
        current_iteration = increment_iteration()

        # Extract task_id for monitor notifications
        _task_id = get_task_id()

        # Check 1: Max iterations exceeded
        if current_iteration >= max_iterations:
            response = build_continue_message(
                f"Max iterations ({max_iterations}) reached. Forcing exit.",
                ["Review the task manually", "Check for infinite loops in logic"]
            )
            json.dump(response, sys.stderr)
            # Notify monitor of forced exit
            if _task_id:
                send_task_fail(_task_id, f"Max iterations ({max_iterations}) exceeded")
            sys.exit(0)  # Allow exit on max iterations

        # Check 2: Promise found in transcript (search ENTIRE transcript)
        promise_found = (
            check_promise_in_transcript(transcript, completion_promise)
            or check_promise_flag_file(completion_promise)
        )

        if promise_found:
            # Verification gate: run tests/lint before allowing exit
            project_types = detect_project_types()
            passed, detail = verify_before_exit(requirements, project_types)
            if passed:
                # Notify monitor of successful completion
                if _task_id:
                    send_task_complete(_task_id)
                sys.exit(0)  # All checks pass — allow exit
            else:
                # Verification failed \u2014 block exit with detail
                response = build_continue_message(
                    "Promise found but verification failed",
                    [
                        detail,
                        "Fix the failing tests/lint issues",
                        f"Then output {completion_promise} again",
                    ]
                )
                json.dump(response, sys.stderr)
                sys.exit(2)

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
