from modules.workout_generator.preprocess     import preprocess_user_profile
from modules.workout_generator.rules          import apply_rules
from modules.workout_generator.prompt_builder import build_workout_prompt
from modules.workout_generator.llm_client     import call_llm_with_fallback
from modules.workout_generator.validator      import validate_workout_response
from modules.workout_generator.fallback       import get_fallback_workout


def generate_workout_plan(profile: dict) -> dict:
    """
    Main entry point — called from main.py
    Takes full user profile dict → returns workout plan dict
    """
    # Step 1 — Preprocess
    data = preprocess_user_profile(profile)

    # Step 2 — Apply rules
    data = apply_rules(data)

    # Step 3 — Build prompt
    prompt = build_workout_prompt(data)

    # Step 4 — Call AI with fallback
    try:
        raw_response, provider = call_llm_with_fallback(prompt)
        print(f"Response from: {provider}")

        # Step 5 — Validate
        workout_plan = validate_workout_response(raw_response)
        workout_plan["generated_by"] = provider
        return workout_plan

    except Exception as e:
        print(f"AI generation failed: {type(e).__name__}: {e}")
        print("Using fallback plan...")

        # Step 6 — Fallback
        return get_fallback_workout(
            goal            = data["goal"],
            level           = data["workout_experience"],
            days            = data["workout_days_per_week"],
            weight          = data.get("weight", 70.0),
            avoid_exercises = data.get("avoid_exercises", "none"),
            health_problems = data.get("health_problems", "none")
        )