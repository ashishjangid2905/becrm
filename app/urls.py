from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views
from django.views.defaults import page_not_found

app_name = 'app'

urlpatterns = [
    # path('', views.home, name='home'),
    path('', views.Home.as_view()),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
