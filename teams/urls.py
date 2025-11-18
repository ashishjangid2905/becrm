from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .views import *

app_name = 'teams'
urlpatterns = [
    path('register', UserListView.as_view(), name='add_user'),
    path('user', UserDetailView.as_view()),
    path('users/dashboard', UserListDashboardView.as_view()),
    path('user-list', UserListView.as_view()),
    path('update/<int:pk>', UserListView.as_view()),
    path('set-target/<int:id>', CreateUpdateUserVariableView.as_view()),
    path("profile/update/<int:id>", UserProfileUpdateView.as_view()),
    path('change-password/<pk>', UserUpdateView.as_view(), name='change_password'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)