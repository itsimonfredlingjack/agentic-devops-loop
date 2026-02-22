# Remote Dev Workflow (Mac + ai-server2)

Use this when your heavy stack (Whisper/Ollama/backend) runs on `ai-server2`, but the Tauri voice app runs on your Mac.

## Why this setup

- Keep GPU/CPU-heavy services on `ai-server2`.
- Keep the app UI and microphone on macOS.
- Expose backend to Mac as `http://localhost:8000` using a reverse SSH tunnel.

## One-command remote shell (recommended)

Run from your Mac terminal:

```bash
bash scripts/remote-dev-shell.sh ai-server2 /home/ai-server2/04-voice-mode-4-loop coffeedev
```

What this does:
- SSH into `ai-server2`.
- Starts/reuses reverse tunnel (`coffeedev` target) if possible.
- Attaches to a persistent `tmux` session named `sejfa`.

You can change defaults with env vars:

```bash
REMOTE_HOST=ai-server2 TMUX_SESSION=sejfa bash scripts/remote-dev-shell.sh
```

## Reverse tunnel management (on ai-server2)

The tunnel maps:
- Mac `localhost:8000` -> ai-server2 `localhost:8000`

Commands:

```bash
bash scripts/reverse-tunnel.sh start coffeedev
bash scripts/reverse-tunnel.sh status coffeedev
bash scripts/reverse-tunnel.sh restart coffeedev
bash scripts/reverse-tunnel.sh stop coffeedev
```

If `autossh` is installed, it is used automatically. Otherwise it falls back to `ssh` with keepalive options.

## Verify end-to-end

1. On ai-server2, run backend on port `8000`.
2. On Mac, test:

```bash
curl -i http://localhost:8000/health
```

Expected: `HTTP/1.1 200 OK`.

## Optional: auto-start tunnel with systemd (ai-server2)

Install services:

```bash
sudo bash scripts/systemd/install.sh
```

Enable tunnel instance for your Mac alias (`coffeedev` example):

```bash
sudo systemctl enable --now sejfa-reverse-tunnel@coffeedev
systemctl status sejfa-reverse-tunnel@coffeedev
journalctl -u sejfa-reverse-tunnel@coffeedev -f
```

## Optional: LaunchAgent (Mac)

If you want tunnel/client command on login, use a local macOS LaunchAgent that runs your preferred command (for example `ssh ai-server2 ...`). This repo currently provides server-side automation via `systemd`.
