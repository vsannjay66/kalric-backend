from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import or_

from database import get_db
from models import User, UserFitnessGoals
# from modules.chat.models import UserLocation, ChatRoom
# from modules.chat.location import calculate_distance
from modules.trainer.models import (
    UserRole, TrainerProfile,
    TrainerClient, TrainerReview
)
from modules.trainer.schemas import (
    RoleRequest, TrainerProfileRequest,
    ReviewRequest, TrainerRequestAction
)
from modules.trainer.verification import save_certificate
from auth import verify_access_token

router = APIRouter()


# ── Auth Helper ───────────────────────────────────────────────────────────────

def get_current_user_trainer(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
    if not token:
        raise HTTPException(401, "Not authenticated")
    payload = verify_access_token(token)
    if not payload:
        raise HTTPException(401, "Invalid token")
    user = db.query(User).filter(User.id == payload["user_id"]).first()
    if not user:
        raise HTTPException(404, "User not found")
    return user


def get_user_role(user_id: int, db: Session) -> str:
    role = db.query(UserRole).filter(UserRole.user_id == user_id).first()
    return role.role if role else "client"


# ── Role Routes ───────────────────────────────────────────────────────────────

@router.post("/role")
def set_role(
    request: Request,
    payload: RoleRequest,
    db: Session = Depends(get_db)
):
    user = get_current_user_trainer(request, db)

    existing = db.query(UserRole).filter(UserRole.user_id == user.id).first()
    if existing:
        existing.role = payload.role
    else:
        db.add(UserRole(user_id=user.id, role=payload.role))
    db.commit()

    return {"message": f"Role set to {payload.role} ✅", "role": payload.role}


@router.get("/role")
def get_role(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_trainer(request, db)
    role = get_user_role(user.id, db)
    return {"user_id": user.id, "role": role}


# ── Trainer Profile Routes ────────────────────────────────────────────────────

@router.post("/profile")
def create_trainer_profile(
    request: Request,
    payload: TrainerProfileRequest,
    db: Session = Depends(get_db)
):
    user = get_current_user_trainer(request, db)

    if get_user_role(user.id, db) != "trainer":
        raise HTTPException(403, "Only trainers can create trainer profile")

    existing = db.query(TrainerProfile).filter(
        TrainerProfile.user_id == user.id
    ).first()
    if existing:
        raise HTTPException(400, "Profile already exists. Use PUT to update.")

    profile = TrainerProfile(
        user_id           = user.id,
        bio               = payload.bio,
        experience_years  = payload.experience_years,
        specializations   = payload.specializations,
        certifications    = payload.certifications,
        trainer_type      = payload.trainer_type,
        is_free           = payload.is_free,
        price_per_session = payload.price_per_session,
        available_times   = payload.available_times,
        max_clients       = payload.max_clients or 10
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)

    return {"message": "Trainer profile created ✅", "profile_id": profile.id}


@router.put("/profile")
def update_trainer_profile(
    request: Request,
    payload: TrainerProfileRequest,
    db: Session = Depends(get_db)
):
    user = get_current_user_trainer(request, db)

    profile = db.query(TrainerProfile).filter(
        TrainerProfile.user_id == user.id
    ).first()
    if not profile:
        raise HTTPException(404, "Profile not found. Use POST to create.")

    profile.bio               = payload.bio
    profile.experience_years  = payload.experience_years
    profile.specializations   = payload.specializations
    profile.certifications    = payload.certifications
    profile.is_free           = payload.is_free
    profile.price_per_session = payload.price_per_session
    profile.available_times   = payload.available_times
    profile.max_clients       = payload.max_clients or 10

    db.commit()
    return {"message": "Trainer profile updated ✅"}


@router.get("/profile/{trainer_id}")
def get_trainer_profile(
    trainer_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    _ = get_current_user_trainer(request, db)

    profile = db.query(TrainerProfile).filter(
        TrainerProfile.user_id == trainer_id
    ).first()
    if not profile:
        raise HTTPException(404, "Trainer profile not found")

    trainer_user = db.query(User).filter(User.id == trainer_id).first()

    return {
        "trainer_id":        trainer_id,
        "name":              trainer_user.name,
        "bio":               profile.bio,
        "trainer_type":      profile.trainer_type,
        "experience_years":  profile.experience_years,
        "specializations":   profile.specializations,
        "certifications":    profile.certifications,
        "is_verified":       profile.is_verified,
        "verification_status": profile.verification_status,
        "is_free":           profile.is_free,
        "price_per_session": profile.price_per_session,
        "available_times":   profile.available_times,
        "max_clients":       profile.max_clients,
        "current_clients":   profile.current_clients,
        "average_rating":    profile.average_rating,
        "total_reviews":     profile.total_reviews
    }


# ── Find Trainers ─────────────────────────────────────────────────────────────

# @router.get("/find/trainers")
# def find_trainers(
#     request:   Request,
#     radius_km: float = 50.0,
#     goal:      str   = None,
#     is_free:   bool  = None,
#     db: Session      = Depends(get_db)
# ):
#     user = get_current_user_trainer(request, db)

#     my_location = db.query(UserLocation).filter(
#         UserLocation.user_id == user.id
#     ).first()
#     if not my_location:
#         raise HTTPException(400, "Please enable location access first")

#     if not goal:
#         my_goals = db.query(UserFitnessGoals).filter(
#             UserFitnessGoals.user_id == user.id
#         ).first()
#         goal = my_goals.goal if my_goals else None

#     trainer_profiles = db.query(TrainerProfile).filter(
#         TrainerProfile.is_verified == True
#     ).all()

#     results = []

#     for profile in trainer_profiles:
#         if profile.user_id == user.id:
#             continue

#         if goal and profile.specializations:
#             if goal.lower() not in profile.specializations.lower():
#                 continue

#         if is_free is not None:
#             if is_free and not profile.is_free:
#                 continue
#             if not is_free and profile.is_free:
#                 continue

#         if profile.current_clients >= profile.max_clients:
#             continue

#         trainer_location = db.query(UserLocation).filter(
#             UserLocation.user_id == profile.user_id
#         ).first()
#         if not trainer_location:
#             continue

#         distance = calculate_distance(
#             my_location.latitude,      my_location.longitude,
#             trainer_location.latitude, trainer_location.longitude
#         )
#         if distance > radius_km:
#             continue

#         trainer_user = db.query(User).filter(User.id == profile.user_id).first()

#         results.append({
#             "trainer_id":        profile.user_id,
#             "name":              trainer_user.name,
#             "bio":               profile.bio,
#             "experience_years":  profile.experience_years,
#             "specializations":   profile.specializations,
#             "is_verified":       profile.is_verified,
#             "is_free":           profile.is_free,
#             "price_per_session": profile.price_per_session,
#             "average_rating":    profile.average_rating,
#             "total_reviews":     profile.total_reviews,
#             "distance_km":       round(distance, 1),
#             "city":              trainer_location.city,
#             "available_times":   profile.available_times
#         })

#     results.sort(key=lambda x: (-x["average_rating"], x["distance_km"]))

#     return {
#         "goal":        goal,
#         "radius_km":   radius_km,
#         "total_found": len(results),
#         "trainers":    results
#     }


# # ── Find Clients ──────────────────────────────────────────────────────────────

# @router.get("/find/clients")
# def find_clients(
#     request:   Request,
#     radius_km: float = 50.0,
#     db: Session      = Depends(get_db)
# ):
#     user = get_current_user_trainer(request, db)

#     if get_user_role(user.id, db) != "trainer":
#         raise HTTPException(403, "Only trainers can find clients")

#     my_location = db.query(UserLocation).filter(
#         UserLocation.user_id == user.id
#     ).first()
#     if not my_location:
#         raise HTTPException(400, "Please enable location access first")

#     client_roles = db.query(UserRole).filter(
#         UserRole.role    == "client",
#         UserRole.user_id != user.id
#     ).all()

#     results = []

#     for client_role in client_roles:
#         client_location = db.query(UserLocation).filter(
#             UserLocation.user_id == client_role.user_id
#         ).first()
#         if not client_location:
#             continue

#         distance = calculate_distance(
#             my_location.latitude,     my_location.longitude,
#             client_location.latitude, client_location.longitude
#         )
#         if distance > radius_km:
#             continue

#         client_user  = db.query(User).filter(User.id == client_role.user_id).first()
#         client_goals = db.query(UserFitnessGoals).filter(
#             UserFitnessGoals.user_id == client_role.user_id
#         ).first()

#         existing = db.query(TrainerClient).filter(
#             TrainerClient.trainer_id == user.id,
#             TrainerClient.client_id  == client_role.user_id
#         ).first()

#         results.append({
#             "client_id":   client_role.user_id,
#             "name":        client_user.name,
#             "goal":        client_goals.goal if client_goals else None,
#             "experience":  client_goals.workout_experience if client_goals else None,
#             "distance_km": round(distance, 1),
#             "city":        client_location.city,
#             "status":      existing.status if existing else "none"
#         })

#     results.sort(key=lambda x: x["distance_km"])
#     return {"total_found": len(results), "clients": results}


# ── Connection Routes ─────────────────────────────────────────────────────────

@router.post("/request/{client_id}")
def send_training_request(
    client_id: int,
    request:   Request,
    db: Session = Depends(get_db)
):
    user = get_current_user_trainer(request, db)
    role = get_user_role(user.id, db)

    trainer_id = user.id      if role == "trainer" else client_id
    c_id       = client_id    if role == "trainer" else user.id

    existing = db.query(TrainerClient).filter(
        TrainerClient.trainer_id == trainer_id,
        TrainerClient.client_id  == c_id
    ).first()
    if existing:
        raise HTTPException(400, f"Request already {existing.status}")

    profile = db.query(TrainerProfile).filter(
        TrainerProfile.user_id == trainer_id
    ).first()
    if not profile:
        raise HTTPException(404, "Trainer profile not found")
    if not profile.is_verified:
        raise HTTPException(403, "Trainer not verified yet")

    connection = TrainerClient(
        trainer_id = trainer_id,
        client_id  = c_id,
        status     = "pending",
        is_paid    = not profile.is_free,
        price      = profile.price_per_session
    )
    db.add(connection)
    db.commit()
    db.refresh(connection)

    return {
        "message":       "Training request sent ✅",
        "connection_id": connection.id,
        "is_paid":       connection.is_paid,
        "price":         connection.price
    }


# @router.put("/request/respond")
# def respond_training_request(
#     request: Request,
#     payload: TrainerRequestAction,
#     db: Session = Depends(get_db)
# ):
#     user = get_current_user_trainer(request, db)

#     connection = db.query(TrainerClient).filter(
#         TrainerClient.id     == payload.connection_id,
#         TrainerClient.status == "pending"
#     ).first()
#     if not connection:
#         raise HTTPException(404, "Request not found")

#     role = get_user_role(user.id, db)
#     if role == "trainer" and connection.trainer_id != user.id:
#         raise HTTPException(403, "Not authorized")
#     if role == "client" and connection.client_id != user.id:
#         raise HTTPException(403, "Not authorized")

#     if payload.action == "accept":
#         connection.status     = "active"
#         connection.started_at = datetime.now(timezone.utc)
#         db.commit()

#         profile = db.query(TrainerProfile).filter(
#             TrainerProfile.user_id == connection.trainer_id
#         ).first()
#         if profile:
#             profile.current_clients += 1
#             db.commit()

#         room = ChatRoom(
#             user1_id = connection.trainer_id,
#             user2_id = connection.client_id
#         )
#         db.add(room)
#         db.commit()
#         db.refresh(room)

#         return {
#             "message": "Training request accepted ✅",
#             "room_id": room.id,
#             "is_paid": connection.is_paid,
#             "price":   connection.price
#         }
#     else:
#         connection.status = "rejected"
#         db.commit()
#         return {"message": "Request rejected"}


# # ── My Clients / My Trainer ───────────────────────────────────────────────────

# @router.get("/my/clients")
# def get_my_clients(request: Request, db: Session = Depends(get_db)):
#     user = get_current_user_trainer(request, db)

#     if get_user_role(user.id, db) != "trainer":
#         raise HTTPException(403, "Only trainers can view clients")

#     connections = db.query(TrainerClient).filter(
#         TrainerClient.trainer_id == user.id,
#         TrainerClient.status     == "active"
#     ).all()

#     result = []
#     for conn in connections:
#         client       = db.query(User).filter(User.id == conn.client_id).first()
#         client_goals = db.query(UserFitnessGoals).filter(
#             UserFitnessGoals.user_id == conn.client_id
#         ).first()
#         room = db.query(ChatRoom).filter(
#             or_(
#                 (ChatRoom.user1_id == user.id) & (ChatRoom.user2_id == conn.client_id),
#                 (ChatRoom.user1_id == conn.client_id) & (ChatRoom.user2_id == user.id)
#             )
#         ).first()

#         result.append({
#             "client_id":  conn.client_id,
#             "name":       client.name,
#             "goal":       client_goals.goal if client_goals else None,
#             "is_paid":    conn.is_paid,
#             "price":      conn.price,
#             "started_at": conn.started_at,
#             "room_id":    room.id if room else None
#         })

#     return {"my_clients": result}


# @router.get("/my/trainer")
# def get_my_trainer(request: Request, db: Session = Depends(get_db)):
#     user = get_current_user_trainer(request, db)

#     connection = db.query(TrainerClient).filter(
#         TrainerClient.client_id == user.id,
#         TrainerClient.status    == "active"
#     ).first()
#     if not connection:
#         raise HTTPException(404, "No active trainer found")

#     trainer = db.query(User).filter(User.id == connection.trainer_id).first()
#     profile = db.query(TrainerProfile).filter(
#         TrainerProfile.user_id == connection.trainer_id
#     ).first()
#     room = db.query(ChatRoom).filter(
#         or_(
#             (ChatRoom.user1_id == user.id) & (ChatRoom.user2_id == connection.trainer_id),
#             (ChatRoom.user1_id == connection.trainer_id) & (ChatRoom.user2_id == user.id)
#         )
#     ).first()

#     return {
#         "trainer_id":       connection.trainer_id,
#         "name":             trainer.name,
#         "bio":              profile.bio              if profile else None,
#         "experience_years": profile.experience_years if profile else None,
#         "is_verified":      profile.is_verified      if profile else False,
#         "is_paid":          connection.is_paid,
#         "price":            connection.price,
#         "started_at":       connection.started_at,
#         "room_id":          room.id                  if room    else None,
#         "average_rating":   profile.average_rating   if profile else 0
#     }


# ── Reviews ───────────────────────────────────────────────────────────────────

@router.post("/review")
def add_review(
    request: Request,
    payload: ReviewRequest,
    db: Session = Depends(get_db)
):
    user = get_current_user_trainer(request, db)

    connection = db.query(TrainerClient).filter(
        TrainerClient.trainer_id == payload.trainer_id,
        TrainerClient.client_id  == user.id,
        TrainerClient.status     == "active"
    ).first()
    if not connection:
        raise HTTPException(403, "You can only review your active trainer")

    profile = db.query(TrainerProfile).filter(
        TrainerProfile.user_id == payload.trainer_id
    ).first()
    if not profile:
        raise HTTPException(404, "Trainer not found")

    review = TrainerReview(
        trainer_id = profile.id,
        client_id  = user.id,
        rating     = payload.rating,
        review     = payload.review
    )
    db.add(review)

    all_reviews            = db.query(TrainerReview).filter(
        TrainerReview.trainer_id == profile.id
    ).all()
    total                  = sum(r.rating for r in all_reviews) + payload.rating
    count                  = len(all_reviews) + 1
    profile.average_rating = round(total / count, 1)
    profile.total_reviews  = count

    db.commit()
    return {"message": "Review added ✅", "average_rating": profile.average_rating}


@router.get("/reviews/{trainer_id}")
def get_reviews(
    trainer_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    _ = get_current_user_trainer(request, db)

    profile = db.query(TrainerProfile).filter(
        TrainerProfile.user_id == trainer_id
    ).first()
    if not profile:
        raise HTTPException(404, "Trainer not found")

    reviews = db.query(TrainerReview).filter(
        TrainerReview.trainer_id == profile.id
    ).all()

    return {
        "trainer_id":     trainer_id,
        "average_rating": profile.average_rating,
        "total_reviews":  profile.total_reviews,
        "reviews": [
            {
                "client_id": r.client_id,
                "rating":    r.rating,
                "review":    r.review,
                "date":      r.created_at
            }
            for r in reviews
        ]
    }


# ── Verification Routes ───────────────────────────────────────────────────────

@router.post("/verification/upload")
async def upload_certificate(
    request: Request,
    file:    UploadFile = File(...),
    db: Session         = Depends(get_db)
):
    user = get_current_user_trainer(request, db)

    if get_user_role(user.id, db) != "trainer":
        raise HTTPException(403, "Only trainers can upload certificates")

    profile = db.query(TrainerProfile).filter(
        TrainerProfile.user_id == user.id
    ).first()
    if not profile:
        raise HTTPException(400, "Please create trainer profile first")

    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(400, "File too large. Max 5MB allowed")
    await file.seek(0)

    try:
        filepath = save_certificate(file, user.id)
    except ValueError as e:
        raise HTTPException(400, str(e))

    profile.certificate_url     = filepath
    profile.verification_status = "pending"
    profile.submitted_at        = datetime.now(timezone.utc)
    db.commit()

    return {
        "message": "Certificate uploaded successfully ✅",
        "status":  "pending",
        "note":    "Our team will verify your certificate within 24-48 hours"
    }


@router.get("/verification/status")
def get_my_verification_status(
    request: Request,
    db: Session = Depends(get_db)
):
    user = get_current_user_trainer(request, db)

    profile = db.query(TrainerProfile).filter(
        TrainerProfile.user_id == user.id
    ).first()
    if not profile:
        raise HTTPException(404, "Trainer profile not found")

    return {
        "trainer_id":          user.id,
        "name":                user.name,
        "is_verified":         profile.is_verified,
        "verification_status": profile.verification_status,
        "certificate_url":     profile.certificate_url,
        "submitted_at":        profile.submitted_at,
        "verified_at":         profile.verified_at,
        "rejection_reason":    profile.rejection_reason
    }


@router.get("/verification/pending")
def get_pending_verifications(
    request: Request,
    db: Session = Depends(get_db)
):
    _ = get_current_user_trainer(request, db)

    pending = db.query(TrainerProfile).filter(
        TrainerProfile.verification_status == "pending"
    ).all()

    result = []
    for profile in pending:
        trainer_user = db.query(User).filter(User.id == profile.user_id).first()
        result.append({
            "trainer_id":       profile.user_id,
            "name":             trainer_user.name,
            "email":            trainer_user.email,
            "certifications":   profile.certifications,
            "experience_years": profile.experience_years,
            "certificate_url":  profile.certificate_url,
            "submitted_at":     profile.submitted_at
        })

    return {"total_pending": len(result), "pending": result}


@router.put("/verification/approve/{trainer_id}")
def approve_trainer(
    trainer_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    _ = get_current_user_trainer(request, db)

    profile = db.query(TrainerProfile).filter(
        TrainerProfile.user_id == trainer_id
    ).first()
    if not profile:
        raise HTTPException(404, "Trainer not found")

    if profile.verification_status != "pending":
        raise HTTPException(400, f"Status is {profile.verification_status} not pending")

    profile.is_verified         = True
    profile.verification_status = "approved"
    profile.verified_at         = datetime.now(timezone.utc)
    profile.rejection_reason    = None
    db.commit()

    return {"message": f"Trainer {trainer_id} approved ✅", "verified_at": profile.verified_at}


@router.put("/verification/reject/{trainer_id}")
def reject_trainer(
    trainer_id: int,
    reason:     str,
    request: Request,
    db: Session = Depends(get_db)
):
    _ = get_current_user_trainer(request, db)

    profile = db.query(TrainerProfile).filter(
        TrainerProfile.user_id == trainer_id
    ).first()
    if not profile:
        raise HTTPException(404, "Trainer not found")

    profile.is_verified         = False
    profile.verification_status = "rejected"
    profile.rejection_reason    = reason
    db.commit()

    return {
        "message": f"Trainer {trainer_id} rejected",
        "reason":  reason,
        "note":    "Trainer can resubmit with correct certificate"
    }


@router.post("/verification/resubmit")
async def resubmit_certificate(
    request: Request,
    file:    UploadFile = File(...),
    db: Session         = Depends(get_db)
):
    user = get_current_user_trainer(request, db)

    profile = db.query(TrainerProfile).filter(
        TrainerProfile.user_id == user.id
    ).first()
    if not profile:
        raise HTTPException(404, "Profile not found")

    if profile.verification_status not in ["rejected", "not_submitted"]:
        raise HTTPException(400, "Can only resubmit if rejected or not submitted")

    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(400, "File too large. Max 5MB")
    await file.seek(0)

    try:
        filepath = save_certificate(file, user.id)
    except ValueError as e:
        raise HTTPException(400, str(e))

    profile.certificate_url     = filepath
    profile.verification_status = "pending"
    profile.submitted_at        = datetime.now(timezone.utc)
    profile.rejection_reason    = None
    db.commit()

    return {
        "message": "Certificate resubmitted ✅",
        "status":  "pending",
        "note":    "Our team will review within 24-48 hours"
    }