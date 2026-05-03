def apply_rules(data: dict) -> dict:

    rules_applied  = []
    warnings       = []

    # ── Fix unrealistic target days ───────────────────────────────────────────
    weight         = data.get("weight", 70)
    target_weight  = data.get("target_weight", weight)
    target_days    = data.get("target_days", 90)
    goal           = data.get("goal", "strength")

    if goal == "fat_loss" and target_weight and target_days:
        weight_to_lose = weight - target_weight
        if weight_to_lose > 0:
            # Safe fat loss = max 0.5kg per week = 2kg per month
            realistic_days = int((weight_to_lose / 0.5) * 7)
            if target_days < realistic_days:
                warnings.append(
                    f"Target {weight_to_lose}kg loss in {target_days} days "
                    f"is not safe. Realistic timeline: {realistic_days} days "
                    f"({weight_to_lose / (realistic_days/30):.1f}kg/month). "
                    f"Adjusted plan accordingly."
                )
                data["target_days"]    = realistic_days
                data["monthly_target"] = 2.0  # max 2kg per month safely

    # ── Fix height if in inches ───────────────────────────────────────────────
    height = data.get("height", 170)
    if height < 100:
        # Likely in inches — convert to cm
        height_cm = round(height * 2.54)
        warnings.append(
            f"Height {height} appears to be in inches. "
            f"Converted to {height_cm}cm."
        )
        data["height"] = height_cm

    # ── Fix sleep hours ───────────────────────────────────────────────────────
    sleep = data.get("sleep_hours", 7)
    if sleep < 5:
        warnings.append(
            f"Sleep {sleep} hours is critically low. "
            f"Fat loss is nearly impossible with under 5 hours sleep. "
            f"Cortisol spikes, hunger increases, muscle loss occurs. "
            f"Sleep fix is priority #1 before any workout plan."
        )
        data["sleep_warning"] = True

    # ── Fix conflicting experience levels ─────────────────────────────────────
    body_exp  = data.get("body_workout_experience", "")
    goal_exp  = data.get("workout_experience", "beginner")
    if body_exp and body_exp != goal_exp:
        warnings.append(
            f"Experience level conflict detected. "
            f"Using beginner for safety."
        )
        data["workout_experience"] = "beginner"

    data["warnings"] = warnings

    # ── Helper — convert list or string to lowercase string ──────────────────
    def to_str(value) -> str:
        if not value:
            return "none"
        if isinstance(value, list):
            return " ".join(str(v) for v in value).lower()
        return str(value).lower()

    # Rule 1 — Beginner gets max 4 days
    if data["workout_experience"] == "beginner" and data["workout_days_per_week"] > 4:
        data["workout_days_per_week"] = 4
        rules_applied.append("Capped workout days to 4 for beginner")

    # Rule 2 — Equipment based on gym access
    if not data["gym_access"]:
        data["equipment"] = "bodyweight only — no gym equipment"
        rules_applied.append("Home workout — bodyweight only")
    else:
        data["equipment"] = "full gym equipment available"

    # Rules 3 4 5 — Injury handling
    avoid_list    = []
    injuries_str  = to_str(data.get("injuries"))

    if injuries_str and injuries_str != "none":

        if "knee" in injuries_str:
            avoid_list.extend([
                "squats", "lunges", "leg press",
                "jumping", "jump", "box jump",
                "running", "burpees"
            ])
            rules_applied.append("Avoiding knee exercises")

        if "back" in injuries_str:
            avoid_list.extend([
                "deadlifts", "bent over rows",
                "good mornings", "sit ups"
            ])
            rules_applied.append("Avoiding back exercises")

        if "shoulder" in injuries_str:
            avoid_list.extend([
                "overhead press", "upright rows",
                "behind neck press"
            ])
            rules_applied.append("Avoiding shoulder exercises")

    data["avoid_exercises"] = ", ".join(avoid_list) if avoid_list else "none"

    # Rule 6 — High stress
    if to_str(data.get("stress_level")) == "high":
        data["add_recommendation"] = "Include 10 min yoga or meditation after every session"
        rules_applied.append("High stress — added yoga")
    else:
        data["add_recommendation"] = "none"

    # Rule 7 — BMI logic
    if data.get("bmi") and data["bmi"] > 30:
        data["cardio_note"] = "Add 20 min cardio after every session — treadmill or cycling"
        rules_applied.append("BMI over 30 — added cardio")
    elif data.get("bmi") and data["bmi"] < 18:
        data["cardio_note"] = "Minimize cardio — focus on strength and calorie surplus"
        rules_applied.append("BMI under 18 — minimize cardio")
    else:
        data["cardio_note"] = "none"

    # Rule 8 — Low sleep
    if data.get("sleep_hours") and data["sleep_hours"] < 6:
        data["recovery_note"] = "Low sleep detected — add extra rest day and avoid overtraining"
        rules_applied.append("Low sleep — extra rest day recommended")
    else:
        data["recovery_note"] = "none"

    # Rule 9 — Senior user
    if data.get("age") and data["age"] > 50:
        senior_avoid = ["heavy deadlifts", "box jumps", "heavy barbell squats"]
        existing     = data.get("avoid_exercises", "none")
        if existing == "none":
            data["avoid_exercises"] = ", ".join(senior_avoid)
        else:
            data["avoid_exercises"] = existing + ", " + ", ".join(senior_avoid)
        rules_applied.append("Senior user — reduced high impact exercises")

    # Rule 10 — Diabetes
    health_str = to_str(data.get("health_conditions") or data.get("health_problems"))
    if health_str and health_str != "none" and "diabetes" in health_str:
        if data["add_recommendation"] == "none":
            data["add_recommendation"] = "Monitor blood sugar before and after workout."
        else:
            data["add_recommendation"] += " Monitor blood sugar before and after workout."
        rules_applied.append("Diabetes — added blood sugar monitoring note")

    # Rule 11 — Low water intake
    if data.get("water_intake_liters"):
        water = data["water_intake_liters"]
    else:
        water = data.get("water_intake", 0)

    if water and water < 1.5:
        if data["add_recommendation"] == "none":
            data["add_recommendation"] = "Increase water intake to at least 2 litres per day."
        else:
            data["add_recommendation"] += " Increase water intake to at least 2 litres per day."
        rules_applied.append("Low water intake — hydration note added")
        
        
    # Rule 12 — Smoker
    if data.get("smoker") == True:

        # Adjust cardio note
        if data["cardio_note"] == "none":
            data["cardio_note"] = (
                "Start with light cardio only — "
                "10 min walking or cycling. "
                "Gradually increase as lung capacity improves. "
                "No HIIT or heavy cardio initially."
            )
        else:
            data["cardio_note"] += (
                " Since you smoke — keep cardio light. "
                "No HIIT. Focus on breathing."
            )

        # Adjust recommendation
        if data["add_recommendation"] == "none":
            data["add_recommendation"] = (
                "Smoker health tips: "
                "1. Do deep breathing exercises after every workout. "
                "2. Include Vitamin C rich foods daily. "
                "3. Drink 3+ litres of water to flush toxins. "
                "4. Avoid smoking before and after workout. "
                "5. Each workout session will improve your lung capacity."
            )
        else:
            data["add_recommendation"] += (
                " Smoker health tips: "
                "Deep breathing after workout. "
                "Vitamin C daily. "
                "3+ litres water. "
                "Avoid smoking around workout time."
            )

    rules_applied.append("Smoker — adjusted cardio + health recommendations")

    data["rules_applied"] = rules_applied
    return data