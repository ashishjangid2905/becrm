from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages, auth
from django.template import loader
from django.db.models import Q
from django.db import transaction, IntegrityError
from teams.models import Profile, Branch, User, UserVariable, SmtpConfig
from django.shortcuts import get_object_or_404
from datetime import datetime, timedelta
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import json

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .permissions import IsAdminRole
from .serializers import *


class UserListView(APIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get(self, request):
        profile_instance = get_object_or_404(Profile, user=request.user)
        branch_id = profile_instance.branch
        users = User.objects.filter(profile__branch=branch_id)
        # users = User.objects.all()
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

            print(user_data)

            user_serializer = UserSerializer(user, data=user_data, partial=True)

            profile_serializer = ProfileSerializer(user.profile,data=profile_data, partial=True)

            with transaction.atomic():
                if not profile_serializer.is_valid():
                    return Response(profile_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                if not user_serializer.is_valid():
                    return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

                user_serializer.save(partial=True)
                profile_serializer.save(partial=True)

                result_serializer = UserListSerializer(user, context={"request": request})
                return Response(result_serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


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


@login_required(login_url="app:login")
def user_list(request):

    profile_instance = get_object_or_404(Profile, user=request.user)
    user_branch = profile_instance.branch
    all_users = Profile.objects.filter(user__profile__branch=user_branch.id)

    role_choices = User.ROLE
    department_choices = User.DEPARTMENT

    branch = Branch.objects.all()

    context = {
        "all_users": all_users,
        "role_choices": role_choices,
        "department_choices": department_choices,
        "user_branch": user_branch,
        "profile_instance": profile_instance,
        "branch": branch,
    }

    if not request.user.is_authenticated:
        return redirect("app:login")

    if request.user.role == "admin":
        return render(request, "admin/users.html", context)

    return redirect("app:home")


@login_required(login_url="app:login")
def add_user(request):

    role_choices = User.ROLE
    department_choices = User.DEPARTMENT

    branch = Branch.objects.all()

    context = {
        "role_choices": role_choices,
        "department_choices": department_choices,
        "branch": branch,
    }

    if request.user.is_authenticated:
        if request.user.role == "admin":
            if request.method == "POST":
                first_name = request.POST.get("first_name")
                last_name = request.POST.get("last_name")
                email = request.POST.get("email")
                role = request.POST.get("chooseRole")
                department = request.POST.get("chooseDepartment")
                password = request.POST.get("createPass")
                confirm_password = request.POST.get("confirmPass")
                if password != confirm_password:
                    messages.error(request, "Password do not match")
                    return redirect("teams:add_user")

                user = User.objects.create(
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    role=role,
                    department=department,
                    password=make_password(password),
                )

                branch_name = request.POST.get("chooseBranch")
                branch = get_object_or_404(Branch, branch_name=branch_name)
                phone = request.POST.get("contact")

                profile = Profile.objects.create(user=user, branch=branch, phone=phone)
                return redirect("teams:users")
            return render(request, "admin/add-user.html", context)
        return redirect("app:home")
    return redirect("app:login")


@login_required(login_url="app:login")
def edit_user(request, user_id):

    user_instance = get_object_or_404(User, pk=user_id)
    profile_instance = get_object_or_404(Profile, user=user_instance)
    role_choices = User.ROLE
    department_choices = User.DEPARTMENT

    chooseBranch = Branch.objects.all()

    context = {
        "role_choices": role_choices,
        "department_choices": department_choices,
        "chooseBranch": chooseBranch,
        "user_instance": user_instance,
        "profile_instance": profile_instance,
    }

    if request.user.is_authenticated:
        if request.user.role == "admin":
            if request.method == "POST":
                first_name = request.POST.get("first_name")
                last_name = request.POST.get("last_name")
                email = request.POST.get("email")
                role = request.POST.get("chooseRole")
                department = request.POST.get("chooseDepartment")

                # Update the sample object with the new data

                user_instance.first_name = first_name
                user_instance.last_name = last_name
                user_instance.email = email
                user_instance.role = role
                user_instance.department = department

                user_instance.save()

                branch_name = request.POST.get("chooseBranch")
                branch_instance = get_object_or_404(Branch, branch_name=branch_name)
                phone = request.POST.get("contact")
                user_profile = Profile.objects.get(user=user_instance)
                user_profile.branch = branch_instance
                user_profile.phone = phone

                user_profile.save()

                return redirect("teams:users")
            return render(request, "admin/edit-user.html", context)
        return redirect("app:home")
    return redirect("app:login")


# Change Password by User itself or admin


@login_required(login_url="app:login")
def change_password(request, user_id):
    if not request.user.is_authenticated:
        return redirect("app:login")

    user = get_object_or_404(User, pk=user_id)

    context = {"user_email": user}

    if request.user.role == "admin":
        if request.method == "POST":
            new_password = request.POST.get("new_password")
            confirm_password = request.POST.get("confirm_password")
            if new_password != confirm_password:
                messages.error(request, "Password do not match")
                return redirect("teams:add_user")
            user.password = make_password(new_password)
            user.save()

            messages.success(request, "Password has been Changed successfully")
            return redirect("teams:users")
        return render(request, "success/change-password.html", context)

    return redirect("app:home")


@login_required(login_url="app:login")
def user_password(request):
    if not request.user.is_authenticated:
        return redirect("app:login")
    if not request.user.is_staff:
        user = request.user

        context = {"user_email": user}
        if request.method == "POST":
            old_password = request.POST.get("old_password")
            new_password = request.POST.get("new_password")
            confirm_password = request.POST.get("confirm_password")

            if not check_password(old_password, user.password):
                messages.error(request, "old Password do not match, Please try again")
                return redirect("teams:user_password")

            if new_password != confirm_password:
                messages.error(request, "Password do not match")
                return redirect("teams:user_password")
            user.password = make_password(new_password)
            user.save()

            update_session_auth_hash(request, user)

            messages.success(request, "Password has been Changed successfully")
            return redirect("app:home")
    else:
        user = request.user

        context = {"user_email": user}
        if request.method == "POST":
            old_password = request.POST.get("old_password")
            new_password = request.POST.get("new_password")
            confirm_password = request.POST.get("confirm_password")

            if not check_password(old_password, user.password):
                messages.error(request, "old Password do not match, Please try again")
                return redirect("teams:user_password")

            if new_password != confirm_password:
                messages.error(request, "Password do not match")
                return redirect("teams:user_password")
            user.password = make_password(new_password)
            user.save()

            update_session_auth_hash(request, user)

            messages.success(
                request,
                "Password has been Changed successfully",
                extra_tags="user-password",
            )

            return redirect("app:home")

    return render(request, "success/change-password_user.html", context)


@login_required(login_url="app:login")
def branch_list(request):
    if not request.user.is_authenticated:
        return redirect("app:login")

    if not request.user.role == "admin":
        return redirect("app:home")

    branch_list = Branch.objects.all()

    context = {"branch_list": branch_list}

    return render(request, "admin/branches.html", context)


@login_required(login_url="app:login")
def add_branch(request):
    if not request.user.is_authenticated:
        return redirect("app:login")
    if request.user.role == "admin":
        if request.method == "POST":
            branch_name = request.POST.get("branch_name")
            address = request.POST.get("building_Name")
            street = request.POST.get("street_name")
            city = request.POST.get("city")
            state = request.POST.get("state")
            postcode = request.POST.get("pincode")
            country = request.POST.get("country")
            branch = Branch.objects.create(
                branch_name=branch_name,
                address=address,
                street=street,
                city=city,
                state=state,
                postcode=postcode,
                country=country,
            )
            return redirect("teams:branch_list")
        return render(request, "admin/add-branch.html")


def edit_branch(request, branch_id):
    if not request.user.is_authenticated:
        return redirect("app:login")

    branch_instance = get_object_or_404(Branch, pk=branch_id)

    context = {"branch_instance": branch_instance}

    if request.user.role == "admin":
        if request.method == "POST":
            branch_name = request.POST.get("branch_name")
            address = request.POST.get("building_Name")
            street = request.POST.get("street_name")
            city = request.POST.get("city")
            state = request.POST.get("state")
            postcode = request.POST.get("pincode")
            country = request.POST.get("country")

            # Update Branch Details

            branch_instance.branch_name = branch_name
            branch_instance.address = address
            branch_instance.street = street
            branch_instance.city = city
            branch_instance.state = state
            branch_instance.postcode = postcode
            branch_instance.country = country

            branch_instance.save()

            return redirect("teams:branch_list")
        return render(request, "admin/edit-branch.html", context)


@login_required(login_url="app:login")
def profile(request):
    if not request.user.is_authenticated:
        return redirect("app:login")
    user = request.user
    user_profile = Profile.objects.all().filter(user=user)

    context = {
        "user_profile": user_profile,
    }

    return render(request, "user/profile.html", context)


def get_user_variable(user_profile, variable_name):
    today = datetime.now().date()

    filters = {
        "from_date__lte": today,
        "user_profile": user_profile,
        "variable_name": variable_name,
    }

    variable = UserVariable.objects.filter(
        Q(to_date__gte=today) | Q(to_date__isnull=True), **filters
    ).last()

    return variable.variable_value if variable else None


@login_required(login_url="app:login")
def set_target(request, user_id):

    if request.user.role != "admin":
        return redirect("app:dashboard")

    user_profile = get_object_or_404(Profile, pk=user_id)

    if request.method == "POST":
        sales_target = request.POST.get("sale_target")
        from_date_str = request.POST.get("from_date")
        variable_name = "sales_target"

        try:
            from_date = datetime.strptime(from_date_str, "%Y-%m-%d").date()
        except ValueError:
            messages.error(request, "Invalid Date format")
            return redirect("teams:users")

        currentTarget = UserVariable.objects.filter(
            user_profile=user_profile, variable_name=variable_name
        ).last()
        if currentTarget:
            currentTarget.to_date = from_date - timedelta(days=1)
            currentTarget.save()

        newTarget = UserVariable.objects.create(
            user_profile=user_profile,
            variable_name=variable_name,
            variable_value=sales_target,
            from_date=from_date,
        )
        messages.success(
            request, f"{user_profile} target {sales_target} is set successfully"
        )
        return redirect("teams:users")
