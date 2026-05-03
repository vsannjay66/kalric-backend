from sqlalchemy.orm import Session
from modules.chat.location import calculate_distance
from modules.chat.models import UserLocation, UserConnection
from models import User, UserFitnessGoals


def get_matches(
    db:        Session,
    user:      User,
    radius_km: float = 50.0,
    national:  bool  = True
) -> dict:
    """
    Find users with same goal.
    Returns local matches first then national.
    """

    my_location = db.query(UserLocation).filter(
        UserLocation.user_id == user.id
    ).first()

    my_goals = db.query(UserFitnessGoals).filter(
        UserFitnessGoals.user_id == user.id
    ).first()

    if not my_goals or not my_goals.goal:
        return {"local": [], "national": []}

    # Get connected user IDs
    connected_ids = set()
    connections   = db.query(UserConnection).filter(
        (UserConnection.sender_id   == user.id) |
        (UserConnection.receiver_id == user.id)
    ).all()

    for conn in connections:
        connected_ids.add(conn.sender_id)
        connected_ids.add(conn.receiver_id)
    connected_ids.discard(user.id)

    # Get same goal users
    same_goal = db.query(UserFitnessGoals).filter(
        UserFitnessGoals.goal    == my_goals.goal,
        UserFitnessGoals.workout_experience == my_goals.workout_experience,
        UserFitnessGoals.user_id != user.id
    ).all()

    local_matches    = []
    national_matches = []

    for goal_user in same_goal:
        if goal_user.user_id in connected_ids:
            continue

        their_location = db.query(UserLocation).filter(
            UserLocation.user_id == goal_user.user_id
        ).first()

        if not their_location:
            continue

        their_user = db.query(User).filter(
            User.id == goal_user.user_id
        ).first()

        # Check pending status
        pending = db.query(UserConnection).filter(
            ((UserConnection.sender_id   == user.id) &
             (UserConnection.receiver_id == goal_user.user_id)) |
            ((UserConnection.sender_id   == goal_user.user_id) &
             (UserConnection.receiver_id == user.id))
        ).first()

        match_data = {
            "user_id":        their_user.id,
            "name":           their_user.name,
            "goal":           goal_user.goal,
            "experience":     goal_user.workout_experience,
            "city":           their_location.city,
            "request_status": pending.status if pending else "none"
        }

        # Check if local
        if my_location:
            distance = calculate_distance(
                my_location.latitude,    my_location.longitude,
                their_location.latitude, their_location.longitude
            )
            match_data["distance_km"] = round(distance, 1)

            if distance <= radius_km:
                local_matches.append(match_data)
            elif national:
                national_matches.append(match_data)
        elif national:
            match_data["distance_km"] = None
            national_matches.append(match_data)

    # Sort local by distance
    local_matches.sort(key=lambda x: x.get("distance_km", 999))

    return {
        "local":    local_matches,
        "national": national_matches
    }