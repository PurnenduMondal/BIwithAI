from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from typing import Dict, Set
import json
import logging
from uuid import UUID

from app.core.security import decode_token
from app.services.websocket.connection_manager import ConnectionManager

router = APIRouter()
logger = logging.getLogger(__name__)

# Connection manager instance
manager = ConnectionManager()

@router.websocket("/ws/realtime")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...)
):
    """WebSocket endpoint for real-time updates"""
    
    # Authenticate user
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        
        if not user_id:
            await websocket.close(code=1008, reason="Invalid token")
            return
    
    except Exception as e:
        logger.error(f"WebSocket authentication failed: {str(e)}")
        await websocket.close(code=1008, reason="Authentication failed")
        return
    
    # Accept connection
    await manager.connect(websocket, user_id)
    
    try:
        # Send welcome message
        await manager.send_personal_message(
            {
                "type": "connection_established",
                "message": "Connected to real-time updates",
                "user_id": user_id
            },
            websocket
        )
        
        # Listen for messages
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            message_type = message.get("type")
            
            if message_type == "subscribe":
                # Subscribe to specific dashboard/resource updates
                resource_type = message.get("resource_type")  # dashboard, widget, datasource
                resource_id = message.get("resource_id")
                
                await manager.subscribe(user_id, resource_type, resource_id)
                
                await manager.send_personal_message(
                    {
                        "type": "subscribed",
                        "resource_type": resource_type,
                        "resource_id": resource_id
                    },
                    websocket
                )
            
            elif message_type == "unsubscribe":
                resource_type = message.get("resource_type")
                resource_id = message.get("resource_id")
                
                await manager.unsubscribe(user_id, resource_type, resource_id)
                
                await manager.send_personal_message(
                    {
                        "type": "unsubscribed",
                        "resource_type": resource_type,
                        "resource_id": resource_id
                    },
                    websocket
                )
            
            elif message_type == "ping":
                await manager.send_personal_message(
                    {"type": "pong", "timestamp": message.get("timestamp")},
                    websocket
                )
            
            else:
                logger.warning(f"Unknown message type: {message_type}")
    
    except WebSocketDisconnect:
        manager.disconnect(user_id)
        logger.info(f"User {user_id} disconnected from WebSocket")
    
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}", exc_info=True)
        manager.disconnect(user_id)
        await websocket.close(code=1011, reason="Internal error")