#!/usr/bin/env bash
# remote-dev-shell-remote.sh - Executed on remote host to attach/create tmux dev session.

set -euo pipefail

REMOTE_REPO="${1:-}"
TMUX_SESSION="${2:-sejfa}"
MAC_SSH_TARGET="${3:-}"

if [[ -z "$REMOTE_REPO" ]]; then
  echo "Remote repo path argument is required." >&2
  exit 2
fi

if [[ ! -d "$REMOTE_REPO" ]]; then
  echo "Remote repo path not found: $REMOTE_REPO" >&2
  exit 1
fi

cd "$REMOTE_REPO"

if [[ -n "$MAC_SSH_TARGET" && -x "./scripts/reverse-tunnel.sh" ]]; then
  ./scripts/reverse-tunnel.sh start "$MAC_SSH_TARGET" || true
fi

if ! command -v tmux >/dev/null 2>&1; then
  echo "tmux is required on remote host but was not found." >&2
  exit 1
fi

# Some local terminals (for example Ghostty) advertise TERM values that may
# not exist on remote hosts. Fall back to common terminfo entries for tmux.
safe_term="${TERM:-xterm-256color}"
if [[ "$safe_term" == "xterm-ghostty" ]]; then
  safe_term="xterm-256color"
fi

if command -v infocmp >/dev/null 2>&1; then
  if ! infocmp "$safe_term" >/dev/null 2>&1; then
    for fallback in xterm-256color screen-256color xterm; do
      if infocmp "$fallback" >/dev/null 2>&1; then
        safe_term="$fallback"
        break
      fi
    done
  fi
else
  safe_term="xterm-256color"
fi
export TERM="$safe_term"

if ! tmux has-session -t "$TMUX_SESSION" 2>/dev/null; then
  tmux new-session -d -s "$TMUX_SESSION" -c "$REMOTE_REPO"
fi

exec tmux attach -t "$TMUX_SESSION"
