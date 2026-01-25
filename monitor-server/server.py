#!/usr/bin/env python3
"""
Agent Monitor Server - Real-time task monitoring via WebSocket
"""

import json
import asyncio
from datetime import datetime
from typing import Set
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(title="Agent Monitor")

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory state
state = {
    "status": "idle",
    "task": None,
    "events": [],
}

# WebSocket connections
connected_clients: Set[WebSocket] = set()


class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass


manager = ConnectionManager()


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok"}


@app.get("/api/state")
async def get_state():
    """Get current monitor state"""
    return state


@app.post("/api/task")
async def post_task(data: dict):
    """Update task state"""
    state["task"] = data
    await manager.broadcast({"type": "task_update", "data": data})
    return {"status": "ok"}


@app.post("/api/event")
async def post_event(data: dict):
    """Add event to log"""
    event = {
        "timestamp": data.get("timestamp", datetime.utcnow().isoformat() + "Z"),
        "event_type": data.get("event_type", "info"),
        "message": data.get("message", ""),
        "source": data.get("source", "unknown"),
    }
    state["events"].append(event)

    # Keep only last 100 events
    if len(state["events"]) > 100:
        state["events"] = state["events"][-100:]

    await manager.broadcast({"type": "event", "data": event})
    return {"status": "ok"}


@app.post("/api/reset")
async def reset_state():
    """Reset monitor state"""
    global state
    state = {
        "status": "idle",
        "task": None,
        "events": [],
    }
    await manager.broadcast({"type": "reset"})
    return {"status": "ok"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)
    try:
        # Send initial state
        await websocket.send_json({
            "type": "init",
            "data": state,
        })

        # Keep connection alive, handle incoming messages
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        manager.disconnect(websocket)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
