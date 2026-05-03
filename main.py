# import random
# from datetime import datetime, timedelta, timezone

# from fastapi import FastAPI, Depends, HTTPException, Response, Request
# from fastapi.middleware.cors import CORSMiddleware
# from slowapi.errors import RateLimitExceeded
# from sqlalchemy.orm import Session

# from database import Base, engine, get_db
# from models import (
#     User, RefreshToken, BlacklistedToken,
#     UserBodyMetrics, UserFitnessGoals,
#     UserLifestyle, UserHealth
# )
# from schemas import (
#     SignUpRequest, LoginRequest, RefreshTokenRequest,
#     BodyMetricsRequest, FitnessGoalsRequest,
#     LifestyleRequest, HealthRequest, VerifyOTPRequest
# )
# from auth import (
#     hash_password, verify_password,
#     create_access_token, create_refresh_token,
#     verify_access_token,
#     COOKIE_SECURE, COOKIE_SAMESITE,
#     MAX_LOGIN_ATTEMPTS, LOCK_MINUTES,
#     ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS,
# )
# from modules.security import (
#     limiter, rate_limit_exceeded_handler,
#     sanitize_string, sanitize_email,
#     get_device_info,
#     blacklist_token, is_token_blacklisted,
#     is_new_device, save_device, log_login_attempt,
#     send_verification_email, send_otp_email,
#     send_new_device_alert,
#     generate_verification_token, generate_otp
# )
# from modules.workout_generator import generate_workout_plan

# Base.metadata.create_all(bind=engine)

# app = FastAPI(title="Gym AI Agent")

# # ── Rate Limiter ──────────────────────────────────────────────────────────────
# app.state.limiter = limiter
# app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# # ── CORS ──────────────────────────────────────────────────────────────────────
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins     = ["http://localhost:5173", "http://localhost:3000"],
#     allow_credentials = True,
#     allow_methods     = ["GET", "POST", "PUT", "DELETE"],
#     allow_headers     = ["Content-Type", "Authorization"],
# )


# # ── Helpers ───────────────────────────────────────────────────────────────────

# def make_aware(dt: datetime) -> datetime:
#     if dt is not None and dt.tzinfo is None:
#         return dt.replace(tzinfo=timezone.utc)
#     return dt


# def set_auth_cookies(response: Response, access_token: str, refresh_token: str):
#     response.set_cookie(
#         key="access_token", value=access_token,
#         httponly=True, secure=COOKIE_SECURE,
#         samesite=COOKIE_SAMESITE,
#         max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60, path="/"
#     )
#     response.set_cookie(
#         key="refresh_token", value=refresh_token,
#         httponly=True, secure=COOKIE_SECURE,
#         samesite=COOKIE_SAMESITE,
#         max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60, path="/"
#     )


# def get_current_user(request: Request, db: Session = Depends(get_db)):
#     token = request.cookies.get("access_token")
#     if not token:
#         raise HTTPException(401, "Not authenticated")

#     # Check blacklist
#     if is_token_blacklisted(db, token):
#         raise HTTPException(401, "Token has been revoked")

#     payload = verify_access_token(token)
#     if not payload:
#         raise HTTPException(401, "Invalid or expired token")

#     user = db.query(User).filter(User.id == payload["user_id"]).first()
#     if not user:
#         raise HTTPException(404, "User not found")
#     if not user.is_verified:
#         raise HTTPException(403, "Please verify your email first")
#     return user


# def user_response(user: User) -> dict:
#     return {
#         "id":             user.id,
#         "name":           user.name,
#         "email":          user.email,
#         "is_verified":    user.is_verified,
#         "two_fa_enabled": user.two_fa_enabled
#     }


# # ── Auth Routes ───────────────────────────────────────────────────────────────

# @app.get("/")
# def home():
#     return {"message": "Gym AI Agent API is running"}


# @app.post("/signup")
# @limiter.limit("5/hour")
# async def signup(
#     request: Request,
#     payload: SignUpRequest,
#     db: Session = Depends(get_db)
# ):
#     # Sanitize inputs
#     name  = sanitize_string(payload.name)
#     email = sanitize_email(payload.email)

#     existing = db.query(User).filter(User.email == email).first()
#     if existing:
#         raise HTTPException(400, "Email already registered")

#     verify_token   = generate_verification_token()
#     verify_expires = datetime.now(timezone.utc) + timedelta(hours=24)

#     user = User(
#         name                 = name,
#         email                = email,
#         password_hash        = hash_password(payload.password),
#         is_verified          = False,
#         verification_token   = verify_token,
#         verification_expires = verify_expires
#     )
#     db.add(user)
#     db.commit()
#     db.refresh(user)

#     await send_verification_email(user.email, user.name, verify_token)

#     return {"message": "Signup successful. Please check your email to verify your account."}


# @app.get("/verify-email")
# def verify_email(token: str, db: Session = Depends(get_db)):
#     user = db.query(User).filter(User.verification_token == token).first()
#     if not user:
#         raise HTTPException(400, "Invalid verification token")

#     if make_aware(user.verification_expires) < datetime.now(timezone.utc):
#         raise HTTPException(400, "Verification link expired. Please request a new one.")

#     user.is_verified          = True
#     user.verification_token   = None
#     user.verification_expires = None
#     db.commit()

#     return {"message": "Email verified successfully. You can now login!"}


# @app.post("/resend-verification")
# @limiter.limit("3/hour")
# async def resend_verification(
#     request: Request,
#     email: str,
#     db: Session = Depends(get_db)
# ):
#     user = db.query(User).filter(User.email == email).first()
#     if not user:
#         raise HTTPException(404, "User not found")
#     if user.is_verified:
#         raise HTTPException(400, "Email already verified")

#     verify_token             = generate_verification_token()
#     user.verification_token   = verify_token
#     user.verification_expires = datetime.now(timezone.utc) + timedelta(hours=24)
#     db.commit()

#     await send_verification_email(user.email, user.name, verify_token)
#     return {"message": "Verification email resent. Please check your inbox."}


# @app.post("/login")
# @limiter.limit("10/minute")
# async def login(
#     request: Request,
#     payload: LoginRequest,
#     response: Response,
#     db: Session = Depends(get_db)
# ):
#     device_info = get_device_info(request)
#     email       = sanitize_email(payload.email)
#     user        = db.query(User).filter(User.email == email).first()

#     if not user:
#         raise HTTPException(401, "Invalid credentials")

#     if not user.is_verified:
#         raise HTTPException(403, "Please verify your email before logging in")

#     now = datetime.now(timezone.utc)

#     # Check lock
#     if user.lock_until and make_aware(user.lock_until) > now:
#         remaining = (make_aware(user.lock_until) - now).seconds // 60
#         log_login_attempt(db, user.id, device_info, "blocked", "Account locked")
#         raise HTTPException(423, f"Account locked. Try again in {remaining} minutes.")

#     # Wrong password
#     if not verify_password(payload.password, user.password_hash):
#         user.failed_login_attempts += 1
#         user.last_failed_ip         = device_info["ip_address"]

#         if user.failed_login_attempts >= MAX_LOGIN_ATTEMPTS:
#             user.lock_until            = now + timedelta(minutes=LOCK_MINUTES)
#             user.failed_login_attempts = 0
#             db.commit()
#             log_login_attempt(db, user.id, device_info, "blocked", "Too many attempts")
#             raise HTTPException(423, f"Too many failed attempts. Account locked for {LOCK_MINUTES} minutes.")

#         db.commit()
#         log_login_attempt(db, user.id, device_info, "failed", "Wrong password")
#         raise HTTPException(401, "Invalid credentials")

#     # Reset lock on success
#     user.failed_login_attempts = 0
#     user.lock_until            = None
#     user.last_login_at         = now
#     db.commit()

#     # Check new device → send alert email
#     new_device = is_new_device(db, user.id, device_info["device_id"])
#     if new_device:
#         await send_new_device_alert(user.email, user.name, device_info)

#     # Save device
#     save_device(db, user.id, device_info)

#     # 2FA enabled → send OTP
#     if user.two_fa_enabled:
#         otp                     = generate_otp()
#         user.two_fa_otp         = otp
#         user.two_fa_otp_expires = now + timedelta(minutes=10)
#         db.commit()

#         await send_otp_email(user.email, user.name, otp)
#         log_login_attempt(db, user.id, device_info, "2fa_pending", "OTP sent")
#         return {"message": "OTP sent to your email", "two_fa_required": True}

#     # Issue tokens
#     access_token              = create_access_token({"user_id": user.id, "email": user.email})
#     refresh_token_str, exp_at = create_refresh_token()

#     db.add(RefreshToken(
#         user_id   = user.id,
#         token     = refresh_token_str,
#         expires_at = exp_at,
#         device_id = device_info["device_id"]
#     ))
#     db.commit()

#     set_auth_cookies(response, access_token, refresh_token_str)
#     log_login_attempt(db, user.id, device_info, "success", None)

#     return {"message": "Login successful", "two_fa_required": False, "user": user_response(user)}


# @app.post("/verify-otp")
# @limiter.limit("5/minute")
# def verify_otp(
#     request: Request,
#     payload: VerifyOTPRequest,
#     response: Response,
#     db: Session = Depends(get_db)
# ):
#     user = db.query(User).filter(User.email == payload.email).first()
#     if not user:
#         raise HTTPException(404, "User not found")

#     now = datetime.now(timezone.utc)

#     if not user.two_fa_otp or user.two_fa_otp != payload.otp:
#         raise HTTPException(401, "Invalid OTP")

#     if make_aware(user.two_fa_otp_expires) < now:
#         raise HTTPException(401, "OTP expired. Please login again.")

#     # Clear OTP
#     user.two_fa_otp         = None
#     user.two_fa_otp_expires = None
#     db.commit()

#     access_token              = create_access_token({"user_id": user.id, "email": user.email})
#     refresh_token_str, exp_at = create_refresh_token()

#     db.add(RefreshToken(user_id=user.id, token=refresh_token_str, expires_at=exp_at))
#     db.commit()

#     set_auth_cookies(response, access_token, refresh_token_str)
#     return {"message": "OTP verified. Login successful.", "user": user_response(user)}


# @app.post("/refresh")
# def refresh(request: Request, response: Response, db: Session = Depends(get_db)):
#     token = request.cookies.get("refresh_token")
#     if not token:
#         raise HTTPException(401, "Refresh token missing")

#     now      = datetime.now(timezone.utc)
#     db_token = db.query(RefreshToken).filter(
#         RefreshToken.token      == token,
#         RefreshToken.is_revoked == False
#     ).first()

#     if not db_token:
#         raise HTTPException(401, "Invalid or revoked refresh token")

#     if make_aware(db_token.expires_at) < now:
#         raise HTTPException(401, "Refresh token expired. Please login again.")

#     # Rotate tokens
#     db_token.is_revoked       = True
#     access_token              = create_access_token({"user_id": db_token.user_id})
#     refresh_token_str, exp_at = create_refresh_token()

#     db.add(RefreshToken(user_id=db_token.user_id, token=refresh_token_str, expires_at=exp_at))
#     db.commit()

#     set_auth_cookies(response, access_token, refresh_token_str)

#     user = db.query(User).filter(User.id == db_token.user_id).first()
#     return {"message": "Token refreshed", "user": user_response(user)}


# @app.post("/logout")
# def logout(request: Request, response: Response, db: Session = Depends(get_db)):
#     # Blacklist access token
#     access_token = request.cookies.get("access_token")
#     if access_token:
#         payload = verify_access_token(access_token)
#         if payload:
#             blacklist_token(db, payload["user_id"], access_token, "logout")

#     # Revoke refresh token
#     refresh_token_val = request.cookies.get("refresh_token")
#     if refresh_token_val:
#         db_token = db.query(RefreshToken).filter(RefreshToken.token == refresh_token_val).first()
#         if db_token:
#             db_token.is_revoked = True
#             db.commit()

#     response.delete_cookie("access_token")
#     response.delete_cookie("refresh_token")
#     return {"message": "Logged out successfully"}


# @app.get("/me")
# def get_me(user: User = Depends(get_current_user)):
#     return {"message": "User fetched", "user": user_response(user)}


# # ── 2FA Management ────────────────────────────────────────────────────────────

# @app.post("/enable-2fa")
# def enable_2fa(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
#     user.two_fa_enabled = True
#     db.commit()
#     return {"message": "2FA enabled. You will receive OTP on every login."}


# @app.post("/disable-2fa")
# def disable_2fa(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
#     user.two_fa_enabled     = False
#     user.two_fa_otp         = None
#     user.two_fa_otp_expires = None
#     db.commit()
#     return {"message": "2FA disabled"}


# # ── Security Info Routes ──────────────────────────────────────────────────────

# @app.get("/login-history")
# def get_login_history(
#     db: Session = Depends(get_db),
#     user: User  = Depends(get_current_user)
# ):
#     from models import LoginHistory
#     history = db.query(LoginHistory).filter(
#         LoginHistory.user_id == user.id
#     ).order_by(LoginHistory.logged_at.desc()).limit(20).all()

#     return {
#         "history": [
#             {
#                 "ip_address":  h.ip_address,
#                 "device_name": h.device_name,
#                 "browser":     h.browser,
#                 "os":          h.os,
#                 "status":      h.status,
#                 "reason":      h.reason,
#                 "logged_at":   h.logged_at
#             }
#             for h in history
#         ]
#     }


# @app.get("/trusted-devices")
# def get_trusted_devices(
#     db: Session = Depends(get_db),
#     user: User  = Depends(get_current_user)
# ):
#     from models import UserDevice
#     devices = db.query(UserDevice).filter(UserDevice.user_id == user.id).all()
#     return {
#         "devices": [
#             {
#                 "device_id":   d.device_id,
#                 "device_name": d.device_name,
#                 "browser":     d.browser,
#                 "os":          d.os,
#                 "ip_address":  d.ip_address,
#                 "is_trusted":  d.is_trusted,
#                 "last_used_at": d.last_used_at
#             }
#             for d in devices
#         ]
#     }


# # ── Profile Routes ────────────────────────────────────────────────────────────

# @app.put("/profile/body")
# def update_body_metrics(
#     payload: BodyMetricsRequest,
#     db: Session = Depends(get_db),
#     user: User  = Depends(get_current_user)
# ):
#     bmi = None
#     if payload.height and payload.weight:
#         height_m = payload.height / 100
#         bmi      = round(payload.weight / (height_m ** 2), 2)

#     metrics = db.query(UserBodyMetrics).filter(UserBodyMetrics.user_id == user.id).first()
#     if metrics:
#         metrics.age = payload.age; metrics.gender = payload.gender
#         metrics.height = payload.height; metrics.weight = payload.weight
#         metrics.bmi = bmi; metrics.body_fat_percentage = payload.body_fat_percentage
#         metrics.muscle_mass = payload.muscle_mass
#     else:
#         db.add(UserBodyMetrics(
#             user_id=user.id, age=payload.age, gender=payload.gender,
#             height=payload.height, weight=payload.weight, bmi=bmi,
#             body_fat_percentage=payload.body_fat_percentage,
#             muscle_mass=payload.muscle_mass
#         ))
#     db.commit()
#     return {"message": "Body metrics updated", "bmi": bmi}


# @app.get("/profile/body")
# def get_body_metrics(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
#     m = db.query(UserBodyMetrics).filter(UserBodyMetrics.user_id == user.id).first()
#     if not m:
#         raise HTTPException(404, "Body metrics not found")
#     return {"age": m.age, "gender": m.gender, "height": m.height, "weight": m.weight,
#             "bmi": m.bmi, "body_fat_percentage": m.body_fat_percentage, "muscle_mass": m.muscle_mass}


# @app.put("/profile/goals")
# def update_fitness_goals(
#     payload: FitnessGoalsRequest,
#     db: Session = Depends(get_db),
#     user: User  = Depends(get_current_user)
# ):
#     goals = db.query(UserFitnessGoals).filter(UserFitnessGoals.user_id == user.id).first()
#     if goals:
#         goals.goal = payload.goal; goals.target_weight = payload.target_weight
#         goals.target_days = payload.target_days; goals.workout_experience = payload.workout_experience
#         goals.gym_access = payload.gym_access; goals.workout_days_per_week = payload.workout_days_per_week
#         goals.preferred_workout_time = payload.preferred_workout_time
#     else:
#         db.add(UserFitnessGoals(
#             user_id=user.id, goal=payload.goal, target_weight=payload.target_weight,
#             target_days=payload.target_days, workout_experience=payload.workout_experience,
#             gym_access=payload.gym_access, workout_days_per_week=payload.workout_days_per_week,
#             preferred_workout_time=payload.preferred_workout_time
#         ))
#     db.commit()
#     return {"message": "Fitness goals updated"}


# @app.get("/profile/goals")
# def get_fitness_goals(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
#     g = db.query(UserFitnessGoals).filter(UserFitnessGoals.user_id == user.id).first()
#     if not g:
#         raise HTTPException(404, "Fitness goals not found")
#     return {"goal": g.goal, "target_weight": g.target_weight, "target_days": g.target_days,
#             "workout_experience": g.workout_experience, "gym_access": g.gym_access,
#             "workout_days_per_week": g.workout_days_per_week, "preferred_workout_time": g.preferred_workout_time}


# @app.put("/profile/lifestyle")
# def update_lifestyle(
#     payload: LifestyleRequest,
#     db: Session = Depends(get_db),
#     user: User  = Depends(get_current_user)
# ):
#     lifestyle = db.query(UserLifestyle).filter(UserLifestyle.user_id == user.id).first()
#     if lifestyle:
#         lifestyle.food_preference = payload.food_preference
#         lifestyle.water_intake = payload.water_intake; lifestyle.sleep_hours = payload.sleep_hours
#         lifestyle.activity_level = payload.activity_level; lifestyle.stress_level = payload.stress_level
#     else:
#         db.add(UserLifestyle(
#             user_id=user.id, food_preference=payload.food_preference,
#             water_intake=payload.water_intake, sleep_hours=payload.sleep_hours,
#             activity_level=payload.activity_level, stress_level=payload.stress_level
#         ))
#     db.commit()
#     return {"message": "Lifestyle updated"}


# @app.get("/profile/lifestyle")
# def get_lifestyle(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
#     l = db.query(UserLifestyle).filter(UserLifestyle.user_id == user.id).first()
#     if not l:
#         raise HTTPException(404, "Lifestyle info not found")
#     return {"food_preference": l.food_preference, "water_intake": l.water_intake,
#             "sleep_hours": l.sleep_hours, "activity_level": l.activity_level, "stress_level": l.stress_level}


# @app.put("/profile/health")
# def update_health(
#     payload: HealthRequest,
#     db: Session = Depends(get_db),
#     user: User  = Depends(get_current_user)
# ):
#     health = db.query(UserHealth).filter(UserHealth.user_id == user.id).first()
#     if health:
#         health.health_problems = payload.health_problems
#         health.injuries = payload.injuries; health.medications = payload.medications
#     else:
#         db.add(UserHealth(
#             user_id=user.id, health_problems=payload.health_problems,
#             injuries=payload.injuries, medications=payload.medications
#         ))
#     db.commit()
#     return {"message": "Health info updated"}


# @app.get("/profile/health")
# def get_health(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
#     h = db.query(UserHealth).filter(UserHealth.user_id == user.id).first()
#     if not h:
#         raise HTTPException(404, "Health info not found")
#     return {"health_problems": h.health_problems, "injuries": h.injuries, "medications": h.medications}


# @app.get("/profile/full")
# def get_full_profile(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
#     m = db.query(UserBodyMetrics).filter(UserBodyMetrics.user_id == user.id).first()
#     g = db.query(UserFitnessGoals).filter(UserFitnessGoals.user_id == user.id).first()
#     l = db.query(UserLifestyle).filter(UserLifestyle.user_id == user.id).first()
#     h = db.query(UserHealth).filter(UserHealth.user_id == user.id).first()

#     return {
#         "user":          user_response(user),
#         "body_metrics":  {"age": m.age if m else None, "gender": m.gender if m else None,
#                           "height": m.height if m else None, "weight": m.weight if m else None,
#                           "bmi": m.bmi if m else None, "body_fat_percentage": m.body_fat_percentage if m else None,
#                           "muscle_mass": m.muscle_mass if m else None},
#         "fitness_goals": {"goal": g.goal if g else None, "target_weight": g.target_weight if g else None,
#                           "target_days": g.target_days if g else None, "workout_experience": g.workout_experience if g else None,
#                           "gym_access": g.gym_access if g else None, "workout_days_per_week": g.workout_days_per_week if g else None,
#                           "preferred_workout_time": g.preferred_workout_time if g else None},
#         "lifestyle":     {"food_preference": l.food_preference if l else None, "water_intake": l.water_intake if l else None,
#                           "sleep_hours": l.sleep_hours if l else None, "activity_level": l.activity_level if l else None,
#                           "stress_level": l.stress_level if l else None},
#         "health":        {"health_problems": h.health_problems if h else None,
#                           "injuries": h.injuries if h else None, "medications": h.medications if h else None}
#     }


# # ── AI Routes ─────────────────────────────────────────────────────────────────

# @app.post("/ai/generate-workout")
# @limiter.limit("20/hour")
# def generate_workout(
#     request: Request,
#     db: Session = Depends(get_db),
#     user: User  = Depends(get_current_user)
# ):
#     m = db.query(UserBodyMetrics).filter(UserBodyMetrics.user_id == user.id).first()
#     g = db.query(UserFitnessGoals).filter(UserFitnessGoals.user_id == user.id).first()
#     l = db.query(UserLifestyle).filter(UserLifestyle.user_id == user.id).first()
#     h = db.query(UserHealth).filter(UserHealth.user_id == user.id).first()

#     profile = {
#         "user":          {"name": user.name, "preferred_language": user.preferred_language},
#         "body_metrics":  {"age": m.age if m else None, "gender": m.gender if m else None,
#                           "height": m.height if m else None, "weight": m.weight if m else None,
#                           "bmi": m.bmi if m else None, "body_fat_percentage": m.body_fat_percentage if m else None,
#                           "muscle_mass": m.muscle_mass if m else None},
#         "fitness_goals": {"goal": g.goal if g else None, "target_weight": g.target_weight if g else None,
#                           "target_days": g.target_days if g else None, "workout_experience": g.workout_experience if g else None,
#                           "gym_access": g.gym_access if g else None, "workout_days_per_week": g.workout_days_per_week if g else None,
#                           "preferred_workout_time": g.preferred_workout_time if g else None},
#         "lifestyle":     {"food_preference": l.food_preference if l else None, "water_intake": l.water_intake if l else None,
#                           "sleep_hours": l.sleep_hours if l else None, "activity_level": l.activity_level if l else None,
#                           "stress_level": l.stress_level if l else None},
#         "health":        {"health_problems": h.health_problems if h else None,
#                           "injuries": h.injuries if h else None, "medications": h.medications if h else None}
#     }

#     plan = generate_workout_plan(profile)
#     return {"message": "Workout plan generated", "plan": plan}






# ##___BEFORE___###
# import random
# from datetime import datetime, timedelta, timezone

# from fastapi import FastAPI, Depends, HTTPException, Response, Request
# from fastapi.middleware.cors import CORSMiddleware
# from slowapi.errors import RateLimitExceeded
# from sqlalchemy.orm import Session

# from database import Base, engine, get_db
# from models import (
#     User, RefreshToken,
#     # BlacklistedToken,       # uncomment after launch
#     UserBodyMetrics, UserFitnessGoals,
#     UserLifestyle, UserHealth
# )
# from schemas import (
#     SignUpRequest, LoginRequest, RefreshTokenRequest,
#     BodyMetricsRequest, FitnessGoalsRequest,
#     LifestyleRequest, HealthRequest, VerifyOTPRequest
# )
# from auth import (
#     hash_password, verify_password,
#     create_access_token, create_refresh_token,
#     verify_access_token,
#     COOKIE_SECURE, COOKIE_SAMESITE,
#     MAX_LOGIN_ATTEMPTS, LOCK_MINUTES,
#     ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS,
# )
# from modules.security import (
#     limiter, rate_limit_exceeded_handler,
#     sanitize_string, sanitize_email,
#     # get_device_info,              # uncomment after launch
#     # blacklist_token,              # uncomment after launch
#     # is_token_blacklisted,         # uncomment after launch
#     # is_new_device,                # uncomment after launch
#     # save_device,                  # uncomment after launch
#     # log_login_attempt,            # uncomment after launch
#     send_verification_email,
#     # send_otp_email,               # uncomment when 2FA enabled
#     # send_new_device_alert,        # uncomment after launch
#     generate_verification_token,
#     # generate_otp                  # uncomment when 2FA enabled
# )
# from modules.workout_generator import generate_workout_plan

# Base.metadata.create_all(bind=engine)

# app = FastAPI(title="Gym AI Agent")

# # ── Rate Limiter ──────────────────────────────────────────────────────────────
# app.state.limiter = limiter
# app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# # ── CORS ──────────────────────────────────────────────────────────────────────
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins     = ["http://localhost:5173", "http://localhost:3000"],
#     allow_credentials = True,
#     allow_methods     = ["GET", "POST", "PUT", "DELETE"],
#     allow_headers     = ["Content-Type", "Authorization"],
# )


# # ── Helpers ───────────────────────────────────────────────────────────────────

# def make_aware(dt: datetime) -> datetime:
#     if dt is not None and dt.tzinfo is None:
#         return dt.replace(tzinfo=timezone.utc)
#     return dt


# def set_auth_cookies(response: Response, access_token: str, refresh_token: str):
#     response.set_cookie(
#         key="access_token", value=access_token,
#         httponly=True, secure=COOKIE_SECURE,
#         samesite=COOKIE_SAMESITE,
#         max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60, path="/"
#     )
#     response.set_cookie(
#         key="refresh_token", value=refresh_token,
#         httponly=True, secure=COOKIE_SECURE,
#         samesite=COOKIE_SAMESITE,
#         max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60, path="/"
#     )


# def get_current_user(request: Request, db: Session = Depends(get_db)):
#     token = request.cookies.get("access_token")
#     if not token:
#         raise HTTPException(401, "Not authenticated")

#     # ── uncomment after launch ──
#     # if is_token_blacklisted(db, token):
#     #     raise HTTPException(401, "Token has been revoked")

#     payload = verify_access_token(token)
#     if not payload:
#         raise HTTPException(401, "Invalid or expired token")

#     user = db.query(User).filter(User.id == payload["user_id"]).first()
#     if not user:
#         raise HTTPException(404, "User not found")
#     if not user.is_verified:
#         raise HTTPException(403, "Please verify your email first")
#     return user


# def user_response(user: User) -> dict:
#     return {
#         "id":             user.id,
#         "name":           user.name,
#         "email":          user.email,
#         "is_verified":    user.is_verified,
#         "two_fa_enabled": user.two_fa_enabled
#     }


# # ── Auth Routes ───────────────────────────────────────────────────────────────

# @app.get("/")
# def home():
#     return {"message": "Gym AI Agent API is running"}


# @app.post("/signup")
# @limiter.limit("5/hour")
# async def signup(
#     request: Request,
#     payload: SignUpRequest,
#     db: Session = Depends(get_db)
# ):
#     name  = sanitize_string(payload.name)
#     email = sanitize_email(payload.email)

#     existing = db.query(User).filter(User.email == email).first()
#     if existing:
#         raise HTTPException(400, "Email already registered")

#     verify_token   = generate_verification_token()
#     verify_expires = datetime.now(timezone.utc) + timedelta(hours=24)

#     user = User(
#         name                 = name,
#         email                = email,
#         password_hash        = hash_password(payload.password),
#         is_verified          = False,
#         verification_token   = verify_token,
#         verification_expires = verify_expires
#     )
#     db.add(user)
#     db.commit()
#     db.refresh(user)

#     await send_verification_email(user.email, user.name, verify_token)

#     return {"message": "Signup successful. Please check your email to verify your account."}


# @app.get("/verify-email")
# def verify_email(token: str, db: Session = Depends(get_db)):
#     user = db.query(User).filter(User.verification_token == token).first()
#     if not user:
#         raise HTTPException(400, "Invalid verification token")

#     if make_aware(user.verification_expires) < datetime.now(timezone.utc):
#         raise HTTPException(400, "Verification link expired. Please request a new one.")

#     user.is_verified          = True
#     user.verification_token   = None
#     user.verification_expires = None
#     db.commit()

#     return {"message": "Email verified successfully. You can now login!"}


# @app.post("/resend-verification")
# @limiter.limit("3/hour")
# async def resend_verification(
#     request: Request,
#     email: str,
#     db: Session = Depends(get_db)
# ):
#     user = db.query(User).filter(User.email == email).first()
#     if not user:
#         raise HTTPException(404, "User not found")
#     if user.is_verified:
#         raise HTTPException(400, "Email already verified")

#     verify_token              = generate_verification_token()
#     user.verification_token   = verify_token
#     user.verification_expires = datetime.now(timezone.utc) + timedelta(hours=24)
#     db.commit()

#     await send_verification_email(user.email, user.name, verify_token)
#     return {"message": "Verification email resent. Please check your inbox."}


# @app.post("/login")
# @limiter.limit("10/minute")
# async def login(
#     request: Request,
#     payload: LoginRequest,
#     response: Response,
#     db: Session = Depends(get_db)
# ):
#     # device_info = get_device_info(request)   # uncomment after launch
#     email = sanitize_email(payload.email)
#     user  = db.query(User).filter(User.email == email).first()

#     if not user:
#         raise HTTPException(401, "Invalid credentials")

#     if not user.is_verified:
#         raise HTTPException(403, "Please verify your email before logging in")

#     now = datetime.now(timezone.utc)

#     # Check lock
#     if user.lock_until and make_aware(user.lock_until) > now:
#         remaining = (make_aware(user.lock_until) - now).seconds // 60
#         # log_login_attempt(db, user.id, device_info, "blocked", "Account locked")  # uncomment after launch
#         raise HTTPException(423, f"Account locked. Try again in {remaining} minutes.")

#     # Wrong password
#     if not verify_password(payload.password, user.password_hash):
#         user.failed_login_attempts += 1
#         # user.last_failed_ip = device_info["ip_address"]   # uncomment after launch

#         if user.failed_login_attempts >= MAX_LOGIN_ATTEMPTS:
#             user.lock_until            = now + timedelta(minutes=LOCK_MINUTES)
#             user.failed_login_attempts = 0
#             db.commit()
#             # log_login_attempt(db, user.id, device_info, "blocked", "Too many attempts")  # uncomment after launch
#             raise HTTPException(423, f"Too many failed attempts. Locked for {LOCK_MINUTES} minutes.")

#         db.commit()
#         # log_login_attempt(db, user.id, device_info, "failed", "Wrong password")  # uncomment after launch
#         raise HTTPException(401, "Invalid credentials")

#     # Reset on success
#     user.failed_login_attempts = 0
#     user.lock_until            = None
#     user.last_login_at         = now
#     db.commit()

#     # ── uncomment after launch ──
#     # new_device = is_new_device(db, user.id, device_info["device_id"])
#     # if new_device:
#     #     await send_new_device_alert(user.email, user.name, device_info)
#     # save_device(db, user.id, device_info)

#     # ── uncomment when 2FA ready ──
#     # if user.two_fa_enabled:
#     #     otp                     = generate_otp()
#     #     user.two_fa_otp         = otp
#     #     user.two_fa_otp_expires = now + timedelta(minutes=10)
#     #     db.commit()
#     #     await send_otp_email(user.email, user.name, otp)
#     #     log_login_attempt(db, user.id, device_info, "2fa_pending", "OTP sent")
#     #     return {"message": "OTP sent to your email", "two_fa_required": True}

#     # Issue tokens
#     access_token              = create_access_token({"user_id": user.id, "email": user.email})
#     refresh_token_str, exp_at = create_refresh_token()

#     db.add(RefreshToken(
#         user_id    = user.id,
#         token      = refresh_token_str,
#         expires_at = exp_at,
#         # device_id = device_info["device_id"]   # uncomment after launch
#     ))
#     db.commit()

#     set_auth_cookies(response, access_token, refresh_token_str)
#     # log_login_attempt(db, user.id, device_info, "success", None)   # uncomment after launch

#     return {"message": "Login successful", "two_fa_required": False, "user": user_response(user)}


# # ── uncomment when 2FA ready ──────────────────────────────────────────────────
# # @app.post("/verify-otp")
# # @limiter.limit("5/minute")
# # def verify_otp(
# #     request: Request,
# #     payload: VerifyOTPRequest,
# #     response: Response,
# #     db: Session = Depends(get_db)
# # ):
# #     user = db.query(User).filter(User.email == payload.email).first()
# #     if not user:
# #         raise HTTPException(404, "User not found")
# #     now = datetime.now(timezone.utc)
# #     if not user.two_fa_otp or user.two_fa_otp != payload.otp:
# #         raise HTTPException(401, "Invalid OTP")
# #     if make_aware(user.two_fa_otp_expires) < now:
# #         raise HTTPException(401, "OTP expired. Please login again.")
# #     user.two_fa_otp         = None
# #     user.two_fa_otp_expires = None
# #     db.commit()
# #     access_token              = create_access_token({"user_id": user.id, "email": user.email})
# #     refresh_token_str, exp_at = create_refresh_token()
# #     db.add(RefreshToken(user_id=user.id, token=refresh_token_str, expires_at=exp_at))
# #     db.commit()
# #     set_auth_cookies(response, access_token, refresh_token_str)
# #     return {"message": "OTP verified. Login successful.", "user": user_response(user)}


# @app.post("/refresh")
# def refresh(request: Request, response: Response, db: Session = Depends(get_db)):
#     token = request.cookies.get("refresh_token")
#     if not token:
#         raise HTTPException(401, "Refresh token missing")

#     now      = datetime.now(timezone.utc)
#     db_token = db.query(RefreshToken).filter(
#         RefreshToken.token      == token,
#         RefreshToken.is_revoked == False
#     ).first()

#     if not db_token:
#         raise HTTPException(401, "Invalid or revoked refresh token")

#     if make_aware(db_token.expires_at) < now:
#         raise HTTPException(401, "Refresh token expired. Please login again.")

#     db_token.is_revoked       = True
#     access_token              = create_access_token({"user_id": db_token.user_id})
#     refresh_token_str, exp_at = create_refresh_token()

#     db.add(RefreshToken(user_id=db_token.user_id, token=refresh_token_str, expires_at=exp_at))
#     db.commit()

#     set_auth_cookies(response, access_token, refresh_token_str)

#     user = db.query(User).filter(User.id == db_token.user_id).first()
#     return {"message": "Token refreshed", "user": user_response(user)}


# @app.post("/logout")
# def logout(request: Request, response: Response, db: Session = Depends(get_db)):
#     # ── uncomment after launch ──
#     # access_token = request.cookies.get("access_token")
#     # if access_token:
#     #     payload = verify_access_token(access_token)
#     #     if payload:
#     #         blacklist_token(db, payload["user_id"], access_token, "logout")

#     refresh_token_val = request.cookies.get("refresh_token")
#     if refresh_token_val:
#         db_token = db.query(RefreshToken).filter(
#             RefreshToken.token == refresh_token_val
#         ).first()
#         if db_token:
#             db_token.is_revoked = True
#             db.commit()

#     response.delete_cookie("access_token")
#     response.delete_cookie("refresh_token")
#     return {"message": "Logged out successfully"}


# @app.get("/me")
# def get_me(user: User = Depends(get_current_user)):
#     return {"message": "User fetched", "user": user_response(user)}


# # ── 2FA — uncomment after launch ─────────────────────────────────────────────
# # @app.post("/enable-2fa")
# # def enable_2fa(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
# #     user.two_fa_enabled = True
# #     db.commit()
# #     return {"message": "2FA enabled"}

# # @app.post("/disable-2fa")
# # def disable_2fa(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
# #     user.two_fa_enabled     = False
# #     user.two_fa_otp         = None
# #     user.two_fa_otp_expires = None
# #     db.commit()
# #     return {"message": "2FA disabled"}


# # ── Device + History — uncomment after launch ─────────────────────────────────
# # @app.get("/login-history")
# # def get_login_history(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
# #     from models import LoginHistory
# #     history = db.query(LoginHistory).filter(
# #         LoginHistory.user_id == user.id
# #     ).order_by(LoginHistory.logged_at.desc()).limit(20).all()
# #     return {"history": [{"ip_address": h.ip_address, "device_name": h.device_name,
# #                          "browser": h.browser, "os": h.os, "status": h.status,
# #                          "reason": h.reason, "logged_at": h.logged_at} for h in history]}

# # @app.get("/trusted-devices")
# # def get_trusted_devices(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
# #     from models import UserDevice
# #     devices = db.query(UserDevice).filter(UserDevice.user_id == user.id).all()
# #     return {"devices": [{"device_id": d.device_id, "device_name": d.device_name,
# #                          "browser": d.browser, "os": d.os, "ip_address": d.ip_address,
# #                          "is_trusted": d.is_trusted, "last_used_at": d.last_used_at} for d in devices]}


# # ── Profile Routes ────────────────────────────────────────────────────────────

# @app.put("/profile/body")
# def update_body_metrics(
#     payload: BodyMetricsRequest,
#     db: Session = Depends(get_db),
#     user: User  = Depends(get_current_user)
# ):
#     bmi = None
#     if payload.height and payload.weight:
#         height_m = payload.height / 100
#         bmi      = round(payload.weight / (height_m ** 2), 2)

#     metrics = db.query(UserBodyMetrics).filter(UserBodyMetrics.user_id == user.id).first()
#     if metrics:
#         metrics.age = payload.age; metrics.gender = payload.gender
#         metrics.height = payload.height; metrics.weight = payload.weight
#         metrics.bmi = bmi; metrics.body_fat_percentage = payload.body_fat_percentage
#         metrics.muscle_mass = payload.muscle_mass
#     else:
#         db.add(UserBodyMetrics(
#             user_id=user.id, age=payload.age, gender=payload.gender,
#             height=payload.height, weight=payload.weight, bmi=bmi,
#             body_fat_percentage=payload.body_fat_percentage,
#             muscle_mass=payload.muscle_mass
#         ))
#     db.commit()
#     return {"message": "Body metrics updated", "bmi": bmi}


# @app.get("/profile/body")
# def get_body_metrics(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
#     m = db.query(UserBodyMetrics).filter(UserBodyMetrics.user_id == user.id).first()
#     if not m:
#         raise HTTPException(404, "Body metrics not found")
#     return {"age": m.age, "gender": m.gender, "height": m.height,
#             "weight": m.weight, "bmi": m.bmi,
#             "body_fat_percentage": m.body_fat_percentage, "muscle_mass": m.muscle_mass}


# @app.put("/profile/goals")
# def update_fitness_goals(
#     payload: FitnessGoalsRequest,
#     db: Session = Depends(get_db),
#     user: User  = Depends(get_current_user)
# ):
#     goals = db.query(UserFitnessGoals).filter(UserFitnessGoals.user_id == user.id).first()
#     if goals:
#         goals.goal = payload.goal; goals.target_weight = payload.target_weight
#         goals.target_days = payload.target_days
#         goals.workout_experience = payload.workout_experience
#         goals.gym_access = payload.gym_access
#         goals.workout_days_per_week = payload.workout_days_per_week
#         goals.preferred_workout_time = payload.preferred_workout_time
#     else:
#         db.add(UserFitnessGoals(
#             user_id=user.id, goal=payload.goal,
#             target_weight=payload.target_weight,
#             target_days=payload.target_days,
#             workout_experience=payload.workout_experience,
#             gym_access=payload.gym_access,
#             workout_days_per_week=payload.workout_days_per_week,
#             preferred_workout_time=payload.preferred_workout_time
#         ))
#     db.commit()
#     return {"message": "Fitness goals updated"}


# @app.get("/profile/goals")
# def get_fitness_goals(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
#     g = db.query(UserFitnessGoals).filter(UserFitnessGoals.user_id == user.id).first()
#     if not g:
#         raise HTTPException(404, "Fitness goals not found")
#     return {"goal": g.goal, "target_weight": g.target_weight,
#             "target_days": g.target_days, "workout_experience": g.workout_experience,
#             "gym_access": g.gym_access, "workout_days_per_week": g.workout_days_per_week,
#             "preferred_workout_time": g.preferred_workout_time}


# @app.put("/profile/lifestyle")
# def update_lifestyle(
#     payload: LifestyleRequest,
#     db: Session = Depends(get_db),
#     user: User  = Depends(get_current_user)
# ):
#     lifestyle = db.query(UserLifestyle).filter(UserLifestyle.user_id == user.id).first()
#     if lifestyle:
#         lifestyle.food_preference = payload.food_preference
#         lifestyle.water_intake    = payload.water_intake
#         lifestyle.sleep_hours     = payload.sleep_hours
#         lifestyle.activity_level  = payload.activity_level
#         lifestyle.stress_level    = payload.stress_level
#     else:
#         db.add(UserLifestyle(
#             user_id=user.id, food_preference=payload.food_preference,
#             water_intake=payload.water_intake, sleep_hours=payload.sleep_hours,
#             activity_level=payload.activity_level, stress_level=payload.stress_level
#         ))
#     db.commit()
#     return {"message": "Lifestyle updated"}


# @app.get("/profile/lifestyle")
# def get_lifestyle(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
#     l = db.query(UserLifestyle).filter(UserLifestyle.user_id == user.id).first()
#     if not l:
#         raise HTTPException(404, "Lifestyle info not found")
#     return {"food_preference": l.food_preference, "water_intake": l.water_intake,
#             "sleep_hours": l.sleep_hours, "activity_level": l.activity_level,
#             "stress_level": l.stress_level}


# @app.put("/profile/health")
# def update_health(
#     payload: HealthRequest,
#     db: Session = Depends(get_db),
#     user: User  = Depends(get_current_user)
# ):
#     health = db.query(UserHealth).filter(UserHealth.user_id == user.id).first()
#     if health:
#         health.health_problems = payload.health_problems
#         health.injuries        = payload.injuries
#         health.medications     = payload.medications
#     else:
#         db.add(UserHealth(
#             user_id=user.id, health_problems=payload.health_problems,
#             injuries=payload.injuries, medications=payload.medications
#         ))
#     db.commit()
#     return {"message": "Health info updated"}


# @app.get("/profile/health")
# def get_health(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
#     h = db.query(UserHealth).filter(UserHealth.user_id == user.id).first()
#     if not h:
#         raise HTTPException(404, "Health info not found")
#     return {"health_problems": h.health_problems,
#             "injuries": h.injuries, "medications": h.medications}


# @app.get("/profile/full")
# def get_full_profile(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
#     m = db.query(UserBodyMetrics).filter(UserBodyMetrics.user_id == user.id).first()
#     g = db.query(UserFitnessGoals).filter(UserFitnessGoals.user_id == user.id).first()
#     l = db.query(UserLifestyle).filter(UserLifestyle.user_id == user.id).first()
#     h = db.query(UserHealth).filter(UserHealth.user_id == user.id).first()

#     return {
#         "user":          user_response(user),
#         "body_metrics":  {
#             "age": m.age if m else None, "gender": m.gender if m else None,
#             "height": m.height if m else None, "weight": m.weight if m else None,
#             "bmi": m.bmi if m else None,
#             "body_fat_percentage": m.body_fat_percentage if m else None,
#             "muscle_mass": m.muscle_mass if m else None
#         },
#         "fitness_goals": {
#             "goal": g.goal if g else None,
#             "target_weight": g.target_weight if g else None,
#             "target_days": g.target_days if g else None,
#             "workout_experience": g.workout_experience if g else None,
#             "gym_access": g.gym_access if g else None,
#             "workout_days_per_week": g.workout_days_per_week if g else None,
#             "preferred_workout_time": g.preferred_workout_time if g else None
#         },
#         "lifestyle":     {
#             "food_preference": l.food_preference if l else None,
#             "water_intake": l.water_intake if l else None,
#             "sleep_hours": l.sleep_hours if l else None,
#             "activity_level": l.activity_level if l else None,
#             "stress_level": l.stress_level if l else None
#         },
#         "health":        {
#             "health_problems": h.health_problems if h else None,
#             "injuries": h.injuries if h else None,
#             "medications": h.medications if h else None
#         }
#     }


# # ── AI Routes ─────────────────────────────────────────────────────────────────

# @app.post("/ai/generate-workout")
# @limiter.limit("20/hour")
# def generate_workout(
#     request: Request,
#     db: Session = Depends(get_db),
#     user: User  = Depends(get_current_user)
# ):
#     m = db.query(UserBodyMetrics).filter(UserBodyMetrics.user_id == user.id).first()
#     g = db.query(UserFitnessGoals).filter(UserFitnessGoals.user_id == user.id).first()
#     l = db.query(UserLifestyle).filter(UserLifestyle.user_id == user.id).first()
#     h = db.query(UserHealth).filter(UserHealth.user_id == user.id).first()

#     profile = {
#         "user":          {"name": user.name, "preferred_language": user.preferred_language},
#         "body_metrics":  {
#             "age": m.age if m else None, "gender": m.gender if m else None,
#             "height": m.height if m else None, "weight": m.weight if m else None,
#             "bmi": m.bmi if m else None,
#             "body_fat_percentage": m.body_fat_percentage if m else None,
#             "muscle_mass": m.muscle_mass if m else None
#         },
#         "fitness_goals": {
#             "goal": g.goal if g else None,
#             "target_weight": g.target_weight if g else None,
#             "target_days": g.target_days if g else None,
#             "workout_experience": g.workout_experience if g else None,
#             "gym_access": g.gym_access if g else None,
#             "workout_days_per_week": g.workout_days_per_week if g else None,
#             "preferred_workout_time": g.preferred_workout_time if g else None
#         },
#         "lifestyle":     {
#             "food_preference": l.food_preference if l else None,
#             "water_intake": l.water_intake if l else None,
#             "sleep_hours": l.sleep_hours if l else None,
#             "activity_level": l.activity_level if l else None,
#             "stress_level": l.stress_level if l else None
#         },
#         "health":        {
#             "health_problems": h.health_problems if h else None,
#             "injuries": h.injuries if h else None,
#             "medications": h.medications if h else None
#         }
#     }

#     plan = generate_workout_plan(profile)
#     return {"message": "Workout plan generated", "plan": plan}



###___WITHOUT__LOGIN__####

from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, Depends, HTTPException, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from sqlalchemy.orm import Session
from schemas import ForgotPasswordRequest

from database import Base, engine, get_db
from models import (
    User, RefreshToken,
    UserBodyMetrics, UserFitnessGoals,
    UserLifestyle, UserHealth, WorkoutPlan
)
from schemas import (
    SignUpRequest, LoginRequest, RefreshTokenRequest,
    BodyMetricsRequest, FitnessGoalsRequest,
    LifestyleRequest, HealthRequest, VerifyOTPRequest
)


from modules.diet_plan.models import DietPreference, DietPlan
from modules.diet_plan import router as diet_router

from fastapi import BackgroundTasks

from auth import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
    verify_access_token,
    COOKIE_SECURE, COOKIE_SAMESITE,
    MAX_LOGIN_ATTEMPTS, LOCK_MINUTES,
    ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS,
)
from modules.security import (
    limiter, rate_limit_exceeded_handler,
    sanitize_string, sanitize_email,
    send_otp_email,
    generate_otp,
)


########__CHAT___####
from modules.chat.models import UserLocation, UserConnection, ChatRoom, ChatMessage

##___TRAINER___####
from modules.trainer.models import UserRole, TrainerProfile, TrainerClient, TrainerReview
from modules.workout_generator import generate_workout_plan

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Gym AI Agent")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins     = ["http://localhost:5173", "http://localhost:3000"],
#     allow_credentials = True,
#     allow_methods     = ["GET", "POST", "PUT", "DELETE"],
#     allow_headers     = ["Content-Type", "Authorization"],
# )

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://192.168.0.111:5173"
        "http://192.168.0.112:5173",  # ← Manoj's Mac
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept"],
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_aware(dt: datetime) -> datetime:
    if dt is not None and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def set_auth_cookies(response: Response, access_token: str, refresh_token: str):
    response.set_cookie(
        key="access_token", value=access_token,
        httponly=True, secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60, path="/"
    )
    response.set_cookie(
        key="refresh_token", value=refresh_token,
        httponly=True, secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60, path="/"
    )


# ── Real Auth — JWT ───────────────────────────────────────────────────────────
def get_current_user(request: Request, db: Session = Depends(get_db)):
    # Try cookie first
    token = request.cookies.get("access_token")

    # If no cookie → try Authorization header (Bearer token)
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

    if not token:
        raise HTTPException(401, "Not authenticated")

    payload = verify_access_token(token)
    if not payload:
        raise HTTPException(401, "Invalid or expired token")

    user = db.query(User).filter(User.id == payload["user_id"]).first()
    if not user:
        raise HTTPException(404, "User not found")
    if not user.is_verified:
        raise HTTPException(403, "Please verify your email first")

    return user


def user_response(user: User) -> dict:
    return {
        "id":             user.id,
        "name":           user.name,
        "email":          user.email,
        "is_verified":    user.is_verified,
        "two_fa_enabled": user.two_fa_enabled
    }


# ── Home ──────────────────────────────────────────────────────────────────────

@app.get("/")
def home():
    return {"message": "Gym AI Agent API is running"}


# ── Signup ────────────────────────────────────────────────────────────────────

@app.post("/signup")
@limiter.limit("100/hour")
async def signup(
    request: Request,
    payload: SignUpRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    name  = sanitize_string(payload.name)
    email = sanitize_email(payload.email)

    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(400, "Email already registered")

    # Generate OTP
    otp          = generate_otp()
    otp_expires  = datetime.now(timezone.utc) + timedelta(minutes=10)

    user = User(
        name                 = name,
        email                = email,
        password_hash        = hash_password(payload.password),
        is_verified          = False,
        verification_token   = otp,
        verification_expires = otp_expires
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    await send_otp_email(user.email, user.name, otp)
    return {
        "message": "OTP sent to your email. Enter OTP to complete signup.",
        "email":   email
    }

# ── Email Verification ────────────────────────────────────────────────────────
@app.post("/verify-signup-otp")
def verify_signup_otp(
    payload: VerifyOTPRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    email = sanitize_email(payload.email)
    user  = db.query(User).filter(User.email == email).first()

    if not user:
        raise HTTPException(404, "User not found")
    if user.is_verified:
        raise HTTPException(400, "Account already verified. Please login.")

    now = datetime.now(timezone.utc)

    if not user.verification_token or user.verification_token != payload.otp:
        raise HTTPException(401, "Invalid OTP")

    if make_aware(user.verification_expires) < now:
        raise HTTPException(401, "OTP expired. Please signup again.")

    # Mark verified
    user.is_verified          = True
    user.verification_token   = None
    user.verification_expires = None
    db.commit()

    # Issue tokens — logged in immediately
    access_token              = create_access_token({"user_id": user.id, "email": user.email})
    refresh_token_str, exp_at = create_refresh_token()

    db.add(RefreshToken(user_id=user.id, token=refresh_token_str, expires_at=exp_at))
    db.commit()

    set_auth_cookies(response, access_token, refresh_token_str)

    return {
        "message":      "Account verified. You are now logged in ✅",
        "access_token": access_token,        # ← return in body
        "user":         user_response(user)
    }
    
@app.post("/resend-otp")
@limiter.limit("100/hour")
async def resend_otp(
    request: Request,
    email: str,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(404, "User not found")
    if user.is_verified:
        raise HTTPException(400, "Account already verified. Please login.")

    otp                       = generate_otp()
    user.verification_token   = otp
    user.verification_expires = datetime.now(timezone.utc) + timedelta(minutes=10)
    db.commit()

    await send_otp_email(user.email, user.name, otp)
    return {"message": "New OTP sent to your email."}





# ── Forgot Password ───────────────────────────────────────────────────────────
@app.post("/forgot-password")
@limiter.limit("5/hour")
async def forgot_password(
    request:          Request,
    payload:          ForgotPasswordRequest,      # ← JSON body ✅
    background_tasks: BackgroundTasks,             # ← background ✅
    db:               Session = Depends(get_db)
):
    email = payload.email.strip().lower()

    user = db.query(User).filter(
        User.email == email
    ).first()

    if not user:
        return {"message": "If this email is registered you will receive an OTP ✅"}

    otp         = generate_otp()
    otp_expires = datetime.now(timezone.utc) + timedelta(minutes=10)

    user.verification_token   = otp
    user.verification_expires = otp_expires
    db.commit()

    # Background — no waiting ✅
    background_tasks.add_task(
        send_otp_email,
        user.email,
        user.name,
        otp
    )

    return {"message": "If this email is registered you will receive an OTP ✅"}
# ── Verify Reset OTP ──────────────────────────────────────────────────────────

@app.post("/verify-reset-otp")
def verify_reset_otp(
    email: str,
    otp:   str,
    db:    Session = Depends(get_db)
):
    import secrets

    user = db.query(User).filter(
        User.email == email.strip().lower()
    ).first()

    if not user:
        raise HTTPException(400, "Invalid request")

    if not user.verification_token:
        raise HTTPException(400, "No OTP requested. Please request a new one.")

    now = datetime.now(timezone.utc)
    if make_aware(user.verification_expires) < now:
        raise HTTPException(400, "OTP expired. Please request a new one.")

    if user.verification_token != otp.strip():
        raise HTTPException(400, "Invalid OTP")

    # Generate reset token
    reset_token               = secrets.token_hex(32)
    user.verification_token   = f"RESET_{reset_token}"
    user.verification_expires = datetime.now(timezone.utc) + timedelta(minutes=15)
    db.commit()

    return {
        "message":     "OTP verified ✅",
        "reset_token": reset_token
    }


# ── Reset Password ────────────────────────────────────────────────────────────

@app.post("/reset-password")
def reset_password(
    email:        str,
    reset_token:  str,
    new_password: str,
    db:           Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.email == email.strip().lower()
    ).first()

    if not user:
        raise HTTPException(400, "Invalid request")

    if not user.verification_token or \
       not user.verification_token.startswith("RESET_"):
        raise HTTPException(400, "Invalid reset token. Please start over.")

    now = datetime.now(timezone.utc)
    if make_aware(user.verification_expires) < now:
        raise HTTPException(400, "Reset token expired. Please start over.")

    stored_token = user.verification_token.replace("RESET_", "")
    if stored_token != reset_token.strip():
        raise HTTPException(400, "Invalid reset token")

    if len(new_password) < 8:
        raise HTTPException(400, "Password must be at least 8 characters")

    # Update password
    user.password_hash         = hash_password(new_password)
    user.verification_token    = None
    user.verification_expires  = None
    user.failed_login_attempts = 0
    user.lock_until            = None
    user.password_changed_at   = datetime.now(timezone.utc)
    db.commit()

    return {"message": "Password reset successfully ✅"}


# ── Resend Reset OTP ──────────────────────────────────────────────────────────

@app.post("/resend-reset-otp")
@limiter.limit("3/hour")
async def resend_reset_otp(
    request: Request,
    email:   str,
    db:      Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.email == email.strip().lower()
    ).first()

    if not user:
        return {"message": "If this email is registered you will receive an OTP ✅"}

    otp         = generate_otp()
    otp_expires = datetime.now(timezone.utc) + timedelta(minutes=10)

    user.verification_token   = otp
    user.verification_expires = otp_expires
    db.commit()

    await send_otp_email(user.email, user.name, otp)

    return {"message": "New OTP sent ✅"}



# ── Login ─────────────────────────────────────────────────────────────────────

@app.post("/login")
@limiter.limit("10/minute")
async def login(
    request: Request,
    payload: LoginRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    email = sanitize_email(payload.email)
    user  = db.query(User).filter(User.email == email).first()

    if not user:
        raise HTTPException(401, "Invalid credentials")

    if not user.is_verified:
        raise HTTPException(403, "Please verify your email before logging in")

    now = datetime.now(timezone.utc)

    # Check lock
    if user.lock_until and make_aware(user.lock_until) > now:
        remaining = (make_aware(user.lock_until) - now).seconds // 60
        raise HTTPException(423, f"Account locked. Try again in {remaining} minutes.")

    # Wrong password
    if not verify_password(payload.password, user.password_hash):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= MAX_LOGIN_ATTEMPTS:
            user.lock_until            = now + timedelta(minutes=LOCK_MINUTES)
            user.failed_login_attempts = 0
            db.commit()
            raise HTTPException(423, f"Too many failed attempts. Locked for {LOCK_MINUTES} minutes.")
        db.commit()
        raise HTTPException(401, "Invalid credentials")

    # Success
    user.failed_login_attempts = 0
    user.lock_until            = None
    user.last_login_at         = now
    db.commit()

    # ── uncomment after launch ──
    # new_device = is_new_device(db, user.id, device_info["device_id"])
    # if new_device:
    #     await send_new_device_alert(user.email, user.name, device_info)
    # save_device(db, user.id, device_info)

    # ── uncomment when 2FA ready ──
    # if user.two_fa_enabled:
    #     otp                     = generate_otp()
    #     user.two_fa_otp         = otp
    #     user.two_fa_otp_expires = now + timedelta(minutes=10)
    #     db.commit()
    #     await send_otp_email(user.email, user.name, otp)
    #     return {"message": "OTP sent to your email", "two_fa_required": True}

    # Send OTP instead of issuing token directly
    # Issue tokens directly — no OTP needed
    access_token              = create_access_token({"user_id": user.id, "email": user.email})
    refresh_token_str, exp_at = create_refresh_token()

    db.add(RefreshToken(
        user_id    = user.id,
        token      = refresh_token_str,
        expires_at = exp_at
    ))
    db.commit()

    set_auth_cookies(response, access_token, refresh_token_str)
    return {
        "message":      "Login successful ✅",
        "access_token": access_token,
        "user":         user_response(user)
    }



# @app.post("/verify-login-otp")
# @limiter.limit("100/minute")
# def verify_login_otp(
#     request: Request,
#     payload: VerifyOTPRequest,
#     response: Response,
#     db: Session = Depends(get_db)
# ):
#     email = sanitize_email(payload.email)
#     user  = db.query(User).filter(User.email == email).first()

#     if not user:
#         raise HTTPException(404, "User not found")

#     now = datetime.now(timezone.utc)

#     if not user.two_fa_otp:
#         raise HTTPException(401, "No OTP found. Please login again.")

#     if user.two_fa_otp != payload.otp:
#         raise HTTPException(401, "Invalid OTP")

#     if make_aware(user.two_fa_otp_expires) < now:
#         raise HTTPException(401, "OTP expired. Please login again.")

#     user.two_fa_otp         = None
#     user.two_fa_otp_expires = None
#     user.last_login_at      = now
#     db.commit()

#     access_token              = create_access_token({"user_id": user.id, "email": user.email})
#     refresh_token_str, exp_at = create_refresh_token()

#     db.add(RefreshToken(
#         user_id    = user.id,
#         token      = refresh_token_str,
#         expires_at = exp_at
#     ))
#     db.commit()

#     set_auth_cookies(response, access_token, refresh_token_str)

#     return {
#         "message":      "Login successful ✅",
#         "access_token": access_token,        # ← return in body
#         "user":         user_response(user)
#     }

# # Resend login OTP
# @app.post("/resend-login-otp")
# @limiter.limit("100/hour")
# async def resend_login_otp(
#     request: Request,
#     email: str,
#     db: Session = Depends(get_db)
# ):
#     user = db.query(User).filter(User.email == email).first()
#     if not user:
#         raise HTTPException(404, "User not found")
#     if not user.is_verified:
#         raise HTTPException(403, "Account not verified")

#     otp                     = generate_otp()
#     user.two_fa_otp         = otp
#     user.two_fa_otp_expires = datetime.now(timezone.utc) + timedelta(minutes=10)
#     db.commit()

#     await send_otp_email(user.email, user.name, otp)
#     return {"message": "New login OTP sent to your email."}


# ── Refresh ───────────────────────────────────────────────────────────────────

@app.post("/refresh")
def refresh(request: Request, response: Response, db: Session = Depends(get_db)):
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(401, "Refresh token missing")

    now      = datetime.now(timezone.utc)
    db_token = db.query(RefreshToken).filter(
        RefreshToken.token      == token,
        RefreshToken.is_revoked == False
    ).first()

    if not db_token:
        raise HTTPException(401, "Invalid or revoked refresh token")

    if make_aware(db_token.expires_at) < now:
        raise HTTPException(401, "Refresh token expired. Please login again.")

    db_token.is_revoked       = True
    access_token              = create_access_token({"user_id": db_token.user_id})
    refresh_token_str, exp_at = create_refresh_token()

    db.add(RefreshToken(user_id=db_token.user_id, token=refresh_token_str, expires_at=exp_at))
    db.commit()

    set_auth_cookies(response, access_token, refresh_token_str)
    user = db.query(User).filter(User.id == db_token.user_id).first()
    return {"message": "Token refreshed", "user": user_response(user)}


# ── Logout ────────────────────────────────────────────────────────────────────

@app.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    # ── uncomment after launch ──
    # access_token = request.cookies.get("access_token")
    # if access_token:
    #     payload = verify_access_token(access_token)
    #     if payload:
    #         blacklist_token(db, payload["user_id"], access_token, "logout")

    refresh_token_val = request.cookies.get("refresh_token")
    if refresh_token_val:
        db_token = db.query(RefreshToken).filter(
            RefreshToken.token == refresh_token_val
        ).first()
        if db_token:
            db_token.is_revoked = True
            db.commit()

    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"message": "Logged out successfully"}


# ── Me ────────────────────────────────────────────────────────────────────────

@app.get("/me")
def get_me(user: User = Depends(get_current_user)):
    return {"message": "User fetched", "user": user_response(user)}


# ── COMMENTED — uncomment after launch ───────────────────────────────────────

# @app.post("/enable-2fa")
# def enable_2fa(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
#     user.two_fa_enabled = True
#     db.commit()
#     return {"message": "2FA enabled"}

# @app.post("/disable-2fa")
# def disable_2fa(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
#     user.two_fa_enabled     = False
#     user.two_fa_otp         = None
#     user.two_fa_otp_expires = None
#     db.commit()
#     return {"message": "2FA disabled"}

# @app.post("/verify-otp")
# def verify_otp(request: Request, payload: VerifyOTPRequest, response: Response, db: Session = Depends(get_db)):
#     user = db.query(User).filter(User.email == payload.email).first()
#     if not user:
#         raise HTTPException(404, "User not found")
#     now = datetime.now(timezone.utc)
#     if not user.two_fa_otp or user.two_fa_otp != payload.otp:
#         raise HTTPException(401, "Invalid OTP")
#     if make_aware(user.two_fa_otp_expires) < now:
#         raise HTTPException(401, "OTP expired. Please login again.")
#     user.two_fa_otp         = None
#     user.two_fa_otp_expires = None
#     db.commit()
#     access_token              = create_access_token({"user_id": user.id, "email": user.email})
#     refresh_token_str, exp_at = create_refresh_token()
#     db.add(RefreshToken(user_id=user.id, token=refresh_token_str, expires_at=exp_at))
#     db.commit()
#     set_auth_cookies(response, access_token, refresh_token_str)
#     return {"message": "OTP verified. Login successful.", "user": user_response(user)}

# @app.get("/login-history")
# def get_login_history(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
#     from models import LoginHistory
#     history = db.query(LoginHistory).filter(
#         LoginHistory.user_id == user.id
#     ).order_by(LoginHistory.logged_at.desc()).limit(20).all()
#     return {"history": [{"ip_address": h.ip_address, "device_name": h.device_name,
#                          "browser": h.browser, "os": h.os, "status": h.status,
#                          "reason": h.reason, "logged_at": h.logged_at} for h in history]}

# @app.get("/trusted-devices")
# def get_trusted_devices(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
#     from models import UserDevice
#     devices = db.query(UserDevice).filter(UserDevice.user_id == user.id).all()
#     return {"devices": [{"device_id": d.device_id, "device_name": d.device_name,
#                          "browser": d.browser, "os": d.os, "ip_address": d.ip_address,
#                          "is_trusted": d.is_trusted, "last_used_at": d.last_used_at} for d in devices]}


# ── Profile Routes — Full CRUD ────────────────────────────────────────────────

# Body Metrics
@app.post("/profile/body")
def create_body_metrics(
    payload: BodyMetricsRequest,
    db: Session = Depends(get_db),
    user: User  = Depends(get_current_user)
):
    existing = db.query(UserBodyMetrics).filter(UserBodyMetrics.user_id == user.id).first()
    if existing:
        raise HTTPException(400, "Body metrics already exists. Use PUT to update.")
    bmi = None
    if payload.height and payload.weight:
        height_m = payload.height / 100
        bmi      = round(payload.weight / (height_m ** 2), 2)
    db.add(UserBodyMetrics(
        user_id=user.id, age=payload.age, gender=payload.gender,
        height=payload.height, weight=payload.weight, bmi=bmi,
        body_fat_percentage=payload.body_fat_percentage,
        muscle_mass=payload.muscle_mass
    ))
    db.commit()
    return {"message": "Body metrics created ✅", "bmi": bmi}


@app.get("/profile/body")
def get_body_metrics(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    m = db.query(UserBodyMetrics).filter(UserBodyMetrics.user_id == user.id).first()
    if not m:
        raise HTTPException(404, "Body metrics not found")
    return {"age": m.age, "gender": m.gender, "height": m.height,
            "weight": m.weight, "bmi": m.bmi,
            "body_fat_percentage": m.body_fat_percentage,
            "muscle_mass": m.muscle_mass, "updated_at": m.updated_at}


@app.put("/profile/body")
def update_body_metrics(
    payload: BodyMetricsRequest,
    db: Session = Depends(get_db),
    user: User  = Depends(get_current_user)
):
    m = db.query(UserBodyMetrics).filter(UserBodyMetrics.user_id == user.id).first()
    if not m:
        raise HTTPException(404, "Body metrics not found. Use POST to create first.")
    bmi = None
    if payload.height and payload.weight:
        height_m = payload.height / 100
        bmi      = round(payload.weight / (height_m ** 2), 2)
    m.age = payload.age; m.gender = payload.gender
    m.height = payload.height; m.weight = payload.weight
    m.bmi = bmi; m.body_fat_percentage = payload.body_fat_percentage
    m.muscle_mass = payload.muscle_mass
    db.commit()
    db.refresh(m)
    return {"message": "Body metrics updated ✅", "bmi": bmi}


@app.delete("/profile/body")
def delete_body_metrics(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    m = db.query(UserBodyMetrics).filter(UserBodyMetrics.user_id == user.id).first()
    if not m:
        raise HTTPException(404, "Body metrics not found")
    db.delete(m)
    db.commit()
    return {"message": "Body metrics deleted ✅"}


# Fitness Goals
@app.post("/profile/goals")
def create_fitness_goals(
    payload: FitnessGoalsRequest,
    db: Session = Depends(get_db),
    user: User  = Depends(get_current_user)
):
    existing = db.query(UserFitnessGoals).filter(UserFitnessGoals.user_id == user.id).first()
    if existing:
        raise HTTPException(400, "Fitness goals already exists. Use PUT to update.")
    db.add(UserFitnessGoals(
        user_id=user.id, goal=payload.goal,
        target_weight=payload.target_weight,
        target_days=payload.target_days,
        workout_experience=payload.workout_experience,
        gym_access=payload.gym_access,
        workout_days_per_week=payload.workout_days_per_week,
        preferred_workout_time=payload.preferred_workout_time
    ))
    db.commit()
    return {"message": "Fitness goals created ✅"}


@app.get("/profile/goals")
def get_fitness_goals(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    g = db.query(UserFitnessGoals).filter(UserFitnessGoals.user_id == user.id).first()
    if not g:
        raise HTTPException(404, "Fitness goals not found")
    return {"goal": g.goal, "target_weight": g.target_weight,
            "target_days": g.target_days, "workout_experience": g.workout_experience,
            "gym_access": g.gym_access, "workout_days_per_week": g.workout_days_per_week,
            "preferred_workout_time": g.preferred_workout_time, "updated_at": g.updated_at}


@app.put("/profile/goals")
def update_fitness_goals(
    payload: FitnessGoalsRequest,
    db: Session = Depends(get_db),
    user: User  = Depends(get_current_user)
):
    g = db.query(UserFitnessGoals).filter(UserFitnessGoals.user_id == user.id).first()
    if not g:
        raise HTTPException(404, "Fitness goals not found. Use POST to create first.")
    g.goal = payload.goal; g.target_weight = payload.target_weight
    g.target_days = payload.target_days
    g.workout_experience = payload.workout_experience
    g.gym_access = payload.gym_access
    g.workout_days_per_week = payload.workout_days_per_week
    g.preferred_workout_time = payload.preferred_workout_time
    db.commit()
    db.refresh(g)
    return {"message": "Fitness goals updated ✅"}


@app.delete("/profile/goals")
def delete_fitness_goals(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    g = db.query(UserFitnessGoals).filter(UserFitnessGoals.user_id == user.id).first()
    if not g:
        raise HTTPException(404, "Fitness goals not found")
    db.delete(g)
    db.commit()
    return {"message": "Fitness goals deleted ✅"}


# Lifestyle
@app.post("/profile/lifestyle")
def create_lifestyle(
    payload: LifestyleRequest,
    db: Session = Depends(get_db),
    user: User  = Depends(get_current_user)
):
    existing = db.query(UserLifestyle).filter(UserLifestyle.user_id == user.id).first()
    if existing:
        raise HTTPException(400, "Lifestyle already exists. Use PUT to update.")
    db.add(UserLifestyle(
        user_id=user.id, food_preference=payload.food_preference,
        water_intake=payload.water_intake, sleep_hours=payload.sleep_hours,
        activity_level=payload.activity_level, stress_level=payload.stress_level
    ))
    db.commit()
    return {"message": "Lifestyle created ✅"}


@app.get("/profile/lifestyle")
def get_lifestyle(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    l = db.query(UserLifestyle).filter(UserLifestyle.user_id == user.id).first()
    if not l:
        raise HTTPException(404, "Lifestyle info not found")
    return {"food_preference": l.food_preference, "water_intake": l.water_intake,
            "sleep_hours": l.sleep_hours, "activity_level": l.activity_level,
            "stress_level": l.stress_level, "updated_at": l.updated_at}


@app.put("/profile/lifestyle")
def update_lifestyle(
    payload: LifestyleRequest,
    db: Session = Depends(get_db),
    user: User  = Depends(get_current_user)
):
    l = db.query(UserLifestyle).filter(UserLifestyle.user_id == user.id).first()
    if not l:
        raise HTTPException(404, "Lifestyle not found. Use POST to create first.")
    l.food_preference = payload.food_preference
    l.water_intake    = payload.water_intake
    l.sleep_hours     = payload.sleep_hours
    l.activity_level  = payload.activity_level
    l.stress_level    = payload.stress_level
    db.commit()
    db.refresh(l)
    return {"message": "Lifestyle updated ✅"}


@app.delete("/profile/lifestyle")
def delete_lifestyle(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    l = db.query(UserLifestyle).filter(UserLifestyle.user_id == user.id).first()
    if not l:
        raise HTTPException(404, "Lifestyle info not found")
    db.delete(l)
    db.commit()
    return {"message": "Lifestyle deleted ✅"}


# Health
@app.post("/profile/health")
def create_health(
    payload: HealthRequest,
    db: Session = Depends(get_db),
    user: User  = Depends(get_current_user)
):
    existing = db.query(UserHealth).filter(UserHealth.user_id == user.id).first()
    if existing:
        raise HTTPException(400, "Health info already exists. Use PUT to update.")
    db.add(UserHealth(
        user_id=user.id, health_problems=payload.health_problems,
        injuries=payload.injuries, medications=payload.medications
    ))
    db.commit()
    return {"message": "Health info created ✅"}


@app.get("/profile/health")
def get_health(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    h = db.query(UserHealth).filter(UserHealth.user_id == user.id).first()
    if not h:
        raise HTTPException(404, "Health info not found")
    return {"health_problems": h.health_problems, "injuries": h.injuries,
            "medications": h.medications, "updated_at": h.updated_at}


@app.put("/profile/health")
def update_health(
    payload: HealthRequest,
    db: Session = Depends(get_db),
    user: User  = Depends(get_current_user)
):
    h = db.query(UserHealth).filter(UserHealth.user_id == user.id).first()
    if not h:
        raise HTTPException(404, "Health info not found. Use POST to create first.")
    h.health_problems = payload.health_problems
    h.injuries        = payload.injuries
    h.medications     = payload.medications
    db.commit()
    db.refresh(h)
    return {"message": "Health info updated ✅"}


@app.delete("/profile/health")
def delete_health(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    h = db.query(UserHealth).filter(UserHealth.user_id == user.id).first()
    if not h:
        raise HTTPException(404, "Health info not found")
    db.delete(h)
    db.commit()
    return {"message": "Health info deleted ✅"}


@app.get("/profile/full")
def get_full_profile(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    m = db.query(UserBodyMetrics).filter(UserBodyMetrics.user_id == user.id).first()
    g = db.query(UserFitnessGoals).filter(UserFitnessGoals.user_id == user.id).first()
    l = db.query(UserLifestyle).filter(UserLifestyle.user_id == user.id).first()
    h = db.query(UserHealth).filter(UserHealth.user_id == user.id).first()
    return {
        "user":          user_response(user),
        "body_metrics":  {"age": m.age if m else None, "gender": m.gender if m else None,
                          "height": m.height if m else None, "weight": m.weight if m else None,
                          "bmi": m.bmi if m else None,
                          "body_fat_percentage": m.body_fat_percentage if m else None,
                          "muscle_mass": m.muscle_mass if m else None},
        "fitness_goals": {"goal": g.goal if g else None,
                          "target_weight": g.target_weight if g else None,
                          "target_days": g.target_days if g else None,
                          "workout_experience": g.workout_experience if g else None,
                          "gym_access": g.gym_access if g else None,
                          "workout_days_per_week": g.workout_days_per_week if g else None,
                          "preferred_workout_time": g.preferred_workout_time if g else None},
        "lifestyle":     {"food_preference": l.food_preference if l else None,
                          "water_intake": l.water_intake if l else None,
                          "sleep_hours": l.sleep_hours if l else None,
                          "activity_level": l.activity_level if l else None,
                          "stress_level": l.stress_level if l else None},
        "health":        {"health_problems": h.health_problems if h else None,
                          "injuries": h.injuries if h else None,
                          "medications": h.medications if h else None}
    }


# ── AI Workout Generator ──────────────────────────────────────────────────────
@app.post("/ai/generate-workout")
@limiter.limit("20/hour")
def generate_workout(
    request: Request,
    db: Session = Depends(get_db),
    user: User  = Depends(get_current_user)
):
    # Fetch all profile data
    m = db.query(UserBodyMetrics).filter(UserBodyMetrics.user_id == user.id).first()
    g = db.query(UserFitnessGoals).filter(UserFitnessGoals.user_id == user.id).first()
    l = db.query(UserLifestyle).filter(UserLifestyle.user_id == user.id).first()
    h = db.query(UserHealth).filter(UserHealth.user_id == user.id).first()

    # Get existing plan to calculate week number
    existing = db.query(WorkoutPlan).filter(
        WorkoutPlan.user_id == user.id
    ).first()

    # Calculate week number (cycles 1 → 2 → 3 → 4 → 1 → ...)
    if existing and existing.week_number:
        week_number = (existing.week_number % 4) + 1
    else:
        week_number = 1

    # Build profile
    profile = {
        "user": {
            "name":               user.name,
            "preferred_language": user.preferred_language
        },
        "body_metrics": {
            "age":                m.age                if m else None,
            "gender":             m.gender             if m else None,
            "height":             m.height             if m else None,
            "weight":             m.weight             if m else None,
            "bmi":                m.bmi                if m else None,
            "body_fat_percentage":m.body_fat_percentage if m else None,
            "muscle_mass":        m.muscle_mass        if m else None
        },
        "fitness_goals": {
            "goal":                  g.goal                  if g else None,
            "target_weight":         g.target_weight         if g else None,
            "target_days":           g.target_days           if g else None,
            "workout_experience":    g.workout_experience    if g else None,
            "gym_access":            g.gym_access            if g else None,
            "workout_days_per_week": g.workout_days_per_week if g else None,
            "preferred_workout_time":g.preferred_workout_time if g else None
        },
        "lifestyle": {
            "food_preference": l.food_preference if l else None,
            "water_intake":    l.water_intake    if l else None,
            "sleep_hours":     l.sleep_hours     if l else None,
            "activity_level":  l.activity_level  if l else None,
            "stress_level":    l.stress_level    if l else None
        },
        "health": {
            "health_problems": h.health_problems if h else None,
            "injuries":        h.injuries        if h else None,
            "medications":     h.medications     if h else None
        },
        # ← Week number for periodization
        "week_number": week_number
    }

    # Generate plan
    plan = generate_workout_plan(profile)

    # Save or update
    if existing:
        existing.goal         = plan.get("goal")
        existing.level        = plan.get("level")
        existing.days_per_week = plan.get("days_per_week")
        existing.plan_data    = plan
        existing.generated_by = plan.get("generated_by", "fallback")
        existing.week_number  = week_number    # ← save week number
        db.commit()
        db.refresh(existing)
        return {
            "message":      "Workout plan regenerated and updated ✅",
            "generated_by": existing.generated_by,
            "week_number":  existing.plan_data.get("week_number", existing.week_number),
            "week_type":    existing.plan_data.get("week_type", ""),
            "created_at":   existing.created_at,
            "updated_at":   existing.updated_at,
            "plan":         existing.plan_data
}
    else:
        new_plan = WorkoutPlan(
            user_id       = user.id,
            goal          = plan.get("goal"),
            level         = plan.get("level"),
            days_per_week = plan.get("days_per_week"),
            plan_data     = plan,
            generated_by  = plan.get("generated_by", "fallback"),
            week_number   = week_number    # ← save week number
        )
        db.add(new_plan)
        db.commit()
        db.refresh(new_plan)
        return {
            "message":      "Workout plan generated and saved ✅",
            "generated_by": new_plan.generated_by,
            "week_number":  new_plan.plan_data.get("week_number", new_plan.week_number),
            "week_type":    new_plan.plan_data.get("week_type", ""),
            "created_at":   new_plan.created_at,
            "updated_at":   new_plan.updated_at,
            "plan":         new_plan.plan_data
}

@app.get("/ai/workout-plan")
def get_workout_plan(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    plan = db.query(WorkoutPlan).filter(WorkoutPlan.user_id == user.id).first()
    if not plan:
        raise HTTPException(404, "No workout plan found. Please generate one first.")
    return {"message": "Workout plan fetched from database",
            "generated_by": plan.generated_by,
            "created_at": plan.created_at,
            "updated_at": plan.updated_at,
            "plan": plan.plan_data}


@app.delete("/ai/workout-plan")
def delete_workout_plan(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    plan = db.query(WorkoutPlan).filter(WorkoutPlan.user_id == user.id).first()
    if not plan:
        raise HTTPException(404, "No workout plan found")
    db.delete(plan)
    db.commit()
    return {"message": "Workout plan deleted ✅"}



# ###########################trainer_routes###########################
from modules.trainer import router as trainer_router

app.include_router(trainer_router, prefix="/trainer", tags=["Trainer"])

##################################__CHAT______##############################
from modules.chat import router as chat_router
app.include_router(chat_router, prefix="/chat", tags=["Chat"])


###########################___CUSTOM__WORKOUT___##############
from modules.custom_workout import router as custom_workout_router
app.include_router(custom_workout_router, prefix="/custom-workout", tags=["Custom Workout"])



######################____DIET____#######################
app.include_router(diet_router, prefix="/diet", tags=["Diet Plan"])