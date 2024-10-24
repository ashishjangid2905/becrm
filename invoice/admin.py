from django.contrib import admin
from .models import biller, bankDetail, proforma, orderList, processedOrder, convertedPI
# Register your models here.

admin.site.register(biller)
admin.site.register(bankDetail)
admin.site.register(proforma)
admin.site.register(orderList)
admin.site.register(convertedPI)
admin.site.register(processedOrder)