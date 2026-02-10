from fastapi import WebSocket
from typing import Dict, Set, List
import json
import logging
import asyncio

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manages WebSocket connections and subscriptions"""
    
    def __init__(self):
        # user_id -> WebSocket
        self.active_connections: Dict[str, WebSocket] = {}
        
        # user_id -> Set of subscribed resources
        # Format: "resource_type:resource_id"
        self.subscriptions: Dict[str, Set[str]] = {}
        
        # resource -> Set of user_ids
        self.resource_subscribers: Dict[str, Set[str]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        self.subscriptions[user_id] = set()
        
        logger.info(f"User {user_id} connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, user_id: str):
        """Remove WebSocket connection"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        
        # Clean up subscriptions
        if user_id in self.subscriptions:
            for resource in self.subscriptions[user_id]:
                if resource in self.resource_subscribers:
                    self.resource_subscribers[resource].discard(user_id)
                    if not self.resource_subscribers[resource]:
                        del self.resource_subscribers[resource]
            
            del self.subscriptions[user_id]
        
        logger.info(f"User {user_id} disconnected. Total connections: {len(self.active_connections)}")
    
    async def subscribe(self, user_id: str, resource_type: str, resource_id: str):
        """Subscribe user to resource updates"""
        resource_key = f"{resource_type}:{resource_id}"
        
        if user_id in self.subscriptions:
            self.subscriptions[user_id].add(resource_key)
        else:
            self.subscriptions[user_id] = {resource_key}
        
        if resource_key in self.resource_subscribers:
            self.resource_subscribers[resource_key].add(user_id)
        else:
            self.resource_subscribers[resource_key] = {user_id}
        
        logger.info(f"User {user_id} subscribed to {resource_key}")
        logger.info(f"Total resource_subscribers: {self.resource_subscribers}")
    
    async def unsubscribe(self, user_id: str, resource_type: str, resource_id: str):
        """Unsubscribe user from resource updates"""
        resource_key = f"{resource_type}:{resource_id}"
        
        if user_id in self.subscriptions:
            self.subscriptions[user_id].discard(resource_key)
        
        if resource_key in self.resource_subscribers:
            self.resource_subscribers[resource_key].discard(user_id)
            if not self.resource_subscribers[resource_key]:
                del self.resource_subscribers[resource_key]
        
        logger.info(f"User {user_id} unsubscribed from {resource_key}")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send message to specific connection"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {str(e)}")
    
    async def broadcast_to_resource(self, resource_type: str, resource_id: str, message: dict):
        """Broadcast message to all subscribers of a resource"""
        resource_key = f"{resource_type}:{resource_id}"
        
        logger.info(f"Broadcasting to {resource_key}")
        logger.info(f"Subscribed resources: {list(self.resource_subscribers.keys())}")
        logger.info(f"Active connections: {list(self.active_connections.keys())}")
        
        if resource_key not in self.resource_subscribers:
            logger.warning(f"No subscribers for {resource_key}")
            return
        
        subscribers = self.resource_subscribers[resource_key].copy()
        logger.info(f"Found {len(subscribers)} subscribers for {resource_key}: {subscribers}")
        
        # Send to all subscribers
        disconnected = []
        for user_id in subscribers:
            if user_id in self.active_connections:
                try:
                    await self.active_connections[user_id].send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to {user_id}: {str(e)}")
                    disconnected.append(user_id)
            else:
                disconnected.append(user_id)
        
        # Clean up disconnected users
        for user_id in disconnected:
            self.disconnect(user_id)
        
        logger.info(f"Broadcast to {len(subscribers) - len(disconnected)} subscribers of {resource_key}")
    
    async def broadcast_to_all(self, message: dict):
        """Broadcast message to all connected users"""
        disconnected = []
        
        for user_id, websocket in self.active_connections.items():
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to {user_id}: {str(e)}")
                disconnected.append(user_id)
        
        # Clean up disconnected users
        for user_id in disconnected:
            self.disconnect(user_id)
        
        logger.info(f"Broadcast to {len(self.active_connections) - len(disconnected)} connections")

# Global instance
connection_manager = ConnectionManager()