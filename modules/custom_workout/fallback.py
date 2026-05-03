import random
from modules.custom_workout.exercise_library import get_exercises_for_muscle


def get_difficulty(level: str) -> str:
    return {
        "beginner":     "easy",
        "intermediate": "medium",
        "advanced":     "hard"
    }.get(level, "medium")


def calculate_calories(weight: float, duration: int) -> int:
    return int(weight * duration * 0.08)


def get_fallback_plan(
    weekly_split:   dict,
    user_exercises: dict,
    mode:           str,
    goal:           str,
    level:          str,
    weight:         float
) -> dict:
    """
    Fallback plan when AI fails.
    Uses user selected exercises in manual mode.
    Uses exercise library in AI mode.
    """

    difficulty     = get_difficulty(level)
    weekly_plan    = {}
    total_calories = 0

    workout_days = [
        day for day, data in weekly_split.items()
        if not data.get("is_rest", False)
    ]

    for day, data in weekly_split.items():

        # ── Rest Day ──────────────────────────────────────────────────────────
        if data.get("is_rest", False):
            weekly_plan[day] = {
                "muscle_group":             "Rest",
                "session_duration_minutes": 0,
                "session_calories_burned":  0,
                "difficulty":               "none",
                "warm_up":                  [],
                "exercises":                [],
                "cool_down":                []
            }
            continue

        # ── Workout Day ───────────────────────────────────────────────────────
        muscles  = data.get("muscles", [])
        duration = random.randint(45, 70)
        calories = calculate_calories(weight, duration)
        total_calories += calories

        muscle_label = " + ".join(
            m.capitalize() for m in muscles
        )

        exercises = []

        # ── Manual Mode — use user exercises ──────────────────────────────────
        if mode == "manual" and user_exercises and day in user_exercises:
            for muscle, exs in user_exercises[day].items():
                for ex in exs:
                    exercises.append({
                        "name":            ex["name"],
                        "exercise_type":   "compound",
                        "sets":            ex.get("sets", 3),
                        "reps":            ex.get("reps", "10-12"),
                        "rest":            ex.get("rest", "60 sec"),
                        "difficulty":      difficulty,
                        "calories_burned": random.randint(40, 90),
                        "muscle_targeted": muscle,
                        "starting_weight": ex.get("weight", "bodyweight"),
                        "weekly_increase": "2.5kg per week",
                        "tips":            "Focus on form",
                        "form_cues":       "controlled movement"
                    })

        # ── AI Mode — pick from library ───────────────────────────────────────
        else:
            for muscle in muscles:
                muscle_exercises = get_exercises_for_muscle(muscle)
                if not muscle_exercises:
                    continue

                # Pick 2-3 exercises per muscle
                count    = 2 if len(muscles) > 1 else 4
                selected = random.sample(
                    muscle_exercises,
                    min(count, len(muscle_exercises))
                )

                for ex in selected:
                    exercises.append({
                        "name":            ex["name"],
                        "exercise_type":   ex["type"],
                        "sets":            3,
                        "reps":            "10-12",
                        "rest":            "60 sec",
                        "difficulty":      difficulty,
                        "calories_burned": random.randint(40, 90),
                        "muscle_targeted": muscle,
                        "starting_weight": "20kg",
                        "weekly_increase": "2.5kg per week",
                        "tips":            "Focus on form",
                        "form_cues":       "controlled movement"
                    })

        weekly_plan[day] = {
            "muscle_group":             muscle_label,
            "session_duration_minutes": duration,
            "session_calories_burned":  calories,
            "difficulty":               difficulty,
            "warm_up": [
                {
                    "name":     "Arm Circles",
                    "duration": "2 min",
                    "tips":     "Slow and controlled"
                },
                {
                    "name":     "Dynamic Stretching",
                    "duration": "3 min",
                    "tips":     "Full body"
                }
            ],
            "exercises": exercises,
            "cool_down": [
                {
                    "name":     "Stretching",
                    "duration": "5 min",
                    "tips":     "Hold each stretch 30 sec"
                },
                {
                    "name":     "Deep Breathing",
                    "duration": "2 min",
                    "tips":     "Inhale 4 sec exhale 6 sec"
                }
            ]
        }

    return {
        "goal":                         goal,
        "level":                        level,
        "mode":                         mode,
        "generated_by":                 "fallback",
        "days_per_week":                len(workout_days),
        "motivation_message":           "Your custom plan is ready! 💪",
        "total_weekly_calories_burned": total_calories,
        "weekly_plan":                  weekly_plan,
        "progression": {
            "week_1": "Focus on form and technique",
            "week_2": "Increase weight by 5-10%",
            "week_3": "Add one extra set per exercise",
            "week_4": "Deload — reduce weight by 20%"
        },
        "pro_tips": [
            "Stay hydrated throughout workout",
            "Sleep 7-8 hours for recovery",
            "Eat protein within 30 min after workout"
        ],
        "note": "Fallback plan — AI unavailable"
    }