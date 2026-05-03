def to_list(value) -> list:
    """Convert string or None to clean list."""
    if not value or str(value).lower() == "none":
        return []
    if isinstance(value, list):
        return value
    return [v.strip() for v in str(value).split(",")]

def preprocess_user_profile(profile: dict) -> dict:
    body   = profile.get("body_metrics", {})
    goals  = profile.get("fitness_goals", {})
    life   = profile.get("lifestyle", {})
    health = profile.get("health", {})
    user   = profile.get("user", {})

    def to_list(value) -> list:
        if not value or str(value).lower() == "none":
            return []
        if isinstance(value, list):
            return value
        return [v.strip() for v in str(value).split(",")]

    return {
    # User
    "name":                   user.get("name", "User"),
    "preferred_language":     user.get("preferred_language", "English"),

    # Body
    "age":                    body.get("age", 25),
    "gender":                 body.get("gender", "male"),
    "height":                 body.get("height", 170),
    "weight":                 body.get("weight", 70),
    "bmi":                    body.get("bmi", 24.0),
    "body_fat_percentage":    body.get("body_fat_percentage") or None,  # ← fixed
    "muscle_mass":            body.get("muscle_mass") or None,           # ← fixed

    # Goals
    "goal":                   goals.get("goal", "strength"),
    "target_weight":          goals.get("target_weight"),
    "target_days":            goals.get("target_days", 90),
    "workout_experience":     goals.get("workout_experience", "beginner"),
    "gym_access":             goals.get("gym_access", True),
    "workout_days_per_week":  goals.get("workout_days_per_week", 4),
    "preferred_workout_time": goals.get("preferred_workout_time", "morning"),

    # Lifestyle
    "food_preference":        life.get("food_preference", "non-veg"),
    "water_intake":           life.get("water_intake", 2.5),
    "sleep_hours":            life.get("sleep_hours", 7),
    "activity_level":         life.get("activity_level", "moderate"),
    "stress_level":           life.get("stress_level", "low"),
    "smoker":                 life.get("smoker", False),                 # ← fixed

    # Health
    "health_problems":        to_list(health.get("health_problems")),
    "injuries":               to_list(health.get("injuries")),
    "medications":            to_list(health.get("medications")),
}