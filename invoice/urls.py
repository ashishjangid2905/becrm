from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from . import views

app_name = 'invoice'
urlpatterns = [
    path('proforma/list', views.ProformaView.as_view()),
    path('proforma/renewals', views.RenewalPIView.as_view()),
    path('proforma/create', views.ProformaCreateUpdateView.as_view()),
    path('proforma/<slug:slug>', views.ProformaCreateUpdateView.as_view()),
    path('proforma/update/<slug:slug>', views.ProformaCreateUpdateView.as_view()),
    path('proforma/approval/request-list', views.ApproveRequestPIView.as_view()),
    path('proforma/process/<slug:slug>', views.ProcessedPIUpdateListView.as_view()),
    path('list', views.InvoiceListView.as_view()),
    path('request-list', views.InvoiceUpdateListView.as_view()),
    path('create/<int:id>', views.InvoiceUpdateListView.as_view()),
    path('process-list', views.ProcessedPIUpdateListView.as_view()),
    path('update-order/<int:id>', views.ProcessedPIUpdateListView.as_view()),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)