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
        fields = '__all__'

class UserVariableSerializer(serializers.ModelSerializer):
    from_date = serializers.DateField(required=True, allow_null=False)
    to_date = serializers.DateField(required=False, allow_null=True)
    class Meta:
        model = UserVariable
        fields = ['id', 'variable_name', 'variable_value', 'from_date', 'to_date', 'created_at']

class ProfileSerializer(serializers.ModelSerializer):
    branch = BranchSerializer()
    uservariable = UserVariableSerializer(many=True)
    class Meta:
        model = Profile
        fields = ['id', 'dob', 'phone', 'profile_img', 'branch', 'last_edited', 'uservariable']


class SmtpConfigSerializer(serializers.ModelSerializer):
    email_host_password = serializers.CharField(write_only=True)
    class Meta:
        model = SmtpConfig
        fields = ['id', 'smtp_server', 'smtp_port', 'email_host_password', 'use_tls', 'use_ssl', 'is_active', 'created_at']



class UserSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)
    profile = ProfileSerializer()
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email', 'role', 'department', 'created_at', 'password', 'confirm_password', 'profile']
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({"password": "Password does not Match."})
        return data
    
    def create(self, validated_data):
        profile_data = validated_data.pop('profile', None)
        validated_data.pop('confirm_password')
        validated_data['password'] = make_password(validated_data['password'])

        user = super().create(validated_data)

        if profile_data:
            uservariable_data = profile_data.pop('uservariable', [])
            branch_data = profile_data.pop('branch', None)
            branch_name = branch_data.get('branch_name')

            try:
                branch = Branch.objects.filter(branch_name=branch_name).first()
            except Branch.DoesNotExist:
                user.delete()
                raise serializers.ValidationError({"branch": f"branch does not exist: {branch_name}"})
            
            try:
                profile = Profile.objects.create(user=user, branch=branch, **profile_data)
                for uservariable in uservariable_data:
                    UserVariable.objects.create(user_profile = profile, **uservariable)
            except Exception as e:
                user.delete()
                raise serializers.ValidationError({"profile": "Profile creation failed. User has been deleted.", "error": f"{e}"})
            
        return user
    
    def update(self, instance, validated_data):

        profile_data = validated_data.pop('profile',None)

        if 'password' in validated_data:
            validated_data['password'] = make_password(validated_data['password'])
        
        instance = super().update(instance, validated_data)

        if profile_data:
            uservariable_data = profile_data.pop('uservariable', [])
            branch_data = profile_data.pop('branch', None)
            if branch_data:
                branch_name = branch_data.get('branch_name')
                if branch_name:
                    try:
                        branch = get_object_or_404(Branch, branch_name=branch_name)
                    except Branch.DoesNotExist:
                        raise serializers.ValidationError({"Branch": f"Branch - {branch_name} does not exist"})

                    profile_instance, created = Profile.objects.update_or_create(user=instance, branch=branch, defaults=profile_data)
            profile_instance, created = Profile.objects.update_or_create(user=instance, defaults=profile_data)
        
            if uservariable_data:
                for user_variable in uservariable_data:
                    variable_name = user_variable.get('variable_name')
                    variable_value = user_variable.get('variable_value')
                    from_date = user_variable.get('from_date')
                    # try:
                    #     from_date = datetime.strptime(from_date, "%Y-%m-%d").date()
                    # except ValueError:
                    #     raise serializers.ValidationError({"From Date": "Invalid date format."})
                    today = datetime.now().date()

                    filters = {'from_date__lte': today, 'user_profile': profile_instance, 'variable_name': variable_name }
                    current_variable = UserVariable.objects.filter(Q(to_date__gte=today) | Q(to_date__isnull = True),
                        **filters).last()
                    if current_variable:
                        current_variable.to_date = from_date - timedelta(days=1)
                        current_variable.save()
                    UserVariable.objects.create(
                        user_profile=profile_instance,
                        variable_name=variable_name,
                        variable_value=variable_value,
                        from_date=from_date
                    )
        
        return instance


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = f'{user.first_name} {user.last_name}'
        token['email'] = user.email
        token['contact'] = user.profile.phone
        token['role'] = user.role if getattr(user, 'role') else "User"
        token['department'] = user.department if getattr(user, 'department') else "Sales"
        token['position'] = get_current_position(user.profile)
        token['target'] = get_current_target(user.profile)

        return token



