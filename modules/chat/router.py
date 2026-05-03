import os
import shutil
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import (
    APIRouter, Depends, HTTPException,
    Request, WebSocket, WebSocketDisconnect,
    UploadFile, File
)
from sqlalchemy.orm import Session
from sqlalchemy import or_

from database import get_db
from models import User, UserFitnessGoals
from modules.chat.models import (
    UserLocation, UserConnection,
    ChatRoom, ChatMessage
)
from modules.chat.schemas import (
    LocationRequest, ConnectionRequest,
    ConnectionResponse, TextMessageRequest,
    DeleteMessageRequest
)
from modules.chat.matching import get_matches
from modules.chat.websocket_manager import manager
from auth import verify_access_token

router = APIRouter()

MEDIA_DIR = "uploads/chat_media"


# ── Auth Helper ───────────────────────────────────────────────────────────────

def get_chat_user(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
    if not token:
        raise HTTPException(401, "Not authenticated")
    payload = verify_access_token(token)
    if not payload:
        raise HTTPException(401, "Invalid token")
    user = db.query(User).filter(User.id == payload["user_id"]).first()
    if not user:
        raise HTTPException(404, "User not found")
    return user


def verify_room_access(room_id: int, user_id: int, db: Session) -> ChatRoom:
    """Check user belongs to chat room."""
    room = db.query(ChatRoom).filter(
        ChatRoom.id == room_id,
        or_(
            ChatRoom.user1_id == user_id,
            ChatRoom.user2_id == user_id
        )
    ).first()
    if not room:
        raise HTTPException(404, "Chat room not found")
    return room


def save_media_file(file: UploadFile, user_id: int, media_type: str) -> tuple[str, int]:
    """Save image or voice file. Returns (filepath, size)."""
    Path(MEDIA_DIR).mkdir(parents=True, exist_ok=True)

    allowed = {
        "image": ["jpg", "jpeg", "png", "gif", "webp"],
        "voice": ["mp3", "wav", "ogg", "m4a", "webm"]
    }

    ext = file.filename.split(".")[-1].lower() if file.filename else ""
    if ext not in allowed.get(media_type, []):
        raise ValueError(f"Invalid {media_type} format")

    unique_id = secrets.token_hex(8)
    timestamp = int(datetime.now(timezone.utc).timestamp())
    filename  = f"{media_type}_{user_id}_{timestamp}_{unique_id}.{ext}"
    filepath  = f"{MEDIA_DIR}/{filename}"

    with open(filepath, "wb") as f:
        shutil.copyfileobj(file.file, f)

    size = os.path.getsize(filepath)
    return filepath, size


# ── Location Routes ───────────────────────────────────────────────────────────

@router.post("/location")
def update_location(
    request: Request,
    payload: LocationRequest,
    db: Session = Depends(get_db)
):
    user     = get_chat_user(request, db)
    location = db.query(UserLocation).filter(
        UserLocation.user_id == user.id
    ).first()

    if location:
        location.latitude      = payload.latitude
        location.longitude     = payload.longitude
        location.city          = payload.city
        location.country       = payload.country
        location.auto_detected = payload.auto_detected
    else:
        db.add(UserLocation(
            user_id       = user.id,
            latitude      = payload.latitude,
            longitude     = payload.longitude,
            city          = payload.city,
            country       = payload.country,
            auto_detected = payload.auto_detected
        ))
    db.commit()
    return {
        "message":       "Location updated ✅",
        "city":          payload.city,
        "auto_detected": payload.auto_detected
    }


@router.get("/location")
def get_location(request: Request, db: Session = Depends(get_db)):
    user     = get_chat_user(request, db)
    location = db.query(UserLocation).filter(
        UserLocation.user_id == user.id
    ).first()
    if not location:
        raise HTTPException(404, "Location not set. Please enable location access.")
    return {
        "latitude":      location.latitude,
        "longitude":     location.longitude,
        "city":          location.city,
        "country":       location.country,
        "auto_detected": location.auto_detected,
        "updated_at":    location.updated_at
    }


# ── Match Routes ──────────────────────────────────────────────────────────────

@router.get("/match")
def find_matches(
    request:   Request,
    radius_km: float = 50.0,
    national:  bool  = True,
    db: Session      = Depends(get_db)
):
    """Find users with same goal — local first then national."""
    user = get_chat_user(request, db)

    my_goals = db.query(UserFitnessGoals).filter(
        UserFitnessGoals.user_id == user.id
    ).first()

    if not my_goals or not my_goals.goal:
        raise HTTPException(400, "Please set your fitness goal first")

    matches = get_matches(db, user, radius_km, national)

    return {
        "my_goal":        my_goals.goal,
        "radius_km":      radius_km,
        "local_count":    len(matches["local"]),
        "national_count": len(matches["national"]),
        "local":          matches["local"],
        "national":       matches["national"]
    }


# ── Connection Routes ─────────────────────────────────────────────────────────

@router.post("/connections/request")
def send_connection_request(
    request: Request,
    payload: ConnectionRequest,
    db: Session = Depends(get_db)
):
    user = get_chat_user(request, db)

    if payload.receiver_id == user.id:
        raise HTTPException(400, "Cannot connect with yourself")

    receiver = db.query(User).filter(User.id == payload.receiver_id).first()
    if not receiver:
        raise HTTPException(404, "User not found")

    existing = db.query(UserConnection).filter(
        or_(
            (UserConnection.sender_id   == user.id) &
            (UserConnection.receiver_id == payload.receiver_id),
            (UserConnection.sender_id   == payload.receiver_id) &
            (UserConnection.receiver_id == user.id)
        )
    ).first()

    if existing:
        raise HTTPException(400, f"Connection already {existing.status}")

    conn = UserConnection(
        sender_id   = user.id,
        receiver_id = payload.receiver_id,
        status      = "pending"
    )
    db.add(conn)
    db.commit()
    db.refresh(conn)

    return {
        "message":       "Connection request sent ✅",
        "connection_id": conn.id
    }


@router.put("/connections/respond")
def respond_connection(
    request: Request,
    payload: ConnectionResponse,
    db: Session = Depends(get_db)
):
    user = get_chat_user(request, db)

    conn = db.query(UserConnection).filter(
        UserConnection.id          == payload.connection_id,
        UserConnection.receiver_id == user.id,
        UserConnection.status      == "pending"
    ).first()

    if not conn:
        raise HTTPException(404, "Connection request not found")

    if payload.action == "accept":
        conn.status = "accepted"
        db.commit()

        # Create chat room
        room = ChatRoom(user1_id=conn.sender_id, user2_id=conn.receiver_id)
        db.add(room)
        db.commit()
        db.refresh(room)

        return {
            "message": "Connection accepted ✅",
            "room_id": room.id
        }
    else:
        conn.status = "rejected"
        db.commit()
        return {"message": "Connection rejected"}


@router.get("/connections")
def get_connections(request: Request, db: Session = Depends(get_db)):
    user = get_chat_user(request, db)

    connections = db.query(UserConnection).filter(
        or_(
            UserConnection.sender_id   == user.id,
            UserConnection.receiver_id == user.id
        ),
        UserConnection.status == "accepted"
    ).all()

    result = []
    for conn in connections:
        other_id   = conn.receiver_id if conn.sender_id == user.id else conn.sender_id
        other_user = db.query(User).filter(User.id == other_id).first()

        room = db.query(ChatRoom).filter(
            or_(
                (ChatRoom.user1_id == user.id)    & (ChatRoom.user2_id == other_id),
                (ChatRoom.user1_id == other_id)   & (ChatRoom.user2_id == user.id)
            )
        ).first()

        # Get last message
        last_msg = None
        unread   = 0
        if room:
            last_message = db.query(ChatMessage).filter(
                ChatMessage.room_id        == room.id,
                ChatMessage.deleted_for_all == False
            ).order_by(ChatMessage.created_at.desc()).first()

            if last_message:
                last_msg = {
                    "content":      last_message.content if last_message.message_type == "text" else f"[{last_message.message_type}]",
                    "message_type": last_message.message_type,
                    "created_at":   last_message.created_at
                }

            unread = db.query(ChatMessage).filter(
                ChatMessage.room_id        == room.id,
                ChatMessage.sender_id      != user.id,
                ChatMessage.is_read        == False,
                ChatMessage.deleted_for_all == False
            ).count()

        result.append({
            "connection_id": conn.id,
            "user_id":       other_user.id,
            "name":          other_user.name,
            "room_id":       room.id if room else None,
            "is_online":     manager.is_online(other_id),
            "unread_count":  unread,
            "last_message":  last_msg
        })

    # Sort by last message time
    result.sort(
        key=lambda x: x["last_message"]["created_at"] if x["last_message"] else datetime.min.replace(tzinfo=timezone.utc),
        reverse=True
    )

    return {"connections": result}


@router.get("/connections/pending")
def get_pending_requests(request: Request, db: Session = Depends(get_db)):
    user = get_chat_user(request, db)

    pending = db.query(UserConnection).filter(
        UserConnection.receiver_id == user.id,
        UserConnection.status      == "pending"
    ).all()

    result = []
    for conn in pending:
        sender = db.query(User).filter(User.id == conn.sender_id).first()

        sender_goals = db.query(UserFitnessGoals).filter(
            UserFitnessGoals.user_id == conn.sender_id
        ).first()

        result.append({
            "connection_id": conn.id,
            "sender_id":     sender.id,
            "name":          sender.name,
            "goal":          sender_goals.goal if sender_goals else None,
            "sent_at":       conn.created_at
        })

    return {"pending_requests": result, "count": len(result)}


# ── Message Routes ────────────────────────────────────────────────────────────

@router.get("/messages/{room_id}")
def get_messages(
    request:  Request,
    room_id:  int,
    page:     int = 1,
    per_page: int = 50,
    db: Session   = Depends(get_db)
):
    user = get_chat_user(request, db)
    room = verify_room_access(room_id, user.id, db)

    offset   = (page - 1) * per_page
    messages = db.query(ChatMessage).filter(
        ChatMessage.room_id         == room_id,
        ChatMessage.deleted_for_all == False
    ).order_by(
        ChatMessage.created_at.desc()
    ).offset(offset).limit(per_page).all()

    # Mark as read
    for msg in messages:
        if msg.sender_id != user.id and not msg.is_read:
            msg.is_read = True
    db.commit()

    return {
        "room_id":  room_id,
        "page":     page,
        "per_page": per_page,
        "messages": [
            {
                "id":               m.id,
                "sender_id":        m.sender_id,
                "message_type":     m.message_type,
                "content":          None if m.deleted_for_me and m.sender_id == user.id else m.content,
                "media_url":        None if m.deleted_for_me and m.sender_id == user.id else m.media_url,
                "duration_seconds": m.duration_seconds,
                "is_read":          m.is_read,
                "created_at":       m.created_at
            }
            for m in reversed(messages)
        ]
    }


@router.post("/messages/{room_id}/text")
def send_text_message(
    request:  Request,
    room_id:  int,
    payload:  TextMessageRequest,
    db: Session = Depends(get_db)
):
    user = get_chat_user(request, db)
    room = verify_room_access(room_id, user.id, db)

    message = ChatMessage(
        room_id      = room_id,
        sender_id    = user.id,
        message_type = "text",
        content      = payload.message
    )
    db.add(message)
    db.commit()
    db.refresh(message)

    return {
        "message_id":  message.id,
        "message_type": "text",
        "content":     message.content,
        "created_at":  message.created_at
    }


@router.post("/messages/{room_id}/image")
async def send_image_message(
    request: Request,
    room_id: int,
    file:    UploadFile = File(...),
    db: Session         = Depends(get_db)
):
    user = get_chat_user(request, db)
    room = verify_room_access(room_id, user.id, db)

    # Check file size max 10MB
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(400, "Image too large. Max 10MB")
    await file.seek(0)

    try:
        filepath, size = save_media_file(file, user.id, "image")
    except ValueError as e:
        raise HTTPException(400, str(e))

    message = ChatMessage(
        room_id      = room_id,
        sender_id    = user.id,
        message_type = "image",
        media_url    = filepath,
        media_size   = size
    )
    db.add(message)
    db.commit()
    db.refresh(message)

    return {
        "message_id":   message.id,
        "message_type": "image",
        "media_url":    filepath,
        "media_size":   size,
        "created_at":   message.created_at
    }


@router.post("/messages/{room_id}/voice")
async def send_voice_message(
    request:          Request,
    room_id:          int,
    file:             UploadFile = File(...),
    duration_seconds: int        = 0,
    db: Session                  = Depends(get_db)
):
    user = get_chat_user(request, db)
    room = verify_room_access(room_id, user.id, db)

    # Check file size max 5MB
    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(400, "Voice message too large. Max 5MB")
    await file.seek(0)

    try:
        filepath, size = save_media_file(file, user.id, "voice")
    except ValueError as e:
        raise HTTPException(400, str(e))

    message = ChatMessage(
        room_id          = room_id,
        sender_id        = user.id,
        message_type     = "voice",
        media_url        = filepath,
        media_size       = size,
        duration_seconds = duration_seconds
    )
    db.add(message)
    db.commit()
    db.refresh(message)

    return {
        "message_id":       message.id,
        "message_type":     "voice",
        "media_url":        filepath,
        "duration_seconds": duration_seconds,
        "created_at":       message.created_at
    }


@router.delete("/messages/{message_id}")
def delete_message(
    request:  Request,
    message_id: int,
    payload:  DeleteMessageRequest,
    db: Session = Depends(get_db)
):
    user = get_chat_user(request, db)

    message = db.query(ChatMessage).filter(
        ChatMessage.id == message_id
    ).first()

    if not message:
        raise HTTPException(404, "Message not found")

    if payload.delete_type == "for_me":
        # Only sender can delete for me
        if message.sender_id != user.id:
            raise HTTPException(403, "Can only delete your own messages for yourself")
        message.deleted_for_me = True
        db.commit()
        return {"message": "Message deleted for you ✅"}

    elif payload.delete_type == "for_all":
        # Only sender can delete for all
        if message.sender_id != user.id:
            raise HTTPException(403, "Can only delete your own messages")
        message.deleted_for_all = True
        message.content         = None
        message.media_url       = None
        db.commit()
        return {"message": "Message deleted for everyone ✅"}


# ── WebSocket — Real Time Chat ─────────────────────────────────────────────────

@router.websocket("/ws/{room_id}/{user_id}")
async def websocket_chat(
    websocket: WebSocket,
    room_id:   int,
    user_id:   int,
    db: Session = Depends(get_db)
):
    # Verify room access
    room = db.query(ChatRoom).filter(
        ChatRoom.id == room_id,
        or_(
            ChatRoom.user1_id == user_id,
            ChatRoom.user2_id == user_id
        )
    ).first()

    if not room:
        await websocket.close(code=4004)
        return

    await manager.connect(websocket, room_id, user_id)

    # Notify online
    await manager.send_to_room(room_id, {
        "type":    "status",
        "user_id": user_id,
        "status":  "online"
    })

    try:
        while True:
            data = await websocket.receive_json()
            event_type = data.get("type")

            # ── Text Message ──────────────────────────────────────────────
            if event_type == "text":
                content = data.get("message", "").strip()
                if not content:
                    continue

                message = ChatMessage(
                    room_id      = room_id,
                    sender_id    = user_id,
                    message_type = "text",
                    content      = content
                )
                db.add(message)
                db.commit()
                db.refresh(message)

                # Stop typing
                manager.set_typing(room_id, user_id, False)

                await manager.send_to_room(room_id, {
                    "type":         "message",
                    "message_id":   message.id,
                    "sender_id":    user_id,
                    "message_type": "text",
                    "content":      content,
                    "created_at":   str(message.created_at)
                })

            # ── Typing Indicator ──────────────────────────────────────────
            elif event_type == "typing":
                is_typing = data.get("is_typing", False)
                manager.set_typing(room_id, user_id, is_typing)

                await manager.send_to_room(room_id, {
                    "type":      "typing",
                    "user_id":   user_id,
                    "is_typing": is_typing
                })

            # ── Read Receipt ──────────────────────────────────────────────
            elif event_type == "read":
                message_id = data.get("message_id")
                if message_id:
                    msg = db.query(ChatMessage).filter(
                        ChatMessage.id        == message_id,
                        ChatMessage.sender_id != user_id
                    ).first()
                    if msg:
                        msg.is_read = True
                        db.commit()

                        await manager.send_to_room(room_id, {
                            "type":       "read",
                            "message_id": message_id,
                            "read_by":    user_id
                        })

            # ── Delete Message ────────────────────────────────────────────
            elif event_type == "delete":
                message_id  = data.get("message_id")
                delete_type = data.get("delete_type", "for_me")

                if message_id:
                    msg = db.query(ChatMessage).filter(
                        ChatMessage.id        == message_id,
                        ChatMessage.sender_id == user_id
                    ).first()

                    if msg:
                        if delete_type == "for_all":
                            msg.deleted_for_all = True
                            msg.content         = None
                            msg.media_url       = None
                            db.commit()

                            await manager.send_to_room(room_id, {
                                "type":       "deleted",
                                "message_id": message_id,
                                "delete_type": "for_all"
                            })
                        else:
                            msg.deleted_for_me = True
                            db.commit()

    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id, user_id)

        # Notify offline
        await manager.send_to_room(room_id, {
            "type":    "status",
            "user_id": user_id,
            "status":  "offline"
        })