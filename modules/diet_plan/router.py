from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from database import get_db
from models import (
    User, UserBodyMetrics, UserFitnessGoals,
    UserLifestyle, UserHealth
)
from auth import verify_access_token
from modules.diet_plan.models   import DietPlan, DietPreference
from modules.diet_plan.schemas  import (
    DietPreferenceRequest,
    EditFoodRequest,
    EditMealRequest
)
from modules.diet_plan.generator import generate_diet_plan
from modules.diet_plan.editor    import edit_single_food, edit_entire_meal

router = APIRouter()


# ── Auth Helper ───────────────────────────────────────────────────────────────

def get_diet_user(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        auth = request.headers.get("Authorization")
        if auth and auth.startswith("Bearer "):
            token = auth.split(" ")[1]
    if not token:
        raise HTTPException(401, "Not authenticated")
    payload = verify_access_token(token)
    if not payload:
        raise HTTPException(401, "Invalid token")
    user = db.query(User).filter(
        User.id == payload["user_id"]
    ).first()
    if not user:
        raise HTTPException(404, "User not found")
    return user


# ── Step 1 — Save Diet Preferences ───────────────────────────────────────────

@router.post("/preferences")
def save_diet_preferences(
    request: Request,
    payload: DietPreferenceRequest,
    db: Session = Depends(get_db)
):
    """
    STEP 1 — MANDATORY before generating diet.
    User fills diet preferences and budget.
    Without this step diet cannot be generated.
    """
    user = get_diet_user(request, db)

    meal_timings = None
    if payload.meal_timings:
        meal_timings = [mt.dict() for mt in payload.meal_timings]

    existing = db.query(DietPreference).filter(
        DietPreference.user_id == user.id
    ).first()

    if existing:
        existing.daily_budget    = payload.daily_budget
        existing.weekly_budget   = payload.weekly_budget
        existing.food_style      = payload.food_style
        existing.meals_per_day   = payload.meals_per_day
        existing.allergies       = payload.allergies
        existing.disliked_foods  = payload.disliked_foods
        existing.favourite_foods = payload.favourite_foods
        existing.cooking_time    = payload.cooking_time
        existing.meal_timings    = meal_timings
        db.commit()
        db.refresh(existing)
        message = "Diet preferences updated ✅"
    else:
        new_pref = DietPreference(
            user_id         = user.id,
            daily_budget    = payload.daily_budget,
            weekly_budget   = payload.weekly_budget,
            food_style      = payload.food_style,
            meals_per_day   = payload.meals_per_day,
            allergies       = payload.allergies,
            disliked_foods  = payload.disliked_foods,
            favourite_foods = payload.favourite_foods,
            cooking_time    = payload.cooking_time,
            meal_timings    = meal_timings
        )
        db.add(new_pref)
        db.commit()
        db.refresh(new_pref)
        message = "Diet preferences saved ✅"

    return {
        "message":       message,
        "next_step":     "POST /diet/generate",
        "daily_budget":  payload.daily_budget,
        "weekly_budget": payload.weekly_budget,
        "meals_per_day": payload.meals_per_day,
        "food_style":    payload.food_style,
        "cooking_time":  payload.cooking_time
    }


# ── Get Diet Preferences ──────────────────────────────────────────────────────

@router.get("/preferences")
def get_diet_preferences(
    request: Request,
    db: Session = Depends(get_db)
):
    """Get saved diet preferences."""
    user = get_diet_user(request, db)

    pref = db.query(DietPreference).filter(
        DietPreference.user_id == user.id
    ).first()

    if not pref:
        raise HTTPException(
            404,
            "No preferences found. "
            "Please set preferences first → POST /diet/preferences"
        )

    return {
        "daily_budget":    pref.daily_budget,
        "weekly_budget":   pref.weekly_budget,
        "food_style":      pref.food_style,
        "meals_per_day":   pref.meals_per_day,
        "allergies":       pref.allergies,
        "disliked_foods":  pref.disliked_foods,
        "favourite_foods": pref.favourite_foods,
        "cooking_time":    pref.cooking_time,
        "meal_timings":    pref.meal_timings,
        "updated_at":      pref.updated_at
    }


# ── Step 2 — Generate Diet Plan ───────────────────────────────────────────────

@router.post("/generate")
def generate_diet(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    STEP 2 — Generate champion diet plan.
    Preferences MUST be saved first.
    Based on profile + preferences + budget.
    """
    user = get_diet_user(request, db)

    # Check preferences exist
    pref = db.query(DietPreference).filter(
        DietPreference.user_id == user.id
    ).first()

    if not pref:
        raise HTTPException(
            400,
            "Please set diet preferences first → POST /diet/preferences"
        )

    # ── Fetch full profile ────────────────────────────────────────────────────
    m = db.query(UserBodyMetrics).filter(
        UserBodyMetrics.user_id == user.id
    ).first()
    g = db.query(UserFitnessGoals).filter(
        UserFitnessGoals.user_id == user.id
    ).first()
    l = db.query(UserLifestyle).filter(
        UserLifestyle.user_id == user.id
    ).first()
    h = db.query(UserHealth).filter(
        UserHealth.user_id == user.id
    ).first()

    # ── Extract values first before using them ────────────────────────────────
    b_weight = m.weight if m else 70
    b_height = m.height if m else 170
    b_age    = m.age    if m else 25
    g_goal   = g.goal   if g else "strength"
    g_target = g.target_weight if g else b_weight
    g_days   = g.target_days   if g else 90
    l_sleep  = l.sleep_hours   if l else 7

    # ── Build profile dict ────────────────────────────────────────────────────
    profile = {
        "user": {
            "name": user.name
        },
        "body_metrics": {
            "age":    b_age,
            "gender": m.gender if m else "male",
            "height": b_height,
            "weight": b_weight,
            "bmi":    m.bmi    if m else 24
        },
        "fitness_goals": {
            "goal":                   g_goal,
            "workout_experience":     g.workout_experience     if g else "beginner",
            "preferred_workout_time": g.preferred_workout_time if g else "morning",
            "target_weight":          g_target,
            "target_days":            g_days,
            "gym_access":             g.gym_access             if g else True
        },
        "lifestyle": {
            "food_preference": l.food_preference if l else "non-veg",
            "activity_level":  l.activity_level  if l else "moderate",
            "sleep_hours":     l_sleep,
            "smoker":          l.smoker           if l else False,
            "stress_level":    l.stress_level     if l else "low"
        },
        "health": {
            "health_problems": h.health_problems if h else "none",
            "injuries":        h.injuries        if h else "none"
        }
    }

    preferences = {
        "daily_budget":    pref.daily_budget,
        "weekly_budget":   pref.weekly_budget,
        "food_style":      pref.food_style,
        "meals_per_day":   pref.meals_per_day,
        "allergies":       pref.allergies,
        "disliked_foods":  pref.disliked_foods,
        "favourite_foods": pref.favourite_foods,
        "cooking_time":    pref.cooking_time,
        "meal_timings":    pref.meal_timings
    }

    # ── Run validation before generating ─────────────────────────────────────
    from modules.diet_plan.calculator import validate_and_fix_profile

    validation = validate_and_fix_profile(
        weight        = b_weight,
        height        = b_height,
        age           = b_age,
        target_weight = g_target,
        target_days   = g_days,
        sleep_hours   = l_sleep,
        goal          = g_goal,
        stress_level  = l.stress_level if l else "low",
        injuries      = h.injuries     if h else "none",
        gym_access    = g.gym_access   if g else True
    )

    # ── Generate plan ─────────────────────────────────────────────────────────
    plan = generate_diet_plan(profile, preferences)

    # ── Add warnings to plan ──────────────────────────────────────────────────
    if validation["warnings"]:
        plan["coach_warnings"] = validation["warnings"]
        plan["profile_fixes"]  = validation["fixes"]
        print("⚠️ Coach warnings added to plan")

    # Add profile warnings to plan
    from modules.diet_plan.calculator import validate_and_fix_profile

    l_data = profile.get("lifestyle", {})
    g_data = profile.get("fitness_goals", {})
    b_data = profile.get("body_metrics", {})

    validation = validate_and_fix_profile(
        weight        = b_data.get("weight", 70),
        height        = b_data.get("height", 170),
        age           = b_data.get("age", 25),
        target_weight = g_data.get("target_weight", b_data.get("weight", 70)),
        target_days   = g_data.get("target_days", 90),
        sleep_hours   = l_data.get("sleep_hours", 7),
        goal          = g_data.get("goal", "strength")
    )

    if validation["warnings"]:
        plan["coach_warnings"] = validation["warnings"]
        plan["profile_fixes"]  = validation["fixes"]

    # Save to DB
    existing = db.query(DietPlan).filter(
        DietPlan.user_id == user.id
    ).first()

    if existing:
        existing.goal         = plan.get("goal")
        existing.calories     = plan.get("daily_calories")
        existing.protein_g    = plan.get("daily_protein_g")
        existing.carbs_g      = plan.get("daily_carbs_g")
        existing.fat_g        = plan.get("daily_fat_g")
        existing.diet_level   = plan.get("diet_level", "basic")
        existing.daily_budget = pref.daily_budget
        existing.plan_data    = plan
        existing.generated_by = plan.get("generated_by", "fallback")
        flag_modified(existing, "plan_data")
        db.commit()
        db.refresh(existing)

        return {
            "message":        "Champion diet plan regenerated ✅",
            "generated_by":   existing.generated_by,
            "champion":       plan.get("champion_reference", ""),
            "calories":       existing.calories,
            "protein_g":      existing.protein_g,
            "daily_budget":   existing.daily_budget,
            "diet_level":     existing.diet_level,
            "created_at":     existing.created_at,
            "updated_at":     existing.updated_at,
            "plan":           existing.plan_data
        }

    else:
        new_plan = DietPlan(
            user_id       = user.id,
            goal          = plan.get("goal"),
            calories      = plan.get("daily_calories"),
            protein_g     = plan.get("daily_protein_g"),
            carbs_g       = plan.get("daily_carbs_g"),
            fat_g         = plan.get("daily_fat_g"),
            diet_level    = plan.get("diet_level", "basic"),
            daily_budget  = pref.daily_budget,
            plan_data     = plan,
            generated_by  = plan.get("generated_by", "fallback")
        )
        db.add(new_plan)
        db.commit()
        db.refresh(new_plan)

        return {
            "message":      "Champion diet plan generated ✅",
            "generated_by": new_plan.generated_by,
            "champion":     plan.get("champion_reference", ""),
            "calories":     new_plan.calories,
            "protein_g":    new_plan.protein_g,
            "daily_budget": new_plan.daily_budget,
            "diet_level":   new_plan.diet_level,
            "created_at":   new_plan.created_at,
            "updated_at":   new_plan.updated_at,
            "plan":         new_plan.plan_data
        }


# ── Get Diet Plan ─────────────────────────────────────────────────────────────

@router.get("/plan")
def get_diet_plan(
    request: Request,
    db: Session = Depends(get_db)
):
    """Get current saved diet plan."""
    user = get_diet_user(request, db)

    plan = db.query(DietPlan).filter(
        DietPlan.user_id == user.id
    ).first()

    if not plan:
        raise HTTPException(
            404,
            "No diet plan found. "
            "Please generate one → POST /diet/generate"
        )

    return {
        "message":      "Diet plan fetched ✅",
        "generated_by": plan.generated_by,
        "champion":     plan.plan_data.get("champion_reference", ""),
        "calories":     plan.calories,
        "protein_g":    plan.protein_g,
        "diet_level":   plan.diet_level,
        "daily_budget": plan.daily_budget,
        "created_at":   plan.created_at,
        "updated_at":   plan.updated_at,
        "plan":         plan.plan_data
    }


# ── Edit Single Food ──────────────────────────────────────────────────────────

@router.put("/edit/food")
def edit_food(
    request: Request,
    payload: EditFoodRequest,
    db: Session = Depends(get_db)
):
    """
    Edit single food item in a meal.
    ONLY that food sent to AI.
    Rest of plan stays unchanged.
    DB auto updated instantly.
    """
    user = get_diet_user(request, db)

    plan = db.query(DietPlan).filter(
        DietPlan.user_id == user.id
    ).first()

    if not plan:
        raise HTTPException(
            404,
            "No diet plan found. Generate first → POST /diet/generate"
        )

    pref = db.query(DietPreference).filter(
        DietPreference.user_id == user.id
    ).first()

    l = db.query(UserLifestyle).filter(
        UserLifestyle.user_id == user.id
    ).first()

    try:
        updated_plan = edit_single_food(
            plan_data       = plan.plan_data,
            meal_name       = payload.meal_name,
            food_name       = payload.food_name,
            reason          = payload.reason,
            replace_with    = payload.replace_with,
            goal            = plan.goal or "strength",
            daily_budget    = pref.daily_budget    if pref else 200,
            food_preference = l.food_preference    if l    else "non-veg",
            allergies       = pref.allergies       if pref else None
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Edit failed: {str(e)}")

    # Auto save to DB
    plan.plan_data = updated_plan
    flag_modified(plan, "plan_data")
    db.commit()
    db.refresh(plan)

    return {
        "message":    f"Food updated ✅",
        "edit_info":  plan.plan_data.get("last_edited", ""),
        "updated_at": plan.updated_at,
        "plan":       plan.plan_data
    }


# ── Edit Entire Meal ──────────────────────────────────────────────────────────

@router.put("/edit/meal")
def edit_meal(
    request: Request,
    payload: EditMealRequest,
    db: Session = Depends(get_db)
):
    """
    Edit entire meal.
    ONLY that meal sent to AI.
    All other meals stay unchanged.
    DB auto updated instantly.
    """
    user = get_diet_user(request, db)

    plan = db.query(DietPlan).filter(
        DietPlan.user_id == user.id
    ).first()

    if not plan:
        raise HTTPException(
            404,
            "No diet plan found. Generate first → POST /diet/generate"
        )

    pref = db.query(DietPreference).filter(
        DietPreference.user_id == user.id
    ).first()

    l = db.query(UserLifestyle).filter(
        UserLifestyle.user_id == user.id
    ).first()

    try:
        updated_plan = edit_entire_meal(
            plan_data       = plan.plan_data,
            meal_name       = payload.meal_name,
            reason          = payload.reason,
            goal            = plan.goal or "strength",
            daily_budget    = pref.daily_budget    if pref else 200,
            food_preference = l.food_preference    if l    else "non-veg",
            allergies       = pref.allergies       if pref else None,
            disliked_foods  = pref.disliked_foods  if pref else None,
            new_timing      = payload.new_timing
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Edit failed: {str(e)}")

    # Auto save to DB
    plan.plan_data = updated_plan
    flag_modified(plan, "plan_data")
    db.commit()
    db.refresh(plan)

    return {
        "message":    f"Meal updated ✅",
        "edit_info":  plan.plan_data.get("last_edited", ""),
        "updated_at": plan.updated_at,
        "plan":       plan.plan_data
    }


# ── Delete Diet Plan ──────────────────────────────────────────────────────────

@router.delete("/plan")
def delete_diet_plan(
    request: Request,
    db: Session = Depends(get_db)
):
    """Delete current diet plan."""
    user = get_diet_user(request, db)

    plan = db.query(DietPlan).filter(
        DietPlan.user_id == user.id
    ).first()

    if not plan:
        raise HTTPException(404, "No diet plan found")

    db.delete(plan)
    db.commit()

    return {"message": "Diet plan deleted ✅"}


# ── Get Supplements ───────────────────────────────────────────────────────────

@router.get("/supplements")
def get_supplements_guide(
    request: Request,
    db: Session = Depends(get_db)
):
    """Get supplement recommendations based on goal and level."""
    user = get_diet_user(request, db)

    g = db.query(UserFitnessGoals).filter(
        UserFitnessGoals.user_id == user.id
    ).first()

    goal  = g.goal               if g else "strength"
    level = g.workout_experience if g else "beginner"

    from modules.diet_plan.calculator import get_supplements
    supps = get_supplements(goal, level)

    return {
        "goal":        goal,
        "level":       level,
        "total":       len(supps),
        "supplements": supps,
        "note":        (
            "Start with Whey + Multivitamin + Vitamin D3. "
            "Add others as you progress."
        )
    }


# ── Get Macros ────────────────────────────────────────────────────────────────

@router.get("/macros")
def get_my_macros(
    request: Request,
    db: Session = Depends(get_db)
):
    """Get calculated macro and calorie targets."""
    user = get_diet_user(request, db)

    m = db.query(UserBodyMetrics).filter(
        UserBodyMetrics.user_id == user.id
    ).first()
    g = db.query(UserFitnessGoals).filter(
        UserFitnessGoals.user_id == user.id
    ).first()
    l = db.query(UserLifestyle).filter(
        UserLifestyle.user_id == user.id
    ).first()

    if not m:
        raise HTTPException(
            400,
            "Please complete body metrics first → POST /profile/body"
        )
    if not g:
        raise HTTPException(
            400,
            "Please complete fitness goals first → POST /profile/goals"
        )

    from modules.diet_plan.calculator import (
        calculate_bmr,
        calculate_tdee,
        calculate_target_calories,
        calculate_macros,
        calculate_water_intake
    )

    activity = l.activity_level if l else "moderate"
    bmr      = calculate_bmr(m.weight, m.height, m.age, m.gender)
    tdee     = calculate_tdee(bmr, activity)
    calories = calculate_target_calories(tdee, g.goal)
    macros   = calculate_macros(calories, g.goal, m.weight)
    water    = calculate_water_intake(m.weight, activity)

    return {
        "name":            user.name,
        "goal":            g.goal,
        "bmr":             round(bmr),
        "tdee":            round(tdee),
        "target_calories": calories,
        "macros":          macros,
        "water":           water,
        "explanation": {
            "bmr":      "Calories your body burns at complete rest",
            "tdee":     "Total calories burned per day with your activity",
            "deficit":  "Eating below TDEE causes fat loss",
            "surplus":  "Eating above TDEE causes muscle gain",
            "protein":  f"{macros['protein_g']}g = {round(macros['protein_g'] / m.weight, 1)}g per kg bodyweight"
        }
    }