from sqlalchemy import (
    Column, Integer, String, Float, Boolean,
    DateTime, ForeignKey, Index, func, Text, JSON
)
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    __tablename__ = "users"

    id                     = Column(Integer, primary_key=True, index=True)
    name                   = Column(String(100), nullable=False)
    email                  = Column(String(150), unique=True, nullable=False, index=True)
    password_hash          = Column(String, nullable=False)
    preferred_language     = Column(String(20), default="English")
    profile_photo_url      = Column(String, nullable=True)

    # Email Verification
    is_verified            = Column(Boolean, default=False, nullable=False)
    verification_token     = Column(String, nullable=True)
    verification_expires   = Column(DateTime(timezone=True), nullable=True)

    # 2FA
    two_fa_enabled         = Column(Boolean, default=False, nullable=False)
    two_fa_otp             = Column(String, nullable=True)
    two_fa_otp_expires     = Column(DateTime(timezone=True), nullable=True)

    # Brute Force Protection
    failed_login_attempts  = Column(Integer, nullable=False, default=0)
    lock_until             = Column(DateTime(timezone=True), nullable=True)
    last_failed_ip         = Column(String, nullable=True)

    # Password Security
    password_changed_at    = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at             = Column(DateTime(timezone=True), server_default=func.now())
    last_login_at          = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    body_metrics       = relationship("UserBodyMetrics",  back_populates="user", uselist=False, cascade="all, delete-orphan")
    fitness_goals      = relationship("UserFitnessGoals", back_populates="user", uselist=False, cascade="all, delete-orphan")
    lifestyle          = relationship("UserLifestyle",    back_populates="user", uselist=False, cascade="all, delete-orphan")
    health             = relationship("UserHealth",       back_populates="user", uselist=False, cascade="all, delete-orphan")
    refresh_tokens     = relationship("RefreshToken",     back_populates="user", cascade="all, delete-orphan")
    devices            = relationship("UserDevice",       back_populates="user", cascade="all, delete-orphan")
    blacklisted_tokens = relationship("BlacklistedToken", back_populates="user", cascade="all, delete-orphan")
    login_history      = relationship("LoginHistory",     back_populates="user", cascade="all, delete-orphan")
    workout_plans      = relationship("WorkoutPlan",      back_populates="user", cascade="all, delete-orphan")  # ✅ added
    role             = relationship("UserRole",        back_populates="user", uselist=False, cascade="all, delete-orphan")
    trainer_profile  = relationship("TrainerProfile",  back_populates="user", uselist=False, cascade="all, delete-orphan")
    my_clients       = relationship("TrainerClient",   foreign_keys="TrainerClient.trainer_id", back_populates="trainer", cascade="all, delete-orphan")
    my_trainers      = relationship("TrainerClient",   foreign_keys="TrainerClient.client_id",  back_populates="client",  cascade="all, delete-orphan")
    
    location             = relationship("UserLocation",     back_populates="user", uselist=False, cascade="all, delete-orphan")
    sent_connections     = relationship("UserConnection",   foreign_keys="UserConnection.sender_id",   back_populates="sender",   cascade="all, delete-orphan")
    received_connections = relationship("UserConnection",   foreign_keys="UserConnection.receiver_id", back_populates="receiver", cascade="all, delete-orphan")
     
     
    diet_preference = relationship( "DietPreference",back_populates = "user",uselist= False,cascade= "all, delete-orphan")
    diet_plan = relationship("DietPlan",back_populates = "user",uselist= False,cascade= "all, delete-orphan") 
   
    __table_args__ = (
        Index("ix_users_email_id", "email", "id"),
    )


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token      = Column(String, unique=True, nullable=False, index=True)
    is_revoked = Column(Boolean, default=False, nullable=False)
    device_id  = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)

    user = relationship("User", back_populates="refresh_tokens")

    __table_args__ = (
        Index("ix_refresh_token_user_id", "user_id"),
        Index("ix_refresh_token_token",   "token"),
    )


class BlacklistedToken(Base):
    __tablename__ = "blacklisted_tokens"

    id             = Column(Integer, primary_key=True, index=True)
    user_id        = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token          = Column(Text, unique=True, nullable=False, index=True)
    blacklisted_at = Column(DateTime(timezone=True), server_default=func.now())
    reason         = Column(String(100), nullable=True)

    user = relationship("User", back_populates="blacklisted_tokens")

    __table_args__ = (
        Index("ix_blacklisted_token", "token"),
    )


class UserDevice(Base):
    __tablename__ = "user_devices"

    id           = Column(Integer, primary_key=True, index=True)
    user_id      = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    device_id    = Column(String, nullable=False)
    device_name  = Column(String(200), nullable=True)
    browser      = Column(String(100), nullable=True)
    os           = Column(String(100), nullable=True)
    ip_address   = Column(String(50), nullable=True)
    is_trusted   = Column(Boolean, default=False)
    last_used_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at   = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="devices")

    __table_args__ = (
        Index("ix_user_device_user_id", "user_id"),
    )


class LoginHistory(Base):
    __tablename__ = "login_history"

    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    ip_address  = Column(String(50), nullable=True)
    device_name = Column(String(200), nullable=True)
    browser     = Column(String(100), nullable=True)
    os          = Column(String(100), nullable=True)
    status      = Column(String(20), nullable=False)
    reason      = Column(String(200), nullable=True)
    logged_at   = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="login_history")

    __table_args__ = (
        Index("ix_login_history_user_id", "user_id"),
    )


class UserBodyMetrics(Base):
    __tablename__ = "user_body_metrics"

    id                  = Column(Integer, primary_key=True, index=True)
    user_id             = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    age                 = Column(Integer, nullable=True)
    gender              = Column(String(20), nullable=True)
    height              = Column(Float, nullable=True)
    weight              = Column(Float, nullable=True)
    bmi                 = Column(Float, nullable=True)
    body_fat_percentage = Column(Float, nullable=True)
    muscle_mass         = Column(Float, nullable=True)
    updated_at          = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="body_metrics")

    __table_args__ = (
        Index("ix_body_metrics_user_id", "user_id"),
    )


class UserFitnessGoals(Base):
    __tablename__ = "user_fitness_goals"

    id                     = Column(Integer, primary_key=True, index=True)
    user_id                = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    goal                   = Column(String(50), nullable=True)
    target_weight          = Column(Float, nullable=True)
    target_days            = Column(Integer, nullable=True)
    workout_experience     = Column(String(50), nullable=True)
    gym_access             = Column(Boolean, default=True)
    workout_days_per_week  = Column(Integer, nullable=True)
    preferred_workout_time = Column(String(20), nullable=True)
    updated_at             = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="fitness_goals")

    __table_args__ = (
        Index("ix_fitness_goals_user_id", "user_id"),
    )


class UserLifestyle(Base):
    __tablename__ = "user_lifestyle"

    id              = Column(Integer, primary_key=True, index=True)
    user_id         = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    food_preference = Column(String(50), nullable=True)
    water_intake    = Column(Float, nullable=True)
    sleep_hours     = Column(Float, nullable=True)
    activity_level  = Column(String(50), nullable=True)
    stress_level    = Column(String(20), nullable=True)
    smoker          = Column(Boolean, nullable=False, default=False)  # ← REPLACE
    updated_at      = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="lifestyle")

    __table_args__ = (
        Index("ix_lifestyle_user_id", "user_id"),
    )


class UserHealth(Base):
    __tablename__ = "user_health"

    id              = Column(Integer, primary_key=True, index=True)
    user_id         = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    health_problems = Column(String(255), nullable=True)
    injuries        = Column(String(255), nullable=True)
    medications     = Column(String(255), nullable=True)
    updated_at      = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="health")

    __table_args__ = (
        Index("ix_health_user_id", "user_id"),
    )


class WorkoutPlan(Base):
    __tablename__ = "workout_plans"

    id            = Column(Integer, primary_key=True, index=True)
    user_id       = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    goal          = Column(String(50), nullable=True)
    level         = Column(String(50), nullable=True)
    days_per_week = Column(Integer, nullable=True)
    week_number   = Column(Integer, default=1)
    plan_data     = Column(JSON, nullable=False)
    generated_by  = Column(String(20), nullable=True)
    
    
    mode           = Column(String(20),  default="ai")
    weekly_split   = Column(JSON,        nullable=True)
    user_exercises = Column(JSON,        nullable=True)

    created_at    = Column(DateTime(timezone=True), server_default=func.now())
    updated_at    = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="workout_plans")

    ############___CHAT____########################
