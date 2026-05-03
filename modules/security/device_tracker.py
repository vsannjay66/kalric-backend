import hashlib
from fastapi import Request

try:
    from user_agents import parse as parse_ua
    UA_AVAILABLE = True
except ImportError:
    UA_AVAILABLE = False


def get_device_info(request: Request) -> dict:
    user_agent_string = request.headers.get("user-agent", "unknown")
    ip_address        = (
        request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        or request.client.host
    )

    if UA_AVAILABLE:
        ua          = parse_ua(user_agent_string)
        browser     = f"{ua.browser.family} {ua.browser.version_string}"
        os_info     = f"{ua.os.family} {ua.os.version_string}"
        device_name = ua.device.family
    else:
        browser     = user_agent_string[:100]
        os_info     = "Unknown"
        device_name = "Unknown"

    device_id = hashlib.sha256(
        f"{ip_address}{user_agent_string}".encode()
    ).hexdigest()[:32]

    return {
        "device_id":   device_id,
        "device_name": device_name,
        "browser":     browser,
        "os":          os_info,
        "ip_address":  ip_address
    }