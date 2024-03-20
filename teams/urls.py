from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views

app_name = 'teams'
urlpatterns = [
    path('user', views.user_list, name='users'),
    path('add', views.add_user, name='add_user'),
    path('edit/<int:user_id>', views.edit_user, name='edit_user'),
    path('change-password/<int:user_id>', views.change_password, name='change_password'),
    path('change-password-user/', views.user_password, name='user_password'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)