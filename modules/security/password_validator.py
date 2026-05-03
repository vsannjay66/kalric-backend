import re

def validate_password_strength(password: str) -> tuple[bool, str]:
    if len(password) < 8:
        return False, "Password must be at least 8 characters"

    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"

    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"

    if not re.search(r"\d", password):
        return False, "Password must contain at least one number"

    if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", password):
        return False, "Password must contain at least one special character"

    if " " in password:
        return False, "Password must not contain spaces"

    common = [
        "password", "12345678", "password1",
        "qwerty123", "admin123", "letmein1"
    ]
    if password.lower() in common:
        return False, "Password is too common. Choose a stronger one"

    return True, "Password is strong"