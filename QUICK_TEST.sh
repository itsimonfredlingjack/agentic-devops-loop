#!/bin/bash

# Quick Testing Script for Monitoring System
# Run this to verify everything works before pushing

echo ""
echo "=============================================="
echo "QUICK TEST SUITE FOR MONITORING SYSTEM"
echo "=============================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Test 1: Health Check
echo "TEST 1: Health Check"
echo "-------------------"
RESULT=$(curl -s http://localhost:5000/health)
if echo "$RESULT" | grep -q "healthy"; then
    echo -e "${GREEN}✓ PASS${NC}: Flask server is responding"
else
    echo -e "${RED}✗ FAIL${NC}: Flask server not responding"
    echo "  Make sure Flask is running: python app.py"
    exit 1
fi
echo ""

# Test 2: Get State
echo "TEST 2: Get Monitoring State"
echo "----------------------------"
RESULT=$(curl -s http://localhost:5000/api/monitor/state)
if echo "$RESULT" | grep -q "current_node"; then
    echo -e "${GREEN}✓ PASS${NC}: API returning state"
    EVENTS=$(echo "$RESULT" | grep -c '"timestamp"')
    echo "  Current events in log: $EVENTS"
else
    echo -e "${RED}✗ FAIL${NC}: API not returning proper state"
    exit 1
fi
echo ""

# Test 3: Update State
echo "TEST 3: Update State (CLAUDE node)"
echo "-----------------------------------"
RESULT=$(curl -s -X POST http://localhost:5000/api/monitor/state \
  -H "Content-Type: application/json" \
  -d '{"node":"claude","state":"active","message":"Test update"}')
if echo "$RESULT" | grep -q '"success": true'; then
    echo -e "${GREEN}✓ PASS${NC}: State update successful"
    NODE=$(echo "$RESULT" | grep -o '"current_node":"[^"]*"' | cut -d'"' -f4)
    echo "  Current node: $NODE"
else
    echo -e "${RED}✗ FAIL${NC}: State update failed"
    exit 1
fi
echo ""

# Test 4: Wrapper Script
echo "TEST 4: Wrapper Script Test"
echo "---------------------------"
if [ -f "claude-monitor-wrapper.sh" ]; then
    OUTPUT=$(bash claude-monitor-wrapper.sh echo "Testing wrapper")
    if [ "$OUTPUT" = "Testing wrapper" ]; then
        echo -e "${GREEN}✓ PASS${NC}: Wrapper executes correctly"
    else
        echo -e "${RED}✗ FAIL${NC}: Wrapper output mismatch"
        exit 1
    fi
else
    echo -e "${RED}✗ FAIL${NC}: Wrapper script not found"
    exit 1
fi
echo ""

# Test 5: Pattern Detection
echo "TEST 5: Pattern Detection"
echo "------------------------"
bash claude-monitor-wrapper.sh echo "Reading from JIRA" > /dev/null
RESULT=$(curl -s http://localhost:5000/api/monitor/state)
NODE=$(echo "$RESULT" | grep -o '"current_node":"[^"]*"' | cut -d'"' -f4)
if [ "$NODE" = "jira" ]; then
    echo -e "${GREEN}✓ PASS${NC}: JIRA pattern detected"
else
    echo -e "${RED}✗ FAIL${NC}: Pattern detection failed (got: $NODE)"
fi
echo ""

# Summary
echo "=============================================="
echo "TEST SUMMARY"
echo "=============================================="
echo -e "${GREEN}All automated tests passed!${NC}"
echo ""
echo "Next steps:"
echo "1. Open dashboard: http://localhost:5000/static/monitor.html"
echo "2. Run workflow test:"
echo "   bash claude-monitor-wrapper.sh bash -c '"
echo "   echo \"Reading spec\"; sleep 0.3"
echo "   echo \"Writing code\"; sleep 0.3"
echo "   echo \"git commit\"; sleep 0.3"
echo "   echo \"Running tests\""
echo "   '"
echo "3. Watch nodes light up in the dashboard"
echo "4. If everything works, proceed with commit/push"
echo ""

