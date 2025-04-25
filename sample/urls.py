from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views

app_name = 'sample'
urlpatterns = [
    path('', views.SampleViews.as_view()),
    path('list', views.SampleViews.as_view()),
    path('edit/<slug:slug>', views.SampleViews.as_view()),
    path('options/', views.CountryAndPortOption.as_view()),
    path('request', views.sample_request, name='sample_request'),
    path('edit/<slug:sample_slug>', views.edit_sample, name = 'edit_sample'),
    path('list', views.sample_list, name='samples'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)