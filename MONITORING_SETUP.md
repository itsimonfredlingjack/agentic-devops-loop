# Claude Code Monitoring System - Setup & Usage Guide

## Overview

The monitoring system provides real-time visualization of the Claude Code agentic loop workflow. It tracks state transitions between nodes (JIRA, CLAUDE, GITHUB, JULES, ACTIONS) and displays them on an interactive dashboard.

## System Architecture

```
Claude Code CLI
      ↓ (output)
Bash Wrapper (claude-monitor-wrapper.sh)
      ↓ (HTTP POST)
Flask Backend (app.py + monitor routes)
      ↓ (WebSocket)
HTML Dashboard (static/monitor.html)
```

## Files Created

### Core Monitoring Module
- `src/sejfa/monitor/__init__.py` - Module initialization
- `src/sejfa/monitor/monitor_service.py` - State management service
- `src/sejfa/monitor/monitor_routes.py` - Flask API routes and SocketIO handlers

### Wrapper & Dashboard
- `claude-monitor-wrapper.sh` - Bash wrapper for intercepting Claude output
- `static/monitor.html` - Real-time dashboard with WebSocket integration

### Modified Files
- `app.py` - Added Flask-SocketIO and monitoring blueprint integration

## Quick Start

### 1. Start the Flask Monitoring Server

```bash
cd grupp-ett-github
source venv/Scripts/activate  # Windows
python app.py
```

The server runs on `http://localhost:5000`

### 2. Open the Dashboard

Open `grupp-ett-github/static/monitor.html` in your web browser.

### 3. Run Claude with the Wrapper

```bash
./claude-monitor-wrapper.sh "Your prompt here"
```

The wrapper:
- Passes through all Claude output transparently
- Parses each line for workflow patterns
- Sends state updates to the Flask API
- Silently fails if the API is unavailable (doesn't block Claude)

## Pattern Matching

The wrapper detects these patterns and maps to nodes:

| Pattern | Node | Color |
|---------|------|-------|
| git commit, git push, Committing | GITHUB | Blue |
| Running tests, pytest, npm test, Build | ACTIONS | Green |
| Writing to, Creating, Editing | CLAUDE | Cyan |
| Reading, Analyzing, Fetching | JIRA | Purple |
| Reviewing, Code review | JULES | Pink |

## API Endpoints

### Get Current State
```bash
GET /api/monitor/state
```

Response: Full monitoring state snapshot with all nodes, event log, and task info.

### Update Node State
```bash
POST /api/monitor/state
Content-Type: application/json

{
  "node": "claude",
  "state": "active",
  "message": "Writing code..."
}
```

### Update Task Info
```bash
POST /api/monitor/task
Content-Type: application/json

{
  "title": "Implement feature X",
  "status": "running",
  "start_time": "2026-02-05T14:00:00Z"  # Optional
}
```

### Reset Monitoring State
```bash
POST /api/monitor/reset
```

## WebSocket Events

The dashboard connects via WebSocket at `http://localhost:5000/monitor`

### Events Received
- `state_update` - Full state snapshot after any update
- `connect` - Sent immediately when client connects

### Events Sent (by client)
- `request_state` - Ask server for current state

## State Structure

```javascript
{
  "current_node": "claude",  // Currently active node ID or null
  "nodes": {
    "jira": {
      "active": false,
      "last_active": "2026-02-05T14:00:00Z",
      "message": "Fetching ticket..."
    },
    "claude": {
      "active": true,
      "last_active": "2026-02-05T14:01:00Z",
      "message": "Writing code..."
    },
    // ... github, jules, actions
  },
  "event_log": [
    {
      "timestamp": "2026-02-05T14:00:00Z",
      "node": "jira",
      "message": "Fetching ticket..."
    },
    // ... more events
  ],
  "task_info": {
    "title": "Implement monitoring",
    "status": "running",  // idle, running, completed, failed
    "start_time": "2026-02-05T14:00:00Z"
  }
}
```

## Monitoring Wrapper Usage

### Basic Usage
```bash
./claude-monitor-wrapper.sh "List files"
```

### With Real Claude CLI
```bash
./claude-monitor-wrapper.sh claude "Implement feature X"
```

### With Complex Commands
```bash
./claude-monitor-wrapper.sh bash -c "npm run build && npm test"
```

The wrapper:
- Executes the command transparently
- Outputs everything as-is (no interference)
- Logs to `~/.claude-monitor.log` for debugging
- Sends state updates asynchronously

## Logging

Wrapper logs go to `~/.claude-monitor.log`:

```bash
tail -f ~/.claude-monitor.log
```

Example log output:
```
[2026-02-05 14:00:00] Claude Monitor Wrapper started with args: echo "Reading file"
[2026-02-05 14:00:00] Sent: node=jira, message=Reading file
[2026-02-05 14:00:01] Claude Monitor Wrapper completed
```

## Dashboard Features

### Real-Time Visualization
- Animated circular workflow with 5 nodes
- Active node highlighted with glow effect
- Moving dot traces the workflow path

### Event Log
- Shows last 5 events
- Timestamp for each event
- Active event highlighted

### Active Step
- Current activity description
- Status name (Fetching, Coding, Pushing, Reviewing, Testing)

### Current Task
- Task title and status
- Elapsed time since task started
- Progress bar animation

## Performance

- Max 100 events retained in memory (configurable)
- Messages truncated to 200 characters
- WebSocket messages sent asynchronously
- Wrapper API calls timeout after 5 seconds

## Security Considerations

1. **Local-Only**: Flask binds to `localhost:5000` by default
2. **CORS**: Enabled for local development (`*`)
3. **No Authentication**: Dashboard has no auth (add to app.py if needed)
4. **Input Validation**: Messages capped at 200 characters
5. **Production**: Use Gunicorn + Nginx with proper CORS/SSL

## Troubleshooting

### Dashboard not updating
1. Check browser console (F12) for WebSocket errors
2. Verify Flask server is running: `curl http://localhost:5000/health`
3. Check that SocketIO client connects: look for "Connected to monitoring server"

### Wrapper not sending updates
1. Check wrapper log: `tail ~/.claude-monitor.log`
2. Verify Flask API is reachable: `curl http://localhost:5000/api/monitor/state`
3. Check JSON is valid: `curl -X POST ... (with proper JSON)`

### Wrong node detection
- Edit pattern matching in `claude-monitor-wrapper.sh`
- Add patterns to regex in `detect_node()` function
- Test with: `echo "your test message" | ./claude-monitor-wrapper.sh`

## Next Steps

### Extend the System

**Add new nodes:**
1. Add to `VALID_NODES` in `monitor_service.py`
2. Add pattern matching to `claude-monitor-wrapper.sh`
3. Add node visualization to `static/monitor.html`

**Integrate with Jira:**
1. Read task from `CURRENT_TASK.md`
2. Call `POST /api/monitor/task` with ticket info
3. Update task status via same endpoint

**Add authentication:**
1. Require token in dashboard
2. Protect WebSocket namespace
3. Use existing `AdminAuthService` from app.py

**Persist data:**
1. Add database models
2. Store events to DB
3. Add historical playback feature

## Testing

### Unit Tests
```bash
pytest tests/test_monitor_service.py -v
```

### Integration Tests
```bash
pytest tests/test_monitor_routes.py -v
```

### Manual Testing
```bash
# Test API
curl http://localhost:5000/api/monitor/state
curl -X POST http://localhost:5000/api/monitor/state \
  -H "Content-Type: application/json" \
  -d '{"node":"claude","state":"active","message":"Test"}'

# Test wrapper
./claude-monitor-wrapper.sh echo "Test message"

# Open dashboard
start static/monitor.html
```

## Deployment

### Docker
```bash
docker build -t agentic-loop .
docker run -p 5000:5000 agentic-loop
```

### Production (Gunicorn)
```bash
gunicorn --worker-class eventlet -w 1 app:app
```

### Cloud Platforms
- Azure App Service: Use `setup_azure.sh`
- Heroku: Add `Procfile` with Gunicorn command
- AWS: Use ECS/Elastic Beanstalk

## References

- [Flask-SocketIO Docs](https://flask-socketio.readthedocs.io/)
- [Socket.IO Client](https://socket.io/docs/v4/client-api/)
- [Flask Blueprint Guide](https://flask.palletsprojects.com/blueprints/)

---

**Created**: February 5, 2026
**Last Updated**: February 5, 2026
