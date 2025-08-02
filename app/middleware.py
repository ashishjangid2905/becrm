from datetime import datetime
from user_agents import parse
from .models import ActivityLog
from .activity_log_utils import log_user_activity, get_action
from django.utils.deprecation import MiddlewareMixin
from rest_framework_simplejwt.authentication import JWTAuthentication

class ActivityLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.user.is_authenticated:
            print(request.path)
            action = get_action(request)
        
            if action:
                log_user_activity(request, action)
        
        return response
    
    def log_session_timeout(self, request):
        """Log activity when session times out."""
        action = 'Session timed out'

        # Log the session timeout event
        log_user_activity(request, action)



class JWTActivityLogMiddleware(MiddlewareMixin):
    def process_request(self, request):

        jwt_auth = JWTAuthentication()
        try:
            user_auth_tuple = jwt_auth.authenticate(request)
            if user_auth_tuple:
                request.user, _ = user_auth_tuple
        except Exception:
            request.user = None

    def process_view(self, request, view_func, view_args, view_kwargs):
        if hasattr(request, "user") and request.user and request.user.is_authenticated:
            action = get_action(request)
            if action:
                log_user_activity(request, action)