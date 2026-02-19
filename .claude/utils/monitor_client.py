#!/usr/bin/env python3
"""
Monitor Client - Lightweight HTTP client for the Agent Monitor API.

Used by hooks and commands to send events and task updates to the monitor.
All methods are non-blocking (fire-and-forget via background threads).
All failures are silently ignored to never block Claude.
"""

import atexit
import json
import threading
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

MONITOR_BASE_URL = "https://agent-monitor.fredlingautomation.dev"
TIMEOUT_SECONDS = 3

# Track pending threads so we can wait for them on exit
_pending_threads: list[threading.Thread] = []


def _flush_pending():
    """Wait for pending sends to complete before process exits (max 2s)."""
    for t in _pending_threads:
        t.join(timeout=2)
    _pending_threads.clear()

atexit.register(_flush_pending)


_HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "AgentMonitor/1.0 (claude-hook)",
    "Accept": "application/json",
}


def _post(url: str, payload: dict):
    """POST JSON to URL. Blocks until complete or timeout."""
    try:
        data = json.dumps(payload).encode("utf-8")
        request = Request(url, data=data, headers=_HEADERS, method="POST")
        with urlopen(request, timeout=TIMEOUT_SECONDS):
            pass
    except (URLError, HTTPError, TimeoutError, OSError, Exception):
        pass  # Silently ignore all errors


def _post_async(url: str, payload: dict):
    """POST in a background thread (non-blocking). Ensures delivery on exit."""
    thread = threading.Thread(target=_post, args=(url, payload), daemon=True)
    _pending_threads.append(thread)
    thread.start()


def send_event(event_type: str, message: str, source: str = "claude",
               task_id: str | None = None, metadata: dict | None = None):
    """Send an event to the monitor (non-blocking)."""
    payload: dict = {
        "event_type": event_type,
        "message": message,
        "source": source,
    }
    if task_id:
        payload["task_id"] = task_id
    if metadata:
        payload["metadata"] = metadata

    _post_async(f"{MONITOR_BASE_URL}/api/event", payload)


def send_task_start(task_id: str, title: str = "",
                    branch: str | None = None,
                    max_iterations: int = 25):
    """Notify monitor that a task has started (non-blocking)."""
    payload: dict = {
        "task_id": task_id,
        "action": "start",
        "title": title,
        "step": 0,
        "step_name": "Jira Ticket",
        "step_desc": "Fetching ticket requirements...",
        "max_iterations": max_iterations,
    }
    if branch:
        payload["branch"] = branch

    _post_async(f"{MONITOR_BASE_URL}/api/task", payload)


def send_task_update(task_id: str, step: int | None = None,
                     step_name: str | None = None,
                     step_desc: str | None = None,
                     status: str | None = None,
                     iteration: int | None = None):
    """Update task state on the monitor (non-blocking)."""
    payload: dict = {
        "task_id": task_id,
        "action": "update",
    }
    if step is not None:
        payload["step"] = step
    if step_name:
        payload["step_name"] = step_name
    if step_desc:
        payload["step_desc"] = step_desc
    if status:
        payload["status"] = status
    if iteration is not None:
        payload["iteration"] = iteration

    _post_async(f"{MONITOR_BASE_URL}/api/task", payload)


def send_task_complete(task_id: str):
    """Notify monitor that a task completed (non-blocking)."""
    _post_async(f"{MONITOR_BASE_URL}/api/task", {
        "task_id": task_id,
        "action": "complete",
    })


def send_task_fail(task_id: str, reason: str = ""):
    """Notify monitor that a task failed (non-blocking)."""
    _post_async(f"{MONITOR_BASE_URL}/api/task", {
        "task_id": task_id,
        "action": "fail",
        "step_desc": reason,
    })


def send_task_reset():
    """Reset the monitor task state (non-blocking)."""
    _post_async(f"{MONITOR_BASE_URL}/api/task", {
        "task_id": "_",
        "action": "reset",
    })
