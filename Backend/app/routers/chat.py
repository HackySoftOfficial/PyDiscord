from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List

router = APIRouter()
connections: List[WebSocket] = []

@router.websocket("/ws/chat/{guild_id}")
async def websocket_endpoint(websocket: WebSocket, guild_id: int):
    await websocket.accept()
    connections.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            for connection in connections:
                if connection != websocket:
                    await connection.send_text(data)
    except WebSocketDisconnect:
        connections.remove(websocket)
