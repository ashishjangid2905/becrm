from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.hashers import make_password
from .models import User, Profile, Branch, UserVariable, SmtpConfig
from django.shortcuts import get_object_or_404
from datetime import datetime, timedelta
from django.db.models import Q
from .templatetags.teams_custom_filters import get_current_position, get_current_target


class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = "__all__"


class UserVariableSerializer(serializers.ModelSerializer):
    from_date = serializers.DateField(required=True, allow_null=False)
    to_date = serializers.DateField(required=False, allow_null=True)

    class Meta:
        model = UserVariable
        fields = [
            "id",
            "variable_name",
            "variable_value",
            "from_date",
            "to_date",
            "created_at",
        ]


class ProfileSerializer(serializers.ModelSerializer):
    branch_name = serializers.SerializerMethodField(read_only=True)
    profile_image = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Profile
        fields = [
            "id",
            "dob",
            "phone",
            "profile_img",
            "profile_image",
            "branch",
            "branch_name",
            "last_edited",
            "user"
        ]

        extra_kwargs = {
            "branch": {"write_only": True},
            "profile_img": {"write_only": True},
            "user": {"write_only": True},
        }

    def get_branch_name(self, obj):
        if obj.branch:
            return obj.branch.branch_name
        return None

    def get_profile_image(self, obj):
        request = self.context.get("request")
        if obj.profile_img and request:
            return request.build_absolute_uri(obj.profile_img.url)
        elif obj.profile_img:
            return obj.profile_img.url
        return None


class SmtpConfigSerializer(serializers.ModelSerializer):
    email_host_password = serializers.CharField(write_only=True)

    class Meta:
        model = SmtpConfig
        fields = [
            "id",
            "smtp_server",
            "smtp_port",
            "email_host_password",
            "use_tls",
            "use_ssl",
            "is_active",
            "created_at",
        ]


class UserListSerializer(serializers.ModelSerializer):

    name = serializers.SerializerMethodField()
    dob = serializers.SerializerMethodField()
    contact = serializers.SerializerMethodField()
    profile_img = serializers.SerializerMethodField()
    position = serializers.SerializerMethodField()
    target = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "name",
            "email",
            "role",
            "department",
            "dob",
            "contact",
            "profile_img",
            "position",
            "target",
        ]

    def get_name(self, obj):
        if obj.last_name:
            return f"{obj.first_name} {obj.last_name}"
        return obj.first_name
        
    
    def get_dob(self, obj):
        return obj.profile.dob

    def get_contact(self, obj):
        return obj.profile.phone

    def get_profile_img(self, obj):
        request = self.context.get("request")
        if obj.profile.profile_img and request:
            return request.build_absolute_uri(obj.profile.profile_img.url)
        elif obj.profile.profile_img:
            return obj.profile.profile_img.url
        return None

    def get_position(self, obj):

        position = get_current_position(obj.profile)

        return position

    def get_target(self, obj):

        target = get_current_target(obj.profile)

        return target


class UserSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "role",
            "department",
            "created_at",
            "password",
            "confirm_password",
            "profile",
        ]
        extra_kwargs = {
            "password": {"write_only": True},
            "confirm_password": {"write_only": True},
        }

    def validate(self, data):
        if data["password"] != data["confirm_password"]:
            raise serializers.ValidationError({"password": "Password does not Match."})
        return data

    def create(self, validated_data):
        validated_data.pop("confirm_password")
        password = validated_data.pop("password")

        user = User.objects.create_user(password=password, **validated_data)

        return user

        # def update(self, instance, validated_data):

        profile_data = validated_data.pop("profile", None)

        if "password" in validated_data:
            validated_data["password"] = make_password(validated_data["password"])

        instance = super().update(instance, validated_data)

        if profile_data:
            uservariable_data = profile_data.pop("uservariable", [])
            branch_data = profile_data.pop("branch", None)
            if branch_data:
                branch_name = branch_data.get("branch_name")
                if branch_name:
                    try:
                        branch = get_object_or_404(Branch, branch_name=branch_name)
                    except Branch.DoesNotExist:
                        raise serializers.ValidationError(
                            {"Branch": f"Branch - {branch_name} does not exist"}
                        )

                    profile_instance, created = Profile.objects.update_or_create(
                        user=instance, branch=branch, defaults=profile_data
                    )
            profile_instance, created = Profile.objects.update_or_create(
                user=instance, defaults=profile_data
            )

            if uservariable_data:
                for user_variable in uservariable_data:
                    variable_name = user_variable.get("variable_name")
                    variable_value = user_variable.get("variable_value")
                    from_date = user_variable.get("from_date")
                    # try:
                    #     from_date = datetime.strptime(from_date, "%Y-%m-%d").date()
                    # except ValueError:
                    #     raise serializers.ValidationError({"From Date": "Invalid date format."})
                    today = datetime.now().date()

                    filters = {
                        "from_date__lte": today,
                        "user_profile": profile_instance,
                        "variable_name": variable_name,
                    }
                    current_variable = UserVariable.objects.filter(
                        Q(to_date__gte=today) | Q(to_date__isnull=True), **filters
                    ).last()
                    if current_variable:
                        current_variable.to_date = from_date - timedelta(days=1)
                        current_variable.save()
                    UserVariable.objects.create(
                        user_profile=profile_instance,
                        variable_name=variable_name,
                        variable_value=variable_value,
                        from_date=from_date,
                    )

        return instance


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        token = self.get_token(self.user)
        profile = getattr(self.user, "profile", None)

        token["username"] = f"{self.user.first_name} {self.user.last_name}"
        token["email"] = self.user.email
        token["contact"] = profile.phone if profile else ""
        token["role"] = getattr(self.user, "role", "User") or "User"
        token["department"] = getattr(self.user, "department", "Sales") or "Sales"
        token["position"] = str(get_current_position(profile) if profile else "")
        token["target"] = str(get_current_target(profile) if profile else "")

        request = self.context.get("request")
        if profile and getattr(profile.profile_img, "url", None):
            image_url = profile.profile_img.url
            if request:
                image_url = request.build_absolute_uri(image_url)
            token["profile_image"] = image_url
        else:
            default_url = "/media/profile/user-default-96.png"
            if request:
                default_url = request.build_absolute_uri(default_url)
            token["profile_image"] = default_url

        # Prepare response
        data["access"] = str(token.access_token)
        data["refresh"] = str(token)

        # Only include valid string keys from token
        for key in token.payload:
            if isinstance(key, str):
                data[key] = token[key]

        return data

    @classmethod
    def get_token(cls, user):
        return super().get_token(user)
