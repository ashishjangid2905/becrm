from django.shortcuts import render, get_object_or_404

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .permissions import IsAdminRole

from billers.models import *
from billers.serializers import *


class BillerView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get(self, request):
        billers_list = Biller.objects.filter()