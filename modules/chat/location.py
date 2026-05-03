import math


def calculate_distance(
    lat1: float, lon1: float,
    lat2: float, lon2: float
) -> float:
    R    = 6371
    lat1 = math.radians(lat1)
    lat2 = math.radians(lat2)
    lon1 = math.radians(lon1)
    lon2 = math.radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        math.sin(dlat / 2) ** 2 +
        math.cos(lat1) *
        math.cos(lat2) *
        math.sin(dlon / 2) ** 2
    )

    return R * 2 * math.asin(math.sqrt(a))


def is_within_radius(
    lat1: float, lon1: float,
    lat2: float, lon2: float,
    radius_km: float = 50.0
) -> bool:
    return calculate_distance(lat1, lon1, lat2, lon2) <= radius_km