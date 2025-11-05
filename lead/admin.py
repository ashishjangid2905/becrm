from django.contrib import admin

# Register your models here.
from .models import *

class Leads(admin.ModelAdmin):
    list_display = ['id','company_name', 'city', 'state', 'country', 'created_at', 'edited_at']


class ContactPerson(admin.ModelAdmin):
    list_display = ['id', 'person_name', 'email_id', 'contact_no', 'company', 'is_active','created_at']

class conversation(admin.ModelAdmin):
    list_display = ['id','title', 'start_at']

class ConversationDetails(admin.ModelAdmin):
    list_display = ['id', 'details','status', 'follow_up', 'chat_no', 'inserted_at']

class Inboundleads(admin.ModelAdmin):
    list_display = ['id', 'name', 'company_name', 'location', 'email', 'contact_no', 'message', 'source']

admin.site.register(leads, Leads)
admin.site.register(contactPerson, ContactPerson)
admin.site.register(Conversation, conversation)
admin.site.register(conversationDetails, ConversationDetails)
admin.site.register(InboundLeads, Inboundleads)