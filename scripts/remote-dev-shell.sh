#!/usr/bin/env bash
# remote-dev-shell.sh - Open a durable remote dev shell in tmux with optional tunnel bootstrap.
#
# Run this from your Mac (or any client machine):
#   bash scripts/remote-dev-shell.sh [remote_host] [remote_repo_path] [mac_ssh_target]
#
# Example:
#   bash scripts/remote-dev-shell.sh ai-server2 /home/ai-server2/04-voice-mode-4-loop coffeedev
#
# If mac_ssh_target is provided, the remote host will run:
#   scripts/reverse-tunnel.sh start <mac_ssh_target>
# before attaching to tmux.

set -euo pipefail

REMOTE_HOST="${1:-${REMOTE_HOST:-ai-server2}}"
REMOTE_REPO="${2:-${REMOTE_REPO:-/home/ai-server2/04-voice-mode-4-loop}}"
MAC_SSH_TARGET="${3:-${MAC_SSH_TARGET:-}}"
TMUX_SESSION="${TMUX_SESSION:-sejfa}"
REMOTE_HELPER="${REMOTE_REPO}/scripts/remote-dev-shell-remote.sh"

ssh -tt "$REMOTE_HOST" \
  "bash '$REMOTE_HELPER' '$REMOTE_REPO' '$TMUX_SESSION' '$MAC_SSH_TARGET'"
