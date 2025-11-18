from django.db import transaction, IntegrityError
from teams.models import Profile, Branch, User, UserVariable, SmtpConfig
from django.shortcuts import get_object_or_404
from datetime import datetime, timedelta
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import json

from datetime import datetime as dt

from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import UpdateAPIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.exceptions import ValidationError
from .permissions import IsAdminRole
from .serializers import *

User = get_user_model()


class UserDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = get_object_or_404(User, pk=request.user.id)
        serializer = UserListSerializer(user, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class UserListDashboardView(APIView):
    # queryset = User.objects.all()
    serializer_class = UserListSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile_instance = get_object_or_404(Profile, user=request.user)
        branch_id = profile_instance.branch
        users = User.objects.filter(profile__branch=branch_id).order_by("first_name")
        current_position = get_current_position(profile_instance)

        # user_exclusion = {
        #     "Head": {"Head"},
        #     "VP": {"Head", "VP"},
        #     "Sr. Executive": {"Head", "VP", "Sr. Executive"},
        # }

        # if request.user.role != "admin":
        #     if current_position in user_exclusion:
        #         users = users.exclude(groups__name__in=user_exclusion[current_position])

        serializers = UserListSerializer(users, many=True, context={"request": request})
        return Response(serializers.data)


class UserListView(APIView):
    # queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile_instance = get_object_or_404(Profile, user=request.user)
        branch_id = profile_instance.branch
        users = User.objects.filter(profile__branch=branch_id).order_by("first_name")
        current_position = get_current_position(profile_instance)

        user_exclusion = {
            "Head": {"Head"},
            "VP": {"Head", "VP"},
            "Sr. Executive": {"Head", "VP", "Sr. Executive"},
        }

        if request.user.role != "admin":
            if current_position in user_exclusion:
                users = users.exclude(groups__name__in=user_exclusion[current_position])

        serializers = UserListSerializer(users, many=True, context={"request": request})
        return Response(serializers.data)

    def post(self, request):
        try:
            data = request.data
            profile_data = data.pop("profile")
            if not profile_data:
                return Response(
                    {"profile": "This field is required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            with transaction.atomic():
                user_serializer = UserSerializer(data=data)
                if not user_serializer.is_valid():
                    raise IntegrityError(
                        user_serializer.errors, status=status.HTTP_400_BAD_REQUEST
                    )
                user = user_serializer.save()

                profile_data["user"] = user.id
                profile_data["branch"] = request.user.profile.branch.id
                if profile_data["dob"] == "":
                    profile_data["dob"] = None

                profile_serializer = ProfileSerializer(data=profile_data)
                if not profile_serializer.is_valid():
                    raise IntegrityError(
                        profile_serializer.errors, status=status.HTTP_400_BAD_REQUEST
                    )
                profile_serializer.save()

                result_serializer = UserListSerializer(
                    user, context={"request": request}
                )

                return Response(result_serializer.data, status=status.HTTP_201_CREATED)

        except IntegrityError as ie:
            return Response({"error": str(ie)}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, *args, **kwargs):
        try:
            user = get_object_or_404(User, pk=kwargs.get("pk"))

            user_data = request.data
            profile_data = user_data.pop("profile")
            profile_data["user_id"] = user

            user_serializer = UserSerializer(user, data=user_data, partial=True)

            profile_serializer = ProfileSerializer(
                user.profile, data=profile_data, partial=True
            )

            with transaction.atomic():
                if not profile_serializer.is_valid():
                    return Response(
                        profile_serializer.errors, status=status.HTTP_400_BAD_REQUEST
                    )
                if not user_serializer.is_valid():
                    return Response(
                        user_serializer.errors, status=status.HTTP_400_BAD_REQUEST
                    )

                user_serializer.save(partial=True)
                profile_serializer.save(partial=True)

                result_serializer = UserListSerializer(
                    user, context={"request": request}
                )
                return Response(result_serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class UserUpdateView(UpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        user = self.get_object()
        data = request.data
        serializer = self.get_serializer(
            user, data=data, partial=True, context={"request": request}
        )
        try:
            serializer.is_valid(raise_exception=True)
            serializer.save()
        except ValidationError as ve:
            return Response(ve.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
        result = UserListSerializer(user, context={"request": request})
        return Response(result.data, status=status.HTTP_200_OK)


class UserProfileUpdateView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def patch(self, request, *args, **kwargs):

        user = get_object_or_404(User, pk=kwargs.get("id"))

        user_data = {
            "first_name": request.data.get("first_name"),
            "last_name": request.data.get("last_name"),
        }
        profile_data = {
            "dob_str": request.data.get("profile[dob]"),
            "gender": request.data.get("profile[gender]"),
            "phone": request.data.get("profile[phone]"),
            "profile_img": request.FILES.get("profile[profile_img]"),
        }

        user_serializer = UserSerializer(user, data=user_data, partial=True)
        profile_serializer = ProfileSerializer(
            user.profile, data=profile_data, partial=True
        )

        with transaction.atomic():
            try:
                if not user_serializer.is_valid():
                    raise ValidationError(
                        user_serializer.errors, status=status.HTTP_400_BAD_REQUEST
                    )
                if not profile_serializer.is_valid():
                    raise ValidationError(
                        profile_serializer.errors, status=status.HTTP_400_BAD_REQUEST
                    )

                user_serializer.save()
                profile_serializer.save()

                result = UserListSerializer(user, context={"request": request})
                return Response(result.data, status=status.HTTP_200_OK)
            except ValidationError as ve:
                return Response(ve.detail, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response({str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CreateUpdateUserVariableView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def post(self, request, id):
        try:
            profile = get_object_or_404(Profile, user=id)
            data = request.data

            user_id = data.pop("user")
            with transaction.atomic():
                user_profile = get_object_or_404(Profile, user=user_id)
                curr_target = (
                    UserVariable.objects.filter(
                        user_profile=user_profile, variable_name="sales_target"
                    )
                    .order_by("created_at")
                    .last()
                )
                from_date = datetime.strptime(data.get("from_date"), "%Y-%m-%d").date()
                if curr_target:
                    if from_date <= curr_target.from_date:
                        raise IntegrityError(
                            "New Target cannot be set earlier than or equal to the current target's start date."
                        )

                    if curr_target.from_date == from_date:
                        curr_target.to_date = from_date
                    else:
                        curr_target.to_date = from_date - timedelta(days=1)
                    curr_target.save()

                serializer = UserVariableSerializer(data=data)
                serializer.is_valid(raise_exception=True)
                serializer.save(user_profile=user_profile)

                result = get_object_or_404(User, id=id)
                result_serializer = UserListSerializer(
                    result, context={"request": request}
                )

                return Response(result_serializer.data, status=status.HTTP_201_CREATED)

        except IntegrityError as ie:
            return Response({"error": str(ie)}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
