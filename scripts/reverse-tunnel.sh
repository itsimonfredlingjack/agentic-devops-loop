#!/usr/bin/env bash
# reverse-tunnel.sh - Manage reverse SSH tunnel so Mac localhost can reach ai-server2 services.
#
# Default mapping:
#   Mac localhost:8000 -> ai-server2 localhost:8000
#
# Usage:
#   bash scripts/reverse-tunnel.sh start [mac_ssh_target]
#   bash scripts/reverse-tunnel.sh stop [mac_ssh_target]
#   bash scripts/reverse-tunnel.sh status [mac_ssh_target]
#   bash scripts/reverse-tunnel.sh restart [mac_ssh_target]
#   bash scripts/reverse-tunnel.sh run [mac_ssh_target]     # foreground (for systemd)
#
# Env overrides:
#   REMOTE_PORT=8000
#   LOCAL_HOST=localhost
#   LOCAL_PORT=8000
#   PID_DIR=/tmp

set -euo pipefail

ACTION="${1:-start}"
SSH_TARGET="${2:-${SSH_TARGET:-coffeedev}}"
REMOTE_PORT="${REMOTE_PORT:-8000}"
LOCAL_HOST="${LOCAL_HOST:-localhost}"
LOCAL_PORT="${LOCAL_PORT:-8000}"
PID_DIR="${PID_DIR:-/tmp}"

if [[ -z "$SSH_TARGET" ]]; then
  echo "Missing SSH target. Provide as arg2 or SSH_TARGET env var." >&2
  exit 1
fi

TUNNEL_ID="$(printf '%s_%s_%s_%s' "$SSH_TARGET" "$REMOTE_PORT" "$LOCAL_HOST" "$LOCAL_PORT" | tr '@/.: ' '_____')"
PID_FILE="$PID_DIR/sejfa-reverse-tunnel-${TUNNEL_ID}.pid"
LOG_FILE="$PID_DIR/sejfa-reverse-tunnel-${TUNNEL_ID}.log"

RUNNER="ssh"
if command -v autossh >/dev/null 2>&1; then
  RUNNER="autossh"
fi

build_cmd() {
  TUNNEL_CMD=()
  if [[ "$RUNNER" == "autossh" ]]; then
    TUNNEL_CMD+=(autossh -M 0)
  else
    TUNNEL_CMD+=(ssh)
  fi

  TUNNEL_CMD+=(
    -N
    -T
    -o ExitOnForwardFailure=yes
    -o ServerAliveInterval=30
    -o ServerAliveCountMax=3
    -o TCPKeepAlive=yes
    -R "${REMOTE_PORT}:${LOCAL_HOST}:${LOCAL_PORT}"
    "$SSH_TARGET"
  )
}

is_running() {
  if [[ ! -f "$PID_FILE" ]]; then
    return 1
  fi

  local pid
  pid="$(cat "$PID_FILE" 2>/dev/null || true)"
  if [[ -z "$pid" ]]; then
    return 1
  fi

  if kill -0 "$pid" 2>/dev/null; then
    return 0
  fi

  return 1
}

find_existing_pid() {
  ps -eo pid=,args= | awk \
    -v rport="$REMOTE_PORT" \
    -v lport="$LOCAL_PORT" \
    -v target="$SSH_TARGET" \
    '($0 ~ /(ssh|autossh)/) && index($0, target) && match($0, "-R " rport ":[^ ]*:" lport) { print $1; exit }'
}

adopt_existing_tunnel() {
  local existing_pid
  existing_pid="$(find_existing_pid || true)"
  if [[ -z "$existing_pid" ]]; then
    return 1
  fi

  echo "$existing_pid" > "$PID_FILE"
  echo "Reusing existing reverse tunnel (pid=$existing_pid)."
  return 0
}

ensure_pid_dir() {
  mkdir -p "$PID_DIR"
}

print_status() {
  if ! is_running; then
    adopt_existing_tunnel >/dev/null 2>&1 || true
  fi

  if is_running; then
    echo "running (pid=$(cat "$PID_FILE"))"
    echo "target=${SSH_TARGET}"
    echo "mapping=remote:${REMOTE_PORT} -> local:${LOCAL_HOST}:${LOCAL_PORT}"
    echo "runner=${RUNNER}"
    echo "log=${LOG_FILE}"
    return 0
  fi

  echo "not running"
  echo "target=${SSH_TARGET}"
  echo "mapping=remote:${REMOTE_PORT} -> local:${LOCAL_HOST}:${LOCAL_PORT}"
  echo "runner=${RUNNER}"
  echo "log=${LOG_FILE}"
  return 1
}

start_tunnel() {
  ensure_pid_dir

  if is_running; then
    echo "Reverse tunnel already running (pid=$(cat "$PID_FILE"))."
    return 0
  fi
  adopt_existing_tunnel >/dev/null 2>&1 && return 0

  rm -f "$PID_FILE"
  build_cmd

  nohup "${TUNNEL_CMD[@]}" >>"$LOG_FILE" 2>&1 &
  local pid=$!
  echo "$pid" > "$PID_FILE"

  sleep 1
  if is_running; then
    echo "Started reverse tunnel (pid=$pid, runner=$RUNNER)."
    echo "Mac localhost:${REMOTE_PORT} now forwards to ai-server2 ${LOCAL_HOST}:${LOCAL_PORT}."
    return 0
  fi

  if adopt_existing_tunnel >/dev/null 2>&1; then
    echo "Reverse tunnel already existed for this mapping and target."
    return 0
  fi

  echo "Failed to start reverse tunnel. Last log lines:" >&2
  if grep -q "remote port forwarding failed for listen port" "$LOG_FILE" 2>/dev/null; then
    echo "Hint: port ${REMOTE_PORT} is already in use on ${SSH_TARGET} (existing tunnel or local service)." >&2
  fi
  tail -n 40 "$LOG_FILE" >&2 || true
  rm -f "$PID_FILE"
  return 1
}

stop_tunnel() {
  if ! is_running; then
    if ! adopt_existing_tunnel >/dev/null 2>&1; then
      echo "Reverse tunnel is not running."
      rm -f "$PID_FILE"
      return 0
    fi
  fi

  local pid
  pid="$(cat "$PID_FILE")"
  kill "$pid" 2>/dev/null || true

  for _ in $(seq 1 20); do
    if ! kill -0 "$pid" 2>/dev/null; then
      rm -f "$PID_FILE"
      echo "Stopped reverse tunnel."
      return 0
    fi
    sleep 0.2
  done

  kill -9 "$pid" 2>/dev/null || true
  rm -f "$PID_FILE"
  echo "Stopped reverse tunnel (forced)."
}

run_foreground() {
  build_cmd
  echo "Running reverse tunnel in foreground (runner=$RUNNER)."
  echo "Mac localhost:${REMOTE_PORT} -> ai-server2 ${LOCAL_HOST}:${LOCAL_PORT}"
  exec "${TUNNEL_CMD[@]}"
}

case "$ACTION" in
  start)
    start_tunnel
    ;;
  stop)
    stop_tunnel
    ;;
  restart)
    stop_tunnel
    start_tunnel
    ;;
  status)
    print_status
    ;;
  run)
    run_foreground
    ;;
  *)
    echo "Unknown action: $ACTION" >&2
    echo "Usage: $0 {start|stop|restart|status|run} [ssh_target]" >&2
    exit 2
    ;;
esac
