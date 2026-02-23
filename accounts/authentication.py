"""
accounts/authentication.py
---------------------------
CookieJWTAuthentication
    Extends simplejwt's JWTAuthentication so that DRF can authenticate
    a request using the 'access' HttpOnly cookie when no Authorization
    header is present.

    Priority order:
        1. Authorization: Bearer <token>   (unchanged simplejwt behaviour)
        2. Cookie: access=<token>

This means every existing endpoint that uses IsAuthenticated continues to
work unchanged — just set the cookie and the middleware/authenticator
handles the rest.
"""

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework.exceptions import AuthenticationFailed
from django.conf import settings


ACCESS_COOKIE_NAME = getattr(settings, "JWT_COOKIE_ACCESS_NAME", "access")


class CookieJWTAuthentication(JWTAuthentication):
    """
    Drop-in replacement for JWTAuthentication that also reads the access
    token from an HttpOnly cookie.
    """

    def authenticate(self, request):
        # ── 1. Try the standard Authorization header first ────────────────
        header = self.get_header(request)
        if header is not None:
            raw_token = self.get_raw_token(header)
            if raw_token is not None:
                try:
                    validated_token = self.get_validated_token(raw_token)
                    return self.get_user(validated_token), validated_token
                except TokenError as e:
                    raise InvalidToken(e.args[0])

        # ── 2. Fall back to the access cookie ─────────────────────────────
        raw_token = request.COOKIES.get(ACCESS_COOKIE_NAME)

        # Also allow a value that was injected by the refresh middleware
        # (stored on the request object before the view ran)
        if raw_token is None:
            raw_token = getattr(request, "_refreshed_access", None)

        if raw_token is None:
            return None  # anonymous request

        try:
            validated_token = self.get_validated_token(raw_token.encode()
                                                        if isinstance(raw_token, str)
                                                        else raw_token)
            return self.get_user(validated_token), validated_token
        except TokenError as e:
            # Token is present but invalid/expired — raise so the client
            # gets a 401 rather than silently treating them as anonymous.
            raise AuthenticationFailed(str(e))




