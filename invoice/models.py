from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from lead.models import contactPerson, leads
from teams.models import Profile
import fiscalyear, datetime
from .utils import STATUS_CHOICES, REPORT_FORMAT, REPORT_TYPE, ORDER_STATUS, PAYMENT_STATUS, VARIABLES

# Create your models here.

class biller(models.Model):
    biller_name = models.CharField(_("Biller Name"), max_length=150)
    brand_name = models.CharField(_("Brand Name"), max_length=150, null=True, blank=True)
    biller_gstin = models.CharField(_("Biller Gstin"), max_length=20, blank=True, null=True)
    biller_pan = models.CharField(_("Biller Pan"), max_length=15, blank=True, null=True)
    biller_msme = models.CharField(_("Biller MSME"), max_length=150, blank=True, null=True)
    reg_address1 = models.CharField(_("Reg. Address Line1"), max_length=254)
    reg_address2 = models.CharField(_("Reg. Address Line2"), max_length=254)
    reg_city = models.CharField(_("Reg. City"), max_length=254)
    reg_state = models.CharField(_("Reg. State"), max_length=254)
    reg_pincode = models.CharField(_("Reg. Pincode"), max_length=254)
    reg_country = models.CharField(_("Reg. Country"), max_length=254)
    corp_address1 = models.CharField(_("Corp. Address Line1"), max_length=254, blank=True, null=True)
    corp_address2 = models.CharField(_("Corp. Address Line2"), max_length=254, blank=True, null=True)
    corp_city = models.CharField(_("Corp. City"), max_length=254, blank=True, null=True)
    corp_state = models.CharField(_("Corp. State"), max_length=254, blank=True, null=True)
    corp_pincode = models.CharField(_("Corp. Pincode"), max_length=254, blank=True, null=True)
    corp_country = models.CharField(_("Corp. Country"), max_length=254, blank=True, null=True)
    inserted_at = models.DateTimeField(_("Inserted"), auto_now=True)
    edited_at = models.DateTimeField(_("Edited"), auto_now_add=True)
    inserted_by = models.IntegerField(_("Inserted By"))

    class Meta:
        verbose_name = _("Biller")
        verbose_name_plural = _("Billers")
        db_table = "Biller"
        unique_together = ('biller_name', 'biller_gstin')

    def get_reg_full_address(self):
        address_parts = [
            self.reg_address1,
            self.reg_address2,
            self.reg_city,
            self.reg_pincode,
            self.reg_state,
            self.reg_country
        ]
        return ', '.join(filter(None, address_parts))
    
    def get_corp_full_address(self):
        address_parts = [
            self.corp_address1,
            self.corp_address2,
            self.corp_city,
            self.corp_pincode,
            self.corp_state,
            self.corp_country
        ]
        return ', '.join(filter(None, address_parts))
    
    def __str__(self):
        return f'{self.biller_name} - {self.reg_state}'
    
    

class BillerVariable(models.Model):
    biller_id = models.ForeignKey(biller, verbose_name=_("Biller Id"), on_delete=models.CASCADE, related_name="variables")
    variable_name = models.CharField(_("Variable Name"), max_length=50, choices=VARIABLES)
    variable_value = models.CharField(_("Variable Value"), max_length=150)
    from_date = models.DateField(_("From Date"), null=False, blank=False)
    to_date = models.DateField(_("To Date"), null=True, blank=True)
    inserted_by = models.IntegerField(_("Inserted By"))
    Inserted_at = models.DateTimeField(_("Inserted At"), auto_now_add=True)

    class Meta:
        verbose_name = _("Biller Variable")
        verbose_name_plural = _("Biller Variables")
        db_table = "Biller_Variable"

    def __str__(self):
        return f'{self.id} - {self.biller_id.biller_name} - {self.variable_name}: {self.variable_value}'
    


class bankDetail(models.Model):

    biller_id = models.ForeignKey(biller, on_delete=models.SET_NULL, null=True)
    is_active = models.BooleanField(_("Is Active"), default=True)
    is_upi = models.BooleanField(_("Is UPI"), default=False)
    upi_id = models.CharField(_("UPI ID"), max_length=50, blank=True, null=True)
    upi_no = models.CharField(_("UPI No"), max_length=50, blank=True, null=True)
    bnf_name = models.CharField(_("Beneficiary Name"), max_length=150, blank=False, null=False)
    bank_name = models.CharField(_("Bank Name"), max_length=150, blank=False, null=False)
    branch_address = models.CharField(_("Branch Address"), max_length=254, blank=True, null=True)
    ac_no = models.CharField(_("A/c No"), max_length=150, blank=False, null=False)
    ifsc = models.CharField(_("IFSC"), max_length=50, blank=False, null=False)
    swift_code = models.CharField(_("Swift Code"), max_length=50, blank=True, null=True)
    inserted_at = models.DateTimeField(_("Inserted at"), auto_now_add=True)
    edited_at = models.DateTimeField(_("Edited at"), auto_now=True)
    inserted_by = models.IntegerField(_("Inserted By"))

    class Meta:
        verbose_name = _("Bank")
        verbose_name_plural = _("Banks")
        db_table = "Bank_List"
        unique_together = ('bnf_name', 'bank_name', 'ac_no', 'upi_id', 'upi_no')

    def __str__(self):
        return f'{self.bank_name} - {self.bnf_name}'
    
def get_biller_variable(biller_dtl,variable_name):
    today = timezone.now().date()

    filters = {'from_date__lte': today, 'biller_id': biller_dtl, 'variable_name': variable_name }

    variable = BillerVariable.objects.filter(
        Q(to_date__gte=today) | Q(to_date__isnull = True),
        **filters).last()

    return variable.variable_value if variable else None

def pi_number(user, pi_tag = None, pi_format=None):
    fiscalyear.START_MONTH = 4
    fy = str(fiscalyear.FiscalYear.current())[-2:]
    py = str(int(fy) - 1)

    branch_id = Profile.objects.get(user=user).branch.id
    
    if not pi_tag:
        pi_tag = 'BE' if branch_id == 1 else 'CE'
    if not pi_format:
        pi_format = '{py}-{fy}/{tag}-{num:04d}'

    if not isinstance(pi_format, str):
        raise ValueError(f"Expected pi_format to be a string, got {type(pi_format)}")

    search_prefix = pi_format.format(py=py, fy=fy, tag=pi_tag, num=0).rstrip("0")

    last_pi = proforma.objects.filter(pi_no__startswith=search_prefix).order_by('pi_no').last()

    if last_pi:
        try:
            last_no = int(last_pi.pi_no.split(search_prefix)[-1])
        except:
            last_no = 0
        new_no = last_no + 1
    else:
        new_no = 1

    pi_no = pi_format.format(py=py, fy=fy, tag=pi_tag, num=new_no)

    return pi_no


class proforma(models.Model):
    
    company_ref = models.ForeignKey(leads, verbose_name=_("Company Ref"), on_delete=models.RESTRICT, blank=True, null=True)
    user_id = models.IntegerField(_("User Id"))
    user_name = models.CharField(_("Team Member"), max_length=50, null=True, blank=True, default="ABC")
    user_contact = models.CharField(_("User Contact"), max_length=50, null=True, blank=True, default="9899999")
    user_email = models.EmailField(_("User Email"), max_length=50, null=True, blank=True, default="email@email.com")
    company_name = models.CharField(_("Company Name"), max_length=150, null=False, blank=False)
    gstin = models.CharField(_("GSTIN"), max_length=50, null=True, blank=True)
    is_sez = models.BooleanField(_("Is_SEZ"), default=False)
    lut_no = models.CharField(_("LUT No"), blank=True, null=True, max_length=50)
    vendor_code = models.CharField(_("Vendor Code"), blank=True, null=True, max_length=50)
    address = models.TextField(_("Address"), max_length=1000)
    country = models.CharField(_("Country"), max_length=50)
    state = models.CharField(_("State"), max_length=50)
    requistioner = models.CharField(_("Requistioner"), max_length=50, null=False, blank=False)
    email_id = models.EmailField(_("Email"), max_length=254)
    contact = models.CharField(_("Contact No"), max_length=50)
    pi_no = models.CharField(_("PI No"), max_length=50, default=pi_number, null=False, blank=False, unique=True)
    pi_date = models.DateField(_("PI Date"), auto_now_add=True, null=False)
    po_no = models.CharField(_("PO No"), max_length=50, blank=True, null=True)
    po_date = models.DateField(_("PO Date"), auto_now=False, blank=True, null=True)
    subscription = models.CharField(_("Subscription Mode"), max_length=50)
    payment_term = models.CharField(_("Payment Term"), max_length=50)
    bank = models.ForeignKey(bankDetail, on_delete=models.RESTRICT)
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
    additional_email = models.EmailField(_("Additional Emails"), max_length=254, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.pi_no)
        super().save(*args,**kwargs)

    class Meta:
        verbose_name = _("proforma")
        verbose_name_plural = _("proformas")
        db_table = "Proforma_Invoice"
        permissions = [
            ("can_proforma_approve", "Can approve Proforma Invoice"),
        ]

    def __str__(self):
        return self.company_name

class orderList(models.Model):
    
    proforma_id = models.ForeignKey(proforma, on_delete=models.RESTRICT, related_name="orderlist")
    category = models.CharField(_("Category"), max_length=50, blank=False, null=False)
    report_type = models.CharField(_("Report Type"), max_length=50)
    product = models.CharField(_("Product"), max_length=500)
    from_month = models.CharField(_("From Month"), max_length=50)
    to_month = models.CharField(_("To Month"), max_length=50)
    unit_price = models.IntegerField(_("Unit Price"), blank=True, null=True)
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
    
    def __str__(self):
        return f'PI No.: {self.proforma_id.pi_no} - {self.report_type}: {self.category}'
    
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
    invoice_no = models.CharField(_("Invoice No"), max_length=50, blank=True, null=True)
    irn = models.CharField(_("IRN"), max_length=250, blank=True, null=True)
    invoice_date = models.DateField(_("Invoice Date"), blank=True, null=True)
    requested_at = models.DateTimeField(_("Requested At"), auto_now_add=True )
    edited_at = models.DateTimeField(_("Edited At"), auto_now=True)

    class Meta:
        verbose_name = _("Converted PI")
        verbose_name_plural = _("Converted PIs")
        db_table = "Converted_PI"

    def __str__(self):
        return f'PI No.-{self.pi_id.pi_no}, Invoice No.-{self.invoice_no}'

class processedOrder(models.Model):
    pi_id = models.ForeignKey(proforma, verbose_name=_("PI ID"), on_delete=models.CASCADE, related_name="processedorders")
    report_type = models.CharField(_("Report Type"), max_length=150, choices=REPORT_TYPE)
    format = models.CharField(_("Format"), max_length=250, choices=REPORT_FORMAT)
    country = models.CharField(_("Country"), max_length=150, blank=True, null=True)
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
    last_sent_date = models.DateField(_("last_sent_date"), blank=True, null=True)
    order_date = models.DateTimeField(_("last_sent_date"), auto_now_add=True)

    class Meta:
        verbose_name = _("Order Process")
        verbose_name_plural = _("Order Process")
        db_table = "Processed_Order"

    def __str__(self):
        return f'{self.report_type} {self.format} {self.country}'