from typing import Optional, List
from pydantic import BaseModel, field_validator


class MealTiming(BaseModel):
    meal_name: str
    time:      str


class DietPreferenceRequest(BaseModel):
    daily_budget:    float
    weekly_budget:   float
    food_style:      str                        = "indian"
    meals_per_day:   int                        = 5
    allergies:       Optional[str]              = None
    disliked_foods:  Optional[str]              = None
    favourite_foods: Optional[str]              = None
    cooking_time:    str                        = "30min"
    meal_timings:    Optional[List[MealTiming]] = None

    @field_validator("daily_budget")
    @classmethod
    def validate_daily_budget(cls, v):
        if v < 50:
            raise ValueError("Daily budget must be at least ₹50")
        return v

    @field_validator("weekly_budget")
    @classmethod
    def validate_weekly_budget(cls, v):
        if v < 350:
            raise ValueError("Weekly budget must be at least ₹350")
        return v

    @field_validator("meals_per_day")
    @classmethod
    def validate_meals(cls, v):
        if v < 3 or v > 7:
            raise ValueError("Meals per day must be between 3 and 7")
        return v

    @field_validator("food_style")
    @classmethod
    def validate_food_style(cls, v):
        valid = ["indian", "international", "both"]
        if v.lower() not in valid:
            raise ValueError(f"Must be one of: {valid}")
        return v.lower()

    @field_validator("cooking_time")
    @classmethod
    def validate_cooking_time(cls, v):
        valid = ["15min", "30min", "1hr", "flexible"]
        if v.lower() not in valid:
            raise ValueError(f"Must be one of: {valid}")
        return v.lower()


class EditFoodRequest(BaseModel):
    meal_name:    str
    food_name:    str
    reason:       Optional[str] = None
    replace_with: Optional[str] = None

    @field_validator("meal_name")
    @classmethod
    def validate_meal_name(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("meal_name cannot be empty")
        return v.strip()

    @field_validator("food_name")
    @classmethod
    def validate_food_name(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("food_name cannot be empty")
        return v.strip()


class EditMealRequest(BaseModel):
    meal_name:  str
    reason:     Optional[str] = None
    new_timing: Optional[str] = None

    @field_validator("meal_name")
    @classmethod
    def validate_meal_name(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("meal_name cannot be empty")
        return v.strip()