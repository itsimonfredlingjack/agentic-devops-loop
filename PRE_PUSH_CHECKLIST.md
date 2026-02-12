# Pre-Push Verification Checklist

## Backend Tests (Automated)

Run these commands to verify backend is working:

```bash
# Test 1: Health Check
curl http://localhost:5000/health
# Expected: {"status": "healthy"}

# Test 2: Get State
curl http://localhost:5000/api/monitor/state | head -5
# Expected: JSON with current_node, event_log, nodes, task_info

# Test 3: Update State
curl -X POST http://localhost:5000/api/monitor/state \
  -H "Content-Type: application/json" \
  -d '{"node":"claude","state":"active","message":"test"}'
# Expected: "success": true

# Test 4: Update Task
curl -X POST http://localhost:5000/api/monitor/task \
  -H "Content-Type: application/json" \
  -d '{"title":"Test","status":"running"}'
# Expected: "success": true

# Test 5: Reset
curl -X POST http://localhost:5000/api/monitor/reset
# Expected: "success": true
```

**Status**:
- [ ] All health checks pass
- [ ] No error messages in Flask logs
- [ ] Ports aren't blocked

## Wrapper Tests (Automated)

```bash
cd grupp-ett-github

# Test each pattern
bash claude-monitor-wrapper.sh echo "Reading spec"
bash claude-monitor-wrapper.sh echo "Writing code.py"
bash claude-monitor-wrapper.sh echo "git commit -m fix"
bash claude-monitor-wrapper.sh echo "Reviewing PR"
bash claude-monitor-wrapper.sh echo "Running pytest"

# Verify each updated the correct node
curl -s http://localhost:5000/api/monitor/state | grep '"current_node"'
```

**Status**:
- [ ] All wrapper commands execute without errors
- [ ] Output passes through transparently
- [ ] State updates detected in API

## Dashboard Tests (Manual)

### Load Dashboard
1. Open: `http://localhost:5000/static/monitor.html`
2. Press F12 (DevTools)
3. Go to **Console** tab

**Checks**:
- [ ] Dashboard loads (no white screen)
- [ ] 5 colored nodes visible
- [ ] Console shows "Connected to monitoring server"
- [ ] No red error messages in console

### Test Real-Time Updates

In separate terminal:
```bash
bash claude-monitor-wrapper.sh echo "Reading task from JIRA"
```

**Watch dashboard**:
- [ ] Purple JIRA node glows
- [ ] Event log adds entry
- [ ] Active step shows "Fetching"
- [ ] No lag or freezing

### Test Full Workflow

```bash
bash claude-monitor-wrapper.sh bash -c "
echo 'Reading issue'
sleep 0.3
echo 'Writing app.py'
sleep 0.3
echo 'git push'
sleep 0.3
echo 'Reviewing'
sleep 0.3
echo 'Testing with pytest'
"
```

**Watch dashboard**:
- [ ] Nodes light up in sequence: Purple → Cyan → Blue → Pink → Green
- [ ] Event log shows all 5 events
- [ ] No animation glitches
- [ ] Console has no errors

### Test Task Info

```bash
curl -X POST http://localhost:5000/api/monitor/task \
  -H "Content-Type: application/json" \
  -d '{"title":"Push to GitHub","status":"running"}'
```

**On dashboard**:
- [ ] Task title updates
- [ ] Status badge shows "RUNNING"
- [ ] Timer starts counting

## File Structure

Verify these files exist:

```bash
grupp-ett-github/
├── app.py                          # Modified with SocketIO
├── claude-monitor-wrapper.sh       # Wrapper script
├── static/
│   ├── monitor.html               # Dashboard
│   ├── center-image.png           # (optional)
│   ├── background.jpg             # (optional)
│   └── Ralph.mp3                  # (optional)
├── src/sejfa/monitor/
│   ├── __init__.py
│   ├── monitor_service.py         # State management
│   └── monitor_routes.py          # API routes
├── MONITORING_SETUP.md            # Setup guide
├── TEST_MONITORING.md             # Detailed tests
├── DASHBOARD_TEST.md              # Dashboard guide
└── PRE_PUSH_CHECKLIST.md         # This file

```

**Verification**:
```bash
cd grupp-ett-github
ls -la src/sejfa/monitor/
ls -la static/
grep -l "SocketIO" app.py
```

**Status**:
- [ ] All monitoring files present
- [ ] app.py imports SocketIO
- [ ] Wrapper script is executable

## Code Quality

```bash
cd grupp-ett-github

# Check for syntax errors
python -m py_compile src/sejfa/monitor/monitor_service.py
python -m py_compile src/sejfa/monitor/monitor_routes.py
python -m py_compile app.py

# Quick import check
python -c "from src.sejfa.monitor.monitor_service import MonitorService; print('OK')"
python -c "from src.sejfa.monitor.monitor_routes import create_monitor_blueprint; print('OK')"
```

**Status**:
- [ ] No Python syntax errors
- [ ] All imports successful
- [ ] No circular dependencies

## Git Status

```bash
cd grupp-ett-github

# Check what's new/modified
git status

# View new files
git status | grep "Untracked files" -A 20

# View modified files
git diff app.py | head -50
```

**Expected changes**:
- [x] New: `src/sejfa/monitor/` (entire directory)
- [x] New: `static/monitor.html`
- [x] New: `claude-monitor-wrapper.sh`
- [x] New: `MONITORING_SETUP.md`
- [x] New: `TEST_MONITORING.md`
- [x] New: `DASHBOARD_TEST.md`
- [x] New: `PRE_PUSH_CHECKLIST.md`
- [x] Modified: `app.py` (SocketIO additions)
- [ ] Optional: `static/center-image.png`, `background.jpg`, `Ralph.mp3`

**Status**:
- [ ] All expected files present
- [ ] No accidental modifications to other files
- [ ] No sensitive data in commits

## Final Safety Checks

```bash
# Make sure no secrets are being committed
grep -r "password\|secret\|token\|key" src/sejfa/monitor/ 2>/dev/null | grep -v "app.secret_key" || echo "No secrets found"

# Check file sizes are reasonable
du -sh src/sejfa/monitor/
du -sh static/monitor.html

# Verify wrapper is executable
ls -la grupp-ett-github/claude-monitor-wrapper.sh
# Should show: -rwxr-xr-x
```

**Status**:
- [ ] No secrets in code
- [ ] File sizes reasonable (< 100KB each)
- [ ] Wrapper script is executable

## Ready to Commit & Push

**Final Checklist**:
- [ ] All backend tests pass
- [ ] All wrapper tests pass
- [ ] Dashboard loads and connects
- [ ] Real-time updates work
- [ ] File structure complete
- [ ] Code quality checks pass
- [ ] No secrets or sensitive data
- [ ] All changes accounted for

---

## Commit Message Template

```bash
git add .

git commit -m "feat: Add real-time monitoring system for Claude Code agentic loop

- Integrate Flask-SocketIO for WebSocket real-time updates
- Create monitoring module with MonitorService for state tracking
- Implement monitoring REST API endpoints
- Add HTML dashboard with live workflow visualization
- Create bash wrapper for transparent Claude output monitoring
- Support pattern detection for 5 workflow nodes (JIRA, CLAUDE, GITHUB, JULES, ACTIONS)
- Add comprehensive testing and setup documentation

The monitoring system provides real-time visibility into the Claude Code
agentic development workflow, showing state transitions between nodes and
maintaining an event log of all activities."
```

---

## Push Commands

```bash
cd grupp-ett-github

# Add all files
git add .

# Commit
git commit -m "feat: Add real-time monitoring system for Claude Code agentic loop"

# Push to origin
git push origin main

# Or create a PR if on a branch
git push -u origin feature/monitoring
gh pr create --title "feat: Add monitoring system" --body "Add real-time monitoring..."
```

---

## Post-Push Verification

After pushing, verify on GitHub:
- [ ] All files show in repo
- [ ] Wrapper script shows as executable (755 permissions)
- [ ] Static files are present
- [ ] app.py shows SocketIO modifications
- [ ] Documentation is readable

---

## Troubleshooting

### If tests fail, check:

1. **Flask not responding**
   ```bash
   lsof -i :5000  # See what's using port 5000
   kill -9 <PID>  # Kill if needed
   python app.py  # Restart
   ```

2. **Wrapper script not working**
   ```bash
   chmod +x claude-monitor-wrapper.sh  # Make executable
   bash claude-monitor-wrapper.sh echo "test"  # Test directly
   ```

3. **Dashboard not loading**
   - Clear browser cache: Ctrl+Shift+Delete
   - Hard refresh: Ctrl+Shift+R
   - Check console: F12 → Console tab
   - Check Flask logs for errors

4. **State not updating**
   ```bash
   curl http://localhost:5000/api/monitor/state
   # Should show recent events
   ```

---

**Last checked**: February 5, 2026
**Status**: Ready for production testing

