from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from . import views

app_name = 'invoice'
urlpatterns = [
    path('proforma/list', views.ProformaView.as_view()),
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


    # path('billers', views.biller_list, name='biller_list'),
    # path('biller/<int:biller_id>', views.biller_detail, name='biller_detail'),
    # path('set-format/<int:biller_id>', views.set_format, name='set_format'),
    # path('add-bank/<int:biler_id>', views.add_bank, name='add_bank'),
    # path('add-biller', views.add_biller, name='add_biller'),
    # path('process/<int:pi>', views.process_pi, name='process_pi'),
    # path('bulk-invoice', views.bulkInvoiceUpdate, name='bulkInvoiceUpdate'),
    # path('pdf/<int:pi_id>', views.download_pdf2, name='download_pdf'),
    # path('xls/<int:pi_id>', views.download_doc, name='download_xls'),
    # path('email/<int:pi>', views.email_form, name='email_form'),
    # path('send-test-email/<int:pi>', views.send_test_mail, name='send_test_mail'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)