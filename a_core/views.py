from django.shortcuts import render

from .models import *
from .serializers import *
from rest_framework.viewsets import ModelViewSet
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


class BranchLabelViewset(ModelViewSet):
    queryset = BranchLabel.objects.all()
    serializer_class = BranchLabelSerializer
    permission_classes = [IsAuthenticated]

