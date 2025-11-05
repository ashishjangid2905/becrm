from django.db import IntegrityError
from django.utils import timezone
from .models import *
from .serializers import *
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView
from rest_framework.mixins import ListModelMixin, CreateModelMixin, UpdateModelMixin, RetrieveModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from teams.permissions import IsAdminRole


class BillerListCreateView(ListModelMixin, CreateModelMixin, RetrieveModelMixin, UpdateModelMixin, GenericAPIView):
    serializer_class = BillerSerializer
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get_queryset(self):
        """Return all billers for the logged-in user’s branch."""
        branch = self.request.user.profile.branch
        return Biller.objects.filter(branch=branch.id)

    def get(self, request, *args, **kwargs):
        """Handle both list and retrieve."""
        if 'pk' in kwargs:
            return self.retrieve(request, *args, **kwargs)
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """Create a new Biller."""
        try:
            user = request.user
            branch = user.profile.branch.id

            data = request.data.copy()
            data["inserted_by"] = user.id
            data["branch"] = branch

            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except IntegrityError as ie:
            print(str(ie))
            raise ValidationError({"error": "Biller with same name and GSTIN already exists."})
        except Exception as e:
            raise ValidationError({"error": str(e)})

    def patch(self, request, *args, **kwargs):
        """Partial update for an existing Biller."""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(edited_at=timezone.now())
        return Response(serializer.data, status=status.HTTP_200_OK)


class BankListCreateUpdateView(ListModelMixin, CreateModelMixin, UpdateModelMixin, GenericAPIView):
    serializer_class = BankDetailSerializer
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get_queryset(self):
        request = self.request
        branch = request.user.profile.branch
        queryset = BankDetail.objects.filter(branch=branch.id)

        biller = self.kwargs.get("biller_id", None)
        if biller:
            queryset = queryset.filter(biller=biller)
        return queryset
    
    def get(self, request, *args, **kwargs):
        """Handle list of Bank Accounts"""
        return self.list(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        """Add new Bank Account Details"""
        try:
            if not 'biller_id' in kwargs:
                return Response({"error": "Choose biller to add bank a/c details"}, status=status.HTTP_400_BAD_REQUEST)
            
            user = request.user
            branch = user.profile.branch.id

            data = request.data.copy()
            data["inserted_by"] = user.id
            data["branch"] = branch

            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except IntegrityError:
            raise ValidationError({"error": "Bank with same name and Account No already exists."})
        except Exception as e:
            raise ValidationError({"error": str(e)})
    
    def patch(self, request, *args, **kwargs):
        """Update Bank Account details"""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    