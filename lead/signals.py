from django.db.models.signals import pre_save
from django.dispatch import receiver
from decimal import Decimal
from .models import *
from .utils import build_full_address


@receiver(pre_save, sender=leads)
def handle_lead_save(sender, instance, **kwargs):
    instance.full_address = build_full_address(instance)
