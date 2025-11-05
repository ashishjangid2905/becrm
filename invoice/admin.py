from django.contrib import admin
from .models import *
# Register your models here.

admin.site.register(proforma)
admin.site.register(orderList)
admin.site.register(convertedPI)
admin.site.register(processedOrder)
admin.site.register(PiSummary)