# Monitoring System Test Plan

## Pre-Test Checklist

- [ ] Flask server running on localhost:5000
- [ ] Dashboard accessible at http://localhost:5000/static/monitor.html
- [ ] Browser developer console open (F12)
- [ ] Monitor log file cleared: `> ~/.claude-monitor.log`

---

## Test 1: Backend API Verification

### 1.1 Health Check
```bash
curl http://localhost:5000/health
```
**Expected**: `{"status": "healthy"}`

### 1.2 Get Initial State
```bash
curl http://localhost:5000/api/monitor/state
```
**Expected**: JSON with empty event_log, all nodes inactive, current_node: null

### 1.3 Update Node State
```bash
curl -X POST http://localhost:5000/api/monitor/state \
  -H "Content-Type: application/json" \
  -d '{"node":"jira","state":"active","message":"Test JIRA node"}'
```
**Expected**: success: true, current_node should be "jira"

### 1.4 Update Task Info
```bash
curl -X POST http://localhost:5000/api/monitor/task \
  -H "Content-Type: application/json" \
  -d '{"title":"Test Task","status":"running"}'
```
**Expected**: success: true, task_info updated with title and status

---

## Test 2: Pattern Matching in Wrapper

Test each node pattern with echo:

### 2.1 Test JIRA Node (Reading pattern)
```bash
./claude-monitor-wrapper.sh echo "Reading JIRA ticket PROJ-123"
```
**Expected in terminal**: "Reading JIRA ticket PROJ-123"
**Check curl**: Node should be "jira" in state

### 2.2 Test CLAUDE Node (Writing pattern)
```bash
./claude-monitor-wrapper.sh echo "Writing to src/app.py"
```
**Expected**: state shows claude node active

### 2.3 Test GITHUB Node (Git pattern)
```bash
./claude-monitor-wrapper.sh echo "git commit -m 'Add feature'"
```
**Expected**: state shows github node active

### 2.4 Test JULES Node (Review pattern)
```bash
./claude-monitor-wrapper.sh echo "Reviewing code quality"
```
**Expected**: state shows jules node active

### 2.5 Test ACTIONS Node (Test pattern)
```bash
./claude-monitor-wrapper.sh echo "Running pytest tests/test_app.py"
```
**Expected**: state shows actions node active

---

## Test 3: Multi-Line Workflow Simulation

Simulate a complete workflow cycle:

```bash
./claude-monitor-wrapper.sh bash -c "
echo 'Reading issue from JIRA'
sleep 1
echo 'Writing implementation to main.py'
sleep 1
echo 'git commit -m \"Fix issue\"'
sleep 1
echo 'Reviewing code for quality'
sleep 1
echo 'Running pytest to verify'
"
```

**Expected in curl**:
- Event log should have 5 entries
- Nodes should show last_active timestamps for jira, claude, github, jules, actions

---

## Test 4: Dashboard Real-Time Updates

### 4.1 Open Dashboard
1. Open browser to: `http://localhost:5000/static/monitor.html`
2. Open DevTools (F12) → Console tab

### 4.2 Check WebSocket Connection
**In browser console, you should see**:
```
Connected to monitoring server
```

### 4.3 Verify Initial State Loads
- Dashboard should show all 5 nodes (purple, cyan, blue, pink, green)
- Event log section should show "Waiting for events..."
- Active step should show "Idle"
- Task info should show "Waiting for task..."

### 4.4 Test Real-Time Updates

In terminal, run:
```bash
./claude-monitor-wrapper.sh echo "Reading requirements.txt"
```

**In browser, you should see**:
- JIRA node (purple) highlights with glow
- Event log adds new entry
- Active step shows "Fetching"
- In console: "Received state update: {current_node: 'jira', ...}"

### 4.5 Test Node Transitions

Run this multi-step simulation:
```bash
./claude-monitor-wrapper.sh bash -c "
echo 'Reading specification'
sleep 0.5
echo 'Writing code to handler.py'
sleep 0.5
echo 'git commit -m done'
sleep 0.5
echo 'Running npm test'
"
```

**Expected in dashboard**:
- Watch nodes light up in sequence
- Moving dot traces path between nodes
- Event log shows all 4 events
- Last event is highlighted

---

## Test 5: Wrapper Logging

Check the wrapper logs:
```bash
cat ~/.claude-monitor.log
```

**Expected format**:
```
[2026-02-05 14:00:00] Claude Monitor Wrapper started with args: ...
[2026-02-05 14:00:00] Sent: node=jira, message=Reading ...
[2026-02-05 14:00:01] Claude Monitor Wrapper completed
```

---

## Test 6: Error Handling

### 6.1 Invalid Node
```bash
curl -X POST http://localhost:5000/api/monitor/state \
  -H "Content-Type: application/json" \
  -d '{"node":"invalid","state":"active"}'
```
**Expected**: error message about invalid node

### 6.2 Missing Required Fields
```bash
curl -X POST http://localhost:5000/api/monitor/state \
  -H "Content-Type: application/json" \
  -d '{"state":"active"}'
```
**Expected**: error message about missing node

### 6.3 Wrapper with API Down
Kill Flask server, then:
```bash
./claude-monitor-wrapper.sh echo "Testing with API down"
```
**Expected**: Message prints normally, no errors shown (silent failure)

---

## Test 7: Performance & Cleanup

### 7.1 Reset State
```bash
curl -X POST http://localhost:5000/api/monitor/reset
```
**Expected**: State returned to initial, event_log empty

### 7.2 Test Event Log Size Limit
Run 50+ state updates in a loop:
```bash
for i in {1..60}; do
  curl -s -X POST http://localhost:5000/api/monitor/state \
    -H "Content-Type: application/json" \
    -d "{\"node\":\"claude\",\"state\":\"active\",\"message\":\"Event $i\"}" > /dev/null
done
```

Check state:
```bash
curl -s http://localhost:5000/api/monitor/state | grep -c '"timestamp"'
```
**Expected**: Should be ≤ 100 (max event limit)

---

## Test 8: Concurrent Connections

### 8.1 Open Dashboard in Multiple Tabs
1. Open `http://localhost:5000/static/monitor.html` in Tab 1
2. Open same URL in Tab 2
3. Open same URL in Tab 3

### 8.2 Update State from Terminal
```bash
./claude-monitor-wrapper.sh echo "Concurrent test"
```

**Expected**:
- All 3 tabs update simultaneously
- All show same state
- Browser console shows "Received state update" in all tabs

---

## Test 9: Message Length & Truncation

Test that long messages are truncated to 200 chars:
```bash
long_msg=$(python -c "print('x' * 500)")
curl -X POST http://localhost:5000/api/monitor/state \
  -H "Content-Type: application/json" \
  -d "{\"node\":\"claude\",\"state\":\"active\",\"message\":\"$long_msg\"}"
```

Check result:
```bash
curl -s http://localhost:5000/api/monitor/state | grep -o '"message":"[^"]*"' | head -1
```
**Expected**: Message should be max 200 characters

---

## Test 10: Integration with Real Claude Code

### 10.1 Create Test Task
```bash
cat > test_task.sh << 'EOF'
#!/bin/bash
echo "Reading: Looking at the codebase structure"
sleep 1
echo "Writing: Creating new function in app.py"
sleep 1
echo "git commit -m 'Add test function'"
sleep 1
echo "Reviewing: Check test coverage"
sleep 1
echo "Running pytest on new tests"
EOF
chmod +x test_task.sh
```

### 10.2 Run with Wrapper
```bash
./claude-monitor-wrapper.sh ./test_task.sh
```

### 10.3 Verify in Dashboard
- All nodes should light up in sequence
- Event log shows all messages
- Task completion visible

---

## Quick Test Commands

### One-Command Full Test
```bash
# Terminal 1: Start server
cd grupp-ett-github
source venv/Scripts/activate
python app.py

# Terminal 2: Run tests
curl http://localhost:5000/health
./claude-monitor-wrapper.sh echo "Test 1"
./claude-monitor-wrapper.sh echo "Writing to file.py"
./claude-monitor-wrapper.sh echo "git commit"
curl http://localhost:5000/api/monitor/state | grep -c event
curl -X POST http://localhost:5000/api/monitor/reset
```

### Dashboard Check
```bash
# Open in browser
start static/monitor.html

# Run this in another terminal
./claude-monitor-wrapper.sh echo "Check dashboard for JIRA activation"
```

---

## Troubleshooting During Tests

### Dashboard not connecting
```bash
# Check browser console (F12)
# Look for WebSocket connection error
# Verify Flask running: curl http://localhost:5000/health
```

### Wrapper not updating state
```bash
# Check wrapper log
tail -f ~/.claude-monitor.log

# Verify API endpoint manually
curl http://localhost:5000/api/monitor/state
```

### Wrong nodes activating
```bash
# Check pattern in wrapper
grep "detect_node" claude-monitor-wrapper.sh
echo "Your test message" | ./claude-monitor-wrapper.sh
```

---

## Success Criteria

- [ ] All API endpoints respond correctly
- [ ] Pattern matching identifies all 5 nodes
- [ ] Dashboard connects via WebSocket
- [ ] Real-time updates visible in dashboard
- [ ] Event log populates and limits to 100 items
- [ ] No errors in browser console
- [ ] Wrapper handles API failures gracefully
- [ ] Multiple concurrent connections work
- [ ] Message truncation at 200 chars works
- [ ] Performance acceptable with 60+ updates

---

## Notes

- Each test should complete in < 2 seconds unless otherwise noted
- Wrapper should not produce any output besides the command's output
- Dashboard should remain responsive during rapid updates
- No Python errors should appear in Flask logs

