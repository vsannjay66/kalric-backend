import json


def validate_workout_response(raw_text: str) -> dict:
    """
    Production-grade validator for AI workout response.
    Cleans, validates, and partially auto-corrects.
    """

    # ── Step 1 — Clean Response ───────────────────────────────────────────────
    clean = raw_text.strip()

    if clean.startswith("```"):
        parts = clean.split("```")
        clean = parts[1] if len(parts) > 1 else clean
        if clean.lower().startswith("json"):
            clean = clean[4:]

    clean = clean.strip()

    # ── Step 2 — Parse JSON ───────────────────────────────────────────────────
    try:
        data = json.loads(clean)
    except json.JSONDecodeError as e:
        # Try to find valid JSON within response
        try:
            start = clean.find("{")
            end   = clean.rfind("}") + 1
            if start != -1 and end > start:
                data = json.loads(clean[start:end])
            else:
                raise ValueError(f"Invalid JSON from AI: {e}")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON from AI: {e}")

    # ── Step 3 — Top Level Validation ─────────────────────────────────────────
    required_keys = ["goal", "level", "days_per_week", "weekly_plan"]
    for key in required_keys:
        if key not in data:
            raise ValueError(f"Missing key: {key}")

    if not isinstance(data["weekly_plan"], dict) or not data["weekly_plan"]:
        raise ValueError("weekly_plan must be a non-empty dict")

    # ── Step 4 — Day Level Validation ─────────────────────────────────────────
    # ── Step 4 — Day Level Validation ─────────────────────────────────────────
    total_calories = 0
    for day, day_data in data["weekly_plan"].items():
        print(f"DEBUG {day}: muscle_group={day_data.get('muscle_group')} exercises={len(day_data.get('exercises', []))}")
        
    for day, day_data in data["weekly_plan"].items():

        if not isinstance(day_data, dict):
            raise ValueError(f"{day} is not a valid object")

        # Skip rest days — check multiple variations
        muscle_group = day_data.get("muscle_group", "")
        if muscle_group.lower() in ["rest", "rest day", "recovery", "active recovery"]:
            continue

        # Skip days with 0 duration — also rest days
        if day_data.get("session_duration_minutes", 0) == 0:
            continue

        # Required fields per day
        day_required = [
            "session_duration_minutes",
            "session_calories_burned",
            "exercises"
        ]
        for key in day_required:
            if key not in day_data:
                raise ValueError(f"{day} missing key: {key}")

        # Validate duration
        duration = day_data["session_duration_minutes"]
        if not isinstance(duration, (int, float)) or not (30 <= duration <= 90):
            raise ValueError(f"{day}: invalid duration {duration}")

        # Validate calories
        calories = day_data["session_calories_burned"]
        if not isinstance(calories, (int, float)) or not (150 <= calories <= 800):
            raise ValueError(f"{day}: invalid calories {calories}")

        total_calories += int(calories)

        # Validate exercises
        exercises = day_data.get("exercises", [])
        if not isinstance(exercises, list):
            raise ValueError(f"{day}: exercises must be a list")

        for ex in exercises:
            if not isinstance(ex, dict):
                raise ValueError(f"{day}: invalid exercise format")

            required_ex_keys = ["name", "sets", "reps", "rest"]
            for k in required_ex_keys:
                if k not in ex:
                    raise ValueError(f"{day}: exercise missing {k}")

    # ── Step 5 — Auto Fix Total Calories ──────────────────────────────────────
    if "total_weekly_calories_burned" in data:
        if abs(data["total_weekly_calories_burned"] - total_calories) > 200:
            data["total_weekly_calories_burned"] = total_calories
    else:
        data["total_weekly_calories_burned"] = total_calories

    return data