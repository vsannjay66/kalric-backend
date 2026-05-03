import re
import html

def sanitize_string(value: str) -> str:
    if not value:
        return value

    value = html.escape(value)

    sql_patterns = [
        r"(\bSELECT\b|\bINSERT\b|\bUPDATE\b|\bDELETE\b|\bDROP\b|\bTABLE\b)",
        r"(--|\bOR\b\s+\d+=\d+|\bAND\b\s+\d+=\d+)",
        r"(;|\bEXEC\b|\bUNION\b|\bCAST\b|\bCONVERT\b)",
    ]
    for pattern in sql_patterns:
        value = re.sub(pattern, "", value, flags=re.IGNORECASE)

    value = re.sub(r"<script.*?>.*?</script>", "", value, flags=re.IGNORECASE | re.DOTALL)
    value = re.sub(r"javascript:", "", value, flags=re.IGNORECASE)

    return value.strip()


def sanitize_email(email: str) -> str:
    return email.strip().lower()