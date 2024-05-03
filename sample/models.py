from django.db import models
from django.utils.text import slugify
from teams.models import User, Profile
from django.core.validators import MinValueValidator, MaxValueValidator
import fiscalyear, datetime
from django.utils.translation import gettext as _
# Create your models here.


class Portmaster(models.Model):
    id = models.BigAutoField(primary_key=True)
    code = models.CharField(max_length=255, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)
    port = models.CharField(db_column='Port', max_length=255, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)  # Field name made lowercase.
    mode = models.CharField(max_length=255, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)
    ismonthly = models.BooleanField(blank=True, null=True)
    isweekly = models.BooleanField(blank=True, null=True)
    issez = models.BooleanField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'portmaster'

def sample_no(user):
    fiscalyear.START_MONTH = 4
    fy = str(fiscalyear.FiscalYear.current())[-4:]

    branch_id = Profile.objects.get(user=user).branch.id

    prefix = 'BE' if branch_id == 1 else 'CE'

    n = sample.objects.filter(sample_id__startswith=f"{prefix}/FY{fy}/Sample:").order_by('sample_id').last()


    if n:
        last_no = int(n.sample_id.split(':')[-1])
        new_no = last_no + 1
    else:
        new_no = 1

    return f"{prefix}/FY{fy}/Sample: {str(new_no).zfill(4)}"

    # if n:
    #     last_fy = n.sample_id[5:9]

    # if not n or fy != last_fy:
    #     n=1
    #     return f'BE/FY{fy}/Sample: {str(n).zfill(4)}'
    # else:
    #     return f'BE/FY{fy}/Sample: {str(n.id+1).zfill(4)}'
    
def current_year():
    year = datetime.datetime.today().strftime('%Y')
    return int(year)

class sample(models.Model):

    FORMAT = (('monthly', 'Monthly'), ('weekly', 'Weekly'), ('sez', 'SEZ'), ('incoterm', 'Incoterm'))
    TYPE = (('export','Export'), ('import', 'Import'))
    MONTH = (
        (1,'Jan'), (2, 'Feb'), (3,'Mar'), (4, 'Apr'), (5,'May'), (6,'Jun'), (7,'Jul'), (8,'Aug'), (9, 'Sep'), (10,'Oct'), (11,'Nov'), (12,'Dec')
        )
    STATUS = (('pending', 'Pending'), ('received', 'Received'), ('rejected', 'Rejected'))

    sample_id = models.CharField(max_length=50, default=sample_no, unique=True)
    user = models.ForeignKey(User, verbose_name='User', on_delete=models.CASCADE)
    country = models.CharField(max_length=100, blank=False, default='India')
    report_format = models.CharField(_("Format"), max_length=100, blank=False, choices=FORMAT, default='monthly')
    report_type = models.CharField(_("Type"), max_length=100, blank=False, choices=TYPE, default='export')
    hs_code = models.CharField(max_length=100, blank=True, default='%')
    product = models.CharField(max_length=100, blank=True, default='%')
    iec = models.CharField(_("IEC"), max_length=100, blank=True, default='%')
    shipper = models.CharField(max_length=255, blank=True, default='%')
    consignee = models.CharField(max_length=255, blank=True, default='%')
    foreign_country = models.CharField(max_length=255, blank=True, default='%')
    port = models.CharField(max_length=255, blank=True, default='%')
    month = models.SmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(13)], blank=True, null=True, default=None, choices=MONTH)
    year = models.SmallIntegerField(validators=[MinValueValidator(2010), MaxValueValidator(current_year)], blank=True, default=current_year)
    client_name = models.CharField(_("Client Name"), max_length=100, blank=False, null=False)
    status = models.CharField(max_length=50, blank=False, choices = STATUS, default='pending')
    requested_at = models.DateTimeField(auto_now_add=True)
    slug = models.SlugField(unique=True, blank=True)
    last_edited = models.DateTimeField(auto_now=True, blank = True)


    def save(self, *args, **kwargs):
        if not self.slug:
            # Generate slug based on sample_id or any other field
            self.slug = slugify(self.sample_id)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Sample'
        verbose_name_plural = 'Samples'
        ordering = ['sample_id']

    def __str__(self):
        return self.sample_id