"""
accounts/cookie_utils.py
------------------------
Helpers to set / delete the two JWT HttpOnly cookies on a response.

Configuration keys read from settings (all optional, with safe defaults):
    JWT_COOKIE_ACCESS_NAME    (str)  default: 'access'
    JWT_COOKIE_REFRESH_NAME   (str)  default: 'refresh'
    JWT_COOKIE_SECURE         (bool) default: False  (set True in production)
    JWT_COOKIE_HTTPONLY       (bool) default: True
    JWT_COOKIE_SAMESITE       (str)  default: 'Lax'
    JWT_COOKIE_ACCESS_MAX_AGE (int)  default: 7 * 3600   seconds (7 h)
    JWT_COOKIE_REFRESH_MAX_AGE(int)  default: 7 * 24 * 3600 seconds (7 d)
"""

from django.conf import settings


# ── defaults ──────────────────────────────────────────────────────────────────
ACCESS_NAME    = getattr(settings, "JWT_COOKIE_ACCESS_NAME",    "access")
REFRESH_NAME   = getattr(settings, "JWT_COOKIE_REFRESH_NAME",   "refresh")
SECURE         = getattr(settings, "JWT_COOKIE_SECURE",         False)
HTTPONLY       = getattr(settings, "JWT_COOKIE_HTTPONLY",        True)
SAMESITE       = getattr(settings, "JWT_COOKIE_SAMESITE",        "Lax")
ACCESS_MAX_AGE = getattr(settings, "JWT_COOKIE_ACCESS_MAX_AGE",  120)
REFRESH_MAX_AGE= getattr(settings, "JWT_COOKIE_REFRESH_MAX_AGE", 7 * 24 * 3600)


def set_auth_cookies(response, *, access_token: str, refresh_token: str) -> None:
    """
    Write both JWT tokens as HttpOnly cookies onto *response*.
    Call this instead of returning raw tokens in the JSON body.
    """
    response.set_cookie(
        key      = ACCESS_NAME,
        value    = access_token,
        max_age  = ACCESS_MAX_AGE,
        httponly = HTTPONLY,
        secure   = SECURE,
        samesite = SAMESITE,
    )
    response.set_cookie(
        key      = REFRESH_NAME,
        value    = refresh_token,
        max_age  = REFRESH_MAX_AGE,
        httponly = HTTPONLY,
        secure   = SECURE,
        samesite = SAMESITE,
    )


def delete_auth_cookies(response) -> None:
    """
    Expire both JWT cookies immediately (logout).
    Uses set_cookie with max_age=0 (more reliable than delete_cookie across
    Django versions) and mirrors the same flags so the browser matches the
    existing cookie and removes it.
    """
    for name in (ACCESS_NAME, REFRESH_NAME):
        response.set_cookie(
            key      = name,
            value    = '',
            max_age  = 0,
            httponly = HTTPONLY,
            secure   = SECURE,
            samesite = SAMESITE,
        )
