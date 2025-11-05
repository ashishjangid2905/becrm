from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User

class UsersCreationForm(UserCreationForm):

    class Meta:
        model = User
        fields = ('first_name', 'last_name','email','role', 'department')

class UsersChangeForm(UserChangeForm):

    class Meta:
        model = User
        fields = ('first_name', 'last_name','email','role', 'department', 'password')