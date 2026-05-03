import json
from modules.workout_generator.llm_client import call_llm_with_fallback
from modules.diet_plan.prompt_builder import (
    build_edit_food_prompt,
    build_edit_meal_prompt
)


def parse_ai_response(raw_response: str) -> dict:
    """Clean and parse AI response to JSON."""
    clean = raw_response.strip()

    if clean.startswith("```"):
        parts = clean.split("```")
        clean = parts[1] if len(parts) > 1 else clean
        if clean.lower().startswith("json"):
            clean = clean[4:]

    clean = clean.strip()

    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        start = clean.find("{")
        end   = clean.rfind("}") + 1
        if start != -1 and end > start:
            return json.loads(clean[start:end])
        raise ValueError("Could not parse AI response as JSON")


def edit_single_food(
    plan_data:        dict,
    meal_name:        str,
    food_name:        str,
    reason:           str,
    replace_with:     str,
    goal:             str,
    daily_budget:     float,
    food_preference:  str,
    allergies:        str
) -> dict:
    """
    Edit single food item in a meal.
    ONLY that food is sent to AI.
    Rest of plan stays exactly the same.
    DB auto updated after this returns.
    """

    meals    = plan_data.get("meals", [])
    meal_idx = None
    food_idx = None
    meal     = None

    # ── Find meal and food ────────────────────────────────────────────────────
    for i, m in enumerate(meals):
        if m.get("meal_name", "").lower() == meal_name.lower():
            meal_idx = i
            meal     = m
            for j, f in enumerate(m.get("foods", [])):
                if f.get("name", "").lower() == food_name.lower():
                    food_idx = j
                    break
            break

    if meal_idx is None:
        raise ValueError(
            f"Meal '{meal_name}' not found. "
            f"Available meals: {[m['meal_name'] for m in meals]}"
        )

    if food_idx is None:
        raise ValueError(
            f"Food '{food_name}' not found in {meal_name}. "
            f"Available foods: {[f['name'] for f in meal.get('foods', [])]}"
        )

    # ── Calculate budget remaining ────────────────────────────────────────────
    current_food_cost = meal["foods"][food_idx].get("cost_inr", 0)
    meal_budget       = round(daily_budget / len(meals), 0)
    budget_remaining  = meal_budget - meal.get("estimated_cost_inr", 0) + current_food_cost

    # ── Build prompt and call AI ──────────────────────────────────────────────
    prompt = build_edit_food_prompt(
        current_meal     = meal,
        food_to_edit     = food_name,
        reason           = reason,
        replace_with     = replace_with,
        goal             = goal,
        budget_remaining = max(budget_remaining, 20),
        food_preference  = food_preference,
        allergies        = allergies or "None"
    )

    raw_response, provider = call_llm_with_fallback(prompt)
    new_food               = parse_ai_response(raw_response)

    # ── Validate new food has required fields ─────────────────────────────────
    required_food_fields = [
        "name", "calories", "protein_g",
        "carbs_g", "fat_g"
    ]
    for field in required_food_fields:
        if field not in new_food:
            new_food[field] = meal["foods"][food_idx].get(field, 0)

    if "cost_inr" not in new_food:
        new_food["cost_inr"] = meal["foods"][food_idx].get("cost_inr", 0)

    if "quantity_g" not in new_food:
        new_food["quantity_g"] = meal["foods"][food_idx].get("quantity_g", None)

    if "quantity_ml" not in new_food:
        new_food["quantity_ml"] = meal["foods"][food_idx].get("quantity_ml", None)

    if "preparation" not in new_food:
        new_food["preparation"] = "Prepare as desired"

    if "why" not in new_food:
        new_food["why"] = f"Good replacement for {goal} goal"

    # ── Calculate differences ─────────────────────────────────────────────────
    old_food  = meal["foods"][food_idx]
    cal_diff  = new_food.get("calories", 0)  - old_food.get("calories", 0)
    prot_diff = new_food.get("protein_g", 0) - old_food.get("protein_g", 0)
    carb_diff = new_food.get("carbs_g", 0)   - old_food.get("carbs_g", 0)
    fat_diff  = new_food.get("fat_g", 0)     - old_food.get("fat_g", 0)
    cost_diff = new_food.get("cost_inr", 0)  - old_food.get("cost_inr", 0)

    # ── Replace food in plan ──────────────────────────────────────────────────
    plan_data["meals"][meal_idx]["foods"][food_idx] = new_food

    # ── Update meal totals ────────────────────────────────────────────────────
    plan_data["meals"][meal_idx]["total_calories"]     = round(
        plan_data["meals"][meal_idx].get("total_calories", 0) + cal_diff, 0
    )
    plan_data["meals"][meal_idx]["total_protein_g"]    = round(
        plan_data["meals"][meal_idx].get("total_protein_g", 0) + prot_diff, 1
    )
    plan_data["meals"][meal_idx]["total_carbs_g"]      = round(
        plan_data["meals"][meal_idx].get("total_carbs_g", 0) + carb_diff, 1
    )
    plan_data["meals"][meal_idx]["total_fat_g"]        = round(
        plan_data["meals"][meal_idx].get("total_fat_g", 0) + fat_diff, 1
    )
    plan_data["meals"][meal_idx]["estimated_cost_inr"] = round(
        plan_data["meals"][meal_idx].get("estimated_cost_inr", 0) + cost_diff, 0
    )

    # ── Update daily totals ───────────────────────────────────────────────────
    if "daily_totals" not in plan_data:
        plan_data["daily_totals"] = {}

    plan_data["daily_totals"]["total_calories"]  = round(
        plan_data["daily_totals"].get("total_calories", 0) + cal_diff, 0
    )
    plan_data["daily_totals"]["total_protein_g"] = round(
        plan_data["daily_totals"].get("total_protein_g", 0) + prot_diff, 1
    )
    plan_data["daily_totals"]["total_carbs_g"]   = round(
        plan_data["daily_totals"].get("total_carbs_g", 0) + carb_diff, 1
    )
    plan_data["daily_totals"]["total_fat_g"]     = round(
        plan_data["daily_totals"].get("total_fat_g", 0) + fat_diff, 1
    )
    plan_data["daily_totals"]["total_cost_inr"]  = round(
        plan_data["daily_totals"].get("total_cost_inr", 0) + cost_diff, 0
    )

    # ── Add edit metadata ─────────────────────────────────────────────────────
    plan_data["last_edited"]  = (
        f"Food '{food_name}' in {meal_name} "
        f"replaced with '{new_food['name']}'"
    )
    plan_data["edited_by"]    = provider
    plan_data["edit_type"]    = "food"

    return plan_data


def edit_entire_meal(
    plan_data:        dict,
    meal_name:        str,
    reason:           str,
    goal:             str,
    daily_budget:     float,
    food_preference:  str,
    allergies:        str,
    disliked_foods:   str,
    new_timing:       str = None
) -> dict:
    """
    Edit entire meal.
    ONLY that one meal is sent to AI.
    All other meals stay exactly unchanged.
    DB auto updated after this returns.
    """

    meals    = plan_data.get("meals", [])
    meal_idx = None
    meal     = None

    # ── Find meal ─────────────────────────────────────────────────────────────
    for i, m in enumerate(meals):
        if m.get("meal_name", "").lower() == meal_name.lower():
            meal_idx = i
            meal     = m
            break

    if meal_idx is None:
        raise ValueError(
            f"Meal '{meal_name}' not found. "
            f"Available meals: {[m['meal_name'] for m in meals]}"
        )

    # ── Calculate remaining macros from other meals ───────────────────────────
    other_calories = sum(
        m.get("total_calories", 0)
        for i, m in enumerate(meals)
        if i != meal_idx
    )
    other_protein  = sum(
        m.get("total_protein_g", 0)
        for i, m in enumerate(meals)
        if i != meal_idx
    )
    other_carbs    = sum(
        m.get("total_carbs_g", 0)
        for i, m in enumerate(meals)
        if i != meal_idx
    )
    other_fat      = sum(
        m.get("total_fat_g", 0)
        for i, m in enumerate(meals)
        if i != meal_idx
    )

    macros_remaining = {
        "calories":  max(plan_data.get("daily_calories", 2000) - other_calories, 0),
        "protein_g": max(round(plan_data.get("daily_protein_g", 150) - other_protein, 1), 0),
        "carbs_g":   max(round(plan_data.get("daily_carbs_g", 200) - other_carbs, 1), 0),
        "fat_g":     max(round(plan_data.get("daily_fat_g", 60) - other_fat, 1), 0)
    }

    budget_per_meal = round(daily_budget / len(meals), 0)

    # ── Build prompt and call AI ──────────────────────────────────────────────
    prompt = build_edit_meal_prompt(
        current_meal     = meal,
        reason           = reason,
        goal             = goal,
        budget_per_meal  = budget_per_meal,
        food_preference  = food_preference,
        allergies        = allergies    or "None",
        disliked_foods   = disliked_foods or "None",
        macros_remaining = macros_remaining,
        new_timing       = new_timing
    )

    raw_response, provider = call_llm_with_fallback(prompt)
    new_meal               = parse_ai_response(raw_response)

    # ── Validate new meal ─────────────────────────────────────────────────────
    if "meal_name" not in new_meal:
        new_meal["meal_name"] = meal_name

    if "time" not in new_meal:
        new_meal["time"] = new_timing or meal.get("time", "12:00 PM")

    if "meal_type" not in new_meal:
        new_meal["meal_type"] = meal.get("meal_type", "meal")

    if "foods" not in new_meal or not isinstance(new_meal["foods"], list):
        new_meal["foods"] = []

    if "champion_note" not in new_meal:
        new_meal["champion_note"] = "Champions eat with purpose"

    if "why_this_meal" not in new_meal:
        new_meal["why_this_meal"] = f"Optimized for {goal} goal"

    if "preparation_tip" not in new_meal:
        new_meal["preparation_tip"] = "Prepare fresh for best results"

    if "preparation_time" not in new_meal:
        new_meal["preparation_time"] = "20 minutes"

    # Fix meal totals from foods
    if not new_meal.get("total_calories"):
        new_meal["total_calories"] = sum(
            f.get("calories", 0) for f in new_meal["foods"]
        )
    if not new_meal.get("total_protein_g"):
        new_meal["total_protein_g"] = round(
            sum(f.get("protein_g", 0) for f in new_meal["foods"]), 1
        )
    if not new_meal.get("total_carbs_g"):
        new_meal["total_carbs_g"] = round(
            sum(f.get("carbs_g", 0) for f in new_meal["foods"]), 1
        )
    if not new_meal.get("total_fat_g"):
        new_meal["total_fat_g"] = round(
            sum(f.get("fat_g", 0) for f in new_meal["foods"]), 1
        )
    if not new_meal.get("estimated_cost_inr"):
        new_meal["estimated_cost_inr"] = sum(
            f.get("cost_inr", 0) for f in new_meal["foods"]
        )

    # ── Replace meal in plan ──────────────────────────────────────────────────
    old_meal = plan_data["meals"][meal_idx]
    plan_data["meals"][meal_idx] = new_meal

    # ── Recalculate daily totals from scratch ─────────────────────────────────
    plan_data["daily_totals"] = {
        "total_calories":  sum(
            m.get("total_calories", 0) for m in plan_data["meals"]
        ),
        "total_protein_g": round(sum(
            m.get("total_protein_g", 0) for m in plan_data["meals"]
        ), 1),
        "total_carbs_g":   round(sum(
            m.get("total_carbs_g", 0) for m in plan_data["meals"]
        ), 1),
        "total_fat_g":     round(sum(
            m.get("total_fat_g", 0) for m in plan_data["meals"]
        ), 1),
        "total_cost_inr":  sum(
            m.get("estimated_cost_inr", 0) for m in plan_data["meals"]
        )
    }

    # ── Add edit metadata ─────────────────────────────────────────────────────
    plan_data["last_edited"] = (
        f"Entire meal '{meal_name}' replaced"
    )
    plan_data["edited_by"]   = provider
    plan_data["edit_type"]   = "meal"

    return plan_data