from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404
from lead.models import contactPerson, leads
from teams.models import Profile, User
import fiscalyear, datetime
from .utils import STATUS_CHOICES, REPORT_FORMAT, REPORT_TYPE, ORDER_STATUS, PAYMENT_STATUS, VARIABLES
from billers.models import *

# Create your models here.

class proforma(models.Model):
    
    company_ref = models.ForeignKey(leads, verbose_name=_("Company Ref"), on_delete=models.RESTRICT, blank=True, null=True, related_name="proformas")
    user_id = models.IntegerField(_("User Id"))
    user_name = models.CharField(_("Team Member"), max_length=50, null=True, blank=True)
    user_contact = models.CharField(_("User Contact"), max_length=50, null=True, blank=True)
    user_email = models.EmailField(_("User Email"), max_length=50, null=True, blank=True)
    company_name = models.CharField(_("Company Name"), max_length=150, null=False, blank=False)
    gstin = models.CharField(_("GSTIN"), max_length=50, null=True, blank=True)
    is_sez = models.BooleanField(_("Is_SEZ"), default=False)
    lut_no = models.CharField(_("LUT No"), blank=True, null=True, max_length=50)
    vendor_code = models.CharField(_("Vendor Code"), blank=True, null=True, max_length=50)
    address = models.TextField(_("Address"), max_length=1000)
    country = models.CharField(_("Country"), max_length=50)
    state = models.CharField(_("State"), max_length=50)
    requistioner = models.CharField(_("Requistioner"), max_length=50, null=False, blank=False)
    email_id = models.CharField(_("Email"), max_length=254, blank=True)
    contact = models.CharField(_("Contact No"), max_length=50, blank=True)
    pi_no = models.CharField(_("PI No"), max_length=50, unique=True)
    pi_date = models.DateField(_("PI Date"), auto_now_add=True, null=False)
    po_no = models.CharField(_("PO No"), max_length=50, blank=True, null=True)
    po_date = models.DateField(_("PO Date"), auto_now=False, blank=True, null=True)
    subscription = models.CharField(_("Subscription Mode"), max_length=50)
    payment_term = models.CharField(_("Payment Term"), max_length=50)
    bank = models.ForeignKey('billers.bankDetail', on_delete=models.RESTRICT, related_name="proformas")
    currency = models.CharField(_("Currency"), max_length=50)
    details = models.TextField(_("Details"), max_length=1000)
    is_Approved = models.BooleanField(_("Is_Approved"), default=False)
    approved_by = models.IntegerField(_("Approved By"), blank=True, null=True)
    approved_at = models.DateTimeField(_("Approved At"), auto_now=True)
    status = models.CharField(_("Status"), max_length=50, default='open', choices=STATUS_CHOICES)
    closed_at = models.DateField(_("Closing Date"), auto_now=False, auto_now_add=False, null=True, blank=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    edited_by = models.IntegerField(_("Edited By"), blank=True, null=True)
    edited_at = models.DateTimeField(_("Edited At"), auto_now=True)
    slug = models.SlugField(_("slug"), unique=True, blank=True)
    feedback = models.TextField(_("feedback"), max_length=255, blank=True, null=True)
    additional_email = models.CharField(_("Additional Emails"), max_length=254, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.pi_no)
        try:
            user = get_object_or_404(User,pk=self.user_id)
            if not self.user_name:
                self.user_name = user.full_name()
                self.user_email = user.email
                self.user_contact = user.profile.phone
        except ObjectDoesNotExist:
            pass
        super().save(*args,**kwargs)

    class Meta:
        verbose_name = _("proforma")
        verbose_name_plural = _("proformas")
        db_table = "Proforma_Invoice"
        permissions = [
            ("can_proforma_approve", "Can approve Proforma Invoice"),
        ]
        indexes = [
            models.Index(fields=["user_id"]),
            models.Index(fields=["company_name"]),
            models.Index(fields=["gstin"]),
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["closed_at"]),
            models.Index(fields=["is_Approved"]),
        ]

    def __str__(self):
        return self.company_name

class orderList(models.Model):
    
    proforma_id = models.ForeignKey(proforma, on_delete=models.RESTRICT, related_name="orderlist")
    category = models.CharField(_("Category"), max_length=50, blank=False, null=False)
    report_type = models.CharField(_("Report Type"), max_length=50)
    country = models.CharField(_("country"), max_length=255, blank=True, null=True)
    product = models.CharField(_("Product"), max_length=500)
    from_month = models.CharField(_("From Month"), max_length=50)
    to_month = models.CharField(_("To Month"), max_length=50)
    unit_price = models.CharField(_("Unit Price"), max_length=50, blank=True, null=True)
    total_price = models.IntegerField(_("Total Price"), blank=True, null=True)
    lumpsum_amt = models.IntegerField(_("Lumpsum"), blank=True, null=True)
    is_lumpsum = models.BooleanField(_("Is_Lumpsum"), default=False)
    order_status = models.CharField(_("Order Status"), max_length=50, default='pending')
    inserted_at = models.DateTimeField(_("Inserted At"), auto_now=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now_add=True)

    class Meta:
        verbose_name = _("Order")
        verbose_name_plural = _("Orders")
        db_table = "Order_List"
        indexes = [
            models.Index(fields=["category"]),
            models.Index(fields=["report_type"]),
            models.Index(fields=["is_lumpsum"]),
        ]
    
    def __str__(self):
        return f'PI No.: {self.proforma_id.pi_no} - {self.report_type}: {self.category}'
    
class PiSummary(models.Model):
    proforma = models.OneToOneField(proforma, verbose_name=_("proforma"), on_delete=models.CASCADE, related_name="summary")
    subtotal = models.DecimalField(_("subtotal"), max_digits=12, decimal_places=2)
    cgst_rate = models.DecimalField(_("cgst rate"), max_digits=4, decimal_places=2, default=0.00)
    sgst_rate = models.DecimalField(_("sgst rate"), max_digits=4, decimal_places=2, default=0.00)
    igst_rate = models.DecimalField(_("igst rate"), max_digits=4, decimal_places=2, default=0.00)
    discount = models.DecimalField(_("discount"), max_digits=4, decimal_places=2, default=0.00)
    total_value = models.DecimalField(_("total_value"), max_digits=12, decimal_places=2)
    offline_sale = models.DecimalField(_("offline sale"), max_digits=12, decimal_places=2, default=0.00)
    online_sale = models.DecimalField(_("online sale"), max_digits=12, decimal_places=2, default=0.00)
    other_sale = models.DecimalField(_("other sale"), max_digits=12, decimal_places=2, default=0.00)
    last_updated = models.DateTimeField(_("last updated"), auto_now=True)

    class Meta:
        verbose_name = _("Pi Summary")
        verbose_name_plural = _("Pi Summary")
        db_table = "PiSummary"
        indexes = [
            models.Index(fields=["last_updated"])
        ]

    def __str__(self):
        return self.proforma.pi_no
    

    
class convertedPI(models.Model):
    pi_id = models.OneToOneField(proforma, verbose_name=_("PI ID"), on_delete=models.CASCADE, related_name="convertedpi")
    is_processed = models.BooleanField(_("Is Processed"), default=False)
    is_invoiceRequire = models.BooleanField(_("Is Invoice Required"), default=False)
    is_taxInvoice = models.BooleanField(_("Is Tax Invoice"), default=False)
    is_closed = models.BooleanField(_("Is Closed"), default=False)
    is_cancel = models.BooleanField(_("Is Cancelled"), default=False)
    is_hold = models.BooleanField(_("Is Hold"), default=False)
    payment_status = models.CharField(_("Payment Status"), max_length=50, choices=PAYMENT_STATUS)
    payment1_date = models.DateField(_("Payment 1 Date"), blank=True, null=True)
    payment1_amt = models.IntegerField(_("Payment 1 Amount"), blank=True, null=True)
    payment2_date = models.DateField(_("Payment 2 Date"), blank=True, null=True)
    payment2_amt = models.IntegerField(_("Payment 2 Amount"), blank=True, null=True)
    payment3_date = models.DateField(_("Payment 3 Date"), blank=True, null=True)
    payment3_amt = models.IntegerField(_("Payment 3 Amount"), blank=True, null=True)
    formatted_invoice = models.CharField(_("formatted invoice"), max_length=50, blank=True, null=True)
    invoice_number = models.PositiveIntegerField(_("invoice number"), blank=True, null=True)
    irn = models.CharField(_("IRN"), max_length=250, blank=True, null=True)
    invoice_date = models.DateField(_("Invoice Date"), blank=True, null=True)
    requested_at = models.DateTimeField(_("Requested At"), auto_now_add=True )
    edited_at = models.DateTimeField(_("Edited At"), auto_now=True)
    generated_by = models.IntegerField(_("invoice generated by"), blank=True, null=True)
    updated_by = models.IntegerField(_("updated_by"), blank=True, null=True)

    class Meta:
        verbose_name = _("Converted PI")
        verbose_name_plural = _("Converted PIs")
        db_table = "Converted_PI"
        indexes = [
            models.Index(fields=['payment_status']),
            models.Index(fields=['formatted_invoice']),
            models.Index(fields=['invoice_number']),
            models.Index(fields=['is_processed']),
            models.Index(fields=['is_closed']),
            models.Index(fields=['invoice_date']),
        ]

    def __str__(self):
        return f'PI No.-{self.pi_id.pi_no}, Invoice No.-{self.formatted_invoice}'

class processedOrder(models.Model):
    pi_id = models.ForeignKey(proforma, verbose_name=_("PI ID"), on_delete=models.CASCADE, related_name="processedorders")
    report_type = models.CharField(_("Report Type"), max_length=150)
    format = models.CharField(_("Format"), max_length=250, choices=REPORT_FORMAT)
    country = models.CharField(_("Country"), max_length=150, blank=True, null=True)
    plan = models.CharField(_("plan"), max_length=50, blank=True, null=True)
    hsn = models.CharField(_("HSN"), max_length=150, blank=True, null=True)
    product = models.CharField(_("Product"), max_length=550, blank=True, null=True)
    iec = models.CharField(_("IEC"), max_length=150, blank=True, null=True)
    exporter = models.CharField(_("Exporter"), max_length=250, blank=True, null=True)
    importer = models.CharField(_("Importer"), max_length=250, blank=True, null=True)
    foreign_country = models.CharField(_("Foreign Country"), max_length=250, blank=True, null=True)
    port = models.CharField(_("Port"), max_length=250, blank=True, null=True)
    from_month = models.CharField(_("From Month"), max_length=50)
    to_month = models.CharField(_("To Month"), max_length=50)
    last_dispatch_month = models.CharField(_("Last Dispatch Month"), max_length=50, blank=True, null=True)
    last_dispatch_date = models.DateField(_("Last Dispatch Date"), blank=True, null=True)
    order_status = models.CharField(_("Order Status"), max_length=50, default='pending', choices=ORDER_STATUS)
    last_sent_date = models.DateField(_("last sent date"), blank=True, null=True)
    order_date = models.DateTimeField(_("order date"), auto_now_add=True)

    class Meta:
        verbose_name = _("Order Process")
        verbose_name_plural = _("Order Process")
        db_table = "Processed_Order"
        indexes = [
            models.Index(fields=["report_type"]),
            models.Index(fields=["format"]),
            models.Index(fields=["country"]),
            models.Index(fields=["order_status"]),
            models.Index(fields=["from_month", "to_month"]),
        ]

    def __str__(self):
        return f'{self.report_type} {self.format} {self.country}'