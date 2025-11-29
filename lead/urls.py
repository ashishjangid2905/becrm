from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from . import views

app_name = 'lead'
urlpatterns = [

    path('list', views.lead_list.as_view()),
    path('add-lead', views.lead_list.as_view()),
    path('get-list', views.LeadListView.as_view()),
    path('<int:id>', views.LeadView.as_view()),
    path('<int:id>/update', views.LeadView.as_view()),
    path('<int:id>/add-contact', views.ContactView.as_view()),
    path('<int:lead_id>/update-contact/<int:id>', views.ContactView.as_view()),
    path('<int:id>/deals', views.ConversationView.as_view()),
    path('<int:id>/create/deal', views.ConversationView.as_view()),
    path('deal/activity/<int:id>', views.dealActivityView.as_view()),
    path('deal/insert/note/<int:id>', views.dealActivityView.as_view()),

    path('follow-up', views.DealFollowUpViews.as_view({'get':'list'})),
    path('subscribe/website', views.InboundLeadGetView.as_view()),

    path('upload-lead', views.upload_Leads, name='upload_Leads'),
    path('download-template', views.download_template, name='download_template'),
    # path('export', views.exportlead, name='export_lead'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)