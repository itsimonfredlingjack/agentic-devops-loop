#!/usr/bin/env python3
"""
Smart Commit Helper

Extracts Jira IDs and smart commit directives from commit messages,
then dispatches corresponding Jira API calls.

Directives:
    #comment <text>     \u2014 add comment to issue
    #in-progress        \u2014 transition to "In Progress"
    #in-review          \u2014 transition to "In Review"
    #done / #resolved / #closed \u2014 transition to "Done"
"""

import re
import shutil
import subprocess
from pathlib import Path

# Maps directive keywords to (action_type, value)
_STATUS_MAP = {
    "in-progress": "In Progress",
    "in-review": "In Review",
    "done": "Done",
    "resolved": "Done",
    "closed": "Done",
}

_JIRA_ID_RE = re.compile(r"^([A-Z][A-Z0-9]+-\d+)")

# Matches #comment <text> or #<status-keyword>
# The comment directive captures everything until the next # directive or end of string
_DIRECTIVE_RE = re.compile(
    r"#(comment)\s+(.*?)(?=\s+#\w|\s*$)"
    r"|#(in-progress|in-review|done|resolved|closed)\b",
    re.IGNORECASE,
)


def extract_jira_id(message: str) -> str | None:
    """Extract Jira issue key from commit message.

    Args:
        message: Full commit message.

    Returns:
        Issue key (e.g. "PROJ-123") or None.
    """
    m = _JIRA_ID_RE.search(message)
    return m.group(1) if m else None


def parse_directives(message: str) -> list[tuple[str, str]]:
    """Parse smart commit directives from a commit message.

    Args:
        message: Full commit message.

    Returns:
        List of (action_type, value) tuples.
        action_type is "comment" or "transition".
    """
    results: list[tuple[str, str]] = []

    for m in _DIRECTIVE_RE.finditer(message):
        if m.group(1):
            # #comment <text>
            results.append(("comment", m.group(2).strip()))
        elif m.group(3):
            # Status keyword
            keyword = m.group(3).lower()
            status = _STATUS_MAP.get(keyword)
            if status:
                results.append(("transition", status))

    return results


def detect_backend(
    shell_script: str = "",
    python_module: str = "",
) -> str | None:
    """Detect which Jira API backend to use.

    Prefers shell script when jq is available, falls back to Python.

    Args:
        shell_script: Path to jira-api.sh.
        python_module: Path to jira_api.py.

    Returns:
        "shell", "python", or None if neither available.
    """
    if Path(shell_script).exists() and shutil.which("jq"):
        return "shell"
    if Path(python_module).exists():
        return "python"
    return None


def dispatch(
    backend: str,
    shell_script: str,
    python_module: str,
    issue_key: str,
    directives: list[tuple[str, str]],
) -> None:
    """Dispatch directives to the Jira API.

    Fire-and-forget: all errors are silently swallowed.

    Args:
        backend: "shell" or "python".
        shell_script: Path to jira-api.sh.
        python_module: Path to jira_api.py.
        issue_key: Jira issue key.
        directives: List of (action_type, value) tuples.
    """
    for action_type, value in directives:
        try:
            if action_type == "comment":
                cmd = _build_comment_cmd(backend, shell_script, python_module, issue_key, value)
            elif action_type == "transition":
                cmd = _build_transition_cmd(backend, shell_script, python_module, issue_key, value)
            else:
                continue

            subprocess.run(cmd, timeout=30, capture_output=True)
        except Exception:
            # Fire-and-forget \u2014 never fail a committed change
            pass


def _build_comment_cmd(
    backend: str, shell_script: str, python_module: str,
    issue_key: str, text: str,
) -> list[str]:
    if backend == "shell":
        return ["bash", shell_script, "add-comment", issue_key, text]
    return ["python3", python_module, "add-comment", issue_key, text]


def _build_transition_cmd(
    backend: str, shell_script: str, python_module: str,
    issue_key: str, status: str,
) -> list[str]:
    if backend == "shell":
        return ["bash", shell_script, "transition-issue", issue_key, status]
    return ["python3", python_module, "transition-issue", issue_key, status]


def has_credentials(env_path: str) -> bool:
    """Check if Jira credentials exist in a .env file.

    Args:
        env_path: Path to .env file.

    Returns:
        True if file exists and contains required credentials.
    """
    path = Path(env_path)
    if not path.exists():
        return False

    env_vars: dict[str, str] = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            env_vars[key.strip()] = value.strip()

    url = env_vars.get("JIRA_URL", "")
    username = env_vars.get("JIRA_USERNAME") or env_vars.get("JIRA_EMAIL", "")
    token = env_vars.get("JIRA_API_TOKEN") or env_vars.get("JIRA_TOKEN", "")

    return bool(url and username and token)


def main() -> None:
    """Entry point for post-commit hook."""
    # Get commit message
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%B"],
            capture_output=True, text=True, timeout=10,
        )
        message = result.stdout.strip()
    except Exception:
        return

    if not message:
        return

    # Extract Jira ID
    issue_key = extract_jira_id(message)
    if not issue_key:
        return

    # Parse directives
    directives = parse_directives(message)
    if not directives:
        return

    # Check credentials
    repo_root = Path(__file__).resolve().parent.parent.parent
    env_candidates = [repo_root / ".env", Path.home() / ".env"]
    env_path = None
    for p in env_candidates:
        if p.exists():
            env_path = str(p)
            break

    if not env_path or not has_credentials(env_path):
        return

    # Detect backend
    utils_dir = repo_root / ".claude" / "utils"
    shell_script = str(utils_dir / "jira-api.sh")
    python_module = str(utils_dir / "jira_api.py")

    backend = detect_backend(shell_script, python_module)
    if not backend:
        return

    # Dispatch (fire-and-forget)
    dispatch(backend, shell_script, python_module, issue_key, directives)


if __name__ == "__main__":
    main()
