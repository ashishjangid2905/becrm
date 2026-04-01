from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.authentication import JWTAuthentication

User = get_user_model()

class JWTAuthFromCookieMiddleware(MiddlewareMixin):
    def process_request(self, request):
        access_token = request.COOKIES.get(settings.ACCESS_TOKEN_NAME)

        if not access_token:
            request.user = AnonymousUser()
            return

        try:
            UntypedToken(access_token)  # Validate token signature
            validated_user = JWTAuthentication().get_user(
                JWTAuthentication().get_validated_token(access_token)
            )
            request.user = validated_user
        except (InvalidToken, TokenError):
            request.user = AnonymousUser()
