from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views
from django.views.defaults import page_not_found

app_name = 'app'

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user , name="logout"),
    path('sample-chart/', views.sample_chart, name='sample_chart'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# custom handlers

handler404 = 'app.views.custom_page_not_found'