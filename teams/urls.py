from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .views import *

app_name = 'teams'
urlpatterns = [
    path('user', UserDetailView.as_view()),
    path('user-list', UserListView.as_view()),
    path('update/<int:pk>', UserListView.as_view()),
    path('register', UserListView.as_view(), name='add_user'),
    # path('user', views.user_list, name='users'),
    path('set-target/<int:id>', CreateUpdateUserVariableView.as_view()),
    # path('add', views.add_user, name='add_user'),
    # path('set-target/<int:user_id>', views.set_target, name='set_target'),
    path('edit/<int:user_id>', edit_user, name='edit_user'),
    path('change-password/<int:user_id>', change_password, name='change_password'),
    path('change-password-user/', user_password, name='user_password'),
    path('branches/', branch_list, name='branch_list'),
    path('add-branch/', add_branch, name='add_branch'),
    path('edit-branch/<int:branch_id>', edit_branch, name='edit_branch'),
    path('profile/', profile, name='profile'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)