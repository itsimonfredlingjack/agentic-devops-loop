#!/bin/bash
# Simple Jira API wrapper for use in Claude Code
# Usage: jira-api.sh get-issue PROJ-123

set -e

# Load credentials from .env
if [ -f "$(pwd)/.env" ]; then
    source "$(pwd)/.env"
elif [ -f "$HOME/.env" ]; then
    source "$HOME/.env"
else
    echo "❌ .env file not found"
    exit 1
fi

# Validate credentials
if [ -z "$JIRA_URL" ] || [ -z "$JIRA_USERNAME" ] || [ -z "$JIRA_API_TOKEN" ]; then
    echo "❌ Missing Jira credentials in .env"
    exit 1
fi

# Base URL
BASE_URL="${JIRA_URL%/}/rest/api/3"

# Commands
case "$1" in
    get-issue)
        if [ -z "$2" ]; then
            echo "❌ Usage: jira-api.sh get-issue ISSUE_KEY"
            exit 1
        fi
        ISSUE_KEY="$2"
        curl -s -u "$JIRA_USERNAME:$JIRA_API_TOKEN" \
            "$BASE_URL/issues/$ISSUE_KEY" \
            -H "Accept: application/json" | jq '.' 2>/dev/null || echo "{}"
        ;;

    transition-issue)
        if [ -z "$2" ] || [ -z "$3" ]; then
            echo "❌ Usage: jira-api.sh transition-issue ISSUE_KEY STATUS"
            exit 1
        fi
        ISSUE_KEY="$2"
        STATUS="$3"

        # Get available transitions
        TRANSITIONS=$(curl -s -u "$JIRA_USERNAME:$JIRA_API_TOKEN" \
            "$BASE_URL/issues/$ISSUE_KEY/transitions" \
            -H "Accept: application/json")

        # Find transition ID for status
        TRANSITION_ID=$(echo "$TRANSITIONS" | jq -r ".transitions[] | select(.to.name == \"$STATUS\") | .id" 2>/dev/null || echo "")

        if [ -z "$TRANSITION_ID" ]; then
            echo "❌ Status '$STATUS' not found for issue $ISSUE_KEY"
            exit 1
        fi

        # Execute transition
        curl -s -X POST -u "$JIRA_USERNAME:$JIRA_API_TOKEN" \
            "$BASE_URL/issues/$ISSUE_KEY/transitions" \
            -H "Accept: application/json" \
            -H "Content-Type: application/json" \
            -d "{\"transition\": {\"id\": \"$TRANSITION_ID\"}}"
        echo "✅ Transitioned to $STATUS"
        ;;

    add-comment)
        if [ -z "$2" ] || [ -z "$3" ]; then
            echo "❌ Usage: jira-api.sh add-comment ISSUE_KEY 'comment text'"
            exit 1
        fi
        ISSUE_KEY="$2"
        COMMENT="$3"

        curl -s -X POST -u "$JIRA_USERNAME:$JIRA_API_TOKEN" \
            "$BASE_URL/issues/$ISSUE_KEY/comments" \
            -H "Accept: application/json" \
            -H "Content-Type: application/json" \
            -d "{\"body\": {\"version\": 1, \"type\": \"doc\", \"content\": [{\"type\": \"paragraph\", \"content\": [{\"type\": \"text\", \"text\": \"$COMMENT\"}]}]}}"
        echo "✅ Comment added"
        ;;

    *)
        echo "❌ Unknown command: $1"
        echo "Available commands: get-issue, transition-issue, add-comment"
        exit 1
        ;;
esac
