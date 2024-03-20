from django.contrib import admin

# Register your models here.
from django.contrib.auth.admin import UserAdmin
from .forms import UsersCreationForm, UsersChangeForm
from .models import User, Branch, Profile

class CustomUserAdmin(UserAdmin):
    add_form = UsersCreationForm
    form = UsersChangeForm

    model = User

    list_display = ('id', 'first_name', 'last_name', 'email', 'role', 'department', 'is_active', 'is_staff', 'is_superuser', 'last_login', 'created_at')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'role', 'department')

    fieldsets = (
        (None, {"fields": ('first_name','last_name',"email", 'role','department', "password")}),
        ("Permissions", {"fields": ("is_staff", "is_active", "groups", "user_permissions")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ('first_name','last_name',"email", 'role','department',
                "password1", "password2", "is_staff",
                "is_active", "groups", "user_permissions"
            )}
        ),
    )

    search_fields = ('email','first_name', 'last_name', 'department')
    ordering = ("id",)


class Branch_List(admin.ModelAdmin):
    list_display = ['id', 'branch_name', 'address', 'street', 'city', 'state', 'postcode', 'country', 'created_at']
    list_filter = ['city', 'state', 'country']

    search_fields = ('branch_name', 'city', 'state', 'country')

    ordering = ('-created_at',)

class User_Profile(admin.ModelAdmin):
    list_display = ['id', 'user', 'dob', 'phone', 'profile_img', 'branch', 'last_edited']
    list_filter = ['user', 'branch']

    ordering = ('id',)

admin.site.register(User, CustomUserAdmin)
admin.site.register(Branch, Branch_List)
admin.site.register(Profile, User_Profile)


