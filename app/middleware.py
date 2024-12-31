from datetime import datetime
from user_agents import parse
from .models import ActivityLog
from .activity_log_utils import log_user_activity, get_action

class ActivityLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.user.is_authenticated:
            action = get_action(request)
        
            if action:
                log_user_activity(request, action)
        
        return response
    
    def log_session_timeout(self, request):
        """Log activity when session times out."""
        action = 'Session timed out'

        # Log the session timeout event
        log_user_activity(request, action)