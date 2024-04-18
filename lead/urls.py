from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views

app_name = 'lead'
urlpatterns = [
    path('', views.leads_list, name='leads_list'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)