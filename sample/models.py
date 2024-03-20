from django.db import models
from django.utils.text import slugify
from teams.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
import fiscalyear, datetime
from django.utils.translation import gettext as _
# Create your models here.

def sample_no():
    fiscalyear.START_MONTH = 4
    n = sample.objects.all().order_by('id').last()
    fy = str(fiscalyear.FiscalYear.current())[-4:]

    if not n:
        n=1
        return f'BE/{fy}/Sample: {str(n).zfill(4)}'
    else:
        return f'BE/{fy}/Sample: {str(n.id+1).zfill(4)}'
    
def current_year():
    year = datetime.datetime.today().strftime('%Y')
    return int(year)

class sample(models.Model):

    FORMAT = (('monthly', 'Monthly'), ('weekly', 'Weekly'), ('sez', 'SEZ'))
    TYPE = (('export','Export'), ('import', 'Import'))
    MONTH = (
        (1,'Jan'), (2, 'Feb'), (3,'Mar'), (4, 'Apr'), (5,'May'), (6,'Jun'), (7,'Jul'), (8,'Aug'), (9, 'Sep'), (10,'Oct'), (11,'Nov'), (12,'Dec')
        )
    STATUS = (('pending', 'Pending'), ('received', 'Received'), ('reject', 'Reject'))

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
    month = models.SmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(13)], blank=True, default=1, choices=MONTH)
    year = models.SmallIntegerField(validators=[MinValueValidator(2010), MaxValueValidator(current_year)], blank=True, default=current_year)
    client_name = models.CharField(_("Client Name"), max_length=100, blank=False, null=False)
    status = models.CharField(max_length=50, blank=False, choices = STATUS, default='pending')
    requested_at = models.DateTimeField(auto_now_add=True)
    slug = models.SlugField(unique=True, blank=True)


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