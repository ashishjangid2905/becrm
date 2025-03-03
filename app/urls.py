from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views
from invoice.views import biller_list
from django.views.defaults import page_not_found

app_name = 'app'

urlpatterns = [
    path('', views.home, name='home'),
    path('', views.Home.as_view()),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user , name="logout"),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/status/<str:task_id>/', views.check_dashboard_status, name='check_dashboard_status'),
    path('activity-logs/', views.logs, name='logs'),
    path('settings', views.settings, name='settings'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# custom handlers

handler404 = 'app.views.custom_page_not_found'