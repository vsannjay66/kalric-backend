from typing import Dict, List, Optional
from pydantic import BaseModel, field_validator


# ── Valid Values ──────────────────────────────────────────────────────────────

VALID_DAYS = [
    "monday", "tuesday", "wednesday",
    "thursday", "friday", "saturday", "sunday"
]

VALID_MUSCLES = [
    "chest", "back", "shoulders",
    "biceps", "triceps",
    "quads", "hamstrings", "glutes", "calves",
    "abs", "obliques",
    "cardio", "full_body"
]


# ── Day Plan ──────────────────────────────────────────────────────────────────

class DayPlan(BaseModel):
    is_rest: bool       = False
    muscles: List[str]  = []

    @field_validator("muscles")
    @classmethod
    def validate_muscles(cls, v):
        for muscle in v:
            if muscle.lower() not in VALID_MUSCLES:
                raise ValueError(f"Invalid muscle: {muscle}. Valid: {VALID_MUSCLES}")
        return [m.lower() for m in v]


# ── Weekly Split Request ──────────────────────────────────────────────────────

class WeeklySplitRequest(BaseModel):
    mode:         str                  = "ai"
    weekly_split: Dict[str, DayPlan]

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, v):
        if v not in ["ai", "manual"]:
            raise ValueError("Mode must be ai or manual")
        return v

    @field_validator("weekly_split")
    @classmethod
    def validate_split(cls, v):
        # Check valid days
        for day in v:
            if day.lower() not in VALID_DAYS:
                raise ValueError(f"Invalid day: {day}")

        # At least 1 workout day
        workout_days = [
            d for d, data in v.items()
            if not data.is_rest
        ]
        if len(workout_days) == 0:
            raise ValueError("Select at least 1 workout day")

        # Workout days must have muscles
        for day, data in v.items():
            if not data.is_rest and len(data.muscles) == 0:
                raise ValueError(
                    f"{day} is a workout day but has no muscles selected"
                )

        return v


# ── Exercise Detail ───────────────────────────────────────────────────────────

class ExerciseDetail(BaseModel):
    name:   str
    sets:   int            = 3
    reps:   str            = "10-12"
    weight: Optional[str]  = None
    rest:   Optional[str]  = "60 sec"

    @field_validator("sets")
    @classmethod
    def validate_sets(cls, v):
        if v < 1 or v > 10:
            raise ValueError("Sets must be between 1 and 10")
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("Exercise name cannot be empty")
        return v.strip()


# ── Manual Exercises Request ──────────────────────────────────────────────────

class ManualExercisesRequest(BaseModel):
    exercises: Dict[str, Dict[str, List[ExerciseDetail]]]
    # Structure:
    # {
    #   "monday": {
    #     "chest": [
    #       {"name": "Bench Press", "sets": 4, "reps": "8-10", "weight": "60kg"}
    #     ],
    #     "triceps": [
    #       {"name": "Tricep Pushdown", "sets": 3, "reps": "12"}
    #     ]
    #   }
    # }

    @field_validator("exercises")
    @classmethod
    def validate_exercises(cls, v):
        for day, muscles in v.items():
            if day.lower() not in VALID_DAYS:
                raise ValueError(f"Invalid day: {day}")
            for muscle, exercises in muscles.items():
                if muscle.lower() not in VALID_MUSCLES:
                    raise ValueError(f"Invalid muscle: {muscle}")
                if len(exercises) == 0:
                    raise ValueError(f"{day} {muscle} has no exercises")
        return v


# ── Edit Exercise Request ─────────────────────────────────────────────────────

class EditExerciseRequest(BaseModel):
    day:          str
    old_exercise: str
    new_exercise: Optional[str]  = None
    sets:         Optional[int]  = None
    reps:         Optional[str]  = None
    weight:       Optional[str]  = None
    rest:         Optional[str]  = None

    @field_validator("day")
    @classmethod
    def validate_day(cls, v):
        if v.lower() not in VALID_DAYS:
            raise ValueError(f"Invalid day: {v}")
        return v.lower()

    @field_validator("old_exercise")
    @classmethod
    def validate_old_exercise(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("old_exercise cannot be empty")
        return v.strip()