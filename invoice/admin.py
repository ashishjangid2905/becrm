from django.contrib import admin
from .models import biller, bankDetail, proforma, orderList
# Register your models here.

admin.site.register(biller)
admin.site.register(bankDetail)
admin.site.register(proforma)
admin.site.register(orderList)