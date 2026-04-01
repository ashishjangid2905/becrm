from django.contrib import admin

# Register your models here.
from .models import sample, Portmaster, CountryMaster

class Sample(admin.ModelAdmin):

    list_display = ['id','sample_id', 'user', 'country','report_format', 'report_type', 'hs_code','product', 'client_name', 'status', 'requested_at']
    list_filter = ['user', 'report_type','status']

    search_fields =('user', 'hs_code','product', 'iec', 'shipper', 'consignee', 'foreign_country','client_name')

@admin.register(Portmaster)
class PortmasterAdmin(admin.ModelAdmin):
    list_display = ['code', 'port', 'mode']
    list_filter = ['ismonthly', 'isweekly','issez']
    search_fields = ['code', 'port', 'mode']

@admin.register(CountryMaster)
class CountryMasterAdmin(admin.ModelAdmin):
    list_display = ['country_code', 'country']
    list_filter = ['is_active', 'can_process']
    search_fields = ['country_code', 'country']
    

    


admin.site.register(sample, Sample)