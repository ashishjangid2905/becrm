from django import template
from datetime import datetime

register = template.Library()


@register.filter
def format_month(value):
    try:
        return datetime.strptime(value, '%Y-%m').strftime('%b-%y')
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
    