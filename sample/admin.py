from django.contrib import admin

# Register your models here.
from .models import sample

class Sample(admin.ModelAdmin):

    list_display = ['id','sample_id', 'user', 'country','report_format', 'report_type', 'hs_code','product', 'client_name', 'status', 'requested_at']
    list_filter = ['user', 'report_type','status']

    search_fields =('user', 'hs_code','product', 'iec', 'shipper', 'consignee', 'foreign_country','client_name')


admin.site.register(sample, Sample)