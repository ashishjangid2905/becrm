from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.template import loader
from teams.models import Profile, Branch, User, UserVariable
from sample.models import sample
from invoice.models import proforma, orderList
from invoice.templatetags.custom_filters import total_order_value, sale_category
from teams.templatetags.teams_custom_filters import get_current_position, get_current_target
from invoice.utils import STATUS_CHOICES
from django.db.models import Count, Q, Min, Max
from django.db.models.functions import ExtractMonth, TruncDate
from django.http import JsonResponse
import calendar
from datetime import timedelta, datetime
from django.utils.timezone import now

from .activity_log_utils import log_user_activity, get_action
from .models import ActivityLog
from .tasks import dashboard_data
from celery.result import AsyncResult
from django.core.cache import cache
# Create your views here.

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny


class CustomTokenObtainPairView(TokenObtainPairView):
    permission_classes = (AllowAny,)


class Home(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        content = {'message': 'hello world'}
        return Response(content)



@login_required(login_url='app:login')
def home(request):
    if not request.user.is_authenticated:
        return redirect('app:login')
    
    user_profile = get_object_or_404(Profile, user=request.user)

    user_branch = user_profile.branch
    all_users = Profile.objects.filter(branch=user_branch).select_related('user')
    
    # user_target_variable = UserVariable.objects.filter(variable_name = 'sales_target', user_profile=user_profile).last()

    user_target_variable = get_current_target(user_profile)

    user_target = int(user_target_variable)/1000 if user_target_variable else 0

    user_details = {
        'user_id': request.user.id,
        'team_member': request.user.full_name(),
        'role': request.user.role,
        'department': request.user.department
    }

    context = {
        'user_id': request.user.id,
        'user_details': user_details,
        'user_target': user_target,
        'all_users': all_users
    }

    return render(request, 'dashboard/dashboard.html', context)

@login_required(login_url='app:login')
def dashboard(request):

    user_id = request.user.id
    selected_fy = request.GET.get('fy', None)

    selected_month = request.GET.get('select_month')
    selected_user = request.GET.get('select_user')

    task = dashboard_data.apply_async(args=[user_id,selected_fy, selected_user, selected_month])

    return JsonResponse({'task_id': task.id, 'status': 'Processing'}, status=202)


@login_required(login_url='app:login')
def check_dashboard_status(request, task_id):

    cache_key = f'dashboard_{task_id}'
    cache_data = cache.get(cache_key)

    if cache_data:
        data = cache_data
        return JsonResponse({'status': 'Completed', 'data': data}, safe=False)

    task_result = AsyncResult(task_id)

    if task_result.ready():  # Task is completed
        if task_result.successful():
            data = task_result.result
            cache.set(cache_key, data, timeout=300)
            return JsonResponse({'status': 'Completed', 'data': data}, safe=False)
        else:
            return JsonResponse({'status': 'Failed', 'error': str(task_result.result)})

    return JsonResponse({'status': 'Processing'})



def login_user(request):
    if request.method == 'POST':
        email =  request.POST['email']
        password =  request.POST['password']

        user = authenticate(request, email=email, password=password)
        if user is not None:

            login(request, user)
            return redirect('app:home')
        else:
            messages.success(request, "There was an Error, Please Try again")
            return redirect('app:login')
    elif request.user.is_authenticated:
        return redirect('app:home')
    else:
        return render(request, 'login.html')

@login_required
def logout_user(request):

    action = get_action(request)

    if action:
        log_user_activity(request, action)

    logout(request)
    messages.success(request,"You have Logged Out")
    return redirect('app:login')

@login_required
def settings(request):
    if request.user.role != 'admin':
        return redirect('teams:user_password')
    
    return render(request,'admin/settings.html')

@login_required(login_url='app:login')
def logs(request):
    if not request.user.is_authenticated:
        return redirect('app:login')
    
    activity_logs = ActivityLog.objects.all()

    context = {
        'activity_logs': activity_logs,
    }

    return render(request, 'activity_log.html', context)


def custom_page_not_found(request, exception):
    return render(request, 'error/page404.html', status=404)