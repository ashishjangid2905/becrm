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
                        END BETWEEN %s AND %s AND p.branch = ({branch})
                    GROUP BY
                        p.user_id, p.user_name, 
                        CASE
                            WHEN p.closed_at IS NULL THEN FORMAT(p.pi_date, 'yyyy-MM') 
                            ELSE FORMAT(p.closed_at, 'yyyy-MM') 
                        END, p.status
                    ORDER BY
                        pi_month, p.user_id
               """.format(branch=profile_instance.branch.id)

        total_clients_query = """
                            SELECT
                                l.[user] AS user_id,
                                COUNT(*) AS clients 
                            FROM Leads l
                            WHERE l.[user] IS NOT NULL AND l.[branch] = ({branch})
                                AND EXISTS (
                                    SELECT 1
                                    FROM Proforma_Invoice p
                                    WHERE p.company_ref_id = l.id
                                        AND p.status = 'closed'
                                        AND p.[user_id] = l.[user]
                                )
                            GROUP BY l.[user]
                        """.format(branch=profile_instance.branch.id)

        with connections["leads_db"].cursor() as cursor:
            cursor.execute(query, [start_date, end_date])

            columns = [col[0] for col in cursor.description]
            pi_summery = [dict(zip(columns, row)) for row in cursor.fetchall()]

            cursor.execute(total_clients_query)
            columns = [col[0] for col in cursor.description]
            total_clients = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
        return Response({"result":pi_summery, "total_clients":total_clients}, status=status.HTTP_200_OK)

