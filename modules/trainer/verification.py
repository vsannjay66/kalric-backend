import shutil
import secrets
from datetime import datetime, timezone
from fastapi import UploadFile
from pathlib import Path


UPLOAD_DIR = "uploads/certificates"
ALLOWED_EXTENSIONS = ["pdf", "jpg", "jpeg", "png"]
MAX_FILE_SIZE_MB   = 5


def save_certificate(file: UploadFile, user_id: int) -> str:
    """
    Save uploaded certificate file.
    Returns file path.
    Raises ValueError for invalid files.
    """
    # Create directory if not exists
    Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

    # Get file extension
    if not file.filename or "." not in file.filename:
        raise ValueError("Invalid file name")

    ext = file.filename.split(".")[-1].lower()

    # Validate file type
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Only {', '.join(ALLOWED_EXTENSIONS)} files allowed")

    # Check file size
    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)

    if size > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise ValueError(f"File too large. Max {MAX_FILE_SIZE_MB}MB allowed")

    # Generate unique filename
    timestamp = int(datetime.now(timezone.utc).timestamp())
    unique_id = secrets.token_hex(4)
    filename  = f"trainer_{user_id}_{timestamp}_{unique_id}.{ext}"
    filepath  = f"{UPLOAD_DIR}/{filename}"

    # Save file
    with open(filepath, "wb") as f:
        shutil.copyfileobj(file.file, f)

    return filepath


def get_verification_status(profile) -> dict:
    """Get full verification status of trainer."""
    return {
        "is_verified":         profile.is_verified,
        "verification_status": profile.verification_status,
        "certificate_url":     profile.certificate_url,
        "submitted_at":        profile.submitted_at,
        "verified_at":         profile.verified_at,
        "rejection_reason":    profile.rejection_reason
    }