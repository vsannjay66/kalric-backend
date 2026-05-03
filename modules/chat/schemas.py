from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator


class LocationRequest(BaseModel):
    latitude:      float
    longitude:     float
    city:          Optional[str] = None
    country:       Optional[str] = None
    auto_detected: bool          = True

    @field_validator("latitude")
    @classmethod
    def validate_lat(cls, v):
        if v < -90 or v > 90:
            raise ValueError("Latitude must be between -90 and 90")
        return v

    @field_validator("longitude")
    @classmethod
    def validate_lng(cls, v):
        if v < -180 or v > 180:
            raise ValueError("Longitude must be between -180 and 180")
        return v


class ConnectionRequest(BaseModel):
    receiver_id: int


class ConnectionResponse(BaseModel):
    connection_id: int
    action:        str

    @field_validator("action")
    @classmethod
    def validate_action(cls, v):
        v = v.strip().lower() 
        if v not in ["accept", "reject"]:
            raise ValueError("Action must be accept or reject")
        return v


class TextMessageRequest(BaseModel):
    message: str

    @field_validator("message")
    @classmethod
    def validate_message(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("Message cannot be empty")
        if len(v) > 2000:
            raise ValueError("Message too long — max 2000 characters")
        return v.strip()


class DeleteMessageRequest(BaseModel):
    message_id:  int
    delete_type: str  # "for_me" or "for_all"

    @field_validator("delete_type")
    @classmethod
    def validate_delete_type(cls, v):
        if v not in ["for_me", "for_all"]:
            raise ValueError("Must be for_me or for_all")
        return v