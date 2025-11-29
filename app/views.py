from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.template import loader
from teams.models import Profile, Branch, User, UserVariable
from sample.models import sample
from invoice.models import proforma, orderList
from invoice.templatetags.custom_filters import total_order_value, sale_category
from teams.templatetags.teams_custom_filters import (
    get_current_position,
    get_current_target,
)
from invoice.utils import STATUS_CHOICES
from django.db import connections
from django.db.models import Count, Q, Min, Max
from django.db.models.functions import ExtractMonth, TruncDate
from django.http import JsonResponse
import calendar
from datetime import timedelta, datetime as dt
from django.utils.timezone import now

from .activity_log_utils import log_user_activity, get_action
from .models import ActivityLog
from .tasks import dashboard_data
from celery.result import AsyncResult
from django.core.cache import cache

# Create your views here.

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny
from teams.serializers import MyTokenObtainPairSerializer
from .serializers import DashboardSaleSerializer
from invoice.custom_utils import current_fy


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        access_token = response.data["access"]
        refresh_token = response.data["refresh"]

        response.set_cookie(
            "access_token", access_token, httponly=True, secure=True, samesite="None"
        )
        response.set_cookie(
            "refresh_token", refresh_token, httponly=True, secure=True, samesite="None"
        )

        return response


class Home(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        profile_instance = get_object_or_404(Profile, user=request.user)
        all_users = User.objects.filter(
            profile__branch=profile_instance.branch
        ).values_list("id", flat=True)

        fy = current_fy()
        start_date = dt(int(fy.split("-")[0]), 4, 1).date()
        end_date = dt.now()

        query = """
                    SELECT
                        p.user_id,
                        p.user_name,
                        p.status,
                        CASE
                            WHEN p.closed_at IS NULL THEN FORMAT(p.pi_date, 'yyyy-MM') 
                            ELSE FORMAT(p.closed_at, 'yyyy-MM') 
                        END AS pi_month,
                        COUNT(p.pi_no) AS total_pi,
                        SUM(s.total_amount_in_inr) AS total_sale,
                        SUM(s.online_sale) AS total_online_sale,
                        SUM(s.offline_sale) AS total_offline_sale,
                        SUM(s.other_sale) AS total_other_sale
                    FROM
                        Proforma_Invoice p
                    JOIN
                        PiSummary s on p.id = s.proforma_id
                    WHERE
                    	CASE
                            WHEN p.closed_at IS NULL THEN p.pi_date 
                            ELSE p.closed_at
                        END BETWEEN %s AND %s AND p.user_id IN ({user_ids})
                    GROUP BY
                        p.user_id, p.user_name, 
                        CASE
                            WHEN p.closed_at IS NULL THEN FORMAT(p.pi_date, 'yyyy-MM') 
                            ELSE FORMAT(p.closed_at, 'yyyy-MM') 
                        END, p.status
                    ORDER BY
                        pi_month, p.user_id
               """.format(
            user_ids=",".join(str(u) for u in all_users)
        )

        total_clients_query = """
                            SELECT
                                l.[user] AS user_id,
                                COUNT(*) AS clients 
                            FROM Leads l
                            WHERE l.[user] IS NOT NULL
                                AND EXISTS (
                                    SELECT 1
                                    FROM Proforma_Invoice p
                                    WHERE p.company_ref_id = l.id
                                        AND p.status = 'closed'
                                        AND p.[user_id] = l.[user]
                                )
                            GROUP BY l.[user]
                        """

        with connections["leads_db"].cursor() as cursor:
            cursor.execute(query, [start_date, end_date])

            columns = [col[0] for col in cursor.description]
            pi_summery = [dict(zip(columns, row)) for row in cursor.fetchall()]

            cursor.execute(total_clients_query)
            columns = [col[0] for col in cursor.description]
            total_clients = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
        return Response({"result":pi_summery, "total_clients":total_clients}, status=status.HTTP_200_OK)


@login_required(login_url="app:login")
def home(request):
    if not request.user.is_authenticated:
        return redirect("app:login")

    user_profile = get_object_or_404(Profile, user=request.user)

    user_branch = user_profile.branch
    all_users = Profile.objects.filter(branch=user_branch).select_related("user")

    # user_target_variable = UserVariable.objects.filter(variable_name = 'sales_target', user_profile=user_profile).last()

    user_target_variable = get_current_target(user_profile)

    user_target = int(user_target_variable) / 1000 if user_target_variable else 0

    user_details = {
        "user_id": request.user.id,
        "team_member": request.user.full_name(),
        "role": request.user.role,
        "department": request.user.department,
    }

    context = {
        "user_id": request.user.id,
        "user_details": user_details,
        "user_target": user_target,
        "all_users": all_users,
    }

    return render(request, "dashboard/dashboard.html", context)


@login_required(login_url="app:login")
def dashboard(request):

    user_id = request.user.id
    selected_fy = request.GET.get("fy", None)

    selected_month = request.GET.get("select_month")
    selected_user = request.GET.get("select_user")

    task = dashboard_data.apply_async(
        args=[user_id, selected_fy, selected_user, selected_month]
    )

    return JsonResponse({"task_id": task.id, "status": "Processing"}, status=202)


@login_required(login_url="app:login")
def check_dashboard_status(request, task_id):

    cache_key = f"dashboard_{task_id}"
    cache_data = cache.get(cache_key)

    if cache_data:
        data = cache_data
        return JsonResponse({"status": "Completed", "data": data}, safe=False)

    task_result = AsyncResult(task_id)

    if task_result.ready():  # Task is completed
        if task_result.successful():
            data = task_result.result
            cache.set(cache_key, data, timeout=300)
            return JsonResponse({"status": "Completed", "data": data}, safe=False)
        else:
            return JsonResponse({"status": "Failed", "error": str(task_result.result)})

    return JsonResponse({"status": "Processing"})


def login_user(request):
    if request.method == "POST":
        email = request.POST["email"]
        password = request.POST["password"]

        user = authenticate(request, email=email, password=password)
        if user is not None:

            login(request, user)
            return redirect("app:home")
        else:
            messages.success(request, "There was an Error, Please Try again")
            return redirect("app:login")
    elif request.user.is_authenticated:
        return redirect("app:home")
    else:
        return render(request, "login.html")


@login_required
def logout_user(request):

    action = get_action(request)

    if action:
        log_user_activity(request, action)

    logout(request)
    messages.success(request, "You have Logged Out")
    return redirect("app:login")


@login_required
def settings(request):
    if request.user.role != "admin":
        return redirect("teams:user_password")

    return render(request, "admin/settings.html")


@login_required(login_url="app:login")
def logs(request):
    if not request.user.is_authenticated:
        return redirect("app:login")

    activity_logs = ActivityLog.objects.all()

    context = {
        "activity_logs": activity_logs,
    }

    return render(request, "activity_log.html", context)


def custom_page_not_found(request, exception):
    return render(request, "error/page404.html", status=404)
