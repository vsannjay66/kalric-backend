from sqlalchemy import (
    Column, Integer, String, Float,
    Boolean, DateTime, ForeignKey,
    Index, func, Text
)
from sqlalchemy.orm import relationship
from database import Base


class UserLocation(Base):
    __tablename__ = "user_locations"

    id            = Column(Integer, primary_key=True, index=True)
    user_id       = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    latitude      = Column(Float, nullable=False)
    longitude     = Column(Float, nullable=False)
    city          = Column(String(100), nullable=True)
    country       = Column(String(100), nullable=True)
    auto_detected = Column(Boolean, default=True)
    updated_at    = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="location")

    __table_args__ = (
        Index("ix_user_locations_user_id", "user_id"),
    )


class UserConnection(Base):
    __tablename__ = "user_connections"

    id          = Column(Integer, primary_key=True, index=True)
    sender_id   = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status      = Column(String(20), default="pending")  # pending/accepted/rejected
    created_at  = Column(DateTime(timezone=True), server_default=func.now())

    sender   = relationship("User", foreign_keys=[sender_id],   back_populates="sent_connections")
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates="received_connections")

    __table_args__ = (
        Index("ix_connections_sender",   "sender_id"),
        Index("ix_connections_receiver", "receiver_id"),
    )


class ChatRoom(Base):
    __tablename__ = "chat_rooms"

    id         = Column(Integer, primary_key=True, index=True)
    user1_id   = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user2_id   = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    messages = relationship("ChatMessage", back_populates="room", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_chat_room_users", "user1_id", "user2_id"),
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id               = Column(Integer, primary_key=True, index=True)
    room_id          = Column(Integer, ForeignKey("chat_rooms.id",  ondelete="CASCADE"), nullable=False)
    sender_id        = Column(Integer, ForeignKey("users.id",       ondelete="CASCADE"), nullable=False)

    # Message content
    message_type     = Column(String(20), default="text")   # text / image / voice
    content          = Column(Text, nullable=True)           # text message
    media_url        = Column(String, nullable=True)         # image/voice file path
    media_size       = Column(Integer, nullable=True)        # file size in bytes
    duration_seconds = Column(Integer, nullable=True)        # voice message duration

    # Status
    is_read          = Column(Boolean, default=False)
    deleted_for_me   = Column(Boolean, default=False)        # delete for sender only
    deleted_for_all  = Column(Boolean, default=False)        # delete for everyone

    created_at       = Column(DateTime(timezone=True), server_default=func.now())

    room   = relationship("ChatRoom", back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id])

    __table_args__ = (
        Index("ix_chat_messages_room_id",  "room_id"),
        Index("ix_chat_messages_sender_id","sender_id"),
    )