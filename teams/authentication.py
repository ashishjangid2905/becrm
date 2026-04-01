from rest_framework_simplejwt.authentication import JWTAuthentication
from django.conf import settings

class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        access_token = request.COOKIES.get(settings.ACCESS_TOKEN_NAME)

        # print(access_token)

        if not access_token:
            return None
        
        # Pretend this token is in the Authorization header
        request.META['HTTP_AUTHORIZATION'] = f"Bearer {access_token}"

        return super().authenticate(request)