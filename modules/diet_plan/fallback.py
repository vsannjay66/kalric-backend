def get_fallback_diet(
    goal:            str,
    food_preference: str,
    calories:        int,
    macros:          dict,
    water:           dict,
    name:            str   = "Champion",
    daily_budget:    float = 200.0
) -> dict:
    """
    Fallback diet plan when AI fails.
    Real Indian food with exact measurements.
    Budget aware. Goal specific.
    """

    budget_per_meal = round(daily_budget / 5, 0)

    # ── Non Veg Meals ─────────────────────────────────────────────────────────
    non_veg_meals = [
        {
            "meal_name":          "Early Morning",
            "time":               "6:30 AM",
            "meal_type":          "early_morning",
            "total_calories":     100,
            "total_protein_g":    3.0,
            "total_carbs_g":      8.0,
            "total_fat_g":        6.0,
            "estimated_cost_inr": 15,
            "champion_note":      "Every champion starts the day right",
            "why_this_meal":      "Kickstart metabolism and hydration after overnight fast",
            "preparation_time":   "2 minutes",
            "preparation_tip":    "Soak almonds overnight for better nutrient absorption",
            "foods": [
                {
                    "name":        "Warm water with lemon",
                    "quantity_g":  None,
                    "quantity_ml": 300,
                    "calories":    10,
                    "protein_g":   0.0,
                    "carbs_g":     3.0,
                    "fat_g":       0.0,
                    "cost_inr":    5,
                    "preparation": "Squeeze half lemon in warm water",
                    "why":         "Alkalizes body and kickstarts digestion"
                },
                {
                    "name":        "Soaked almonds",
                    "quantity_g":  15,
                    "quantity_ml": None,
                    "calories":    90,
                    "protein_g":   3.0,
                    "carbs_g":     3.0,
                    "fat_g":       8.0,
                    "cost_inr":    10,
                    "preparation": "Soak 10 almonds overnight. Peel skin before eating.",
                    "why":         "Healthy fats and Vitamin E to start the day"
                }
            ]
        },
        {
            "meal_name":          "Breakfast",
            "time":               "8:00 AM",
            "meal_type":          "breakfast",
            "total_calories":     int(calories * 0.25),
            "total_protein_g":    round(macros['protein_g'] * 0.28, 1),
            "total_carbs_g":      round(macros['carbs_g'] * 0.25, 1),
            "total_fat_g":        round(macros['fat_g'] * 0.20, 1),
            "estimated_cost_inr": int(budget_per_meal),
            "champion_note":      "Virat Kohli never skips breakfast — neither should you",
            "why_this_meal":      "Highest protein meal of the day. Sets metabolism for full day.",
            "preparation_time":   "15 minutes",
            "preparation_tip":    "Boil eggs night before. Keep oats soaked. Save morning time.",
            "foods": [
                {
                    "name":        "Whole eggs boiled",
                    "quantity_g":  150,
                    "quantity_ml": None,
                    "calories":    210,
                    "protein_g":   18.0,
                    "carbs_g":     1.5,
                    "fat_g":       14.0,
                    "cost_inr":    30,
                    "preparation": "Boil 3 eggs for 8-10 minutes. Add salt and pepper.",
                    "why":         "Complete protein with all essential amino acids"
                },
                {
                    "name":        "Oats cooked",
                    "quantity_g":  80,
                    "quantity_ml": None,
                    "calories":    300,
                    "protein_g":   10.0,
                    "carbs_g":     54.0,
                    "fat_g":       5.0,
                    "cost_inr":    15,
                    "preparation": "Cook in 200ml milk or water. Add banana slices.",
                    "why":         "Complex carbs for sustained energy through morning"
                },
                {
                    "name":        "Milk full fat",
                    "quantity_g":  None,
                    "quantity_ml": 200,
                    "calories":    130,
                    "protein_g":   6.5,
                    "carbs_g":     9.5,
                    "fat_g":       7.5,
                    "cost_inr":    20,
                    "preparation": "Warm milk. Can add turmeric for immunity.",
                    "why":         "Calcium and protein combination for bone and muscle health"
                }
            ]
        },
        {
            "meal_name":          "Mid Morning Snack",
            "time":               "11:00 AM",
            "meal_type":          "snack",
            "total_calories":     int(calories * 0.10),
            "total_protein_g":    round(macros['protein_g'] * 0.10, 1),
            "total_carbs_g":      round(macros['carbs_g'] * 0.10, 1),
            "total_fat_g":        round(macros['fat_g'] * 0.10, 1),
            "estimated_cost_inr": int(budget_per_meal * 0.5),
            "champion_note":      "Never let 4 hours pass without eating",
            "why_this_meal":      "Prevent energy crash. Keep protein synthesis active.",
            "preparation_time":   "5 minutes",
            "preparation_tip":    "Keep fruits and curd ready in fridge for quick access",
            "foods": [
                {
                    "name":        "Greek yogurt or thick curd",
                    "quantity_g":  200,
                    "quantity_ml": None,
                    "calories":    120,
                    "protein_g":   12.0,
                    "carbs_g":     8.0,
                    "fat_g":       3.0,
                    "cost_inr":    20,
                    "preparation": "Plain curd. No sugar. Can add pinch of jeera.",
                    "why":         "Probiotics for gut health and steady protein intake"
                },
                {
                    "name":        "Banana",
                    "quantity_g":  120,
                    "quantity_ml": None,
                    "calories":    110,
                    "protein_g":   1.5,
                    "carbs_g":     28.0,
                    "fat_g":       0.0,
                    "cost_inr":    10,
                    "preparation": "Eat as is. Perfect portable snack.",
                    "why":         "Natural sugar for energy. Potassium for muscle function."
                }
            ]
        },
        {
            "meal_name":          "Lunch",
            "time":               "1:00 PM",
            "meal_type":          "lunch",
            "total_calories":     int(calories * 0.30),
            "total_protein_g":    round(macros['protein_g'] * 0.30, 1),
            "total_carbs_g":      round(macros['carbs_g'] * 0.30, 1),
            "total_fat_g":        round(macros['fat_g'] * 0.25, 1),
            "estimated_cost_inr": int(budget_per_meal * 1.5),
            "champion_note":      "Neeraj Chopra fuels his power with a proper lunch",
            "why_this_meal":      "Biggest meal. Fuel for afternoon training and recovery.",
            "preparation_time":   "25 minutes",
            "preparation_tip":    "Cook rice and dal in bulk. Grill chicken fresh daily.",
            "foods": [
                {
                    "name":        "Chicken breast grilled",
                    "quantity_g":  200,
                    "quantity_ml": None,
                    "calories":    330,
                    "protein_g":   62.0,
                    "carbs_g":     0.0,
                    "fat_g":       7.0,
                    "cost_inr":    60,
                    "preparation": "Marinate with turmeric salt jeera. Grill 15 min.",
                    "why":         "Lean complete protein. Best muscle building food."
                },
                {
                    "name":        "Brown rice cooked",
                    "quantity_g":  150,
                    "quantity_ml": None,
                    "calories":    195,
                    "protein_g":   4.0,
                    "carbs_g":     43.0,
                    "fat_g":       1.5,
                    "cost_inr":    15,
                    "preparation": "Cook with 1:2 water ratio. Add pinch of salt.",
                    "why":         "Complex carbs for sustained energy and fiber"
                },
                {
                    "name":        "Dal tadka cooked",
                    "quantity_g":  150,
                    "quantity_ml": None,
                    "calories":    180,
                    "protein_g":   12.0,
                    "carbs_g":     28.0,
                    "fat_g":       3.5,
                    "cost_inr":    20,
                    "preparation": "Cook masoor dal with tomato onion jeera turmeric.",
                    "why":         "Plant protein and iron combination"
                },
                {
                    "name":        "Mixed salad",
                    "quantity_g":  100,
                    "quantity_ml": None,
                    "calories":    35,
                    "protein_g":   1.5,
                    "carbs_g":     7.0,
                    "fat_g":       0.0,
                    "cost_inr":    15,
                    "preparation": "Cucumber tomato onion lemon salt. Fresh only.",
                    "why":         "Fiber vitamins minerals for micronutrient needs"
                }
            ]
        },
        {
            "meal_name":          "Pre Workout Snack",
            "time":               "4:30 PM",
            "meal_type":          "pre_workout",
            "total_calories":     int(calories * 0.15),
            "total_protein_g":    round(macros['protein_g'] * 0.12, 1),
            "total_carbs_g":      round(macros['carbs_g'] * 0.20, 1),
            "total_fat_g":        round(macros['fat_g'] * 0.10, 1),
            "estimated_cost_inr": int(budget_per_meal * 0.7),
            "champion_note":      "Fuel before training like a professional athlete",
            "why_this_meal":      "Pre workout energy. Carbs for performance. Light protein.",
            "preparation_time":   "5 minutes",
            "preparation_tip":    "Eat exactly 30-45 minutes before workout for best results",
            "foods": [
                {
                    "name":        "Banana large",
                    "quantity_g":  130,
                    "quantity_ml": None,
                    "calories":    120,
                    "protein_g":   1.5,
                    "carbs_g":     31.0,
                    "fat_g":       0.0,
                    "cost_inr":    10,
                    "preparation": "Eat as is. Nature's best pre workout food.",
                    "why":         "Fast carbs for immediate energy during workout"
                },
                {
                    "name":        "Boiled eggs",
                    "quantity_g":  100,
                    "quantity_ml": None,
                    "calories":    140,
                    "protein_g":   12.0,
                    "carbs_g":     1.0,
                    "fat_g":       9.5,
                    "cost_inr":    20,
                    "preparation": "2 eggs boiled. Add salt pepper.",
                    "why":         "Light protein to prevent muscle breakdown during workout"
                }
            ]
        },
        {
            "meal_name":          "Dinner",
            "time":               "7:30 PM",
            "meal_type":          "dinner",
            "total_calories":     int(calories * 0.20),
            "total_protein_g":    round(macros['protein_g'] * 0.20, 1),
            "total_carbs_g":      round(macros['carbs_g'] * 0.10, 1),
            "total_fat_g":        round(macros['fat_g'] * 0.25, 1),
            "estimated_cost_inr": int(budget_per_meal),
            "champion_note":      "Light dinner is the secret of every lean champion",
            "why_this_meal":      "High protein light carb dinner for overnight muscle repair.",
            "preparation_time":   "20 minutes",
            "preparation_tip":    "Finish dinner by 8pm. Never eat heavy at night.",
            "foods": [
                {
                    "name":        "Fish rohu or pomfret",
                    "quantity_g":  200,
                    "quantity_ml": None,
                    "calories":    220,
                    "protein_g":   40.0,
                    "carbs_g":     0.0,
                    "fat_g":       8.0,
                    "cost_inr":    60,
                    "preparation": "Steam or grill with turmeric salt lemon. Avoid frying.",
                    "why":         "Omega 3 rich lean protein perfect for overnight recovery"
                },
                {
                    "name":        "Roti whole wheat",
                    "quantity_g":  60,
                    "quantity_ml": None,
                    "calories":    160,
                    "protein_g":   5.0,
                    "carbs_g":     33.0,
                    "fat_g":       2.0,
                    "cost_inr":    10,
                    "preparation": "2 rotis. Make fresh. Use minimal ghee.",
                    "why":         "Complex carbs for energy without fat storage at night"
                },
                {
                    "name":        "Sabzi mixed vegetables",
                    "quantity_g":  150,
                    "quantity_ml": None,
                    "calories":    80,
                    "protein_g":   3.0,
                    "carbs_g":     15.0,
                    "fat_g":       2.0,
                    "cost_inr":    20,
                    "preparation": "Stir fry with minimal oil. Add spices generously.",
                    "why":         "Fiber and micronutrients for complete nutrition"
                }
            ]
        }
    ]

    # ── Veg Meals ─────────────────────────────────────────────────────────────
    veg_meals = [
        {
            "meal_name":          "Early Morning",
            "time":               "6:30 AM",
            "meal_type":          "early_morning",
            "total_calories":     100,
            "total_protein_g":    3.0,
            "total_carbs_g":      8.0,
            "total_fat_g":        6.0,
            "estimated_cost_inr": 15,
            "champion_note":      "Every champion starts the day right",
            "why_this_meal":      "Kickstart metabolism after overnight fast",
            "preparation_time":   "2 minutes",
            "preparation_tip":    "Soak almonds and walnuts overnight",
            "foods": [
                {
                    "name":        "Warm water with lemon",
                    "quantity_g":  None,
                    "quantity_ml": 300,
                    "calories":    10,
                    "protein_g":   0.0,
                    "carbs_g":     3.0,
                    "fat_g":       0.0,
                    "cost_inr":    5,
                    "preparation": "Squeeze half lemon in warm water",
                    "why":         "Alkalizes body and kickstarts digestion"
                },
                {
                    "name":        "Soaked almonds and walnuts",
                    "quantity_g":  20,
                    "quantity_ml": None,
                    "calories":    130,
                    "protein_g":   4.0,
                    "carbs_g":     5.0,
                    "fat_g":       12.0,
                    "cost_inr":    15,
                    "preparation": "Soak overnight. Peel almonds. Eat walnuts as is.",
                    "why":         "Healthy omega 3 fats and plant protein to start day"
                }
            ]
        },
        {
            "meal_name":          "Breakfast",
            "time":               "8:00 AM",
            "meal_type":          "breakfast",
            "total_calories":     int(calories * 0.25),
            "total_protein_g":    round(macros['protein_g'] * 0.25, 1),
            "total_carbs_g":      round(macros['carbs_g'] * 0.25, 1),
            "total_fat_g":        round(macros['fat_g'] * 0.20, 1),
            "estimated_cost_inr": int(budget_per_meal),
            "champion_note":      "High protein breakfast is non negotiable for champions",
            "why_this_meal":      "Start protein synthesis early. Fuel for the morning.",
            "preparation_time":   "15 minutes",
            "preparation_tip":    "Make poha or upma fresh. Keep sprouts soaked overnight.",
            "foods": [
                {
                    "name":        "Paneer bhurji",
                    "quantity_g":  100,
                    "quantity_ml": None,
                    "calories":    265,
                    "protein_g":   18.0,
                    "carbs_g":     3.0,
                    "fat_g":       20.0,
                    "cost_inr":    35,
                    "preparation": "Crumble paneer. Cook with onion tomato spices.",
                    "why":         "Highest protein vegetarian option for breakfast"
                },
                {
                    "name":        "Oats cooked",
                    "quantity_g":  80,
                    "quantity_ml": None,
                    "calories":    300,
                    "protein_g":   10.0,
                    "carbs_g":     54.0,
                    "fat_g":       5.0,
                    "cost_inr":    15,
                    "preparation": "Cook in 200ml milk. Add banana.",
                    "why":         "Complex carbs for sustained morning energy"
                },
                {
                    "name":        "Milk",
                    "quantity_g":  None,
                    "quantity_ml": 200,
                    "calories":    130,
                    "protein_g":   6.5,
                    "carbs_g":     9.5,
                    "fat_g":       7.5,
                    "cost_inr":    20,
                    "preparation": "Warm milk with turmeric optional",
                    "why":         "Calcium and complete protein combination"
                }
            ]
        },
        {
            "meal_name":          "Mid Morning Snack",
            "time":               "11:00 AM",
            "meal_type":          "snack",
            "total_calories":     int(calories * 0.10),
            "total_protein_g":    round(macros['protein_g'] * 0.10, 1),
            "total_carbs_g":      round(macros['carbs_g'] * 0.10, 1),
            "total_fat_g":        round(macros['fat_g'] * 0.10, 1),
            "estimated_cost_inr": int(budget_per_meal * 0.5),
            "champion_note":      "Consistent small meals is the champion secret",
            "why_this_meal":      "Keep protein intake steady throughout day",
            "preparation_time":   "5 minutes",
            "preparation_tip":    "Keep sprouted moong and curd ready in fridge",
            "foods": [
                {
                    "name":        "Sprouted moong",
                    "quantity_g":  100,
                    "quantity_ml": None,
                    "calories":    105,
                    "protein_g":   9.0,
                    "carbs_g":     19.0,
                    "fat_g":       0.5,
                    "cost_inr":    10,
                    "preparation": "Soak moong overnight. Sprout 12 hours. Add lemon salt.",
                    "why":         "Highest bioavailable plant protein. Cheap and powerful."
                },
                {
                    "name":        "Curd",
                    "quantity_g":  150,
                    "quantity_ml": None,
                    "calories":    90,
                    "protein_g":   8.0,
                    "carbs_g":     7.0,
                    "fat_g":       2.5,
                    "cost_inr":    15,
                    "preparation": "Plain curd. No sugar. Add jeera powder.",
                    "why":         "Probiotics for gut health and steady protein"
                }
            ]
        },
        {
            "meal_name":          "Lunch",
            "time":               "1:00 PM",
            "meal_type":          "lunch",
            "total_calories":     int(calories * 0.30),
            "total_protein_g":    round(macros['protein_g'] * 0.28, 1),
            "total_carbs_g":      round(macros['carbs_g'] * 0.30, 1),
            "total_fat_g":        round(macros['fat_g'] * 0.25, 1),
            "estimated_cost_inr": int(budget_per_meal * 1.5),
            "champion_note":      "Fuel the body like an Olympic athlete",
            "why_this_meal":      "Complete nutrition for muscle building and energy",
            "preparation_time":   "25 minutes",
            "preparation_tip":    "Cook dal and rice in bulk. Make sabzi fresh.",
            "foods": [
                {
                    "name":        "Paneer",
                    "quantity_g":  150,
                    "quantity_ml": None,
                    "calories":    400,
                    "protein_g":   27.0,
                    "carbs_g":     4.5,
                    "fat_g":       30.0,
                    "cost_inr":    50,
                    "preparation": "Grill or add to sabzi. Minimal oil cooking.",
                    "why":         "Best complete protein for vegetarians"
                },
                {
                    "name":        "Brown rice cooked",
                    "quantity_g":  150,
                    "quantity_ml": None,
                    "calories":    195,
                    "protein_g":   4.0,
                    "carbs_g":     43.0,
                    "fat_g":       1.5,
                    "cost_inr":    15,
                    "preparation": "Cook with 1:2 water ratio.",
                    "why":         "Complex carbs and fiber for sustained energy"
                },
                {
                    "name":        "Dal masoor cooked",
                    "quantity_g":  150,
                    "quantity_ml": None,
                    "calories":    180,
                    "protein_g":   12.0,
                    "carbs_g":     28.0,
                    "fat_g":       3.5,
                    "cost_inr":    15,
                    "preparation": "Cook with tomato onion turmeric jeera.",
                    "why":         "Plant protein and iron for energy"
                },
                {
                    "name":        "Mixed salad",
                    "quantity_g":  100,
                    "quantity_ml": None,
                    "calories":    35,
                    "protein_g":   1.5,
                    "carbs_g":     7.0,
                    "fat_g":       0.0,
                    "cost_inr":    10,
                    "preparation": "Fresh cucumber tomato onion lemon.",
                    "why":         "Fiber vitamins minerals for complete nutrition"
                }
            ]
        },
        {
            "meal_name":          "Pre Workout Snack",
            "time":               "4:30 PM",
            "meal_type":          "pre_workout",
            "total_calories":     int(calories * 0.15),
            "total_protein_g":    round(macros['protein_g'] * 0.12, 1),
            "total_carbs_g":      round(macros['carbs_g'] * 0.20, 1),
            "total_fat_g":        round(macros['fat_g'] * 0.10, 1),
            "estimated_cost_inr": int(budget_per_meal * 0.7),
            "champion_note":      "Fuel before training like a professional",
            "why_this_meal":      "Pre workout energy from natural sources",
            "preparation_time":   "5 minutes",
            "preparation_tip":    "Eat 30-45 minutes before training for best energy",
            "foods": [
                {
                    "name":        "Banana",
                    "quantity_g":  130,
                    "quantity_ml": None,
                    "calories":    120,
                    "protein_g":   1.5,
                    "carbs_g":     31.0,
                    "fat_g":       0.0,
                    "cost_inr":    10,
                    "preparation": "Eat as is. Nature's best pre workout food.",
                    "why":         "Fast carbs for immediate workout energy"
                },
                {
                    "name":        "Peanut butter",
                    "quantity_g":  30,
                    "quantity_ml": None,
                    "calories":    180,
                    "protein_g":   8.0,
                    "carbs_g":     6.0,
                    "fat_g":       15.0,
                    "cost_inr":    15,
                    "preparation": "Eat with banana or on roti.",
                    "why":         "Plant protein and healthy fats for sustained energy"
                }
            ]
        },
        {
            "meal_name":          "Dinner",
            "time":               "7:30 PM",
            "meal_type":          "dinner",
            "total_calories":     int(calories * 0.20),
            "total_protein_g":    round(macros['protein_g'] * 0.20, 1),
            "total_carbs_g":      round(macros['carbs_g'] * 0.10, 1),
            "total_fat_g":        round(macros['fat_g'] * 0.25, 1),
            "estimated_cost_inr": int(budget_per_meal),
            "champion_note":      "Light protein dinner is the champion recovery secret",
            "why_this_meal":      "High protein light dinner for overnight muscle repair",
            "preparation_time":   "20 minutes",
            "preparation_tip":    "Finish dinner by 8pm. Keep it light.",
            "foods": [
                {
                    "name":        "Tofu or paneer",
                    "quantity_g":  150,
                    "quantity_ml": None,
                    "calories":    200,
                    "protein_g":   20.0,
                    "carbs_g":     4.0,
                    "fat_g":       12.0,
                    "cost_inr":    40,
                    "preparation": "Grill or stir fry with minimal oil and spices.",
                    "why":         "Complete protein for overnight muscle recovery"
                },
                {
                    "name":        "Roti whole wheat",
                    "quantity_g":  60,
                    "quantity_ml": None,
                    "calories":    160,
                    "protein_g":   5.0,
                    "carbs_g":     33.0,
                    "fat_g":       2.0,
                    "cost_inr":    10,
                    "preparation": "2 fresh rotis. Minimal ghee.",
                    "why":         "Complex carbs without excess calories"
                },
                {
                    "name":        "Mixed vegetable sabzi",
                    "quantity_g":  150,
                    "quantity_ml": None,
                    "calories":    80,
                    "protein_g":   3.0,
                    "carbs_g":     15.0,
                    "fat_g":       2.0,
                    "cost_inr":    20,
                    "preparation": "Stir fry seasonal vegetables minimal oil.",
                    "why":         "Fiber and micronutrients for complete nutrition"
                }
            ]
        }
    ]

    # ── Select meals based on preference ─────────────────────────────────────
    if food_preference in ["veg", "vegan", "eggetarian"]:
        meals = veg_meals
    else:
        meals = non_veg_meals

    # ── Calculate totals ──────────────────────────────────────────────────────
    total_cal  = sum(m["total_calories"]  for m in meals)
    total_prot = sum(m["total_protein_g"] for m in meals)
    total_carb = sum(m["total_carbs_g"]   for m in meals)
    total_fat  = sum(m["total_fat_g"]     for m in meals)
    total_cost = sum(m["estimated_cost_inr"] for m in meals)

    return {
        "goal":                goal,
        "champion_reference":  "Indian Olympic Champions",
        "champion_quote":      "Real food eaten consistently beats any supplement stack.",
        "diet_level":          "basic",
        "food_style":          "indian",
        "food_preference":     food_preference,
        "daily_calories":      calories,
        "daily_protein_g":     macros['protein_g'],
        "daily_carbs_g":       macros['carbs_g'],
        "daily_fat_g":         macros['fat_g'],
        "water_intake_ml":     water['total_ml'],
        "water_intake_litres": water['total_litres'],
        "water_glasses":       water['glasses'],
        "daily_budget_inr":    daily_budget,
        "weekly_budget_inr":   daily_budget * 7,
        "generated_by":        "fallback",
        "motivation_message":  (
            f"Every champion started exactly where you are {name}. "
            f"This plan is your foundation. "
            f"Follow it consistently and results will come. 💪"
        ),
        "meals": meals,
        "daily_totals": {
            "total_calories":  total_cal,
            "total_protein_g": round(total_prot, 1),
            "total_carbs_g":   round(total_carb, 1),
            "total_fat_g":     round(total_fat, 1),
            "total_cost_inr":  total_cost
        },
        "foods_to_eat": [
            "Dal chawal roti — Indian staples are champion foods",
            "Chicken breast eggs fish paneer — protein every meal",
            "Seasonal vegetables — cheap and nutrient dense",
            "Curd milk — calcium and protein combination",
            "Almonds walnuts — healthy fats and omega 3",
            "Banana apple orange — natural energy sources",
            "Brown rice oats sweet potato — complex carbs only"
        ],
        "foods_to_avoid": [
            "Fried foods — samosa pakora chips bhajiya",
            "Sugary drinks — cold drinks juice sweetened tea",
            "Processed foods — biscuits instant noodles maggi",
            "White bread maida — spike blood sugar crash energy",
            "Late night heavy meals — disrupts recovery and sleep",
            "Alcohol — destroys muscle recovery and sleep quality"
        ],
        "champion_foods": [
            "Eggs — cheapest most complete protein available",
            "Dal — cheapest plant protein power food",
            "Banana — best natural pre workout food",
            "Curd — best probiotic and protein combination",
            "Sweet potato — complex carbs with vitamins"
        ],
        "grocery_list": [
            "Eggs 1 dozen",
            "Chicken breast 500g",
            "Brown rice 1kg",
            "Dal masoor 500g",
            "Oats 500g",
            "Paneer 200g",
            "Seasonal vegetables 1kg",
            "Almonds 100g",
            "Bananas 6 pieces",
            "Milk 1 litre",
            "Curd 500g",
            "Lemons 4 pieces"
        ],
        "meal_prep_tips": [
            "Sunday batch cooking saves the entire week",
            "Cook rice and dal in large quantity — store 3 days",
            "Grill chicken in batch — refrigerate up to 3 days",
            "Soak almonds every night — takes 30 seconds",
            "Boil 6 eggs at once — ready for 3 days",
            "Chop all vegetables Sunday — store in containers"
        ],
        "budget_tips": [
            "Buy from local sabzi mandi not supermarket — 40% cheaper",
            "Eggs are cheapest protein source — 6 rupees per egg",
            "Buy dal in 1kg bag not 200g pack — much cheaper",
            "Seasonal vegetables always cheaper and fresher",
            "Buy chicken from local butcher not supermarket",
            "Oats from local kirana store cheaper than branded"
        ],
        "pro_tips": [
            "Eat every 3-4 hours — consistency beats perfection",
            "Protein at every single meal is non negotiable",
            "Drink one full glass water before every meal",
            "Prepare meals in advance like a professional athlete",
            "Sleep 7-8 hours — 80% of recovery happens during sleep",
            "Track your meals for first 2 weeks to build awareness"
        ],
        "note": "Fallback plan — AI temporarily unavailable"
    }