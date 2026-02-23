"""
accounts/middleware.py
-----------------------
CookieTokenRefreshMiddleware
    Sits in front of every view. On each request it checks whether:
      - the access token cookie is missing / expired, AND
      - a refresh token cookie is present.

    If both conditions are met it silently rotates both tokens and:
      1. Injects the new access token onto request._refreshed_access so that
         CookieJWTAuthentication can validate the request in the same cycle.
      2. After the view returns, writes the fresh access + refresh cookies
         onto the response.

    ROLLBACK SAFETY
    ───────────────
    The new tokens are only committed (written to the response) if the
    rotation step succeeds completely.  If RefreshToken() raises (expired,
    blacklisted, tampered), the request is allowed to proceed *without*
    deleting the existing cookies — the user's session state is preserved
    and the protected endpoint will simply return 401 if it requires auth.

    This avoids a nasty race condition where a tab was slow and the refresh
    cookie gets deleted before it had a chance to use it.
"""

from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken

from .cookie_utils import (
    set_auth_cookies,
    ACCESS_NAME  as ACCESS_COOKIE_NAME,
    REFRESH_NAME as REFRESH_COOKIE_NAME,
)


class CookieTokenRefreshMiddleware:
    """
    WSGI-style middleware (Django's new-style __call__ middleware).
    Add to settings.MIDDLEWARE after 'corsheaders.middleware.CorsMiddleware'.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Placeholders — filled if we successfully rotate tokens
        new_access   = None
        new_refresh  = None

        # ── Check if we should attempt a refresh ──────────────────────────
        access_cookie   = request.COOKIES.get(ACCESS_COOKIE_NAME)
        refresh_cookie  = request.COOKIES.get(REFRESH_COOKIE_NAME)

        if refresh_cookie and not access_cookie:
            # Access token is gone (expired / cleared) but refresh exists.
            # Attempt rotation — wrapped in a full try/except for rollback.
            try:
                old_refresh     = RefreshToken(refresh_cookie)
                new_access_tok  = old_refresh.access_token
                # Rotate: create a brand-new refresh token
                old_refresh.set_jti()
                old_refresh.set_exp()

                new_access  = str(new_access_tok)
                new_refresh = str(old_refresh)

                # Inject the fresh access token so CookieJWTAuthentication
                # can authenticate this request in the same request cycle.
                request._refreshed_access = new_access

            except (TokenError, InvalidToken, Exception):
                # ROLLBACK: rotation failed — do NOT touch any cookies.
                # The request continues; protected endpoints will 401.
                pass

        # ── Let the view run ──────────────────────────────────────────────
        response = self.get_response(request)

        # ── Post-response: write fresh cookies if rotation succeeded ──────
        if new_access and new_refresh:
            set_auth_cookies(response, access_token=new_access, refresh_token=new_refresh)

        return response
