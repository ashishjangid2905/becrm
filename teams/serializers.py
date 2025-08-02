from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User, Profile, Branch, UserVariable, SmtpConfig
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
        fields = '__all__'

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
    phone = serializers.SerializerMethodField()
    gender = serializers.SerializerMethodField()
    employee_code = serializers.SerializerMethodField()
    profile_img = serializers.SerializerMethodField()
    position = serializers.SerializerMethodField()
    target = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "name",
            "first_name",
            "last_name",
            "email",
            "is_active",
            "gender",
            "employee_code",
            "role",
            "department",
            "dob",
            "phone",
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

    def get_phone(self, obj):
        return obj.profile.phone
    
    def get_gender(self, obj):
        return obj.profile.gender
    
    def get_employee_code(self, obj):
        return obj.profile.employee_code

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
            "is_active",
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
        password = data.get("password")
        confirm_password = data.get("confirm_password")

        if password or confirm_password:
            if password != confirm_password:
                raise serializers.ValidationError({"password": "Password does not Match."})
        return data

    def create(self, validated_data):
        validated_data.pop("confirm_password")
        password = validated_data.pop("password")

        user = User.objects.create_user(password=password, **validated_data)

        return user


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        token = self.get_token(self.user)
        profile = getattr(self.user, "profile", None)

        token["first_name"] = self.user.first_name
        token["last_name"] = self.user.last_name
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
