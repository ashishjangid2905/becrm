from datetime import datetime
from user_agents import parse
from .models import ActivityLog


def log_user_activity(request, action):

    ip = get_client_ip(request)
    browser_info = get_browser_info(request)

    if action:
        ActivityLog.objects.create(
            user = request.user,
            action = action,
            ip_address = ip,
            timestamp = datetime.now(),
            extra_info = {
                'method': request.method,
                'path': request.path,
                'query_params': request.GET.dict(),
                'browser': browser_info,
            }
        )
        
@staticmethod
def get_action(request):
    if request.path == '/logout/':
        return 'User logged out'
    elif '/login' in request.path:
        return 'User logged in'
    elif '/pdf' in request.path:
        return 'Download PI'
    elif 'export' in request.GET:
        return 'Invoice-list Exported in Excel file.'
    return None
    
@staticmethod
def get_client_ip(request):

    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')
    
@staticmethod
def get_browser_info(request):

    user_agent_string = request.META.get('HTTP_USER_AGENT', '')
    user_agent = parse(user_agent_string)

    return {
        'browser': user_agent.browser.family,
        'browser_version': user_agent.browser.version_string,
        'os': user_agent.os.family,
        'os_version': user_agent.os.version_string,
        'device': user_agent.device.family,
    }