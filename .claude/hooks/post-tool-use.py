#!/usr/bin/env python3
"""
PostToolUse Monitor Hook

Posts events to the agent monitor API after Claude performs actions.
Uses non-blocking requests to avoid slowing down Claude.
Handles failures gracefully - Claude continues even if monitor is down.

Exit codes:
- 0: Always (never blocks Claude)
"""

import json
import sys
import os
import threading
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError


# ============================================================================
# CONFIGURATION
# ============================================================================

MONITOR_API_URL = "https://agent-monitor.fredlingautomation.dev/api/event"
TIMEOUT_SECONDS = 2  # Don't wait long for the monitor
SOURCE = "claude"

# Map tool names to human-readable descriptions
TOOL_DESCRIPTIONS = {
    "bash": "Running command",
    "read": "Reading file",
    "write": "Writing to",
    "edit": "Editing",
    "glob": "Searching for files",
    "grep": "Searching in files",
    "webfetch": "Fetching web content",
    "websearch": "Searching the web",
}

# Map operations to event types
OPERATION_EVENT_TYPES = {
    "read": "info",
    "glob": "info",
    "grep": "info",
    "write": "info",
    "edit": "info",
    "bash": "info",
    "webfetch": "info",
    "websearch": "info",
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_task_id():
    """Extract task_id from environment or CURRENT_TASK.md if available."""
    # Check environment first
    task_id = os.environ.get("TASK_ID") or os.environ.get("JIRA_TASK_ID")
    if task_id:
        return task_id

    # Try to extract from CURRENT_TASK.md
    current_task_paths = [
        Path.cwd() / "docs" / "CURRENT_TASK.md",
        Path.cwd() / "CURRENT_TASK.md",
    ]

    for task_path in current_task_paths:
        if task_path.exists():
            try:
                content = task_path.read_text()
                # Look for patterns like "PROJ-123" or "Task: PROJ-123"
                import re
                match = re.search(r"([A-Z]+-\d+)", content)
                if match:
                    return match.group(1)
            except Exception:
                pass

    return None


def format_message(tool_name: str, tool_input: dict) -> str:
    """Format a human-readable message for the event."""
    tool_lower = tool_name.lower()
    description = TOOL_DESCRIPTIONS.get(tool_lower, f"Using {tool_name}")

    # Extract relevant details based on tool type
    if tool_lower in ["read", "write", "edit"]:
        file_path = tool_input.get("file_path", "") or tool_input.get("path", "")
        if file_path:
            # Shorten path for display
            path_obj = Path(file_path)
            short_path = str(path_obj.name) if len(file_path) > 50 else file_path
            return f"Claude: {description} {short_path}"

    elif tool_lower == "bash":
        command = tool_input.get("command", "")
        # Extract the main command (first word or first part before space)
        if command:
            main_cmd = command.split()[0] if command.split() else command
            # Shorten if too long
            if len(command) > 50:
                command = command[:47] + "..."

            # Special cases for common commands
            if main_cmd in ["git", "pytest", "npm", "ruff", "eslint"]:
                return f"Claude: {main_cmd} {' '.join(command.split()[1:3])}"
            return f"Claude: {description}: {command[:50]}"

    elif tool_lower == "glob":
        pattern = tool_input.get("pattern", "")
        return f"Claude: {description} matching {pattern}"

    elif tool_lower == "grep":
        pattern = tool_input.get("pattern", "")
        return f"Claude: {description} for '{pattern[:30]}'"

    return f"Claude: {description}"


def get_event_type(tool_name: str, tool_result: dict) -> str:
    """Determine event type based on tool and result."""
    tool_lower = tool_name.lower()

    # Check if there was an error in the result
    if tool_result:
        error = tool_result.get("error") or tool_result.get("stderr", "")
        if error and "error" in str(error).lower():
            return "warning"

    return OPERATION_EVENT_TYPES.get(tool_lower, "info")


def post_event_async(payload: dict):
    """Post event to monitor API in a background thread (non-blocking)."""
    def _post():
        try:
            data = json.dumps(payload).encode("utf-8")
            request = Request(
                MONITOR_API_URL,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urlopen(request, timeout=TIMEOUT_SECONDS) as _response:
                pass  # We don't need the response
        except (URLError, HTTPError, TimeoutError, Exception):
            # Silently ignore all errors - don't slow down Claude
            pass

    # Start in background thread so we don't block
    thread = threading.Thread(target=_post, daemon=True)
    thread.start()
    # Don't join - let it run in background


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main hook logic."""
    try:
        # Read input from stdin
        input_data = sys.stdin.read()

        if not input_data.strip():
            sys.exit(0)  # No input, exit

        try:
            hook_input = json.loads(input_data)
        except json.JSONDecodeError:
            sys.exit(0)  # Invalid JSON, exit silently

        tool_name = hook_input.get("tool_name", "")
        tool_input = hook_input.get("tool_input", {})
        tool_result = hook_input.get("tool_result", {})

        if not tool_name:
            sys.exit(0)

        # Build the event payload
        message = format_message(tool_name, tool_input)
        event_type = get_event_type(tool_name, tool_result)
        task_id = get_task_id()

        payload = {
            "event_type": event_type,
            "message": message,
            "source": SOURCE,
        }

        # Add optional fields
        if task_id:
            payload["task_id"] = task_id

        # Add tool metadata
        payload["metadata"] = {
            "tool": tool_name,
            "timestamp": __import__("datetime").datetime.now().isoformat(),
        }

        # Post event asynchronously (non-blocking)
        post_event_async(payload)

        # Always exit successfully - never block Claude
        sys.exit(0)

    except Exception:
        # Fail silently on any error
        sys.exit(0)


if __name__ == "__main__":
    main()
