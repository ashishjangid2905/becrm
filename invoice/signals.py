from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from decimal import Decimal
from .models import *
from .custom_utils import total_order_value, total_pi_value_inc_tax, sale_category


def calculate_summery(pi):
    
    subtotal = total_order_value(pi.id)
    total_value = total_pi_value_inc_tax(pi.id)
    category_sales = sale_category(pi.id)

    if not pi.bank.biller_id.biller_gstin or pi.is_sez:
        cgst_rate = sgst_rate = igst_rate = 0
    else:
        state_code = str(pi.state)
        biller_state_code = pi.bank.biller_id.biller_gstin[0:2]
        if state_code == biller_state_code:
            cgst_rate, sgst_rate, igst_rate = 9, 9, 0
        elif state_code == "500":
            cgst_rate = sgst_rate = igst_rate = 0
        else:
            cgst_rate = sgst_rate = 0
            igst_rate = 18
    
    return {
        "subtotal": Decimal(subtotal),
        "total_value": Decimal(total_value),
        "cgst_rate": Decimal(cgst_rate),
        "sgst_rate": Decimal(sgst_rate),
        "igst_rate": Decimal(igst_rate),
        "offline_sale": Decimal(category_sales["offline_sale"]),
        "online_sale": Decimal(category_sales["online_sale"]),
        "other_sale": Decimal(category_sales["domestic_sale"])
    }

def update_or_create_summery(pi):
    summery_data = calculate_summery(pi)
    PiSummary.objects.update_or_create(
        proforma = pi,
        defaults=summery_data
    )

@receiver(post_save, sender=orderList)
def handle_orderlist_save(sender, instance, created, **kwargs):
    print(f"[Signal Triggered] Updating summary for PI {instance.proforma_id}")
    update_or_create_summery(instance.proforma_id)


@receiver(post_delete, sender=orderList)
def handle_orderlist_delete(sender, instance, **kwargs):
    update_or_create_summery(instance.proforma_id)

@receiver(post_save, sender=proforma)
def handle_proforma_save(sender, instance, created, **kwargs):
    update_or_create_summery(instance)
    # try:
    #     old_instance = proforma.objects.get(pk=instance.id)
    # except proforma.DoesNotExist:
    #     old_instance = None
    
    # if not old_instance:
        # update_or_create_summery(instance)
        # return
    
    # has_important_changes = (
    #     old_instance.bank_id != instance.bank_id or
    #     old_instance.state != instance.state or
    #     old_instance.is_sez != instance.is_sez
    # )

    # if has_important_changes:
    #     update_or_create_summery(instance)


@receiver(post_delete, sender=proforma)
def handle_proforma_delete(sender, instance, **kwargs):
    PiSummary.objects.filter(proforma=instance).delete()