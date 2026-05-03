import json


def validate_custom_workout_response(raw_text: str) -> dict:
    """
    Validates and cleans AI response for custom workout.
    Auto fixes common issues.
    """

    ALL_DAYS = [
        "monday", "tuesday", "wednesday",
        "thursday", "friday", "saturday", "sunday"
    ]

    REST_DAY = {
        "muscle_group":             "Rest",
        "session_duration_minutes": 0,
        "session_calories_burned":  0,
        "difficulty":               "none",
        "warm_up":                  [],
        "exercises":                [],
        "cool_down":                []
    }

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
        # Try to find valid JSON
        try:
            start = clean.find("{")
            end   = clean.rfind("}") + 1
            if start != -1 and end > start:
                data = json.loads(clean[start:end])
            else:
                raise ValueError(f"Invalid JSON from AI: {e}")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON from AI: {e}")

    # ── Step 3 — Check Required Keys ─────────────────────────────────────────
    required_keys = ["goal", "level", "weekly_plan"]
    for key in required_keys:
        if key not in data:
            raise ValueError(f"Missing key: {key}")

    if not isinstance(data["weekly_plan"], dict):
        raise ValueError("weekly_plan must be a dict")

    # ── Step 4 — Fix All 7 Days ───────────────────────────────────────────────
    for day in ALL_DAYS:
        # Day missing completely
        if day not in data["weekly_plan"]:
            data["weekly_plan"][day] = REST_DAY.copy()
            continue

        day_data = data["weekly_plan"][day]

        # Day is empty dict
        if not day_data or day_data == {}:
            data["weekly_plan"][day] = REST_DAY.copy()
            continue

        # Day is rest
        muscle_group = day_data.get("muscle_group", "")
        if muscle_group.lower() in [
            "rest", "rest day", "recovery", "active recovery"
        ]:
            data["weekly_plan"][day] = REST_DAY.copy()
            continue

        # Day has 0 duration → treat as rest
        if day_data.get("session_duration_minutes", 0) == 0:
            data["weekly_plan"][day] = REST_DAY.copy()
            continue

        # ── Fix missing fields ────────────────────────────────────────────────
        if "warm_up" not in day_data or not day_data["warm_up"]:
            day_data["warm_up"] = [
                {"name": "Arm Circles",        "duration": "2 min", "tips": "Slow and controlled"},
                {"name": "Dynamic Stretching", "duration": "3 min", "tips": "Full body"}
            ]

        if "cool_down" not in day_data or not day_data["cool_down"]:
            day_data["cool_down"] = [
                {"name": "Stretching",    "duration": "5 min", "tips": "Hold each stretch"},
                {"name": "Deep Breathing","duration": "2 min", "tips": "Inhale 4 exhale 6"}
            ]

        if "difficulty" not in day_data:
            day_data["difficulty"] = "medium"

        if "session_duration_minutes" not in day_data:
            day_data["session_duration_minutes"] = 45

        if "session_calories_burned" not in day_data:
            day_data["session_calories_burned"] = 300

        if "muscle_group" not in day_data:
            day_data["muscle_group"] = "Full Body"

        # ── Fix exercises ─────────────────────────────────────────────────────
        exercises = day_data.get("exercises", [])

        if not isinstance(exercises, list):
            day_data["exercises"] = []
            exercises             = []

        # Fix each exercise
        for ex in exercises:
            if not isinstance(ex, dict):
                continue
            if "rest" not in ex:
                ex["rest"] = "60 sec"
            if "difficulty" not in ex:
                ex["difficulty"] = "medium"
            if "calories_burned" not in ex:
                ex["calories_burned"] = 50
            if "tips" not in ex:
                ex["tips"] = "Focus on form"
            if "form_cues" not in ex:
                ex["form_cues"] = "Controlled movement"
            if "starting_weight" not in ex:
                ex["starting_weight"] = "bodyweight"
            if "weekly_increase" not in ex:
                ex["weekly_increase"] = "2.5kg per week"
            if "muscle_targeted" not in ex:
                ex["muscle_targeted"] = "unknown"
            if "exercise_type" not in ex:
                ex["exercise_type"] = "compound"

    # ── Step 5 — Fix Total Calories ───────────────────────────────────────────
    total = sum(
        d.get("session_calories_burned", 0)
        for d in data["weekly_plan"].values()
        if isinstance(d, dict)
    )
    data["total_weekly_calories_burned"] = total

    # ── Step 6 — Fix Missing Top Level Fields ─────────────────────────────────
    if "days_per_week" not in data:
        workout_days = [
            d for d in data["weekly_plan"].values()
            if isinstance(d, dict) and
            d.get("muscle_group", "Rest") != "Rest" and
            d.get("session_duration_minutes", 0) > 0
        ]
        data["days_per_week"] = len(workout_days)

    if "motivation_message" not in data or not data["motivation_message"]:
        data["motivation_message"] = "Stay consistent! Every rep counts. 💪"

    if "progression" not in data:
        data["progression"] = {
            "week_1": "Focus on form and technique",
            "week_2": "Increase weight by 5-10%",
            "week_3": "Add one extra set per exercise",
            "week_4": "Deload — reduce weight by 20%"
        }

    if "pro_tips" not in data or not data["pro_tips"]:
        data["pro_tips"] = [
            "Stay hydrated throughout workout",
            "Sleep 7-8 hours for recovery",
            "Eat protein within 30 min after workout"
        ]

    return data