from typing import Optional
from pydantic import BaseModel, field_validator


class RoleRequest(BaseModel):
    role: str

    @field_validator("role")
    @classmethod
    def validate_role(cls, v):
        if v not in ["client", "trainer"]:
            raise ValueError("Role must be client or trainer")
        return v

class TrainerProfileRequest(BaseModel):
    bio:               Optional[str]   = None
    experience_years:  Optional[int]   = None
    specializations:   Optional[str]   = None
    certifications:    Optional[str]   = None
    trainer_type:      str             = "certified"  # certified / experienced
    is_free:           bool            = False
    price_per_session: Optional[float] = None
    available_times:   Optional[str]   = None
    max_clients:       Optional[int]   = 10

    @field_validator("trainer_type")
    @classmethod
    def validate_trainer_type(cls, v):
        if v not in ["certified", "experienced"]:
            raise ValueError("Must be certified or experienced")
        return v

    @field_validator("experience_years")
    @classmethod
    def validate_experience(cls, v):
        if v and (v < 0 or v > 50):
            raise ValueError("Experience must be between 0 and 50 years")
        return v

    @field_validator("price_per_session")
    @classmethod
    def validate_price(cls, v):
        if v and v < 0:
            raise ValueError("Price cannot be negative")
        return v

    @field_validator("max_clients")
    @classmethod
    def validate_max_clients(cls, v):
        if v and (v < 1 or v > 100):
            raise ValueError("Max clients must be between 1 and 100")
        return v


class ReviewRequest(BaseModel):
    trainer_id: int
    rating:     int
    review:     Optional[str] = None

    @field_validator("rating")
    @classmethod
    def validate_rating(cls, v):
        if v < 1 or v > 5:
            raise ValueError("Rating must be between 1 and 5")
        return v

    @field_validator("review")
    @classmethod
    def validate_review(cls, v):
        if v and len(v) > 500:
            raise ValueError("Review must be under 500 characters")
        return v


class TrainerRequestAction(BaseModel):
    connection_id: int
    action:        str

    @field_validator("action")
    @classmethod
    def validate_action(cls, v):
        v = v.strip().lower() 
        if v not in ["accept", "reject"]:
            raise ValueError("Action must be accept or reject")
        return v