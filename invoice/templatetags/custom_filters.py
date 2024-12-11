from django import template
from datetime import datetime

register = template.Library()


@register.filter
def format_month(value):
    try:
        if value == None or value == '':
            return ''
        else:
            return datetime.strptime(value, '%Y-%m').strftime("%b'%y")
    except ValueError:
        return value
    
@register.filter
def total_month(from_month, to_month):
    try:
        from_m = datetime.strptime(from_month, '%Y-%m')
        to_m = datetime.strptime(to_month, '%Y-%m')
        return (to_m.year - from_m.year) * 12 + to_m.month - from_m.month + 1
    except (ValueError, TypeError):
        return 0

@register.filter
def multiply(value, arg):
    try:
        return value*arg
    except (ValueError, TypeError):
        return 0
    
@register.filter
def sale_category(proforma):
    online_sale = 0
    offline_sale = 0
    domestic_sale = 0
    unique_lumpsum_amt_online = set()  # To track unique lumpsum amounts
    unique_lumpsum_amt_offline = set()  # To track unique lumpsum amounts
    unique_lumpsum_amt_domestic = set()  # To track unique lumpsum amounts
    for order in proforma.orderlist_set.all():
        if not order.is_lumpsum:
            if order.category == 'online' and order.report_type == 'online':
                online_sale += order.total_price
            elif order.category == 'offline' and order.report_type != 'domestic':
                offline_sale += order.total_price
            elif order.category == 'offline' and order.report_type == 'domestic':
                domestic_sale += order.total_price
        else:
            if order.category == 'online' and order.report_type == 'online':
                unique_lumpsum_amt_online.add(order.lumpsum_amt)
            elif order.category == 'offline' and order.report_type != 'domestic':
                unique_lumpsum_amt_offline.add(order.lumpsum_amt)
            elif order.category == 'offline' and order.report_type == 'domestic':
                unique_lumpsum_amt_domestic.add(order.lumpsum_amt)

    online_sale+=sum(unique_lumpsum_amt_online)
    offline_sale+=sum(unique_lumpsum_amt_offline)
    domestic_sale+=sum(unique_lumpsum_amt_domestic)

    sale_category = {'online_sale': online_sale,'offline_sale': offline_sale,'domestic_sale': domestic_sale}
    return sale_category
    
@register.simple_tag
def total_order_value(proforma):
    total_sum = 0
    unique_lumpsum_amt = set()  # To track unique lumpsum amounts
    for order in proforma.orderlist_set.all():
        if order.is_lumpsum and order.lumpsum_amt:
            unique_lumpsum_amt.add(order.lumpsum_amt)
        elif not order.is_lumpsum:
            total_sum += order.total_price

    total_sum+=sum(unique_lumpsum_amt)
    return total_sum

@register.simple_tag
def total_pi_value_inc_tax(proforma):

    total_value = total_order_value(proforma)
    tax_value = 0

    if not proforma.bank.biller_id.biller_gstin or proforma.is_sez:
        cgst = 0
        sgst = 0
        igst = 0
        total_inc_tax = total_value
    else:
        if str(proforma.state) == proforma.bank.biller_id.biller_gstin[0:2]:
            cgst = total_value*0.09
            sgst = total_value*0.09
            igst = 0
            total_inc_tax = total_value*1.18
        else:
            cgst = 0
            sgst = 0
            igst = total_value*0.18
            total_inc_tax = total_value*1.18

    return f'{round(total_inc_tax,0):.0f}'

@register.filter
def filter_by_lumpsum(queryset, is_lumpsum):
    return queryset.filter(is_lumpsum=is_lumpsum)

@register.filter
def total_lumpsums(proforma):
    unique_lumpsum_amt = set()  # To track unique lumpsum amounts
    total_lumpsum_amt = 0
    for order in proforma.orderlist_set.all():
        if order.is_lumpsum and order.lumpsum_amt:
            unique_lumpsum_amt.add(order.lumpsum_amt)
    total_lumpsum_amt += sum(unique_lumpsum_amt)
    return total_lumpsum_amt

@register.filter
def split(value, delimiter):
    """Splits the string by the given delimiter."""
    return value.split(delimiter)
    