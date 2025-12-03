"""
WebSocket Connection Manager
Manages WebSocket connections and broadcasts logs to connected clients.
"""

from typing import List, Optional
from fastapi import WebSocket
import asyncio
import json
from datetime import datetime
from queue import Queue
import threading


class ConnectionManager:
    """Manages WebSocket connections and broadcasts messages."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.log_queue: Queue = Queue()
        self._log_processor_running = False
        self._log_processor_task: Optional[asyncio.Task] = None
    
    async def connect(self, websocket: WebSocket):
        """Accept and store a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        
        # Start log processor if not running
        if not self._log_processor_running:
            self._log_processor_running = True
            try:
                self._log_processor_task = asyncio.create_task(self._process_log_queue())
            except RuntimeError:
                # If no event loop, will be started when needed
                pass
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        # Stop log processor if no connections
        if not self.active_connections and self._log_processor_running:
            self._log_processor_running = False
            if self._log_processor_task:
                self._log_processor_task.cancel()
    
    def send_log_sync(self, message: str, log_type: str = "info"):
        """
        Queue log message (synchronous - can be called from sync code).
        
        Args:
            message: Log message text
            log_type: Type of log (info, success, error, warning, progress)
        """
        self.log_queue.put({
            "type": "log",
            "log_type": log_type,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
    
    async def send_log(self, message: str, log_type: str = "info"):
        """
        Send log message to all connected clients (async).
        
        Args:
            message: Log message text
            log_type: Type of log (info, success, error, warning, progress)
        """
        data = {
            "type": "log",
            "log_type": log_type,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        
        await self._broadcast(data)
    
    async def _process_log_queue(self):
        """Process queued log messages and send them."""
        while self._log_processor_running:
            try:
                # Get message from queue (with timeout)
                try:
                    message = self.log_queue.get(timeout=0.1)
                    await self._broadcast(message)
                except:
                    await asyncio.sleep(0.1)
                    continue
            except asyncio.CancelledError:
                break
            except Exception:
                continue
    
    async def _broadcast(self, data: dict):
        """Broadcast data to all connected clients."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(data)
            except Exception:
                disconnected.append(connection)
        
        # Remove disconnected clients
        for conn in disconnected:
            self.disconnect(conn)
    
    async def send_result(self, result: dict):
        """
        Send final result to all connected clients.
        
        Args:
            result: Final result dictionary
        """
        data = {
            "type": "result",
            "data": result
        }
        await self._broadcast(data)
    
    async def send_error(self, error_message: str):
        """Send error message to all connected clients."""
        data = {
            "type": "error",
            "message": error_message,
            "timestamp": datetime.now().isoformat()
        }
        await self._broadcast(data)

