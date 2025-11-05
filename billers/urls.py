from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from .views import *

app_name = 'billers'

urlpatterns = [
    path('', BillerListCreateView.as_view()),
    path('<int:pk>', BillerListCreateView.as_view()),
    path('bank', BankListCreateUpdateView.as_view()),
    path('<int:biller_id>/bank', BankListCreateUpdateView.as_view()),
    path('<int:biller_id>/bank/<int:pk>', BankListCreateUpdateView.as_view()),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# custom handlers

handler404 = 'app.views.custom_page_not_found'