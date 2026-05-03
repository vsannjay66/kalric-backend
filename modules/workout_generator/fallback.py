import random


def get_difficulty(level: str) -> str:
    return {
        "beginner":     "easy",
        "intermediate": "medium",
        "advanced":     "hard"
    }.get(level, "medium")


def calculate_calories(weight: float, duration: int, intensity: float = 1.0) -> int:
    return int(weight * duration * 0.08 * intensity)


def to_str(value) -> str:
    """Convert list or any value to lowercase string."""
    if not value:
        return "none"
    if isinstance(value, list):
        return " ".join(str(v) for v in value).lower()
    return str(value).lower()


def get_exercise_pool(goal: str, avoid_exercises: str = "none") -> list:
    """Returns exercises filtered by goal and injuries."""

    all_exercises = {
        "fat_loss": [
            {"name": "Jump Rope",        "sets": 3, "reps": "2 min", "rest": "30 sec", "muscle_targeted": "cardio",    "tips": "Light feet"},
            {"name": "Mountain Climbers","sets": 3, "reps": "20",    "rest": "30 sec", "muscle_targeted": "core",      "tips": "Fast pace"},
            {"name": "Burpees",          "sets": 3, "reps": "15",    "rest": "45 sec", "muscle_targeted": "full body", "tips": "Explosive"},
            {"name": "Box Jumps",        "sets": 3, "reps": "12",    "rest": "60 sec", "muscle_targeted": "legs",      "tips": "Land softly"},
            {"name": "High Knees",       "sets": 3, "reps": "30 sec","rest": "30 sec", "muscle_targeted": "cardio",    "tips": "Drive knees up"},
            {"name": "Jumping Jacks",    "sets": 3, "reps": "30",    "rest": "30 sec", "muscle_targeted": "full body", "tips": "Stay light"},
            {"name": "Plank",            "sets": 3, "reps": "45 sec","rest": "30 sec", "muscle_targeted": "core",      "tips": "Keep flat"},
            {"name": "Push Ups",         "sets": 3, "reps": "12",    "rest": "45 sec", "muscle_targeted": "chest",     "tips": "Full range"},
            {"name": "Bicycle Crunches", "sets": 3, "reps": "20",    "rest": "30 sec", "muscle_targeted": "core",      "tips": "Controlled pace"},
            {"name": "Step Ups",         "sets": 3, "reps": "12",    "rest": "45 sec", "muscle_targeted": "legs",      "tips": "Full extension"},
            {"name": "Tricep Dips",      "sets": 3, "reps": "12",    "rest": "45 sec", "muscle_targeted": "triceps",   "tips": "Elbows close"},
            {"name": "Seated Row",       "sets": 3, "reps": "12",    "rest": "60 sec", "muscle_targeted": "back",      "tips": "Pull to waist"},
            {"name": "Arm Circles",      "sets": 3, "reps": "30 sec","rest": "30 sec", "muscle_targeted": "shoulders", "tips": "Both directions"},
        ],
        "bulk": [
            {"name": "Bench Press",      "sets": 4, "reps": "8-10",  "rest": "90 sec", "muscle_targeted": "chest",      "tips": "Full range"},
            {"name": "Squat",            "sets": 4, "reps": "8-10",  "rest": "90 sec", "muscle_targeted": "legs",       "tips": "Chest up"},
            {"name": "Overhead Press",   "sets": 3, "reps": "8-10",  "rest": "90 sec", "muscle_targeted": "shoulders",  "tips": "Brace core"},
            {"name": "Barbell Row",      "sets": 4, "reps": "8-10",  "rest": "90 sec", "muscle_targeted": "back",       "tips": "Pull to chest"},
            {"name": "Incline Press",    "sets": 3, "reps": "10-12", "rest": "75 sec", "muscle_targeted": "upper chest","tips": "Full stretch"},
            {"name": "Lat Pulldown",     "sets": 3, "reps": "10-12", "rest": "75 sec", "muscle_targeted": "back",       "tips": "Pull to chest"},
            {"name": "Dumbbell Curl",    "sets": 3, "reps": "12",    "rest": "60 sec", "muscle_targeted": "biceps",     "tips": "Controlled"},
            {"name": "Tricep Pushdown",  "sets": 3, "reps": "12",    "rest": "60 sec", "muscle_targeted": "triceps",    "tips": "Elbows fixed"},
            {"name": "Leg Press",        "sets": 3, "reps": "10-12", "rest": "90 sec", "muscle_targeted": "legs",       "tips": "Push through heels"},
            {"name": "Calf Raises",      "sets": 3, "reps": "15",    "rest": "45 sec", "muscle_targeted": "calves",     "tips": "Full range"},
        ],
        "strength": [
            {"name": "Deadlift",         "sets": 4, "reps": "5",     "rest": "2 min",  "muscle_targeted": "back",       "tips": "Flat back"},
            {"name": "Squat",            "sets": 4, "reps": "5",     "rest": "2 min",  "muscle_targeted": "legs",       "tips": "Go deep"},
            {"name": "Bench Press",      "sets": 4, "reps": "5",     "rest": "2 min",  "muscle_targeted": "chest",      "tips": "Control bar"},
            {"name": "Pull Ups",         "sets": 3, "reps": "6-8",   "rest": "90 sec", "muscle_targeted": "back",       "tips": "Full range"},
            {"name": "Overhead Press",   "sets": 3, "reps": "5",     "rest": "2 min",  "muscle_targeted": "shoulders",  "tips": "Brace core"},
            {"name": "Romanian Deadlift","sets": 3, "reps": "8",     "rest": "90 sec", "muscle_targeted": "hamstrings", "tips": "Hinge at hips"},
            {"name": "Barbell Row",      "sets": 3, "reps": "6-8",   "rest": "90 sec", "muscle_targeted": "back",       "tips": "Pull to chest"},
            {"name": "Dip",              "sets": 3, "reps": "8-10",  "rest": "90 sec", "muscle_targeted": "triceps",    "tips": "Lean forward"},
        ],
        "slim": [
            {"name": "Jump Rope",        "sets": 4, "reps": "2 min", "rest": "30 sec", "muscle_targeted": "cardio",     "tips": "Steady pace"},
            {"name": "Plank",            "sets": 3, "reps": "45 sec","rest": "30 sec", "muscle_targeted": "core",       "tips": "Keep flat"},
            {"name": "Lunges",           "sets": 3, "reps": "12",    "rest": "45 sec", "muscle_targeted": "legs",       "tips": "Step forward"},
            {"name": "Push Ups",         "sets": 3, "reps": "15",    "rest": "45 sec", "muscle_targeted": "chest",      "tips": "Full range"},
            {"name": "Bicycle Crunches", "sets": 3, "reps": "20",    "rest": "30 sec", "muscle_targeted": "core",       "tips": "Controlled"},
            {"name": "Wall Sit",         "sets": 3, "reps": "30 sec","rest": "45 sec", "muscle_targeted": "legs",       "tips": "Back flat"},
            {"name": "Side Plank",       "sets": 3, "reps": "30 sec","rest": "30 sec", "muscle_targeted": "obliques",   "tips": "Stack feet"},
            {"name": "Glute Bridge",     "sets": 3, "reps": "15",    "rest": "45 sec", "muscle_targeted": "glutes",     "tips": "Squeeze top"},
        ],
        "bodybuilding": [
            {"name": "Incline Press",    "sets": 4, "reps": "10-12", "rest": "75 sec", "muscle_targeted": "upper chest","tips": "Full stretch"},
            {"name": "Cable Fly",        "sets": 3, "reps": "12-15", "rest": "60 sec", "muscle_targeted": "chest",      "tips": "Squeeze top"},
            {"name": "Lat Pulldown",     "sets": 4, "reps": "10-12", "rest": "75 sec", "muscle_targeted": "back",       "tips": "Pull to chest"},
            {"name": "Lateral Raise",    "sets": 3, "reps": "15",    "rest": "45 sec", "muscle_targeted": "shoulders",  "tips": "Control weight"},
            {"name": "Preacher Curl",    "sets": 3, "reps": "12",    "rest": "60 sec", "muscle_targeted": "biceps",     "tips": "Full range"},
            {"name": "Skull Crushers",   "sets": 3, "reps": "12",    "rest": "60 sec", "muscle_targeted": "triceps",    "tips": "Elbows fixed"},
            {"name": "Leg Extension",    "sets": 3, "reps": "12-15", "rest": "60 sec", "muscle_targeted": "quads",      "tips": "Full extension"},
            {"name": "Leg Curl",         "sets": 3, "reps": "12-15", "rest": "60 sec", "muscle_targeted": "hamstrings", "tips": "Controlled"},
            {"name": "Calf Raises",      "sets": 4, "reps": "15-20", "rest": "45 sec", "muscle_targeted": "calves",     "tips": "Full range"},
        ]
    }

    exercises = all_exercises.get(goal, all_exercises["strength"])

    # Filter by injuries
    avoid_str = to_str(avoid_exercises)
    if avoid_str and avoid_str != "none":
        avoid_list = [e.strip().lower() for e in avoid_str.split(",") if e.strip()]
        filtered   = [
            ex for ex in exercises
            if not any(avoid in ex["name"].lower() for avoid in avoid_list)
        ]
        exercises = filtered if len(filtered) >= 4 else exercises

    return exercises


def get_splits(goal: str) -> list:
    splits_map = {
        "fat_loss":     ["Full Body + Cardio", "Cardio + Core", "Lower Body + Cardio", "HIIT + Core"],
        "bulk":         ["Chest + Triceps", "Back + Biceps", "Legs", "Shoulders + Core"],
        "strength":     ["Upper Body", "Lower Body", "Full Body", "Core + Conditioning"],
        "slim":         ["Cardio + Core", "Full Body", "Lower Body", "Upper Body + Cardio"],
        "bodybuilding": ["Chest + Triceps", "Back + Biceps", "Legs", "Shoulders + Arms"],
    }
    return splits_map.get(goal, ["Full Body", "Upper Body", "Lower Body", "Core"])


def get_fallback_workout(
    goal:            str,
    level:           str,
    days:            int,
    weight:          float = 70.0,
    avoid_exercises: str   = "none",
    health_problems: str   = "none"
) -> dict:

    difficulty  = get_difficulty(level)
    exercises   = get_exercise_pool(goal, avoid_exercises)
    splits      = get_splits(goal)

    # Health based intensity
    intensity   = 1.0
    health_note = ""

    health_str = to_str(health_problems)
    if health_str and health_str != "none":
        if "diabetes" in health_str:
            intensity   = 0.85
            health_note = "Moderate intensity — monitor blood sugar"
        elif "bp" in health_str or "blood pressure" in health_str:
            intensity   = 0.80
            health_note = "Low intensity — avoid sudden movements"
        elif "heart" in health_str:
            intensity   = 0.75
            health_note = "Light intensity — consult doctor before heavy cardio"

    all_days     = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    workout_days = all_days[:days]
    rest_days    = all_days[days:]
    weekly_plan  = {}

    for i, day in enumerate(workout_days):
        duration      = random.randint(45, 70)
        calories      = calculate_calories(weight, duration, intensity)
        day_exercises = exercises.copy()
        random.shuffle(day_exercises)
        day_exercises = day_exercises[:4]

        weekly_plan[day] = {
            "muscle_group":             splits[i % len(splits)],
            "session_duration_minutes": duration,
            "session_calories_burned":  calories,
            "difficulty":               difficulty,
            "health_note":              health_note if health_note else "none",
            "warm_up": [
                {"name": "Jump Rope",          "duration": "3 min", "tips": "Light pace"},
                {"name": "Dynamic Stretching", "duration": "5 min", "tips": "Full body"}
            ],
            "exercises": [
                {**ex, "difficulty": difficulty, "calories_burned": random.randint(40, 90)}
                for ex in day_exercises
            ],
            "cool_down": [
                {"name": "Stretching", "duration": "5 min", "tips": "Hold each stretch 30 sec"},
                {"name": "Breathing",  "duration": "2 min", "tips": "Inhale 4 sec exhale 6 sec"}
            ]
        }

    for day in rest_days:
        weekly_plan[day] = {
            "muscle_group":             "Rest",
            "session_duration_minutes": 0,
            "session_calories_burned":  0,
            "difficulty":               "none",
            "health_note":              "none",
            "warm_up":                  [],
            "exercises":                [],
            "cool_down":                []
        }

    total_calories = sum(d["session_calories_burned"] for d in weekly_plan.values())

    return {
        "goal":                         goal,
        "level":                        level,
        "generated_by":                 "fallback",
        "days_per_week":                days,
        "motivation_message":           "Consistency beats intensity. Keep going!",
        "total_weekly_calories_burned": total_calories,
        "weekly_plan":                  weekly_plan,
        "progression": {
            "week_1": "Focus on form",
            "week_2": "Increase weight",
            "week_3": "Increase volume",
            "week_4": "Deload"
        },
        "pro_tips": [
            "Stay hydrated",
            "Sleep well",
            "Maintain proper form"
        ],
        "note": "Fallback plan — AI unavailable"
    }