from sqlalchemy.orm import Session
from models import BlacklistedToken


def blacklist_token(db: Session, user_id: int, token: str, reason: str = "logout"):
    existing = db.query(BlacklistedToken).filter(
        BlacklistedToken.token == token
    ).first()

    if not existing:
        db.add(BlacklistedToken(
            user_id = user_id,
            token   = token,
            reason  = reason
        ))
        db.commit()


def is_token_blacklisted(db: Session, token: str) -> bool:
    result = db.query(BlacklistedToken).filter(
        BlacklistedToken.token == token
    ).first()
    return result is not None