# Dashboard Testing Guide

## Current Test Status

All backend API tests have **PASSED**:
- ✅ Health check: Responsive
- ✅ State endpoints: GET/POST working
- ✅ Pattern detection: All 5 nodes correctly identified
- ✅ Event logging: Messages stored with timestamps
- ✅ Task tracking: Title and status updating
- ✅ Wrapper script: Transparent pass-through working

## Dashboard Visual Testing

### Step 1: Open the Dashboard

1. **Start Flask Server** (if not running):
   ```bash
   cd grupp-ett-github
   source venv/Scripts/activate
   python app.py
   ```

2. **Open in Browser**:
   - Navigate to: `http://localhost:5000/static/monitor.html`
   - Open Developer Tools: Press `F12`
   - Go to **Console** tab

### Step 2: Verify Initial Load

**What you should see**:
- 5 circular nodes arranged in a circle (purple, cyan, blue, pink, green)
- Center yellow circle with text "Place your image..."
- Sidebar on right showing:
  - "Event Log" section with "Waiting for events..."
  - "Active Step" section showing "Idle"
  - "Current Task" section showing "Waiting for task..."
- **Console messages**: "Connected to monitoring server"

**If not seeing this**:
- Check console for errors (red text)
- Verify Flask is running: `curl http://localhost:5000/health`
- Check WebSocket connection: Look for "Connected" message

### Step 3: Real-Time Update Test

**In a separate terminal**, run:
```bash
cd grupp-ett-github
bash claude-monitor-wrapper.sh echo "Reading JIRA ticket"
```

**Watch the dashboard**:
- The purple **JIRA** node should:
  - Grow slightly (scale up)
  - Glow with purple light
  - Show "JIRA" label in black text
- The event log should:
  - Add "Reading JIRA ticket" entry
  - Show timestamp
  - Highlight in yellow
- Active step should show:
  - Status: "Fetching"
  - Description: "Retrieving ticket from JIRA..."

### Step 4: Sequential Node Test

Run this to cycle through all nodes:

```bash
cd grupp-ett-github
bash claude-monitor-wrapper.sh bash -c "
echo 'Reading ticket from JIRA'
sleep 0.5
echo 'Writing solution to app.py'
sleep 0.5
echo 'git commit -m feature'
sleep 0.5
echo 'Reviewing code quality'
sleep 0.5
echo 'Running pytest tests'
"
```

**Watch the dashboard**:

1. **JIRA node (purple)** activates
   - Event log shows "Reading ticket from JIRA"
   - Active step: "Fetching"

2. **CLAUDE node (cyan)** activates (after ~0.5s)
   - Event log adds new entry
   - Active step: "Coding"

3. **GITHUB node (blue)** activates
   - Active step: "Pushing"

4. **JULES node (pink)** activates
   - Active step: "Reviewing"

5. **ACTIONS node (green)** activates
   - Active step: "Testing"

**Advanced**: Watch the moving dot trace between nodes

### Step 5: Task Info Test

```bash
curl -X POST http://localhost:5000/api/monitor/task \
  -H "Content-Type: application/json" \
  -d '{"title":"Implement Dashboard","status":"running"}'
```

**On dashboard, you should see**:
- Current Task section updates with:
  - Title: "Implement Dashboard"
  - Status badge: "RUNNING"
  - Timer starting and counting up

### Step 6: Multi-Tab Test

1. Open dashboard in **Tab 1**
2. Open same URL in **Tab 2**
3. In terminal, run:
   ```bash
   bash claude-monitor-wrapper.sh echo "Writing test.py"
   ```

**Expected**: Both tabs update simultaneously with same state

### Step 7: Responsive Test

Resize browser window:
- On desktop: Dashboard should adapt
- On mobile: Should stack vertically
- All 5 nodes should remain visible

### Step 8: Audio/Image Test

1. Look for center image (should show placeholder if no image)
2. Click on center circle
3. Listen for Ralph sound (optional)

---

## Detailed Component Verification

### Event Log
- [ ] Shows last 5 events
- [ ] Newest event has yellow background
- [ ] Oldest event has white background
- [ ] Timestamps are accurate
- [ ] Scrollable if more than 5 items

### Active Step
- [ ] Status updates: Idle → Fetching → Coding → Pushing → Reviewing → Testing
- [ ] Description changes for each step
- [ ] Yellow background maintains
- [ ] Text is readable

### Current Task
- [ ] Title updates when calling /api/monitor/task
- [ ] Status badge shows correct status (IDLE, RUNNING, COMPLETED)
- [ ] Timer counts up when running (seconds increment every 1s)
- [ ] Progress bar animates continuously

### Nodes
- [ ] Purple (JIRA) activates with reading patterns
- [ ] Cyan (CLAUDE) activates with writing patterns
- [ ] Blue (GITHUB) activates with git patterns
- [ ] Pink (JULES) activates with review patterns
- [ ] Green (ACTIONS) activates with test patterns
- [ ] Only ONE node active at a time
- [ ] Glow effect appears on active node
- [ ] Node returns to normal size when inactive

---

## Performance Checks

### Rapid Updates
```bash
for i in {1..10}; do
  curl -s -X POST http://localhost:5000/api/monitor/state \
    -H "Content-Type: application/json" \
    -d "{\"node\":\"claude\",\"state\":\"active\",\"message\":\"Update $i\"}" > /dev/null
  sleep 0.1
done
```

**Expected**: Dashboard smoothly handles 10 updates in quick succession

### Check Console for Errors
- No red error messages
- No "WebSocket connection closed" messages
- Only "Received state update" messages

---

## Browser Compatibility

Test on:
- [ ] Chrome/Edge (Windows)
- [ ] Firefox (Windows)
- [ ] Safari (if available)

**Expected in all browsers**:
- Smooth animations
- No rendering issues
- WebSocket connects successfully

---

## Network Testing

### Test with API Down
1. Stop Flask server: `Ctrl+C` in Flask terminal
2. Run wrapper: `bash claude-monitor-wrapper.sh echo "test"`
3. Start Flask again: `python app.py`

**Expected**:
- Wrapper completes normally (doesn't error)
- Dashboard reconnects automatically
- Previous state isn't lost (if you refresh browser)

### Test with Slow Network (optional)
Use browser DevTools to throttle connection:
1. F12 → Network tab
2. Select "Slow 3G" or "Offline"
3. Try updating state
4. Set back to "No throttling"

**Expected**: Dashboard eventually catches up

---

## Success Checklist

- [ ] Dashboard loads on first visit
- [ ] WebSocket connects (see "Connected to monitoring server")
- [ ] Each pattern triggers correct node color
- [ ] Event log populates with real messages
- [ ] Active step description matches node activity
- [ ] Task title and status update correctly
- [ ] Timer counts up accurately
- [ ] All 5 nodes glow when active
- [ ] No JavaScript errors in console
- [ ] Smooth animations between node transitions
- [ ] Multiple tabs stay in sync
- [ ] Dashboard remains responsive with rapid updates

---

## If Something Doesn't Work

### Dashboard Won't Load
```bash
# Check Flask is running
curl http://localhost:5000/static/monitor.html

# Check for JavaScript errors
# F12 → Console, look for red errors
```

### WebSocket Won't Connect
```bash
# Check in console (F12):
# Should see: "Connected to monitoring server"
# If not, check Flask logs for SocketIO errors

# Restart Flask:
# Kill the python process and restart
```

### Events Not Showing
```bash
# Test API directly:
curl http://localhost:5000/api/monitor/state

# If empty, send test event:
curl -X POST http://localhost:5000/api/monitor/state \
  -H "Content-Type: application/json" \
  -d '{"node":"claude","state":"active","message":"test"}'
```

### Wrong Nodes Activating
- Check pattern matching in `claude-monitor-wrapper.sh`
- Test your message against regex:
  ```bash
  echo "Your test message" | bash claude-monitor-wrapper.sh
  ```

---

## Ready to Push?

Once you've verified:
1. ✅ All API endpoints responding
2. ✅ Dashboard loads and connects
3. ✅ Real-time updates visible
4. ✅ All 5 nodes working correctly
5. ✅ No console errors
6. ✅ Wrapper script working

**Then you're ready to commit and push!**

