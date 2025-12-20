from django.contrib import admin
from .models import *
# Register your models here.

@admin.register(proforma)
class proformaAdmin(admin.ModelAdmin):
    list_display = ['id','user_name','company_name', 'gstin', 'pi_no', 'status', 'created_at', 'edited_at']
    search_fields = ['user_name','company_name', 'gstin', 'pi_no', 'status']

@admin.register(convertedPI)
class convertedPIAdmin(admin.ModelAdmin):
    list_display = ["id",'get_user_name','get_company_name', 'get_gstin', 'get_pi_no', 'get_status', "formatted_invoice"]
    search_fields = ['pi_id__user_name','pi_id__company_name', 'pi_id__gstin', 'pi_id__pi_no', 'pi_id__status', "formatted_invoice"]

    def get_user_name(self, obj):
        return obj.pi_id.user_name
    get_user_name.short_description = "User Name"

    def get_company_name(self, obj):
        return obj.pi_id.company_name
    get_company_name.short_description = "Company"

    def get_gstin(self, obj):
        return obj.pi_id.gstin
    get_gstin.short_description = "GSTIN"

    def get_pi_no(self, obj):
        return obj.pi_id.pi_no
    get_pi_no.short_description = "PI No"

    def get_status(self, obj):
        return obj.pi_id.status
    get_status.short_description = "Status"


@admin.register(orderList)
class OrderListAdmin(admin.ModelAdmin):
    list_display = ["id",'get_company_name', 'get_pi_no','get_pi_date', 'category', 'report_type', 'product', 'from_month', 'to_month']
    search_fields = ["proforma__company_name", "proforma__pi_no", "category"]

    def get_company_name(self, obj):
        return obj.proforma.company_name
    get_company_name.short_description = "Company"

    def get_pi_no(self, obj):
        return obj.proforma.pi_no
    get_pi_no.short_description = "PI No"

    def get_pi_date(self, obj):
        return obj.proforma.pi_date
    get_pi_no.short_description = "PI Date"

@admin.register(processedOrder)
class ProcessOrderAdmin(admin.ModelAdmin):
    list_display = ["id",'get_user_name','get_company_name', 'get_gstin', 'get_pi_no', 'get_status', 'report_type', 'format', 'country' ]
    search_fields = ['pi_id__user_name','pi_id__company_name', 'pi_id__gstin', 'pi_id__pi_no', 'pi_id__status', 'report_type', 'format', 'country']

    def get_user_name(self, obj):
        return obj.pi_id.user_name
    get_user_name.short_description = "User Name"

    def get_company_name(self, obj):
        return obj.pi_id.company_name
    get_company_name.short_description = "Company"

    def get_gstin(self, obj):
        return obj.pi_id.gstin
    get_gstin.short_description = "GSTIN"

    def get_pi_no(self, obj):
        return obj.pi_id.pi_no
    get_pi_no.short_description = "PI No"

    def get_status(self, obj):
        return obj.pi_id.status
    get_status.short_description = "Status"


@admin.register(PiSummary)
class PiSummaryAdmin(admin.ModelAdmin):
    list_display = ["id",'get_company_name', 'get_pi_no','get_pi_date', 'subtotal']
    search_fields = ["proforma__company_name", "proforma__pi_no", 'subtotal']

    def get_company_name(self, obj):
        return obj.proforma.company_name
    get_company_name.short_description = "Company"

    def get_pi_no(self, obj):
        return obj.proforma.pi_no
    get_pi_no.short_description = "PI No"

    def get_pi_date(self, obj):
        return obj.proforma.pi_date
    get_pi_no.short_description = "PI Date"



# admin.site.register(proforma)
# admin.site.register(orderList)
# admin.site.register(convertedPI)
# admin.site.register(processedOrder)
# admin.site.register(PiSummary)