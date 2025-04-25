from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from teams.models import Profile
from teams.templatetags.teams_custom_filters import get_current_position

def can_approve_proforma(user):
        
    try:

        user_profile = get_object_or_404(Profile, user = user)
        current_position = get_current_position(user_profile)

        if current_position in ['Head', 'VP', 'Sr. Executive']:
            return True
    except Profile.DoesNotExist:
        return False

    return False
    
def proforma_approval_required(view_func):

    def _wrapped_view(request, *args, **kwargs):
        if not can_approve_proforma(request.user):
            return redirect('permission_denied')  # Redirect if the user doesn't have permission
        return view_func(request, *args, **kwargs)
    return _wrapped_view