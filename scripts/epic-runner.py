#!/usr/bin/env python3
"""Epic-tuggaren — Feed an entire Jira Epic to the Ralph Loop.

Fetches all child issues from a Jira Epic and enqueues them
for automatic processing by the loop-runner.

Usage:
    python3 scripts/epic-runner.py DEV-42
    python3 scripts/epic-runner.py DEV-42 --dry-run
    python3 scripts/epic-runner.py DEV-42 --status "To Do"
    python3 scripts/epic-runner.py DEV-42 --backend http://localhost:8000

Environment:
    Reads .env for JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN
"""

import argparse
import json
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

# Add project root to path so we can import the Jira client
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

try:
    from dotenv import load_dotenv

    load_dotenv(project_root / ".env")
except ImportError:
    pass

from src.sejfa.integrations.jira_client import JiraAPIError, JiraClient, JiraIssue  # noqa: E402


def fetch_epic_children(
    client: JiraClient, epic_key: str, status_filter: str | None = None
) -> list[JiraIssue]:
    """Fetch all child issues of an Epic."""
    jql = f'"Epic Link" = {epic_key} OR parent = {epic_key}'
    if status_filter:
        jql += f' AND status = "{status_filter}"'
    jql += " ORDER BY rank ASC"

    print(f"  JQL: {jql}")
    return client.search_issues(jql, max_results=100)


def enqueue_ticket(backend_url: str, key: str, summary: str) -> str:
    """POST a ticket to the backend's enqueue endpoint."""
    url = f"{backend_url}/api/loop/enqueue"
    payload = json.dumps({"key": key, "summary": summary}).encode()
    req = Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")

    try:
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            return data.get("status", "unknown")
    except URLError as e:
        return f"error: {e.reason}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Epic-tuggaren: feed a Jira Epic to Ralph Loop")
    parser.add_argument("epic_key", help="Jira Epic key (e.g., DEV-42)")
    parser.add_argument("--backend", default="http://localhost:8000", help="Backend URL")
    parser.add_argument(
        "--status", default=None, help="Only include issues with this status (e.g., 'To Do')"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be enqueued without doing it"
    )
    args = parser.parse_args()

    print("Epic-tuggaren")
    print(f"  Epic:    {args.epic_key}")
    print(f"  Backend: {args.backend}")
    if args.status:
        print(f"  Filter:  status = '{args.status}'")
    if args.dry_run:
        print("  Mode:    DRY RUN")
    print()

    # Connect to Jira
    try:
        client = JiraClient()
    except ValueError as e:
        print(f"Jira config error: {e}")
        print("Make sure .env has JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN")
        sys.exit(1)

    # Fetch the Epic itself
    print(f"Fetching Epic {args.epic_key}...")
    try:
        epic = client.get_issue(args.epic_key)
        print(f"  {epic.key}: {epic.summary}")
        print(f"  Type: {epic.issue_type}, Status: {epic.status}")
    except JiraAPIError as e:
        print(f"Failed to fetch Epic: {e}")
        sys.exit(1)

    # Fetch children
    print("\nFetching child issues...")
    try:
        children = fetch_epic_children(client, args.epic_key, args.status)
    except JiraAPIError as e:
        print(f"Failed to search: {e}")
        sys.exit(1)

    if not children:
        print("  No child issues found.")
        sys.exit(0)

    print(f"  Found {len(children)} issues:\n")

    # Display table
    print(f"  {'#':<4} {'Key':<12} {'Status':<15} {'Type':<12} Summary")
    print(f"  {'─' * 4} {'─' * 12} {'─' * 15} {'─' * 12} {'─' * 40}")
    for i, issue in enumerate(children, 1):
        print(
            f"  {i:<4} {issue.key:<12} {issue.status:<15} {issue.issue_type:<12} {issue.summary[:50]}"
        )

    if args.dry_run:
        print(f"\n  DRY RUN — {len(children)} tickets would be enqueued.")
        return

    # Enqueue
    print(f"\nEnqueuing {len(children)} tickets to {args.backend}...")
    queued = 0
    dupes = 0
    errors = 0

    for issue in children:
        status = enqueue_ticket(args.backend, issue.key, issue.summary)
        if status == "queued":
            queued += 1
            print(f"  + {issue.key}: queued")
        elif status == "duplicate":
            dupes += 1
            print(f"  ~ {issue.key}: already in queue")
        else:
            errors += 1
            print(f"  ! {issue.key}: {status}")
        time.sleep(0.1)  # gentle on the API

    print(f"\nDone! Queued: {queued}, Duplicates: {dupes}, Errors: {errors}")
    print("Loop runner will process them automatically.")
    if queued > 0:
        est_hours = queued * 0.5  # rough estimate: 30 min per ticket
        print(f"Estimated time: ~{est_hours:.0f}h (at ~30 min/ticket)")


if __name__ == "__main__":
    main()
