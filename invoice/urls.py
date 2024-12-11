from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from . import views

app_name = 'invoice'
urlpatterns = [
    path('billers', views.biller_list, name='biller_list'),
    path('biller/<int:biller_id>', views.biller_detail, name='biller_detail'),
    path('set-format/<int:biller_id>', views.set_format, name='set_format'),
    path('add-bank/<int:biler_id>', views.add_bank, name='add_bank'),
    path('add-biller', views.add_biller, name='add_biller'),
    path('proforma-invoice', views.pi_list, name='pi_list'),
    path('create-pi', views.create_pi, name='create_pi'),
    path('create-pi/<int:lead_id>', views.create_pi, name='create_pi_lead_id'),
    path('approve-pi/<int:pi_id>', views.approve_pi, name='approve_pi'),
    path('update-status/<int:pi>', views.update_pi_status, name='update_pi_status'),
    path('process/<int:pi>', views.process_pi, name='process_pi'),
    path('edit-pi/<slug:pi>', views.edit_pi, name='edit_pi'),
    path('processed', views.processed_list, name='processed_list'),
    path('processed/pi-<int:pi_id>', views.processed_pi_order, name='processed_pi_order'),
    path('create-invoice/<int:pi>', views.generate_invoice, name='generate_invoice'),
    path('bulk-invoice', views.bulkInvoiceUpdate, name='bulkInvoiceUpdate'),
    path('list', views.invoice_list, name='invoice_list'),
    path('pdf/<int:pi_id>', views.download_pdf2, name='download_pdf'),
    # path('xls/<int:pi_id>', views.download_doc, name='download_xls'),
    path('email/<int:pi>', views.email_form, name='email_form'),
    path('send-test-email/<int:pi>', views.send_test_mail, name='send_test_mail'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)