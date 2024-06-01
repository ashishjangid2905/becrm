from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from . import views

app_name = 'lead'
urlpatterns = [
    path('', views.leads_list, name='leads_list'),
    path('add', views.add_lead, name='add_lead'),
    path('edit/<int:leads_id>', views.edit_lead, name='edit_lead'),
    path('<int:leads_id>', views.lead, name='lead'),
    path('follow-up', views.follow_ups, name='follow_ups'),
    path('upload-lead', views.upload_Leads, name='upload_Leads'),
    path('download-template', views.download_template, name='download_template'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)