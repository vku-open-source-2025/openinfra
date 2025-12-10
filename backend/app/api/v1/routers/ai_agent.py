"""
WebSocket endpoint for AI Agent streaming
"""
import json
import asyncio
import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.infrastructure.database.mongodb import get_database
from app.services.ai_agent import AIAgentService
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI Agent"])


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = None
    asset_context: Optional[Dict[str, Any]] = None


class ConnectionManager:
    """Manage WebSocket connections"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"Client {client_id} connected")
        
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"Client {client_id} disconnected")
            
    async def send_json(self, client_id: str, data: dict):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(data)


manager = ConnectionManager()


@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """
    WebSocket endpoint for streaming AI responses
    
    Message format from client:
    {
        "type": "chat",
        "message": "user message",
        "history": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
    }
    
    Response format:
    - {"type": "token", "content": "..."} - Streaming token
    - {"type": "tool_start", "tool": "...", "input": "..."} - Tool execution started
    - {"type": "tool_end", "output": "..."} - Tool execution finished
    - {"type": "final", "content": "..."} - Final complete response
    - {"type": "error", "content": "..."} - Error message
    - {"type": "done"} - Stream complete
    """
    await manager.connect(websocket, client_id)
    
    try:
        db = await get_database()
        agent = AIAgentService(db)
        
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
                continue
                
            if data.get("type") != "chat":
                await websocket.send_json({
                    "type": "error",
                    "content": "Invalid message type. Expected 'chat'."
                })
                continue
            
            message = data.get("message", "")
            history = data.get("history", [])
            asset_context = data.get("asset_context")
            
            if not message.strip():
                await websocket.send_json({
                    "type": "error",
                    "content": "Empty message"
                })
                continue
            
            # Stream response
            try:
                async for chunk in agent.stream_response(message, history, asset_context):
                    await websocket.send_json(chunk)
            except Exception as e:
                logger.error(f"Error streaming response: {e}")
                await websocket.send_json({
                    "type": "error",
                    "content": f"Error: {str(e)}"
                })
                await websocket.send_json({"type": "done"})
                
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(client_id)


@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Non-streaming chat endpoint for simple requests
    
    Returns complete response in one call.
    For streaming, use WebSocket endpoint.
    """
    db = await get_database()
    agent = AIAgentService(db)
    
    history = None
    if request.history:
        history = [{"role": msg.role, "content": msg.content} for msg in request.history]
    
    try:
        response = await agent.query(request.message, history, request.asset_context)
        return {"response": response}
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def agent_status():
    """Check AI agent status"""
    import os
    api_key = os.getenv("GEMINI_API_KEY")
    
    return {
        "status": "ready" if api_key else "not_configured",
        "model": settings.GEMINI_CHAT_MODEL,
        "model_stable": settings.GEMINI_CHAT_MODEL_STABLE,
        "model_live": settings.GEMINI_CHAT_MODEL_LIVE,
        "use_live": settings.GEMINI_CHAT_MODEL_USE_LIVE,
        "features": [
            "Database querying (assets, sensors, incidents)",
            "API documentation and code examples",
            "Streaming responses via WebSocket",
            "Chat history support"
        ]
    }
