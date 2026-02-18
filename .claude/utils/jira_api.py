#!/usr/bin/env python3
"""
Python Jira API Fallback

Mirrors jira-api.sh CLI interface using only stdlib (urllib.request).
Commands: ping, get-issue, transition-issue, add-comment, search

Usage:
    python3 jira_api.py ping
    python3 jira_api.py get-issue PROJ-123
    python3 jira_api.py transition-issue PROJ-123 "In Progress"
    python3 jira_api.py add-comment PROJ-123 "Comment text"
    python3 jira_api.py search "project = DEV ORDER BY created DESC"
"""

import base64
import json
import os
import sys
import urllib.parse
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class JiraAPIError(Exception):
    """Raised when a Jira API call fails."""


def load_credentials(env_path: str | None = None) -> dict:
    """Load Jira credentials from environment or a .env file.

    Supports both JIRA_USERNAME/JIRA_EMAIL and JIRA_API_TOKEN/JIRA_TOKEN.

    Args:
        env_path: Optional path to .env file.

    Returns:
        Dict with keys: url, username, token.

    Raises:
        FileNotFoundError: If env_path is provided but .env file doesn't exist.
        ValueError: If required credentials are missing.
    """
    env_vars: dict[str, str] = {}
    keys = ("JIRA_URL", "JIRA_USERNAME", "JIRA_EMAIL", "JIRA_API_TOKEN", "JIRA_TOKEN")
    for key in keys:
        value = os.environ.get(key)
        if value:
            env_vars[key] = value

    if env_path:
        path = Path(env_path)
        if not path.exists():
            raise FileNotFoundError(f".env file not found: {env_path}")
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip()
                # Strip surrounding quotes
                if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                    value = value[1:-1]
                if key and key not in env_vars:
                    env_vars[key] = value

    url = env_vars.get("JIRA_URL", "")
    username = env_vars.get("JIRA_USERNAME") or env_vars.get("JIRA_EMAIL", "")
    token = env_vars.get("JIRA_API_TOKEN") or env_vars.get("JIRA_TOKEN", "")

    if not url or not username or not token:
        raise ValueError(
            "Missing Jira credentials in environment or .env "
            "(need JIRA_URL, username, token)"
        )

    return {"url": url.rstrip("/"), "username": username, "token": token}


def find_env_file() -> str:
    """Find .env file in cwd or home directory.

    Returns:
        Path to .env file.

    Raises:
        FileNotFoundError: If no .env file found.
    """
    candidates = [
        Path.cwd() / ".env",
        Path.home() / ".env",
    ]
    for p in candidates:
        if p.exists():
            return str(p)
    raise FileNotFoundError(".env file not found in cwd or home directory")


def build_headers(creds: dict) -> dict:
    """Build HTTP headers with Basic auth.

    Args:
        creds: Dict with username and token.

    Returns:
        Dict of HTTP headers.
    """
    auth_bytes = f"{creds['username']}:{creds['token']}".encode()
    auth_b64 = base64.b64encode(auth_bytes).decode()
    return {
        "Authorization": f"Basic {auth_b64}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def _api_request(
    creds: dict, method: str, path: str, data: dict | None = None
) -> dict | None:
    """Make an authenticated Jira API request.

    Args:
        creds: Credentials dict.
        method: HTTP method (GET, POST).
        path: API path (appended to base URL).
        data: Optional JSON body.

    Returns:
        Parsed JSON response, or None for empty responses.

    Raises:
        JiraAPIError: On HTTP errors.
    """
    url = f"{creds['url']}/rest/api/3{path}"
    headers = build_headers(creds)
    body = json.dumps(data).encode() if data else None

    req = Request(url, data=body, headers=headers, method=method)

    try:
        with urlopen(req) as resp:
            raw = resp.read()
            if not raw:
                return None
            return json.loads(raw)
    except HTTPError as e:
        raise JiraAPIError(f"HTTP {e.code}: {e.reason} \u2014 {url}") from e
    except URLError as e:
        raise JiraAPIError(f"Connection error: {e.reason} \u2014 {url}") from e


def get_issue(creds: dict, issue_key: str) -> dict:
    """Fetch a Jira issue by key.

    Uses /rest/api/3/issue/{key} (singular, not issues/).

    Args:
        creds: Credentials dict.
        issue_key: e.g. "PROJ-123".

    Returns:
        Issue data dict.
    """
    return _api_request(creds, "GET", f"/issue/{issue_key}")


def transition_issue(creds: dict, issue_key: str, status_name: str) -> None:
    """Transition a Jira issue to a new status.

    Uses /rest/api/3/issue/{key}/transitions (singular issue/).

    Args:
        creds: Credentials dict.
        issue_key: e.g. "PROJ-123".
        status_name: Target status name, e.g. "In Progress".

    Raises:
        JiraAPIError: If status not found or API error.
    """
    # Get available transitions
    result = _api_request(creds, "GET", f"/issue/{issue_key}/transitions")
    transitions = result.get("transitions", [])

    # Find matching transition
    transition_id = None
    for t in transitions:
        if t.get("to", {}).get("name") == status_name:
            transition_id = t["id"]
            break

    if transition_id is None:
        raise JiraAPIError(
            f"Status '{status_name}' not found for issue {issue_key}"
        )

    # Execute transition
    _api_request(
        creds, "POST", f"/issue/{issue_key}/transitions",
        data={"transition": {"id": transition_id}}
    )


def add_comment(creds: dict, issue_key: str, text: str) -> dict | None:
    """Add a comment to a Jira issue using ADF format.

    Uses /rest/api/3/issue/{key}/comment (singular issue/).

    Args:
        creds: Credentials dict.
        issue_key: e.g. "PROJ-123".
        text: Comment text.

    Returns:
        API response dict.
    """
    adf_body = {
        "body": {
            "version": 1,
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": text}
                    ],
                }
            ],
        }
    }
    return _api_request(creds, "POST", f"/issue/{issue_key}/comment", data=adf_body)


def ping(creds: dict) -> dict:
    """Verify Jira credentials by calling /myself.

    Args:
        creds: Credentials dict.

    Returns:
        Jira user profile dict.
    """
    return _api_request(creds, "GET", "/myself")


def search_issues(creds: dict, jql: str, max_results: int = 10) -> dict:
    """Search Jira issues using JQL.

    Args:
        creds: Credentials dict.
        jql: JQL query string, e.g. "project = DEV ORDER BY created DESC".
        max_results: Maximum number of results to return (default 10).

    Returns:
        Search results dict containing issues array.
    """
    params = urllib.parse.urlencode({"jql": jql, "maxResults": max_results})
    return _api_request(creds, "GET", f"/search?{params}")


def cli(args: list[str]) -> int:
    """CLI entrypoint \u2014 mirrors jira-api.sh interface.

    Args:
        args: Command-line arguments (without script name).

    Returns:
        Exit code (0 = success, 1 = error).
    """
    if not args:
        print("Usage: jira_api.py <command> [args...]", file=sys.stderr)
        print(
            "Commands: ping, get-issue, transition-issue, add-comment, search",
            file=sys.stderr,
        )
        return 1

    command = args[0]

    env_path = None
    try:
        env_path = find_env_file()
    except FileNotFoundError:
        env_path = None

    try:
        creds = load_credentials(env_path)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    try:
        if command == "ping":
            result = ping(creds)
            print(json.dumps(result, indent=2))
            return 0

        elif command == "get-issue":
            if len(args) < 2:
                print("Usage: jira_api.py get-issue ISSUE_KEY", file=sys.stderr)
                return 1
            result = get_issue(creds, args[1])
            print(json.dumps(result, indent=2))
            return 0

        elif command == "transition-issue":
            if len(args) < 3:
                print(
                    "Usage: jira_api.py transition-issue ISSUE_KEY STATUS",
                    file=sys.stderr,
                )
                return 1
            transition_issue(creds, args[1], args[2])
            print(f"Transitioned {args[1]} to {args[2]}")
            return 0

        elif command == "add-comment":
            if len(args) < 3:
                print(
                    "Usage: jira_api.py add-comment ISSUE_KEY 'text'", file=sys.stderr
                )
                return 1
            add_comment(creds, args[1], args[2])
            print(f"Comment added to {args[1]}")
            return 0

        elif command == "search":
            if len(args) < 2:
                print("Usage: jira_api.py search 'JQL query'", file=sys.stderr)
                return 1
            max_results = int(args[2]) if len(args) > 2 else 10
            result = search_issues(creds, args[1], max_results)
            print(json.dumps(result, indent=2))
            return 0

        else:
            print(f"Unknown command: {command}", file=sys.stderr)
            print(
                "Commands: ping, get-issue, transition-issue, add-comment, search",
                file=sys.stderr,
            )
            return 1

    except JiraAPIError as e:
        print(f"Jira API error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(cli(sys.argv[1:]))
