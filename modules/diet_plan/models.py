from sqlalchemy import (
    Column, Integer, String, Float,
    DateTime, ForeignKey, JSON, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class DietPreference(Base):
    __tablename__ = "diet_preferences"

    id              = Column(Integer,     primary_key=True, index=True)
    user_id         = Column(Integer,     ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    daily_budget    = Column(Float,       nullable=False)
    weekly_budget   = Column(Float,       nullable=False)
    food_style      = Column(String(50),  default="indian")
    meals_per_day   = Column(Integer,     default=5)
    allergies       = Column(String(500), nullable=True)
    disliked_foods  = Column(String(500), nullable=True)
    favourite_foods = Column(String(500), nullable=True)
    cooking_time    = Column(String(20),  default="30min")
    meal_timings    = Column(JSON,        nullable=True)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())
    updated_at      = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="diet_preference")

    __table_args__ = (
        Index("ix_diet_preferences_user_id", "user_id"),
    )


class DietPlan(Base):
    __tablename__ = "diet_plans"

    id           = Column(Integer,    primary_key=True, index=True)
    user_id      = Column(Integer,    ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    goal         = Column(String(50), nullable=True)
    calories     = Column(Integer,    nullable=True)
    protein_g    = Column(Float,      nullable=True)
    carbs_g      = Column(Float,      nullable=True)
    fat_g        = Column(Float,      nullable=True)
    diet_level   = Column(String(20), default="basic")
    daily_budget = Column(Float,      nullable=True)
    plan_data    = Column(JSON,       nullable=False)
    generated_by = Column(String(20), nullable=True)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())
    updated_at   = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="diet_plan")

    __table_args__ = (
        Index("ix_diet_plans_user_id", "user_id"),
    )