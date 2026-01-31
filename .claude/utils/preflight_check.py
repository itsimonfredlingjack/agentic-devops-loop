#!/usr/bin/env python3
"""
Preflight validation for starting new tasks.
"""

import subprocess
import json
from pathlib import Path
from typing import Dict, Tuple


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
        # Accept both JIRA_TOKEN and JIRA_API_TOKEN
        has_jira_token = "JIRA_TOKEN" in content or "JIRA_API_TOKEN" in content

        if not (has_jira_url and has_jira_token):
            missing = []
            if not has_jira_url:
                missing.append("JIRA_URL")
            if not has_jira_token:
                missing.append("JIRA_TOKEN or JIRA_API_TOKEN")
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
