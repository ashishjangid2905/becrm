from django.contrib import admin

# Register your models here.
from .models import leads

class Leads(admin.ModelAdmin):
    list_display = ['id','company_name', 'city', 'state', 'country', 'created_at', 'edited_at']

admin.site.register(leads, Leads)