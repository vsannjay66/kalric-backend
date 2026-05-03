from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from database import get_db
from models import User, UserFitnessGoals, UserBodyMetrics, WorkoutPlan
from auth import verify_access_token

from modules.custom_workout.schemas import (
    WeeklySplitRequest,
    ManualExercisesRequest,
    EditExerciseRequest
)
from modules.custom_workout.exercise_library import (
    get_all_muscles,
    get_exercises_for_muscle,
    get_exercises_for_goal,
    get_total_exercises,
    EXERCISE_LIBRARY
)
from modules.custom_workout.prompt_builder import (
    build_custom_ai_prompt,
    build_custom_manual_prompt
)
from modules.custom_workout.fallback import get_fallback_plan

router = APIRouter()


# ── Auth Helper ───────────────────────────────────────────────────────────────

def get_custom_user(request: Request, db: Session = Depends(get_db)):
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


# ── Get All Muscles ───────────────────────────────────────────────────────────

@router.get("/muscles")
def get_muscles(
    request: Request,
    db: Session = Depends(get_db)
):
    """Get all muscle groups for selection."""
    _ = get_custom_user(request, db)
    muscles = get_all_muscles()
    return {
        "muscles":         muscles,
        "total_muscles":   sum(len(v) for v in muscles.values()),
        "total_exercises": get_total_exercises()
    }


# ── Get Exercises for Muscle ──────────────────────────────────────────────────

@router.get("/exercises/{muscle}")
def get_exercises(
    muscle:  str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Get all exercises for a specific muscle."""
    user = get_custom_user(request, db)

    # Get user goal
    g    = db.query(UserFitnessGoals).filter(
        UserFitnessGoals.user_id == user.id
    ).first()
    goal = g.goal if g else "strength"

    # Get exercises sorted by goal
    exercises = get_exercises_for_goal(goal, muscle)

    if not exercises:
        raise HTTPException(
            404,
            f"No exercises found for muscle: {muscle}"
        )

    return {
        "muscle":    muscle,
        "goal":      goal,
        "total":     len(exercises),
        "exercises": exercises
    }


# ── Get Full Exercise Library ─────────────────────────────────────────────────

@router.get("/library")
def get_library(
    request: Request,
    db: Session = Depends(get_db)
):
    """Get complete exercise library."""
    _ = get_custom_user(request, db)
    return {
        "library":         EXERCISE_LIBRARY,
        "total_muscles":   len(EXERCISE_LIBRARY),
        "total_exercises": get_total_exercises()
    }


# ── Step 1 — Save Weekly Split ────────────────────────────────────────────────

@router.post("/split")
def save_weekly_split(
    request: Request,
    payload: WeeklySplitRequest,
    db: Session = Depends(get_db)
):
    """
    Step 1 — Save weekly split.
    Which muscles to train each day.
    """
    user = get_custom_user(request, db)

    # Convert to JSON
    split_data = {
        day: {
            "is_rest": data.is_rest,
            "muscles": data.muscles
        }
        for day, data in payload.weekly_split.items()
    }

    workout_days = [
        day for day, data in split_data.items()
        if not data["is_rest"]
    ]

    # Save to DB
    existing = db.query(WorkoutPlan).filter(
        WorkoutPlan.user_id == user.id
    ).first()

    if existing:
        existing.mode          = payload.mode
        existing.weekly_split  = split_data
        existing.days_per_week = len(workout_days)
        existing.user_exercises = None  # reset exercises
        existing.plan_data     = {}
        existing.generated_by  = "pending"
        flag_modified(existing, "weekly_split")
        db.commit()
        db.refresh(existing)
    else:
        new = WorkoutPlan(
            user_id        = user.id,
            mode           = payload.mode,
            weekly_split   = split_data,
            days_per_week  = len(workout_days),
            plan_data      = {},
            generated_by   = "pending"
        )
        db.add(new)
        db.commit()
        db.refresh(new)

    return {
        "message":      "Weekly split saved ✅",
        "mode":         payload.mode,
        "workout_days": workout_days,
        "total_days":   len(workout_days),
        "split":        split_data,
        "next_step": (
            "POST /custom-workout/generate"
            if payload.mode == "ai"
            else "POST /custom-workout/exercises"
        )
    }


# ── Step 2 (Manual Only) — Save Exercises ────────────────────────────────────

@router.post("/exercises")
def save_manual_exercises(
    request: Request,
    payload: ManualExercisesRequest,
    db: Session = Depends(get_db)
):
    """
    Step 2 for manual mode only.
    Save user selected exercises with sets/reps/weight.
    """
    user = get_custom_user(request, db)

    plan = db.query(WorkoutPlan).filter(
        WorkoutPlan.user_id == user.id
    ).first()

    if not plan:
        raise HTTPException(
            400,
            "Please save weekly split first → POST /custom-workout/split"
        )

    if plan.mode != "manual":
        raise HTTPException(
            400,
            "This endpoint is for manual mode only"
        )

    # Convert to JSON
    exercises_data = {
        day: {
            muscle: [ex.dict() for ex in exercises]
            for muscle, exercises in muscles.items()
        }
        for day, muscles in payload.exercises.items()
    }

    plan.user_exercises = exercises_data
    flag_modified(plan, "user_exercises")
    db.commit()

    return {
        "message":   "Exercises saved ✅",
        "next_step": "POST /custom-workout/generate"
    }


# ── Step 3 — Generate Plan ────────────────────────────────────────────────────

@router.post("/generate")
def generate_custom_plan(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Final step — generate complete plan.
    AI mode   → AI picks exercises + fills all details
    Manual mode → AI fills missing details only
    """
    user = get_custom_user(request, db)

    plan = db.query(WorkoutPlan).filter(
        WorkoutPlan.user_id == user.id
    ).first()

    if not plan or not plan.weekly_split:
        raise HTTPException(
            400,
            "Please save weekly split first → POST /custom-workout/split"
        )

    if plan.mode == "manual" and not plan.user_exercises:
        raise HTTPException(
            400,
            "Please save exercises first → POST /custom-workout/exercises"
        )

    # Get user profile
    m = db.query(UserBodyMetrics).filter(
        UserBodyMetrics.user_id == user.id
    ).first()
    g = db.query(UserFitnessGoals).filter(
        UserFitnessGoals.user_id == user.id
    ).first()

    goal   = g.goal              if g else "strength"
    level  = g.workout_experience if g else "beginner"
    weight = m.weight            if m else 70.0

    # Build prompt based on mode
    if plan.mode == "ai":
        prompt = build_custom_ai_prompt(
            weekly_split = plan.weekly_split,
            goal         = goal,
            level        = level,
            weight       = weight
        )
    else:
        prompt = build_custom_manual_prompt(
            weekly_split   = plan.weekly_split,
            user_exercises = plan.user_exercises,
            goal           = goal,
            level          = level,
            weight         = weight
        )

    # Call AI
    try:
        # from modules.workout_generator.llm_client import call_llm_with_fallback
        # from modules.workout_generator.validator  import validate_workout_response
        from modules.workout_generator.llm_client        import call_llm_with_fallback
        from modules.custom_workout.validator             import validate_custom_workout_response

        print(f"Generating custom plan — mode: {plan.mode}")
        raw_response, provider = call_llm_with_fallback(prompt)
        workout_plan           = validate_custom_workout_response(raw_response)
        workout_plan["generated_by"] = provider
        workout_plan["mode"]         = plan.mode
        print(f"Response from: {provider}")
        # Fix empty or missing days
        all_days = [
            "monday","tuesday","wednesday",
            "thursday","friday","saturday","sunday"
        ]
        for day in all_days:
            if day not in workout_plan.get("weekly_plan", {}):
                workout_plan["weekly_plan"][day] = {
                    "muscle_group":             "Rest",
                    "session_duration_minutes": 0,
                    "session_calories_burned":  0,
                    "difficulty":               "none",
                    "warm_up":                  [],
                    "exercises":                [],
                    "cool_down":                []
                }
            elif workout_plan["weekly_plan"][day] == {}:
                workout_plan["weekly_plan"][day] = {
                    "muscle_group":             "Rest",
                    "session_duration_minutes": 0,
                    "session_calories_burned":  0,
                    "difficulty":               "none",
                    "warm_up":                  [],
                    "exercises":                [],
                    "cool_down":                []
                }

    except Exception as e:
        print(f"AI failed: {e} — using fallback")
        workout_plan = get_fallback_plan(
            weekly_split   = plan.weekly_split,
            user_exercises = plan.user_exercises,
            mode           = plan.mode,
            goal           = goal,
            level          = level,
            weight         = weight
        )

    # Save to DB
    plan.plan_data    = workout_plan
    plan.goal         = goal
    plan.level        = level
    plan.generated_by = workout_plan.get("generated_by", "ai")
    flag_modified(plan, "plan_data")
    db.commit()
    db.refresh(plan)

    return {
        "message":      "Custom workout plan generated ✅",
        "mode":         plan.mode,
        "generated_by": plan.generated_by,
        "created_at":   plan.created_at,
        "updated_at":   plan.updated_at,
        "plan":         plan.plan_data
    }


# ── Edit Exercise ─────────────────────────────────────────────────────────────

@router.put("/edit")
def edit_exercise(
    request: Request,
    payload: EditExerciseRequest,
    db: Session = Depends(get_db)
):
    """Edit any exercise in the generated plan."""
    user = get_custom_user(request, db)

    plan = db.query(WorkoutPlan).filter(
        WorkoutPlan.user_id == user.id
    ).first()

    if not plan or not plan.plan_data:
        raise HTTPException(404, "No workout plan found")

    # Get day
    day_plan = plan.plan_data.get(
        "weekly_plan", {}
    ).get(payload.day)

    if not day_plan:
        raise HTTPException(404, f"Day {payload.day} not found")

    if day_plan.get("muscle_group") == "Rest":
        raise HTTPException(400, "Cannot edit rest day")

    # Find and update exercise
    exercises = day_plan.get("exercises", [])
    found     = False

    for ex in exercises:
        if ex["name"].lower() == payload.old_exercise.lower():
            if payload.new_exercise:
                ex["name"] = payload.new_exercise
            if payload.sets:
                ex["sets"] = payload.sets
            if payload.reps:
                ex["reps"] = payload.reps
            if payload.weight:
                ex["starting_weight"] = payload.weight
            if payload.rest:
                ex["rest"] = payload.rest
            found = True
            break

    if not found:
        raise HTTPException(
            404,
            f"Exercise '{payload.old_exercise}' not found in {payload.day}"
        )

    # Save updated plan
    flag_modified(plan, "plan_data")
    db.commit()

    return {
        "message":     "Exercise updated ✅",
        "day":         payload.day,
        "updated":     payload.new_exercise or payload.old_exercise
    }


# ── Get Current Custom Plan ───────────────────────────────────────────────────

@router.get("/plan")
def get_custom_plan(
    request: Request,
    db: Session = Depends(get_db)
):
    """Get current custom workout plan."""
    user = get_custom_user(request, db)

    plan = db.query(WorkoutPlan).filter(
        WorkoutPlan.user_id == user.id
    ).first()

    if not plan or not plan.plan_data:
        raise HTTPException(
            404,
            "No custom plan found. Please generate one first."
        )

    return {
        "message":      "Custom plan fetched ✅",
        "mode":         plan.mode,
        "generated_by": plan.generated_by,
        "week_number":  plan.week_number,
        "created_at":   plan.created_at,
        "updated_at":   plan.updated_at,
        "weekly_split": plan.weekly_split,
        "plan":         plan.plan_data
    }


# ── Get Split ─────────────────────────────────────────────────────────────────

@router.get("/split")
def get_split(
    request: Request,
    db: Session = Depends(get_db)
):
    """Get current weekly split."""
    user = get_custom_user(request, db)

    plan = db.query(WorkoutPlan).filter(
        WorkoutPlan.user_id == user.id
    ).first()

    if not plan or not plan.weekly_split:
        raise HTTPException(
            404,
            "No split found. Please save split first."
        )

    workout_days = [
        day for day, data in plan.weekly_split.items()
        if not data.get("is_rest", False)
    ]

    return {
        "mode":          plan.mode,
        "workout_days":  workout_days,
        "total_days":    len(workout_days),
        "weekly_split":  plan.weekly_split
    }