#!/usr/bin/env python3
"""Call Jules API directly and post findings as GitHub PR review comment.

Replaces google-labs-code/jules-action to avoid unwanted PR creation.
Uses only stdlib — no pip install needed in CI.

API Reference: https://jules.google/docs/api/reference/sessions
"""

from __future__ import annotations

import json
import os
import subprocess
import time
import urllib.error
import urllib.request

JULES_API_BASE = "https://jules.googleapis.com/v1alpha"
POLL_INTERVAL_SEC = 15
MAX_POLL_SEC = 540  # 9 min (workflow timeout is 20 min)
REQUEST_TIMEOUT_SEC = 30


def _log(msg: str, level: str = "notice") -> None:
    print(f"::{level}::{msg}" if level != "notice" else msg, flush=True)


def _jules_request(
    path: str,
    *,
    method: str = "GET",
    body: dict | None = None,
    api_key: str,
) -> dict:
    url = f"{JULES_API_BASE}{path}"
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key,
    }
    data = json.dumps(body).encode("utf-8") if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_SEC) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw.strip() else {}
    except urllib.error.HTTPError as exc:
        resp_body = (
            exc.read().decode("utf-8", errors="replace") if exc.fp else ""
        )
        _log(
            f"Jules API {method} {path} -> {exc.code}: {resp_body}",
            "error",
        )
        raise
    except urllib.error.URLError as exc:
        _log(f"Jules API connection failed: {exc.reason}", "error")
        raise


def derive_source_name(repo: str) -> str:
    """Derive Jules source name from GITHUB_REPOSITORY (owner/repo)."""
    owner, name = repo.split("/", 1)
    return f"sources/github-{owner}-{name}"


def list_sources(api_key: str) -> list[dict]:
    """List connected sources to verify availability."""
    resp = _jules_request("/sources", api_key=api_key)
    return resp.get("sources", [])


def create_session(
    api_key: str,
    prompt: str,
    source_name: str,
    branch: str,
) -> dict:
    """Create a Jules review session — NO automationMode = no PR creation."""
    return _jules_request(
        "/sessions",
        method="POST",
        body={
            "prompt": prompt,
            "sourceContext": {
                "source": source_name,
                "githubRepoContext": {
                    "startingBranch": branch,
                },
            },
            # automationMode intentionally omitted -> review only, no PR
        },
        api_key=api_key,
    )


def poll_session(api_key: str, session_name: str) -> dict | None:
    """Poll until session completes or timeout."""
    path = session_name if session_name.startswith("/") else f"/{session_name}"
    if not path.startswith("/sessions/"):
        path = f"/sessions/{session_name}"

    start = time.monotonic()
    last_state = ""
    while time.monotonic() - start < MAX_POLL_SEC:
        try:
            session = _jules_request(path, api_key=api_key)
        except Exception:
            time.sleep(POLL_INTERVAL_SEC)
            continue

        state = session.get("state", "UNKNOWN")
        elapsed = int(time.monotonic() - start)
        if state != last_state:
            _log(f"  Session state: {state} ({elapsed}s)")
            last_state = state

        if state.upper() in ("COMPLETED", "FAILED"):
            return session

        time.sleep(POLL_INTERVAL_SEC)

    _log("Jules session timed out", "warning")
    return None


def extract_review_text(session: dict) -> str:
    """Extract readable review text from completed session response."""
    parts: list[str] = []

    # Check outputs array (completed sessions have this)
    outputs = session.get("outputs", [])
    if isinstance(outputs, list):
        for output in outputs:
            if not isinstance(output, dict):
                continue
            pr_info = output.get("pullRequest", {})
            if isinstance(pr_info, dict) and pr_info:
                title = pr_info.get("title", "")
                desc = pr_info.get("description", "")
                url = pr_info.get("url", "")
                if title:
                    parts.append(f"**PR Title:** {title}")
                if desc:
                    parts.append(desc)
                if url:
                    parts.append(f"PR URL: {url}")

    # Check plan (sessions expose their plan)
    plan = session.get("plan", {})
    if isinstance(plan, dict):
        for key in ("description", "summary"):
            val = plan.get(key, "")
            if isinstance(val, str) and val.strip():
                parts.append(val.strip())
        steps = plan.get("steps", [])
        if isinstance(steps, list):
            step_texts: list[str] = []
            for item in steps:
                if isinstance(item, str) and item.strip():
                    step_texts.append(f"- {item.strip()}")
                elif isinstance(item, dict):
                    desc = item.get(
                        "description", item.get("content", "")
                    )
                    if desc:
                        step_texts.append(f"- {str(desc).strip()}")
            if step_texts:
                parts.append("**Plan steps:**\n" + "\n".join(step_texts))

    # Check session-level text fields
    for key in ("response", "output", "result", "summary", "review"):
        val = session.get(key, "")
        if val and isinstance(val, str) and val.strip():
            parts.append(val.strip())

    if not parts:
        _log("No structured findings found, using raw session data")
        raw = json.dumps(session, indent=2, ensure_ascii=False)
        if len(raw) > 3000:
            raw = raw[:3000] + "\n...(truncated)"
        parts.append(f"Raw session data:\n```json\n{raw}\n```")

    return "\n\n".join(parts)


def format_review_body(
    review_text: str,
    session_id: str,
    session_url: str = "",
) -> str:
    """Format the final PR review comment body."""
    header = "## \U0001f50d Jules Code Review\n\n"
    link = f"[View session]({session_url})" if session_url else ""
    footer = (
        f"\n\n---\n"
        f"*Automated review via Jules API (session: `{session_id}`)*"
        f"{' | ' + link if link else ''}\n"
        f"*Mode: `api_direct_review_comment` — no PRs created*"
    )

    max_body = 60000
    body = review_text
    if len(body) > max_body:
        body = body[:max_body] + "\n\n...(truncated)"

    return header + body + footer


def post_review_comment(
    repo: str,
    pr_number: str,
    head_sha: str,
    body: str,
) -> bool:
    """Post a PR review comment via gh CLI."""
    payload = json.dumps(
        {
            "body": body,
            "event": "COMMENT",
            "commit_id": head_sha,
        }
    )

    result = subprocess.run(
        [
            "gh",
            "api",
            f"repos/{repo}/pulls/{pr_number}/reviews",
            "--method",
            "POST",
            "--input",
            "-",
        ],
        input=payload,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        _log(f"Failed to post review via gh api: {result.stderr}", "error")
        _log("Falling back to regular issue comment...")
        fallback = subprocess.run(
            [
                "gh",
                "api",
                f"repos/{repo}/issues/{pr_number}/comments",
                "--method",
                "POST",
                "-f",
                f"body={body}",
            ],
            capture_output=True,
            text=True,
        )
        if fallback.returncode != 0:
            _log(
                f"Fallback comment also failed: {fallback.stderr}", "error"
            )
            return False
        _log(f"Posted as regular comment on PR #{pr_number}")
        return True

    _log(f"Review comment posted on PR #{pr_number}")
    return True


def main() -> int:
    api_key = os.environ.get("JULES_API_KEY", "").strip()
    repo = os.environ.get("GITHUB_REPOSITORY", "").strip()
    pr_number = os.environ.get("PR_NUMBER", "").strip()
    head_sha = os.environ.get("HEAD_SHA", "").strip()
    head_ref = os.environ.get("HEAD_REF", "main").strip()
    context = os.environ.get("JULES_CONTEXT", "").strip()

    if not api_key:
        _log("JULES_API_KEY not set", "error")
        return 1
    if not repo or not pr_number:
        _log("GITHUB_REPOSITORY or PR_NUMBER missing", "error")
        return 1

    # Derive source name from repo (owner/repo -> sources/github-owner-repo)
    source_name = derive_source_name(repo)
    _log(f"Derived source: {source_name}")

    # Verify source exists
    try:
        sources = list_sources(api_key)
        source_names = [s.get("name", "") for s in sources]
        if source_name not in source_names:
            _log(
                f"Source {source_name} not found in connected sources. "
                f"Available: {source_names}",
                "warning",
            )
            if source_names:
                _log(
                    "Tip: Install the Jules GitHub App on your repo at "
                    "https://jules.google",
                    "warning",
                )
    except Exception as exc:
        _log(
            f"Could not list sources ({exc}), proceeding with derived name",
            "warning",
        )

    # Build review prompt
    prompt = (
        "You are the automated PR reviewer for this repository.\n"
        "Review the code changes on the current branch and provide "
        "concise, actionable feedback.\n"
        "Prioritize: correctness > security > reliability > test coverage.\n"
        "Return at most 8 findings sorted by severity.\n"
        "Format each finding as: [SEVERITY] file:line \u2014 description\n"
        "Do NOT create a pull request or make any code changes.\n\n"
    )
    if context:
        prompt += f"PR CONTEXT:\n{context}"

    # Step 1: Create session
    _log(f"Creating Jules review session for {repo} PR #{pr_number}...")
    _log(f"  Source: {source_name}, Branch: {head_ref}")
    try:
        session = create_session(api_key, prompt, source_name, head_ref)
    except Exception as exc:
        body = (
            "\u26a0\ufe0f **Jules Review** \u2014 Failed to create review session.\n\n"
            f"Error: `{exc}`\n\n"
            "The Jules API may be temporarily unavailable. "
            "Manual review recommended."
        )
        if head_sha:
            post_review_comment(repo, pr_number, head_sha, body)
        return 1

    # Extract session ID (API returns "name": "sessions/abc123")
    session_name = session.get("name", "")
    session_id = (
        session_name.split("/")[-1]
        if session_name
        else session.get("id", "")
    )
    session_url = session.get("url", "")

    if not session_id:
        _log(f"No session ID in response: {json.dumps(session)}", "error")
        body = (
            "\u26a0\ufe0f **Jules Review** \u2014 API returned unexpected response.\n\n"
            f"```json\n{json.dumps(session, indent=2)[:2000]}\n```"
        )
        if head_sha:
            post_review_comment(repo, pr_number, head_sha, body)
        return 1

    _log(f"Session created: {session_id}")
    if session_url:
        _log(f"  Dashboard: {session_url}")

    # Step 2: Poll for completion
    _log("Polling for completion...")
    final_session = poll_session(api_key, session_name or session_id)

    if final_session is None:
        body = (
            "\u23f1\ufe0f **Jules Review** \u2014 "
            "Session timed out after 9 minutes.\n\n"
            f"Session ID: `{session_id}`\n"
            "Manual review recommended."
        )
        if head_sha:
            post_review_comment(repo, pr_number, head_sha, body)
        return 1

    state = final_session.get("state", "UNKNOWN").upper()
    _log(f"Session finished with state: {state}")

    if state == "FAILED":
        error_msg = final_session.get(
            "error", final_session.get("message", "Unknown error")
        )
        body = (
            f"\u274c **Jules Review** \u2014 Session failed.\n\n"
            f"Error: `{error_msg}`\n"
            f"Session ID: `{session_id}`"
        )
        if head_sha:
            post_review_comment(repo, pr_number, head_sha, body)
        return 1

    # Step 3: Extract findings from session response
    _log("Extracting review findings...")
    review_text = extract_review_text(final_session)
    review_body = format_review_body(review_text, session_id, session_url)

    if not head_sha:
        _log("No HEAD_SHA \u2014 printing review to stdout only")
        print(review_body)
        return 0

    success = post_review_comment(repo, pr_number, head_sha, review_body)
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
