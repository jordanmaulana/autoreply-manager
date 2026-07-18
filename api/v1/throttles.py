from rest_framework.throttling import AnonRateThrottle


class AuthRateThrottle(AnonRateThrottle):
    """Per-IP brute-force / enumeration guard for the AllowAny auth endpoints.

    Rate is the "auth" scope in REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"].
    """

    scope = "auth"
