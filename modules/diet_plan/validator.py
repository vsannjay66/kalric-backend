import json


def validate_diet_response(raw_text: str) -> dict:
    """
    Validate and clean AI diet response.
    Auto fixes common issues.
    Never crashes — always returns valid plan.
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
        try:
            start = clean.find("{")
            end   = clean.rfind("}") + 1
            if start != -1 and end > start:
                data = json.loads(clean[start:end])
            else:
                raise ValueError(f"Cannot parse JSON: {e}")
        except json.JSONDecodeError:
            raise ValueError(f"Cannot parse JSON: {e}")

    # ── Step 3 — Check Required Keys ─────────────────────────────────────────
    required = ["goal", "daily_calories", "meals"]
    for key in required:
        if key not in data:
            raise ValueError(f"Missing required key: {key}")

    if not isinstance(data["meals"], list):
        raise ValueError("meals must be a list")

    if len(data["meals"]) == 0:
        raise ValueError("meals list cannot be empty")

    # ── Step 4 — Fix Top Level Missing Fields ─────────────────────────────────
    if "motivation_message" not in data or not data["motivation_message"]:
        data["motivation_message"] = (
            "Champions are made in the kitchen! "
            "Every meal brings you closer to your goal. 💪"
        )

    if "champion_reference" not in data:
        data["champion_reference"] = "Indian Champion Athlete"

    if "champion_quote" not in data:
        data["champion_quote"] = (
            "Eat right train hard and results will follow."
        )

    if "foods_to_eat" not in data or not data["foods_to_eat"]:
        data["foods_to_eat"] = [
            "Dal, roti, brown rice, oats",
            "Chicken breast, eggs, fish, paneer",
            "Seasonal vegetables, salads",
            "Curd, milk, Greek yogurt",
            "Almonds, walnuts, peanut butter",
            "Banana, apple, orange, berries"
        ]

    if "foods_to_avoid" not in data or not data["foods_to_avoid"]:
        data["foods_to_avoid"] = [
            "Fried foods — samosa pakora chips",
            "Sugary drinks — cold drinks juice sweetened chai",
            "Processed foods — biscuits instant noodles",
            "White bread maida products",
            "Late night heavy meals"
        ]

    if "champion_foods" not in data:
        data["champion_foods"] = []

    if "grocery_list" not in data:
        data["grocery_list"] = []

    if "meal_prep_tips" not in data or not data["meal_prep_tips"]:
        data["meal_prep_tips"] = [
            "Cook rice and dal in bulk on Sunday",
            "Grill chicken in batch and store in fridge",
            "Soak almonds and sprouts overnight",
            "Keep boiled eggs ready in fridge",
            "Chop vegetables in advance and store"
        ]

    if "budget_tips" not in data or not data["budget_tips"]:
        data["budget_tips"] = [
            "Buy vegetables from local sabzi mandi — 30% cheaper",
            "Buy chicken in bulk — freeze portions",
            "Buy eggs by dozen — most affordable protein",
            "Seasonal fruits are cheaper and fresher",
            "Dal is cheapest high protein food available"
        ]

    if "pro_tips" not in data or not data["pro_tips"]:
        data["pro_tips"] = [
            "Eat every 3-4 hours — never let yourself starve",
            "Protein at every meal is non negotiable",
            "Drink a full glass of water before every meal",
            "Prepare meals in advance like a professional athlete",
            "Sleep 7-8 hours — recovery happens during sleep"
        ]

    # ── Step 5 — Fix Each Meal ────────────────────────────────────────────────
    for i, meal in enumerate(data["meals"]):
        if not isinstance(meal, dict):
            continue

        # Fix missing meal fields
        if "meal_name" not in meal:
            meal["meal_name"] = f"Meal {i + 1}"

        if "time" not in meal:
            default_times = [
                "7:00 AM", "9:00 AM", "12:00 PM",
                "3:00 PM", "6:00 PM", "8:00 PM"
            ]
            meal["time"] = default_times[i] if i < len(default_times) else "12:00 PM"

        if "meal_type" not in meal:
            meal["meal_type"] = "meal"

        if "champion_note" not in meal or not meal["champion_note"]:
            meal["champion_note"] = "Champions eat with purpose and precision"

        if "why_this_meal" not in meal or not meal["why_this_meal"]:
            meal["why_this_meal"] = "Balanced nutrition for your goal"

        if "preparation_tip" not in meal or not meal["preparation_tip"]:
            meal["preparation_tip"] = "Prepare fresh for best results"

        if "preparation_time" not in meal:
            meal["preparation_time"] = "15-20 minutes"

        if "estimated_cost_inr" not in meal:
            meal["estimated_cost_inr"] = 0

        # Fix foods list
        if "foods" not in meal or not isinstance(meal["foods"], list):
            meal["foods"] = []

        # Fix each food item
        for food in meal["foods"]:
            if not isinstance(food, dict):
                continue

            if "quantity_g" not in food:
                food["quantity_g"] = None

            if "quantity_ml" not in food:
                food["quantity_ml"] = None

            if "calories" not in food:
                food["calories"] = 0

            if "protein_g" not in food:
                food["protein_g"] = 0.0

            if "carbs_g" not in food:
                food["carbs_g"] = 0.0

            if "fat_g" not in food:
                food["fat_g"] = 0.0

            if "cost_inr" not in food:
                food["cost_inr"] = 0

            if "preparation" not in food:
                food["preparation"] = "Prepare as desired"

            if "why" not in food:
                food["why"] = "Good nutrition source"

        # Fix meal totals from foods if missing
        if "total_calories" not in meal or meal["total_calories"] == 0:
            meal["total_calories"] = sum(
                f.get("calories", 0) for f in meal["foods"]
            )

        if "total_protein_g" not in meal or meal["total_protein_g"] == 0:
            meal["total_protein_g"] = round(
                sum(f.get("protein_g", 0) for f in meal["foods"]), 1
            )

        if "total_carbs_g" not in meal or meal["total_carbs_g"] == 0:
            meal["total_carbs_g"] = round(
                sum(f.get("carbs_g", 0) for f in meal["foods"]), 1
            )

        if "total_fat_g" not in meal or meal["total_fat_g"] == 0:
            meal["total_fat_g"] = round(
                sum(f.get("fat_g", 0) for f in meal["foods"]), 1
            )

        if "estimated_cost_inr" not in meal or meal["estimated_cost_inr"] == 0:
            meal["estimated_cost_inr"] = sum(
                f.get("cost_inr", 0) for f in meal["foods"]
            )

    # ── Step 6 — Fix Daily Totals ─────────────────────────────────────────────
    if "daily_totals" not in data or not data["daily_totals"]:
        data["daily_totals"] = {}

    data["daily_totals"]["total_calories"] = sum(
        m.get("total_calories", 0) for m in data["meals"]
    )
    data["daily_totals"]["total_protein_g"] = round(
        sum(m.get("total_protein_g", 0) for m in data["meals"]), 1
    )
    data["daily_totals"]["total_carbs_g"] = round(
        sum(m.get("total_carbs_g", 0) for m in data["meals"]), 1
    )
    data["daily_totals"]["total_fat_g"] = round(
        sum(m.get("total_fat_g", 0) for m in data["meals"]), 1
    )
    data["daily_totals"]["total_cost_inr"] = sum(
        m.get("estimated_cost_inr", 0) for m in data["meals"]
    )

    return data