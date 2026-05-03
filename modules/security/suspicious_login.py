from sqlalchemy.orm import Session
from models import UserDevice, LoginHistory
from datetime import datetime, timezone


def is_new_device(db: Session, user_id: int, device_id: str) -> bool:
    device = db.query(UserDevice).filter(
        UserDevice.user_id   == user_id,
        UserDevice.device_id == device_id
    ).first()
    return device is None


def save_device(db: Session, user_id: int, device_info: dict):
    existing = db.query(UserDevice).filter(
        UserDevice.user_id   == user_id,
        UserDevice.device_id == device_info["device_id"]
    ).first()

    if existing:
        existing.last_used_at = datetime.now(timezone.utc)
    else:
        db.add(UserDevice(
            user_id     = user_id,
            device_id   = device_info["device_id"],
            device_name = device_info["device_name"],
            browser     = device_info["browser"],
            os          = device_info["os"],
            ip_address  = device_info["ip_address"],
            is_trusted  = False
        ))
    db.commit()


def log_login_attempt(
    db: Session,
    user_id: int,
    device_info: dict,
    status: str,
    reason: str = None
):
    db.add(LoginHistory(
        user_id     = user_id,
        ip_address  = device_info.get("ip_address"),
        device_name = device_info.get("device_name"),
        browser     = device_info.get("browser"),
        os          = device_info.get("os"),
        status      = status,
        reason      = reason
    ))
    db.commit()