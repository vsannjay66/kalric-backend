from fastapi import WebSocket
from typing import Dict, List, Set


class ConnectionManager:
    def __init__(self):
        # room_id → list of websockets
        self.active_connections: Dict[int, List[WebSocket]] = {}
        # user_id → websocket
        self.online_users: Dict[int, WebSocket] = {}
        # room_id → set of typing user_ids
        self.typing_users: Dict[int, Set[int]] = {}

    async def connect(self, websocket: WebSocket, room_id: int, user_id: int):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append(websocket)
        self.online_users[user_id] = websocket

    def disconnect(self, websocket: WebSocket, room_id: int, user_id: int):
        if room_id in self.active_connections:
            if websocket in self.active_connections[room_id]:
                self.active_connections[room_id].remove(websocket)
        if user_id in self.online_users:
            del self.online_users[user_id]
        # Remove from typing
        if room_id in self.typing_users:
            self.typing_users[room_id].discard(user_id)

    async def send_to_room(self, room_id: int, message: dict):
        """Send message to all users in room."""
        if room_id in self.active_connections:
            dead_connections = []
            for connection in self.active_connections[room_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    dead_connections.append(connection)
            # Clean dead connections
            for dead in dead_connections:
                self.active_connections[room_id].remove(dead)

    async def send_to_user(self, user_id: int, message: dict):
        """Send message to specific user."""
        if user_id in self.online_users:
            try:
                await self.online_users[user_id].send_json(message)
            except Exception:
                del self.online_users[user_id]

    def is_online(self, user_id: int) -> bool:
        return user_id in self.online_users

    def set_typing(self, room_id: int, user_id: int, is_typing: bool):
        if room_id not in self.typing_users:
            self.typing_users[room_id] = set()
        if is_typing:
            self.typing_users[room_id].add(user_id)
        else:
            self.typing_users[room_id].discard(user_id)

    def get_typing_users(self, room_id: int) -> list:
        return list(self.typing_users.get(room_id, set()))

    def get_online_count(self, room_id: int) -> int:
        return len(self.active_connections.get(room_id, []))


manager = ConnectionManager()