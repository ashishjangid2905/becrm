from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from .views import *

app_name = 'billers'

urlpatterns = [
    path('bank-list', BankListView.as_view()),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# custom handlers

handler404 = 'app.views.custom_page_not_found'