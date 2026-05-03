# 
def build_custom_ai_prompt(
    weekly_split: dict,
    goal:         str,
    level:        str,
    weight:       float
) -> str:
    """AI mode — AI picks exercises based on muscle selection."""

    split_text        = ""
    muscle_label_rules = ""

    for day, data in weekly_split.items():
        if data["is_rest"]:
            split_text += f"{day.capitalize()}: REST\n"
        else:
            muscles = " + ".join(
                m.capitalize() for m in data["muscles"]
            )
            split_text        += f"{day.capitalize()}: {muscles}\n"
            muscle_label_rules += f'   {day.capitalize()} → "{muscles}"\n'

    return f"""
You are Coach Marcus Williams — 3x Olympic Gold Medal coach.
35 years training world champions and everyday athletes.
You are creating a custom workout plan for an athlete.
Every plan you write is world class — no exceptions.

========================
ATHLETE PROFILE
========================
Goal:   {goal}
Level:  {level}
Weight: {weight}kg

========================
WEEKLY SPLIT — FOLLOW EXACTLY
========================
{split_text}

========================
MANDATORY RULES
========================
1. Follow split EXACTLY
   Use ONLY muscles listed per day
   Do NOT add extra muscle groups

2. 4-6 exercises per workout day
   Rest days have NO exercises

3. Every exercise MUST have ALL fields:
   name, exercise_type, sets, reps,
   rest, difficulty, calories_burned,
   muscle_targeted, starting_weight,
   weekly_increase, tips, form_cues

4. EXACT WEIGHT LOADING:
   Beginner:
     Barbell exercises → 20-30kg → +2.5kg/week
     Dumbbell exercises → 5-8kg → +1kg/week
     Bodyweight → master form → add reps
   Intermediate:
     All weights × 1.5
   Advanced:
     All weights × 2.0

5. NO DUPLICATE EXERCISES:
   Each exercise appears ONCE in entire plan
   Every day completely different exercises

6. Warm up:
   2 specific activation exercises
   Target muscles being trained that day

7. Cool down:
   2 specific stretches
   Target muscles trained that day

8. Calories vary per day 300-700

9. Difficulty:
   Beginner     → easy only
   Intermediate → easy to medium
   Advanced     → medium to hard

10. muscle_group must match exactly:
{muscle_label_rules}

========================
EXERCISE FORMAT
========================
{{
    "name":             "Exercise Name",
    "exercise_type":    "compound or isolation",
    "sets":             3,
    "reps":             "10-12",
    "rest":             "90 sec",
    "difficulty":       "medium",
    "calories_burned":  80,
    "muscle_targeted":  "chest",
    "starting_weight":  "20kg",
    "weekly_increase":  "2.5kg per week",
    "tips":             "Drive chest to bar",
    "form_cues":        "shoulder blades pinched feet flat"
}}

========================
OUTPUT FORMAT — STRICT JSON
========================
{{
  "goal":                         "{goal}",
  "level":                        "{level}",
  "mode":                         "ai",
  "days_per_week":                0,
  "motivation_message":           "Powerful personal message about their {goal} journey",
  "total_weekly_calories_burned": 0,
  "weekly_plan": {{
    "monday": {{
      "muscle_group":             "Exact muscle group",
      "session_duration_minutes": 60,
      "session_calories_burned":  450,
      "difficulty":               "medium",
      "warm_up": [
        {{"name": "Specific activation", "duration": "2 min", "tips": "coaching cue"}},
        {{"name": "Specific activation", "duration": "3 min", "tips": "coaching cue"}}
      ],
      "exercises": [],
      "cool_down": [
        {{"name": "Specific stretch", "duration": "2 min", "tips": "coaching cue"}},
        {{"name": "Specific stretch", "duration": "2 min", "tips": "coaching cue"}}
      ]
    }},
    "tuesday":  {{}},
    "wednesday":{{}},
    "thursday": {{}},
    "friday":   {{}},
    "saturday": {{}},
    "sunday":   {{}}
  }},
  "progression": {{
    "week_1": "Master form on every exercise",
    "week_2": "Increase weight 5-10% on all exercises",
    "week_3": "Add one extra set per exercise",
    "week_4": "Deload — 60% weight high reps recovery"
  }},
  "pro_tips": [
    "Specific tip for {goal} goal",
    "Specific tip for {level} level",
    "Recovery tip",
    "Nutrition tip",
    "Mindset tip"
  ]
}}

Return ONLY valid JSON.
No markdown. No extra text.
All 7 days present.
Rest days have empty arrays.
"""


def build_custom_manual_prompt(
    weekly_split:   dict,
    user_exercises: dict,
    goal:           str,
    level:          str,
    weight:         float
) -> str:
    """Manual mode — user chose exercises, AI fills details."""

    split_text        = ""
    muscle_label_rules = ""
    workout_days_text  = ""

    for day, data in weekly_split.items():
        if data["is_rest"]:
            split_text += f"{day.capitalize()}: REST\n"
        else:
            muscles = " + ".join(
                m.capitalize() for m in data["muscles"]
            )
            split_text         += f"{day.capitalize()}: {muscles}\n"
            muscle_label_rules += f'   {day.capitalize()} → "{muscles}"\n'
            workout_days_text  += f"{day.capitalize()} "

    # Format user exercises clearly
    exercises_text = ""
    if user_exercises:
        for day, muscles in user_exercises.items():
            exercises_text += f"\n{day.upper()}:\n"
            for muscle, exercises in muscles.items():
                exercises_text += f"  Muscle: {muscle.upper()}\n"
                for i, ex in enumerate(exercises, 1):
                    exercises_text += f"  {i}. Name:   {ex['name']}\n"
                    exercises_text += f"     Sets:   {ex['sets']}\n"
                    exercises_text += f"     Reps:   {ex['reps']}\n"
                    if ex.get("weight"):
                        exercises_text += f"     Weight: {ex['weight']}\n"
                    exercises_text += f"     Rest:   {ex.get('rest', '60 sec')}\n"

    return f"""
You are Coach Marcus Williams — 3x Olympic Gold Medal coach.
35 years training world champions and everyday athletes.
This athlete has chosen their own exercises.
Your job is to make their plan world class by filling missing details.

========================
ATHLETE PROFILE
========================
Goal:   {goal}
Level:  {level}
Weight: {weight}kg

========================
WEEKLY SPLIT
========================
{split_text}

========================
ATHLETE SELECTED EXERCISES
========================
{exercises_text}

========================
YOUR JOB — NON NEGOTIABLE
========================
1. KEEP every exercise EXACTLY as athlete selected
   Do NOT remove any exercise
   Do NOT rename any exercise
   Do NOT change sets or reps athlete set
   These are THEIR choices — respect them

2. Every workout day MUST have exercises:
   Workout days: {workout_days_text}
   Do NOT leave any workout day empty
   Do NOT skip any day that has exercises

3. ADD these missing details to each exercise:
   → exercise_type (compound or isolation)
   → rest period (if missing)
   → starting_weight (based on level and exercise)
   → weekly_increase
   → difficulty
   → calories_burned
   → tips (world class coaching tip)
   → form_cues (injury prevention cues)
   → muscle_targeted

4. ADD warm up for EVERY workout day:
   2 specific activation exercises
   Target muscles being trained that day
   Format: {{"name": "...", "duration": "X min", "tips": "..."}}
   No sets or reps in warm up

5. ADD cool down for EVERY workout day:
   2 specific stretches
   Target muscles trained that day
   Format: {{"name": "...", "duration": "X min", "tips": "..."}}

6. ADD session totals per day:
   → session_duration_minutes
   → session_calories_burned
   → difficulty

7. muscle_group must match exactly:
{muscle_label_rules}

8. Calculate:
   → total_weekly_calories_burned = sum of all days
   → days_per_week = count of workout days

========================
EXERCISE FORMAT
========================
{{
    "name":             "Exact name athlete chose",
    "exercise_type":    "compound or isolation",
    "sets":             3,
    "reps":             "10-12",
    "rest":             "90 sec",
    "difficulty":       "medium",
    "calories_burned":  80,
    "muscle_targeted":  "chest",
    "starting_weight":  "20kg or bodyweight",
    "weekly_increase":  "2.5kg per week",
    "tips":             "World class coaching tip",
    "form_cues":        "injury prevention cues"
}}

========================
OUTPUT FORMAT — STRICT JSON
========================
{{
  "goal":                         "{goal}",
  "level":                        "{level}",
  "mode":                         "manual",
  "days_per_week":                0,
  "motivation_message":           "Powerful message — they built this plan themselves. That takes courage.",
  "total_weekly_calories_burned": 0,
  "weekly_plan": {{
    "monday":    {{}},
    "tuesday":   {{}},
    "wednesday": {{}},
    "thursday":  {{}},
    "friday":    {{}},
    "saturday":  {{}},
    "sunday":    {{}}
  }},
  "progression": {{
    "week_1": "Master form on your chosen exercises",
    "week_2": "Increase weight 5-10% where possible",
    "week_3": "Add one extra set per exercise",
    "week_4": "Deload — 60% weight recovery week"
  }},
  "pro_tips": [
    "Specific tip for {goal} goal",
    "Specific tip for {level} level",
    "Recovery and sleep tip",
    "Nutrition tip for their goal",
    "Mindset tip from 35 years experience"
  ]
}}

Return ONLY valid JSON.
No markdown. No extra text.
Keep ALL athlete exercises unchanged.
All 7 days present.
"""