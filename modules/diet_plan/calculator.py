import re

# ── Injury Configuration Map ──────────────────────────────────────────────────
# Config driven system — scalable and clean
# Each injury group has keywords banned safe exercises and protocol

INJURY_MAP = {
    "shoulder": {
        "keywords": [
            "shoulder", "rotator cuff", "labral",
            "impingement", "ac joint", "clavicle",
            "collarbone", "slap lesion", "shoulder pain",
            "shoulder strain", "shoulder tear"
        ],
        "banned": [
            "overhead press", "upright row",
            "behind neck press", "military press",
            "lateral raise heavy", "bench press heavy",
            "arnold press", "push press"
        ],
        "safe": [
            "leg press", "squats", "deadlifts",
            "core exercises", "face pulls light",
            "resistance bands lower body"
        ],
        "protocol":    "no_overhead",
        "diet_note":   "Include omega 3 and turmeric daily for joint inflammation",
        "warning_msg": (
            "⚠️ SHOULDER INJURY: No overhead press, upright rows, "
            "behind neck press, or heavy bench. "
            "Safe: lower body, core, light resistance bands."
        )
    },

    "elbow": {
        "keywords": [
            "elbow", "tennis elbow", "golfer elbow",
            "golfers elbow", "epicondylitis",
            "biceps tendon", "forearm tendonitis",
            "bicep tendonitis", "elbow pain", "elbow strain"
        ],
        "banned": [
            "skull crushers", "tricep dips",
            "heavy curls", "close grip bench",
            "preacher curl heavy", "wrist curl"
        ],
        "safe": [
            "light resistance bands",
            "leg exercises", "core exercises",
            "machine leg exercises"
        ],
        "protocol":    "light_resistance_only",
        "diet_note":   "Include turmeric and omega 3 daily for tendon recovery",
        "warning_msg": (
            "⚠️ ELBOW INJURY: No skull crushers, dips, "
            "heavy curls, or close grip bench. "
            "Safe: legs, core, light resistance bands."
        )
    },

    "wrist": {
        "keywords": [
            "wrist", "carpal tunnel", "wrist sprain",
            "wrist fracture", "hand injury",
            "wrist pain", "wrist strain"
        ],
        "banned": [
            "barbell press", "standard push ups",
            "standard grip pull ups", "wrist curls",
            "heavy dumbbell press"
        ],
        "safe": [
            "neutral grip dumbbell",
            "leg exercises", "core exercises",
            "resistance bands", "machine exercises"
        ],
        "protocol":    "neutral_grip_only",
        "diet_note":   "Include collagen rich foods — bone broth, eggs, citrus fruits",
        "warning_msg": (
            "⚠️ WRIST INJURY: No barbell work, standard push ups, "
            "or standard grip pull ups. "
            "Use neutral grip only. Safe: legs, core, bands."
        )
    },

    "back": {
        "keywords": [
            "back", "lumbar", "herniated disc",
            "bulging disc", "spinal", "spondylolysis",
            "lower back", "upper back", "disc herniation",
            "back pain", "back strain", "back injury",
            "disc problem", "sciatica"
        ],
        "banned": [
            "deadlifts", "bent over rows",
            "good mornings", "heavy barbell squats",
            "stiff leg deadlift", "barbell row",
            "hyperextensions heavy"
        ],
        "safe": [
            "swimming", "light walking",
            "leg press machine", "planks",
            "resistance band exercises",
            "lat pulldown seated"
        ],
        "protocol":    "no_heavy_spine_load",
        "diet_note":   "Anti-inflammatory foods: turmeric, ginger, omega 3 daily",
        "warning_msg": (
            "⚠️ BACK INJURY: No deadlifts, heavy squats, "
            "bent over rows, or good mornings. "
            "Safe: swimming, walking, planks, leg press."
        )
    },

    "hip": {
        "keywords": [
            "hip", "hip flexor", "groin",
            "adductor strain", "abdominal tear",
            "oblique tear", "hip impingement",
            "hip pain", "groin strain", "groin pull"
        ],
        "banned": [
            "heavy squats", "lunges",
            "sprints", "explosive jumps",
            "heavy leg raises", "hip thrust heavy"
        ],
        "safe": [
            "upper body exercises",
            "light walking", "swimming",
            "seated upper body machines"
        ],
        "protocol":    "no_explosive_lower",
        "diet_note":   "High protein and omega 3 for muscle tissue repair",
        "warning_msg": (
            "⚠️ HIP INJURY: No heavy squats, lunges, "
            "explosive jumps, or sprinting. "
            "Safe: upper body, light walking, swimming."
        )
    },

    "knee": {
        "keywords": [
            "knee", "acl", "mcl", "lcl",
            "meniscus", "patellar tendonitis",
            "patellofemoral", "runners knee",
            "jumpers knee", "knee pain",
            "knee strain", "knee injury",
            "anterior cruciate", "medial collateral",
            "lateral collateral"
        ],
        "banned": [
            "deep squats", "lunges", "box jumps",
            "running", "jumping", "burpees",
            "leg extension heavy", "jump squats",
            "step ups heavy"
        ],
        "safe": [
            "swimming", "cycling stationary",
            "upper body exercises",
            "seated leg curl light",
            "resistance bands upper",
            "leg press partial range"
        ],
        "protocol":    "low_impact_only",
        "diet_note":   "Omega 3, turmeric, ginger daily for joint inflammation",
        "warning_msg": (
            "⚠️ KNEE INJURY: No jumping, running, deep squats, "
            "lunges, or burpees. "
            "Safe: swimming, cycling, upper body, light resistance."
        )
    },

    "leg": {
        "keywords": [
            "hamstring", "quadriceps", "quad tear",
            "it band", "shin splints", "thigh strain",
            "tibial stress", "hamstring tear",
            "quad strain", "thigh pain", "leg pain",
            "iliotibial"
        ],
        "banned": [
            "sprinting", "heavy leg press",
            "heavy squats", "box jumps",
            "plyometrics", "jump training"
        ],
        "safe": [
            "upper body exercises",
            "light walking", "swimming",
            "seated upper body machines"
        ],
        "protocol":    "upper_body_focus",
        "diet_note":   "High protein diet for muscle tissue repair",
        "warning_msg": (
            "⚠️ LEG INJURY: No sprinting, heavy leg work, "
            "or plyometrics. "
            "Safe: upper body, light walking, swimming."
        )
    },

    "foot": {
        "keywords": [
            "calf", "achilles", "ankle sprain",
            "plantar fasciitis", "foot pain",
            "stress fracture", "metatarsal",
            "shin pain", "ankle injury",
            "ankle fracture", "foot fracture",
            "achilles tendonitis", "achilles rupture"
        ],
        "banned": [
            "running", "jumping rope",
            "box jumps", "standing calf raise heavy",
            "burpees", "sprinting",
            "high impact cardio"
        ],
        "safe": [
            "upper body exercises",
            "seated exercises",
            "swimming", "cycling seated",
            "upper body resistance bands"
        ],
        "protocol":    "no_impact_lower",
        "diet_note":   "Calcium and vitamin D for bone and tendon recovery",
        "warning_msg": (
            "⚠️ FOOT/ANKLE INJURY: No running, jumping, "
            "or high impact cardio. "
            "Safe: upper body, seated exercises, swimming."
        )
    },

    "neck": {
        "keywords": [
            "neck", "cervical", "cervical spine",
            "neck pain", "neck strain", "neck injury",
            "cervical disc", "whiplash"
        ],
        "banned": [
            "overhead press", "behind neck press",
            "heavy shrugs", "neck bridges",
            "upright row", "military press"
        ],
        "safe": [
            "lower body exercises",
            "core exercises light",
            "light resistance bands",
            "light leg exercises"
        ],
        "protocol":    "no_overhead_no_neck_load",
        "diet_note":   "Omega 3 and anti-inflammatory foods daily",
        "warning_msg": (
            "⚠️ NECK INJURY: No overhead work, behind neck press, "
            "or heavy shrugs. Consult physiotherapist before training. "
            "Safe: lower body, core, light bands."
        )
    },

    "serious": {
        "keywords": [
            "concussion", "rhabdomyolysis",
            "nerve compression", "heat stroke",
            "fracture", "bone fracture",
            "surgery", "post surgery",
            "torn ligament"
        ],
        "banned": [
            "all heavy exercises",
            "high intensity training",
            "contact sports"
        ],
        "safe": [
            "light walking only",
            "physiotherapy exercises"
        ],
        "protocol":    "doctor_clearance_required",
        "diet_note":   "Anti-inflammatory diet + high protein for recovery",
        "warning_msg": (
            "🚨 SERIOUS CONDITION DETECTED: "
            "Consult doctor before any exercise. "
            "Rest and recovery is priority."
        )
    }
}

# ── Severity Keywords ─────────────────────────────────────────────────────────

SEVERITY_MAP = {
    "mild": [
        "pain", "soreness", "tightness",
        "discomfort", "ache", "mild"
    ],
    "moderate": [
        "strain", "sprain", "inflammation",
        "tendonitis", "stress fracture",
        "moderate", "chronic"
    ],
    "severe": [
        "tear", "rupture", "fracture",
        "herniated", "herniation", "torn",
        "complete tear", "full tear",
        "surgery", "severe", "acute"
    ]
}

SEVERITY_RECOVERY = {
    "mild":     "1-2 weeks rest then gradual return",
    "moderate": "3-6 weeks with physiotherapy",
    "severe":   "6-12+ weeks — doctor supervision required"
}


# ── Text Normalizer ───────────────────────────────────────────────────────────

def normalize_text(text: str) -> str:
    """
    Normalize text for better injury keyword matching.
    Removes punctuation, lowercases, strips extra spaces.
    """
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"[^a-z\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# ── BMR Calculation ───────────────────────────────────────────────────────────

def calculate_bmr(
    weight: float,
    height: float,
    age:    int,
    gender: str
) -> float:
    """
    Mifflin St Jeor BMR formula.
    Most accurate for general population.

    Male:   (10 × weight) + (6.25 × height) - (5 × age) + 5
    Female: (10 × weight) + (6.25 × height) - (5 × age) - 161

    weight in kg, height in cm, age in years
    """
    if gender.lower() == "male":
        return (10 * weight) + (6.25 * height) - (5 * age) + 5
    else:
        return (10 * weight) + (6.25 * height) - (5 * age) - 161


# ── TDEE Calculation ──────────────────────────────────────────────────────────

def calculate_tdee(bmr: float, activity_level: str) -> float:
    """
    Total Daily Energy Expenditure.
    BMR × Activity multiplier.

    Sedentary: desk job little or no exercise
    Light:     light exercise 1-3 days per week
    Moderate:  moderate exercise 3-5 days per week
    Active:    hard exercise 6-7 days per week
    """
    multipliers = {
        "sedentary": 1.2,
        "light":     1.375,
        "moderate":  1.55,
        "active":    1.725
    }
    return bmr * multipliers.get(activity_level.lower(), 1.55)


# ── Target Calories ───────────────────────────────────────────────────────────

def calculate_target_calories(tdee: float, goal: str) -> int:
    """
    Adjust calories based on goal.
    Sustainable approach — real coach mindset.

    Fat loss:     18% deficit — sustainable not crash diet
    Slim:         15% deficit — gentle reduction
    Strength:      5% surplus — fuel performance
    Bulk:         15% surplus — mass building
    Bodybuilding: 10% surplus — lean mass building
    """
    adjustments = {
        "fat_loss":     0.82,
        "slim":         0.85,
        "strength":     1.05,
        "bulk":         1.15,
        "bodybuilding": 1.10
    }

    target = int(tdee * adjustments.get(goal.lower(), 1.0))

    # Minimum calorie floors
    # Real coaches never starve their athletes
    minimums = {
        "fat_loss":     1400,
        "slim":         1350,
        "strength":     1800,
        "bulk":         2000,
        "bodybuilding": 1800
    }

    minimum = minimums.get(goal.lower(), 1400)
    return max(target, minimum)


# ── Macro Calculator ──────────────────────────────────────────────────────────

def calculate_macros(
    calories: int,
    goal:     str,
    weight:   float
) -> dict:
    """
    Calculate protein carbs fat in grams.
    Sustainable macro split — real coach approach.

    Protein: 1.6-2.0g per kg (sustainable not excessive)
    Fat:     0.7-1.0g per kg (hormone health)
    Carbs:   remaining calories with goal specific minimums

    Minimum carb floors prevent low energy and brain fog.
    """
    goal = goal.lower()

    if goal == "fat_loss":
        protein_g = weight * 1.8   # preserve muscle
        fat_g     = weight * 0.8   # moderate fat
        min_carbs = 80             # gym performance minimum

    elif goal == "slim":
        protein_g = weight * 1.6
        fat_g     = weight * 0.7
        min_carbs = 70

    elif goal == "strength":
        protein_g = weight * 1.8
        fat_g     = weight * 1.0
        min_carbs = 150            # high carbs for strength

    elif goal in ["bulk", "bodybuilding"]:
        protein_g = weight * 2.0
        fat_g     = weight * 1.0
        min_carbs = 200            # high carbs for mass

    else:
        protein_g = weight * 1.6
        fat_g     = weight * 0.9
        min_carbs = 100

    protein_cal = protein_g * 4
    fat_cal     = fat_g * 9
    carb_cal    = calories - protein_cal - fat_cal
    carbs_g     = max(carb_cal / 4, min_carbs)

    protein_g = round(protein_g, 1)
    carbs_g   = round(carbs_g, 1)
    fat_g     = round(fat_g, 1)

    return {
        "protein_g":   protein_g,
        "carbs_g":     carbs_g,
        "fat_g":       fat_g,
        "protein_cal": round(protein_g * 4),
        "carbs_cal":   round(carbs_g * 4),
        "fat_cal":     round(fat_g * 9)
    }


# ── Water Intake ──────────────────────────────────────────────────────────────

def calculate_water_intake(
    weight:         float,
    activity_level: str
) -> dict:
    """
    Calculate daily water intake.
    Base: 35ml per kg bodyweight
    Activity bonus on top of base.
    """
    base_ml = weight * 35

    bonus = {
        "sedentary": 0,
        "light":     250,
        "moderate":  500,
        "active":    750
    }

    total_ml = base_ml + bonus.get(activity_level.lower(), 500)

    return {
        "total_ml":     int(total_ml),
        "total_litres": round(total_ml / 1000, 1),
        "glasses":      int(total_ml / 250)
    }


# ── Diet Level ────────────────────────────────────────────────────────────────

def get_diet_level(workout_experience: str) -> str:
    """
    Map workout experience to diet complexity level.
    Beginner     → basic (simple meals easy prep)
    Intermediate → intermediate (macro tracking)
    Advanced     → advanced (precision nutrition)
    """
    return {
        "beginner":     "basic",
        "intermediate": "intermediate",
        "advanced":     "advanced"
    }.get(workout_experience.lower(), "basic")


# ── Injury Severity Detector ──────────────────────────────────────────────────

def detect_severity(injury_text: str) -> str:
    """
    Detect injury severity from user input text.
    Returns mild, moderate, or severe.
    """
    normalized = normalize_text(injury_text)

    for severity, keywords in SEVERITY_MAP.items():
        if any(k in normalized for k in keywords):
            if severity == "severe":
                return "severe"

    for severity, keywords in SEVERITY_MAP.items():
        if any(k in normalized for k in keywords):
            if severity == "moderate":
                return "moderate"

    if any(k in normalized for k in SEVERITY_MAP["mild"]):
        return "mild"

    return "moderate"  # default if unclear


# ── Profile Validation ────────────────────────────────────────────────────────

def validate_and_fix_profile(
    weight:        float,
    height:        float,
    age:           int,
    target_weight: float,
    target_days:   int,
    sleep_hours:   float,
    goal:          str,
    stress_level:  str  = "low",
    injuries:      str  = "none",
    gym_access:    bool = True
) -> dict:
    """
    Validate user profile and fix unrealistic values.
    Real coach approach — correct bad data with explanation.
    Config driven injury system — scalable and accurate.
    Returns warnings, fixes, and injury protocols.
    """

    warnings        = []
    fixes           = {}
    banned_set      = set()   # use set to prevent duplicates
    safe_set        = set()   # use set to prevent duplicates

    # ── Fix height if entered in inches ───────────────────────────────────────
    if height < 100:
        fixed_height = round(height * 2.54)
        warnings.append(
            f"Height {height} looks like inches. "
            f"Converted to {fixed_height}cm automatically. "
            f"Please update your profile."
        )
        fixes["height"] = fixed_height
    else:
        fixes["height"] = height

    # ── Fix unrealistic weight loss target ────────────────────────────────────
    if target_weight and target_days and goal in ["fat_loss", "slim"]:
        weight_to_lose = weight - target_weight
        if weight_to_lose > 0:
            min_days    = int((weight_to_lose / 0.5) * 7)
            months      = round(min_days / 30)
            if target_days < min_days:
                warnings.append(
                    f"⚠️ UNREALISTIC TARGET: "
                    f"Losing {weight_to_lose}kg in {target_days} days "
                    f"is not medically safe. "
                    f"Maximum safe rate = 0.5kg per week. "
                    f"Realistic timeline = {min_days} days ({months} months). "
                    f"Month 1 safe target = {weight - 2}kg. "
                    f"This adjusted plan gives lasting results."
                )
                fixes["target_days"]            = min_days
                fixes["monthly_realistic_loss"] = 2.0
                fixes["first_month_target"]     = round(weight - 2, 1)
            else:
                fixes["target_days"]            = target_days
                fixes["monthly_realistic_loss"] = round(
                    weight_to_lose / (target_days / 30), 1
                )

    # ── Sleep warnings ────────────────────────────────────────────────────────
    if sleep_hours < 5:
        warnings.append(
            f"🚨 CRITICAL SLEEP: Only {sleep_hours} hours detected. "
            f"Fat loss is nearly impossible at this level. "
            f"Cortisol rises → belly fat increases. "
            f"Ghrelin spikes → cravings double. "
            f"Muscle recovery blocked completely. "
            f"Fix sleep to 7 hours FIRST — "
            f"this matters more than any diet or workout."
        )
        fixes["sleep_critical"] = True
        fixes["sleep_target"]   = "7 hours minimum"
        fixes["sleep_priority"] = "Fix sleep before expecting results"

    elif sleep_hours < 6.5:
        warnings.append(
            f"⚠️ SLEEP WARNING: {sleep_hours} hours is below optimal. "
            f"Target 7-8 hours for best fat loss and recovery."
        )
        fixes["sleep_critical"] = False
        fixes["sleep_target"]   = "7-8 hours"

    elif sleep_hours < 7:
        warnings.append(
            f"Sleep {sleep_hours} hours slightly below optimal. "
            f"Try to reach 7 hours for best results."
        )
        fixes["sleep_critical"] = False

    # ── High stress warning ───────────────────────────────────────────────────
    if stress_level and stress_level.lower() == "high":
        warnings.append(
            "⚠️ HIGH STRESS: Cortisol raised → belly fat storage. "
            "Simple fixes: 10 min walk after meals, "
            "no phone 1 hour before sleep, "
            "5 min deep breathing daily."
        )
        fixes["stress_protocol"] = "stress_management"

    # ── No gym warning ────────────────────────────────────────────────────────
    if not gym_access:
        warnings.append(
            "⚠️ NO GYM: Home workout plan recommended. "
            "6000-8000 steps walking daily is essential. "
            "Bodyweight exercises and resistance bands are effective."
        )
        fixes["workout_type"] = "home"

    # ── Injury detection — config driven ─────────────────────────────────────
    injury_normalized  = normalize_text(injuries)
    detected_areas     = []

    if injury_normalized and injury_normalized not in ["none", "na", "no", ""]:

        # Detect severity first
        severity = detect_severity(injury_normalized)
        fixes["injury_severity"]          = severity
        fixes["injury_recovery_timeline"] = SEVERITY_RECOVERY[severity]

        # Check each injury group
        for area, config in INJURY_MAP.items():
            if any(k in injury_normalized for k in config["keywords"]):
                detected_areas.append(area)

                # Add warning
                warnings.append(config["warning_msg"])

                # Add diet note
                fixes.setdefault("injury_diet_notes", []).append(
                    config["diet_note"]
                )

                # Add protocol
                fixes[f"{area}_protocol"] = config["protocol"]

                # Collect banned and safe exercises
                banned_set.update(config["banned"])
                safe_set.update(config["safe"])

        # Convert sets to sorted lists
        if banned_set:
            fixes["banned_exercises"] = sorted(list(banned_set))

        if safe_set:
            fixes["safe_exercises"] = sorted(list(safe_set))

        # Store detected areas
        if detected_areas:
            fixes["injured_areas"] = detected_areas

        # Multiple injury areas
        if len(detected_areas) >= 2:
            warnings.append(
                f"⚠️ MULTIPLE INJURIES: "
                f"{len(detected_areas)} areas affected "
                f"({', '.join(detected_areas)}). "
                f"Strongly recommend physiotherapist consultation "
                f"before training. "
                f"Anti-inflammatory diet protocol activated: "
                f"omega 3, turmeric, ginger, vitamin C daily."
            )
            fixes["consult_physio"]         = True
            fixes["anti_inflammatory_diet"] = True

        # Severe multi-injury — block workout
        if len(detected_areas) >= 3 or severity == "severe":
            warnings.append(
                "🚨 WORKOUT SAFETY LOCK: "
                f"{'Multiple severe injury areas' if len(detected_areas) >= 3 else 'Severe injury'} detected. "
                "Do NOT start workout program without doctor clearance. "
                "Focus on diet and recovery only."
            )
            fixes["workout_blocked"] = True

        # Severity specific message
        if severity == "mild":
            fixes["severity_advice"] = (
                "Mild injury: Train around it carefully. "
                "Stop if pain increases. "
                "Recovery: 1-2 weeks."
            )
        elif severity == "moderate":
            fixes["severity_advice"] = (
                "Moderate injury: Reduce intensity significantly. "
                "Avoid all banned exercises. "
                "Recovery: 3-6 weeks with rest."
            )
        elif severity == "severe":
            fixes["severity_advice"] = (
                "Severe injury: Rest completely. "
                "Consult physiotherapist. "
                "Recovery: 6-12+ weeks under supervision."
            )

    return {
        "warnings":       warnings,
        "fixes":          fixes,
        "detected_areas": detected_areas,
        "is_valid":       len([
            w for w in warnings
            if "CRITICAL" in w or "UNREALISTIC" in w
        ]) == 0
    }


# ── Champion Style ────────────────────────────────────────────────────────────

def get_champion_style(goal: str) -> dict:
    """
    Real Indian champion diet style based on goal.
    Each champion matches the specific fitness goal.
    """
    styles = {
        "fat_loss": {
            "champion":       "Virat Kohli",
            "sport":          "Cricket — Indian Captain",
            "style":          "Lean Athletic Performance",
            "description": (
                "Virat Kohli achieved his lean physique through "
                "consistent clean eating over years — not crash dieting. "
                "High protein whole foods minimal processed food. "
                "He personally removed dairy and gluten but "
                "that is his individual choice — not required "
                "for everyday fat loss. "
                "For you: focus on clean Indian food, "
                "high protein, moderate carbs, healthy fats. "
                "Curd, roti, dal, chicken, eggs — real Indian food "
                "eaten consistently for 3 months gives "
                "Virat level results. No extreme restrictions needed."
            ),
            "key_foods": (
                "Grilled chicken, eggs, brown rice, roti, "
                "curd, dal, vegetables, fruits, nuts, buttermilk"
            ),
            "avoid": (
                "Fried food, excess sugar, processed food, "
                "alcohol, late night heavy meals"
            ),
            "meal_timing": (
                "5 meals per day every 3 hours. "
                "Never skip breakfast. "
                "Light dinner before 8pm. "
                "Curd with every main meal."
            ),
            "champion_quote": (
                "Consistency over perfection. "
                "Eat clean 90% of the time and "
                "results will come — Virat Kohli"
            )
        },

        "bulk": {
            "champion":       "Sushil Kumar",
            "sport":          "Wrestling — Olympic Gold Medalist",
            "style":          "Traditional Mass Building",
            "description": (
                "Sushil Kumar combines traditional Indian foods "
                "with modern sports nutrition for maximum mass. "
                "Dal, rice, roti, milk, ghee combined with "
                "high protein foods every single day. "
                "6 full meals per day without exception. "
                "Never trains on empty stomach."
            ),
            "key_foods": (
                "Dal, roti, rice, full fat milk, ghee, "
                "paneer, eggs, chicken, dry fruits, banana"
            ),
            "avoid": (
                "Junk food, soft drinks, "
                "processed snacks, alcohol"
            ),
            "meal_timing": (
                "6 meals per day. "
                "Post workout meal within 30 min critical. "
                "Never sleep hungry."
            ),
            "champion_quote": (
                "Food is fuel. "
                "Eat like a champion to become one — Sushil Kumar"
            )
        },

        "strength": {
            "champion":       "Sajad Maddah",
            "sport":          "Powerlifting — World Champion",
            "style":          "Raw Strength Nutrition",
            "description": (
                "World class powerlifters eat for maximum "
                "strength output. High protein high carb diet. "
                "Every meal fuels the next heavy session. "
                "Dal, roti, rice, chicken, eggs, milk daily. "
                "No compromise on food quality or quantity."
            ),
            "key_foods": (
                "Chicken breast, eggs, brown rice, roti, "
                "full fat milk, dal, paneer, ghee, "
                "sweet potato, banana, dry fruits"
            ),
            "avoid": (
                "Processed food, alcohol, "
                "excessive sugar, junk food"
            ),
            "meal_timing": (
                "5-6 meals per day. "
                "Heavy pre workout meal 1 hour before. "
                "Post workout protein and carbs within 30 min. "
                "Never train fasted."
            ),
            "champion_quote": (
                "Strength is built in the kitchen "
                "before it is built in the gym. "
                "Eat big, lift big, get strong."
            )
        },

        "bodybuilding": {
            "champion":       "Sangram Chougule",
            "sport":          "Mr Universe — Bodybuilding Champion",
            "style":          "Championship Precision Nutrition",
            "description": (
                "Sangram Chougule follows extremely precise macros. "
                "Strict meal timing and portion control every day. "
                "High protein every 2-3 hours mandatory. "
                "Carb cycling for contest prep phases. "
                "Zero tolerance for processed food or alcohol."
            ),
            "key_foods": (
                "Chicken breast, egg whites, "
                "brown rice, oats, sweet potato, "
                "broccoli, green vegetables"
            ),
            "avoid": (
                "Any processed food, excess fat, "
                "sugar completely, alcohol completely"
            ),
            "meal_timing": (
                "6-7 meals per day. "
                "Protein every 2-3 hours mandatory. "
                "Carbs only pre and post workout."
            ),
            "champion_quote": (
                "Precision in the kitchen "
                "equals perfection on stage — Sangram Chougule"
            )
        },

        "slim": {
            "champion":       "PV Sindhu",
            "sport":          "Badminton — Olympic Silver Medalist",
            "style":          "Lean Fit Athletic Performance",
            "description": (
                "PV Sindhu focuses on South Indian diet "
                "combined with modern nutrition science. "
                "Balanced nutrition for endurance and agility. "
                "Rice, idli, dosa with proteins and vegetables. "
                "Light but nutrient dense every single meal."
            ),
            "key_foods": (
                "Idli, dosa, rice, dal, "
                "chicken, fish, vegetables, "
                "buttermilk, coconut"
            ),
            "avoid": (
                "Fried food, sugar, "
                "heavy desserts, oily curries"
            ),
            "meal_timing": (
                "5 meals per day. "
                "Heavy breakfast. "
                "Light dinner before 7pm."
            ),
            "champion_quote": (
                "Eat light, train hard, "
                "and results will follow — PV Sindhu"
            )
        }
    }

    return styles.get(goal.lower(), styles["strength"])


# ── Supplements ───────────────────────────────────────────────────────────────

def get_supplements(goal: str, level: str) -> list:
    """
    Supplement recommendations.
    Practical and affordable Indian market brands.
    Ordered by priority.
    """
    supplements = []

    # ── Essential for everyone ────────────────────────────────────────────────
    supplements.append({
        "name":             "Whey Protein",
        "when":             "Within 30 minutes after workout",
        "dosage":           "25-30g (1 scoop) in 200-250ml water or milk",
        "benefit":          "Fast absorbing protein for muscle repair and recovery",
        "indian_brands":    "MuscleBlaze Biozyme, ON Gold Standard, MyProtein",
        "approximate_cost": "₹1500-3000 per kg (30-40 servings)",
        "priority":         "HIGH",
        "note":             "Mix with milk for better taste and extra protein"
    })

    supplements.append({
        "name":             "Multivitamin",
        "when":             "With breakfast every morning",
        "dosage":           "1 tablet daily with food",
        "benefit":          "Fill nutritional gaps. Support immunity and energy.",
        "indian_brands":    "HealthKart HK Vitals, Centrum, Revital H",
        "approximate_cost": "₹300-600 per month",
        "priority":         "HIGH"
    })

    supplements.append({
        "name":             "Vitamin D3 + K2",
        "when":             "With any meal containing fat",
        "dosage":           "2000 IU D3 + 100mcg K2 daily",
        "benefit":          "Bone health, immunity, testosterone, mood",
        "indian_brands":    "Carbamide Forte, HealthKart, NOW Foods",
        "approximate_cost": "₹200-500 per month",
        "priority":         "HIGH — 80% Indians are deficient"
    })

    supplements.append({
        "name":             "Omega 3 Fish Oil",
        "when":             "With lunch or dinner",
        "dosage":           "2 capsules (2000mg EPA+DHA) daily",
        "benefit":          "Joint health, inflammation reduction, heart and brain health",
        "indian_brands":    "MuscleBlaze Fish Oil, WOW Omega 3, Himalaya",
        "approximate_cost": "₹400-800 per month",
        "priority":         "MEDIUM-HIGH"
    })

    # ── Goal specific ─────────────────────────────────────────────────────────
    if goal.lower() in ["bulk", "strength", "bodybuilding"]:
        supplements.append({
            "name":             "Creatine Monohydrate",
            "when":             "Post workout or any consistent time daily",
            "dosage":           "3-5g daily — no loading phase needed",
            "benefit":          "Increases strength, power output and muscle size",
            "indian_brands":    "MuscleBlaze CreAMP, ON Micronized, MyProtein",
            "approximate_cost": "₹500-1200 per month",
            "priority":         "HIGH",
            "note":             (
                "Take every day consistently for 8+ weeks. "
                "Results are cumulative not immediate."
            )
        })

    if goal.lower() == "fat_loss":
        supplements.append({
            "name":             "L-Carnitine",
            "when":             "30 minutes before workout on empty stomach",
            "dosage":           "2000mg daily",
            "benefit":          "Transports fat to mitochondria to be burned as energy",
            "indian_brands":    "MuscleBlaze L-Carnitine, HealthKart, GNC",
            "approximate_cost": "₹600-1200 per month",
            "priority":         "MEDIUM"
        })

    # ── Advanced only ─────────────────────────────────────────────────────────
    if level.lower() == "advanced":
        supplements.append({
            "name":             "BCAA",
            "when":             "During workout — sip throughout session",
            "dosage":           "5-10g in 500ml water",
            "benefit":          "Prevent muscle breakdown during intense fasted training",
            "indian_brands":    "MuscleBlaze BCAA Pro, ON BCAA 5000, MyProtein",
            "approximate_cost": "₹800-2000 per month",
            "priority":         "MEDIUM"
        })

    return supplements