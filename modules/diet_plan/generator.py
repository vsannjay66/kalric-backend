from modules.diet_plan.calculator import (
    calculate_bmr,
    calculate_tdee,
    calculate_target_calories,
    calculate_macros,
    calculate_water_intake,
    get_diet_level,
    get_champion_style,
    get_supplements
)
from modules.diet_plan.prompt_builder import build_diet_prompt
from modules.diet_plan.validator      import validate_diet_response

def generate_diet_plan(profile: dict, preferences: dict) -> dict:

    # ── Extract profile data ──────────────────────────────────────────────────
    body   = profile.get("body_metrics",  {})
    goals  = profile.get("fitness_goals", {})
    life   = profile.get("lifestyle",     {})
    health = profile.get("health",        {})
    user   = profile.get("user",          {})

    # User info
    name   = user.get("name", "Champion")

    # Body metrics — extract ALL first
    age    = body.get("age",    25)
    gender = body.get("gender", "male")
    height = body.get("height", 170)
    weight = body.get("weight", 70)      # ← weight extracted here
    bmi    = body.get("bmi",    24)

    # Goals — extract ALL
    goal          = goals.get("goal",                   "strength")
    workout_time  = goals.get("preferred_workout_time", "morning")
    workout_exp   = goals.get("workout_experience",     "beginner")
    target_weight = goals.get("target_weight",          weight)    # ← uses weight
    target_days   = goals.get("target_days",            90)

    # Lifestyle — extract ALL
    food_preference = life.get("food_preference", "non-veg")
    activity_level  = life.get("activity_level",  "moderate")
    sleep_hours     = life.get("sleep_hours",      7)
    smoker          = life.get("smoker",           False)
    stress_level    = life.get("stress_level",     "low")

    # Health — extract ALL
    health_problems = health.get("health_problems", "none")
    injuries        = health.get("injuries",        "none")
    gym_access      = goals.get("gym_access",       True)

    # ── NOW validate — all variables ready ───────────────────────────────────
    from modules.diet_plan.calculator import validate_and_fix_profile

    validation = validate_and_fix_profile(
        weight        = weight,
        height        = height,
        age           = age,
        target_weight = target_weight,
        target_days   = target_days,
        sleep_hours   = sleep_hours,
        goal          = goal,
        stress_level  = stress_level,
        injuries      = injuries,
        gym_access    = gym_access
    )

    # Apply fixes
    if validation["fixes"].get("height"):
        height = validation["fixes"]["height"]

    if validation["fixes"].get("target_days"):
        target_days = validation["fixes"]["target_days"]

    # Log warnings
    if validation["warnings"]:
        print("⚠️ Profile warnings:")
        for w in validation["warnings"]:
            print(f"  → {w}")

    print(f"BMR → weight:{weight} height:{height} age:{age} gender:{gender}")

    # ── Calculate nutrition targets ───────────────────────────────────────────
    bmr      = calculate_bmr(weight, height, age, gender)
    tdee     = calculate_tdee(bmr, activity_level)
    calories = calculate_target_calories(tdee, goal)
    macros   = calculate_macros(calories, goal, weight)
    water    = calculate_water_intake(weight, activity_level)
    level    = get_diet_level(workout_exp)
    champion = get_champion_style(goal)
    supps    = get_supplements(goal, level)

    print(f"BMR: {round(bmr)} | TDEE: {round(tdee)} | Target: {calories} kcal")
    print(f"Protein: {macros['protein_g']}g | Carbs: {macros['carbs_g']}g | Fat: {macros['fat_g']}g")
    print(f"Champion: {champion['champion']} | Level: {level}")

    # ── Build prompt data ─────────────────────────────────────────────────────
    prompt_data = {
        "name":            name,
        "age":             age,
        "gender":          gender,
        "height":          height,
        "weight":          weight,
        "bmi":             bmi,
        "goal":            goal,
        "level":           workout_exp,
        "diet_level":      level,
        "food_preference": food_preference,
        "activity_level":  activity_level,
        "stress_level":    stress_level,
        "gym_access":      gym_access,
        "target_weight":   target_weight,
        "target_days":     target_days,
        "sleep_hours":     sleep_hours,
        "injuries":        injuries,
        "smoker":          smoker,
        "health_problems": health_problems,
        "injuries":        injuries,
        "workout_time":    workout_time,
        "calories":        calories,
        "macros":          macros,
        "water":           water,
        "champion_style":  champion,
        "daily_budget":    preferences.get("daily_budget",  200),
        "weekly_budget":   preferences.get("weekly_budget", 1400),
        "meals_per_day":   preferences.get("meals_per_day", 5),
        "preferences":     preferences
    }

    # ── Generate with AI ──────────────────────────────────────────────────────
    try:
        from modules.workout_generator.llm_client import call_llm_with_fallback

        print("Generating champion diet plan with AI...")
        prompt        = build_diet_prompt(prompt_data)
        raw, provider = call_llm_with_fallback(prompt)
        plan          = validate_diet_response(raw)

        # Add metadata
        plan["generated_by"]   = provider
        plan["supplements"]    = supps
        plan["bmr"]            = round(bmr)
        plan["tdee"]           = round(tdee)
        plan["champion_style"] = champion

        print(f"Diet plan generated by: {provider} ✅")
        return plan

    except Exception as e:
        print(f"AI failed: {e} — using fallback diet plan")

        from modules.diet_plan.fallback import get_fallback_diet

        fallback = get_fallback_diet(
            goal            = goal,
            food_preference = food_preference,
            calories        = calories,
            macros          = macros,
            water           = water,
            name            = name,
            daily_budget    = preferences.get("daily_budget", 200)
        )

        # Add metadata to fallback
        fallback["supplements"]    = supps
        fallback["bmr"]            = round(bmr)
        fallback["tdee"]           = round(tdee)
        fallback["champion_style"] = champion

        print("Fallback diet plan returned ✅")
        return fallback