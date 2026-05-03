from sqlalchemy import (
    Column, Integer, String, Float,
    Boolean, DateTime, ForeignKey,
    Index, func, Text
)
from sqlalchemy.orm import relationship
from database import Base


class UserRole(Base):
    __tablename__ = "user_roles"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    role       = Column(String(20), nullable=False, default="client")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="role")

    __table_args__ = (
        Index("ix_user_roles_user_id", "user_id"),
    )


class TrainerProfile(Base):
    __tablename__ = "trainer_profiles"

    id                  = Column(Integer, primary_key=True, index=True)
    user_id             = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)

    # Professional Info
    bio                 = Column(Text, nullable=True)
    experience_years    = Column(Integer, nullable=True)
    specializations     = Column(String(500), nullable=True)
    certifications      = Column(String(500), nullable=True)
    trainer_type        = Column(String(20), default="certified")  # ← add this

    # Verification
    is_verified         = Column(Boolean, default=False)
    certificate_url     = Column(String, nullable=True)
    verification_status = Column(String(20), default="not_submitted")
    rejection_reason    = Column(String(500), nullable=True)
    submitted_at        = Column(DateTime(timezone=True), nullable=True)
    verified_at         = Column(DateTime(timezone=True), nullable=True)

    # Pricing
    is_free             = Column(Boolean, default=False)
    price_per_session   = Column(Float, nullable=True)
    currency            = Column(String(10), default="INR")

    # Availability
    available_times     = Column(String(200), nullable=True)
    max_clients         = Column(Integer, default=10)
    current_clients     = Column(Integer, default=0)

    # Rating
    average_rating      = Column(Float, default=0.0)
    total_reviews       = Column(Integer, default=0)

    created_at          = Column(DateTime(timezone=True), server_default=func.now())
    updated_at          = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user    = relationship("User", back_populates="trainer_profile")
    reviews = relationship("TrainerReview", back_populates="trainer", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_trainer_profiles_user_id", "user_id"),
    )


class TrainerClient(Base):
    __tablename__ = "trainer_clients"

    id         = Column(Integer, primary_key=True, index=True)
    trainer_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    client_id  = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status     = Column(String(20), default="pending")
    is_paid    = Column(Boolean, default=False)
    price      = Column(Float, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    trainer = relationship("User", foreign_keys=[trainer_id], back_populates="my_clients")
    client  = relationship("User", foreign_keys=[client_id],  back_populates="my_trainers")

    __table_args__ = (
        Index("ix_trainer_clients_trainer", "trainer_id"),
        Index("ix_trainer_clients_client",  "client_id"),
    )


class TrainerReview(Base):
    __tablename__ = "trainer_reviews"

    id         = Column(Integer, primary_key=True, index=True)
    trainer_id = Column(Integer, ForeignKey("trainer_profiles.id", ondelete="CASCADE"), nullable=False)
    client_id  = Column(Integer, ForeignKey("users.id",            ondelete="CASCADE"), nullable=False)
    rating     = Column(Integer, nullable=False)
    review     = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    trainer = relationship("TrainerProfile", back_populates="reviews")

    __table_args__ = (
        Index("ix_trainer_reviews_trainer", "trainer_id"),
    )