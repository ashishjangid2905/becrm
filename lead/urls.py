from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from . import views

app_name = 'lead'
urlpatterns = [
    path('', views.leads_list, name='leads_list'),
    path('list', views.lead_list.as_view()),
    path('add-lead', views.lead_list.as_view()),
    path('<int:id>', views.LeadView.as_view()),
    path('<int:id>/add-contact', views.ContactView.as_view()),
    path('<int:id>/deals', views.ConversationView.as_view()),
    path('<int:id>/create/deal', views.ConversationView.as_view()),
    path('deal/activity/<int:id>', views.dealActivityView.as_view()),
    path('deal/insert/note/<int:id>', views.dealActivityView.as_view()),


    path('add', views.add_lead, name='add_lead'),
    path('edit/<int:leads_id>', views.edit_lead, name='edit_lead'),
    path('<int:leads_id>', views.lead, name='lead'),
    path('<int:leads_id>/pi_list', views.lead, name='leads_pi'),
    path('<int:leads_id>/add_contact', views.add_contact, name='add_contact'),
    path('<int:contact_id>/edit_contact', views.edit_contact, name='edit_contact'),
    path('<int:leads_id>/chat', views.lead_chat, name='leads_chat'),
    path('<int:leads_id>/new_chat', views.new_chat, name='new_chat'),
    path('chat/<int:chat_id>', views.chat_insert, name='chat_insert'),
    path('follow-up', views.follow_ups, name='follow_ups'),
    path('upload-lead', views.upload_Leads, name='upload_Leads'),
    path('download-template', views.download_template, name='download_template'),
    # path('export', views.exportlead, name='export_lead'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)