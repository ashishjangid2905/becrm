from django.contrib import admin
from .models import proforma, orderList, processedOrder, convertedPI, BillerVariable
# Register your models here.

admin.site.register(proforma)
admin.site.register(orderList)
admin.site.register(convertedPI)
admin.site.register(processedOrder)
admin.site.register(BillerVariable)