from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views

app_name = 'teams'
urlpatterns = [
    path('user-list', views.UserListView.as_view()),
    path('update/<int:pk>', views.UserListView.as_view()),
    path('register', views.UserListView.as_view(), name='add_user'),
    path('user', views.user_list, name='users'),
    path('set-target/<int:id>', views.CreateUpdateUserVariableView.as_view()),
    # path('add', views.add_user, name='add_user'),
    # path('set-target/<int:user_id>', views.set_target, name='set_target'),
    path('edit/<int:user_id>', views.edit_user, name='edit_user'),
    path('change-password/<int:user_id>', views.change_password, name='change_password'),
    path('change-password-user/', views.user_password, name='user_password'),
    path('branches/', views.branch_list, name='branch_list'),
    path('add-branch/', views.add_branch, name='add_branch'),
    path('edit-branch/<int:branch_id>', views.edit_branch, name='edit_branch'),
    path('profile/', views.profile, name='profile'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)