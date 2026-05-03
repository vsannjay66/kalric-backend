from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator
from modules.security import validate_password_strength


class SignUpRequest(BaseModel):
    name:             str
    email:            EmailStr
    password:         str
    confirm_password: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str):
        if not v or len(v.strip()) < 2:
            raise ValueError("Name must be at least 2 characters")
        return v.strip()

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str):
        is_valid, message = validate_password_strength(v)
        if not is_valid:
            raise ValueError(message)
        return v

    @field_validator("confirm_password")
    @classmethod
    def validate_confirm_password(cls, v: str, info):
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Passwords do not match")
        return v


class LoginRequest(BaseModel):
    email:    EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class BodyMetricsRequest(BaseModel):
    age:                 int
    gender:              str
    height:              float
    weight:              float
    body_fat_percentage: Optional[float] = None
    muscle_mass:         Optional[float] = None

    @field_validator("age")
    @classmethod
    def validate_age(cls, v):
        if v < 10 or v > 100:
            raise ValueError("Age must be between 10 and 100")
        return v

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v):
        if v.lower() not in ["male", "female", "other"]:
            raise ValueError("Must be male, female, or other")
        return v.lower()

    @field_validator("height")
    @classmethod
    def validate_height(cls, v):
        if v < 50 or v > 300:
            raise ValueError("Height must be between 50 and 300 cm")
        return v

    @field_validator("weight")
    @classmethod
    def validate_weight(cls, v):
        if v < 20 or v > 500:
            raise ValueError("Weight must be between 20 and 500 kg")
        return v


class FitnessGoalsRequest(BaseModel):
    goal:                   Optional[str]   = None
    target_weight:          Optional[float] = None
    target_days:            Optional[int]   = None
    workout_experience:     Optional[str]   = None
    gym_access:             Optional[bool]  = True
    workout_days_per_week:  Optional[int]   = None
    preferred_workout_time: Optional[str]   = None

    @field_validator("goal")
    @classmethod
    def validate_goal(cls, v):
        if v and v.lower() not in [
            "bulk", "slim", "bodybuilding",
            "fat_loss", "strength"
        ]:
            raise ValueError(
                "Must be bulk, slim, bodybuilding, fat_loss, or strength"
            )
        return v.lower() if v else v

    @field_validator("workout_experience")
    @classmethod
    def validate_experience(cls, v):
        if v and v.lower() not in [
            "beginner", "intermediate", "advanced"
        ]:
            raise ValueError(
                "Must be beginner, intermediate, or advanced"
            )
        return v.lower() if v else v

    @field_validator("preferred_workout_time")
    @classmethod
    def validate_time(cls, v):
        if v and v.lower() not in ["morning", "evening", "night"]:
            raise ValueError("Must be morning, evening, or night")
        return v.lower() if v else v

    @field_validator("workout_days_per_week")
    @classmethod
    def validate_days(cls, v):
        if v is not None and (v < 1 or v > 7):  # ← fixed
            raise ValueError("Must be between 1 and 7")
        return v


class LifestyleRequest(BaseModel):
    food_preference: Optional[str]   = None
    water_intake:    Optional[float] = None
    sleep_hours:     Optional[float] = None
    activity_level:  Optional[str]   = None
    stress_level:    Optional[str]   = None
    smoker:          bool  

    @field_validator("food_preference")
    @classmethod
    def validate_food(cls, v):
        if v and v.lower() not in [
            "veg", "non-veg", "vegan", "eggetarian"  # ← added
        ]:
            raise ValueError("Must be veg, non-veg, vegan, or eggetarian")
        return v.lower() if v else v

    @field_validator("activity_level")
    @classmethod
    def validate_activity(cls, v):
        if v and v.lower() not in [
            "sedentary", "light", "moderate", "active"
        ]:
            raise ValueError(
                "Must be sedentary, light, moderate, or active"
            )
        return v.lower() if v else v

    @field_validator("stress_level")
    @classmethod
    def validate_stress(cls, v):
        if v and v.lower() not in ["low", "medium", "high"]:
            raise ValueError("Must be low, medium, or high")
        return v.lower() if v else v


class HealthRequest(BaseModel):
    health_problems: Optional[str] = None
    injuries:        Optional[str] = None
    medications:     Optional[str] = None


class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp:   str


# ── Forgot Password Schemas ───────────────────────────────────────────────────

class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class VerifyResetOTPRequest(BaseModel):
    email: EmailStr
    otp:   str

    @field_validator("otp")
    @classmethod
    def validate_otp(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("OTP cannot be empty")
        return v.strip()


class ResetPasswordRequest(BaseModel):
    email:        EmailStr
    reset_token:  str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

    @field_validator("reset_token")
    @classmethod
    def validate_reset_token(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("Reset token cannot be empty")
        return v.strip()


class ResendResetOTPRequest(BaseModel):
    email: EmailStr